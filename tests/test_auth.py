from datetime import UTC, datetime, timedelta

import jwt
import pytest
from pydantic import ValidationError

from src.api.rate_limit import RateLimiter
from src.core.logger import logger
from src.core.settings import Settings
from src.infrastructure.models import User

DJANGO_PASSWORD = "legacy-password"
DJANGO_HASH = (
    "pbkdf2_sha256$1500000$fixedsaltvalue123456$"
    "sZsXC80KtcKfIZJ2kx/PbR4v8HGBt8z4Lyq4tbp3QXo="
)


def login(client, username, password):
    return client.post(
        "/api/v1/auth/token", data={"username": username, "password": password}
    )


def test_login_returns_token_with_user_id(client, create_user):
    user = create_user("alice")

    response = login(client, "alice", "password123")

    assert response.status_code == 200
    token = response.json()["access_token"]
    assert jwt.decode(token, options={"verify_signature": False})["sub"] == str(user.id)


@pytest.mark.parametrize(
    ("username", "password"),
    [("alice", "wrong-password"), ("nobody", "password123"), ("alice", "я" * 40)],
)
def test_login_with_bad_credentials_returns_401(
    client, create_user, username, password
):
    create_user("alice")

    response = login(client, username, password)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_inactive_user_cannot_login(client, create_user):
    create_user("alice", is_active=False)

    assert login(client, "alice", "password123").status_code == 403


def test_failed_logins_are_rate_limited(client, create_user):
    create_user("alice")
    client.app.state.login_limiter = RateLimiter(limit=2, window_seconds=60)

    assert login(client, "alice", "wrong-password").status_code == 401
    assert login(client, "alice", "wrong-password").status_code == 401
    blocked = login(client, "alice", "password123")

    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0


def test_token_signed_with_other_key_is_rejected(client, create_user):
    user = create_user("alice")
    forged = jwt.encode(
        {"sub": str(user.id), "exp": datetime.now(UTC) + timedelta(days=1)},
        "secret-key-for-jwt-token-change-in-production",
        algorithm="HS256",
    )

    response = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {forged}"}
    )

    assert response.status_code == 401


def test_token_stays_bound_to_user_after_rename(client, create_user, auth_headers):
    create_user("admin", is_admin=True)
    carol = create_user("carol")
    carol_headers = auth_headers("carol")

    client.patch(
        f"/api/v1/users/{carol.id}",
        json={"username": "carol_old"},
        headers=auth_headers("admin"),
    )
    create_user("carol")

    response = client.get("/api/v1/users/me", headers=carol_headers)

    assert response.status_code == 200
    assert response.json()["id"] == carol.id


def test_token_of_deleted_user_is_not_reused(client, create_user, auth_headers):
    create_user("admin", is_admin=True)
    bob = create_user("bob")
    bob_headers = auth_headers("bob")

    client.delete(f"/api/v1/users/{bob.id}", headers=auth_headers("admin"))
    newcomer = create_user("newcomer")

    assert newcomer.id != bob.id
    assert client.get("/api/v1/users/me", headers=bob_headers).status_code == 401


def test_admin_password_reset_invalidates_tokens(client, create_user, auth_headers):
    create_user("admin", is_admin=True)
    bob = create_user("bob")
    bob_headers = auth_headers("bob")

    response = client.patch(
        f"/api/v1/users/{bob.id}",
        json={"password": "reset-password"},
        headers=auth_headers("admin"),
    )

    assert response.status_code == 200
    assert client.get("/api/v1/users/me", headers=bob_headers).status_code == 401
    auth_headers("bob", "reset-password")


def test_django_password_hash_is_accepted_and_upgraded(
    client, create_user, session_factory
):
    user = create_user("legacy", password=DJANGO_HASH)

    assert login(client, "legacy", "wrong-password").status_code == 401
    assert login(client, "legacy", DJANGO_PASSWORD).status_code == 200

    with session_factory() as db:
        stored_user = db.get(User, user.id)
    assert stored_user is not None
    assert stored_user.password.startswith("$2")
    assert login(client, "legacy", DJANGO_PASSWORD).status_code == 200


def test_login_log_escapes_control_characters(client, create_user):
    messages: list[str] = []
    sink_id = logger.add(messages.append, format="{message}")
    try:
        login(client, "ghost\n2026-01-01 | INFO | forged", "password123")
    finally:
        logger.remove(sink_id)

    assert messages
    assert all("\n" not in message.rstrip("\n") for message in messages)


def test_secret_key_is_required(monkeypatch):
    monkeypatch.delenv("SECRET_KEY")
    monkeypatch.setitem(Settings.model_config, "env_file", None)

    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize(
    ("algorithm", "key_length", "is_valid"),
    [
        ("HS256", 32, True),
        ("HS384", 32, False),
        ("HS384", 48, True),
        ("HS512", 63, False),
    ],
)
def test_secret_key_length_depends_on_algorithm(algorithm, key_length, is_valid):
    values = {"SECRET_KEY": "k" * key_length, "ALGORITHM": algorithm}

    if is_valid:
        Settings.model_validate(values)
    else:
        with pytest.raises(ValidationError):
            Settings.model_validate(values)


@pytest.mark.parametrize(
    "value", ["http://a.test, http://b.test", '["http://a.test", "http://b.test"]']
)
def test_cors_origins_accept_list_and_json(monkeypatch, value):
    monkeypatch.setenv("CORS_ORIGINS", value)

    assert Settings().CORS_ORIGINS == ["http://a.test", "http://b.test"]
