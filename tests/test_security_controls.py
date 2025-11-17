from __future__ import annotations

import datetime as dt
import os
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from adapters.db.repositories.base import ForbiddenError
from app.api.v1.deps import auth as auth_deps
from app.api.v1.routers import uploads as uploads_module
from app.api.v1.schemas import TaskCreate, TaskRead, TaskUpdate
from app.main import app
from domain.value_objects.task_priority import TaskPriority
from domain.value_objects.task_state import TaskState
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from services.task_service import get_task_service

if not any(getattr(route, "path", None) == "/__test__/http-error" for route in app.router.routes):

    @app.get("/__test__/http-error")
    def _raise_http_error():
        raise HTTPException(status_code=403, detail="Sensitive detail")


class DummyTaskService:
    def __init__(self):
        self.list_calls: list[dict] = []
        self.admin_calls: list[dict] = []
        self.create_calls: list[dict] = []
        self.update_calls: list[dict] = []
        self.delete_calls: list[uuid.UUID] = []
        self.sample_task = TaskRead(
            id=uuid.uuid4(),
            name="Sample",
            description="Desc",
            state=TaskState.TODO,
            priority=TaskPriority.LOW,
            owner_id=uuid.uuid4(),
        )

    async def list_tasks(
        self,
        *,
        owner_id,
        status=None,
        due_before=None,
        limit=50,
        offset=0,
    ):
        self.list_calls.append(
            {
                "owner_id": owner_id,
                "status": status,
                "due_before": due_before,
                "limit": limit,
                "offset": offset,
            }
        )
        return []

    async def create_task(self, **kwargs):
        self.create_calls.append(kwargs)
        return self.sample_task

    async def get_task(self, *_, **__):
        return self.sample_task

    async def update_task(self, *_, **kwargs):
        self.update_calls.append(kwargs)
        return self.sample_task

    async def delete_task(self, task_id, *, owner_id):
        self.delete_calls.append(task_id)
        return None

    async def admin_list_all(
        self,
        *,
        status=None,
        due_before=None,
        limit=100,
        offset=0,
    ):
        self.admin_calls.append(
            {
                "status": status,
                "due_before": due_before,
                "limit": limit,
                "offset": offset,
            }
        )
        return []


@pytest.fixture()
def auth_overrides():
    user = SimpleNamespace(id=uuid.uuid4(), is_admin=True)

    def _current_user_override():
        return user

    def _admin_override():
        return user

    app.dependency_overrides[auth_deps.get_current_user] = _current_user_override
    app.dependency_overrides[auth_deps.admin_required] = _admin_override
    try:
        yield user
    finally:
        app.dependency_overrides.pop(auth_deps.get_current_user, None)
        app.dependency_overrides.pop(auth_deps.admin_required, None)


@pytest.fixture()
def task_service_spy():
    service = DummyTaskService()

    async def _override():
        return service

    app.dependency_overrides[get_task_service] = _override
    try:
        yield service
    finally:
        app.dependency_overrides.pop(get_task_service, None)


@pytest.fixture()
def client(auth_overrides, task_service_spy) -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def uploads_dir(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(uploads_module, "UPLOAD_DIR", upload_dir)
    return upload_dir


def test_problem_details_include_correlation_id(client: TestClient):
    response = client.get(
        "/api/v1/unknown-route",
        headers={"X-Correlation-ID": "deadbeef-cid"},
    )
    assert response.status_code == 404
    body = response.json()
    assert body["title"] == "Not Found"
    assert body["detail"] == "Request cannot be processed."
    assert body["correlation_id"] == "deadbeef-cid"
    assert response.headers["x-correlation-id"] == "deadbeef-cid"
    assert body["errors"]["code"] == "http_error"
    assert body["errors"]["message"] == "Not Found"


def test_problem_response_masks_http_exception(client: TestClient):
    response = client.get("/__test__/http-error", headers={"X-Correlation-ID": "cid-1"})
    assert response.status_code == 403
    body = response.json()
    assert body["title"] == "Forbidden"
    assert body["detail"] == "Request cannot be processed."
    assert body["errors"]["code"] == "http_error"
    assert body["errors"]["message"] == "Sensitive detail"
    assert body["correlation_id"] == "cid-1"


def test_task_create_normalizes_and_validates_fields():
    due_at = dt.datetime(2024, 1, 1, 12, tzinfo=dt.timezone(dt.timedelta(hours=3)))
    task = TaskCreate(
        name="  Demo Task  ",
        description="  Important description ",
        state=TaskState.TODO,
        priority=TaskPriority.LOW,
        due_at=due_at,
    )
    assert task.name == "Demo Task"
    assert task.description == "Important description"
    assert task.due_at == dt.datetime(2024, 1, 1, 9, tzinfo=dt.timezone.utc)

    with pytest.raises(ValidationError):
        TaskCreate(
            name="  sh  ",  # trimmed -> "sh" (too short)
            description=" ok description ",
            state=TaskState.TODO,
            priority=TaskPriority.LOW,
        )


def test_upload_rejects_symlink_targets(client: TestClient, uploads_dir: Path):
    cid = "123e4567-e89b-12d3-a456-426614174000"
    secret_target = uploads_dir.parent / "secret.txt"
    secret_target.write_text("secret-value")

    malicious_link = uploads_dir / f"{cid}.png"
    os.symlink(secret_target, malicious_link)

    response = client.post(
        "/api/v1/uploads",
        headers={"X-Correlation-ID": cid},
        files={"file": ("test.png", b"\x89PNG\r\n\x1a\npayload", "image/png")},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["errors"]["message"] == "Invalid upload path."
    assert malicious_link.is_symlink()
    assert secret_target.read_text() == "secret-value"


def test_upload_rejects_large_files(client: TestClient, uploads_dir, monkeypatch):
    monkeypatch.setattr(uploads_module, "MAX_UPLOAD_SIZE", 64)
    cid = "deadbeef-dead-beef-dead-beefdeadbeef"
    data = b"\x89PNG\r\n\x1a\n" + b"a" * 100
    response = client.post(
        "/api/v1/uploads",
        headers={"X-Correlation-ID": cid},
        files={"file": ("huge.png", data, "image/png")},
    )
    assert response.status_code == 413
    body = response.json()
    assert body["errors"]["message"] == "Uploaded file is too large."


def test_upload_rejects_invalid_signature(client: TestClient, uploads_dir, monkeypatch):
    monkeypatch.setattr(uploads_module, "MAX_UPLOAD_SIZE", 1024)
    response = client.post(
        "/api/v1/uploads",
        headers={"X-Correlation-ID": "cid"},
        files={"file": ("doc.png", b"not-a-real-signature", "image/png")},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["errors"]["message"] == "Unsupported or invalid file type."


def test_list_tasks_rejects_large_limit(client: TestClient):
    response = client.get("/api/v1/tasks/?limit=5000")
    assert response.status_code == 400
    body = response.json()
    assert body["title"] == "Validation error"
    violation = body["errors"]["fields"][0]
    assert violation["loc"] == ["query", "limit"]
    assert violation["type"] == "less_than_equal"


def test_list_tasks_normalizes_due_before(client: TestClient, task_service_spy: DummyTaskService):
    response = client.get("/api/v1/tasks/", params={"due<": "2024-02-01T00:00:00"})
    assert response.status_code == 200
    assert response.json() == []
    call = task_service_spy.list_calls[-1]
    assert call["due_before"].tzinfo == dt.timezone.utc
    assert call["due_before"].isoformat() == "2024-02-01T00:00:00+00:00"


def test_task_create_rejects_long_description():
    long_text = "A" * 3000
    with pytest.raises(ValidationError):
        TaskCreate(
            name="valid name",
            description=long_text,
            state=TaskState.TODO,
            priority=TaskPriority.MEDIUM,
        )


def test_task_update_trims_optional_fields():
    payload = TaskUpdate(
        name="  Trimmed ",
        description="  Desc  ",
        due_at=dt.datetime(2024, 5, 1, 12, 0, 0),
    )
    assert payload.name == "Trimmed"
    assert payload.description == "Desc"
    assert payload.due_at.tzinfo == dt.timezone.utc


def test_task_create_converts_naive_due_at_to_utc():
    due = dt.datetime(2024, 1, 1, 12, 30, 0)
    task = TaskCreate(
        name="Task",
        description="Desc",
        state=TaskState.DONE,
        priority=TaskPriority.HIGH,
        due_at=due,
    )
    assert task.due_at.tzinfo == dt.timezone.utc
    assert task.due_at.isoformat() == "2024-01-01T12:30:00+00:00"


def test_upload_directory_symlink_rejected(client: TestClient, uploads_dir: Path):
    real_dir = uploads_dir.parent / "real_uploads"
    real_dir.mkdir()
    uploads_dir.rmdir()
    uploads_dir.symlink_to(real_dir, target_is_directory=True)

    response = client.post(
        "/api/v1/uploads",
        headers={"X-Correlation-ID": "cid-symlink"},
        files={"file": ("test.png", b"\x89PNG\r\n\x1a\npayload", "image/png")},
    )
    assert response.status_code == 500
    body = response.json()
    assert body["title"] == "Internal Server Error"
    assert body["status"] == 500


def test_upload_conflict_when_file_exists(client: TestClient, uploads_dir, monkeypatch):
    monkeypatch.setattr(uploads_module, "MAX_UPLOAD_SIZE", 1024 * 1024)
    data = b"\x89PNG\r\n\x1a\npayload"
    headers = {"X-Correlation-ID": "same-id"}

    first = client.post(
        "/api/v1/uploads",
        headers=headers,
        files={"file": ("test.png", data, "image/png")},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/uploads",
        headers=headers,
        files={"file": ("test.png", data, "image/png")},
    )
    assert second.status_code == 409
    assert second.json()["errors"]["message"] == "File already exists."


def test_admin_list_tasks_enforces_limit(client: TestClient):
    response = client.get("/api/v1/admin/tasks/?limit=999")
    assert response.status_code == 400
    assert response.json()["title"] == "Validation error"


def test_admin_list_tasks_normalizes_due_before(
    client: TestClient, task_service_spy: DummyTaskService
):
    response = client.get(
        "/api/v1/admin/tasks/",
        params={"due<": "2024-03-01T03:00:00+03:00"},
    )
    assert response.status_code == 200
    call = task_service_spy.admin_calls[-1]
    assert call["due_before"].tzinfo == dt.timezone.utc
    assert call["due_before"].isoformat() == "2024-03-01T00:00:00+00:00"


def test_list_tasks_rejects_negative_offset(client: TestClient):
    response = client.get("/api/v1/tasks/?offset=-5")
    assert response.status_code == 400
    violation = response.json()["errors"]["fields"][0]
    assert violation["loc"] == ["query", "offset"]
    assert violation["type"] == "greater_than_equal"


def test_tasks_endpoint_maps_repo_forbidden(client: TestClient):
    prev_override = app.dependency_overrides[get_task_service]

    class FailingService:
        async def list_tasks(self, **kwargs):
            raise ForbiddenError("nope")

    async def _override():
        return FailingService()

    app.dependency_overrides[get_task_service] = _override
    try:
        response = client.get("/api/v1/tasks/")
    finally:
        app.dependency_overrides[get_task_service] = prev_override

    assert response.status_code == 403
    body = response.json()
    assert body["title"] == "Forbidden"
    assert body["errors"]["code"] == "tasks.forbidden"


def test_problem_details_instance_matches_url(client: TestClient):
    response = client.get("/api/v1/nothing-here", headers={"X-Correlation-ID": "inst"})
    assert response.status_code == 404
    body = response.json()
    assert body["instance"].endswith("/api/v1/nothing-here")


def test_create_task_calls_service(client: TestClient, task_service_spy: DummyTaskService):
    payload = {
        "name": "My task",
        "description": "detail",
        "state": "todo",
        "priority": "low",
    }
    response = client.post("/api/v1/tasks/", json=payload)
    assert response.status_code == 201
    call = task_service_spy.create_calls[-1]
    assert call["name"] == "My task"
    assert call["description"] == "detail"


def test_get_task_returns_payload(client: TestClient):
    task_id = uuid.uuid4()
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Sample"


def test_update_task_passes_fields(client: TestClient, task_service_spy: DummyTaskService):
    task_id = uuid.uuid4()
    payload = {"name": "Updated", "priority": "high"}
    response = client.patch(f"/api/v1/tasks/{task_id}", json=payload)
    assert response.status_code == 200
    call = task_service_spy.update_calls[-1]
    assert call["name"] == "Updated"
    assert call["priority"] == TaskPriority.HIGH


def test_delete_task_returns_no_content(client: TestClient, task_service_spy: DummyTaskService):
    task_id = uuid.uuid4()
    response = client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 204
    assert task_id in task_service_spy.delete_calls
