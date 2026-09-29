from fastapi.testclient import TestClient

from src.core.logger import logger
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


def test_migration_renders_utc_datetime_as_plain_datetime():
    assert render_migration_type("type", UTCDateTime(), None) == "sa.DateTime()"
    assert render_migration_type("column", UTCDateTime(), None) is False
