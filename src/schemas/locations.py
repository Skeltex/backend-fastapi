from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from src.schemas.common import NotNull


class LocationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256, description="Название места")
    is_published: bool = Field(default=True, description="Опубликовано")


class LocationUpdate(BaseModel):
    name: Annotated[str | None, NotNull] = Field(
        default=None, min_length=1, max_length=256, description="Название места"
    )
    is_published: Annotated[bool | None, NotNull] = Field(
        default=None, description="Опубликовано"
    )


class Location(BaseModel):
    id: int
    name: str = Field(description="Название места")
    is_published: bool = Field(description="Опубликовано")
    created_at: datetime = Field(description="Дата и время создания")
