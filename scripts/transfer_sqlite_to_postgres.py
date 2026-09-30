import sqlite3
import sys
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import (
    Connection,
    Engine,
    Table,
    create_engine,
    func,
    inspect,
    select,
    text,
)
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from src.core.settings import BASE_DIR
from src.infrastructure.database import engine
from src.infrastructure.models import Base

DEFAULT_SOURCE = BASE_DIR / "data" / "db.sqlite3"
ALEMBIC_INI = BASE_DIR / "alembic.ini"
BATCH_SIZE = 1000


def head_revision() -> str | None:
    return ScriptDirectory.from_config(Config(str(ALEMBIC_INI))).get_current_head()


def schema_revision(connection: Connection) -> str | None:
    return MigrationContext.configure(connection).get_current_revision()


def sqlite_sequences(connection: Connection) -> dict[str, int]:
    if not inspect(connection).has_table("sqlite_sequence"):
        return {}
    rows = connection.execute(text("SELECT name, seq FROM sqlite_sequence"))
    return {name: seq for name, seq in rows}


def copy_table(
    source: Connection, target: Connection, table: Table, last_id: int
) -> int:
    result = source.execution_options(yield_per=BATCH_SIZE).execute(
        select(table).order_by(table.c.id)
    )
    count = 0
    for partition in result.partitions():
        rows = [dict(row._mapping) for row in partition]
        target.execute(table.insert(), rows)
        count += len(rows)
        last_id = max(last_id, rows[-1]["id"])
    if last_id:
        target.execute(
            select(func.setval(func.pg_get_serial_sequence(table.name, "id"), last_id))
        )
    return count


def transfer(source: Engine, target: Engine) -> dict[str, int]:
    head = head_revision()
    tables = Base.metadata.sorted_tables
    with source.connect() as source_connection, target.begin() as target_connection:
        for name, connection in (
            ("SQLite", source_connection),
            ("PostgreSQL", target_connection),
        ):
            revision = schema_revision(connection)
            if revision != head:
                raise RuntimeError(
                    f"Схема {name} на ревизии {revision}, а перенос рассчитан на {head}. "
                    "Примените миграции: alembic upgrade head"
                )

        for table in tables:
            if target_connection.execute(
                select(func.count()).select_from(table)
            ).scalar():
                raise RuntimeError(
                    f"Таблица {table.name} в PostgreSQL уже содержит данные"
                )

        sequences = sqlite_sequences(source_connection)
        counts = {}
        for table in tables:
            try:
                counts[table.name] = copy_table(
                    source_connection,
                    target_connection,
                    table,
                    sequences.get(table.name, 0),
                )
            except (DBAPIError, ValueError) as error:
                reason = error.orig if isinstance(error, DBAPIError) else error
                raise RuntimeError(
                    f"Не удалось перенести таблицу {table.name}: {reason}"
                ) from error
        return counts


def open_read_only(path: Path) -> Engine:
    uri = f"{path.resolve().as_uri()}?mode=ro"
    return create_engine("sqlite://", creator=lambda: sqlite3.connect(uri, uri=True))


def main() -> None:
    source_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    if not source_path.is_file():
        raise SystemExit(f"Файл {source_path} не найден")

    source = open_read_only(source_path)
    try:
        counts = transfer(source, engine)
    except RuntimeError as error:
        raise SystemExit(f"Перенос отменен, PostgreSQL не изменен. {error}") from None
    except SQLAlchemyError as error:
        reason = error.orig if isinstance(error, DBAPIError) else error
        raise SystemExit(f"Перенос отменен, PostgreSQL не изменен. {reason}") from None
    finally:
        source.dispose()

    for table_name, count in counts.items():
        print(f"{table_name}: {count}")


if __name__ == "__main__":
    main()
