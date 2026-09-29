from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from src.schemas.common import NotNull


class CommentCreate(BaseModel):
    text: str = Field(min_length=1, description="Текст")
    post_id: int = Field(description="ID публикации")


class CommentUpdate(BaseModel):
    text: Annotated[str | None, NotNull] = Field(
        default=None, min_length=1, description="Текст"
    )


class Comment(BaseModel):
    id: int
    text: str = Field(description="Текст")
    post_id: int = Field(description="ID публикации")
    author_id: int = Field(description="ID автора")
    created_at: datetime = Field(description="Дата и время создания")
