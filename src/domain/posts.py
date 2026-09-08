from sqlalchemy.orm import Session

from src.core.exceptions.auth_exceptions import AccessDeniedException
from src.core.exceptions.database_exceptions import (
    ItemAlreadyExistsException,
    ItemNotFoundException,
)
from src.core.exceptions.domain_exceptions import (
    ItemAlreadyExistsException as DomainAlreadyExistsException,
)
from src.core.exceptions.domain_exceptions import (
    ItemNotFoundByIdException,
)
from src.infrastructure.repositories import PostRepository
from src.schemas.posts import PostCreate, PostUpdate
from src.schemas.users import User


class GetPostsUseCase:
    def __init__(self, db: Session):
        self.repo = PostRepository(db)

    def execute(self):
        return self.repo.get_all()


class GetPostUseCase:
    def __init__(self, db: Session):
        self.repo = PostRepository(db)

    def execute(self, post_id: int):
        try:
            return self.repo.get_by_id(post_id)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=post_id, item_name="Публикация")


class CreatePostUseCase:
    def __init__(self, db: Session):
        self.repo = PostRepository(db)

    def execute(self, data: PostCreate):
        try:
            return self.repo.create(data)
        except ItemAlreadyExistsException:
            raise DomainAlreadyExistsException(
                identifier=data.title, item_name="Публикация"
            )


class UpdatePostUseCase:
    def __init__(self, db: Session):
        self.repo = PostRepository(db)

    def execute(self, post_id: int, data: PostUpdate, current_user: User):
        try:
            post = self.repo.get_by_id(post_id)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=post_id, item_name="Публикация")

        if post.author_id != current_user.id and not current_user.is_admin:
            raise AccessDeniedException(
                detail="Вы не можете редактировать чужую публикацию"
            )

        try:
            return self.repo.update(post_id, data)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=post_id, item_name="Публикация")


class DeletePostUseCase:
    def __init__(self, db: Session):
        self.repo = PostRepository(db)

    def execute(self, post_id: int, current_user: User):
        try:
            post = self.repo.get_by_id(post_id)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=post_id, item_name="Публикация")

        if post.author_id != current_user.id and not current_user.is_admin:
            raise AccessDeniedException(detail="Вы не можете удалить чужую публикацию")

        try:
            self.repo.delete(post_id)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=post_id, item_name="Публикация")
