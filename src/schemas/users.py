from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator


class UserBase(BaseModel):
    username: str = Field(description="Имя пользователя")
    email: EmailStr | None = Field(default=None, description="Email")
    first_name: str | None = Field(default=None, description="Имя")
    last_name: str | None = Field(default=None, description="Фамилия")

    @field_validator("email", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: str | None) -> str | None:
        if v == "":
            return None
        return v


class UserCreate(UserBase):
    password: SecretStr = Field(min_length=8, description="Пароль")


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, description="Имя пользователя")
    email: EmailStr | None = Field(default=None, description="Email")
    first_name: str | None = Field(default=None, description="Имя")
    last_name: str | None = Field(default=None, description="Фамилия")
    password: SecretStr | None = Field(default=None, min_length=8, description="Пароль")

    @field_validator("email", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: str | None) -> str | None:
        if v == "":
            return None
        return v


class User(UserBase):
    id: int
    created_at: datetime = Field(description="Дата регистрации")
    is_active: bool = Field(default=True, description="Является активным")
    is_admin: bool = Field(default=False, description="Является администратором")
