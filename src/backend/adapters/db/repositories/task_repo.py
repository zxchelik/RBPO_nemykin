import datetime as dt
import uuid
from typing import Optional, Sequence

from adapters.db.models.task import Task
from domain.value_objects.task_priority import TaskPriority
from domain.value_objects.task_state import TaskState
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository, ForbiddenError, NotFoundError


class TaskRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def _require_owned(self, task_id: uuid.UUID, owner_id: uuid.UUID) -> Task:
        res = await self.session.execute(
            select(Task)
            .options(selectinload(Task.owner))
            .where(and_(Task.id == task_id, Task.owner_id == owner_id))
        )
        task = res.scalars().first()
        if not task:
            res2 = await self.session.execute(select(Task.id).where(Task.id == task_id))
            if res2.scalars().first():
                raise ForbiddenError("Task belongs to another user")
            raise NotFoundError("Task not found")
        return task

    async def create(
        self,
        *,
        owner_id: uuid.UUID,
        name: str,
        description: str,
        state: TaskState,
        priority: TaskPriority,
        due_at: Optional[dt.datetime] = None,
    ) -> Task:
        task_kwargs = dict(
            owner_id=owner_id,
            name=name,
            description=description,
            state=state,
            priority=priority,
        )
        if hasattr(Task, "due_at") and due_at is not None:
            task_kwargs["due_at"] = due_at

        task = Task(**task_kwargs)
        async with self._transaction():
            self.session.add(task)
            await self._flush_refresh(task)
        return task

    async def get(self, task_id: uuid.UUID, *, owner_id: uuid.UUID) -> Task:
        return await self._require_owned(task_id, owner_id)

    async def list(
        self,
        *,
        owner_id: uuid.UUID,
        state: Optional[TaskState] = None,
        due_before: Optional[dt.datetime] = None,
        limit: int = 50,
        offset: int = 0,
        order_by_due_first: bool = True,
    ) -> Sequence[Task]:
        filters = [Task.owner_id == owner_id]
        if state is not None:
            filters.append(Task.state == state)
        if due_before is not None and hasattr(Task, "due_at"):
            filters.append(getattr(Task, "due_at") < due_before)  # type: ignore[misc]

        stmt = (
            select(Task)
            .options(selectinload(Task.owner))
            .where(and_(*filters))
            .limit(limit)
            .offset(offset)
        )

        if hasattr(Task, "due_at") and order_by_due_first:
            due_col = getattr(Task, "due_at")
            stmt = stmt.order_by(due_col.asc().nulls_last(), Task.priority.desc())
        else:
            stmt = stmt.order_by(
                Task.priority.desc(),
                Task.created_at.asc() if hasattr(Task, "created_at") else Task.id.asc(),
            )

        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def update(
        self,
        task_id: uuid.UUID,
        *,
        owner_id: uuid.UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        state: Optional[TaskState] = None,
        priority: Optional[TaskPriority] = None,
        due_at: Optional[dt.datetime] = None,
    ) -> Task:
        task = await self._require_owned(task_id, owner_id)

        if name is not None:
            task.name = name
        if description is not None:
            task.description = description
        if state is not None:
            task.state = state
        if priority is not None:
            task.priority = priority
        if due_at is not None and hasattr(Task, "due_at"):
            setattr(task, "due_at", due_at)

        async with self._transaction():
            await self._flush_refresh(task)
        return task

    async def delete(self, task_id: uuid.UUID, *, owner_id: uuid.UUID) -> None:
        task = await self._require_owned(task_id, owner_id)
        async with self._transaction():
            await self.session.delete(task)

    async def count(
        self,
        *,
        owner_id: uuid.UUID,
        state: Optional[TaskState] = None,
        due_before: Optional[dt.datetime] = None,
    ) -> int:
        filters = [Task.owner_id == owner_id]
        if state is not None:
            filters.append(Task.state == state)
        if due_before is not None and hasattr(Task, "due_at"):
            filters.append(getattr(Task, "due_at") < due_before)  # type: ignore[misc]

        res = await self.session.execute(
            select(func.count()).select_from(
                select(Task.id).where(and_(*filters)).subquery()
            )
        )
        return int(res.scalar_one())

    async def admin_list_all(
        self,
        *,
        state: Optional[TaskState] = None,
        due_before: Optional[dt.datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Task]:
        filters = []
        if state is not None:
            filters.append(Task.state == state)
        if due_before is not None and hasattr(Task, "due_at"):
            filters.append(getattr(Task, "due_at") < due_before)

        stmt = (
            select(Task)
            .options(selectinload(Task.owner))
            .where(and_(*filters) if filters else True)
            .limit(limit)
            .offset(offset)
        )
        if hasattr(Task, "due_at"):
            stmt = stmt.order_by(
                getattr(Task, "due_at").asc().nulls_last(), Task.priority.desc()
            )
        else:
            stmt = stmt.order_by(Task.priority.desc(), Task.id.asc())

        res = await self.session.execute(stmt)
        return list(res.scalars().all())
