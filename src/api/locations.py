from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.exceptions.domain_exceptions import ItemNotFoundByIdException
from src.domain.locations import (
    CreateLocationUseCase,
    DeleteLocationUseCase,
    GetLocationsUseCase,
    GetLocationUseCase,
    UpdateLocationUseCase,
)
from src.infrastructure.database import get_db
from src.schemas.locations import Location, LocationCreate, LocationUpdate

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Location])
def get_locations(db: DbSession):
    return GetLocationsUseCase(db).execute()


@router.get("/{location_id}", status_code=status.HTTP_200_OK, response_model=Location)
def get_location(location_id: int, db: DbSession):
    try:
        return GetLocationUseCase(db).execute(location_id)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Location)
def create_location(location_in: LocationCreate, db: DbSession):
    return CreateLocationUseCase(db).execute(location_in)


@router.put("/{location_id}", status_code=status.HTTP_200_OK, response_model=Location)
def update_location(location_id: int, location_in: LocationUpdate, db: DbSession):
    try:
        return UpdateLocationUseCase(db).execute(location_id, location_in)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(location_id: int, db: DbSession):
    try:
        DeleteLocationUseCase(db).execute(location_id)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
