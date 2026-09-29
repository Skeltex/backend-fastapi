COMMENTS_URL = "/api/v1/comments/"


def add_comment(client, headers, post_id, text="Комментарий"):
    return client.post(
        COMMENTS_URL, json={"text": text, "post_id": post_id}, headers=headers
    )


def test_create_comment(client, create_user, auth_headers, create_post):
    alice = create_user("alice")
    headers = auth_headers("alice")
    post = create_post(headers)

    response = add_comment(client, headers, post["id"], text="  Комментарий  ")

    assert response.status_code == 201
    assert response.json()["author_id"] == alice.id
    assert response.json()["text"] == "Комментарий"


def test_comment_requires_visible_post(client, create_user, auth_headers, create_post):
    create_user("alice")
    create_user("bob")
    hidden = create_post(auth_headers("alice"), is_published=False)
    bob_headers = auth_headers("bob")

    for post_id in (hidden["id"], 12345):
        assert add_comment(client, bob_headers, post_id).status_code == 400
    assert add_comment(client, bob_headers, 10**20).status_code == 422


def test_comment_text_is_validated(client, create_user, auth_headers, create_post):
    create_user("alice")
    headers = auth_headers("alice")
    post = create_post(headers)
    comment = add_comment(client, headers, post["id"]).json()

    assert add_comment(client, headers, post["id"], text="").status_code == 422
    assert add_comment(client, headers, post["id"], text="   ").status_code == 422
    assert add_comment(client, headers, post["id"], text="x" * 5_001).status_code == 422
    null = client.patch(
        f"{COMMENTS_URL}{comment['id']}", json={"text": None}, headers=headers
    )
    assert null.status_code == 422


def test_only_author_or_admin_can_delete_comment(
    client, create_user, auth_headers, create_post
):
    create_user("alice")
    create_user("bob")
    create_user("admin", is_admin=True)
    headers = auth_headers("alice")
    post = create_post(headers)
    comment = add_comment(client, headers, post["id"]).json()
    url = f"{COMMENTS_URL}{comment['id']}"

    assert client.delete(url, headers=auth_headers("bob")).status_code == 403
    assert client.delete(url, headers=auth_headers("admin")).status_code == 204


def test_deleting_post_removes_comments(client, create_user, auth_headers, create_post):
    create_user("alice")
    create_user("admin", is_admin=True)
    headers = auth_headers("alice")
    post = create_post(headers)
    add_comment(client, headers, post["id"])

    client.delete(f"/api/v1/posts/{post['id']}", headers=headers)

    assert client.get(COMMENTS_URL, headers=auth_headers("admin")).json() == []


def test_comments_of_hidden_posts_are_not_listed(
    client, create_user, auth_headers, create_post
):
    create_user("alice")
    headers = auth_headers("alice")
    post = create_post(headers)
    add_comment(client, headers, post["id"])

    client.patch(
        f"/api/v1/posts/{post['id']}", json={"is_published": False}, headers=headers
    )

    assert client.get(COMMENTS_URL).json() == []
    assert len(client.get(COMMENTS_URL, headers=headers).json()) == 1


def test_comment_author_keeps_access_after_post_is_hidden(
    client, create_user, auth_headers, create_post
):
    create_user("alice")
    create_user("bob")
    create_user("carol")
    alice_headers = auth_headers("alice")
    bob_headers = auth_headers("bob")
    post = create_post(alice_headers)
    comment = add_comment(client, bob_headers, post["id"]).json()
    url = f"{COMMENTS_URL}{comment['id']}"

    client.patch(
        f"/api/v1/posts/{post['id']}",
        json={"is_published": False},
        headers=alice_headers,
    )

    assert client.get(url, headers=bob_headers).status_code == 200
    assert [
        item["id"] for item in client.get(COMMENTS_URL, headers=bob_headers).json()
    ] == [comment["id"]]
    assert (
        client.patch(url, json={"text": "Правка"}, headers=bob_headers).status_code
        == 200
    )
    assert client.get(url, headers=auth_headers("carol")).status_code == 404
    assert client.delete(url, headers=auth_headers("carol")).status_code == 404
