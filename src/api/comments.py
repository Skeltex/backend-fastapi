from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.infrastructure.database import get_db
from src.infrastructure.repositories import CommentRepository
from src.schemas.comments import Comment, CommentCreate, CommentUpdate

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Comment])
def get_comments(db: DbSession):
    repo = CommentRepository(db)
    return repo.get_all()


@router.get("/{comment_id}", status_code=status.HTTP_200_OK, response_model=Comment)
def get_comment(comment_id: int, db: DbSession):
    repo = CommentRepository(db)
    comment = repo.get_by_id(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Комментарий не найден"
        )
    return comment


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Comment)
def create_comment(comment_in: CommentCreate, db: DbSession):
    repo = CommentRepository(db)
    return repo.create(comment_in)


@router.put("/{comment_id}", status_code=status.HTTP_200_OK, response_model=Comment)
def update_comment(comment_id: int, comment_in: CommentUpdate, db: DbSession):
    repo = CommentRepository(db)
    comment = repo.update(comment_id, comment_in)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Комментарий не найден"
        )
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, db: DbSession):
    repo = CommentRepository(db)
    if not repo.delete(comment_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Комментарий не найден"
        )
