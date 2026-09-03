from sqlalchemy.orm import Session

from src.core.exceptions.database_exceptions import ItemNotFoundException
from src.core.exceptions.domain_exceptions import ItemNotFoundByIdException
from src.infrastructure.repositories import LocationRepository
from src.schemas.locations import LocationCreate, LocationUpdate


class GetLocationsUseCase:
    def __init__(self, db: Session):
        self.repo = LocationRepository(db)

    def execute(self):
        return self.repo.get_all()


class GetLocationUseCase:
    def __init__(self, db: Session):
        self.repo = LocationRepository(db)

    def execute(self, location_id: int):
        try:
            return self.repo.get_by_id(location_id)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(
                item_id=location_id, item_name="Местоположение"
            )


class CreateLocationUseCase:
    def __init__(self, db: Session):
        self.repo = LocationRepository(db)

    def execute(self, data: LocationCreate):
        return self.repo.create(data)


class UpdateLocationUseCase:
    def __init__(self, db: Session):
        self.repo = LocationRepository(db)

    def execute(self, location_id: int, data: LocationUpdate):
        try:
            return self.repo.update(location_id, data)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(
                item_id=location_id, item_name="Местоположение"
            )


class DeleteLocationUseCase:
    def __init__(self, db: Session):
        self.repo = LocationRepository(db)

    def execute(self, location_id: int):
        try:
            self.repo.delete(location_id)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(
                item_id=location_id, item_name="Местоположение"
            )
