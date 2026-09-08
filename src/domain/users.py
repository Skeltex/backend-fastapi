from sqlalchemy.orm import Session

from src.core.exceptions.database_exceptions import (
    ItemAlreadyExistsException,
    ItemNotFoundException,
)
from src.core.exceptions.domain_exceptions import (
    ItemAlreadyExistsException as DomainAlreadyExistsException,
)
from src.core.exceptions.domain_exceptions import (
    ItemNotFoundByIdException,
)
from src.core.security import get_password_hash
from src.infrastructure.repositories import UserRepository
from src.schemas.users import UserCreate, UserUpdate


class GetUsersUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def execute(self):
        return self.repo.get_all()


class GetUserUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def execute(self, user_id: int):
        try:
            return self.repo.get_by_id(user_id)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=user_id, item_name="Пользователь")


class CreateUserUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def execute(self, data: UserCreate):
        if self.repo.get_by_email_or_username(data.email, data.username):
            raise DomainAlreadyExistsException(
                identifier=f"{data.username} или {data.email}", item_name="Пользователь"
            )
        data.password = get_password_hash(data.password.get_secret_value())
        return self.repo.create(data)


class UpdateUserUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def execute(self, user_id: int, data: UserUpdate):
        if data.password:
            data.password = get_password_hash(data.password.get_secret_value())
        try:
            return self.repo.update(user_id, data)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=user_id, item_name="Пользователь")
        except ItemAlreadyExistsException:
            raise DomainAlreadyExistsException(
                identifier="Обновляемые данные", item_name="Пользователь"
            )


class DeleteUserUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def execute(self, user_id: int):
        try:
            self.repo.delete(user_id)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=user_id, item_name="Пользователь")
