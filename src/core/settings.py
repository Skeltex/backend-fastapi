import json
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
MIN_SECRET_KEY_BYTES = {"HS256": 32, "HS384": 48, "HS512": 64}


class Settings(BaseSettings):
    SECRET_KEY: SecretStr = SecretStr("")
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0, le=525_600)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, gt=0, le=365)
    DATABASE_URL: str = f"sqlite:///{(BASE_DIR / 'data' / 'db.sqlite3').as_posix()}"
    LOG_FILE: Path = BASE_DIR / "logs" / "app.log"
    CORS_ORIGINS: Annotated[list[str], NoDecode] = ["*"]
    AUTH_FAILURES_LIMIT: int = Field(default=10, gt=0)
    AUTH_FAILURES_WINDOW_SECONDS: int = Field(default=300, gt=0)
    MAX_REQUEST_BODY_BYTES: int = Field(default=1_048_576, gt=0)

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

    @model_validator(mode="after")
    def check_secret_key(self) -> Self:
        min_bytes = MIN_SECRET_KEY_BYTES[self.ALGORITHM]
        if len(self.SECRET_KEY.get_secret_value().encode("utf-8")) < min_bytes:
            raise ValueError(
                f"SECRET_KEY для {self.ALGORITHM} должен быть не короче {min_bytes} байт"
            )
        return self


settings = Settings()
