from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from src.api.depends import DbSession
from src.domain.auth import AuthenticateUserUseCase
from src.schemas.auth import Token

router = APIRouter()


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession
):
    token = AuthenticateUserUseCase(db).execute(form_data.username, form_data.password)
    return Token(access_token=token)
