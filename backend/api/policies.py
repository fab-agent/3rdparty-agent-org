from datetime import datetime
from typing import Optional
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from api.auth import get_current_user, require_manager
from database import get_session
from models import ChangeRequest, Policy, User

router = APIRouter(tags=["policies"])


class PolicyCreate(BaseModel):
    company_id: str
    name: str
    slug: str
    content: str = ""
    scope: str = "company"        # company | department | agent
    department_id: Optional[str] = None
    agent_config_id: Optional[str] = None


class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    scope: Optional[str] = None
    department_id: Optional[str] = None
    agent_config_id: Optional[str] = None
    is_active: Optional[bool] = None


def _policy_dict(p: Policy) -> dict:
    return {
        "id": p.id,
        "company_id": p.company_id,
        "department_id": p.department_id,
        "agent_config_id": p.agent_config_id,
        "name": p.name,
        "slug": p.slug,
        "content": p.content,
        "scope": p.scope,
        "is_active": p.is_active,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


@router.get("/policies")
def list_policies(
    company_id: Optional[str] = None,
    department_id: Optional[str] = None,
    agent_config_id: Optional[str] = None,
    scope: Optional[str] = None,
    _: User = Depends(get_current_user),
):
    with get_session() as session:
        q = select(Policy)
        if company_id:
            q = q.where(Policy.company_id == company_id)
        if department_id:
            q = q.where(Policy.department_id == department_id)
        if agent_config_id:
            q = q.where(Policy.agent_config_id == agent_config_id)
        if scope:
            q = q.where(Policy.scope == scope)
        rows = session.exec(q.order_by(Policy.scope, Policy.name)).all()
        return [_policy_dict(p) for p in rows]


@router.post("/policies", status_code=201)
def create_policy(body: PolicyCreate, _: User = Depends(require_manager)):
    with get_session() as session:
        policy = Policy(
            company_id=body.company_id,
            name=body.name,
            slug=body.slug,
            content=body.content,
            scope=body.scope,
            department_id=body.department_id or None,
            agent_config_id=body.agent_config_id or None,
        )
        session.add(policy)
        session.commit()
        session.refresh(policy)
        return _policy_dict(policy)


@router.get("/policies/{policy_id}")
def get_policy(policy_id: str, _: User = Depends(get_current_user)):
    with get_session() as session:
        p = session.get(Policy, policy_id)
        if not p:
            raise HTTPException(status_code=404, detail="Policy not found")
        return _policy_dict(p)


@router.put("/policies/{policy_id}")
def update_policy(
    policy_id: str,
    body: PolicyUpdate,
    propose: bool = False,
    personnel_id: Optional[str] = None,
    user: User = Depends(require_manager),
):
    """
    Direct update (managers+) or propose a CR.
    If propose=true, creates a ChangeRequest instead of applying.
    """
    with get_session() as session:
        p = session.get(Policy, policy_id)
        if not p:
            raise HTTPException(status_code=404, detail="Policy not found")

        if propose and personnel_id:
            original = {"name": p.name, "content": p.content, "scope": p.scope}
            proposed = {k: v for k, v in body.model_dump().items() if v is not None}
            cr = ChangeRequest(
                company_id=p.company_id,
                personnel_id=personnel_id,
                change_type="policy",
                title=f"Politika güncelleme: {p.name}",
                proposed_json=json.dumps({"policy_id": policy_id, **proposed}),
                original_json=json.dumps(original),
                status="submitted",
            )
            session.add(cr)
            session.commit()
            session.refresh(cr)
            return {"change_request_id": cr.id, "status": "submitted"}

        for field, val in body.model_dump(exclude_none=True).items():
            setattr(p, field, val)
        p.updated_at = datetime.utcnow()
        session.add(p)
        session.commit()
        session.refresh(p)
        return _policy_dict(p)


@router.delete("/policies/{policy_id}", status_code=204)
def delete_policy(policy_id: str, _: User = Depends(require_manager)):
    with get_session() as session:
        p = session.get(Policy, policy_id)
        if not p:
            raise HTTPException(status_code=404, detail="Policy not found")
        session.delete(p)
        session.commit()
