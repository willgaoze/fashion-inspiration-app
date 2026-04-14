"""Dynamic filter options derived from stored image metadata (no hardcoded values)."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.image import Image

router = APIRouter(prefix="/api", tags=["filters"])


def _distinct_non_null_strings(db: Session, column: Any) -> list[str]:
    """Return sorted distinct non-empty string values for *column*."""
    stmt = select(column).where(column.isnot(None)).distinct()
    raw = [row[0] for row in db.execute(stmt).all()]
    out: set[str] = set()
    for value in raw:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            out.add(text)
    return sorted(out)


def _distinct_non_null_ints(db: Session, column: Any) -> list[int]:
    """Return sorted distinct integer values for *column*."""
    stmt = select(column).where(column.isnot(None)).distinct()
    raw = [row[0] for row in db.execute(stmt).all()]
    return sorted({v for v in raw if v is not None})


def _distinct_color_tokens(db: Session) -> list[str]:
    """Parse ``color_palette`` JSON arrays and return sorted distinct color strings."""
    stmt = select(Image.color_palette).where(Image.color_palette.isnot(None))
    tokens: set[str] = set()
    for (raw,) in db.execute(stmt).all():
        if raw is None or not str(raw).strip():
            continue
        try:
            parsed = json.loads(str(raw))
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, list):
            continue
        for item in parsed:
            text = str(item).strip()
            if text:
                tokens.add(text)
    return sorted(tokens)


@router.get("/filters")
def list_filters(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return distinct attribute values currently present in the database.

    Values come entirely from persisted rows (no hardcoded option lists).
    ``color_palette`` is stored as a JSON array string per row; individual
    color strings are flattened and de-duplicated into ``data["color_palette"]``.
    """
    data: dict[str, Any] = {
        "garment_type": _distinct_non_null_strings(db, Image.garment_type),
        "style": _distinct_non_null_strings(db, Image.style),
        "material": _distinct_non_null_strings(db, Image.material),
        "pattern": _distinct_non_null_strings(db, Image.pattern),
        "season": _distinct_non_null_strings(db, Image.season),
        "occasion": _distinct_non_null_strings(db, Image.occasion),
        "consumer_profile": _distinct_non_null_strings(db, Image.consumer_profile),
        "location_country": _distinct_non_null_strings(db, Image.location_country),
        "location_continent": _distinct_non_null_strings(db, Image.location_continent),
        "capture_year": _distinct_non_null_ints(db, Image.capture_year),
        "color_palette": _distinct_color_tokens(db),
    }
    return {"data": data, "error": None}
