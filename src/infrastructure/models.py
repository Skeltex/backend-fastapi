from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from .database import Base


class User(Base):
    __tablename__ = "auth_user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(254), nullable=False)
    first_name = Column(String(150))
    last_name = Column(String(150))
    password = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)

    is_admin = Column("is_superuser", Boolean, default=False)
    created_at = Column("date_joined", DateTime)


class Category(Base):
    __tablename__ = "blog_category"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    description = Column(String, nullable=False)
    slug = Column(String(64), unique=True, nullable=False)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime)


class Location(Base):
    __tablename__ = "blog_location"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime)


class Post(Base):
    __tablename__ = "blog_post"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    text = Column(String, nullable=False)
    pub_date = Column(DateTime, nullable=False)

    image_url = Column("image", String, nullable=True)

    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime)

    author_id = Column(Integer, ForeignKey("auth_user.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("blog_category.id"))
    location_id = Column(Integer, ForeignKey("blog_location.id"))


class Comment(Base):
    __tablename__ = "blog_comment"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    created_at = Column(DateTime)

    author_id = Column(Integer, ForeignKey("auth_user.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("blog_post.id"), nullable=False)
