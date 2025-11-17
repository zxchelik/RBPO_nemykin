from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

import pytest
from app.api.v1.routers import uploads as uploads_module
from app.api.v1.schemas import TaskCreate
from app.main import app
from domain.value_objects.task_priority import TaskPriority
from domain.value_objects.task_state import TaskState
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

if not any(getattr(route, "path", None) == "/__test__/http-error" for route in app.router.routes):

    @app.get("/__test__/http-error")
    def _raise_http_error():
        raise HTTPException(status_code=403, detail="Sensitive detail")


@pytest.fixture()
def client() -> TestClient:
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
