"""Full-text and facet search over stored images."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.image import Image
from app.schemas.image import ImageResponse

router = APIRouter(prefix="/api", tags=["search"])


def _optional_str(value: str | None) -> str | None:
    """Normalize optional string query params (empty → ``None``)."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _like_pattern(term: str) -> str:
    """Build a SQL ``LIKE`` pattern with ``%`` wildcards; escape ``%``, ``_``, ``\\``."""
    cleaned = term.strip()
    escaped = (
        cleaned.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    return f"%{escaped}%"


@router.get("/images/search")
def search_images(
    q: str | None = Query(default=None, description="Substring match on search_text"),
    garment_type: str | None = Query(default=None),
    style: str | None = Query(default=None),
    material: str | None = Query(default=None),
    pattern: str | None = Query(default=None),
    season: str | None = Query(default=None),
    occasion: str | None = Query(default=None),
    consumer_profile: str | None = Query(default=None),
    location_country: str | None = Query(default=None),
    location_continent: str | None = Query(default=None),
    capture_year: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Filter images by optional full-text ``q`` and exact facet matches (AND)."""
    stmt = select(Image).order_by(Image.uploaded_at.desc())
    predicates: list[Any] = []

    text_q = _optional_str(q)
    if text_q is not None:
        predicates.append(
            Image.search_text.like(_like_pattern(text_q), escape="\\"),
        )

    if (gt := _optional_str(garment_type)) is not None:
        predicates.append(Image.garment_type == gt)
    if (st := _optional_str(style)) is not None:
        predicates.append(Image.style == st)
    if (mat := _optional_str(material)) is not None:
        predicates.append(Image.material == mat)
    if (pat := _optional_str(pattern)) is not None:
        predicates.append(Image.pattern == pat)
    if (sea := _optional_str(season)) is not None:
        predicates.append(Image.season == sea)
    if (occ := _optional_str(occasion)) is not None:
        predicates.append(Image.occasion == occ)
    if (cp := _optional_str(consumer_profile)) is not None:
        predicates.append(Image.consumer_profile == cp)
    if (lc := _optional_str(location_country)) is not None:
        predicates.append(Image.location_country == lc)
    if (lcon := _optional_str(location_continent)) is not None:
        predicates.append(Image.location_continent == lcon)
    if capture_year is not None:
        predicates.append(Image.capture_year == capture_year)

    if predicates:
        stmt = stmt.where(and_(*predicates))

    rows = list(db.execute(stmt).scalars().all())
    return {
        "data": [ImageResponse.model_validate(row) for row in rows],
        "error": None,
    }
