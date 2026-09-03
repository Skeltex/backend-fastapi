from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.exceptions.domain_exceptions import ItemNotFoundByIdException
from src.domain.comments import (
    CreateCommentUseCase,
    DeleteCommentUseCase,
    GetCommentsUseCase,
    GetCommentUseCase,
    UpdateCommentUseCase,
)
from src.infrastructure.database import get_db
from src.schemas.comments import Comment, CommentCreate, CommentUpdate

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Comment])
def get_comments(db: DbSession):
    return GetCommentsUseCase(db).execute()


@router.get("/{comment_id}", status_code=status.HTTP_200_OK, response_model=Comment)
def get_comment(comment_id: int, db: DbSession):
    try:
        return GetCommentUseCase(db).execute(comment_id)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Comment)
def create_comment(comment_in: CommentCreate, db: DbSession):
    return CreateCommentUseCase(db).execute(comment_in)


@router.put("/{comment_id}", status_code=status.HTTP_200_OK, response_model=Comment)
def update_comment(comment_id: int, comment_in: CommentUpdate, db: DbSession):
    try:
        return UpdateCommentUseCase(db).execute(comment_id, comment_in)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, db: DbSession):
    try:
        DeleteCommentUseCase(db).execute(comment_id)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
