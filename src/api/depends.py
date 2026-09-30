from typing import Annotated

from fastapi import Depends, Path, Query, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.api.rate_limit import RateLimiter
from src.core.exceptions.auth_exceptions import (
    AccessDeniedException,
    CredentialsException,
)
from src.core.security import decode_access_token, token_matches_password
from src.infrastructure.database import get_db
from src.infrastructure.models import User
from src.infrastructure.repositories import UserRepository
from src.schemas.common import MAX_ID, PaginationParams

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]
Pagination = Annotated[PaginationParams, Query()]
PathId = Annotated[int, Path(ge=1, le=MAX_ID)]


def get_optional_user(
    token: Annotated[str | None, Depends(oauth2_scheme)], db: DbSession
) -> User | None:
    if token is None:
        return None

    claims = decode_access_token(token)
    if claims is None:
        raise CredentialsException()

    user = UserRepository(db).get_by_id(claims.user_id)
    if user is None or not user.is_active:
        raise CredentialsException(detail="Пользователь не найден или неактивен")
    if not token_matches_password(claims, user.password):
        raise CredentialsException(detail="Токен устарел, выполните вход заново")

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


def get_client_key(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


def get_login_limiter(request: Request) -> RateLimiter:
    return request.app.state.login_limiter


def get_conflict_limiter(request: Request) -> RateLimiter:
    return request.app.state.conflict_limiter


OptionalUser = Annotated[User | None, Depends(get_optional_user)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(get_admin_user)]
ClientKey = Annotated[str, Depends(get_client_key)]
LoginLimiter = Annotated[RateLimiter, Depends(get_login_limiter)]
ConflictLimiter = Annotated[RateLimiter, Depends(get_conflict_limiter)]
