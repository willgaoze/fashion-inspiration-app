"""End-to-end upload → persist → search workflow (AI mocked)."""

from __future__ import annotations

from io import BytesIO
from unittest.mock import patch

from PIL import Image as PilImage
from sqlalchemy.orm import sessionmaker

from app.models.image import Image


def _tiny_jpeg_bytes() -> bytes:
    buf = BytesIO()
    PilImage.new("RGB", (1, 1), color=(120, 80, 60)).save(buf, format="JPEG")
    return buf.getvalue()


@patch("app.api.upload.classify_image")
def test_upload_persists_and_search_finds_image(mock_classify, client, engine, tmp_path, monkeypatch):
    mock_classify.return_value = {
        "description": "Tiny test garment",
        "garment_type": "test-jacket",
        "style": "e2e-style",
        "material": "cotton",
        "color_palette": ["rust"],
        "pattern": "solid",
        "season": "fall",
        "occasion": "casual",
        "consumer_profile": "tester",
        "trend_notes": "mock trend",
        "location_context": "mock studio",
    }

    from app.config import settings

    monkeypatch.setattr(settings, "upload_dir", tmp_path)

    jpeg = _tiny_jpeg_bytes()
    files = {"file": ("pixel.jpg", jpeg, "image/jpeg")}
    data = {"uploaded_by": "e2e-user"}
    response = client.post("/api/upload", files=files, data=data)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["error"] is None
    row = payload["data"]
    image_id = row["id"]
    assert row["garment_type"] == "test-jacket"
    assert row["uploaded_by"] == "e2e-user"

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        stored = db.get(Image, image_id)
        assert stored is not None
        assert stored.filename == "pixel.jpg"
        assert stored.garment_type == "test-jacket"
        assert stored.search_text is not None
        assert "Tiny test garment" in stored.search_text
    finally:
        db.close()

    search = client.get(
        "/api/images/search",
        params={"garment_type": "test-jacket", "style": "e2e-style"},
    )
    assert search.status_code == 200
    sbody = search.json()
    assert sbody["error"] is None
    ids = {item["id"] for item in sbody["data"]}
    assert image_id in ids
