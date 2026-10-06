import functools
import os
import shutil
import tempfile
from pathlib import Path

TEST_DIR = Path(tempfile.mkdtemp(prefix="blog-tests-"))
os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-32-characters"
os.environ["LOG_FILE"] = str(TEST_DIR / "app.log")
os.environ["MEDIA_DIR"] = str(TEST_DIR / "media")

import bcrypt
import pytest
from alembic import command
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import URL, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from utils import alembic_config, drop_database, now_iso, recreate_database

from src.core.settings import Settings, settings

TEST_DATABASE_URL = settings.database_url.set(
    database=f"{settings.database_url.database}_test"
)
settings.DATABASE_URL = SecretStr(
    TEST_DATABASE_URL.render_as_string(hide_password=False)
)

from src.app import create_app
from src.core.logger import logger
from src.core.security import get_password_hash
from src.infrastructure import database
from src.infrastructure.database import Base, create_db_engine, get_db
from src.infrastructure.models import User

PASSWORD = "password123"
TABLES = ", ".join(table.name for table in Base.metadata.sorted_tables)
DATABASE_SETTINGS = (
    "DATABASE_URL",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
)


def pytest_sessionfinish(session, exitstatus):
    logger.remove()
    database.engine.dispose()
    shutil.rmtree(TEST_DIR, ignore_errors=True)


@pytest.fixture(autouse=True, scope="session")
def fast_password_hashing():
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(bcrypt, "gensalt", functools.partial(bcrypt.gensalt, rounds=4))
        yield


@pytest.fixture
def settings_env(monkeypatch):
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    for name in DATABASE_SETTINGS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("POSTGRES_PASSWORD", "db-password")
    return monkeypatch


def create_test_database(url: URL) -> None:
    try:
        recreate_database(url)
    except OperationalError as error:
        reason = str(error.orig).partition("\n")[0]
        pytest.exit(
            f"Не удалось подключиться к PostgreSQL {url.host}:{url.port} ({reason}). "
            "Запустите базу: docker compose up -d db",
            returncode=1,
        )


@pytest.fixture(scope="session")
def test_engine():
    create_test_database(TEST_DATABASE_URL)
    command.upgrade(alembic_config(TEST_DATABASE_URL), "head")
    engine = create_db_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()
    drop_database(TEST_DATABASE_URL)


@pytest.fixture
def empty_database():
    url = TEST_DATABASE_URL.set(database=f"{TEST_DATABASE_URL.database}_empty")
    create_test_database(url)
    yield url
    drop_database(url)


@pytest.fixture
def session_factory(test_engine):
    with test_engine.begin() as connection:
        connection.execute(text("SET LOCAL lock_timeout = '5s'"))
        connection.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))
    return sessionmaker(bind=test_engine, autoflush=False)


@pytest.fixture
def client(session_factory):
    app = create_app()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def create_user(session_factory):
    def factory(
        username: str,
        *,
        is_admin: bool = False,
        is_active: bool = True,
        password: str = PASSWORD,
        email: str = "",
    ) -> User:
        with session_factory() as db:
            user = User(
                username=username,
                email=email,
                password=password
                if password.startswith("pbkdf2_")
                else get_password_hash(password),
                is_admin=is_admin,
                is_active=is_active,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            db.expunge(user)
            return user

    return factory


@pytest.fixture
def auth_headers(client):
    def factory(username: str, password: str = PASSWORD) -> dict[str, str]:
        response = client.post(
            "/api/v1/auth/token", data={"username": username, "password": password}
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return factory


@pytest.fixture
def create_post(client):
    def factory(headers: dict[str, str], **fields) -> dict:
        payload = {"title": "Заголовок", "text": "Текст", "pub_date": now_iso()}
        payload.update(fields)
        response = client.post("/api/v1/posts/", json=payload, headers=headers)
        assert response.status_code == 201, response.text
        return response.json()

    return factory
