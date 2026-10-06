class BaseDomainException(Exception):
    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class ItemNotFoundByIdException(BaseDomainException):
    def __init__(self, item_id: int, item_name: str = "Запись"):
        super().__init__(detail=f"{item_name} с id '{item_id}' не существует.")


class RelatedItemNotFoundException(ItemNotFoundByIdException):
    pass


class ItemAlreadyExistsException(BaseDomainException):
    def __init__(self, identifier: str, item_name: str = "Запись"):
        super().__init__(detail=f"{item_name} '{identifier}' уже существует.")


class PermissionDeniedException(BaseDomainException):
    def __init__(self, detail: str = "Недостаточно прав для выполнения операции"):
        super().__init__(detail=detail)


class WrongCredentialsException(BaseDomainException):
    def __init__(self):
        super().__init__(detail="Неверный логин или пароль")


class InactiveUserException(BaseDomainException):
    def __init__(self):
        super().__init__(detail="Учетная запись отключена")


class InvalidRefreshTokenException(BaseDomainException):
    def __init__(self):
        super().__init__(detail="Refresh-токен недействителен или истек")


class InvalidCurrentPasswordException(BaseDomainException):
    def __init__(self):
        super().__init__(detail="Текущий пароль указан неверно")


class InvalidImageException(BaseDomainException):
    def __init__(self):
        super().__init__(detail="Файл должен быть изображением JPEG, PNG, WebP или GIF")


class ImageTooLargeException(BaseDomainException):
    def __init__(self, max_bytes: int):
        super().__init__(
            detail=f"Изображение не должно превышать {max_bytes / 1_048_576:g} МБ"
        )


class LastAdminException(BaseDomainException):
    def __init__(self):
        super().__init__(
            detail="Нельзя отключить, удалить или лишить прав последнего администратора"
        )
