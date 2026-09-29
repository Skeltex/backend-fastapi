from datetime import UTC, datetime, timedelta, timezone

from utils import future_iso, now_iso

POSTS_URL = "/api/v1/posts/"


def test_create_post_uses_current_user_as_author(
    client, create_user, auth_headers, create_post
):
    alice = create_user("alice")

    post = create_post(auth_headers("alice"))

    assert post["author_id"] == alice.id


def test_create_post_rejects_unknown_relations(client, create_user, auth_headers):
    create_user("alice")
    headers = auth_headers("alice")
    payload = {"title": "Заголовок", "text": "Текст", "pub_date": now_iso()}

    for field in ("category_id", "location_id"):
        response = client.post(
            POSTS_URL, json={**payload, field: 12345}, headers=headers
        )
        assert response.status_code == 400


def test_pub_date_is_stored_in_utc(client, create_user, auth_headers, create_post):
    create_user("alice")
    local_time = (datetime.now(UTC) + timedelta(days=1)).replace(microsecond=0)
    moscow_time = local_time.astimezone(timezone(timedelta(hours=3)))

    post = create_post(auth_headers("alice"), pub_date=moscow_time.isoformat())

    assert datetime.fromisoformat(post["pub_date"]) == local_time
    assert post["pub_date"].endswith("Z")


def test_create_post_rejects_invalid_data(client, create_user, auth_headers):
    create_user("alice")
    headers = auth_headers("alice")
    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()

    for payload in (
        {"title": "", "text": "Текст", "pub_date": now_iso()},
        {"title": "Заголовок", "text": "", "pub_date": now_iso()},
        {"title": "Заголовок", "text": "Текст", "pub_date": past},
        {"title": "Заголовок", "text": "Текст", "pub_date": now_iso(), "image_url": 1},
    ):
        assert client.post(POSTS_URL, json=payload, headers=headers).status_code == 422


def test_update_post_rejects_null_for_required_fields(
    client, create_user, auth_headers, create_post
):
    create_user("alice")
    headers = auth_headers("alice")
    post = create_post(headers)

    for field in ("title", "text", "pub_date", "is_published"):
        response = client.patch(
            f"{POSTS_URL}{post['id']}", json={field: None}, headers=headers
        )
        assert response.status_code == 422


def test_only_author_or_admin_can_modify_post(
    client, create_user, auth_headers, create_post
):
    create_user("alice")
    create_user("bob")
    create_user("admin", is_admin=True)
    post = create_post(auth_headers("alice"))
    url = f"{POSTS_URL}{post['id']}"

    bob_response = client.patch(
        url, json={"text": "Чужой"}, headers=auth_headers("bob")
    )
    admin_response = client.patch(
        url, json={"text": "Админ"}, headers=auth_headers("admin")
    )

    assert bob_response.status_code == 403
    assert admin_response.status_code == 200
    assert client.delete(url, headers=auth_headers("bob")).status_code == 403


def test_hidden_posts_are_visible_only_to_author_and_admin(
    client, create_user, auth_headers, create_post
):
    create_user("alice")
    create_user("bob")
    create_user("admin", is_admin=True)
    alice_headers = auth_headers("alice")
    visible = create_post(alice_headers)
    unpublished = create_post(alice_headers, is_published=False)
    delayed = create_post(alice_headers, pub_date=future_iso())

    def ids(headers=None):
        return {post["id"] for post in client.get(POSTS_URL, headers=headers).json()}

    hidden = {unpublished["id"], delayed["id"]}
    assert ids() == {visible["id"]}
    assert ids(auth_headers("bob")) == {visible["id"]}
    assert ids(alice_headers) == {visible["id"]} | hidden
    assert ids(auth_headers("admin")) == {visible["id"]} | hidden
    assert client.get(f"{POSTS_URL}{unpublished['id']}").status_code == 404


def test_post_in_unpublished_category_is_hidden(
    client, create_user, auth_headers, create_post
):
    create_user("admin", is_admin=True)
    create_user("alice")
    admin_headers = auth_headers("admin")
    category = client.post(
        "/api/v1/categories/",
        json={"title": "Скрытая", "description": "Описание", "slug": "hidden"},
        headers=admin_headers,
    ).json()
    post = create_post(auth_headers("alice"), category_id=category["id"])

    client.patch(
        f"/api/v1/categories/{category['id']}",
        json={"is_published": False},
        headers=admin_headers,
    )

    assert client.get(f"{POSTS_URL}{post['id']}").status_code == 404


def test_deleting_category_and_location_clears_post_relations(
    client, create_user, auth_headers, create_post
):
    create_user("admin", is_admin=True)
    headers = auth_headers("admin")
    category = client.post(
        "/api/v1/categories/",
        json={"title": "Категория", "description": "Описание", "slug": "news"},
        headers=headers,
    ).json()
    location = client.post(
        "/api/v1/locations/", json={"name": "Москва"}, headers=headers
    ).json()
    post = create_post(headers, category_id=category["id"], location_id=location["id"])

    client.delete(f"/api/v1/categories/{category['id']}", headers=headers)
    client.delete(f"/api/v1/locations/{location['id']}", headers=headers)

    updated = client.get(f"{POSTS_URL}{post['id']}", headers=headers).json()
    assert updated["category_id"] is None
    assert updated["location_id"] is None


def test_posts_are_paginated(client, create_user, auth_headers, create_post):
    create_user("alice")
    headers = auth_headers("alice")
    created = [create_post(headers)["id"] for _ in range(3)]

    page = client.get(POSTS_URL, params={"offset": 1, "limit": 1}).json()

    assert [post["id"] for post in page] == [created[1]]
    assert client.get(POSTS_URL, params={"limit": 101}).status_code == 422
