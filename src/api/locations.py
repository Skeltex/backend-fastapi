from fastapi import APIRouter, status

from src.api.depends import AdminUser, DbSession, OptionalUser, Pagination, PathId
from src.domain.locations import (
    CreateLocationUseCase,
    DeleteLocationUseCase,
    GetLocationsUseCase,
    GetLocationUseCase,
    UpdateLocationUseCase,
)
from src.schemas.locations import Location, LocationCreate, LocationUpdate

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Location])
def get_locations(db: DbSession, viewer: OptionalUser, pagination: Pagination):
    return GetLocationsUseCase(db).execute(viewer, pagination.offset, pagination.limit)


@router.get("/{location_id}", status_code=status.HTTP_200_OK, response_model=Location)
def get_location(location_id: PathId, db: DbSession, viewer: OptionalUser):
    return GetLocationUseCase(db).execute(location_id, viewer)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Location)
def create_location(
    location_in: LocationCreate,
    db: DbSession,
    current_user: AdminUser,
):
    return CreateLocationUseCase(db).execute(location_in)


@router.patch("/{location_id}", status_code=status.HTTP_200_OK, response_model=Location)
def update_location(
    location_id: PathId,
    location_in: LocationUpdate,
    db: DbSession,
    current_user: AdminUser,
):
    return UpdateLocationUseCase(db).execute(location_id, location_in)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(location_id: PathId, db: DbSession, current_user: AdminUser):
    DeleteLocationUseCase(db).execute(location_id)
