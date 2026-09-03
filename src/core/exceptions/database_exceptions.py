class BaseDatabaseException(Exception):
    """Базовый класс для всех ошибок базы данных."""


class ItemNotFoundException(BaseDatabaseException):
    """Выбрасывается, если запись не найдена в БД."""


class ItemAlreadyExistsException(BaseDatabaseException):
    """Выбрасывается при нарушении уникальности."""
