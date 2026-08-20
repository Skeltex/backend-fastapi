from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.infrastructure.database import get_db
from src.infrastructure.repositories import CategoryRepository
from src.schemas.categories import Category, CategoryCreate, CategoryUpdate

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Category])
def get_categories(db: DbSession):
    repo = CategoryRepository(db)
    return repo.get_all()


@router.get("/{category_id}", status_code=status.HTTP_200_OK, response_model=Category)
def get_category(category_id: int, db: DbSession):
    repo = CategoryRepository(db)
    category = repo.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
        )
    return category


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Category)
def create_category(category_in: CategoryCreate, db: DbSession):
    repo = CategoryRepository(db)
    if repo.get_by_slug(category_in.slug):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Категория с таким slug уже существует",
        )
    return repo.create(category_in)


@router.put("/{category_id}", status_code=status.HTTP_200_OK, response_model=Category)
def update_category(category_id: int, category_in: CategoryUpdate, db: DbSession):
    repo = CategoryRepository(db)
    category = repo.update(category_id, category_in)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
        )
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: DbSession):
    repo = CategoryRepository(db)
    if not repo.delete(category_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
        )
