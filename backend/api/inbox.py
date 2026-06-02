from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, func

from api.auth import get_current_user
from database import get_session
from models import InboxMessage, User

router = APIRouter(prefix="/inbox", tags=["inbox"])


def _to_dict(m: InboxMessage) -> dict:
    return {
        "id": m.id,
        "company_id": m.company_id,
        "recipient_user_id": m.recipient_user_id,
        "source_type": m.source_type,
        "source_id": m.source_id,
        "title": m.title,
        "body": m.body,
        "read": m.read,
        "created_at": m.created_at.isoformat(),
    }


@router.get("")
def list_inbox(
    company_id: Optional[str] = None,
    unread_only: bool = False,
    period: Optional[str] = None,   # "week" | "month"
    current_user: User = Depends(get_current_user),
):
    with get_session() as session:
        q = select(InboxMessage).where(InboxMessage.recipient_user_id == current_user.id)
        if company_id:
            q = q.where(InboxMessage.company_id == company_id)
        if unread_only:
            q = q.where(InboxMessage.read == False)
        if period == "week":
            from datetime import timedelta
            q = q.where(InboxMessage.created_at >= datetime.utcnow() - timedelta(days=7))
        elif period == "month":
            from datetime import timedelta
            q = q.where(InboxMessage.created_at >= datetime.utcnow() - timedelta(days=30))
        q = q.order_by(InboxMessage.created_at.desc())
        return [_to_dict(m) for m in session.exec(q).all()]


@router.get("/unread-count")
def unread_count(company_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    with get_session() as session:
        q = select(func.count()).where(
            InboxMessage.recipient_user_id == current_user.id,
            InboxMessage.read == False,
        )
        if company_id:
            q = q.where(InboxMessage.company_id == company_id)
        count = session.exec(q).one()
        return {"count": count}


@router.post("/{msg_id}/read")
def mark_read(msg_id: str, current_user: User = Depends(get_current_user)):
    with get_session() as session:
        msg = session.get(InboxMessage, msg_id)
        if not msg or msg.recipient_user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Message not found")
        msg.read = True
        session.add(msg)
        session.commit()
        session.refresh(msg)
        return _to_dict(msg)


@router.post("/read-all")
def mark_all_read(company_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    with get_session() as session:
        q = select(InboxMessage).where(
            InboxMessage.recipient_user_id == current_user.id,
            InboxMessage.read == False,
        )
        if company_id:
            q = q.where(InboxMessage.company_id == company_id)
        msgs = session.exec(q).all()
        for m in msgs:
            m.read = True
            session.add(m)
        session.commit()
        return {"marked": len(msgs)}


@router.delete("/{msg_id}", status_code=204)
def delete_message(msg_id: str, current_user: User = Depends(get_current_user)):
    with get_session() as session:
        msg = session.get(InboxMessage, msg_id)
        if not msg or msg.recipient_user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Message not found")
        session.delete(msg)
        session.commit()
