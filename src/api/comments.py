from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.depends import get_current_user
from src.core.exceptions.auth_exceptions import AccessDeniedException
from src.core.exceptions.domain_exceptions import (
    ItemAlreadyExistsException,
    ItemNotFoundByIdException,
)
from src.domain.comments import (
    CreateCommentUseCase,
    DeleteCommentUseCase,
    GetCommentsUseCase,
    GetCommentUseCase,
    UpdateCommentUseCase,
)
from src.infrastructure.database import get_db
from src.schemas.comments import Comment, CommentCreate, CommentUpdate
from src.schemas.users import User

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


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
def create_comment(comment_in: CommentCreate, db: DbSession, current_user: CurrentUser):
    comment_in.author_id = current_user.id
    use_case = CreateCommentUseCase(db)
    try:
        return use_case.execute(comment_in)
    except ItemAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.detail)


@router.put("/{comment_id}", status_code=status.HTTP_200_OK, response_model=Comment)
def update_comment(
    comment_id: int,
    comment_in: CommentUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    use_case = UpdateCommentUseCase(db)
    try:
        return use_case.execute(comment_id, comment_in, current_user)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except AccessDeniedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.detail)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, db: DbSession, current_user: CurrentUser):
    use_case = DeleteCommentUseCase(db)
    try:
        use_case.execute(comment_id, current_user)
    except ItemNotFoundByIdException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except AccessDeniedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.detail)
