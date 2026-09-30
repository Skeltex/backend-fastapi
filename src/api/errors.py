from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.exceptions.database_exceptions import (
    IntegrityViolationException,
    ItemNoLongerExistsException,
)
from src.core.exceptions.domain_exceptions import (
    BaseDomainException,
    InactiveUserException,
    InvalidCurrentPasswordException,
    ItemAlreadyExistsException,
    ItemNotFoundByIdException,
    LastAdminException,
    PermissionDeniedException,
    RelatedItemNotFoundException,
    WrongCredentialsException,
)
from src.core.logger import logger

DOMAIN_EXCEPTION_STATUS_CODES: dict[type[BaseDomainException], int] = {
    RelatedItemNotFoundException: status.HTTP_400_BAD_REQUEST,
    ItemNotFoundByIdException: status.HTTP_404_NOT_FOUND,
    ItemAlreadyExistsException: status.HTTP_409_CONFLICT,
    LastAdminException: status.HTTP_409_CONFLICT,
    PermissionDeniedException: status.HTTP_403_FORBIDDEN,
    InactiveUserException: status.HTTP_403_FORBIDDEN,
    InvalidCurrentPasswordException: status.HTTP_400_BAD_REQUEST,
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


def escape_invalid_unicode(value: object) -> object:
    if isinstance(value, str):
        return value.encode("utf-8", "backslashreplace").decode("utf-8")
    if isinstance(value, list):
        return [escape_invalid_unicode(item) for item in value]
    if isinstance(value, dict):
        return {
            escape_invalid_unicode(key): escape_invalid_unicode(item)
            for key, item in value.items()
        }
    return value


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    errors = exc.errors() if isinstance(exc, RequestValidationError) else []
    detail = [
        {key: value for key, value in error.items() if key != "input"}
        for error in errors
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": escape_invalid_unicode(jsonable_encoder(detail))},
    )


async def integrity_violation_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Операция нарушает целостность данных"},
    )


async def item_no_longer_exists_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Запись была удалена другим запросом"},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.opt(exception=exc).error(
        f"Необработанная ошибка при запросе {request.method} {request.url.path!r}"
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(BaseDomainException, domain_exception_handler)
    app.add_exception_handler(IntegrityViolationException, integrity_violation_handler)
    app.add_exception_handler(
        ItemNoLongerExistsException, item_no_longer_exists_handler
    )
    app.add_exception_handler(Exception, unhandled_exception_handler)
