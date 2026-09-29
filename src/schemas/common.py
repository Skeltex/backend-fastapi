from datetime import UTC, datetime, timedelta
from typing import Annotated

from pydantic import AfterValidator, BaseModel, BeforeValidator, Field


def empty_string_to_none(value: object) -> object:
    return None if value == "" else value


def reject_null(value: object) -> object:
    if value is None:
        raise ValueError("Поле не может быть null")
    return value


def check_pub_date(pub_date: datetime) -> datetime:
    if pub_date.tzinfo is None:
        pub_date = pub_date.replace(tzinfo=UTC)
    pub_date = pub_date.astimezone(UTC)
    if pub_date < datetime.now(UTC) - timedelta(seconds=5):
        raise ValueError("Нельзя делать публикации с прошедшей датой")
    return pub_date


NotNull = BeforeValidator(reject_null)
OptionalStr = Annotated[str | None, BeforeValidator(empty_string_to_none)]
FuturePubDate = Annotated[datetime, AfterValidator(check_pub_date)]


class PaginationParams(BaseModel):
    offset: int = Field(default=0, ge=0, description="Сколько записей пропустить")
    limit: int = Field(default=100, ge=1, le=100, description="Сколько записей вернуть")
