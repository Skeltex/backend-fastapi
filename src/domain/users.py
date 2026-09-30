from typing import Any

from sqlalchemy.orm import Session

from src.core.exceptions.database_exceptions import IntegrityViolationException
from src.core.exceptions.domain_exceptions import (
    InvalidCurrentPasswordException,
    ItemAlreadyExistsException,
    LastAdminException,
)
from src.core.security import get_password_hash, verify_password
from src.domain.common import ensure_found, get_user_id, is_admin
from src.infrastructure.models import User
from src.infrastructure.repositories import RefreshTokenRepository, UserRepository
from src.schemas.users import UserCreate, UserSelfUpdate, UserUpdate

ITEM_NAME = "Пользователь"


def check_user_unique(
    repo: UserRepository,
    username: str | None,
    email: str | None,
    exclude_id: int | None = None,
) -> None:
    if username is not None and repo.username_exists(username, exclude_id):
        raise ItemAlreadyExistsException(identifier=username, item_name=ITEM_NAME)
    if email and repo.email_exists(email, exclude_id):
        raise ItemAlreadyExistsException(
            identifier=email, item_name=f"{ITEM_NAME} с email"
        )


def ensure_admin_remains(
    repo: UserRepository, user: User, values: dict[str, Any] | None = None
) -> None:
    if not (user.is_admin and user.is_active):
        return
    loses_admin = values is None or (
        values.get("is_admin") is False or values.get("is_active") is False
    )
    if loses_admin and repo.count_active_admins(exclude_id=user.id) == 0:
        raise LastAdminException()


class GetUsersUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def execute(self, viewer: User | None, offset: int, limit: int) -> list[User]:
        if is_admin(viewer):
            return self.repo.get_all(offset, limit)
        return self.repo.get_active(offset, limit)


class GetUserUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def execute(self, user_id: int, viewer: User | None) -> User:
        if is_admin(viewer) or get_user_id(viewer) == user_id:
            user = self.repo.get_by_id(user_id)
        else:
            user = self.repo.get_active_by_id(user_id)
        return ensure_found(user, user_id, ITEM_NAME)


class CreateUserUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def execute(self, data: UserCreate) -> User:
        check_user_unique(self.repo, data.username, data.email)
        values = data.model_dump(exclude={"password"})
        values["password"] = get_password_hash(data.password.get_secret_value())
        try:
            return self.repo.create(values)
        except IntegrityViolationException:
            check_user_unique(self.repo, data.username, data.email)
            raise


class UpdateUserUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)
        self.tokens = RefreshTokenRepository(db)

    def execute(self, user_id: int, data: UserUpdate) -> User:
        user = ensure_found(self.repo.get_by_id(user_id), user_id, ITEM_NAME)
        values = data.model_dump(
            exclude_unset=True, exclude={"password", "current_password"}
        )
        check_user_unique(
            self.repo, values.get("username"), values.get("email"), exclude_id=user.id
        )
        ensure_admin_remains(self.repo, user, values)

        if data.password is not None:
            values["password"] = get_password_hash(data.password.get_secret_value())
        if data.password is not None or values.get("is_active") is False:
            self.tokens.revoke_all_for_user(user.id)

        try:
            return self.repo.update(user, values)
        except IntegrityViolationException:
            check_user_unique(
                self.repo,
                values.get("username"),
                values.get("email"),
                exclude_id=user_id,
            )
            raise


class UpdateCurrentUserUseCase:
    def __init__(self, db: Session):
        self.update_user = UpdateUserUseCase(db)

    def execute(self, user: User, data: UserSelfUpdate) -> User:
        if data.password is not None:
            current_password = (
                data.current_password.get_secret_value()
                if data.current_password is not None
                else ""
            )
            if not verify_password(current_password, user.password):
                raise InvalidCurrentPasswordException()
        return self.update_user.execute(user.id, data)


class DeleteUserUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def execute(self, user_id: int) -> None:
        user = ensure_found(self.repo.get_by_id(user_id), user_id, ITEM_NAME)
        ensure_admin_remains(self.repo, user)
        self.repo.delete(user)
