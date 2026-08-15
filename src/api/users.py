from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from src.schemas.users import User, UserCreate, UserUpdate

router = APIRouter()
users: list[User] = []


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[User])
async def get_users():
    return users


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=User)
async def get_user(user_id: int):
    for user in users:
        if user.id == user_id:
            return user
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=User)
async def create_user(user_in: UserCreate):
    for user in users:
        if user.email == user_in.email or user.username == user_in.username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким email или username уже существует",
            )

    new_id = max((u.id for u in users), default=0) + 1
    new_user = User(
        **user_in.model_dump(),
        id=new_id,
        created_at=datetime.now(UTC),
        is_active=True,
        is_admin=False,
    )
    users.append(new_user)
    return new_user


@router.put("/{user_id}", status_code=status.HTTP_200_OK, response_model=User)
async def update_user(user_id: int, user_in: UserUpdate):
    for i, user in enumerate(users):
        if user.id == user_id:
            updated_data = user_in.model_dump(exclude_unset=True)
            current_data = user.model_dump()
            current_data.update(updated_data)

            users[i] = User(**current_data)
            return users[i]
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    for i, user in enumerate(users):
        if user.id == user_id:
            users.pop(i)
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
    )
