"""
Autonomous flow executor.

For each Flow: find the agent's model+provider config → call LLM API →
deliver result to agent's responsible_user via InboxMessage.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from core.security import decrypt
from database import get_session
from models import AgentConfig, Flow, InboxMessage, Personnel, ProviderKey, User, CompanyMember, Skill


def _call_llm(provider: str, model: str, system_prompt: str, user_prompt: str, api_key: str) -> str:
    """Single-turn LLM call. Returns response text."""
    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return msg.content[0].text

    elif provider == "openai":
        import openai
        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2048,
        )
        return resp.choices[0].message.content or ""

    elif provider == "google":
        from google import genai
        client = genai.Client(api_key=api_key)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        resp = client.models.generate_content(model=model, contents=full_prompt)
        return resp.text or ""

    raise ValueError(f"Unsupported provider: {provider}")


def _build_system_prompt(agent: Personnel, agent_cfg: AgentConfig) -> str:
    return (
        f"Sen {agent.name} adlı bir AI ajansın.\n"
        f"Görevin: {agent.title or agent.role or 'Ajan'}\n"
        "Verilen görevi eksiksiz ve öz bir şekilde tamamla."
    )


def _get_anthropic_tool_definitions(skills: list) -> list[dict]:
    """Convert active skills to Anthropic tool definitions."""
    _BUILTIN_TOOLS = {
        "web_search": {
            "description": "Search the web for information",
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search query"}},
                "required": ["query"],
            },
        },
        "text_to_chart": {
            "description": "Generate a chart from data",
            "input_schema": {
                "type": "object",
                "properties": {
                    "data": {"type": "string"},
                    "chart_type": {"type": "string"},
                    "title": {"type": "string"},
                },
                "required": ["data"],
            },
        },
    }
    tools = []
    for s in skills:
        if not s.is_active:
            continue
        cfg = {}
        if s.config_json:
            import json as _json
            try:
                cfg = _json.loads(s.config_json)
            except Exception:
                pass
        if s.skill_type == "builtin":
            fn_name = cfg.get("function_name", s.name)
            if fn_name in _BUILTIN_TOOLS:
                tools.append({"name": fn_name, **_BUILTIN_TOOLS[fn_name]})
            else:
                tools.append({
                    "name": fn_name,
                    "description": s.description or s.name,
                    "input_schema": {"type": "object", "properties": {}, "required": []},
                })
        elif s.skill_type == "http" and cfg.get("url"):
            tools.append({
                "name": s.name.lower().replace(" ", "_"),
                "description": s.description or s.name,
                "input_schema": {
                    "type": "object",
                    "properties": {"input": {"type": "string", "description": "Input to the tool"}},
                    "required": ["input"],
                },
            })
    return tools


def _execute_flow_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool call during flow execution. Returns string result."""
    if tool_name == "web_search":
        try:
            from services.mcp_client import execute_builtin
            import asyncio
            result = asyncio.run(execute_builtin("web_search", tool_input))
            return str(result)
        except Exception as e:
            return f"Search error: {e}"
    return f"Tool '{tool_name}' called with input: {tool_input}"


def _call_llm_with_tools(
    provider: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    tools: list[dict],
) -> str:
    """Multi-turn LLM call with tool use loop. Returns final text response."""
    if provider != "anthropic" or not tools:
        return _call_llm(provider, model, system_prompt, user_prompt, api_key)

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    messages = [{"role": "user", "content": user_prompt}]

    for _iteration in range(8):
        resp = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
            tools=tools,
        )

        if resp.stop_reason != "tool_use":
            return "".join(
                block.text for block in resp.content if hasattr(block, "text")
            )

        # Collect tool use blocks and results
        messages.append({"role": "assistant", "content": resp.content})
        tool_results = []
        for block in resp.content:
            if block.type == "tool_use":
                result_text = _execute_flow_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                })
        messages.append({"role": "user", "content": tool_results})

    # Fallback: extract any text from last response
    return "".join(block.text for block in resp.content if hasattr(block, "text")) or "[max tool iterations reached]"


def _find_responsible_user_id(session: Session, agent_cfg: AgentConfig) -> Optional[str]:
    """Returns the User.id of the agent's responsible person, if linked."""
    if not agent_cfg.responsible_id:
        return None
    responsible_personnel = session.get(Personnel, agent_cfg.responsible_id)
    if not responsible_personnel or not responsible_personnel.user_id:
        return None
    return responsible_personnel.user_id


def _find_admin_user_id(session: Session, company_id: str) -> Optional[str]:
    """Fallback: find a founder/executive in the company."""
    for role in ("founder", "executive"):
        member = session.exec(
            select(CompanyMember)
            .where(CompanyMember.company_id == company_id)
            .where(CompanyMember.role == role)
        ).first()
        if member:
            return member.user_id
    return None


def run_flow(flow_id: str) -> None:
    """Execute a single flow. Called by APScheduler."""
    with get_session() as session:
        flow = session.get(Flow, flow_id)
        if not flow or not flow.enabled:
            return

        try:
            agent = session.get(Personnel, flow.personnel_id)
            if not agent:
                raise ValueError(f"Agent {flow.personnel_id} not found")

            agent_cfg = session.exec(
                select(AgentConfig).where(AgentConfig.personnel_id == agent.id)
            ).first()
            if not agent_cfg:
                raise ValueError(f"AgentConfig not found for {agent.name}")

            # Get provider key
            provider_key = session.exec(
                select(ProviderKey).where(ProviderKey.provider == agent_cfg.model.split("/")[0].lower())
            ).first()
            # Try to infer provider from model name
            if not provider_key:
                for prov in ("anthropic", "openai", "google", "mistral"):
                    pk = session.exec(
                        select(ProviderKey).where(ProviderKey.provider == prov).where(ProviderKey.status == "active")
                    ).first()
                    if pk:
                        provider_key = pk
                        break

            if not provider_key:
                raise ValueError("No active provider key found")

            api_key = decrypt(provider_key.encrypted_key)
            system_prompt = _build_system_prompt(agent, agent_cfg)

            # Load agent skills for tool use
            from sqlmodel import select as sql_select
            skills = session.exec(
                sql_select(Skill).where(Skill.agent_id == agent_cfg.id).where(Skill.is_active == True)
            ).all()

            tools = _get_anthropic_tool_definitions(list(skills)) if provider_key.provider == "anthropic" else []
            output = _call_llm_with_tools(
                provider=provider_key.provider,
                model=agent_cfg.model,
                system_prompt=system_prompt,
                user_prompt=flow.prompt,
                api_key=api_key,
                tools=tools,
            )

            # Deliver to inbox
            recipient_user_id = _find_responsible_user_id(session, agent_cfg)
            if not recipient_user_id:
                recipient_user_id = _find_admin_user_id(session, flow.company_id)
            if not recipient_user_id:
                raise ValueError("No recipient found for flow output")

            msg = InboxMessage(
                company_id=flow.company_id,
                recipient_user_id=recipient_user_id,
                source_type="flow",
                source_id=flow.id,
                title=f"[Akış] {flow.name}",
                body=output,
                created_at=datetime.utcnow(),
            )
            session.add(msg)

            # Update flow metadata
            flow.last_run_at = datetime.utcnow()
            flow.last_run_status = "success"
            flow.last_run_output = output[:500]
            flow.updated_at = datetime.utcnow()
            session.add(flow)
            session.commit()

        except Exception as e:
            flow.last_run_at = datetime.utcnow()
            flow.last_run_status = "error"
            flow.last_run_output = str(e)
            flow.updated_at = datetime.utcnow()
            session.add(flow)
            session.commit()
