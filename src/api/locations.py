from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.infrastructure.database import get_db
from src.infrastructure.repositories import LocationRepository
from src.schemas.locations import Location, LocationCreate, LocationUpdate

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Location])
def get_locations(db: DbSession):
    repo = LocationRepository(db)
    return repo.get_all()


@router.get("/{location_id}", status_code=status.HTTP_200_OK, response_model=Location)
def get_location(location_id: int, db: DbSession):
    repo = LocationRepository(db)
    location = repo.get_by_id(location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Локация не найдена"
        )
    return location


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Location)
def create_location(location_in: LocationCreate, db: DbSession):
    repo = LocationRepository(db)
    return repo.create(location_in)


@router.put("/{location_id}", status_code=status.HTTP_200_OK, response_model=Location)
def update_location(location_id: int, location_in: LocationUpdate, db: DbSession):
    repo = LocationRepository(db)
    location = repo.update(location_id, location_in)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Локация не найдена"
        )
    return location


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(location_id: int, db: DbSession):
    repo = LocationRepository(db)
    if not repo.delete(location_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Локация не найдена"
        )
