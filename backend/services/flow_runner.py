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
from models import AgentConfig, Flow, InboxMessage, Personnel, ProviderKey, User, CompanyMember


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
            output = _call_llm(
                provider=provider_key.provider,
                model=agent_cfg.model,
                system_prompt=system_prompt,
                user_prompt=flow.prompt,
                api_key=api_key,
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
