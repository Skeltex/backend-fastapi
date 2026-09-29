from datetime import UTC, datetime, timedelta

import jwt
import pytest
from pydantic import ValidationError

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


def test_secret_key_is_required(monkeypatch):
    monkeypatch.delenv("SECRET_KEY")
    monkeypatch.setitem(Settings.model_config, "env_file", None)

    with pytest.raises(ValidationError):
        Settings()
