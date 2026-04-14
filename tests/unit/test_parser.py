"""Unit tests for ``parse_ai_output``."""

from app.services.parser import parse_ai_output


def test_empty_and_invalid_returns_empty_dict() -> None:
    assert parse_ai_output("") == {}
    assert parse_ai_output("   ") == {}
    assert parse_ai_output("not json") == {}


def test_json_fenced_and_partial_keys() -> None:
    fenced = """```json
{"garment_type": "coat", "color_palette": ["black"]}
```"""
    r = parse_ai_output(fenced)
    assert r["garment_type"] == "coat"
    assert r["color_palette"] == ["black"]
    assert r["style"] is None

    r2 = parse_ai_output('{"description": "x"}')
    assert r2["description"] == "x"
    assert r2["occasion"] is None
