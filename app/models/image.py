"""Image ORM model: stored garment inspiration metadata and search text."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utc_now() -> datetime:
    """Return the current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class Image(Base):
    """A single uploaded inspiration image and its AI / user / filter metadata."""

    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    filepath: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
    )
    uploaded_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    ai_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    garment_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    style: Mapped[str | None] = mapped_column(String(255), nullable=True)
    material: Mapped[str | None] = mapped_column(String(255), nullable=True)
    color_palette: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of color strings",
    )
    pattern: Mapped[str | None] = mapped_column(String(255), nullable=True)
    season: Mapped[str | None] = mapped_column(String(64), nullable=True)
    occasion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    consumer_profile: Mapped[str | None] = mapped_column(Text, nullable=True)
    trend_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    location_city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_country: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_continent: Mapped[str | None] = mapped_column(String(128), nullable=True)

    capture_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capture_month: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user_tags: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of user tag strings",
    )
    user_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    search_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Denormalized: ai_description and user_notes merged for search",
    )
