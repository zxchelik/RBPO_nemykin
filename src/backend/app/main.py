from contextlib import asynccontextmanager
from typing import AsyncIterator

from app.api.v1.routers import auth as auth_router
from app.api.v1.routers import tasks as tasks_router
from app.api.v1.routers import uploads as uploads_router
from app.core import errors as error_handlers
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    r = APIRouter(prefix="/api/v1")
    app.add_exception_handler(
        StarletteHTTPException,
        error_handlers.http_exception_handler,
    )
    app.add_exception_handler(
        RequestValidationError,
        error_handlers.validation_exception_handler,
    )
    app.add_exception_handler(
        Exception,
        error_handlers.unhandled_exception_handler,
    )
    r.include_router(uploads_router.router)
    r.include_router(auth_router.router)
    r.include_router(tasks_router.router)
    r.include_router(tasks_router.admin_router)
    app.include_router(r)
    yield


app = FastAPI(lifespan=lifespan, title="SecDev Course App", version="0.1.0")


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


@app.middleware("http")
async def add_correlation_id_header(request: Request, call_next):
    """
    Middleware: гарантирует наличие correlation_id и добавляет его в заголовок ответа.
    """
    cid = error_handlers.get_correlation_id(request)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Normalize FastAPI HTTPException into our error envelope
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
    )


@app.get("/health")
def health():
    return {"status": "ok"}
