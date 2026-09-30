import os
from pathlib import Path

from sqlalchemy import Engine, MetaData, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.core.settings import settings

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def create_db_engine(url: str) -> Engine:
    database_url = make_url(url)
    if database_url.get_backend_name() != "sqlite":
        return create_engine(database_url, hide_parameters=True)

    if database_url.database and database_url.database != ":memory:":
        _prepare_sqlite_file(Path(database_url.database))

    engine = create_engine(
        database_url,
        hide_parameters=True,
        connect_args={"check_same_thread": False},
    )
    event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def _prepare_sqlite_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    targets = [path.parent, path] if path.exists() else [path.parent]
    for target in targets:
        if not os.access(target, os.W_OK):
            raise PermissionError(
                f"Нет прав на запись в {target}: база данных SQLite недоступна. "
                "Проверьте владельца и права каталога с базой"
            )


def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


engine = create_db_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
