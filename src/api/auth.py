from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.domain.auth import AuthenticateUserUseCase, WrongCredentialsException
from src.infrastructure.database import get_db
from src.schemas.auth import Token

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession
):
    use_case = AuthenticateUserUseCase(db)
    try:
        token = use_case.execute(form_data.username, form_data.password)
        return Token(access_token=token)
    except WrongCredentialsException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
