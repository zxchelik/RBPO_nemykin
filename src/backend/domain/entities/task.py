from uuid import UUID

from domain.value_objects.task_priority import TaskPriority
from domain.value_objects.task_state import TaskState
from pydantic import BaseModel


class Task(BaseModel):
    id: UUID
    name: str
    description: str
    state: TaskState
    priority: TaskPriority
    owner_id: UUID
