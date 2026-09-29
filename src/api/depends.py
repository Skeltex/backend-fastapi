from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.core.exceptions.auth_exceptions import (
    AccessDeniedException,
    CredentialsException,
)
from src.core.security import decode_access_token
from src.infrastructure.database import get_db
from src.infrastructure.models import User
from src.infrastructure.repositories import UserRepository
from src.schemas.common import PaginationParams

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]
Pagination = Annotated[PaginationParams, Query()]


def get_optional_user(
    token: Annotated[str | None, Depends(oauth2_scheme)], db: DbSession
) -> User | None:
    if token is None:
        return None

    subject = decode_access_token(token)
    try:
        user_id = int(subject) if subject is not None else None
    except ValueError:
        user_id = None
    if user_id is None:
        raise CredentialsException()

    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise CredentialsException(detail="Пользователь не найден или неактивен")

    return user


def get_current_user(
    user: Annotated[User | None, Depends(get_optional_user)],
) -> User:
    if user is None:
        raise CredentialsException()
    return user


def get_admin_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Зависимость для эндпоинтов, требующих прав администратора."""
    if not current_user.is_admin:
        raise AccessDeniedException()
    return current_user


OptionalUser = Annotated[User | None, Depends(get_optional_user)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(get_admin_user)]
