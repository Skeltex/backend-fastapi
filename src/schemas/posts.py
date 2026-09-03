from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field, field_validator


class PostBase(BaseModel):
    title: str = Field(max_length=256, description="Заголовок")
    text: str = Field(description="Текст")
    pub_date: datetime = Field(description="Дата и время публикации")
    is_published: bool = Field(default=True, description="Опубликовано")

    location_id: int | None = Field(default=None, description="ID местоположения")
    category_id: int | None = Field(default=None, description="ID категории")

    image_url: str | None = Field(
        default=None, description="URL или путь прикрепленного изображения"
    )

    @field_validator("image_url", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: str | None) -> str | None:
        if not v:
            return None
        return str(v)


class PostCreate(PostBase):
    author_id: int = Field(description="ID автора")

    @field_validator("pub_date", mode="after")
    @classmethod
    def check_pub_date(cls, pub_date: datetime) -> datetime:
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=UTC)
        if pub_date < datetime.now(UTC) - timedelta(seconds=5):
            raise ValueError("Нельзя делать публикации с прошедшей датой")
        return pub_date


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=256, description="Заголовок")
    text: str | None = Field(default=None, description="Текст")
    pub_date: datetime | None = Field(
        default=None, description="Дата и время публикации"
    )
    is_published: bool | None = Field(default=None, description="Опубликовано")

    location_id: int | None = Field(default=None, description="ID местоположения")
    category_id: int | None = Field(default=None, description="ID категории")

    image_url: str | None = Field(
        default=None, description="URL или путь прикрепленного изображения"
    )

    @field_validator("image_url", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: str | None) -> str | None:
        if not v:
            return None
        return str(v)

    @field_validator("pub_date", mode="after")
    @classmethod
    def check_pub_date(cls, pub_date: datetime | None) -> datetime | None:
        if pub_date is not None and pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=UTC)
        if pub_date and pub_date < datetime.now(UTC) - timedelta(seconds=5):
            raise ValueError("Нельзя обновлять публикацию прошедшей датой")
        return pub_date


class Post(PostBase):
    id: int
    author_id: int = Field(description="ID автора")
    created_at: datetime = Field(description="Дата и время создания")
