from datetime import datetime

from pydantic import BaseModel, Field


class LocationBase(BaseModel):
    name: str = Field(max_length=256, description="Название места")
    is_published: bool = Field(default=True, description="Опубликовано")


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=256, description="Название места")
    is_published: bool | None = Field(default=None, description="Опубликовано")


class Location(LocationBase):
    id: int
    created_at: datetime = Field(description="Дата и время создания")
