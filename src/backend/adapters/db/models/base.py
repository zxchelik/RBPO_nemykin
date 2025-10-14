from datetime import datetime, UTC
from typing import Optional, Annotated

from sqlalchemy import BigInteger, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import String
from sqlalchemy import DateTime

# Custom types
MyShortSTR = Annotated[str, mapped_column(String(63))]
MyLongSTR = Annotated[str, mapped_column(String(255))]
TgId = Annotated[int, mapped_column(BigInteger)]


# Base


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True  # чтобы не создавать таблицу для Base


    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )

