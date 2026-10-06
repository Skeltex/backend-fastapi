import re

import pytest
from utils import now_iso

from src.core.settings import settings

POSTS_URL = "/api/v1/posts/"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 64
GIF = b"GIF89a" + b"\x00" * 64


def upload(client, post_id, data, headers, filename="photo.png"):
    return client.post(
        f"{POSTS_URL}{post_id}/image",
        files={"image": (filename, data)},
        headers=headers,
    )


def stored_file(image_url):
    return settings.MEDIA_DIR / image_url.removeprefix("/media/")


def media_files():
    return set(settings.MEDIA_DIR.rglob("*.*"))


@pytest.mark.parametrize(
    ("data", "extension", "content_type"),
    [
        (PNG, "png", "image/png"),
        (JPEG, "jpg", "image/jpeg"),
        (WEBP, "webp", "image/webp"),
        (GIF, "gif", "image/gif"),
    ],
)
def test_author_uploads_image_and_it_is_served(
    client, create_user, auth_headers, create_post, data, extension, content_type
):
    create_user("alice")
    headers = auth_headers("alice")
    post = create_post(headers)

    response = upload(client, post["id"], data, headers, filename="photo.txt")

    assert response.status_code == 200
    image_url = response.json()["image_url"]
    assert re.fullmatch(rf"/media/posts/[0-9a-f]{{32}}\.{extension}", image_url)
    assert client.get(f"{POSTS_URL}{post['id']}").json()["image_url"] == image_url
    served = client.get(image_url)
    assert served.status_code == 200
    assert served.content == data
    assert served.headers["content-type"] == content_type


def test_old_image_file_is_removed_when_replaced_or_cleared(
    client, create_user, auth_headers, create_post
):
    create_user("alice")
    headers = auth_headers("alice")
    post = create_post(headers)
    url = f"{POSTS_URL}{post['id']}"

    first = upload(client, post["id"], PNG, headers).json()["image_url"]
    second = upload(client, post["id"], JPEG, headers).json()["image_url"]
    assert not stored_file(first).exists()
    assert stored_file(second).exists()

    client.patch(url, json={"text": "Правка"}, headers=headers)
    assert stored_file(second).exists()

    response = client.patch(url, json={"image_url": None}, headers=headers)
    assert response.json()["image_url"] is None
    assert not stored_file(second).exists()

    third = upload(client, post["id"], PNG, headers).json()["image_url"]
    external = "https://example.com/picture.png"
    response = client.patch(url, json={"image_url": external}, headers=headers)
    assert response.json()["image_url"] == external
    assert not stored_file(third).exists()


def test_image_files_are_removed_with_post_and_author(
    client, create_user, auth_headers, create_post
):
    create_user("admin", is_admin=True)
    bob = create_user("bob")
    headers = auth_headers("bob")
    first = create_post(headers)
    second = create_post(headers)
    first_image = upload(client, first["id"], PNG, headers).json()["image_url"]
    second_image = upload(client, second["id"], PNG, headers).json()["image_url"]

    client.delete(f"{POSTS_URL}{first['id']}", headers=headers)
    assert not stored_file(first_image).exists()
    assert stored_file(second_image).exists()

    client.delete(f"/api/v1/users/{bob.id}", headers=auth_headers("admin"))
    assert not stored_file(second_image).exists()


def test_invalid_uploads_are_rejected_without_saving_files(
    client, create_user, auth_headers, create_post, monkeypatch
):
    create_user("alice")
    create_user("bob")
    headers = auth_headers("alice")
    post = create_post(headers)
    before = media_files()

    assert (
        upload(client, post["id"], b"<svg onload=alert(1)>", headers).status_code == 422
    )
    assert upload(client, post["id"], b"", headers).status_code == 422
    assert upload(client, post["id"], PNG, auth_headers("bob")).status_code == 403
    assert upload(client, post["id"], PNG, {}).status_code == 401
    assert upload(client, 12345, PNG, headers).status_code == 404
    assert (
        client.post(
            f"{POSTS_URL}{post['id']}/image", data={"image": "text"}, headers=headers
        ).status_code
        == 422
    )
    too_big = PNG + b"\x00" * (settings.MAX_IMAGE_BYTES + 100_000)
    assert upload(client, post["id"], too_big, headers).status_code == 413

    monkeypatch.setattr(settings, "MAX_IMAGE_BYTES", len(PNG) - 1)
    response = upload(client, post["id"], PNG, headers)
    assert response.status_code == 413
    assert "МБ" in response.json()["detail"]

    assert media_files() == before
    assert client.get(f"{POSTS_URL}{post['id']}").json()["image_url"] is None


@pytest.mark.parametrize(
    "image_url",
    [
        "/media/posts/0123456789abcdef0123456789abcdef.png",
        "/MEDIA/posts/0123456789abcdef0123456789abcdef.png",
        "/media/other.png",
    ],
)
def test_uploaded_image_paths_cannot_be_set_through_json(
    client, create_user, auth_headers, create_post, image_url
):
    create_user("alice")
    headers = auth_headers("alice")
    post = create_post(headers)
    payload = {
        "title": "Заголовок",
        "text": "Текст",
        "pub_date": now_iso(),
        "image_url": image_url,
    }

    assert client.post(POSTS_URL, json=payload, headers=headers).status_code == 422
    assert (
        client.patch(
            f"{POSTS_URL}{post['id']}", json={"image_url": image_url}, headers=headers
        ).status_code
        == 422
    )
