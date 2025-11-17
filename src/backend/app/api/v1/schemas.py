from __future__ import annotations

import datetime as dt
import uuid
from typing import Optional

from domain.value_objects.task_priority import TaskPriority
from domain.value_objects.task_state import TaskState
from pydantic import BaseModel, EmailStr, Field, field_validator


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
    login: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


# -------- Tasks --------
MAX_NAME_LENGTH = 120
MAX_DESCRIPTION_LENGTH = 2000


class TaskBase(BaseModel):
    name: Optional[str] = Field(default=None, min_length=3, max_length=MAX_NAME_LENGTH)
    description: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=MAX_DESCRIPTION_LENGTH,
    )
    due_at: Optional[dt.datetime] = None

    @field_validator("name", "description", mode="before")
    @classmethod
    def _strip_text(cls, value: Optional[str]) -> Optional[str]:
        if isinstance(value, str):
            value = value.strip()
        return value

    @field_validator("due_at")
    @classmethod
    def _ensure_utc(cls, value: Optional[dt.datetime]) -> Optional[dt.datetime]:
        if value is None:
            return value
        if value.tzinfo is None:
            return value.replace(tzinfo=dt.timezone.utc)
        return value.astimezone(dt.timezone.utc)


class TaskCreate(TaskBase):
    name: str = Field(min_length=3, max_length=MAX_NAME_LENGTH)
    description: str = Field(min_length=1, max_length=MAX_DESCRIPTION_LENGTH)
    state: TaskState
    priority: TaskPriority


class TaskUpdate(TaskBase):
    state: Optional[TaskState] = None
    priority: Optional[TaskPriority] = None


class TaskRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    state: TaskState
    priority: TaskPriority
    owner_id: uuid.UUID

    class Config:
        from_attributes = True
