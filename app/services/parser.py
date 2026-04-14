"""Parse model-generated JSON for garment classification fields.

The vision model is instructed to emit JSON, but responses may include Markdown
fences, partial objects, or malformed text. This module normalizes that output
into a predictable shape for persistence and search.
"""

from __future__ import annotations

import json
import re
from typing import Any, Final

_JSON_FENCE_RE: Final[re.Pattern[str]] = re.compile(
    r"```(?:json)?\s*\n?(.*?)```",
    re.DOTALL | re.IGNORECASE,
)

# Keys the classifier prompt asks the model to return (canonical output shape).
_EXPECTED_KEYS: Final[tuple[str, ...]] = (
    "description",
    "garment_type",
    "style",
    "material",
    "color_palette",
    "pattern",
    "season",
    "occasion",
    "consumer_profile",
    "trend_notes",
    "location_context",
)


def _strip_markdown_fences(text: str) -> str:
    """Remove a leading/trailing Markdown code fence if present."""
    stripped = text.strip()
    match = _JSON_FENCE_RE.search(stripped)
    if match:
        return match.group(1).strip()
    return stripped


def _decode_json_object(text: str) -> dict[str, Any] | None:
    """Decode *text* into a JSON object, or ``None`` if decoding fails or value is not an object."""
    candidate = text.strip()
    if not candidate:
        return None
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        fragment = candidate[start : end + 1]
        try:
            value = json.loads(fragment)
        except json.JSONDecodeError:
            return None
    if not isinstance(value, dict):
        return None
    return value


def _normalize_color_palette(value: Any) -> list[str] | None:
    """Coerce *value* into a list of non-empty strings, or ``None`` if not representable."""
    if value is None:
        return None
    if isinstance(value, list):
        out = [str(item).strip() for item in value if str(item).strip() != ""]
        return out or None
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return _normalize_color_palette(parsed)
    return None


def _normalize_record(data: dict[str, Any]) -> dict[str, Any]:
    """Build a full record with all expected keys; unknown keys are dropped."""
    out: dict[str, Any] = {key: None for key in _EXPECTED_KEYS}
    for key in _EXPECTED_KEYS:
        if key not in data:
            continue
        raw = data[key]
        if key == "color_palette":
            out[key] = _normalize_color_palette(raw)
        else:
            if raw is None:
                out[key] = None
            elif isinstance(raw, str):
                out[key] = raw.strip() or None
            elif isinstance(raw, (int, float, bool)):
                out[key] = str(raw).strip() or None
            else:
                out[key] = str(raw).strip() or None
    return out


def parse_ai_output(raw: str) -> dict[str, Any]:
    """Parse classifier model text into a normalized classification dictionary.

    The model is asked to return JSON with keys matching garment metadata. In
    practice the raw string may be plain JSON, JSON wrapped in Markdown ``json``
    code fences, or unusable text. This function applies a small pipeline:

    1. Strip optional `` ```json ... ``` `` (or generic `` ``` ... ``` ``) fences.
    2. Parse JSON. If that fails, attempt to locate the outermost ``{...}`` substring
       and parse again (handles short lead-in text before the object).
    3. If no JSON object can be parsed, return ``{}`` (total failure).
    4. If parsing succeeds, return a new dict containing **only** the canonical keys
       :data:`_EXPECTED_KEYS`. Any missing key is set to ``None``. The
       ``color_palette`` field is normalized to ``list[str] | None``.

    Args:
        raw: Raw assistant text (ideally JSON, possibly fenced or prefixed).

    Returns:
        A mapping with all expected keys when JSON decoding succeeds; each value
        is either a normalized scalar/list or ``None`` for missing or empty fields.
        Returns ``{}`` when *raw* is empty/whitespace, decoding fails, or the decoded
        value is not a JSON object.

    Examples:
        * ``'{"garment_type": "dress"}'`` → missing keys become ``None``.
        * ``'```json\\n{"pattern": "stripes"}\\n```'`` → fence stripped first.
        * ``'not json'`` → ``{}``.
    """
    if raw is None:
        return {}
    text = str(raw).strip()
    if not text:
        return {}

    unfenced = _strip_markdown_fences(text)
    parsed = _decode_json_object(unfenced)
    if parsed is None:
        parsed = _decode_json_object(text)
    if parsed is None:
        return {}

    return _normalize_record(parsed)
