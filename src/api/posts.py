from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.infrastructure.database import get_db
from src.infrastructure.repositories import PostRepository
from src.schemas.posts import Post, PostCreate, PostUpdate

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Post])
def get_posts(db: DbSession):
    repo = PostRepository(db)
    return repo.get_all()


@router.get("/{post_id}", status_code=status.HTTP_200_OK, response_model=Post)
def get_post(post_id: int, db: DbSession):
    repo = PostRepository(db)
    post = repo.get_by_id(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Публикация не найдена"
        )
    return post


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Post)
def create_post(post_in: PostCreate, db: DbSession):
    repo = PostRepository(db)
    return repo.create(post_in)


@router.put("/{post_id}", status_code=status.HTTP_200_OK, response_model=Post)
def update_post(post_id: int, post_in: PostUpdate, db: DbSession):
    repo = PostRepository(db)
    post = repo.update(post_id, post_in)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Публикация не найдена"
        )
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: DbSession):
    repo = PostRepository(db)
    if not repo.delete(post_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Публикация не найдена"
        )
