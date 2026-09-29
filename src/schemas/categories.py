from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from src.schemas.common import InputSchema, NonBlankStr, NotNull

SLUG_PATTERN: str = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
TITLE_MAX_LENGTH = 256
DESCRIPTION_MAX_LENGTH = 10_000


class CategoryCreate(InputSchema):
    title: NonBlankStr = Field(max_length=TITLE_MAX_LENGTH, description="Заголовок")
    description: NonBlankStr = Field(
        max_length=DESCRIPTION_MAX_LENGTH, description="Описание"
    )
    slug: str = Field(
        pattern=SLUG_PATTERN,
        max_length=64,
        description="Идентификатор категории в формате slug",
    )
    is_published: bool = Field(default=True, description="Опубликовано")


class CategoryUpdate(InputSchema):
    title: Annotated[NonBlankStr | None, NotNull] = Field(
        default=None, max_length=TITLE_MAX_LENGTH, description="Заголовок"
    )
    description: Annotated[NonBlankStr | None, NotNull] = Field(
        default=None, max_length=DESCRIPTION_MAX_LENGTH, description="Описание"
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
