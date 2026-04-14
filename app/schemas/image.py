"""Pydantic schemas for image upload, API responses, and annotation updates."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImageCreate(BaseModel):
    """Payload used when registering a new upload (path and file identity on disk)."""

    filename: str = Field(..., min_length=1, max_length=512)
    filepath: str = Field(..., min_length=1)
    uploaded_by: str | None = Field(default=None, max_length=255)
    location_city: str | None = Field(default=None, max_length=255)
    location_country: str | None = Field(default=None, max_length=255)
    location_continent: str | None = Field(default=None, max_length=128)
    capture_year: int | None = Field(default=None, ge=1)
    capture_month: int | None = Field(default=None, ge=1, le=12)


class ImageResponse(BaseModel):
    """Full image record as returned to the client (matches ORM columns)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    filepath: str
    uploaded_at: datetime
    uploaded_by: str | None

    ai_description: str | None
    garment_type: str | None
    style: str | None
    material: str | None
    color_palette: str | None = Field(
        default=None,
        description="JSON array string, e.g. [\"navy\",\"cream\"]",
    )
    pattern: str | None
    season: str | None
    occasion: str | None
    consumer_profile: str | None
    trend_notes: str | None

    location_city: str | None
    location_country: str | None
    location_continent: str | None

    capture_year: int | None
    capture_month: int | None

    user_tags: str | None = Field(
        default=None,
        description="JSON array string of user tags",
    )
    user_notes: str | None

    search_text: str | None


class AnnotationUpdate(BaseModel):
    """Partial update for designer annotations only."""

    user_tags: str | None = Field(
        default=None,
        description="JSON array string; omit to leave unchanged",
    )
    user_notes: str | None = Field(
        default=None,
        description="Free-form notes; omit to leave unchanged",
    )
