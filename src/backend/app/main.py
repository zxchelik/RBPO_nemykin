from app.api.v1.routers import auth as auth_router
from app.api.v1.routers import tasks as tasks_router
from app.api.v1.routers import uploads as uploads_router
from app.core import errors as error_handlers
from app.core.errors import ProblemException
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


app = FastAPI(title="SecDev Course App", version="0.1.0")

app.add_exception_handler(
    ProblemException,
    error_handlers.problem_exception_handler,
)
app.add_exception_handler(
    HTTPException,
    error_handlers.http_exception_handler,
)
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


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(uploads_router.router)
api_router.include_router(auth_router.router)
api_router.include_router(tasks_router.router)
api_router.include_router(tasks_router.admin_router)
app.include_router(api_router)


@app.middleware("http")
async def add_correlation_id_header(request: Request, call_next):
    """
    Middleware: гарантирует наличие correlation_id и добавляет его в заголовок ответа.
    """
    cid = error_handlers.get_correlation_id(request)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response


@app.get("/health")
def health():
    return {"status": "ok"}
