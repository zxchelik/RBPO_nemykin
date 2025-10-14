import datetime as dt
import uuid
from typing import Optional

from app.api.v1.deps.auth import admin_required, get_current_user
from app.api.v1.schemas import TaskCreate, TaskRead, TaskUpdate
from domain.value_objects.task_state import TaskState
from fastapi import APIRouter, Depends, Query
from services.fastapi_adapters import map_service_errors
from services.task_service import TaskService, get_task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskRead, status_code=201)
async def create_task(
    payload: TaskCreate,
    svc: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
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


@router.get("/", response_model=list[TaskRead])
async def list_tasks(
    status: Optional[TaskState] = Query(None, alias="status"),
    due_before: Optional[dt.datetime] = Query(None, alias="due<"),
    limit: int = 50,
    offset: int = 0,
    svc: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
    try:
        tasks = await svc.list_tasks(
            owner_id=current_user.id,
            status=status,
            due_before=due_before,
            limit=limit,
            offset=offset,
        )
        return tasks
    except Exception as e:
        map_service_errors(e)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: uuid.UUID,
    svc: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
    try:
        return await svc.get_task(task_id, owner_id=current_user.id)
    except Exception as e:
        map_service_errors(e)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    svc: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
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


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: uuid.UUID,
    svc: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
    try:
        await svc.delete_task(task_id, owner_id=current_user.id)
        return {"ok": True}
    except Exception as e:
        map_service_errors(e)


# ------------------------------ Admin endpoints ------------------------------
admin_router = APIRouter(prefix="/admin/tasks", tags=["admin:tasks"])


@admin_router.get("/", response_model=list[TaskRead])
async def admin_list_all_tasks(
    status: Optional[TaskState] = Query(None, alias="status"),
    due_before: Optional[dt.datetime] = Query(None, alias="due<"),
    limit: int = 100,
    offset: int = 0,
    svc: TaskService = Depends(get_task_service),
    _admin=Depends(admin_required),
):
    try:
        return await svc.admin_list_all(
            status=status, due_before=due_before, limit=limit, offset=offset
        )
    except Exception as e:
        map_service_errors(e)
