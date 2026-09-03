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
from src.infrastructure.repositories import CategoryRepository
from src.schemas.categories import CategoryCreate, CategoryUpdate


class GetCategoriesUseCase:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)

    def execute(self):
        return self.repo.get_all()


class GetCategoryUseCase:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)

    def execute(self, category_id: int):
        try:
            return self.repo.get_by_id(category_id)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=category_id, item_name="Категория")


class CreateCategoryUseCase:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)

    def execute(self, data: CategoryCreate):
        try:
            return self.repo.create(data)
        except ItemAlreadyExistsException:
            raise DomainAlreadyExistsException(
                identifier=data.slug, item_name="Категория"
            )


class UpdateCategoryUseCase:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)

    def execute(self, category_id: int, data: CategoryUpdate):
        try:
            return self.repo.update(category_id, data)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=category_id, item_name="Категория")
        except ItemAlreadyExistsException:
            raise DomainAlreadyExistsException(
                identifier=data.slug or "с таким slug", item_name="Категория"
            )


class DeleteCategoryUseCase:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)

    def execute(self, category_id: int):
        try:
            self.repo.delete(category_id)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=category_id, item_name="Категория")
