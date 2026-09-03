from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.exceptions.domain_exceptions import (
    ItemAlreadyExistsException,
    ItemNotFoundByIdException,
)
from src.domain.posts import (
    CreatePostUseCase,
    DeletePostUseCase,
    GetPostsUseCase,
    GetPostUseCase,
    UpdatePostUseCase,
)
from src.infrastructure.database import get_db
from src.schemas.posts import Post, PostCreate, PostUpdate

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Post])
def get_posts(db: DbSession):
    return GetPostsUseCase(db).execute()


@router.get("/{post_id}", status_code=status.HTTP_200_OK, response_model=Post)
def get_post(post_id: int, db: DbSession):
    try:
        return GetPostUseCase(db).execute(post_id)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Post)
def create_post(post_in: PostCreate, db: DbSession):
    try:
        return CreatePostUseCase(db).execute(post_in)
    except ItemAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.detail)


@router.put("/{post_id}", status_code=status.HTTP_200_OK, response_model=Post)
def update_post(post_id: int, post_in: PostUpdate, db: DbSession):
    try:
        return UpdatePostUseCase(db).execute(post_id, post_in)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: DbSession):
    try:
        DeletePostUseCase(db).execute(post_id)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
