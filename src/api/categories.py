from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.depends import get_admin_user
from src.core.exceptions.domain_exceptions import (
    ItemAlreadyExistsException,
    ItemNotFoundByIdException,
)
from src.domain.categories import (
    CreateCategoryUseCase,
    DeleteCategoryUseCase,
    GetCategoriesUseCase,
    GetCategoryUseCase,
    UpdateCategoryUseCase,
)
from src.infrastructure.database import get_db
from src.schemas.categories import Category, CategoryCreate, CategoryUpdate
from src.schemas.users import User

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[User, Depends(get_admin_user)]


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Category])
def get_categories(db: DbSession):
    use_case = GetCategoriesUseCase(db)
    return use_case.execute()


@router.get("/{category_id}", status_code=status.HTTP_200_OK, response_model=Category)
def get_category(category_id: int, db: DbSession):
    use_case = GetCategoryUseCase(db)
    try:
        return use_case.execute(category_id)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Category)
def create_category(
    category_in: CategoryCreate,
    db: DbSession,
    current_user: AdminUser,
):
    use_case = CreateCategoryUseCase(db)
    try:
        return use_case.execute(category_in)
    except ItemAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail,
        )


@router.put("/{category_id}", status_code=status.HTTP_200_OK, response_model=Category)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    db: DbSession,
    current_user: AdminUser,
):
    use_case = UpdateCategoryUseCase(db)
    try:
        return use_case.execute(category_id, category_in)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except ItemAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.detail)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: DbSession, current_user: AdminUser):
    use_case = DeleteCategoryUseCase(db)
    try:
        use_case.execute(category_id)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
