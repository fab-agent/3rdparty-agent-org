"""Auth endpoints + service unit tests."""

import pytest

from tests.conftest import make_user

# ── Service unit tests ────────────────────────────────────────────────────────


def test_hash_and_verify():
    from services.auth import hash_password, verify_password

    h = hash_password("secret123")
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)


def test_jwt_roundtrip():
    from services.auth import create_access_token, decode_token

    token = create_access_token("user-abc")
    assert decode_token(token) == "user-abc"


def test_jwt_invalid_raises():
    from services.auth import decode_token

    with pytest.raises(Exception):
        decode_token("not.a.valid.token")


# ── Setup status ──────────────────────────────────────────────────────────────


def test_setup_status_empty_db(client):
    r = client.get("/auth/setup-status")
    assert r.status_code == 200
    assert r.json()["needs_setup"] is True


def test_setup_status_with_user(client, db_session):
    make_user(db_session)
    db_session.commit()
    r = client.get("/auth/setup-status")
    assert r.json()["needs_setup"] is False


# ── First-time setup ──────────────────────────────────────────────────────────


def test_setup_creates_user_and_company(client):
    r = client.post(
        "/auth/setup",
        json={
            "name": "Kuntay Kunt",
            "email": "kuntay@test.com",
            "password": "secure1234",
            "company_name": "Fabrika Test",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_setup_blocked_when_user_exists(client, db_session):
    make_user(db_session)
    db_session.commit()
    r = client.post(
        "/auth/setup",
        json={
            "name": "X",
            "email": "x@x.com",
            "password": "pass1234",
            "company_name": "X Corp",
        },
    )
    assert r.status_code == 403


def test_setup_requires_all_fields(client):
    r = client.post("/auth/setup", json={"name": "X", "email": "x@x.com"})
    assert r.status_code == 422


def test_setup_password_too_short(client):
    r = client.post(
        "/auth/setup",
        json={
            "name": "X",
            "email": "x@x.com",
            "password": "short",
            "company_name": "X",
        },
    )
    assert r.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────


def test_login_success(client, db_session):
    make_user(db_session, email="test@login.com", password="mypassword")
    db_session.commit()
    r = client.post(
        "/auth/token", json={"email": "test@login.com", "password": "mypassword"}
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client, db_session):
    make_user(db_session, email="test@login.com", password="correct")
    db_session.commit()
    r = client.post(
        "/auth/token", json={"email": "test@login.com", "password": "wrong"}
    )
    assert r.status_code == 401


def test_login_unknown_email(client):
    r = client.post(
        "/auth/token", json={"email": "ghost@test.com", "password": "whatever"}
    )
    assert r.status_code == 401


def test_login_inactive_user(client, db_session):
    make_user(
        db_session, email="inactive@test.com", password="pass1234", is_active=False
    )
    db_session.commit()
    r = client.post(
        "/auth/token", json={"email": "inactive@test.com", "password": "pass1234"}
    )
    assert r.status_code == 403


# ── /auth/me ──────────────────────────────────────────────────────────────────


def test_me_returns_user(auth_client):
    r = auth_client.get("/auth/me")
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "admin@test.com"
    assert "companies" in data


def test_me_unauthenticated(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_me_invalid_token(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401


# ── Change password ───────────────────────────────────────────────────────────


def test_change_password(auth_client):
    r = auth_client.post("/auth/change-password", json={"password": "newpassword99"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_change_password_too_short(auth_client):
    r = auth_client.post("/auth/change-password", json={"password": "short"})
    assert r.status_code == 422
