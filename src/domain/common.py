from src.core.exceptions.domain_exceptions import (
    ItemNotFoundByIdException,
    PermissionDeniedException,
)
from src.infrastructure.models import User


def is_admin(user: User | None) -> bool:
    return user is not None and user.is_admin


def get_user_id(user: User | None) -> int | None:
    return user.id if user is not None else None


def ensure_found[T](item: T | None, item_id: int, item_name: str) -> T:
    if item is None:
        raise ItemNotFoundByIdException(item_id=item_id, item_name=item_name)
    return item


def ensure_can_modify(author_id: int, user: User, detail: str) -> None:
    if author_id != user.id and not user.is_admin:
        raise PermissionDeniedException(detail=detail)
