from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    SECRET_KEY: SecretStr = Field(min_length=32)
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)
    DATABASE_URL: str = f"sqlite:///{(BASE_DIR / 'data' / 'db.sqlite3').as_posix()}"
    LOG_FILE: Path = BASE_DIR / "logs" / "app.log"
    CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")


settings = Settings()
