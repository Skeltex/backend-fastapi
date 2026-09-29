from fastapi import APIRouter, status

from src.api.depends import (
    AdminUser,
    ClientKey,
    ConflictLimiter,
    CurrentUser,
    DbSession,
    LoginLimiter,
    OptionalUser,
    Pagination,
    PathId,
)
from src.core.exceptions.domain_exceptions import (
    InvalidCurrentPasswordException,
    ItemAlreadyExistsException,
)
from src.domain.common import get_user_id, is_admin
from src.domain.users import (
    CreateUserUseCase,
    DeleteUserUseCase,
    GetUsersUseCase,
    GetUserUseCase,
    UpdateCurrentUserUseCase,
    UpdateUserUseCase,
)
from src.schemas.users import (
    User,
    UserAdminUpdate,
    UserCreate,
    UserPublic,
    UserSelfUpdate,
)

router = APIRouter()


@router.get(
    "/", status_code=status.HTTP_200_OK, response_model=list[User] | list[UserPublic]
)
def get_users(db: DbSession, viewer: OptionalUser, pagination: Pagination):
    users = GetUsersUseCase(db).execute(viewer, pagination.offset, pagination.limit)
    schema = User if is_admin(viewer) else UserPublic
    return [schema.model_validate(user, from_attributes=True) for user in users]


@router.get("/me", status_code=status.HTTP_200_OK, response_model=User)
def get_me(current_user: CurrentUser):
    return current_user


@router.patch("/me", status_code=status.HTTP_200_OK, response_model=User)
def update_me(
    user_in: UserSelfUpdate,
    db: DbSession,
    current_user: CurrentUser,
    login_limiter: LoginLimiter,
    conflict_limiter: ConflictLimiter,
    client: ClientKey,
):
    with (
        login_limiter.guard(client, InvalidCurrentPasswordException),
        conflict_limiter.guard(client, ItemAlreadyExistsException),
    ):
        return UpdateCurrentUserUseCase(db).execute(current_user, user_in)


@router.get(
    "/{user_id}", status_code=status.HTTP_200_OK, response_model=User | UserPublic
)
def get_user(user_id: PathId, db: DbSession, viewer: OptionalUser):
    user = GetUserUseCase(db).execute(user_id, viewer)
    full_access = is_admin(viewer) or get_user_id(viewer) == user.id
    schema = User if full_access else UserPublic
    return schema.model_validate(user, from_attributes=True)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=User)
def create_user(
    user_in: UserCreate, db: DbSession, limiter: ConflictLimiter, client: ClientKey
):
    with limiter.guard(client, ItemAlreadyExistsException):
        return CreateUserUseCase(db).execute(user_in)


@router.patch("/{user_id}", status_code=status.HTTP_200_OK, response_model=User)
def update_user(
    user_id: PathId, user_in: UserAdminUpdate, db: DbSession, current_user: AdminUser
):
    return UpdateUserUseCase(db).execute(user_id, user_in)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: PathId, db: DbSession, current_user: AdminUser):
    DeleteUserUseCase(db).execute(user_id)
