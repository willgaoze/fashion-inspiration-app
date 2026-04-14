"""Integration tests for ``GET /api/filters``."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from app.models.image import Image


def _assert_lists_have_no_none(payload: dict) -> None:
    for _key, values in payload.items():
        assert isinstance(values, list)
        for item in values:
            assert item is not None


def test_filters_reflects_inserted_rows(client, engine) -> None:
    SessionLocal = sessionmaker(bind=engine)
    db: Session = SessionLocal()
    try:
        db.add_all(
            [
                Image(
                    filename="a.jpg",
                    filepath="/static/a.jpg",
                    garment_type="jacket",
                    style="streetwear",
                    material="nylon",
                    color_palette='["black", "grey"]',
                    pattern="solid",
                    season="winter",
                    occasion="outdoor",
                    consumer_profile="unisex",
                    location_country="Japan",
                    location_continent="Asia",
                    capture_year=2024,
                    search_text="test a",
                ),
                Image(
                    filename="b.jpg",
                    filepath="/static/b.jpg",
                    garment_type="dress",
                    style="minimal",
                    material="silk",
                    color_palette='["ivory"]',
                    pattern="plain",
                    season="spring",
                    occasion="evening",
                    consumer_profile="women",
                    location_country="France",
                    location_continent="Europe",
                    capture_year=2023,
                    search_text="test b",
                ),
            ],
        )
        db.commit()
    finally:
        db.close()

    response = client.get("/api/filters")
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    data = body["data"]
    _assert_lists_have_no_none(data)

    assert "jacket" in data["garment_type"]
    assert "dress" in data["garment_type"]
    assert "streetwear" in data["style"]
    assert "nylon" in data["material"]
    assert "black" in data["color_palette"]
    assert "grey" in data["color_palette"]
    assert "ivory" in data["color_palette"]
    assert "Japan" in data["location_country"]
    assert "France" in data["location_country"]
    assert "Asia" in data["location_continent"]
    assert "Europe" in data["location_continent"]
    assert 2024 in data["capture_year"]
    assert 2023 in data["capture_year"]
