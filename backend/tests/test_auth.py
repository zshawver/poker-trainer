"""Integration tests for the auth slice (login + /me).

Hits a real Postgres test DB via the `client` and `db_session` fixtures
in conftest.py. Verifies ADR-0004 wiring end to end.
"""

import pytest

from src.core.security import hash_password
from src.models.user import User

pytestmark = pytest.mark.asyncio


async def _seed_user(db_session, email: str, password: str, is_admin: bool = False) -> User:
    user = User(email=email, hashed_password=hash_password(password), is_admin=is_admin)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def test_login_and_me_happy_path(client, db_session):
    user = await _seed_user(db_session, "alice@example.com", "hunter2")

    resp = await client.post(
        "/api/auth/login",
        data={"username": "alice@example.com", "password": "hunter2"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    token = body["access_token"]
    assert token

    me = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    payload = me.json()
    assert payload["id"] == str(user.id)
    assert payload["email"] == "alice@example.com"


async def test_login_wrong_password_returns_401(client, db_session):
    await _seed_user(db_session, "bob@example.com", "correct-horse")

    resp = await client.post(
        "/api/auth/login",
        data={"username": "bob@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401


async def test_login_unknown_email_returns_401(client):
    resp = await client.post(
        "/api/auth/login",
        data={"username": "nobody@example.com", "password": "whatever"},
    )
    assert resp.status_code == 401


async def test_me_without_token_returns_401(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_me_with_bogus_token_returns_401(client):
    resp = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer not-a-real-jwt"},
    )
    assert resp.status_code == 401
