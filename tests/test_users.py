import pytest

USERS_URL = "/api/v1/users/"


def register(client, **fields):
    payload = {"username": "alice", "password": "password123"}
    payload.update(fields)
    return client.post(USERS_URL, json=payload)


def test_register_user(client):
    response = register(client, email="Alice@Example.com")

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
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
    ],
)
def test_register_rejects_invalid_data(client, fields):
    assert register(client, **fields).status_code == 422


@pytest.mark.parametrize(
    "fields", [{"username": "ALICE"}, {"username": "bob", "email": "ALICE@example.com"}]
)
def test_register_rejects_case_insensitive_duplicates(client, fields):
    register(client, email="alice@example.com")

    assert register(client, **fields).status_code == 409


def test_public_user_list_hides_private_fields(client, create_user):
    create_user("alice", is_admin=True, email="alice@example.com")

    response = client.get(USERS_URL)

    assert response.status_code == 200
    user = response.json()[0]
    assert set(user) == {"id", "username", "first_name", "last_name", "created_at"}


def test_user_can_update_own_profile(client, create_user, auth_headers):
    create_user("alice")
    headers = auth_headers("alice")

    response = client.patch(
        f"{USERS_URL}me",
        json={"first_name": "Алиса", "password": "new-password", "is_admin": True},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Алиса"
    assert response.json()["is_admin"] is False
    auth_headers("alice", "new-password")


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
