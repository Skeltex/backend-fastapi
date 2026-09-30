from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from urllib.parse import urlsplit

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    SecretStr,
    StringConstraints,
    field_validator,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema

MAX_ID = 2**31 - 1
MAX_OFFSET = 2**63 - 1
IMAGE_URL_SCHEMES = frozenset({"", "http", "https"})


def empty_string_to_none(value: object) -> object:
    if isinstance(value, str):
        value = value.strip()
    return None if value == "" else value


def reject_null(value: object) -> object:
    if value is None:
        raise ValueError("Поле не может быть null")
    return value


def check_pub_date(pub_date: datetime) -> datetime:
    if pub_date.tzinfo is None:
        pub_date = pub_date.replace(tzinfo=UTC)
    try:
        pub_date = pub_date.astimezone(UTC)
    except OverflowError:
        raise ValueError("Дата публикации вне допустимого диапазона") from None
    if pub_date < datetime.now(UTC) - timedelta(seconds=5):
        raise ValueError("Нельзя делать публикации с прошедшей датой")
    return pub_date


def check_image_url(value: str | None) -> str | None:
    if value is not None and urlsplit(value).scheme.lower() not in IMAGE_URL_SCHEMES:
        raise ValueError("Допустимы только ссылки http(s) и относительные пути")
    return value


class NotNullMarker:
    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_before_validator_function(
            reject_null, handler(source_type)
        )

    def __get_pydantic_json_schema__(
        self, schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(schema)
        variants = [
            variant
            for variant in json_schema.get("anyOf", [])
            if variant != {"type": "null"}
        ]
        if len(variants) == 1:
            json_schema = {
                key: value for key, value in json_schema.items() if key != "anyOf"
            } | variants[0]
        return json_schema


NotNull = NotNullMarker()
NonBlankStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
OptionalStr = Annotated[str | None, BeforeValidator(empty_string_to_none)]
ImageUrl = Annotated[
    Annotated[str, StringConstraints(max_length=2048)] | None,
    BeforeValidator(empty_string_to_none),
    AfterValidator(check_image_url),
]
FuturePubDate = Annotated[datetime, AfterValidator(check_pub_date)]
EntityId = Annotated[int, Field(ge=1, le=MAX_ID)]


class InputSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="after")
    @classmethod
    def reject_invalid_unicode(cls, value: object) -> object:
        text = value.get_secret_value() if isinstance(value, SecretStr) else value
        if isinstance(text, str):
            try:
                text.encode("utf-8")
            except UnicodeEncodeError:
                raise ValueError("Строка содержит недопустимые символы") from None
            if "\x00" in text:
                raise ValueError("Строка содержит недопустимые символы")
        return value


class PaginationParams(BaseModel):
    offset: int = Field(
        default=0, ge=0, le=MAX_OFFSET, description="Сколько записей пропустить"
    )
    limit: int = Field(default=100, ge=1, le=100, description="Сколько записей вернуть")
