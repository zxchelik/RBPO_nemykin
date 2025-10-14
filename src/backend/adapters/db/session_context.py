from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.core.settings import config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(url=config.database.url, echo=False)
sessionmaker = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def get_async_session_manager() -> AsyncGenerator[AsyncSession, None]:
    session = sessionmaker()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_async_session():
    async with get_async_session_manager() as session:
        yield session
