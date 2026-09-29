import os
import tempfile
from pathlib import Path

TEST_DIR = Path(tempfile.mkdtemp(prefix="blog-tests-"))
os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-32-characters"
os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_DIR / 'default.sqlite3').as_posix()}"
os.environ["LOG_FILE"] = str(TEST_DIR / "app.log")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from utils import now_iso

from src.app import create_app
from src.core.security import get_password_hash
from src.infrastructure.database import Base, create_db_engine, get_db
from src.infrastructure.models import User

PASSWORD = "password123"


@pytest.fixture
def session_factory(tmp_path):
    engine = create_db_engine(f"sqlite:///{(tmp_path / 'test.sqlite3').as_posix()}")
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False)
    engine.dispose()


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
