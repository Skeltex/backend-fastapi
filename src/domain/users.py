from sqlalchemy.orm import Session

from src.core.exceptions.domain_exceptions import ItemAlreadyExistsException
from src.core.security import get_password_hash
from src.domain.common import ensure_found
from src.infrastructure.models import User
from src.infrastructure.repositories import UserRepository
from src.schemas.users import UserCreate, UserUpdate

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


class GetUsersUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def execute(self, offset: int, limit: int) -> list[User]:
        return self.repo.get_all(offset, limit)


class GetUserUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def execute(self, user_id: int) -> User:
        return ensure_found(self.repo.get_by_id(user_id), user_id, ITEM_NAME)


class CreateUserUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def execute(self, data: UserCreate) -> User:
        check_user_unique(self.repo, data.username, data.email)
        values = data.model_dump(exclude={"password"})
        values["password"] = get_password_hash(data.password.get_secret_value())
        return self.repo.create(values)


class UpdateUserUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def execute(self, user_id: int, data: UserUpdate) -> User:
        user = ensure_found(self.repo.get_by_id(user_id), user_id, ITEM_NAME)
        values = data.model_dump(exclude_unset=True, exclude={"password"})
        check_user_unique(
            self.repo, values.get("username"), values.get("email"), exclude_id=user.id
        )

        if data.password is not None:
            values["password"] = get_password_hash(data.password.get_secret_value())

        return self.repo.update(user, values)


class DeleteUserUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def execute(self, user_id: int) -> None:
        user = ensure_found(self.repo.get_by_id(user_id), user_id, ITEM_NAME)
        self.repo.delete(user)
