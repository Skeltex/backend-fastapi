from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from src.schemas.posts import Post, PostCreate, PostUpdate

router = APIRouter()
posts: list[Post] = []


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[Post])
async def get_posts():
    return posts


@router.get("/{post_id}", status_code=status.HTTP_200_OK, response_model=Post)
async def get_post(post_id: int):
    for post in posts:
        if post.id == post_id:
            return post
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Публикация не найдена"
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Post)
async def create_post(post_in: PostCreate):
    new_id = max((p.id for p in posts), default=0) + 1
    new_post = Post(**post_in.model_dump(), id=new_id, created_at=datetime.now(UTC))
    posts.append(new_post)
    return new_post


@router.put("/{post_id}", status_code=status.HTTP_200_OK, response_model=Post)
async def update_post(post_id: int, post_in: PostUpdate):
    for i, post in enumerate(posts):
        if post.id == post_id:
            updated_data = post_in.model_dump(exclude_unset=True)
            current_data = post.model_dump()
            current_data.update(updated_data)

            posts[i] = Post(**current_data)
            return posts[i]
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Публикация не найдена"
    )


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int):
    for i, post in enumerate(posts):
        if post.id == post_id:
            posts.pop(i)
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Публикация не найдена"
    )
