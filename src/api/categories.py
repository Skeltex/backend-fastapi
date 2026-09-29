from fastapi import APIRouter, status

from src.api.depends import AdminUser, DbSession, OptionalUser, Pagination
from src.domain.categories import (
    CreateCategoryUseCase,
    DeleteCategoryUseCase,
    GetCategoriesUseCase,
    GetCategoryUseCase,
    UpdateCategoryUseCase,
)
from src.schemas.categories import Category, CategoryCreate, CategoryUpdate

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Category])
def get_categories(db: DbSession, viewer: OptionalUser, pagination: Pagination):
    return GetCategoriesUseCase(db).execute(viewer, pagination.offset, pagination.limit)


@router.get("/{category_id}", status_code=status.HTTP_200_OK, response_model=Category)
def get_category(category_id: int, db: DbSession, viewer: OptionalUser):
    return GetCategoryUseCase(db).execute(category_id, viewer)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Category)
def create_category(
    category_in: CategoryCreate,
    db: DbSession,
    current_user: AdminUser,
):
    return CreateCategoryUseCase(db).execute(category_in)


@router.patch("/{category_id}", status_code=status.HTTP_200_OK, response_model=Category)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    db: DbSession,
    current_user: AdminUser,
):
    return UpdateCategoryUseCase(db).execute(category_id, category_in)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: DbSession, current_user: AdminUser):
    DeleteCategoryUseCase(db).execute(category_id)
