from datetime import datetime

from pydantic import AnyUrl, BaseModel, Field


class PostBase(BaseModel):
    title: str = Field(max_length=256, description="Заголовок")
    text: str = Field(description="Текст")
    pub_date: datetime = Field(description="Дата и время публикации")
    is_published: bool = Field(default=True, description="Опубликовано")

    location_id: int | None = Field(default=None, description="ID местоположения")
    category_id: int | None = Field(default=None, description="ID категории")
    image_url: AnyUrl | None = Field(
        default=None, description="URL прикрепленного изображения"
    )


class PostCreate(PostBase):
    author_id: int = Field(description="ID автора")


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=256, description="Заголовок")
    text: str | None = Field(default=None, description="Текст")
    pub_date: datetime | None = Field(
        default=None, description="Дата и время публикации"
    )
    is_published: bool | None = Field(default=None, description="Опубликовано")

    location_id: int | None = Field(default=None, description="ID местоположения")
    category_id: int | None = Field(default=None, description="ID категории")
    image_url: AnyUrl | None = Field(
        default=None, description="URL прикрепленного изображения"
    )


class Post(PostBase):
    id: int
    author_id: int = Field(description="ID автора")
    created_at: datetime = Field(description="Дата и время создания")
