import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import cache

import bcrypt
import jwt

from src.core.settings import settings

BCRYPT_MAX_PASSWORD_BYTES = 72
DJANGO_PBKDF2_PREFIX = "pbkdf2_sha256$"


@dataclass(frozen=True)
class TokenClaims:
    user_id: int
    password_version: str


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


def password_version(hashed_password: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.get_secret_value().encode("utf-8"),
        hashed_password.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:32]


def create_access_token(user_id: int, hashed_password: str) -> str:
    """Создает JWT токен с временем истечения."""
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {
            "sub": str(user_id),
            "ver": password_version(hashed_password),
            "exp": expire,
        },
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> TokenClaims | None:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub", "ver"]},
        )
        return TokenClaims(
            user_id=int(payload["sub"]), password_version=str(payload["ver"])
        )
    except jwt.InvalidTokenError, TypeError, ValueError:
        return None


def token_matches_password(claims: TokenClaims, hashed_password: str) -> bool:
    return hmac.compare_digest(
        claims.password_version, password_version(hashed_password)
    )


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def generate_token_family() -> str:
    return secrets.token_hex(16)


def hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()


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
