import unicodedata

import pytest

from src.api.rate_limit import RateLimiter
from src.infrastructure.repositories import UserRepository

USERS_URL = "/api/v1/users/"


def register(client, **fields):
    payload = {"username": "alice", "password": "password123"}
    payload.update(fields)
    return client.post(USERS_URL, json=payload)


def test_register_user(client):
    response = register(client, email="Alice@Example.com", first_name="  Алиса  ")

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert body["first_name"] == "Алиса"
    assert "password" not in body
    assert body["created_at"].endswith("Z")


@pytest.mark.parametrize(
    "fields",
    [
        {"username": ""},
        {"username": "with space"},
        {"username": "x" * 151},
        {"password": "short"},
        {"password": "пароль" * 7},
        {"first_name": "x" * 151},
        {"is_admin": True},
    ],
)
def test_register_rejects_invalid_data(client, fields):
    assert register(client, **fields).status_code == 422


@pytest.mark.parametrize(
    "body",
    [
        b'{"username": "alice", "password": "password123", "first_name": "\\ud800"}',
        b'{"username": "alice", "password": "password123", "\\ud800": 1}',
        b'{"username": "alice", "password": "pass\\udfffword"}',
    ],
)
def test_register_rejects_lone_surrogates(client, body):
    response = client.post(
        USERS_URL, content=body, headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422


def test_validation_errors_do_not_echo_input(client):
    response = register(client, password="Secret1")

    assert response.status_code == 422
    assert "Secret1" not in response.text


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ({"username": "alice"}, {"username": "ALICE"}),
        ({"username": "Иван"}, {"username": "иван"}),
        (
            {"username": unicodedata.normalize("NFC", "José")},
            {"username": unicodedata.normalize("NFD", "José")},
        ),
        (
            {"username": "alice", "email": "alice@example.com"},
            {"username": "bob", "email": "ALICE@example.com"},
        ),
    ],
)
def test_register_rejects_equivalent_duplicates(client, first, second):
    assert register(client, **first).status_code == 201

    assert register(client, **second).status_code == 409


def test_register_race_is_resolved_by_database(client, monkeypatch):
    register(client)
    original = UserRepository.username_exists
    calls = []

    def skip_first_check(self, username, exclude_id=None):
        calls.append(username)
        return False if len(calls) == 1 else original(self, username, exclude_id)

    monkeypatch.setattr(UserRepository, "username_exists", skip_first_check)

    response = register(client, username="ALICE")

    assert response.status_code == 409
    assert "ALICE" in response.json()["detail"]


def test_registration_conflicts_are_rate_limited(client):
    client.app.state.conflict_limiter = RateLimiter(limit=2, window_seconds=60)
    register(client)

    assert register(client).status_code == 409
    assert register(client).status_code == 409
    assert register(client, username="someone-else").status_code == 429


def test_public_user_list_hides_private_fields_and_inactive_users(client, create_user):
    create_user("alice", is_admin=True, email="alice@example.com")
    create_user("bob", is_active=False)

    response = client.get(USERS_URL)

    assert response.status_code == 200
    assert [user["username"] for user in response.json()] == ["alice"]
    assert set(response.json()[0]) == {
        "id",
        "username",
        "first_name",
        "last_name",
        "created_at",
    }


def test_admin_sees_private_fields_of_all_users(client, create_user, auth_headers):
    create_user("admin", is_admin=True, email="admin@example.com")
    bob = create_user("bob", is_active=False)
    headers = auth_headers("admin")

    users = client.get(USERS_URL, headers=headers).json()
    bob_details = client.get(f"{USERS_URL}{bob.id}", headers=headers).json()

    assert {user["username"] for user in users} == {"admin", "bob"}
    assert {"email", "is_active", "is_admin"} <= set(users[0])
    assert bob_details["is_active"] is False
    assert client.get(f"{USERS_URL}{bob.id}").status_code == 404


def test_user_can_update_own_profile(client, create_user, auth_headers):
    create_user("alice")
    headers = auth_headers("alice")

    response = client.patch(
        f"{USERS_URL}me",
        json={
            "first_name": "Алиса",
            "password": "new-password",
            "current_password": "password123",
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Алиса"
    assert response.json()["is_admin"] is False
    assert client.get(f"{USERS_URL}me", headers=headers).status_code == 401
    auth_headers("alice", "new-password")


def test_password_change_requires_valid_current_password(
    client, create_user, auth_headers
):
    create_user("alice")
    headers = auth_headers("alice")

    missing = client.patch(
        f"{USERS_URL}me", json={"password": "new-password"}, headers=headers
    )
    wrong = client.patch(
        f"{USERS_URL}me",
        json={"password": "new-password", "current_password": "wrong-password"},
        headers=headers,
    )

    assert missing.status_code == 422
    assert wrong.status_code == 400
    auth_headers("alice")


def test_self_update_rejects_privileged_and_unknown_fields(
    client, create_user, auth_headers
):
    create_user("alice")
    headers = auth_headers("alice")

    for payload in ({"is_admin": True}, {"is_active": False}, {"nickname": "a"}):
        response = client.patch(f"{USERS_URL}me", json=payload, headers=headers)
        assert response.status_code == 422


def test_user_update_rejects_null_and_taken_email(client, create_user, auth_headers):
    create_user("alice")
    create_user("bob", email="bob@example.com")
    headers = auth_headers("alice")

    null_response = client.patch(
        f"{USERS_URL}me", json={"username": None}, headers=headers
    )
    email_response = client.patch(
        f"{USERS_URL}me", json={"email": "BOB@example.com"}, headers=headers
    )

    assert null_response.status_code == 422
    assert email_response.status_code == 409


def test_only_admin_can_update_other_users(client, create_user, auth_headers):
    create_user("admin", is_admin=True)
    create_user("alice")
    bob = create_user("bob")

    forbidden = client.patch(
        f"{USERS_URL}{bob.id}", json={"is_admin": True}, headers=auth_headers("alice")
    )
    allowed = client.patch(
        f"{USERS_URL}{bob.id}", json={"is_active": False}, headers=auth_headers("admin")
    )

    assert forbidden.status_code == 403
    assert allowed.status_code == 200
    assert allowed.json()["is_active"] is False


def test_last_admin_cannot_be_demoted_deactivated_or_deleted(
    client, create_user, auth_headers
):
    admin = create_user("admin", is_admin=True)
    headers = auth_headers("admin")
    url = f"{USERS_URL}{admin.id}"

    assert (
        client.patch(url, json={"is_admin": False}, headers=headers).status_code == 409
    )
    assert (
        client.patch(url, json={"is_active": False}, headers=headers).status_code == 409
    )
    assert client.delete(url, headers=headers).status_code == 409

    create_user("second_admin", is_admin=True)
    assert (
        client.patch(url, json={"is_admin": False}, headers=headers).status_code == 200
    )


def test_deleting_user_removes_their_posts_and_comments(
    client, create_user, auth_headers, create_post
):
    admin = create_user("admin", is_admin=True)
    bob = create_user("bob")
    admin_headers = auth_headers("admin")
    bob_post = create_post(auth_headers("bob"))
    admin_post = create_post(admin_headers)
    client.post(
        "/api/v1/comments/",
        json={"text": "Комментарий", "post_id": admin_post["id"]},
        headers=auth_headers("bob"),
    )

    assert (
        client.delete(f"{USERS_URL}{bob.id}", headers=admin_headers).status_code == 204
    )

    assert (
        client.get(f"/api/v1/posts/{bob_post['id']}", headers=admin_headers).status_code
        == 404
    )
    assert client.get("/api/v1/comments/", headers=admin_headers).json() == []
    assert client.get(f"{USERS_URL}{admin.id}").status_code == 200
