from fastapi import APIRouter, status

from src.api.depends import CurrentUser, DbSession, OptionalUser, Pagination, PathId
from src.domain.comments import (
    CreateCommentUseCase,
    DeleteCommentUseCase,
    GetCommentsUseCase,
    GetCommentUseCase,
    UpdateCommentUseCase,
)
from src.schemas.comments import Comment, CommentCreate, CommentUpdate

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Comment])
def get_comments(db: DbSession, viewer: OptionalUser, pagination: Pagination):
    return GetCommentsUseCase(db).execute(viewer, pagination.offset, pagination.limit)


@router.get("/{comment_id}", status_code=status.HTTP_200_OK, response_model=Comment)
def get_comment(comment_id: PathId, db: DbSession, viewer: OptionalUser):
    return GetCommentUseCase(db).execute(comment_id, viewer)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Comment)
def create_comment(comment_in: CommentCreate, db: DbSession, current_user: CurrentUser):
    return CreateCommentUseCase(db).execute(comment_in, current_user)


@router.patch("/{comment_id}", status_code=status.HTTP_200_OK, response_model=Comment)
def update_comment(
    comment_id: PathId,
    comment_in: CommentUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    return UpdateCommentUseCase(db).execute(comment_id, comment_in, current_user)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: PathId, db: DbSession, current_user: CurrentUser):
    DeleteCommentUseCase(db).execute(comment_id, current_user)
