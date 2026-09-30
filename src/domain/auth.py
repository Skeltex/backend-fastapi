from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import NoReturn

from sqlalchemy.orm import Session

from src.core.exceptions.domain_exceptions import (
    InactiveUserException,
    InvalidRefreshTokenException,
    WrongCredentialsException,
)
from src.core.logger import logger
from src.core.security import (
    create_access_token,
    generate_refresh_token,
    generate_token_family,
    hash_refresh_token,
    rehash_password_if_needed,
    verify_password,
)
from src.core.settings import settings
from src.infrastructure.models import User
from src.infrastructure.repositories import RefreshTokenRepository, UserRepository


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int


def issue_token_pair(
    tokens: RefreshTokenRepository, user: User, family_id: str | None = None
) -> TokenPair:
    refresh_token = generate_refresh_token()
    tokens.delete_expired_for_user(user.id)
    tokens.create(
        {
            "user_id": user.id,
            "family_id": family_id or generate_token_family(),
            "token_hash": hash_refresh_token(refresh_token),
            "expires_at": datetime.now(UTC)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        }
    )
    return TokenPair(
        access_token=create_access_token(user.id, user.password),
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


class AuthenticateUserUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)
        self.tokens = RefreshTokenRepository(db)

    def execute(self, username: str, password: str) -> TokenPair:
        user = self.repo.get_by_username(username)
        password_is_valid = verify_password(
            password, user.password if user is not None else None
        )

        if user is None or not password_is_valid:
            logger.warning(f"Неудачная попытка входа для пользователя: {username!r}")
            raise WrongCredentialsException()

        if not user.is_active:
            logger.warning(f"Попытка входа в отключенную учетную запись: {username!r}")
            raise InactiveUserException()

        new_hash = rehash_password_if_needed(password, user.password)
        if new_hash is not None:
            self.repo.update(user, {"password": new_hash})
            logger.info(
                f"Хэш пароля пользователя {user.username!r} переведен на bcrypt"
            )

        return issue_token_pair(self.tokens, user)


class RefreshTokensUseCase:
    def __init__(self, db: Session):
        self.users = UserRepository(db)
        self.tokens = RefreshTokenRepository(db)

    def execute(self, refresh_token: str) -> TokenPair:
        stored = self.tokens.get_by_hash(hash_refresh_token(refresh_token))
        if stored is None:
            raise InvalidRefreshTokenException()

        if stored.revoked_at is not None:
            self._revoke_reused(stored.family_id, stored.user_id)

        if stored.expires_at <= datetime.now(UTC):
            raise InvalidRefreshTokenException()

        user = self.users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise InvalidRefreshTokenException()

        if not self.tokens.revoke(stored.id):
            self._revoke_reused(stored.family_id, stored.user_id)

        return issue_token_pair(self.tokens, user, stored.family_id)

    def _revoke_reused(self, family_id: str, user_id: int) -> NoReturn:
        self.tokens.revoke_family(family_id)
        logger.warning(
            f"Повторное использование refresh-токена пользователя {user_id}, "
            "сессия отозвана"
        )
        raise InvalidRefreshTokenException()


class LogoutUseCase:
    def __init__(self, db: Session):
        self.tokens = RefreshTokenRepository(db)

    def execute(self, refresh_token: str) -> None:
        stored = self.tokens.get_by_hash(hash_refresh_token(refresh_token))
        if stored is not None:
            self.tokens.revoke_family(stored.family_id)
