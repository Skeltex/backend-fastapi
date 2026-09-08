from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.core.exceptions.auth_exceptions import (
    AccessDeniedException,
    CredentialsException,
)
from src.core.settings import settings
from src.infrastructure.database import get_db
from src.infrastructure.repositories import UserRepository
from src.schemas.users import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: DbSession
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise CredentialsException()
    except JWTError:
        raise CredentialsException()

    repo = UserRepository(db)
    user = repo.get_by_email_or_username(email="", username=username)

    if user is None or not user.is_active:
        raise CredentialsException(detail="Пользователь не найден или неактивен")

    return user


def get_admin_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Зависимость для эндпоинтов, требующих прав администратора."""
    if not current_user.is_admin:
        raise AccessDeniedException()
    return current_user
