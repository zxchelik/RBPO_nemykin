import datetime
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core import settings
from app.core.settings import config

engine = create_async_engine(url=config.database.url, echo=False)
sessionmaker = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def get_async_session_manager() -> AsyncGenerator[AsyncSession, None]:
    session = sessionmaker()
    try:
        yield session
    except Exception as e:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_async_session():
    async with get_async_session_manager() as session:
        yield session
