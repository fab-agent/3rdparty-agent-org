"""Agent memory: generate and load session summaries."""

from datetime import datetime

from sqlmodel import select

from core.security import decrypt
from database import get_session
from models import AgentConfig, AgentMemory, AgentSession, ProviderKey, SessionMessage


async def generate_session_summary(session_id: str) -> None:
    """Background task: summarize a closed session and store as AgentMemory."""
    with get_session() as db:
        sess = db.get(AgentSession, session_id)
        if not sess:
            return

        messages = db.exec(
            select(SessionMessage)
            .where(SessionMessage.session_id == session_id)
            .order_by(SessionMessage.created_at)
        ).all()

        if len(messages) < 2:
            return  # Not enough content to summarize

        # Build conversation text
        convo_lines = []
        for m in messages:
            role_label = "User" if m.role == "user" else "Agent"
            convo_lines.append(f"{role_label}: {m.content[:500]}")
        convo_text = "\n".join(convo_lines[-30:])  # last 30 messages max

        # Get agent config and provider
        agent_cfg = db.exec(
            select(AgentConfig).where(AgentConfig.personnel_id == sess.personnel_id)
        ).first()
        if not agent_cfg:
            return

        provider_key = None

        def _prov_for_model(m: str) -> str:
            m = (m or "").lower()
            if m.startswith("claude"):
                return "anthropic"
            if m.startswith(("gpt-", "o1", "o3")):
                return "openai"
            if m.startswith("gemini"):
                return "google"
            if m.startswith(("mistral", "codestral")):
                return "mistral"
            if m.startswith("qwen"):
                return "qwen"
            return ""

        agent_prov = _prov_for_model(agent_cfg.model or "")
        provider_key = None
        for prov in ([agent_prov] if agent_prov else []) + [
            "anthropic",
            "openai",
            "google",
            "mistral",
            "qwen",
        ]:
            if not prov:
                continue
            pk = db.exec(
                select(ProviderKey)
                .where(ProviderKey.provider == prov)
                .where(ProviderKey.status == "active")
            ).first()
            if pk:
                provider_key = pk
                break
        if not provider_key:
            return

        api_key = decrypt(provider_key.encrypted_key)
        summary_prompt = (
            "The following is a conversation between a user and an AI agent. "
            "Extract 2-4 key facts the agent learned, decisions made, or tasks completed. "
            "Write a brief paragraph (max 100 words) in plain English starting with 'In a previous session,'\n\n"
            + convo_text
        )

        try:
            summary = _call_summary_llm(
                provider=provider_key.provider,
                model=agent_cfg.model,
                api_key=api_key,
                prompt=summary_prompt,
            )
        except Exception:
            return

        if not summary.strip():
            return

        memory = AgentMemory(
            personnel_id=sess.personnel_id,
            session_id=session_id,
            summary=summary.strip(),
            created_at=datetime.utcnow(),
        )
        db.add(memory)
        db.commit()


def _call_summary_llm(provider: str, model: str, api_key: str, prompt: str) -> str:

    if provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text

    elif provider == "openai":
        import openai

        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
        )
        return resp.choices[0].message.content or ""

    elif provider == "google":
        from google import genai

        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(model=model, contents=prompt)
        return resp.text or ""

    elif provider in ("qwen", "mistral"):
        import openai
        from sqlmodel import select as _sel

        from database import get_session as _gs
        from models import ProviderKey as _PK

        base_url = None
        with _gs() as _db:
            pk = _db.exec(_sel(_PK).where(_PK.provider == provider)).first()
            if pk and pk.base_url:
                base_url = (
                    f"{pk.base_url}/v1"
                    if not pk.base_url.endswith("/v1")
                    else pk.base_url
                )
        if not base_url:
            base_url = (
                "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
                if provider == "qwen"
                else "https://api.mistral.ai/v1"
            )
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
        )
        return resp.choices[0].message.content or ""

    return ""


def load_agent_memories(personnel_id: str, limit: int = 3) -> list[str]:
    """Return the most recent memory summaries for an agent."""
    with get_session() as db:
        rows = db.exec(
            select(AgentMemory)
            .where(AgentMemory.personnel_id == personnel_id)
            .order_by(AgentMemory.created_at.desc())
            .limit(limit)
        ).all()
        return [r.summary for r in rows]
