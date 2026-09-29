from sqlalchemy.orm import Session

from src.core.exceptions.domain_exceptions import (
    InactiveUserException,
    WrongCredentialsException,
)
from src.core.logger import logger
from src.core.security import (
    create_access_token,
    rehash_password_if_needed,
    verify_password,
)
from src.infrastructure.repositories import UserRepository


class AuthenticateUserUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def execute(self, username: str, password: str) -> str:
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

        return create_access_token(user.id, user.password)
