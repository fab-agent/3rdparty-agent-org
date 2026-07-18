"""
Tenant resolution API — maps subdomain slug → company metadata.

Called by the frontend on load:
  GET /tenant/resolve?slug=fabrikayazilim
  → { id, name, slug, logo_url }

Also resolves from the Host header directly:
  GET /tenant/resolve   (Host: fabrikayazilim.agent.fab.engineering)
  → same response

Used to:
- Display company branding on the login page
- Auto-select the company after login
- Block access if the slug doesn't exist (404)
"""

import re

from fastapi import APIRouter, HTTPException, Request
from sqlmodel import select

from database import get_session
from models import Company

router = APIRouter(prefix="/tenant", tags=["tenant"])

_AGENT_DOMAIN = "agent.fab.engineering"
_SLUG_RE = re.compile(r"^[a-z0-9-]{2,64}$")


def _extract_slug_from_host(host: str) -> str | None:
    """Extract company slug from Host header.

    fabrikayazilim.agent.fab.engineering → 'fabrikayazilim'
    agent.fab.engineering                → None  (root domain, no tenant)
    localhost:8000                       → None
    """
    host = host.split(":")[0].lower()
    if host.endswith(f".{_AGENT_DOMAIN}"):
        slug = host[: -len(f".{_AGENT_DOMAIN}")]
        if "." not in slug and _SLUG_RE.match(slug):
            return slug
    return None


@router.get("/resolve")
def resolve_tenant(request: Request, slug: str | None = None):
    """
    Resolve a tenant slug to company metadata.

    Priority: ?slug= query param > Host header subdomain.
    Returns 404 if not found so the frontend can show "Company not found".
    """
    if not slug:
        slug = _extract_slug_from_host(request.headers.get("host", ""))

    if not slug:
        # Root domain — no tenant pre-selection
        return {"slug": None, "name": None, "id": None}

    if not _SLUG_RE.match(slug):
        raise HTTPException(status_code=400, detail="Invalid slug format")

    with get_session() as session:
        company = session.exec(select(Company).where(Company.slug == slug)).first()

    if not company:
        raise HTTPException(
            status_code=404, detail=f"No company found for slug '{slug}'"
        )

    return {
        "id": company.id,
        "name": company.name,
        "slug": company.slug,
    }
