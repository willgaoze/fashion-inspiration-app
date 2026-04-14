# Fashion Inspiration App

## Requirements Coverage

| Requirement | Implementation | Status |
|-------------|---------------|--------|
| AI-Driven Development | Claude `claude-sonnet-4-20250514` Vision API for garment classification | ✅ |
| LLM Integration Patterns | Structured JSON output via prompt engineering, robust parser with edge case handling | ✅ |
| Scalable API Design | FastAPI microservices, modular router architecture | ✅ |
| RAG/Knowledge Retrieval | Full-text search across AI-generated descriptions + user annotations | ✅ |
| Production-grade Backend | Type hints, docstrings, error handling, try/except on all AI calls | ✅ |
| Testability | Unit + Integration + E2E tests, in-memory DB for isolation | ✅ |
| Observability | Structured error responses, AI failure graceful degradation | ✅ |
| Agentic Workflow | Upload → AI classify → structured storage → search pipeline | ✅ |

## Overview

Design teams collect large libraries of garment photos; this app uploads those images, classifies them with a vision model, and exposes search and faceted filters so the library stays usable without manual tagging at scale. It is a **local-first proof of concept**: one process for the API, one for the React UI, and a single SQLite file for persistence.

## Results Showcase

These snapshots are included as execution evidence of end-to-end product outcomes (not just UI styling):

- **Operationalized inspiration library**: designers can ingest raw field photos and immediately retrieve them through metadata-driven filtering without manual pre-labeling.

![Outcome: searchable inspiration library](docs/screenshots/library-overview.png)

- **Explainable AI output at record level**: each asset includes natural-language rationale and structured attributes that can be audited, searched, and enriched with designer annotations.

![Outcome: structured AI classification record](docs/screenshots/ai-structured-output.png)

## System Architecture

The end-to-end workflow is:

Upload Image → Validate file type → Save to disk → Call Claude Vision API → Parse structured JSON output → Store in SQLite → Update `search_text` index → Return `ImageResponse` to frontend

## Technical Highlights

- **Prompt Engineering**: The classifier prompt enforces a single structured JSON object so the AI output stays machine-parseable and stable for downstream mapping.
- **Robust Parser**: Parsing logic handles markdown code fences, missing fields, and invalid model output safely, returning normalized data or graceful fallback.
- **Dynamic Filter Generation**: Filter values are generated from live `SELECT DISTINCT` queries against persisted data, with no hardcoded enums.
- **Graceful Degradation**: If AI classification fails, uploads still persist with empty AI fields so user workflows are not blocked.
- **Search Architecture**: A denormalized `search_text` field merges AI descriptions and designer notes to support natural-language search.
- **color_palette handling**: `color_palette` is stored as a JSON array string, parsed and flattened for distinct facet options and color filtering.

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
