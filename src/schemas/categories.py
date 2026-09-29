from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from src.schemas.common import NotNull

SLUG_PATTERN: str = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class CategoryCreate(BaseModel):
    title: str = Field(min_length=1, max_length=256, description="Заголовок")
    description: str = Field(min_length=1, description="Описание")
    slug: str = Field(
        pattern=SLUG_PATTERN,
        max_length=64,
        description="Идентификатор категории в формате slug",
    )
    is_published: bool = Field(default=True, description="Опубликовано")


class CategoryUpdate(BaseModel):
    title: Annotated[str | None, NotNull] = Field(
        default=None, min_length=1, max_length=256, description="Заголовок"
    )
    description: Annotated[str | None, NotNull] = Field(
        default=None, min_length=1, description="Описание"
    )
    slug: Annotated[str | None, NotNull] = Field(
        default=None,
        pattern=SLUG_PATTERN,
        max_length=64,
        description="Идентификатор категории в формате slug",
    )
    is_published: Annotated[bool | None, NotNull] = Field(
        default=None, description="Опубликовано"
    )


class Category(BaseModel):
    id: int
    title: str = Field(description="Заголовок")
    description: str = Field(description="Описание")
    slug: str = Field(description="Идентификатор категории в формате slug")
    is_published: bool = Field(description="Опубликовано")
    created_at: datetime = Field(description="Дата и время создания")
