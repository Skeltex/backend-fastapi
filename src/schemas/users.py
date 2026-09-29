from datetime import datetime
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    EmailStr,
    Field,
    SecretStr,
)

from src.core.security import BCRYPT_MAX_PASSWORD_BYTES
from src.schemas.common import NotNull, OptionalStr, empty_string_to_none

USERNAME_PATTERN: str = r"^[\w.@+-]+$"


def check_password_bytes(password: SecretStr) -> SecretStr:
    if len(password.get_secret_value().encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(
            f"Пароль не должен превышать {BCRYPT_MAX_PASSWORD_BYTES} байта в UTF-8"
        )
    return password


Password = Annotated[
    SecretStr, Field(min_length=8), AfterValidator(check_password_bytes)
]
OptionalEmail = Annotated[EmailStr | None, BeforeValidator(empty_string_to_none)]


class UserPublic(BaseModel):
    id: int
    username: str = Field(description="Имя пользователя")
    first_name: str | None = Field(default=None, description="Имя")
    last_name: str | None = Field(default=None, description="Фамилия")
    created_at: datetime = Field(description="Дата регистрации")


class User(UserPublic):
    email: OptionalStr = Field(default=None, description="Email")
    is_active: bool = Field(description="Является активным")
    is_admin: bool = Field(description="Является администратором")


class UserCreate(BaseModel):
    username: str = Field(
        max_length=150, pattern=USERNAME_PATTERN, description="Имя пользователя"
    )
    email: OptionalEmail = Field(default=None, description="Email")
    first_name: str | None = Field(default=None, max_length=150, description="Имя")
    last_name: str | None = Field(default=None, max_length=150, description="Фамилия")
    password: Password = Field(description="Пароль")


class UserUpdate(BaseModel):
    username: Annotated[str | None, NotNull] = Field(
        default=None,
        max_length=150,
        pattern=USERNAME_PATTERN,
        description="Имя пользователя",
    )
    email: OptionalEmail = Field(default=None, description="Email")
    first_name: str | None = Field(default=None, max_length=150, description="Имя")
    last_name: str | None = Field(default=None, max_length=150, description="Фамилия")
    password: Annotated[Password | None, NotNull] = Field(
        default=None, description="Пароль"
    )


class UserAdminUpdate(UserUpdate):
    is_active: Annotated[bool | None, NotNull] = Field(
        default=None, description="Является активным"
    )
    is_admin: Annotated[bool | None, NotNull] = Field(
        default=None, description="Является администратором"
    )
