from pydantic import BaseModel, Field, SecretStr

from src.schemas.common import InputSchema


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Время жизни access-токена в секундах")


class RefreshTokenRequest(InputSchema):
    refresh_token: SecretStr = Field(
        min_length=1, max_length=256, description="Refresh-токен"
    )
