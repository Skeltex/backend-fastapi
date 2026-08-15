from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from src.schemas.categories import Category, CategoryCreate, CategoryUpdate

router = APIRouter()
categories: list[Category] = []


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Category])
async def get_categories():
    return categories


@router.get("/{category_id}", status_code=status.HTTP_200_OK, response_model=Category)
async def get_category(category_id: int):
    for category in categories:
        if category.id == category_id:
            return category
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Category)
async def create_category(category_in: CategoryCreate):
    for category in categories:
        if category.slug == category_in.slug:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Категория с таким slug уже существует",
            )

    new_id = max((c.id for c in categories), default=0) + 1
    new_category = Category(
        **category_in.model_dump(), id=new_id, created_at=datetime.now(UTC)
    )
    categories.append(new_category)
    return new_category


@router.put("/{category_id}", status_code=status.HTTP_200_OK, response_model=Category)
async def update_category(category_id: int, category_in: CategoryUpdate):
    for i, category in enumerate(categories):
        if category.id == category_id:
            updated_data = category_in.model_dump(exclude_unset=True)
            current_data = category.model_dump()
            current_data.update(updated_data)

            categories[i] = Category(**current_data)
            return categories[i]
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
    )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int):
    for i, category in enumerate(categories):
        if category.id == category_id:
            categories.pop(i)
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
    )
