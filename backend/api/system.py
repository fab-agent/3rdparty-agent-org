from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter

router = APIRouter(tags=["system"])

APP_VERSION = "0.2.0"
GITHUB_REPO = "fab-agent/3rdparty-agent-org"

_cache: dict = {"data": None, "expires": datetime.min}


@router.get("/system/version")
def check_version():
    """Returns current version and checks GitHub for latest release (cached 1h)."""
    global _cache
    now = datetime.utcnow()

    if _cache["data"] is None or now > _cache["expires"]:
        latest_tag: Optional[str] = None
        release_url: Optional[str] = None
        try:
            resp = httpx.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                timeout=5,
                headers={"Accept": "application/vnd.github+json", "User-Agent": "3rdparty-agent-org"},
            )
            if resp.status_code == 200:
                data = resp.json()
                latest_tag = data.get("tag_name", "").lstrip("v")
                release_url = data.get("html_url")
        except Exception:
            pass

        _cache["data"] = {
            "current": APP_VERSION,
            "latest": latest_tag,
            "release_url": release_url,
            "update_available": bool(latest_tag and latest_tag != APP_VERSION),
        }
        _cache["expires"] = now + timedelta(hours=1)

    return _cache["data"]
