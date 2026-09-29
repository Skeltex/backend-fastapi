from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from src.schemas.common import FuturePubDate, NotNull, OptionalStr


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=256, description="Заголовок")
    text: str = Field(min_length=1, description="Текст")
    pub_date: FuturePubDate = Field(description="Дата и время публикации")
    is_published: bool = Field(default=True, description="Опубликовано")

    location_id: int | None = Field(default=None, description="ID местоположения")
    category_id: int | None = Field(default=None, description="ID категории")

    image_url: OptionalStr = Field(
        default=None, description="URL или путь прикрепленного изображения"
    )


class PostUpdate(BaseModel):
    title: Annotated[str | None, NotNull] = Field(
        default=None, min_length=1, max_length=256, description="Заголовок"
    )
    text: Annotated[str | None, NotNull] = Field(
        default=None, min_length=1, description="Текст"
    )
    pub_date: Annotated[FuturePubDate | None, NotNull] = Field(
        default=None, description="Дата и время публикации"
    )
    is_published: Annotated[bool | None, NotNull] = Field(
        default=None, description="Опубликовано"
    )

    location_id: int | None = Field(default=None, description="ID местоположения")
    category_id: int | None = Field(default=None, description="ID категории")

    image_url: OptionalStr = Field(
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
