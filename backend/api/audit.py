"""Audit log API — read-only, admin/executive only in production."""
from typing import Optional
import json
from datetime import datetime

from fastapi import APIRouter
from sqlmodel import select

from database import get_session
from models import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


def log_action(
    session,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    entity_name: Optional[str] = None,
    company_id: Optional[str] = None,
    user_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    """Helper called from other routers to record an audit event."""
    entry = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        company_id=company_id,
        user_id=user_id,
        details_json=json.dumps(details) if details else None,
        created_at=datetime.utcnow(),
    )
    session.add(entry)


@router.get("")
def list_audit_logs(
    company_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
):
    with get_session() as session:
        q = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        if company_id:
            q = q.where(AuditLog.company_id == company_id)
        if entity_type:
            q = q.where(AuditLog.entity_type == entity_type)
        if action:
            q = q.where(AuditLog.action == action)
        if user_id:
            q = q.where(AuditLog.user_id == user_id)
        rows = session.exec(q).all()
        return [
            {
                "id": r.id,
                "action": r.action,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "entity_name": r.entity_name,
                "company_id": r.company_id,
                "user_id": r.user_id,
                "details": json.loads(r.details_json) if r.details_json else None,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
