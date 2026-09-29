from datetime import UTC, datetime
from typing import Any

from sqlalchemy import ColumnElement, and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session

from src.core.exceptions.database_exceptions import IntegrityViolationException
from src.core.logger import logger
from src.core.normalization import (
    make_username_key,
    normalize_email,
    normalize_username,
)

from .models import Category, Comment, Location, Post, User


class BaseRepository[ModelT: (Category, Comment, Location, Post, User)]:
    def __init__(self, model: type[ModelT], db: Session):
        self.model = model
        self.db = db

    def get_all(self, offset: int, limit: int) -> list[ModelT]:
        return self._paginate(self.db.query(self.model), offset, limit)

    def get_by_id(self, item_id: int) -> ModelT | None:
        return self.db.get(self.model, item_id)

    def create(self, values: dict[str, Any]) -> ModelT:
        db_item = self.model(**values)
        self.db.add(db_item)
        self._commit()
        self.db.refresh(db_item)
        logger.info(f"Успешно создана запись {self.model.__name__} (ID: {db_item.id})")
        return db_item

    def update(self, db_item: ModelT, values: dict[str, Any]) -> ModelT:
        for key, value in values.items():
            setattr(db_item, key, value)
        self._commit()
        self.db.refresh(db_item)
        return db_item

    def delete(self, db_item: ModelT) -> None:
        self.db.delete(db_item)
        self._commit()

    def _ordering(self) -> tuple[Any, ...]:
        return (self.model.id,)

    def _paginate(self, query: Query[ModelT], offset: int, limit: int) -> list[ModelT]:
        return query.order_by(*self._ordering()).offset(offset).limit(limit).all()

    def _commit(self) -> None:
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            logger.warning(
                f"Нарушение целостности данных в {self.model.__name__}: {e.orig}"
            )
            raise IntegrityViolationException from e


class PublishableRepository[ModelT: (Category, Location)](BaseRepository[ModelT]):
    def get_published(self, offset: int, limit: int) -> list[ModelT]:
        query = self.db.query(self.model).filter(self.model.is_published.is_(True))
        return self._paginate(query, offset, limit)

    def get_published_by_id(self, item_id: int) -> ModelT | None:
        return (
            self.db.query(self.model)
            .filter(self.model.id == item_id, self.model.is_published.is_(True))
            .first()
        )


class CategoryRepository(PublishableRepository[Category]):
    def __init__(self, db: Session):
        super().__init__(Category, db)

    def get_by_slug(self, slug: str) -> Category | None:
        return self.db.query(Category).filter(Category.slug == slug).first()


class LocationRepository(PublishableRepository[Location]):
    def __init__(self, db: Session):
        super().__init__(Location, db)


def post_visibility_clause(viewer_id: int | None) -> ColumnElement[bool]:
    clause = and_(
        Post.is_published.is_(True),
        Post.pub_date <= datetime.now(UTC),
        or_(Post.category_id.is_(None), Category.is_published.is_(True)),
    )
    if viewer_id is not None:
        return or_(clause, Post.author_id == viewer_id)
    return clause


class PostRepository(BaseRepository[Post]):
    def __init__(self, db: Session):
        super().__init__(Post, db)

    def get_visible(self, viewer_id: int | None, offset: int, limit: int) -> list[Post]:
        return self._paginate(self._visible_query(viewer_id), offset, limit)

    def get_visible_by_id(self, post_id: int, viewer_id: int | None) -> Post | None:
        return self._visible_query(viewer_id).filter(Post.id == post_id).first()

    def unpublish_by_category(self, category_id: int) -> None:
        self.db.query(Post).filter(Post.category_id == category_id).update(
            {Post.is_published: False}, synchronize_session=False
        )

    def _ordering(self) -> tuple[Any, ...]:
        return (Post.pub_date.desc(), Post.id.desc())

    def _visible_query(self, viewer_id: int | None) -> Query[Post]:
        return (
            self.db.query(Post)
            .outerjoin(Category, Post.category_id == Category.id)
            .filter(post_visibility_clause(viewer_id))
        )


class CommentRepository(BaseRepository[Comment]):
    def __init__(self, db: Session):
        super().__init__(Comment, db)

    def get_visible(
        self, viewer_id: int | None, offset: int, limit: int
    ) -> list[Comment]:
        return self._paginate(self._visible_query(viewer_id), offset, limit)

    def get_visible_by_id(
        self, comment_id: int, viewer_id: int | None
    ) -> Comment | None:
        return self._visible_query(viewer_id).filter(Comment.id == comment_id).first()

    def _ordering(self) -> tuple[Any, ...]:
        return (Comment.created_at, Comment.id)

    def _visible_query(self, viewer_id: int | None) -> Query[Comment]:
        visibility = post_visibility_clause(viewer_id)
        if viewer_id is not None:
            visibility = or_(visibility, Comment.author_id == viewer_id)
        return (
            self.db.query(Comment)
            .join(Post, Comment.post_id == Post.id)
            .outerjoin(Category, Post.category_id == Category.id)
            .filter(visibility)
        )


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_active(self, offset: int, limit: int) -> list[User]:
        query = self.db.query(User).filter(User.is_active.is_(True))
        return self._paginate(query, offset, limit)

    def get_active_by_id(self, user_id: int) -> User | None:
        return (
            self.db.query(User)
            .filter(User.id == user_id, User.is_active.is_(True))
            .first()
        )

    def get_by_username(self, username: str) -> User | None:
        return (
            self.db.query(User)
            .filter(User.username == normalize_username(username))
            .first()
        )

    def username_exists(self, username: str, exclude_id: int | None = None) -> bool:
        query = self.db.query(User).filter(
            User.username_key == make_username_key(username)
        )
        if exclude_id is not None:
            query = query.filter(User.id != exclude_id)
        return query.first() is not None

    def email_exists(self, email: str, exclude_id: int | None = None) -> bool:
        query = self.db.query(User).filter(User.email == normalize_email(email))
        if exclude_id is not None:
            query = query.filter(User.id != exclude_id)
        return query.first() is not None

    def count_active_admins(self, exclude_id: int) -> int:
        return (
            self.db.query(User)
            .filter(
                User.is_admin.is_(True),
                User.is_active.is_(True),
                User.id != exclude_id,
            )
            .count()
        )
