COMMENTS_URL = "/api/v1/comments/"


def test_create_comment(client, create_user, auth_headers, create_post):
    alice = create_user("alice")
    headers = auth_headers("alice")
    post = create_post(headers)

    response = client.post(
        COMMENTS_URL,
        json={"text": "Комментарий", "post_id": post["id"]},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["author_id"] == alice.id


def test_comment_requires_visible_post(client, create_user, auth_headers, create_post):
    create_user("alice")
    create_user("bob")
    hidden = create_post(auth_headers("alice"), is_published=False)
    bob_headers = auth_headers("bob")

    for post_id in (hidden["id"], 12345):
        response = client.post(
            COMMENTS_URL,
            json={"text": "Комментарий", "post_id": post_id},
            headers=bob_headers,
        )
        assert response.status_code == 400


def test_comment_text_is_validated(client, create_user, auth_headers, create_post):
    create_user("alice")
    headers = auth_headers("alice")
    post = create_post(headers)
    comment = client.post(
        COMMENTS_URL,
        json={"text": "Комментарий", "post_id": post["id"]},
        headers=headers,
    ).json()

    empty = client.post(
        COMMENTS_URL, json={"text": "", "post_id": post["id"]}, headers=headers
    )
    null = client.patch(
        f"{COMMENTS_URL}{comment['id']}", json={"text": None}, headers=headers
    )

    assert empty.status_code == 422
    assert null.status_code == 422


def test_only_author_or_admin_can_delete_comment(
    client, create_user, auth_headers, create_post
):
    create_user("alice")
    create_user("bob")
    create_user("admin", is_admin=True)
    headers = auth_headers("alice")
    post = create_post(headers)
    comment = client.post(
        COMMENTS_URL,
        json={"text": "Комментарий", "post_id": post["id"]},
        headers=headers,
    ).json()
    url = f"{COMMENTS_URL}{comment['id']}"

    assert client.delete(url, headers=auth_headers("bob")).status_code == 403
    assert client.delete(url, headers=auth_headers("admin")).status_code == 204


def test_deleting_post_removes_comments(client, create_user, auth_headers, create_post):
    create_user("alice")
    create_user("admin", is_admin=True)
    headers = auth_headers("alice")
    post = create_post(headers)
    client.post(
        COMMENTS_URL,
        json={"text": "Комментарий", "post_id": post["id"]},
        headers=headers,
    )

    client.delete(f"/api/v1/posts/{post['id']}", headers=headers)

    assert client.get(COMMENTS_URL, headers=auth_headers("admin")).json() == []


def test_comments_of_hidden_posts_are_not_listed(
    client, create_user, auth_headers, create_post
):
    create_user("alice")
    headers = auth_headers("alice")
    post = create_post(headers)
    client.post(
        COMMENTS_URL,
        json={"text": "Комментарий", "post_id": post["id"]},
        headers=headers,
    )

    client.patch(
        f"/api/v1/posts/{post['id']}", json={"is_published": False}, headers=headers
    )

    assert client.get(COMMENTS_URL).json() == []
    assert len(client.get(COMMENTS_URL, headers=headers).json()) == 1
