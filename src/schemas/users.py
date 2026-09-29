from datetime import datetime
from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    EmailStr,
    Field,
    SecretStr,
    StringConstraints,
    model_validator,
)

from src.core.normalization import normalize_email, normalize_username
from src.core.security import BCRYPT_MAX_PASSWORD_BYTES
from src.schemas.common import (
    InputSchema,
    NotNull,
    OptionalStr,
    empty_string_to_none,
)

USERNAME_PATTERN: str = r"^[\w.@+-]+$"


def normalize_username_input(value: object) -> object:
    return normalize_username(value) if isinstance(value, str) else value


def normalize_email_input(value: str | None) -> str | None:
    return normalize_email(value) if value is not None else None


def check_password_bytes(password: SecretStr) -> SecretStr:
    try:
        password_bytes = password.get_secret_value().encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError("Строка содержит недопустимые символы") from None
    if len(password_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(
            f"Пароль не должен превышать {BCRYPT_MAX_PASSWORD_BYTES} байта в UTF-8"
        )
    return password


Username = Annotated[
    str,
    BeforeValidator(normalize_username_input),
    StringConstraints(max_length=150, pattern=USERNAME_PATTERN),
]
Password = Annotated[
    SecretStr, Field(min_length=8), AfterValidator(check_password_bytes)
]
OptionalEmail = Annotated[
    EmailStr | None,
    BeforeValidator(empty_string_to_none),
    AfterValidator(normalize_email_input),
]
PersonName = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True, max_length=150)] | None,
    BeforeValidator(empty_string_to_none),
]


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


class UserCreate(InputSchema):
    username: Username = Field(description="Имя пользователя")
    email: OptionalEmail = Field(default=None, description="Email")
    first_name: PersonName = Field(default=None, description="Имя")
    last_name: PersonName = Field(default=None, description="Фамилия")
    password: Password = Field(description="Пароль")


class UserUpdate(InputSchema):
    username: Annotated[Username | None, NotNull] = Field(
        default=None, description="Имя пользователя"
    )
    email: OptionalEmail = Field(default=None, description="Email")
    first_name: PersonName = Field(default=None, description="Имя")
    last_name: PersonName = Field(default=None, description="Фамилия")
    password: Annotated[Password | None, NotNull] = Field(
        default=None, description="Пароль"
    )


class UserSelfUpdate(UserUpdate):
    current_password: Annotated[SecretStr | None, NotNull] = Field(
        default=None, description="Текущий пароль, обязателен при смене пароля"
    )

    @model_validator(mode="after")
    def require_current_password(self) -> Self:
        if self.password is not None and self.current_password is None:
            raise ValueError("Для смены пароля укажите текущий пароль")
        return self


class UserAdminUpdate(UserUpdate):
    is_active: Annotated[bool | None, NotNull] = Field(
        default=None, description="Является активным"
    )
    is_admin: Annotated[bool | None, NotNull] = Field(
        default=None, description="Является администратором"
    )
