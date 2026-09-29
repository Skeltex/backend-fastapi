from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from src.schemas.common import InputSchema, NonBlankStr, NotNull

NAME_MAX_LENGTH = 256


class LocationCreate(InputSchema):
    name: NonBlankStr = Field(max_length=NAME_MAX_LENGTH, description="Название места")
    is_published: bool = Field(default=True, description="Опубликовано")


class LocationUpdate(InputSchema):
    name: Annotated[NonBlankStr | None, NotNull] = Field(
        default=None, max_length=NAME_MAX_LENGTH, description="Название места"
    )
    is_published: Annotated[bool | None, NotNull] = Field(
        default=None, description="Опубликовано"
    )


class Location(BaseModel):
    id: int
    name: str = Field(description="Название места")
    is_published: bool = Field(description="Опубликовано")
    created_at: datetime = Field(description="Дата и время создания")
