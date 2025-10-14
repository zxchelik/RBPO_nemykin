from __future__ import annotations

import datetime as dt
import uuid
from typing import Optional

from domain.value_objects.task_priority import TaskPriority
from domain.value_objects.task_state import TaskState
from pydantic import BaseModel, EmailStr


# -------- Auth --------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: uuid.UUID
    exp: int


# -------- Users --------
class UserRead(BaseModel):
    id: uuid.UUID
    login: str
    email: EmailStr
    is_admin: bool

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    login: str
    email: EmailStr
    password: str


# -------- Tasks --------
class TaskCreate(BaseModel):
    name: str
    description: str
    state: TaskState
    priority: TaskPriority
    due_at: Optional[dt.datetime] = None


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    state: Optional[TaskState] = None
    priority: Optional[TaskPriority] = None
    due_at: Optional[dt.datetime] = None


class TaskRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    state: TaskState
    priority: TaskPriority
    owner_id: uuid.UUID

    class Config:
        from_attributes = True
