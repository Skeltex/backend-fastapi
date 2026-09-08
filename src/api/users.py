from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.depends import get_admin_user
from src.core.exceptions.domain_exceptions import (
    ItemAlreadyExistsException,
    ItemNotFoundByIdException,
)
from src.domain.users import (
    CreateUserUseCase,
    DeleteUserUseCase,
    GetUsersUseCase,
    GetUserUseCase,
    UpdateUserUseCase,
)
from src.infrastructure.database import get_db
from src.schemas.users import User, UserCreate, UserUpdate

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[User, Depends(get_admin_user)]


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[User])
def get_users(db: DbSession):
    return GetUsersUseCase(db).execute()


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=User)
def get_user(user_id: int, db: DbSession):
    try:
        return GetUserUseCase(db).execute(user_id)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=User)
def create_user(user_in: UserCreate, db: DbSession):
    try:
        return CreateUserUseCase(db).execute(user_in)
    except ItemAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.detail)


@router.put("/{user_id}", status_code=status.HTTP_200_OK, response_model=User)
def update_user(
    user_id: int, user_in: UserUpdate, db: DbSession, current_user: AdminUser
):
    try:
        return UpdateUserUseCase(db).execute(user_id, user_in)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except ItemAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.detail)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: DbSession, current_user: AdminUser):
    try:
        DeleteUserUseCase(db).execute(user_id)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
