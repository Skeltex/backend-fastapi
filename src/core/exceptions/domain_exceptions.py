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
