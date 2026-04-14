"""Designer annotations (tags and notes) on stored images."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.image import Image
from app.schemas.image import AnnotationUpdate, ImageResponse

router = APIRouter(prefix="/api", tags=["annotations"])


def _search_text(ai_description: str | None, user_notes: str | None) -> str | None:
    """Build denormalized search text (matches upload pipeline)."""
    text = (ai_description or "") + " " + (user_notes or "")
    text = text.strip()
    return text or None


@router.patch("/images/{image_id}/annotations")
def patch_image_annotations(
    image_id: int,
    body: AnnotationUpdate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Update ``user_tags`` and/or ``user_notes`` and refresh ``search_text``."""
    row = db.get(Image, image_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Image not found")

    updates = body.model_dump(exclude_unset=True)
    if "user_tags" in updates:
        row.user_tags = updates["user_tags"]
    if "user_notes" in updates:
        row.user_notes = updates["user_notes"]

    row.search_text = _search_text(row.ai_description, row.user_notes)

    db.add(row)
    db.commit()
    db.refresh(row)

    return {"data": ImageResponse.model_validate(row), "error": None}
