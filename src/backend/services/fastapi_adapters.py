from adapters.db.repositories.base import ForbiddenError as RepoForbidden
from adapters.db.repositories.base import NotFoundError as RepoNotFound
from fastapi import HTTPException, status
from services.errors import ConflictError


def map_service_errors(exc: Exception) -> None:
    if isinstance(exc, RepoForbidden):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, RepoNotFound):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    # unknown -> 500
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error",
    )
