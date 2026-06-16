import time
from uuid import uuid4

from fastapi import FastAPI, Request

from app.core.config import settings


def register_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = request.headers.get(settings.request_id_header, str(uuid4()))
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)
        response.headers[settings.request_id_header] = request_id
        response.headers["X-Process-Time-Ms"] = f"{(time.perf_counter() - start) * 1000:.2f}"
        return response
