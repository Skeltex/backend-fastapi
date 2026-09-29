from sqlalchemy.orm import Session

from src.core.exceptions.domain_exceptions import ItemAlreadyExistsException
from src.domain.common import ensure_found, is_admin
from src.infrastructure.models import Category, User
from src.infrastructure.repositories import CategoryRepository
from src.schemas.categories import CategoryCreate, CategoryUpdate

ITEM_NAME = "Категория"


class GetCategoriesUseCase:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)

    def execute(self, viewer: User | None, offset: int, limit: int) -> list[Category]:
        if is_admin(viewer):
            return self.repo.get_all(offset, limit)
        return self.repo.get_published(offset, limit)


class GetCategoryUseCase:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)

    def execute(self, category_id: int, viewer: User | None) -> Category:
        if is_admin(viewer):
            category = self.repo.get_by_id(category_id)
        else:
            category = self.repo.get_published_by_id(category_id)
        return ensure_found(category, category_id, ITEM_NAME)


class CreateCategoryUseCase:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)

    def execute(self, data: CategoryCreate) -> Category:
        if self.repo.get_by_slug(data.slug) is not None:
            raise ItemAlreadyExistsException(identifier=data.slug, item_name=ITEM_NAME)
        return self.repo.create(data.model_dump())


class UpdateCategoryUseCase:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)

    def execute(self, category_id: int, data: CategoryUpdate) -> Category:
        category = ensure_found(
            self.repo.get_by_id(category_id), category_id, ITEM_NAME
        )
        values = data.model_dump(exclude_unset=True)

        slug = values.get("slug")
        if slug is not None:
            existing = self.repo.get_by_slug(slug)
            if existing is not None and existing.id != category.id:
                raise ItemAlreadyExistsException(identifier=slug, item_name=ITEM_NAME)

        return self.repo.update(category, values)


class DeleteCategoryUseCase:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)

    def execute(self, category_id: int) -> None:
        category = ensure_found(
            self.repo.get_by_id(category_id), category_id, ITEM_NAME
        )
        self.repo.delete(category)
