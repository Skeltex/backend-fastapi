from fastapi import APIRouter, status
from sqlalchemy import text

from src.api.depends import DbSession

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
def health(db: DbSession) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
