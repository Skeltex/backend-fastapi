import json
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy import URL
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

BASE_DIR = Path(__file__).resolve().parents[2]
MIN_SECRET_KEY_BYTES = {"HS256": 32, "HS384": 48, "HS512": 64}
POSTGRES_DRIVER = "postgresql+psycopg"
POSTGRES_BACKENDS = frozenset({"postgres", "postgresql"})
MEDIA_URL = "/media/"


class Settings(BaseSettings):
    SECRET_KEY: SecretStr = SecretStr("")
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0, le=525_600)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, gt=0, le=365)
    POSTGRES_USER: str = "blog"
    POSTGRES_PASSWORD: SecretStr = SecretStr("")
    POSTGRES_DB: str = "blog"
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = Field(default=5432, gt=0, le=65535)
    DATABASE_URL: SecretStr | None = None
    LOG_FILE: Path = BASE_DIR / "logs" / "app.log"
    CORS_ORIGINS: Annotated[list[str], NoDecode] = ["*"]
    AUTH_FAILURES_LIMIT: int = Field(default=10, gt=0)
    AUTH_FAILURES_WINDOW_SECONDS: int = Field(default=300, gt=0)
    MAX_REQUEST_BODY_BYTES: int = Field(default=1_048_576, gt=0)
    MEDIA_DIR: Path = BASE_DIR / "media"
    MAX_IMAGE_BYTES: int = Field(default=5_242_880, gt=0)

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", extra="ignore", hide_input_in_errors=True
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        value = value.strip()
        if value.startswith("["):
            return json.loads(value)
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def empty_database_url_to_none(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value

    @model_validator(mode="after")
    def check_secret_key(self) -> Self:
        min_bytes = MIN_SECRET_KEY_BYTES[self.ALGORITHM]
        if len(self.SECRET_KEY.get_secret_value().encode("utf-8")) < min_bytes:
            raise ValueError(
                f"SECRET_KEY для {self.ALGORITHM} должен быть не короче {min_bytes} байт"
            )
        return self

    @model_validator(mode="after")
    def check_database(self) -> Self:
        if self.DATABASE_URL is None and not self.POSTGRES_PASSWORD.get_secret_value():
            raise ValueError("Задайте POSTGRES_PASSWORD или DATABASE_URL")
        if self.database_url.get_backend_name() != "postgresql":
            raise ValueError("DATABASE_URL должен указывать на PostgreSQL")
        return self

    @property
    def database_url(self) -> URL:
        if self.DATABASE_URL is None:
            return URL.create(
                POSTGRES_DRIVER,
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD.get_secret_value(),
                host=self.POSTGRES_HOST,
                port=self.POSTGRES_PORT,
                database=self.POSTGRES_DB,
            )
        try:
            url = make_url(self.DATABASE_URL.get_secret_value())
        except ArgumentError, ValueError:
            raise ValueError("DATABASE_URL имеет неверный формат") from None
        if url.get_backend_name() in POSTGRES_BACKENDS:
            return url.set(drivername=POSTGRES_DRIVER)
        return url


settings = Settings()
