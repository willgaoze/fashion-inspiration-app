"""Call Anthropic vision to classify a garment image and normalize JSON output."""

from __future__ import annotations

import base64
import traceback
from io import BytesIO
from pathlib import Path

from anthropic import Anthropic
from PIL import Image

from app.config import settings
from app.services.parser import parse_ai_output

_MAX_TOKENS = 4096
# Anthropic base64 image payloads must not exceed this decoded byte size.
_MAX_IMAGE_BYTES = 5 * 1024 * 1024

_CLASSIFIER_PROMPT = """You are a fashion design research assistant. Look at the garment image and describe it for an inspiration archive.

Respond with a single JSON object only (no Markdown, no commentary). Use this exact set of keys. Use null for unknown values. color_palette must be an array of short color name strings.

Required JSON shape:
{
  "description": string,
  "garment_type": string,
  "style": string,
  "material": string,
  "color_palette": string[],
  "pattern": string,
  "season": string,
  "occasion": string,
  "consumer_profile": string,
  "trend_notes": string,
  "location_context": string
}

description should be a concise natural-language overview. location_context should summarize visible or inferable place context (e.g. street market, boutique) if any, else null."""


def _media_type_for_path(path: Path) -> str:
    """Return an IANA media type for *path* based on its suffix."""
    suffix = path.suffix.lower()
    mapping = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return mapping.get(suffix, "image/jpeg")


def _encode_jpeg_under_limit(img: Image.Image) -> tuple[str, str]:
    """Re-encode *img* as JPEG, shrinking until under :data:`_MAX_IMAGE_BYTES`."""
    rgb = img
    if rgb.mode in ("RGBA", "LA"):
        background = Image.new("RGB", rgb.size, (255, 255, 255))
        alpha = rgb.split()[-1] if rgb.mode == "RGBA" else None
        background.paste(rgb, mask=alpha)
        rgb = background
    elif rgb.mode != "RGB":
        rgb = rgb.convert("RGB")

    max_side = 2048
    quality = 88
    working = rgb
    for _ in range(16):
        w, h = working.size
        if max(w, h) > max_side:
            scale = max_side / float(max(w, h))
            working = working.resize(
                (max(1, int(w * scale)), max(1, int(h * scale))),
                Image.Resampling.LANCZOS,
            )
        buf = BytesIO()
        working.save(buf, format="JPEG", quality=quality, optimize=True)
        data = buf.getvalue()
        if len(data) <= _MAX_IMAGE_BYTES:
            return (
                base64.standard_b64encode(data).decode("ascii"),
                "image/jpeg",
            )
        max_side = max(512, int(max_side * 0.82))
        quality = max(50, quality - 7)

    buf = BytesIO()
    tiny = working.resize((512, 512), Image.Resampling.LANCZOS)
    tiny.save(buf, format="JPEG", quality=50, optimize=True)
    data = buf.getvalue()
    return base64.standard_b64encode(data).decode("ascii"), "image/jpeg"


def _read_image_base64(image_path: str) -> tuple[str, str]:
    """Read *image_path* and return ``(base64_data, media_type)`` within API size limits."""
    path = Path(image_path)
    data = path.read_bytes()
    media_type = _media_type_for_path(path)
    if len(data) <= _MAX_IMAGE_BYTES:
        return base64.standard_b64encode(data).decode("ascii"), media_type

    with Image.open(BytesIO(data)) as img:
        img.load()
        return _encode_jpeg_under_limit(img)


def _extract_message_text(response: object) -> str:
    """Concatenate all text blocks from an Anthropic ``messages.create`` response."""
    parts: list[str] = []
    content = getattr(response, "content", None) or []
    for block in content:
        if getattr(block, "type", None) == "text":
            parts.append(getattr(block, "text", "") or "")
    return "".join(parts).strip()


def classify_image(image_path: str) -> dict | None:
    """Classify a garment image with Claude vision and return parsed metadata.

    Reads the file at *image_path*, encodes it as base64, and sends it to
    the configured Anthropic vision model (default ``claude-sonnet-4-20250514``)
    together with a prompt that requires
    a single JSON object. The raw assistant text is passed through
    :func:`app.services.parser.parse_ai_output`.

    Args:
        image_path: Filesystem path to an image (JPEG/PNG/WebP/GIF supported).

    Returns:
        A dict with canonical keys (see :mod:`app.services.parser`) and normalized
        values, or ``None`` if the API key is missing, the file cannot be read,
        the API call fails, or parsing yields no usable object.

    Note:
        Network and authentication errors are swallowed; callers should treat
        ``None`` as a failed classification.
    """
    try:
        if not settings.anthropic_api_key:
            return None
        b64, media_type = _read_image_base64(image_path)
        client = Anthropic(api_key=settings.anthropic_api_key)
        message = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=_MAX_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": _CLASSIFIER_PROMPT},
                    ],
                },
            ],
        )
        raw_text = _extract_message_text(message)
        if not raw_text:
            return None
        parsed = parse_ai_output(raw_text)
        if not parsed:
            return None
        return parsed
    except Exception as e:
        # DEBUG: remove after fixing classify_image failures
        print("[classify_image]", e)
        traceback.print_exc()
        return None
