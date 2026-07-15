"""User & CompanyMember management (founder-only CRUD)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from api.auth import require_founder
from database import get_session
from models import Company, CompanyMember, Department, Personnel, User

router = APIRouter(prefix="/users", tags=["users"])


def _user_to_dict(user: User, session) -> dict:
    memberships = session.exec(
        select(CompanyMember).where(CompanyMember.user_id == user.id)
    ).all()
    companies = []
    for m in memberships:
        co = session.get(Company, m.company_id)
        scope_name = None
        if m.scope_id:
            dept = session.get(Department, m.scope_id)
            if dept:
                scope_name = dept.name
            else:
                agent = session.get(Personnel, m.scope_id)
                if agent:
                    scope_name = agent.name
        companies.append(
            {
                "membership_id": m.id,
                "company_id": m.company_id,
                "company_name": co.name if co else None,
                "role": m.role,
                "scope_id": m.scope_id,
                "scope_name": scope_name,
            }
        )
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "is_active": user.is_active,
        "must_change_password": user.must_change_password,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat(),
        "companies": companies,
    }


@router.get("")
def list_users(company_id: str | None = None, _: User = Depends(require_founder)):
    with get_session() as session:
        if company_id:
            member_ids = [
                m.user_id
                for m in session.exec(
                    select(CompanyMember).where(CompanyMember.company_id == company_id)
                ).all()
            ]
            users = session.exec(select(User).where(User.id.in_(member_ids))).all()
        else:
            users = session.exec(select(User)).all()
        return [_user_to_dict(u, session) for u in users]


@router.get("/{user_id}")
def get_user(user_id: str, _: User = Depends(require_founder)):
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        return _user_to_dict(user, session)


@router.patch("/{user_id}")
def update_user(user_id: str, body: dict, _: User = Depends(require_founder)):
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        if "name" in body:
            user.name = body["name"]
        if "is_active" in body:
            user.is_active = body["is_active"]
        session.add(user)
        session.commit()
        session.refresh(user)
        return _user_to_dict(user, session)


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: str, _: User = Depends(require_founder)):
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        # Remove memberships
        for m in session.exec(
            select(CompanyMember).where(CompanyMember.user_id == user_id)
        ).all():
            session.delete(m)
        session.delete(user)
        session.commit()


# ── Membership management ─────────────────────────────────────────────────────


@router.get("/{user_id}/memberships")
def list_memberships(user_id: str, _: User = Depends(require_founder)):
    with get_session() as session:
        return session.exec(
            select(CompanyMember).where(CompanyMember.user_id == user_id)
        ).all()


@router.patch("/memberships/{member_id}")
def update_membership(member_id: str, body: dict, _: User = Depends(require_founder)):
    with get_session() as session:
        member = session.get(CompanyMember, member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Üyelik bulunamadı")
        if "role" in body:
            member.role = body["role"]
        if "scope_id" in body:
            member.scope_id = body["scope_id"]
        session.add(member)
        session.commit()
        session.refresh(member)
        return member


@router.delete("/memberships/{member_id}", status_code=204)
def delete_membership(member_id: str, _: User = Depends(require_founder)):
    with get_session() as session:
        member = session.get(CompanyMember, member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Üyelik bulunamadı")
        session.delete(member)
        session.commit()
