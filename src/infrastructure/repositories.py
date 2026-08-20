from sqlalchemy.orm import Session

from .models import Category, Comment, Location, Post, User


class BaseRepository:
    def __init__(self, model, db: Session):
        self.model = model
        self.db = db

    def get_all(self):
        return self.db.query(self.model).all()

    def get_by_id(self, item_id: int):
        return self.db.query(self.model).filter(self.model.id == item_id).first()

    def create(self, item_in):
        item_data = item_in.model_dump()

        if "password" in item_data and hasattr(item_in.password, "get_secret_value"):
            item_data["password"] = item_in.password.get_secret_value()

        db_item = self.model(**item_data)
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return db_item

    def update(self, item_id: int, item_in):
        db_item = self.get_by_id(item_id)
        if not db_item:
            return None

        update_data = item_in.model_dump(exclude_unset=True)

        if "password" in update_data and hasattr(item_in.password, "get_secret_value"):
            update_data["password"] = item_in.password.get_secret_value()

        for key, value in update_data.items():
            setattr(db_item, key, value)

        self.db.commit()
        self.db.refresh(db_item)
        return db_item

    def delete(self, item_id: int) -> bool:
        db_item = self.get_by_id(item_id)
        if not db_item:
            return False
        self.db.delete(db_item)
        self.db.commit()
        return True


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

    def get_by_email_or_username(self, email: str, username: str):
        return (
            self.db.query(self.model)
            .filter((self.model.email == email) | (self.model.username == username))
            .first()
        )
