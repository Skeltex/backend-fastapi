from sqlalchemy.orm import Session

from src.core.exceptions.domain_exceptions import BaseDomainException
from src.core.security import create_access_token, verify_password
from src.infrastructure.repositories import UserRepository


class WrongCredentialsException(BaseDomainException):
    def __init__(self):
        super().__init__(detail="Неверный логин или пароль")


class AuthenticateUserUseCase:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def execute(self, username: str, password: str) -> str:
        user = self.repo.get_by_email_or_username(email="", username=username)

        if not user or not verify_password(password, user.password):
            raise WrongCredentialsException()

        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "is_admin": user.is_admin,
        }
        return create_access_token(token_data)
