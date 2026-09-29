from fastapi import APIRouter, status

from src.api.depends import AdminUser, CurrentUser, DbSession, Pagination
from src.domain.users import (
    CreateUserUseCase,
    DeleteUserUseCase,
    GetUsersUseCase,
    GetUserUseCase,
    UpdateUserUseCase,
)
from src.schemas.users import User, UserAdminUpdate, UserCreate, UserPublic, UserUpdate

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[UserPublic])
def get_users(db: DbSession, pagination: Pagination):
    return GetUsersUseCase(db).execute(pagination.offset, pagination.limit)


@router.get("/me", status_code=status.HTTP_200_OK, response_model=User)
def get_me(current_user: CurrentUser):
    return current_user


@router.patch("/me", status_code=status.HTTP_200_OK, response_model=User)
def update_me(user_in: UserUpdate, db: DbSession, current_user: CurrentUser):
    return UpdateUserUseCase(db).execute(current_user.id, user_in)


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserPublic)
def get_user(user_id: int, db: DbSession):
    return GetUserUseCase(db).execute(user_id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=User)
def create_user(user_in: UserCreate, db: DbSession):
    return CreateUserUseCase(db).execute(user_in)


@router.patch("/{user_id}", status_code=status.HTTP_200_OK, response_model=User)
def update_user(
    user_id: int, user_in: UserAdminUpdate, db: DbSession, current_user: AdminUser
):
    return UpdateUserUseCase(db).execute(user_id, user_in)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: DbSession, current_user: AdminUser):
    DeleteUserUseCase(db).execute(user_id)
