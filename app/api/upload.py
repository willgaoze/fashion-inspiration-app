"""Multipart image upload, AI classification, and persistence."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.image import Image
from app.schemas.image import ImageResponse
from app.services.ai_classifier import classify_image

router = APIRouter(prefix="/api", tags=["upload"])

_ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".webp"})
_ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/jpg", "image/png", "image/webp"},
)


def _validate_upload(filename: str | None, content_type: str | None) -> str:
    """Return the normalized lower-case extension (e.g. ``.jpg``) or raise 400."""
    if not filename or not filename.strip():
        raise HTTPException(status_code=400, detail="Missing filename")
    ext = Path(filename).suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type; allowed: jpg, jpeg, png, webp",
        )
    if content_type:
        base = content_type.split(";", 1)[0].strip().lower()
        if base not in _ALLOWED_CONTENT_TYPES and base not in (
            "application/octet-stream",
            "",
        ):
            raise HTTPException(status_code=400, detail="Unsupported content type")
    return ext


def _color_palette_to_db(value: Any) -> str | None:
    """Serialize classifier ``color_palette`` to the JSON string stored in the DB."""
    if value is None:
        return None
    if isinstance(value, list):
        if not value:
            return None
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, str):
        return value.strip() or None
    return None


def _merge_trend_and_location(trend_notes: Any, location_context: Any) -> str | None:
    """Combine trend notes and free-text location context for a single DB column."""
    parts: list[str] = []
    if isinstance(trend_notes, str) and trend_notes.strip():
        parts.append(trend_notes.strip())
    if isinstance(location_context, str) and location_context.strip():
        parts.append(location_context.strip())
    if not parts:
        return None
    return " ".join(parts)


def _search_text(ai_description: str | None, user_notes: str | None) -> str | None:
    """Build denormalized search text per product rules."""
    text = (ai_description or "") + " " + (user_notes or "")
    text = text.strip()
    return text or None


def _apply_classification(row: Image, data: dict[str, Any] | None) -> None:
    """Fill AI columns on *row* from classifier output; no-op if *data* is empty."""
    if not data:
        return
    row.ai_description = data.get("description")
    row.garment_type = data.get("garment_type")
    row.style = data.get("style")
    row.material = data.get("material")
    row.color_palette = _color_palette_to_db(data.get("color_palette"))
    row.pattern = data.get("pattern")
    row.season = data.get("season")
    row.occasion = data.get("occasion")
    row.consumer_profile = data.get("consumer_profile")
    row.trend_notes = _merge_trend_and_location(
        data.get("trend_notes"),
        data.get("location_context"),
    )


@router.post("/upload")
def upload_image(
    file: UploadFile = File(..., description="Image file (jpg, jpeg, png, webp)"),
    uploaded_by: str = Form(default="anonymous"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Accept an image, classify it, save metadata, and return the stored row.

    Steps: validate type → write bytes under :attr:`app.config.settings.upload_dir`
    → run vision classification → insert :class:`~app.models.image.Image` with
    ``search_text = ai_description + \" \" + (user_notes or \"\")`` (``user_notes``
    is unset on upload, so typically just the description).
    """
    ext = _validate_upload(file.filename, file.content_type)
    raw_bytes = file.file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    original_name = Path(file.filename or "image").name[:512]
    stored_name = f"{uuid.uuid4().hex}{ext}"
    disk_path = settings.upload_dir / stored_name
    disk_path.write_bytes(raw_bytes)

    classification = classify_image(str(disk_path.resolve()))

    uploader = (uploaded_by or "").strip() or "anonymous"

    row = Image(
        filename=original_name,
        filepath=f"/static/{stored_name}",
        uploaded_by=uploader,
        user_notes=None,
        user_tags=None,
    )
    _apply_classification(row, classification)
    row.search_text = _search_text(row.ai_description, row.user_notes)

    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "data": ImageResponse.model_validate(row),
        "error": None,
    }
