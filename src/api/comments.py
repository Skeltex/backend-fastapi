from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from src.schemas.comments import Comment, CommentCreate, CommentUpdate

router = APIRouter()
comments: list[Comment] = []


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Comment])
async def get_comments():
    return comments


@router.get("/{comment_id}", status_code=status.HTTP_200_OK, response_model=Comment)
async def get_comment(comment_id: int):
    for comment in comments:
        if comment.id == comment_id:
            return comment
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Комментарий не найден"
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Comment)
async def create_comment(comment_in: CommentCreate):
    new_id = max((c.id for c in comments), default=0) + 1
    new_comment = Comment(
        **comment_in.model_dump(), id=new_id, created_at=datetime.now(UTC)
    )
    comments.append(new_comment)
    return new_comment


@router.put("/{comment_id}", status_code=status.HTTP_200_OK, response_model=Comment)
async def update_comment(comment_id: int, comment_in: CommentUpdate):
    for i, comment in enumerate(comments):
        if comment.id == comment_id:
            updated_data = comment_in.model_dump(exclude_unset=True)
            current_data = comment.model_dump()
            current_data.update(updated_data)

            comments[i] = Comment(**current_data)
            return comments[i]
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Комментарий не найден"
    )


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: int):
    for i, comment in enumerate(comments):
        if comment.id == comment_id:
            comments.pop(i)
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Комментарий не найден"
    )
