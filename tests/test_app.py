import pytest
from fastapi.testclient import TestClient
from utils import now_iso

from src.core.logger import logger
from src.infrastructure import database
from src.infrastructure.models import Category, User
from src.infrastructure.repositories import CategoryRepository, PostRepository
from src.infrastructure.types import UTCDateTime, render_migration_type


def test_health_endpoint(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unhandled_errors_are_logged_and_hidden(client):
    def fail():
        raise RuntimeError("secret details")

    client.app.add_api_route("/api/v1/fail", fail)
    messages: list[str] = []
    sink_id = logger.add(messages.append, format="{message}")
    try:
        response = TestClient(client.app, raise_server_exceptions=False).get(
            "/api/v1/fail"
        )
    finally:
        logger.remove(sink_id)

    assert response.status_code == 500
    assert response.json() == {"detail": "Внутренняя ошибка сервера"}
    assert any("/api/v1/fail" in message for message in messages)


def test_streamed_request_body_is_limited(client, create_user, auth_headers):
    create_user("alice")

    def chunks():
        yield b'{"title": "t", "text": "'
        for _ in range(20):
            yield b"x" * 100_000
        yield b'", "pub_date": "2999-01-01T00:00:00Z"}'

    response = client.post(
        "/api/v1/posts/",
        content=chunks(),
        headers={**auth_headers("alice"), "Content-Type": "application/json"},
    )

    assert response.status_code == 413


def delete_after_loading(monkeypatch, session_factory, repository, model, item_id):
    original = repository.get_by_id

    def get_then_delete(self, requested_id):
        item = original(self, requested_id)
        with session_factory() as other:
            other.delete(other.get(model, item_id))
            other.commit()
        return item

    monkeypatch.setattr(repository, "get_by_id", get_then_delete)


def test_update_of_concurrently_deleted_category_returns_404(
    client, create_user, auth_headers, session_factory, monkeypatch
):
    create_user("admin", is_admin=True)
    headers = auth_headers("admin")
    category = client.post(
        "/api/v1/categories/",
        json={"title": "Категория", "description": "Описание", "slug": "news"},
        headers=headers,
    ).json()
    delete_after_loading(
        monkeypatch, session_factory, CategoryRepository, Category, category["id"]
    )

    response = client.patch(
        f"/api/v1/categories/{category['id']}", json={"title": "Новая"}, headers=headers
    )

    assert response.status_code == 404


def test_update_of_post_removed_with_its_author_returns_404(
    client, create_user, auth_headers, session_factory, monkeypatch
):
    create_user("admin", is_admin=True)
    author = create_user("alice")
    post = client.post(
        "/api/v1/posts/",
        json={"title": "Заголовок", "text": "Текст", "pub_date": now_iso()},
        headers=auth_headers("alice"),
    ).json()
    admin_headers = auth_headers("admin")
    delete_after_loading(monkeypatch, session_factory, PostRepository, User, author.id)

    response = client.patch(
        f"/api/v1/posts/{post['id']}", json={"text": "Правка"}, headers=admin_headers
    )

    assert response.status_code == 404


def test_unwritable_database_directory_is_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(database.os, "access", lambda path, mode: False)

    with pytest.raises(PermissionError, match="Нет прав на запись"):
        database.create_db_engine(f"sqlite:///{(tmp_path / 'db.sqlite3').as_posix()}")


def test_migration_renders_utc_datetime_as_plain_datetime():
    assert render_migration_type("type", UTCDateTime(), None) == "sa.DateTime()"
    assert render_migration_type("column", UTCDateTime(), None) is False
