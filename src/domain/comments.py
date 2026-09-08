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
from src.infrastructure.repositories import CommentRepository
from src.schemas.comments import CommentCreate, CommentUpdate
from src.schemas.users import User


class GetCommentsUseCase:
    def __init__(self, db: Session):
        self.repo = CommentRepository(db)

    def execute(self):
        return self.repo.get_all()


class GetCommentUseCase:
    def __init__(self, db: Session):
        self.repo = CommentRepository(db)

    def execute(self, comment_id: int):
        try:
            return self.repo.get_by_id(comment_id)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=comment_id, item_name="Комментарий")


class CreateCommentUseCase:
    def __init__(self, db: Session):
        self.repo = CommentRepository(db)

    def execute(self, data: CommentCreate):
        try:
            return self.repo.create(data)
        except ItemAlreadyExistsException:
            raise DomainAlreadyExistsException(
                identifier="с такими данными", item_name="Комментарий"
            )


class UpdateCommentUseCase:
    def __init__(self, db: Session):
        self.repo = CommentRepository(db)

    def execute(self, comment_id: int, data: CommentUpdate, current_user: User):
        try:
            comment = self.repo.get_by_id(comment_id)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=comment_id, item_name="Комментарий")

        if comment.author_id != current_user.id and not current_user.is_admin:
            raise AccessDeniedException(
                detail="Вы не можете редактировать чужой комментарий"
            )

        try:
            return self.repo.update(comment_id, data)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=comment_id, item_name="Комментарий")


class DeleteCommentUseCase:
    def __init__(self, db: Session):
        self.repo = CommentRepository(db)

    def execute(self, comment_id: int, current_user: User):
        try:
            comment = self.repo.get_by_id(comment_id)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=comment_id, item_name="Комментарий")

        if comment.author_id != current_user.id and not current_user.is_admin:
            raise AccessDeniedException(detail="Вы не можете удалить чужой комментарий")

        try:
            self.repo.delete(comment_id)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=comment_id, item_name="Комментарий")
