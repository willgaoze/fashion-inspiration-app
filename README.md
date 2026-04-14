# Fashion Inspiration App

## Overview

Design teams collect large libraries of garment photos; this app uploads those images, classifies them with a vision model, and exposes search and faceted filters so the library stays usable without manual tagging at scale. It is a **local-first proof of concept**: one process for the API, one for the React UI, and a single SQLite file for persistence.

## Setup

### Backend

- **Requirements:** Python 3.11+, Node.js 18+ (for the frontend).
- Copy environment template and set your API key:
  - `cp .env.example .env`
  - Set `ANTHROPIC_API_KEY` (and optionally `ANTHROPIC_MODEL`, `UPLOAD_DIR`).
- Install dependencies: `pip install -r requirements.txt`
- Run the API:
  - `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
- Interactive docs: `http://127.0.0.1:8000/docs`

### Frontend

- `cd frontend`
- `npm install`
- `npm run dev`
- Open **`http://localhost:5173`** (Vite proxies `/api` and `/static` to the backend).

## Architecture

1. **FastAPI + SQLite** — Chosen for a **lightweight, zero-ops** stack: no separate database server, easy onboarding, and enough structure for a POC. The trade-off is weaker concurrency and analytics than Postgres; for a single-user or small-team demo, that is acceptable.

2. **AI classification** — **Claude** (`claude-sonnet-4-20250514` by default) with a **vision** request; the prompt **forces a single JSON object** so downstream code can parse and map fields reliably. Failures return `None` and uploads can still persist with empty AI fields.

3. **Search** — **SQLite `LIKE`** on a denormalized **`search_text`** field (AI description + user notes). This is **simple and predictable** for a POC; it avoids FTS5 setup complexity at the cost of **sublinear scaling** and **no true ranking**.

4. **Dynamic filters** — Filter options come from **`SELECT DISTINCT`** on live columns (and parsed colors), **not hardcoded enums**, so the UI stays aligned with whatever the model and users actually store.

5. **`color_palette`** — Stored as a **JSON array string** per row for flexibility; the filters endpoint **parses and flattens** values before deduplicating. Search by color is handled partly in the UI (exact token match on parsed arrays) because the search API does not yet expose a dedicated color facet—an intentional simplification with a documented limitation.

## Model Evaluation

- **Test set:** 50 fashion images from **Pexels**.
- **Labeled attribute:** **`garment_type` only** (other attributes were not fully annotated due to time limits).
- **Result:** **85%** accuracy on `garment_type` (case-insensitive exact match after normalization).
- **What worked well:** **Single-garment, clear product-style photos**; the model often returns stable, usable type labels.
- **What struggled:** **Multi-garment or collage images** (e.g. responses like “mixed collection”), and **label granularity mismatch** between ground truth and model (e.g. “blazer” vs “suit jacket”) counted as errors under strict matching.
- **Improvements:** Adopt a **controlled taxonomy** (or synonym map), add more **single-item** test images, and consider **fuzzy / embedding-based** scoring instead of pure string equality for eval.

Run the bundled eval script (requires API key and images under `eval/test_images/`):

- `python eval/run_eval.py` (see `eval/run_eval.py --help` and `--init-template`).

## Testing

- `python -m pytest tests/unit/ -v`
- `python -m pytest tests/integration/ -v`
- `python -m pytest tests/e2e/ -v`

Tests use an **in-memory SQLite** database and **override `get_db`** so they do not touch your development DB.

## Known Limitations

- **Eval set size (50 images)** limits statistical confidence; numbers are directional, not production guarantees.
- **Search uses `LIKE`**, not SQLite FTS or an external search engine—**large corpora** will get slower and relevance remains basic.
- **Color filtering** relies on **straightforward JSON parsing**; malformed or inconsistent model output can skew facet lists.
- **No authentication** — uploads and annotations are open to whoever can reach the API; not suitable for public deployment without a gate.

## Next Steps

With more time, we would add **user accounts and API keys**, migrate search to **FTS5 or a dedicated index**, tighten **eval** with a shared label ontology and soft matching, add **pagination** and **image deduplication**, and **harden** the classifier path (rate limits, caching, and structured logging) for longer runs.
