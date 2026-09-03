from sqlalchemy.orm import Session

from src.core.exceptions.database_exceptions import ItemNotFoundException
from src.core.exceptions.domain_exceptions import ItemNotFoundByIdException
from src.infrastructure.repositories import CommentRepository
from src.schemas.comments import CommentCreate, CommentUpdate


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
        return self.repo.create(data)


class UpdateCommentUseCase:
    def __init__(self, db: Session):
        self.repo = CommentRepository(db)

    def execute(self, comment_id: int, data: CommentUpdate):
        try:
            return self.repo.update(comment_id, data)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=comment_id, item_name="Комментарий")


class DeleteCommentUseCase:
    def __init__(self, db: Session):
        self.repo = CommentRepository(db)

    def execute(self, comment_id: int):
        try:
            self.repo.delete(comment_id)
        except ItemNotFoundException:
            raise ItemNotFoundByIdException(item_id=comment_id, item_name="Комментарий")
