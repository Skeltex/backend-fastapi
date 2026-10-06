from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from src.api.auth import router as auth_router
from src.api.categories import router as categories_router
from src.api.comments import router as comments_router
from src.api.errors import register_exception_handlers
from src.api.health import router as health_router
from src.api.locations import router as locations_router
from src.api.middleware import BodySizeLimitMiddleware
from src.api.posts import router as posts_router
from src.api.rate_limit import RateLimiter
from src.api.users import router as users_router
from src.core.logger import logger
from src.core.settings import MEDIA_URL, settings


def create_app() -> FastAPI:
    logger.info("Инициализация приложения FastAPI...")
    app = FastAPI(
        title="Django to FastAPI Migration API",
        description="REST API для сущностей блога",
    )

    app.state.login_limiter = RateLimiter(
        settings.AUTH_FAILURES_LIMIT, settings.AUTH_FAILURES_WINDOW_SECONDS
    )
    app.state.conflict_limiter = RateLimiter(
        settings.AUTH_FAILURES_LIMIT, settings.AUTH_FAILURES_WINDOW_SECONDS
    )

    app.add_middleware(
        BodySizeLimitMiddleware,
        max_body_bytes=settings.MAX_REQUEST_BODY_BYTES,
        max_upload_bytes=settings.MAX_IMAGE_BYTES,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    api_router = APIRouter(prefix="/api/v1")
    api_router.include_router(
        categories_router, prefix="/categories", tags=["Categories"]
    )
    api_router.include_router(users_router, prefix="/users", tags=["Users"])
    api_router.include_router(locations_router, prefix="/locations", tags=["Locations"])
    api_router.include_router(posts_router, prefix="/posts", tags=["Posts"])
    api_router.include_router(comments_router, prefix="/comments", tags=["Comments"])
    api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
    api_router.include_router(health_router, tags=["Health"])
    app.include_router(api_router)

    settings.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    app.mount(
        MEDIA_URL.rstrip("/"), StaticFiles(directory=settings.MEDIA_DIR), name="media"
    )

    return app
