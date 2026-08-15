from datetime import datetime

from pydantic import BaseModel, Field


class CommentBase(BaseModel):
    text: str = Field(description="Текст")
    post_id: int = Field(description="ID публикации")


class CommentCreate(CommentBase):
    author_id: int = Field(description="ID автора")


class CommentUpdate(BaseModel):
    text: str | None = Field(default=None, description="Текст")


class Comment(CommentBase):
    id: int
    author_id: int = Field(description="ID автора")
    created_at: datetime = Field(description="Дата и время создания")
