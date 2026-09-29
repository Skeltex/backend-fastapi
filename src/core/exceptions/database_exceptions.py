class BaseDatabaseException(Exception):
    """Базовый класс для всех ошибок базы данных."""


class IntegrityViolationException(BaseDatabaseException):
    pass
