from sqlalchemy.orm import Session

from src.core.exceptions.domain_exceptions import RelatedItemNotFoundException
from src.domain.common import ensure_can_modify, ensure_found, get_user_id, is_admin
from src.infrastructure.models import Comment, User
from src.infrastructure.repositories import CommentRepository, PostRepository
from src.schemas.comments import CommentCreate, CommentUpdate

ITEM_NAME = "Комментарий"


def find_visible_comment(
    repo: CommentRepository, comment_id: int, viewer: User | None
) -> Comment:
    if is_admin(viewer):
        comment = repo.get_by_id(comment_id)
    else:
        comment = repo.get_visible_by_id(comment_id, get_user_id(viewer))
    return ensure_found(comment, comment_id, ITEM_NAME)


class GetCommentsUseCase:
    def __init__(self, db: Session):
        self.repo = CommentRepository(db)

    def execute(self, viewer: User | None, offset: int, limit: int) -> list[Comment]:
        if is_admin(viewer):
            return self.repo.get_all(offset, limit)
        return self.repo.get_visible(get_user_id(viewer), offset, limit)


class GetCommentUseCase:
    def __init__(self, db: Session):
        self.repo = CommentRepository(db)

    def execute(self, comment_id: int, viewer: User | None) -> Comment:
        return find_visible_comment(self.repo, comment_id, viewer)


class CreateCommentUseCase:
    def __init__(self, db: Session):
        self.repo = CommentRepository(db)
        self.posts = PostRepository(db)

    def execute(self, data: CommentCreate, author: User) -> Comment:
        if is_admin(author):
            post = self.posts.get_by_id(data.post_id)
        else:
            post = self.posts.get_visible_by_id(data.post_id, author.id)
        if post is None:
            raise RelatedItemNotFoundException(
                item_id=data.post_id, item_name="Публикация"
            )
        return self.repo.create({**data.model_dump(), "author_id": author.id})


class UpdateCommentUseCase:
    def __init__(self, db: Session):
        self.repo = CommentRepository(db)

    def execute(
        self, comment_id: int, data: CommentUpdate, current_user: User
    ) -> Comment:
        comment = find_visible_comment(self.repo, comment_id, current_user)
        ensure_can_modify(
            comment.author_id,
            current_user,
            detail="Вы не можете редактировать чужой комментарий",
        )
        return self.repo.update(comment, data.model_dump(exclude_unset=True))


class DeleteCommentUseCase:
    def __init__(self, db: Session):
        self.repo = CommentRepository(db)

    def execute(self, comment_id: int, current_user: User) -> None:
        comment = find_visible_comment(self.repo, comment_id, current_user)
        ensure_can_modify(
            comment.author_id,
            current_user,
            detail="Вы не можете удалить чужой комментарий",
        )
        self.repo.delete(comment)
