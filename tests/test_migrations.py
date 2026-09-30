import io
import logging
import unicodedata

import pytest
from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, create_engine, inspect, text
from utils import alembic_config

INITIAL_REVISION = "8f41f800dc74"


@pytest.fixture
def config(empty_database):
    return alembic_config(empty_database)


@pytest.fixture
def engine(empty_database):
    engine = create_engine(empty_database)
    yield engine
    engine.dispose()


def current_revision(engine) -> str | None:
    with engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def insert_ignoring_foreign_keys(connection: Connection, *statements: str) -> None:
    foreign_keys = [
        (table, foreign_key)
        for table in ("blog_post", "blog_comment")
        for foreign_key in inspect(connection).get_foreign_keys(table)
    ]
    for table, foreign_key in foreign_keys:
        connection.execute(
            text(f'ALTER TABLE {table} DROP CONSTRAINT "{foreign_key["name"]}"')
        )
    for statement in statements:
        connection.execute(text(statement))
    for table, foreign_key in foreign_keys:
        connection.execute(
            text(
                f'ALTER TABLE {table} ADD CONSTRAINT "{foreign_key["name"]}" '
                f"FOREIGN KEY ({foreign_key['constrained_columns'][0]}) "
                f"REFERENCES {foreign_key['referred_table']} (id) NOT VALID"
            )
        )


def test_migrations_match_models_and_clean_orphans(config, engine, caplog):
    command.upgrade(config, INITIAL_REVISION)

    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO auth_user (id, username, email, password, is_active, is_superuser) "
                "VALUES (1, 'alice', '', 'hash', NULL, NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO auth_user (id, username, email, password) "
                "VALUES (2, :username, :email, 'hash')"
            ),
            {
                "username": unicodedata.normalize("NFD", "José"),
                "email": "Mixed@Example.COM",
            },
        )
        insert_ignoring_foreign_keys(
            connection,
            "INSERT INTO blog_post (id, title, text, pub_date, author_id, category_id, location_id) "
            "VALUES (1, 'Пост', 'Текст', '2026-01-01 00:00:00', 1, 0, 0)",
            "INSERT INTO blog_post (id, title, text, pub_date, author_id) "
            "VALUES (2, 'Сирота', 'Текст', '2026-01-01 00:00:00', 99)",
            "INSERT INTO blog_post (id, title, text, pub_date, author_id) "
            "VALUES (3, 'Без категории', 'Текст', '2026-01-01 00:00:00', 1)",
            "INSERT INTO blog_comment (id, text, author_id, post_id) "
            "VALUES (1, 'Висячий', 1, 0)",
            "INSERT INTO blog_comment (id, text, author_id, post_id) "
            "VALUES (2, 'Нормальный', 1, 1)",
        )

    command.upgrade(config, "head")
    command.check(config)

    assert [
        record.getMessage()
        for record in caplog.records
        if record.levelno == logging.WARNING
    ] == [
        "Удалено публикаций несуществующих авторов: 1",
        "Сброшена ссылка на несуществующую категорию у публикаций: 1",
        "Сброшена ссылка на несуществующее местоположение у публикаций: 1",
        "Удалено комментариев к несуществующим публикациям или авторам: 1",
    ]
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT id, category_id, location_id FROM blog_post ORDER BY id")
        ).all() == [(1, None, None), (3, None, None)]
        assert connection.execute(text("SELECT id FROM blog_comment")).all() == [(2,)]
        assert connection.execute(
            text(
                "SELECT is_active, is_superuser, date_joined IS NOT NULL "
                "FROM auth_user WHERE id = 1"
            )
        ).all() == [(True, False, True)]
        assert connection.execute(
            text("SELECT username, username_key, email FROM auth_user WHERE id = 2")
        ).all() == [(unicodedata.normalize("NFC", "José"), "josé", "mixed@example.com")]
        assert not connection.execute(
            text("SELECT conname FROM pg_constraint WHERE NOT convalidated")
        ).all()
        inspector = inspect(connection)
        actions = {
            (foreign_key["referred_table"], foreign_key["options"].get("ondelete"))
            for table in ("blog_post", "blog_comment", "auth_refresh_token")
            for foreign_key in inspector.get_foreign_keys(table)
        }
    assert actions == {
        ("auth_user", "CASCADE"),
        ("blog_category", "SET NULL"),
        ("blog_location", "SET NULL"),
        ("blog_post", "CASCADE"),
    }


@pytest.mark.parametrize(
    ("field", "values", "duplicate"),
    [
        ("username", ("Bob", "bob"), "bob"),
        ("email", ("Ann@Example.com", "ann@example.com"), "ann@example.com"),
    ],
)
def test_migrations_stop_on_case_insensitive_duplicates(
    config, engine, field, values, duplicate
):
    command.upgrade(config, INITIAL_REVISION)
    with engine.begin() as connection:
        for number, value in enumerate(values):
            user = {"username": f"user{number}", "email": f"user{number}@example.com"}
            connection.execute(
                text(
                    "INSERT INTO auth_user (username, email, password) "
                    "VALUES (:username, :email, 'hash')"
                ),
                user | {field: value},
            )

    with pytest.raises(RuntimeError, match=duplicate):
        command.upgrade(config, "head")

    assert current_revision(engine) == INITIAL_REVISION
    with engine.connect() as connection:
        columns = {
            column["name"] for column in inspect(connection).get_columns("auth_user")
        }
        foreign_keys = inspect(connection).get_foreign_keys("blog_post")
    assert "username_key" not in columns
    assert all(not foreign_key["options"] for foreign_key in foreign_keys)


def test_migrations_can_be_rolled_back(config, engine):
    command.upgrade(config, "head")
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO auth_user (username, username_key, email, password, "
                "is_active, is_superuser, date_joined) "
                "VALUES ('alice', 'alice', '', 'hash', true, false, now())"
            )
        )

    command.downgrade(config, INITIAL_REVISION)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT username FROM auth_user")).all() == [
            ("alice",)
        ]

    command.downgrade(config, "base")
    with engine.connect() as connection:
        assert inspect(connection).get_table_names() == ["alembic_version"]

    command.upgrade(config, "head")
    command.check(config)


def test_offline_sql_creates_the_same_schema(config, engine):
    config.output_buffer = io.StringIO()
    command.upgrade(config, "head", sql=True)
    script = config.output_buffer.getvalue()

    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.exec_driver_sql(script)

    assert (
        current_revision(engine)
        == ScriptDirectory.from_config(config).get_current_head()
    )
    command.check(config)
