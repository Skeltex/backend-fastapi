import sqlite3
import unicodedata
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
INITIAL_REVISION = "8f41f800dc74"


def make_config(tmp_path):
    database_path = tmp_path / "migrations.sqlite3"
    config = Config(str(ALEMBIC_INI))
    config.attributes["database_url"] = f"sqlite:///{database_path.as_posix()}"
    return config, database_path


def test_migrations_match_models_and_clean_orphans(tmp_path):
    config, database_path = make_config(tmp_path)
    command.upgrade(config, INITIAL_REVISION)

    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            INSERT INTO auth_user (id, username, email, password, is_active, is_superuser)
            VALUES (1, 'alice', '', 'hash', NULL, NULL);
            INSERT INTO blog_post (id, title, text, pub_date, author_id, category_id, location_id)
            VALUES (1, 'Пост', 'Текст', '2026-01-01 00:00:00', 1, 0, 0);
            INSERT INTO blog_post (id, title, text, pub_date, author_id)
            VALUES (2, 'Сирота', 'Текст', '2026-01-01 00:00:00', 99);
            INSERT INTO blog_comment (id, text, author_id, post_id) VALUES (1, 'Висячий', 1, 0);
            INSERT INTO blog_comment (id, text, author_id, post_id) VALUES (2, 'Нормальный', 1, 1);
            """
        )
        connection.execute(
            "INSERT INTO auth_user (id, username, email, password) VALUES (2, ?, ?, 'hash')",
            (unicodedata.normalize("NFD", "José"), "Mixed@Example.COM"),
        )

    command.upgrade(config, "head")
    command.check(config)

    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT id, category_id, location_id FROM blog_post"
        ).fetchall() == [(1, None, None)]
        assert connection.execute("SELECT id FROM blog_comment").fetchall() == [(2,)]
        assert connection.execute(
            "SELECT is_active, is_superuser, date_joined IS NOT NULL "
            "FROM auth_user WHERE id = 1"
        ).fetchall() == [(1, 0, 1)]
        assert connection.execute(
            "SELECT username, username_key, email FROM auth_user WHERE id = 2"
        ).fetchall() == [
            (unicodedata.normalize("NFC", "José"), "josé", "mixed@example.com")
        ]
        actions = {
            (row[2], row[6])
            for table in ("blog_post", "blog_comment")
            for row in connection.execute(f"PRAGMA foreign_key_list({table})")
        }
    assert actions == {
        ("auth_user", "CASCADE"),
        ("blog_category", "SET NULL"),
        ("blog_location", "SET NULL"),
        ("blog_post", "CASCADE"),
    }


def test_migrations_report_case_insensitive_duplicates(tmp_path):
    config, database_path = make_config(tmp_path)
    command.upgrade(config, INITIAL_REVISION)

    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            INSERT INTO auth_user (username, email, password) VALUES ('Bob', '', 'hash');
            INSERT INTO auth_user (username, email, password) VALUES ('bob', '', 'hash');
            """
        )

    with pytest.raises(RuntimeError, match="bob"):
        command.upgrade(config, "head")


def test_migrations_can_be_rolled_back(tmp_path):
    config, _ = make_config(tmp_path)

    command.upgrade(config, "head")
    command.downgrade(config, INITIAL_REVISION)
    command.upgrade(config, "head")
    command.check(config)
