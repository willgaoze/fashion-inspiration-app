"""Unit tests for ``parse_ai_output``."""

from app.services.parser import parse_ai_output


def test_normal_json() -> None:
    raw = (
        '{"description": "A linen dress", "garment_type": "dress", '
        '"color_palette": ["white", "beige"]}'
    )
    r = parse_ai_output(raw)
    assert r["description"] == "A linen dress"
    assert r["garment_type"] == "dress"
    assert r["color_palette"] == ["white", "beige"]
    assert r["pattern"] is None


def test_json_with_markdown_fence() -> None:
    fenced = """```json
{"garment_type": "coat", "color_palette": ["black"]}
```"""
    r = parse_ai_output(fenced)
    assert r["garment_type"] == "coat"
    assert r["color_palette"] == ["black"]
    assert r["style"] is None


def test_missing_fields_filled_with_none() -> None:
    r = parse_ai_output('{"description": "only this"}')
    assert r["description"] == "only this"
    assert r["garment_type"] is None
    assert r["occasion"] is None
    assert r["color_palette"] is None
    assert all(r[k] is None for k in ("trend_notes", "location_context"))


def test_invalid_input_returns_empty_dict() -> None:
    assert parse_ai_output("not json at all") == {}
    assert parse_ai_output("[1, 2, 3]") == {}


def test_empty_string_returns_empty_dict() -> None:
    assert parse_ai_output("") == {}
    assert parse_ai_output("   ") == {}
