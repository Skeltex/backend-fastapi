from sqlalchemy.orm import Session

from src.domain.common import ensure_found, is_admin
from src.infrastructure.models import Location, User
from src.infrastructure.repositories import LocationRepository
from src.schemas.locations import LocationCreate, LocationUpdate

ITEM_NAME = "Местоположение"


class GetLocationsUseCase:
    def __init__(self, db: Session):
        self.repo = LocationRepository(db)

    def execute(self, viewer: User | None, offset: int, limit: int) -> list[Location]:
        if is_admin(viewer):
            return self.repo.get_all(offset, limit)
        return self.repo.get_published(offset, limit)


class GetLocationUseCase:
    def __init__(self, db: Session):
        self.repo = LocationRepository(db)

    def execute(self, location_id: int, viewer: User | None) -> Location:
        if is_admin(viewer):
            location = self.repo.get_by_id(location_id)
        else:
            location = self.repo.get_published_by_id(location_id)
        return ensure_found(location, location_id, ITEM_NAME)


class CreateLocationUseCase:
    def __init__(self, db: Session):
        self.repo = LocationRepository(db)

    def execute(self, data: LocationCreate) -> Location:
        return self.repo.create(data.model_dump())


class UpdateLocationUseCase:
    def __init__(self, db: Session):
        self.repo = LocationRepository(db)

    def execute(self, location_id: int, data: LocationUpdate) -> Location:
        location = ensure_found(
            self.repo.get_by_id(location_id), location_id, ITEM_NAME
        )
        return self.repo.update(location, data.model_dump(exclude_unset=True))


class DeleteLocationUseCase:
    def __init__(self, db: Session):
        self.repo = LocationRepository(db)

    def execute(self, location_id: int) -> None:
        location = ensure_found(
            self.repo.get_by_id(location_id), location_id, ITEM_NAME
        )
        self.repo.delete(location)
