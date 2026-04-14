"""Application configuration loaded from environment variables via python-dotenv."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Load ``.env`` from the project root (not ``.env.example``); works regardless of CWD.
load_dotenv(BASE_DIR / ".env")


def _resolve_upload_dir(raw: str) -> Path:
    """Resolve UPLOAD_DIR relative to the project root when not absolute."""
    path = Path(raw)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


class Settings:
    """Runtime settings derived from the environment."""

    def __init__(self) -> None:
        self.anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
        self.anthropic_model: str = os.getenv(
            "ANTHROPIC_MODEL",
            "claude-sonnet-4-20250514",
        )
        self.upload_dir: Path = _resolve_upload_dir(
            os.getenv("UPLOAD_DIR", "app/static"),
        )
        db_path = (BASE_DIR / "fashion_inspiration.db").resolve()
        default_sqlite = f"sqlite:///{db_path.as_posix()}"
        self.database_url: str = os.getenv("DATABASE_URL", default_sqlite)


settings = Settings()
