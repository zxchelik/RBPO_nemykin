import uuid
from typing import TYPE_CHECKING

from adapters.db.models.base import Base, MyLongSTR, MyShortSTR
from domain.value_objects.task_priority import TaskPriority
from domain.value_objects.task_state import TaskState
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from adapters.db.models.user import User


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[MyShortSTR]
    description: Mapped[MyLongSTR]
    state: Mapped[TaskState] = mapped_column(
        SQLEnum(
            TaskState,
            native_enum=False,  # строка + CHECK
            create_constraint=True,  # включаем CHECK
            validate_strings=True,  # проверка на уровне Python
            name="task_state",  # имя для CHECK (важно для alembic)
            values_callable=lambda e: [
                m.value for m in e
            ],  # чтобы в бд был value, а не name
        ),
        nullable=False,
        index=True,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SQLEnum(
            TaskPriority,
            native_enum=False,  # строка + CHECK
            create_constraint=True,  # включаем CHECK
            validate_strings=True,  # проверка на уровне Python
            name="task_priority",  # имя для CHECK (важно для alembic)
            values_callable=lambda e: [
                m.value for m in e
            ],  # чтобы в бд был value, а не name
        ),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        index=True,
    )

    owner: Mapped["User"] = relationship(lazy="selectin")
