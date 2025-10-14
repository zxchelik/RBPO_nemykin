import uuid
import datetime as dt
from typing import Optional, Sequence

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.db.repositories.task_repo import TaskRepository
from adapters.db.repositories.base import NotFoundError as RepoNotFound, ForbiddenError as RepoForbidden
from adapters.db.session_context import get_async_session
from domain.value_objects.task_state import TaskState
from domain.value_objects.task_priority import TaskPriority


class TaskService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.tasks = TaskRepository(session)

    async def create_task(
        self,
        *,
        owner_id: uuid.UUID,
        name: str,
        description: str,
        state: TaskState,
        priority: TaskPriority,
        due_at: Optional[dt.datetime] = None,
    ):
        return await self.tasks.create(
            owner_id=owner_id,
            name=name,
            description=description,
            state=state,
            priority=priority,
            due_at=due_at,
        )

    async def get_task(self, task_id: uuid.UUID, *, owner_id: uuid.UUID):
        return await self.tasks.get(task_id, owner_id=owner_id)

    async def list_tasks(
        self,
        *,
        owner_id: uuid.UUID,
        status: Optional[TaskState] = None,
        due_before: Optional[dt.datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence:
        return await self.tasks.list(
            owner_id=owner_id,
            state=status,
            due_before=due_before,
            limit=limit,
            offset=offset,
        )

    async def update_task(
        self,
        task_id: uuid.UUID,
        *,
        owner_id: uuid.UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        state: Optional[TaskState] = None,
        priority: Optional[TaskPriority] = None,
        due_at: Optional[dt.datetime] = None,
    ):
        return await self.tasks.update(
            task_id,
            owner_id=owner_id,
            name=name,
            description=description,
            state=state,
            priority=priority,
            due_at=due_at,
        )

    async def delete_task(self, task_id: uuid.UUID, *, owner_id: uuid.UUID) -> None:
        await self.tasks.delete(task_id, owner_id=owner_id)

    async def count(self, *, owner_id: uuid.UUID, status: Optional[TaskState] = None, due_before: Optional[dt.datetime] = None) -> int:
        return await self.tasks.count(owner_id=owner_id, state=status, due_before=due_before)

    async def admin_list_all(
            self,
            *,
            status: Optional[TaskState] = None,
            due_before: Optional[dt.datetime] = None,
            limit: int = 100,
            offset: int = 0,
    ):
        return await self.tasks.admin_list_all(state=status, due_before=due_before, limit=limit, offset=offset)

async def get_task_service(session: AsyncSession = Depends(get_async_session)) -> TaskService:
    return TaskService(session)