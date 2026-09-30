import hashlib
import sys
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import MetaData, create_engine, insert, select, text
from sqlalchemy.exc import OperationalError

from scripts import transfer_sqlite_to_postgres as transfer_script
from src.core.security import get_password_hash, hash_refresh_token
from src.infrastructure.database import Base
from src.infrastructure.models import NOT_EMPTY_EMAIL

INITIAL_REVISION = "8f41f800dc74"
MOMENT = datetime(2026, 9, 1, 12, 30, 15, 123456, tzinfo=UTC)
EXPECTED_COUNTS = {
    "auth_user": 3,
    "blog_category": 2,
    "blog_location": 1,
    "blog_post": 2,
    "blog_comment": 1,
    "auth_refresh_token": 1,
}
NEXT_IDS = {
    "auth_user": 13,
    "blog_category": 5,
    "blog_location": 3,
    "blog_post": 12,
    "blog_comment": 2,
    "auth_refresh_token": 2,
}


def sqlite_metadata() -> MetaData:
    metadata = MetaData()
    for table in Base.metadata.sorted_tables:
        table.to_metadata(metadata)
    users = metadata.tables["auth_user"]
    users.dialect_kwargs["sqlite_autoincrement"] = True
    for index in users.indexes:
        if index.name == "uq_auth_user_email":
            index.dialect_kwargs["sqlite_where"] = NOT_EMPTY_EMAIL
    return metadata


def user(user_id: int, username: str, **fields) -> dict:
    return {
        "id": user_id,
        "username": username,
        "username_key": username.casefold(),
        "email": "",
        "first_name": None,
        "last_name": None,
        "password": get_password_hash("password123"),
        "is_active": True,
        "is_superuser": False,
        "date_joined": MOMENT,
    } | fields


@pytest.fixture
def source_path(tmp_path):
    path = tmp_path / "старая база" / "db.sqlite3"
    path.parent.mkdir()
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    metadata = sqlite_metadata()
    metadata.create_all(engine)
    tables = metadata.tables
    with engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)")
        )
        connection.execute(
            text("INSERT INTO alembic_version VALUES (:revision)"),
            {"revision": transfer_script.head_revision()},
        )
        connection.execute(
            insert(tables["auth_user"]),
            [
                user(5, "Alice", first_name="Алиса"),
                user(6, "bob", is_active=False),
                user(7, "carol", email="carol@example.com", is_superuser=True),
                user(12, "removed"),
            ],
        )
        connection.execute(text("DELETE FROM auth_user WHERE id = 12"))
        connection.execute(
            insert(tables["blog_category"]),
            [
                {
                    "id": 3,
                    "title": "Новости",
                    "description": "",
                    "slug": "news",
                    "is_published": True,
                    "created_at": MOMENT,
                },
                {
                    "id": 4,
                    "title": "Черновики",
                    "description": "Скрыто",
                    "slug": "drafts",
                    "is_published": False,
                    "created_at": MOMENT,
                },
            ],
        )
        connection.execute(
            insert(tables["blog_location"]),
            [{"id": 2, "name": "Москва", "is_published": True, "created_at": MOMENT}],
        )
        connection.execute(
            insert(tables["blog_post"]),
            [
                {
                    "id": 10,
                    "title": "Пост",
                    "text": "Текст",
                    "pub_date": MOMENT,
                    "image": "https://example.com/a.png",
                    "is_published": True,
                    "created_at": MOMENT,
                    "author_id": 5,
                    "category_id": 3,
                    "location_id": 2,
                },
                {
                    "id": 11,
                    "title": "Отложенный",
                    "text": "Позже",
                    "pub_date": MOMENT + timedelta(days=365),
                    "image": None,
                    "is_published": False,
                    "created_at": MOMENT,
                    "author_id": 6,
                    "category_id": None,
                    "location_id": None,
                },
            ],
        )
        connection.execute(
            insert(tables["blog_comment"]),
            [
                {
                    "id": 1,
                    "text": "Комментарий",
                    "created_at": MOMENT,
                    "author_id": 6,
                    "post_id": 10,
                }
            ],
        )
        connection.execute(
            insert(tables["auth_refresh_token"]),
            [
                {
                    "id": 1,
                    "user_id": 5,
                    "family_id": "f" * 32,
                    "token_hash": hash_refresh_token("token"),
                    "expires_at": MOMENT + timedelta(days=30),
                    "revoked_at": None,
                    "created_at": MOMENT,
                }
            ],
        )
    engine.dispose()
    return path


def change_source(path, statement: str) -> None:
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    with engine.begin() as connection:
        connection.execute(text(statement))
    engine.dispose()


def table_rows(engine) -> dict[str, list[dict]]:
    with engine.connect() as connection:
        return {
            table.name: [
                dict(row._mapping)
                for row in connection.execute(select(table).order_by(table.c.id))
            ]
            for table in Base.metadata.sorted_tables
        }


def file_hash(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_transfer_copies_all_rows_and_advances_sequences(
    client, test_engine, source_path
):
    source = transfer_script.open_read_only(source_path)
    try:
        counts = transfer_script.transfer(source, test_engine)
        source_rows = table_rows(source)
    finally:
        source.dispose()

    assert counts == EXPECTED_COUNTS
    assert table_rows(test_engine) == source_rows
    with test_engine.begin() as connection:
        next_ids = {
            table: connection.execute(
                text("SELECT nextval(pg_get_serial_sequence(:table, 'id'))"),
                {"table": table},
            ).scalar()
            for table in NEXT_IDS
        }
    assert next_ids == NEXT_IDS

    response = client.post(
        "/api/v1/auth/token", data={"username": "Alice", "password": "password123"}
    )
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert client.get("/api/v1/users/me", headers=headers).json()["id"] == 5
    assert [post["id"] for post in client.get("/api/v1/posts/").json()] == [10]


def test_transfer_does_not_modify_source(source_path):
    before = file_hash(source_path)
    source = transfer_script.open_read_only(source_path)
    try:
        with (
            pytest.raises(OperationalError, match="readonly"),
            source.begin() as connection,
        ):
            connection.execute(text("DELETE FROM auth_user"))
    finally:
        source.dispose()

    assert file_hash(source_path) == before


def test_transfer_requires_same_schema_revision(
    session_factory, test_engine, source_path
):
    change_source(
        source_path, f"UPDATE alembic_version SET version_num = '{INITIAL_REVISION}'"
    )
    source = transfer_script.open_read_only(source_path)
    try:
        with pytest.raises(RuntimeError, match=f"SQLite на ревизии {INITIAL_REVISION}"):
            transfer_script.transfer(source, test_engine)
    finally:
        source.dispose()


def test_transfer_refuses_to_mix_data(create_user, test_engine, source_path):
    create_user("existing")
    source = transfer_script.open_read_only(source_path)
    try:
        with pytest.raises(RuntimeError, match="auth_user"):
            transfer_script.transfer(source, test_engine)
    finally:
        source.dispose()

    assert [row["username"] for row in table_rows(test_engine)["auth_user"]] == [
        "existing"
    ]


def test_failed_transfer_leaves_postgres_empty(
    session_factory, test_engine, source_path
):
    change_source(
        source_path, f"UPDATE blog_post SET title = '{'x' * 257}' WHERE id = 11"
    )
    source = transfer_script.open_read_only(source_path)
    try:
        with pytest.raises(RuntimeError, match="blog_post: value too long"):
            transfer_script.transfer(source, test_engine)
    finally:
        source.dispose()

    assert all(not rows for rows in table_rows(test_engine).values())


def test_main_reports_counts(session_factory, source_path, monkeypatch, capsys):
    before = file_hash(source_path)
    monkeypatch.setattr(sys, "argv", ["transfer", str(source_path)])

    transfer_script.main()

    assert capsys.readouterr().out.splitlines() == [
        f"{table.name}: {EXPECTED_COUNTS[table.name]}"
        for table in Base.metadata.sorted_tables
    ]
    assert file_hash(source_path) == before


def test_main_explains_failures(session_factory, source_path, tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["transfer", str(tmp_path / "missing.sqlite3")])
    with pytest.raises(SystemExit, match="не найден"):
        transfer_script.main()

    change_source(source_path, "DROP TABLE alembic_version")
    monkeypatch.setattr(sys, "argv", ["transfer", str(source_path)])
    with pytest.raises(SystemExit) as error:
        transfer_script.main()
    assert str(error.value).startswith(
        "Перенос отменен, PostgreSQL не изменен. Схема SQLite на ревизии None"
    )
