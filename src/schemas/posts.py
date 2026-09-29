from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from src.schemas.common import (
    EntityId,
    FuturePubDate,
    ImageUrl,
    InputSchema,
    NonBlankStr,
    NotNull,
)

TITLE_MAX_LENGTH = 256
TEXT_MAX_LENGTH = 50_000


class PostCreate(InputSchema):
    title: NonBlankStr = Field(max_length=TITLE_MAX_LENGTH, description="Заголовок")
    text: NonBlankStr = Field(max_length=TEXT_MAX_LENGTH, description="Текст")
    pub_date: FuturePubDate = Field(description="Дата и время публикации")
    is_published: bool = Field(default=True, description="Опубликовано")

    location_id: EntityId | None = Field(default=None, description="ID местоположения")
    category_id: EntityId | None = Field(default=None, description="ID категории")

    image_url: ImageUrl = Field(
        default=None, description="URL или путь прикрепленного изображения"
    )


class PostUpdate(InputSchema):
    title: Annotated[NonBlankStr | None, NotNull] = Field(
        default=None, max_length=TITLE_MAX_LENGTH, description="Заголовок"
    )
    text: Annotated[NonBlankStr | None, NotNull] = Field(
        default=None, max_length=TEXT_MAX_LENGTH, description="Текст"
    )
    pub_date: Annotated[FuturePubDate | None, NotNull] = Field(
        default=None, description="Дата и время публикации"
    )
    is_published: Annotated[bool | None, NotNull] = Field(
        default=None, description="Опубликовано"
    )

    location_id: EntityId | None = Field(default=None, description="ID местоположения")
    category_id: EntityId | None = Field(default=None, description="ID категории")

    image_url: ImageUrl = Field(
        default=None, description="URL или путь прикрепленного изображения"
    )


class Post(BaseModel):
    id: int
    title: str = Field(description="Заголовок")
    text: str = Field(description="Текст")
    pub_date: datetime = Field(description="Дата и время публикации")
    is_published: bool = Field(description="Опубликовано")

    location_id: int | None = Field(default=None, description="ID местоположения")
    category_id: int | None = Field(default=None, description="ID категории")

    image_url: str | None = Field(
        default=None, description="URL или путь прикрепленного изображения"
    )

    author_id: int = Field(description="ID автора")
    created_at: datetime = Field(description="Дата и время создания")
