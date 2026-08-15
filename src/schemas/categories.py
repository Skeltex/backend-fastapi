from datetime import datetime

from pydantic import BaseModel, Field

SLUG_PATTERN: str = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class CategoryBase(BaseModel):
    title: str = Field(max_length=256, description="Заголовок")
    description: str = Field(description="Описание")
    slug: str = Field(
        pattern=SLUG_PATTERN,
        max_length=64,
        description="Идентификатор категории в формате slug",
    )
    is_published: bool = Field(default=True, description="Опубликовано")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=256, description="Заголовок")
    description: str | None = Field(default=None, description="Описание")
    slug: str | None = Field(
        default=None,
        pattern=SLUG_PATTERN,
        max_length=64,
        description="Идентификатор категории в формате slug",
    )
    is_published: bool | None = Field(default=None, description="Опубликовано")


class Category(CategoryBase):
    id: int
    created_at: datetime = Field(description="Дата и время создания")
