"""Local filesystem storage helpers for uploaded documents (MVP storage backend)."""
from __future__ import annotations

import os
import uuid

from app.core.config import get_settings

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "png", "jpg", "jpeg", "xlsx"}


def get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def is_supported_file(filename: str) -> bool:
    return get_extension(filename) in ALLOWED_EXTENSIONS


def build_storage_path(document_id: str, filename: str) -> str:
    settings = get_settings()
    ext = get_extension(filename)
    directory = os.path.join(settings.storage_root, document_id)
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, f"original.{ext}")


async def save_upload(document_id: str, filename: str, file_obj) -> tuple[str, int]:
    """Persists an UploadFile-like object to disk. Returns (path, size_bytes)."""
    path = build_storage_path(document_id, filename)
    size = 0
    with open(path, "wb") as out:
        while chunk := await file_obj.read(1024 * 1024):
            out.write(chunk)
            size += len(chunk)
    return path, size


def new_document_id() -> str:
    return str(uuid.uuid4())
