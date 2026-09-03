from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.exceptions.database_exceptions import (
    ItemAlreadyExistsException,
    ItemNotFoundException,
)

from .models import Category, Comment, Location, Post, User


class BaseRepository:
    def __init__(self, model, db: Session):
        self.model = model
        self.db = db

    def get_all(self):
        return self.db.query(self.model).all()

    def get_by_id(self, item_id: int):
        db_item = self.db.query(self.model).filter(self.model.id == item_id).first()
        if not db_item:
            raise ItemNotFoundException()
        return db_item

    def create(self, item_in):
        item_data = item_in.model_dump()

        if "password" in item_data and hasattr(item_in.password, "get_secret_value"):
            item_data["password"] = item_in.password.get_secret_value()

        db_item = self.model(**item_data)
        self.db.add(db_item)
        try:
            self.db.commit()
            self.db.refresh(db_item)
            return db_item
        except IntegrityError:
            self.db.rollback()
            raise ItemAlreadyExistsException()

    def update(self, item_id: int, item_in):
        db_item = self.get_by_id(item_id)

        update_data = item_in.model_dump(exclude_unset=True)

        if "password" in update_data and hasattr(item_in.password, "get_secret_value"):
            update_data["password"] = item_in.password.get_secret_value()

        for key, value in update_data.items():
            setattr(db_item, key, value)

        try:
            self.db.commit()
            self.db.refresh(db_item)
            return db_item
        except IntegrityError:
            self.db.rollback()
            raise ItemAlreadyExistsException()

    def delete(self, item_id: int):
        db_item = self.get_by_id(item_id)
        self.db.delete(db_item)
        self.db.commit()


class CategoryRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Category, db)

    def get_by_slug(self, slug: str):
        return self.db.query(self.model).filter(self.model.slug == slug).first()


class CommentRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Comment, db)


class LocationRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Location, db)


class PostRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Post, db)


class UserRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email_or_username(self, email: str | None, username: str):
        condition = self.model.username == username
        if email:
            condition = condition | (self.model.email == email)
        return self.db.query(self.model).filter(condition).first()
