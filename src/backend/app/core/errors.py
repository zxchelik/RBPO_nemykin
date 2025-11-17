import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR

logger = logging.getLogger(__name__)


class ProblemException(Exception):
    """
    Custom exception that carries metadata for RFC 7807 responses.
    """

    def __init__(
        self,
        *,
        status_code: int,
        title: str,
        detail: str,
        type_: str = "about:blank",
        errors: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.type_ = type_
        self.errors = errors or {}


HTTP_STATUS_TITLES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    413: "Payload Too Large",
    429: "Too Many Requests",
    500: "Internal Server Error",
}


def get_correlation_id(request: Request) -> str:
    """
    Возвращаем correlation_id из state или заголовка.
    Если его ещё нет, создаём новый и кладём в state.
    """
    cid: Optional[str] = getattr(request.state, "correlation_id", None)
    if not cid:
        cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = cid
    return cid


def problem_response(
    request: Request,
    *,
    status_code: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    extra: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    correlation_id = get_correlation_id(request)

    problem: Dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url),
        "correlation_id": correlation_id,
    }

    if extra:
        problem.update(extra)

    return JSONResponse(
        status_code=status_code,
        content=problem,
        headers={"X-Correlation-ID": correlation_id},
    )


async def problem_exception_handler(request: Request, exc: ProblemException) -> JSONResponse:
    extra = {"errors": exc.errors} if exc.errors else None
    return problem_response(
        request,
        status_code=exc.status_code,
        title=exc.title,
        detail=exc.detail,
        type_=exc.type_,
        extra=extra,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Хэндлер для HTTPException (404, 401, 403 и т.п.)
    """
    title = HTTP_STATUS_TITLES.get(exc.status_code, "HTTP error")
    error_map: Dict[str, Any] = {"code": "http_error"}
    if isinstance(exc.detail, dict):
        error_map.update(exc.detail)
    elif isinstance(exc.detail, list):
        error_map["messages"] = exc.detail
    elif isinstance(exc.detail, str) and exc.status_code < 500:
        error_map["message"] = exc.detail

    return problem_response(
        request,
        status_code=exc.status_code,
        title=title,
        detail="Request cannot be processed.",
        type_=f"https://example.com/problems/http-{exc.status_code}",
        extra={"errors": error_map},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Хэндлер для ошибок валидации FastAPI/Pydantic.
    """
    errors = exc.errors()
    extra = {"errors": {"fields": errors}}
    return problem_response(
        request,
        status_code=HTTP_400_BAD_REQUEST,
        title="Validation error",
        detail="Request validation failed.",
        type_="https://example.com/problems/validation-error",
        extra=extra,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Хэндлер для всех неожиданных ошибок.
    """
    correlation_id = get_correlation_id(request)
    logger.exception("Unhandled exception (correlation_id=%s): %s", correlation_id, exc)

    return problem_response(
        request,
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail="An unexpected error has occurred. Please contact support.",
        type_="https://example.com/problems/internal-server-error",
    )
