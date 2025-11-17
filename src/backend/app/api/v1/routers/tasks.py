import datetime as dt
import uuid
from typing import Any, Optional, cast

from app.api.v1.deps.auth import admin_required, get_current_user
from app.api.v1.schemas import TaskCreate, TaskRead, TaskUpdate
from domain.value_objects.task_state import TaskState
from fastapi import APIRouter, Depends, Query, Response
from services.fastapi_adapters import map_service_errors
from services.task_service import TaskService, get_task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _normalize_dt(value: Optional[dt.datetime]) -> Optional[dt.datetime]:
    if value is None:
        return value
    if value.tzinfo is None:
        return value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(dt.timezone.utc)


@router.post("/", response_model=TaskRead, status_code=201)
async def create_task(
    payload: TaskCreate,
    svc: TaskService = Depends(get_task_service),
    current_user: Any = Depends(get_current_user),
) -> TaskRead:
    try:
        task = await svc.create_task(
            owner_id=current_user.id,
            name=payload.name,
            description=payload.description,
            state=payload.state,
            priority=payload.priority,
            due_at=payload.due_at,
        )
        return task
    except Exception as e:
        map_service_errors(e)
        raise


@router.get("/", response_model=list[TaskRead])
async def list_tasks(
    status: Optional[TaskState] = Query(default=None, alias="status"),
    due_before: Optional[dt.datetime] = Query(default=None, alias="due<"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=1000),
    svc: TaskService = Depends(get_task_service),
    current_user: Any = Depends(get_current_user),
) -> list[TaskRead]:
    try:
        tasks = cast(
            list[TaskRead],
            await svc.list_tasks(
                owner_id=current_user.id,
                status=status,
                due_before=_normalize_dt(due_before),
                limit=limit,
                offset=offset,
            ),
        )
        return tasks
    except Exception as e:
        map_service_errors(e)
        raise


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: uuid.UUID,
    svc: TaskService = Depends(get_task_service),
    current_user: Any = Depends(get_current_user),
) -> TaskRead:
    try:
        return await svc.get_task(task_id, owner_id=current_user.id)
    except Exception as e:
        map_service_errors(e)
        raise


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    svc: TaskService = Depends(get_task_service),
    current_user: Any = Depends(get_current_user),
) -> TaskRead:
    try:
        return await svc.update_task(
            task_id,
            owner_id=current_user.id,
            name=payload.name,
            description=payload.description,
            state=payload.state,
            priority=payload.priority,
            due_at=payload.due_at,
        )
    except Exception as e:
        map_service_errors(e)
        raise


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: uuid.UUID,
    svc: TaskService = Depends(get_task_service),
    current_user: Any = Depends(get_current_user),
) -> Response:
    try:
        await svc.delete_task(task_id, owner_id=current_user.id)
        return Response(status_code=204)
    except Exception as e:
        map_service_errors(e)
        raise


# ------------------------------ Admin endpoints ------------------------------
admin_router = APIRouter(prefix="/admin/tasks", tags=["admin:tasks"])


@admin_router.get("/", response_model=list[TaskRead])
async def admin_list_all_tasks(
    status: Optional[TaskState] = Query(default=None, alias="status"),
    due_before: Optional[dt.datetime] = Query(default=None, alias="due<"),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0, le=2000),
    svc: TaskService = Depends(get_task_service),
    _admin: Any = Depends(admin_required),
) -> list[TaskRead]:
    try:
        return cast(
            list[TaskRead],
            await svc.admin_list_all(
                status=status,
                due_before=_normalize_dt(due_before),
                limit=limit,
                offset=offset,
            ),
        )
    except Exception as e:
        map_service_errors(e)
        raise
