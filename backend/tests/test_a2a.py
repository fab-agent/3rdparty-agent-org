"""
A2A (Agent-to-Agent) delegation flow tests.

Covers: create request → approve → (mocked execution) → approve-result
        and: create request → reject
"""

from unittest.mock import patch

import pytest

from tests.conftest import (
    make_agent_config,
    make_personnel,
    make_provider_key,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def a2a_setup(auth_client, db_session):
    """
    Two agents (from_agent, to_agent) with configs.
    A human responsible person linked to to_agent.
    Returns dict with ids needed for A2A tests.
    """
    co = auth_client._test_company
    human = auth_client._test_user

    # Responsible human personnel record
    responsible = make_personnel(
        db_session,
        co.id,
        name="Responsible Human",
        slug="responsible-human",
        type="human",
        title="Lead",
    )
    responsible.user_id = human.id

    from_agent = make_personnel(
        db_session,
        co.id,
        name="FromBot",
        slug="from-bot",
        type="agent",
        title="Sender Agent",
    )
    to_agent = make_personnel(
        db_session,
        co.id,
        name="ToBot",
        slug="to-bot",
        type="agent",
        title="Receiver Agent",
    )

    from_cfg = make_agent_config(
        db_session, from_agent.id, model="gpt-4o-mini", responsible_id=responsible.id
    )
    to_cfg = make_agent_config(
        db_session, to_agent.id, model="gpt-4o-mini", responsible_id=responsible.id
    )

    make_provider_key(db_session, provider="openai")
    db_session.commit()

    return {
        "company_id": co.id,
        "from_agent_id": from_agent.id,
        "to_agent_id": to_agent.id,
        "responsible_id": responsible.id,
        "from_cfg_id": from_cfg.id,
        "to_cfg_id": to_cfg.id,
    }


def _post_request(client, setup, task="Test görevi", **extra):
    """Helper: POST /a2a/requests with required fields."""
    return client.post(
        "/a2a/requests",
        json={
            "from_agent_id": setup["from_agent_id"],
            "to_agent_id": setup["to_agent_id"],
            "task": task,
            **extra,
        },
    )


# ── Pending count ──────────────────────────────────────────────────────────────


def test_pending_count_empty(auth_client):
    r = auth_client.get("/a2a/requests/pending-count")
    assert r.status_code == 200
    assert r.json()["count"] == 0


# ── Create request ─────────────────────────────────────────────────────────────


def test_create_a2a_request(auth_client, a2a_setup):
    r = _post_request(
        auth_client,
        a2a_setup,
        task="Lütfen deployment sürecini analiz et",
        context="Proje: fab.engineering",
    )
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "pending_approval"
    assert data["from_agent_name"] == "FromBot"
    assert data["to_agent_name"] == "ToBot"
    assert data["task"] == "Lütfen deployment sürecini analiz et"
    assert data["approver_id"] == a2a_setup["responsible_id"]


def test_create_request_invalid_agent(auth_client):
    r = auth_client.post(
        "/a2a/requests",
        json={
            "from_agent_id": "nonexistent-id",
            "to_agent_id": "also-nonexistent",
            "task": "test",
        },
    )
    assert r.status_code == 404


def test_pending_count_after_create(auth_client, a2a_setup):
    _post_request(auth_client, a2a_setup, task="Task 1")
    _post_request(auth_client, a2a_setup, task="Task 2")
    r = auth_client.get("/a2a/requests/pending-count")
    assert r.json()["count"] == 2


# ── List & get ────────────────────────────────────────────────────────────────


def test_list_requests(auth_client, a2a_setup):
    _post_request(auth_client, a2a_setup, task="Test görev")
    r = auth_client.get("/a2a/requests")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_get_request_by_id(auth_client, a2a_setup):
    created = _post_request(auth_client, a2a_setup, task="Detaylı görev").json()
    r = auth_client.get(f"/a2a/requests/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_get_request_not_found(auth_client):
    r = auth_client.get("/a2a/requests/nonexistent-id")
    assert r.status_code == 404


# ── Reject ────────────────────────────────────────────────────────────────────


def test_reject_request(auth_client, a2a_setup):
    req = _post_request(auth_client, a2a_setup, task="Reddedilecek görev").json()
    r = auth_client.post(
        f"/a2a/requests/{req['id']}/reject",
        json={
            "approver_id": a2a_setup["responsible_id"],
            "reason": "Uygun değil",
        },
    )
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"
    assert r.json()["rejection_reason"] == "Uygun değil"


def test_cannot_reject_already_rejected(auth_client, a2a_setup):
    req = _post_request(auth_client, a2a_setup, task="Görev").json()
    auth_client.post(
        f"/a2a/requests/{req['id']}/reject",
        json={
            "approver_id": a2a_setup["responsible_id"],
            "reason": "Reddedildi",
        },
    )
    r = auth_client.post(
        f"/a2a/requests/{req['id']}/reject",
        json={
            "approver_id": a2a_setup["responsible_id"],
            "reason": "Tekrar red",
        },
    )
    assert r.status_code == 409


# ── Approve → execution → approve-result ──────────────────────────────────────


def test_approve_request_transitions_to_running(auth_client, a2a_setup):
    req = _post_request(auth_client, a2a_setup, task="Onaylanacak görev").json()
    with patch("api.a2a._execute_a2a_task"):
        r = auth_client.post(
            f"/a2a/requests/{req['id']}/approve",
            json={
                "approver_id": a2a_setup["responsible_id"],
            },
        )
    assert r.status_code == 200
    assert r.json()["status"] == "running"


def test_cannot_approve_non_pending(auth_client, a2a_setup):
    req = _post_request(auth_client, a2a_setup, task="Görev").json()
    with patch("api.a2a._execute_a2a_task"):
        auth_client.post(
            f"/a2a/requests/{req['id']}/approve",
            json={
                "approver_id": a2a_setup["responsible_id"],
            },
        )
        r = auth_client.post(
            f"/a2a/requests/{req['id']}/approve",
            json={
                "approver_id": a2a_setup["responsible_id"],
            },
        )
    assert r.status_code == 409


def test_full_a2a_flow(auth_client, a2a_setup):
    """Complete flow: create → approve → (mock result) → approve-result → completed"""
    # 1. Create
    req = _post_request(
        auth_client,
        a2a_setup,
        task="Deploy raporu hazırla",
        context="Son sprint sonuçları",
    ).json()
    assert req["status"] == "pending_approval"

    # 2. Approve (suppress background task)
    with patch("api.a2a._execute_a2a_task"):
        auth_client.post(
            f"/a2a/requests/{req['id']}/approve",
            json={
                "approver_id": a2a_setup["responsible_id"],
            },
        )

    # 3. Simulate completed execution
    from database import get_session
    from models import A2ARequest

    with get_session() as s:
        a2a_req = s.get(A2ARequest, req["id"])
        a2a_req.result = "Deploy başarıyla tamamlandı. 3 servis güncellendi."
        a2a_req.status = "pending_result_approval"
        s.commit()

    # 4. Verify pending_result_approval
    r = auth_client.get(f"/a2a/requests/{req['id']}")
    assert r.json()["status"] == "pending_result_approval"
    assert "Deploy" in r.json()["result"]

    # 5. Approve result
    r = auth_client.post(
        f"/a2a/requests/{req['id']}/approve-result",
        json={
            "approver_id": a2a_setup["responsible_id"],
        },
    )
    assert r.status_code == 200
    assert r.json()["status"] == "completed"
    assert r.json()["result_approved_at"] is not None


def test_approve_result_on_wrong_status(auth_client, a2a_setup):
    req = _post_request(auth_client, a2a_setup, task="Görev").json()
    # Still pending_approval, try to approve-result
    r = auth_client.post(
        f"/a2a/requests/{req['id']}/approve-result",
        json={
            "approver_id": a2a_setup["responsible_id"],
        },
    )
    assert r.status_code == 409


# ── Filter by company ──────────────────────────────────────────────────────────


def test_filter_requests_by_company(auth_client, a2a_setup):
    _post_request(auth_client, a2a_setup, task="Şirket görevi")
    r = auth_client.get(f"/a2a/requests?company_id={a2a_setup['company_id']}")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_filter_by_status(auth_client, a2a_setup):
    _post_request(auth_client, a2a_setup, task="Görev")
    r = auth_client.get("/a2a/requests?status=pending_approval")
    assert all(req["status"] == "pending_approval" for req in r.json())
