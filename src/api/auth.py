from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from src.api.depends import ClientKey, DbSession, LoginLimiter
from src.core.exceptions.domain_exceptions import WrongCredentialsException
from src.domain.auth import (
    AuthenticateUserUseCase,
    LogoutUseCase,
    RefreshTokensUseCase,
    TokenPair,
)
from src.schemas.auth import RefreshTokenRequest, Token

router = APIRouter()


def to_token(tokens: TokenPair) -> Token:
    return Token(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
    limiter: LoginLimiter,
    client: ClientKey,
):
    with limiter.guard(client, WrongCredentialsException):
        tokens = AuthenticateUserUseCase(db).execute(
            form_data.username, form_data.password
        )
    return to_token(tokens)


@router.post("/refresh", response_model=Token)
def refresh_tokens(data: RefreshTokenRequest, db: DbSession):
    tokens = RefreshTokensUseCase(db).execute(data.refresh_token.get_secret_value())
    return to_token(tokens)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: RefreshTokenRequest, db: DbSession):
    LogoutUseCase(db).execute(data.refresh_token.get_secret_value())
