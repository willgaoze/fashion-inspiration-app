"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.upload import router as upload_router
from app.config import settings
from app.database import init_db

app = FastAPI(title="Fashion Inspiration API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.mount(
    "/static",
    StaticFiles(directory=str(settings.upload_dir.resolve())),
    name="static",
)


@app.on_event("startup")
def on_startup() -> None:
    """Ensure database schema and upload directory exist."""
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    init_db()


@app.get("/")
def root() -> dict[str, str]:
    """Health-style root endpoint."""
    return {"status": "ok"}
