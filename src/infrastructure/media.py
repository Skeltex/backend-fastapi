import re
import uuid

from src.core.settings import MEDIA_URL, settings

POST_IMAGES_DIR = "posts"
IMAGE_SIGNATURES = (
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
)
UPLOADED_IMAGE_URL = re.compile(
    rf"{MEDIA_URL}{POST_IMAGES_DIR}/[0-9a-f]{{32}}\.(?:jpg|png|gif|webp)"
)


def detect_image_extension(data: bytes) -> str | None:
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return next(
        (
            extension
            for signature, extension in IMAGE_SIGNATURES
            if data.startswith(signature)
        ),
        None,
    )


def save_post_image(data: bytes, extension: str) -> str:
    directory = settings.MEDIA_DIR / POST_IMAGES_DIR
    directory.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.{extension}"
    (directory / name).write_bytes(data)
    return f"{MEDIA_URL}{POST_IMAGES_DIR}/{name}"


def delete_post_image(image_url: str | None) -> None:
    if image_url is not None and UPLOADED_IMAGE_URL.fullmatch(image_url):
        (settings.MEDIA_DIR / image_url.removeprefix(MEDIA_URL)).unlink(missing_ok=True)
