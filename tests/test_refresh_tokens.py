from datetime import UTC, datetime, timedelta

import pytest

from src.core.security import hash_refresh_token
from src.core.settings import settings
from src.infrastructure.models import RefreshToken
from src.infrastructure.repositories import RefreshTokenRepository

TOKEN_URL = "/api/v1/auth/token"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"


def login(client, username="alice", password="password123"):
    response = client.post(TOKEN_URL, data={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def refresh(client, refresh_token):
    return client.post(REFRESH_URL, json={"refresh_token": refresh_token})


def bearer(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_login_returns_token_pair(client, create_user):
    create_user("alice")

    tokens = login(client)

    assert tokens["token_type"] == "bearer"
    assert tokens["refresh_token"]
    assert tokens["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def test_refresh_rotates_token_pair(client, create_user):
    create_user("alice")
    first = login(client)

    response = refresh(client, first["refresh_token"])

    assert response.status_code == 200
    second = response.json()
    assert second["refresh_token"] != first["refresh_token"]
    assert client.get("/api/v1/users/me", headers=bearer(second)).status_code == 200
    assert refresh(client, second["refresh_token"]).status_code == 200


def test_reused_refresh_token_revokes_session(client, create_user):
    create_user("alice")
    first = login(client)
    second = refresh(client, first["refresh_token"]).json()

    reused = refresh(client, first["refresh_token"])

    assert reused.status_code == 401
    assert reused.headers["WWW-Authenticate"] == "Bearer"
    assert refresh(client, second["refresh_token"]).status_code == 401


def test_reuse_does_not_affect_other_sessions(client, create_user):
    create_user("alice")
    laptop = login(client)
    phone = login(client)

    refresh(client, laptop["refresh_token"])
    refresh(client, laptop["refresh_token"])

    assert refresh(client, phone["refresh_token"]).status_code == 200


def test_concurrent_refresh_with_same_token_revokes_session(
    client, create_user, monkeypatch
):
    create_user("alice")
    tokens = login(client)
    monkeypatch.setattr(RefreshTokenRepository, "revoke", lambda self, token_id: False)

    assert refresh(client, tokens["refresh_token"]).status_code == 401

    monkeypatch.undo()
    assert refresh(client, tokens["refresh_token"]).status_code == 401


@pytest.mark.parametrize(
    ("payload", "status_code"),
    [
        ({"refresh_token": "unknown"}, 401),
        ({"refresh_token": ""}, 422),
        ({"refresh_token": None}, 422),
        ({"refresh_token": "x" * 257}, 422),
        ({"refresh_token": "unknown", "user_id": 1}, 422),
        ({}, 422),
    ],
)
def test_invalid_refresh_requests_are_rejected(client, payload, status_code):
    assert client.post(REFRESH_URL, json=payload).status_code == status_code


def test_expired_refresh_token_is_rejected(client, create_user, session_factory):
    create_user("alice")
    tokens = login(client)
    with session_factory() as db:
        stored = db.query(RefreshToken).one()
        stored.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()

    assert refresh(client, tokens["refresh_token"]).status_code == 401


def test_refresh_tokens_are_stored_hashed(client, create_user, session_factory):
    create_user("alice")
    tokens = login(client)

    with session_factory() as db:
        stored = db.query(RefreshToken).one()

    assert stored.token_hash == hash_refresh_token(tokens["refresh_token"])
    assert stored.token_hash != tokens["refresh_token"]


def test_expired_tokens_are_removed_on_next_login(client, create_user, session_factory):
    create_user("alice")
    login(client)
    with session_factory() as db:
        db.query(RefreshToken).update(
            {RefreshToken.expires_at: datetime.now(UTC) - timedelta(days=1)}
        )
        db.commit()

    login(client)

    with session_factory() as db:
        assert db.query(RefreshToken).count() == 1


def test_logout_revokes_refresh_token(client, create_user):
    create_user("alice")
    tokens = login(client)

    response = client.post(LOGOUT_URL, json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 204
    assert refresh(client, tokens["refresh_token"]).status_code == 401
    assert client.post(LOGOUT_URL, json={"refresh_token": "unknown"}).status_code == 204


def test_password_change_revokes_refresh_tokens(client, create_user):
    create_user("alice")
    tokens = login(client)

    client.patch(
        "/api/v1/users/me",
        json={"password": "new-password", "current_password": "password123"},
        headers=bearer(tokens),
    )

    assert refresh(client, tokens["refresh_token"]).status_code == 401
    assert (
        refresh(
            client, login(client, password="new-password")["refresh_token"]
        ).status_code
        == 200
    )


def test_deactivation_and_deletion_revoke_refresh_tokens(client, create_user):
    create_user("admin", is_admin=True)
    alice = create_user("alice")
    bob = create_user("bob")
    admin_headers = bearer(login(client, "admin"))
    alice_tokens = login(client, "alice")
    bob_tokens = login(client, "bob")

    client.patch(
        f"/api/v1/users/{alice.id}", json={"is_active": False}, headers=admin_headers
    )
    client.delete(f"/api/v1/users/{bob.id}", headers=admin_headers)
    client.patch(
        f"/api/v1/users/{alice.id}", json={"is_active": True}, headers=admin_headers
    )

    assert refresh(client, alice_tokens["refresh_token"]).status_code == 401
    assert refresh(client, bob_tokens["refresh_token"]).status_code == 401
