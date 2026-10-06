from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_TOO_LARGE_DETAIL = "Слишком большое тело запроса"
MULTIPART_OVERHEAD_BYTES = 65_536


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_body_bytes: int, max_upload_bytes: int):
        self.app = app
        self.max_body_bytes = max_body_bytes
        self.max_upload_bytes = max_upload_bytes + MULTIPART_OVERHEAD_BYTES

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        content_type = headers.get(b"content-type", b"").lower()
        max_bytes = (
            self.max_upload_bytes
            if content_type.startswith(b"multipart/form-data")
            else self.max_body_bytes
        )
        content_length = headers.get(b"content-length")
        if (
            content_length is not None
            and content_length.isdigit()
            and int(content_length) > max_bytes
        ):
            response = JSONResponse(
                {"detail": REQUEST_TOO_LARGE_DETAIL},
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            )
            await response(scope, receive, send)
            return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=REQUEST_TOO_LARGE_DETAIL,
                    )
            return message

        await self.app(scope, limited_receive, send)
