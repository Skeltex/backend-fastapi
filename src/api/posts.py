from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from src.api.depends import CurrentUser, DbSession, OptionalUser, Pagination, PathId
from src.core.settings import settings
from src.domain.posts import (
    CreatePostUseCase,
    DeletePostUseCase,
    GetPostsUseCase,
    GetPostUseCase,
    SetPostImageUseCase,
    UpdatePostUseCase,
)
from src.schemas.posts import Post, PostCreate, PostUpdate

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Post])
def get_posts(db: DbSession, viewer: OptionalUser, pagination: Pagination):
    return GetPostsUseCase(db).execute(viewer, pagination.offset, pagination.limit)


@router.get("/{post_id}", status_code=status.HTTP_200_OK, response_model=Post)
def get_post(post_id: PathId, db: DbSession, viewer: OptionalUser):
    return GetPostUseCase(db).execute(post_id, viewer)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Post)
def create_post(post_in: PostCreate, db: DbSession, current_user: CurrentUser):
    return CreatePostUseCase(db).execute(post_in, current_user)


@router.patch("/{post_id}", status_code=status.HTTP_200_OK, response_model=Post)
def update_post(
    post_id: PathId,
    post_in: PostUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    return UpdatePostUseCase(db).execute(post_id, post_in, current_user)


@router.post("/{post_id}/image", status_code=status.HTTP_200_OK, response_model=Post)
def upload_post_image(
    post_id: PathId,
    image: Annotated[
        UploadFile, File(description="Изображение JPEG, PNG, WebP или GIF")
    ],
    db: DbSession,
    current_user: CurrentUser,
):
    data = image.file.read(settings.MAX_IMAGE_BYTES + 1)
    return SetPostImageUseCase(db).execute(post_id, data, current_user)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: PathId, db: DbSession, current_user: CurrentUser):
    DeletePostUseCase(db).execute(post_id, current_user)
