from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.infrastructure.database import get_db
from src.infrastructure.repositories import UserRepository
from src.schemas.users import User, UserCreate, UserUpdate

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[User])
def get_users(db: DbSession):
    repo = UserRepository(db)
    return repo.get_all()


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=User)
def get_user(user_id: int, db: DbSession):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )
    return user


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=User)
def create_user(user_in: UserCreate, db: DbSession):
    repo = UserRepository(db)
    if repo.get_by_email_or_username(user_in.email, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email или username уже существует",
        )
    return repo.create(user_in)


@router.put("/{user_id}", status_code=status.HTTP_200_OK, response_model=User)
def update_user(user_id: int, user_in: UserUpdate, db: DbSession):
    repo = UserRepository(db)
    user = repo.update(user_id, user_in)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: DbSession):
    repo = UserRepository(db)
    if not repo.delete(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )
