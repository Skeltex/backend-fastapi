import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from functools import cache

import bcrypt
import jwt

from src.core.settings import settings

BCRYPT_MAX_PASSWORD_BYTES = 72
DJANGO_PBKDF2_PREFIX = "pbkdf2_sha256$"


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Проверяет, совпадает ли введенный пароль с хэшем из БД."""
    if hashed_password is None:
        _check_bcrypt(plain_password, _dummy_hash())
        return False
    if hashed_password.startswith(DJANGO_PBKDF2_PREFIX):
        return _check_django_pbkdf2(plain_password, hashed_password)
    return _check_bcrypt(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Генерирует хэш пароля для сохранения в БД."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def rehash_password_if_needed(plain_password: str, hashed_password: str) -> str | None:
    if hashed_password.startswith("$2"):
        return None
    if len(plain_password.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
        return None
    return get_password_hash(plain_password)


def create_access_token(subject: str) -> str:
    """Создает JWT токен с временем истечения."""
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": subject, "exp": expire},
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        return None
    return payload["sub"]


def _check_bcrypt(plain_password: str, hashed_password: str) -> bool:
    password = plain_password.encode("utf-8")
    if len(password) > BCRYPT_MAX_PASSWORD_BYTES:
        return False
    try:
        return bcrypt.checkpw(password, hashed_password.encode("utf-8"))
    except ValueError:
        return False


def _check_django_pbkdf2(plain_password: str, hashed_password: str) -> bool:
    try:
        _, iterations, salt, expected = hashed_password.split("$", 3)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        )
    except ValueError:
        return False
    return hmac.compare_digest(base64.b64encode(digest).decode("ascii"), expected)


@cache
def _dummy_hash() -> str:
    return get_password_hash(secrets.token_urlsafe(16))
