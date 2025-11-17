import os
from pathlib import Path
from typing import Tuple

from app.core import errors as error_handlers
from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

router = APIRouter(prefix="/uploads", tags=["uploads"])

UPLOAD_DIR = Path("uploads")
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}
SECURE_FILE_MODE = 0o600


def detect_file_type(data: bytes) -> Tuple[str, str]:
    """
    Минимальная проверка magic bytes.

    Возвращает (kind, extension):
    - kind: "png" / "jpeg" / "pdf" / "unknown"
    - extension: ".png" / ".jpg" / ".pdf" / ""
    """
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg", ".jpg"
    if data.startswith(b"%PDF-"):
        return "pdf", ".pdf"
    return "unknown", ""


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Безопасная загрузка файла",
)
async def upload_file(request: Request, file: UploadFile = File(...)):
    # Читаем файл в память
    data = await file.read()

    if len(data) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file is too large.",
        )

    detected_kind, ext = detect_file_type(data)

    if detected_kind == "unknown" or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported or invalid file type.",
        )

    # Имя файла: correlation_id + расширение (UUID внутри)
    cid = error_handlers.get_correlation_id(request)
    safe_name = f"{cid}{ext}"

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    if UPLOAD_DIR.is_symlink():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload directory misconfigured.",
        )

    target_path = (UPLOAD_DIR / safe_name).resolve()
    upload_root = UPLOAD_DIR.resolve()

    # Доп. защита: убеждаемся, что файл пишется внутрь UPLOAD_DIR
    try:
        target_path.relative_to(upload_root)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid upload path.",
        )

    if target_path.exists() and target_path.is_symlink():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid upload path.",
        )

    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(target_path, flags, SECURE_FILE_MODE)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)
    except FileExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="File already exists.",
        )
    except OSError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not store the uploaded file.",
        )

    return {
        "filename": safe_name,
        "size": len(data),
        "content_type": file.content_type,
        "kind": detected_kind,
    }
