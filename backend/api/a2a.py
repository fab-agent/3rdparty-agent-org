"""
A2A (Agent-to-Agent) delegation API.

Flow:
  1. POST /a2a/requests        — requesting agent creates a delegation request
  2. POST /a2a/requests/{id}/approve     — responsible human of target agent approves the task
  3. Backend auto-executes target agent  — POST /sessions to run the task
  4. POST /a2a/requests/{id}/approve-result — responsible human approves the result
  5. Result returned to the originating session
"""
import asyncio
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import select

from api.auth import get_current_user
from database import get_session
from models import A2ARequest, AgentConfig, AgentSession, Personnel, SessionMessage, User
from schemas import A2AApprove, A2AReject, A2ARequestCreate, A2AResultApprove

router = APIRouter(prefix="/a2a", tags=["a2a"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _req_to_dict(req: A2ARequest, session) -> dict:
    from_agent = session.get(Personnel, req.from_agent_id)
    to_agent = session.get(Personnel, req.to_agent_id)
    approver = session.get(Personnel, req.approver_id) if req.approver_id else None

    return {
        "id": req.id,
        "from_session_id": req.from_session_id,
        "from_agent_id": req.from_agent_id,
        "from_agent_name": from_agent.name if from_agent else None,
        "to_agent_id": req.to_agent_id,
        "to_agent_name": to_agent.name if to_agent else None,
        "task": req.task,
        "context": req.context,
        "status": req.status,
        "result": req.result,
        "approver_id": req.approver_id,
        "approver_name": approver.name if approver else None,
        "approved_at": req.approved_at.isoformat() if req.approved_at else None,
        "result_approved_at": req.result_approved_at.isoformat() if req.result_approved_at else None,
        "rejection_reason": req.rejection_reason,
        "created_at": req.created_at.isoformat(),
        "updated_at": req.updated_at.isoformat(),
    }


def _auto_set_approver(req: A2ARequest, session) -> None:
    """Set approver_id to the responsible human of the target agent."""
    cfg = session.exec(
        select(AgentConfig).where(AgentConfig.personnel_id == req.to_agent_id)
    ).first()
    if cfg and cfg.responsible_id:
        req.approver_id = cfg.responsible_id


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.get("/requests")
def list_requests(
    company_id: Optional[str] = None,
    approver_id: Optional[str] = None,
    status: Optional[str] = None,
    from_agent_id: Optional[str] = None,
    to_agent_id: Optional[str] = None,
    _: User = Depends(get_current_user),
):
    from sqlalchemy import or_
    with get_session() as session:
        q = select(A2ARequest).order_by(A2ARequest.created_at.desc())
        if company_id:
            agent_ids = list(session.exec(
                select(Personnel.id).where(Personnel.company_id == company_id)
            ).all())
            q = q.where(
                or_(
                    A2ARequest.from_agent_id.in_(agent_ids),
                    A2ARequest.to_agent_id.in_(agent_ids),
                )
            )
        if approver_id:
            q = q.where(A2ARequest.approver_id == approver_id)
        if status:
            q = q.where(A2ARequest.status == status)
        if from_agent_id:
            q = q.where(A2ARequest.from_agent_id == from_agent_id)
        if to_agent_id:
            q = q.where(A2ARequest.to_agent_id == to_agent_id)
        rows = session.exec(q).all()
        return [_req_to_dict(r, session) for r in rows]


@router.get("/requests/pending-count")
def pending_count(company_id: Optional[str] = None, _: User = Depends(get_current_user)):
    """Returns count of requests awaiting approval (for notification badge)."""
    from sqlalchemy import or_
    with get_session() as session:
        q = select(A2ARequest).where(
            A2ARequest.status.in_(["pending_approval", "pending_result_approval"])
        )
        if company_id:
            agent_ids = list(session.exec(
                select(Personnel.id).where(Personnel.company_id == company_id)
            ).all())
            q = q.where(
                or_(
                    A2ARequest.from_agent_id.in_(agent_ids),
                    A2ARequest.to_agent_id.in_(agent_ids),
                )
            )
        return {"count": len(session.exec(q).all())}


@router.post("/requests", status_code=201)
def create_request(body: A2ARequestCreate, _: User = Depends(get_current_user)):
    with get_session() as session:
        # Validate agents exist
        for pid in [body.from_agent_id, body.to_agent_id]:
            if not session.get(Personnel, pid):
                raise HTTPException(status_code=404, detail=f"Personnel {pid} not found")

        req = A2ARequest(
            from_session_id=body.from_session_id,
            from_agent_id=body.from_agent_id,
            to_agent_id=body.to_agent_id,
            task=body.task,
            context=body.context,
            status="pending_approval",
        )
        _auto_set_approver(req, session)
        session.add(req)
        session.commit()
        session.refresh(req)
        return _req_to_dict(req, session)


@router.get("/requests/{req_id}")
def get_request(req_id: str, _: User = Depends(get_current_user)):
    with get_session() as session:
        req = session.get(A2ARequest, req_id)
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")
        return _req_to_dict(req, session)


@router.post("/requests/{req_id}/approve")
def approve_request(req_id: str, body: A2AApprove, background_tasks: BackgroundTasks,
                    caller: User = Depends(get_current_user)):
    """Approve the task. Triggers execution in background."""
    with get_session() as session:
        req = session.get(A2ARequest, req_id)
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")
        if req.status != "pending_approval":
            raise HTTPException(status_code=409, detail=f"Request is not pending approval (status: {req.status})")
        # Verify the approver matches the designated responsible person
        if req.approver_id and req.approver_id != body.approver_id:
            raise HTTPException(status_code=403, detail="Yetkisiz: bu talebi onaylayacak kişi siz değilsiniz")
        req.status = "running"
        req.approver_id = body.approver_id
        req.approved_at = datetime.utcnow()
        req.updated_at = datetime.utcnow()
        session.add(req)
        session.commit()
        req_id_copy = req.id

    background_tasks.add_task(_execute_a2a_task, req_id_copy)
    return {"status": "running", "req_id": req_id_copy}


@router.post("/requests/{req_id}/approve-result")
def approve_result(req_id: str, body: A2AResultApprove, _: User = Depends(get_current_user)):
    """Approve the result and mark the request as completed."""
    with get_session() as session:
        req = session.get(A2ARequest, req_id)
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")
        if req.status != "pending_result_approval":
            raise HTTPException(status_code=409, detail=f"Request is not pending result approval (status: {req.status})")
        req.status = "completed"
        req.result_approved_at = datetime.utcnow()
        req.updated_at = datetime.utcnow()
        session.add(req)
        session.commit()
        session.refresh(req)
        return _req_to_dict(req, session)


@router.post("/requests/{req_id}/reject")
def reject_request(req_id: str, body: A2AReject, _: User = Depends(get_current_user)):
    with get_session() as session:
        req = session.get(A2ARequest, req_id)
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")
        if req.status not in ("pending_approval", "pending_result_approval"):
            raise HTTPException(status_code=409, detail="Request cannot be rejected at this stage")
        req.status = "rejected"
        req.rejection_reason = body.reason
        req.approver_id = body.approver_id
        req.updated_at = datetime.utcnow()
        session.add(req)
        session.commit()
        session.refresh(req)
        return _req_to_dict(req, session)


# ── Background execution ──────────────────────────────────────────────────────

async def _run_agent_task(session_id: str, task: str) -> str:
    """Run the agent and collect the full text response."""
    from services.agent_runtime import run_session
    text_parts = []
    async for event in run_session(session_id, task):
        if event["type"] == "text":
            text_parts.append(event["content"])
    return "".join(text_parts)


def _execute_a2a_task(req_id: str) -> None:
    """
    Background task: create a temporary session for the target agent,
    run the task, store the result, set status to pending_result_approval.
    """
    with get_session() as session:
        req = session.get(A2ARequest, req_id)
        if not req or req.status != "running":
            return

        # Create ephemeral session for target agent
        ephemeral = AgentSession(
            personnel_id=req.to_agent_id,
            title=f"A2A: {req.task[:60]}",
        )
        session.add(ephemeral)
        session.commit()
        session.refresh(ephemeral)
        ephemeral_id = ephemeral.id

    # Build the task message including context
    full_task = req.task
    if req.context:
        full_task = f"{req.task}\n\nBağlam:\n{req.context}"

    # Run async in a new event loop (background thread)
    try:
        result = asyncio.run(_run_agent_task(ephemeral_id, full_task))
    except Exception as e:
        result = f"[Görev yürütme hatası: {e}]"

    with get_session() as session:
        req = session.get(A2ARequest, req_id)
        if req:
            req.result = result or "[Boş yanıt]"
            req.status = "pending_result_approval"
            req.updated_at = datetime.utcnow()
            session.add(req)
            session.commit()
