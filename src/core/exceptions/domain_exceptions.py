class BaseDomainException(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class ItemNotFoundByIdException(BaseDomainException):
    def __init__(self, item_id: int, item_name: str = "Запись"):
        super().__init__(detail=f"{item_name} с id '{item_id}' не найдена.")


class ItemAlreadyExistsException(BaseDomainException):
    def __init__(self, identifier: str, item_name: str = "Запись"):
        super().__init__(detail=f"{item_name} '{identifier}' уже существует.")
