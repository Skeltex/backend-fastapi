from datetime import UTC, datetime, timedelta
from pathlib import Path

from alembic.config import Config
from sqlalchemy import URL, create_engine, text

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def future_iso(days: int = 1) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


def alembic_config(url: URL) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR).replace("%", "%%"))
    config.attributes["database_url"] = url.render_as_string(hide_password=False)
    return config


def _execute_on_server(url: URL, *statements: str) -> None:
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as connection:
            for statement in statements:
                connection.execute(text(statement))
    finally:
        admin.dispose()


def _quoted_name(url: URL) -> str:
    return '"' + (url.database or "").replace('"', '""') + '"'


def recreate_database(url: URL) -> None:
    name = _quoted_name(url)
    _execute_on_server(
        url, f"DROP DATABASE IF EXISTS {name} WITH (FORCE)", f"CREATE DATABASE {name}"
    )


def drop_database(url: URL) -> None:
    _execute_on_server(url, f"DROP DATABASE IF EXISTS {_quoted_name(url)} WITH (FORCE)")
