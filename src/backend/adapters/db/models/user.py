import uuid

from adapters.db.models.base import Base, MyLongSTR, MyShortSTR
from sqlalchemy import false, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    login: Mapped[MyShortSTR] = mapped_column(unique=True)
    email: Mapped[MyShortSTR] = mapped_column(unique=True)
    pass_hash: Mapped[MyLongSTR]
    is_admin: Mapped[bool] = mapped_column(default=False, server_default=false())
