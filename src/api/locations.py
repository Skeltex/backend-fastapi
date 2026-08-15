from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from src.schemas.locations import Location, LocationCreate, LocationUpdate

router = APIRouter()
locations: list[Location] = []


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Location])
async def get_locations():
    return locations


@router.get("/{location_id}", status_code=status.HTTP_200_OK, response_model=Location)
async def get_location(location_id: int):
    for location in locations:
        if location.id == location_id:
            return location
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Локация не найдена"
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Location)
async def create_location(location_in: LocationCreate):
    new_id = max((l.id for l in locations), default=0) + 1
    new_location = Location(
        **location_in.model_dump(), id=new_id, created_at=datetime.now(UTC)
    )
    locations.append(new_location)
    return new_location


@router.put("/{location_id}", status_code=status.HTTP_200_OK, response_model=Location)
async def update_location(location_id: int, location_in: LocationUpdate):
    for i, location in enumerate(locations):
        if location.id == location_id:
            updated_data = location_in.model_dump(exclude_unset=True)
            current_data = location.model_dump()
            current_data.update(updated_data)

            locations[i] = Location(**current_data)
            return locations[i]
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Локация не найдена"
    )


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(location_id: int):
    for i, location in enumerate(locations):
        if location.id == location_id:
            locations.pop(i)
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Локация не найдена"
    )
