from typing import Any

from fastapi import Request


def get_request_id(request: Request | None) -> str | None:
    if request is None:
        return None

    request_id = getattr(request.state, "request_id", None)
    return str(request_id) if request_id else None


def api_success(
    data: Any,
    *,
    request: Request | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "error": None,
        "message": message,
        "request_id": get_request_id(request),
    }
