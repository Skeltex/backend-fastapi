import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from utils import now_iso

from src.core.logger import logger
from src.core.settings import Settings
from src.infrastructure.database import create_db_engine, get_db

MAX_ID = 2**31 - 1
MAX_OFFSET = 2**63 - 1
NUL = "до\x00после"
LIST_URLS = (
    "/api/v1/posts/",
    "/api/v1/comments/",
    "/api/v1/categories/",
    "/api/v1/locations/",
    "/api/v1/users/",
)


def test_database_password_is_required(settings_env):
    settings_env.delenv("POSTGRES_PASSWORD")

    with pytest.raises(ValidationError, match="POSTGRES_PASSWORD"):
        Settings()


def test_database_url_is_built_from_postgres_settings(settings_env):
    settings_env.setenv("DATABASE_URL", " ")
    settings_env.setenv("POSTGRES_PASSWORD", "p@ss:w/rd#?%")
    settings_env.setenv("POSTGRES_HOST", "db")
    settings_env.setenv("POSTGRES_PORT", "5433")

    url = Settings().database_url

    assert url.drivername == "postgresql+psycopg"
    assert (url.username, url.password, url.host, url.port, url.database) == (
        "blog",
        "p@ss:w/rd#?%",
        "db",
        5433,
        "blog",
    )
    assert make_url(url.render_as_string(hide_password=False)) == url


@pytest.mark.parametrize(
    "scheme", ["postgres", "postgresql", "postgresql+psycopg", "postgresql+psycopg2"]
)
def test_database_url_always_uses_psycopg(settings_env, scheme):
    settings_env.delenv("POSTGRES_PASSWORD")
    settings_env.setenv(
        "DATABASE_URL", f"{scheme}://user:secret@example.test:6543/blog"
    )

    url = Settings().database_url

    assert (
        url.render_as_string(hide_password=False)
        == "postgresql+psycopg://user:secret@example.test:6543/blog"
    )


@pytest.mark.parametrize(
    "value",
    [
        "sqlite:///data/db.sqlite3",
        "mysql://user:Qz7secret@example.test/blog",
        "postgresql://user:Qz7secret@example.test:port/blog",
        "Qz7secret",
    ],
)
def test_invalid_database_url_is_rejected_without_leaking_it(settings_env, value):
    settings_env.setenv("DATABASE_URL", value)

    with pytest.raises(ValidationError, match="DATABASE_URL") as error:
        Settings()

    assert "Qz7secret" not in str(error.value)


def is_validation_error(response) -> bool:
    return response.status_code == 422 and isinstance(response.json()["detail"], list)


def test_identifiers_are_limited_to_postgres_integer(
    client, create_user, auth_headers, create_post
):
    create_user("admin", is_admin=True)
    headers = auth_headers("admin")
    post = create_post(headers)
    post_fields = {"title": "t", "text": "t", "pub_date": now_iso()}

    for url in LIST_URLS:
        assert client.get(f"{url}{MAX_ID}", headers=headers).status_code == 404
        assert is_validation_error(client.get(f"{url}{MAX_ID + 1}", headers=headers))
    for method, url, payload in (
        ("post", "/api/v1/posts/", post_fields | {"category_id": MAX_ID + 1}),
        ("post", "/api/v1/posts/", post_fields | {"location_id": MAX_ID + 1}),
        ("patch", f"/api/v1/posts/{post['id']}", {"category_id": MAX_ID + 1}),
        ("post", "/api/v1/comments/", {"text": "t", "post_id": MAX_ID + 1}),
    ):
        response = client.request(method, url, json=payload, headers=headers)
        assert is_validation_error(response), (url, response.text)
    missing = client.post(
        "/api/v1/posts/", json=post_fields | {"category_id": MAX_ID}, headers=headers
    )
    assert missing.status_code == 400


def test_offset_is_limited_to_postgres_bigint(client, create_user, auth_headers):
    create_user("admin", is_admin=True)
    headers = auth_headers("admin")

    for url in LIST_URLS:
        response = client.get(url, params={"offset": MAX_OFFSET}, headers=headers)
        assert (response.status_code, response.json()) == (200, [])
        response = client.get(url, params={"offset": MAX_OFFSET + 1}, headers=headers)
        assert is_validation_error(response)


def test_nul_characters_are_rejected_before_reaching_database(
    client, create_user, auth_headers, create_post
):
    create_user("admin", is_admin=True)
    headers = auth_headers("admin")
    post = create_post(headers)

    requests = [
        (
            "post",
            "/api/v1/users/",
            {"username": "bob", "password": "password123", "first_name": NUL},
        ),
        ("post", "/api/v1/users/", {"username": "bob", "password": "pass\x00word123"}),
        ("patch", "/api/v1/users/me", {"last_name": NUL}),
        (
            "post",
            "/api/v1/categories/",
            {"title": "К", "description": NUL, "slug": "news"},
        ),
        ("post", "/api/v1/locations/", {"name": NUL}),
        (
            "post",
            "/api/v1/posts/",
            {"title": NUL, "text": "Текст", "pub_date": now_iso()},
        ),
        (
            "patch",
            f"/api/v1/posts/{post['id']}",
            {"image_url": f"https://example.com/{NUL}"},
        ),
        ("post", "/api/v1/comments/", {"text": NUL, "post_id": post["id"]}),
        ("post", "/api/v1/auth/refresh", {"refresh_token": NUL}),
        ("post", "/api/v1/auth/logout", {"refresh_token": NUL}),
    ]
    for method, url, payload in requests:
        response = client.request(method, url, json=payload, headers=headers)
        assert response.status_code == 422, (url, response.text)
        messages = [error["msg"] for error in response.json()["detail"]]
        assert any("недопустимые символы" in message for message in messages), url


@pytest.mark.parametrize(
    ("username", "password"),
    [("ali\x00ce", "password123"), ("alice", "password\x00123"), ("\x00", "\x00")],
)
def test_login_with_nul_characters_is_rejected(client, create_user, username, password):
    create_user("alice")

    response = client.post(
        "/api/v1/auth/token", data={"username": username, "password": password}
    )

    assert response.status_code == 401


def test_maximum_field_lengths_fit_database_columns(client, create_user, auth_headers):
    create_user("admin", is_admin=True)
    headers = auth_headers("admin")
    email = "a" * 64 + "@" + "b" * 63 + "." + "c" * 63 + "." + "d" * 57 + ".com"

    user = client.post(
        "/api/v1/users/",
        json={
            "username": "Ю" * 150,
            "email": email,
            "first_name": "И" * 150,
            "last_name": "Ф" * 150,
            "password": "п" * 36,
        },
    )
    category = client.post(
        "/api/v1/categories/",
        json={"title": "К" * 256, "description": "О" * 10_000, "slug": "s" * 64},
        headers=headers,
    )
    location = client.post(
        "/api/v1/locations/", json={"name": "М" * 256}, headers=headers
    )
    assert (user.status_code, category.status_code, location.status_code) == (
        201,
        201,
        201,
    )

    post = client.post(
        "/api/v1/posts/",
        json={
            "title": "З" * 256,
            "text": "Т" * 50_000,
            "pub_date": now_iso(),
            "image_url": "https://example.com/" + "x" * 2028,
            "category_id": category.json()["id"],
            "location_id": location.json()["id"],
        },
        headers=headers,
    )
    assert post.status_code == 201, post.text
    comment = client.post(
        "/api/v1/comments/",
        json={"text": "К" * 5_000, "post_id": post.json()["id"]},
        headers=headers,
    )
    assert comment.status_code == 201, comment.text
    assert (
        client.post(
            "/api/v1/auth/token", data={"username": "Ю" * 150, "password": "п" * 36}
        ).status_code
        == 200
    )


def test_values_rejected_by_database_return_422(client, session_factory):
    def out_of_range():
        with session_factory() as db:
            db.execute(text("SELECT CAST(:value AS integer)"), {"value": MAX_OFFSET})

    client.app.add_api_route("/api/v1/out-of-range", out_of_range)
    messages: list[str] = []
    sink_id = logger.add(messages.append, format="{message}")
    try:
        response = client.get("/api/v1/out-of-range")
    finally:
        logger.remove(sink_id)

    assert response.status_code == 422
    assert response.json() == {"detail": "Недопустимые данные в запросе"}
    assert any("integer out of range" in message for message in messages)
    assert all(str(MAX_OFFSET) not in message for message in messages)


def test_unavailable_database_returns_503(client, test_engine):
    missing = create_db_engine(
        test_engine.url.set(database=f"{test_engine.url.database}_missing")
    )

    def unavailable_db():
        with Session(missing) as db:
            yield db

    client.app.dependency_overrides[get_db] = unavailable_db
    messages: list[str] = []
    sink_id = logger.add(messages.append, format="{message}")
    try:
        response = client.get("/api/v1/health")
    finally:
        logger.remove(sink_id)
        missing.dispose()

    assert response.status_code == 503
    assert response.json() == {"detail": "База данных временно недоступна"}
    assert any("/api/v1/health" in message for message in messages)
    assert all(str(test_engine.url.password) not in message for message in messages)
