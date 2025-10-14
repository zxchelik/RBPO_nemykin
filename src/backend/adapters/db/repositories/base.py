from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class RepositoryError(RuntimeError):
    pass


class NotFoundError(RepositoryError):
    pass


class ForbiddenError(RepositoryError):
    pass


class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _flush_refresh(self, instance: Any) -> Any:
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    @asynccontextmanager
    async def _transaction(self):
        try:
            yield
        except Exception:
            await self.session.rollback()
            raise
        else:
            await self.session.commit()
