from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from src.schemas.common import EntityId, InputSchema, NonBlankStr, NotNull

TEXT_MAX_LENGTH = 5_000


class CommentCreate(InputSchema):
    text: NonBlankStr = Field(max_length=TEXT_MAX_LENGTH, description="Текст")
    post_id: EntityId = Field(description="ID публикации")


class CommentUpdate(InputSchema):
    text: Annotated[NonBlankStr | None, NotNull] = Field(
        default=None, max_length=TEXT_MAX_LENGTH, description="Текст"
    )


class Comment(BaseModel):
    id: int
    text: str = Field(description="Текст")
    post_id: int = Field(description="ID публикации")
    author_id: int = Field(description="ID автора")
    created_at: datetime = Field(description="Дата и время создания")
