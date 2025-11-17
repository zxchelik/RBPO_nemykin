import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR

logger = logging.getLogger(__name__)


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

    return JSONResponse(status_code=status_code, content=problem)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Хэндлер для HTTPException (404, 401, 403 и т.п.)
    """
    title = exc.detail if isinstance(exc.detail, str) else "HTTP error"

    return problem_response(
        request,
        status_code=exc.status_code,
        title=title,
        detail="Request cannot be processed.",
        type_=f"https://example.com/problems/http-{exc.status_code}",
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Хэндлер для ошибок валидации FastAPI/Pydantic.
    """
    errors = exc.errors()
    extra = {"errors": errors}
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
    logger.exception(
        "Unhandled exception (correlation_id=%s): %s", correlation_id, exc
    )

    return problem_response(
        request,
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail="An unexpected error has occurred. Please contact support.",
        type_="https://example.com/problems/internal-server-error",
    )
