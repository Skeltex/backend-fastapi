from typing import Any

from sqlalchemy.orm import Session

from src.core.exceptions.domain_exceptions import RelatedItemNotFoundException
from src.domain.common import ensure_can_modify, ensure_found, get_user_id, is_admin
from src.infrastructure.models import Post, User
from src.infrastructure.repositories import (
    CategoryRepository,
    LocationRepository,
    PostRepository,
)
from src.schemas.posts import PostCreate, PostUpdate

ITEM_NAME = "Публикация"


def check_post_relations(db: Session, values: dict[str, Any]) -> None:
    category_id = values.get("category_id")
    if (
        category_id is not None
        and CategoryRepository(db).get_by_id(category_id) is None
    ):
        raise RelatedItemNotFoundException(item_id=category_id, item_name="Категория")

    location_id = values.get("location_id")
    if (
        location_id is not None
        and LocationRepository(db).get_by_id(location_id) is None
    ):
        raise RelatedItemNotFoundException(
            item_id=location_id, item_name="Местоположение"
        )


class GetPostsUseCase:
    def __init__(self, db: Session):
        self.repo = PostRepository(db)

    def execute(self, viewer: User | None, offset: int, limit: int) -> list[Post]:
        if is_admin(viewer):
            return self.repo.get_all(offset, limit)
        return self.repo.get_visible(get_user_id(viewer), offset, limit)


class GetPostUseCase:
    def __init__(self, db: Session):
        self.repo = PostRepository(db)

    def execute(self, post_id: int, viewer: User | None) -> Post:
        if is_admin(viewer):
            post = self.repo.get_by_id(post_id)
        else:
            post = self.repo.get_visible_by_id(post_id, get_user_id(viewer))
        return ensure_found(post, post_id, ITEM_NAME)


class CreatePostUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PostRepository(db)

    def execute(self, data: PostCreate, author: User) -> Post:
        values = data.model_dump()
        check_post_relations(self.db, values)
        return self.repo.create({**values, "author_id": author.id})


class UpdatePostUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PostRepository(db)

    def execute(self, post_id: int, data: PostUpdate, current_user: User) -> Post:
        post = ensure_found(self.repo.get_by_id(post_id), post_id, ITEM_NAME)
        ensure_can_modify(
            post.author_id,
            current_user,
            detail="Вы не можете редактировать чужую публикацию",
        )

        values = data.model_dump(exclude_unset=True)
        check_post_relations(self.db, values)
        return self.repo.update(post, values)


class DeletePostUseCase:
    def __init__(self, db: Session):
        self.repo = PostRepository(db)

    def execute(self, post_id: int, current_user: User) -> None:
        post = ensure_found(self.repo.get_by_id(post_id), post_id, ITEM_NAME)
        ensure_can_modify(
            post.author_id, current_user, detail="Вы не можете удалить чужую публикацию"
        )
        self.repo.delete(post)
