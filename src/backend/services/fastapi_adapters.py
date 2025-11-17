from adapters.db.repositories.base import ForbiddenError as RepoForbidden
from adapters.db.repositories.base import NotFoundError as RepoNotFound
from app.core.errors import ProblemException
from fastapi import status
from services.errors import ConflictError


def map_service_errors(exc: Exception) -> None:
    if isinstance(exc, RepoForbidden):
        raise ProblemException(
            status_code=status.HTTP_403_FORBIDDEN,
            title="Forbidden",
            detail="You are not allowed to perform this action.",
            type_="https://example.com/problems/forbidden",
            errors={"code": "tasks.forbidden"},
        ) from exc
    if isinstance(exc, RepoNotFound):
        raise ProblemException(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Not Found",
            detail="Requested entity was not found.",
            type_="https://example.com/problems/not-found",
            errors={"code": "tasks.not_found"},
        ) from exc
    if isinstance(exc, ConflictError):
        raise ProblemException(
            status_code=status.HTTP_409_CONFLICT,
            title="Conflict",
            detail="Resource is in conflicting state.",
            type_="https://example.com/problems/conflict",
            errors={"code": "tasks.conflict"},
        ) from exc
    # unknown -> 500
    raise ProblemException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail="Internal server error.",
        type_="https://example.com/problems/internal",
        errors={"code": "tasks.internal_error"},
    ) from exc
