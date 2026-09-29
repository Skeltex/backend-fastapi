from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, validates

from src.core.normalization import (
    make_username_key,
    normalize_email,
    normalize_username,
)

from .database import Base
from .types import UTCDateTime, utc_now

NOT_EMPTY_EMAIL = text("email != ''")


class User(Base):
    __tablename__ = "auth_user"
    __table_args__ = (
        Index("uq_auth_user_username_key", "username_key", unique=True),
        Index(
            "uq_auth_user_email",
            "email",
            unique=True,
            sqlite_where=NOT_EMPTY_EMAIL,
            postgresql_where=NOT_EMPTY_EMAIL,
        ),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(150), unique=True)
    username_key: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String(254))
    first_name: Mapped[str | None] = mapped_column(String(150))
    last_name: Mapped[str | None] = mapped_column(String(150))
    password: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(default=True)

    is_admin: Mapped[bool] = mapped_column("is_superuser", default=False)
    created_at: Mapped[datetime] = mapped_column(
        "date_joined", UTCDateTime, default=utc_now
    )

    @validates("username")
    def validate_username(self, key, value):
        value = normalize_username(value)
        self.username_key = make_username_key(value)
        return value

    @validates("email")
    def validate_email(self, key, value):
        return "" if value is None else normalize_email(value)

    @validates("first_name", "last_name")
    def normalize_optional_strings(self, key, value):
        return "" if value is None else value


class Category(Base):
    __tablename__ = "blog_category"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    is_published: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)


class Location(Base):
    __tablename__ = "blog_location"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    is_published: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)


class Post(Base):
    __tablename__ = "blog_post"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(256))
    text: Mapped[str] = mapped_column(String)
    pub_date: Mapped[datetime] = mapped_column(UTCDateTime, index=True)

    image_url: Mapped[str | None] = mapped_column("image", String)

    is_published: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)

    author_id: Mapped[int] = mapped_column(
        ForeignKey("auth_user.id", ondelete="CASCADE"), index=True
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("blog_category.id", ondelete="SET NULL"), index=True
    )
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("blog_location.id", ondelete="SET NULL"), index=True
    )


class Comment(Base):
    __tablename__ = "blog_comment"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)

    author_id: Mapped[int] = mapped_column(
        ForeignKey("auth_user.id", ondelete="CASCADE"), index=True
    )
    post_id: Mapped[int] = mapped_column(
        ForeignKey("blog_post.id", ondelete="CASCADE"), index=True
    )
