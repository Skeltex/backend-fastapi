from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.core.exceptions.database_exceptions import IntegrityViolationException
from src.core.exceptions.domain_exceptions import (
    BaseDomainException,
    InactiveUserException,
    ItemAlreadyExistsException,
    ItemNotFoundByIdException,
    PermissionDeniedException,
    RelatedItemNotFoundException,
    WrongCredentialsException,
)

DOMAIN_EXCEPTION_STATUS_CODES: dict[type[BaseDomainException], int] = {
    RelatedItemNotFoundException: status.HTTP_400_BAD_REQUEST,
    ItemNotFoundByIdException: status.HTTP_404_NOT_FOUND,
    ItemAlreadyExistsException: status.HTTP_409_CONFLICT,
    PermissionDeniedException: status.HTTP_403_FORBIDDEN,
    InactiveUserException: status.HTTP_403_FORBIDDEN,
    WrongCredentialsException: status.HTTP_401_UNAUTHORIZED,
}


async def domain_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    status_code = next(
        (
            code
            for exc_type, code in DOMAIN_EXCEPTION_STATUS_CODES.items()
            if isinstance(exc, exc_type)
        ),
        status.HTTP_400_BAD_REQUEST,
    )
    headers = (
        {"WWW-Authenticate": "Bearer"}
        if status_code == status.HTTP_401_UNAUTHORIZED
        else None
    )
    return JSONResponse(
        status_code=status_code,
        content={"detail": getattr(exc, "detail", str(exc))},
        headers=headers,
    )


async def integrity_violation_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Операция нарушает целостность данных"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(BaseDomainException, domain_exception_handler)
    app.add_exception_handler(IntegrityViolationException, integrity_violation_handler)
