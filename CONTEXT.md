# Original Requirements

## Overview
Design teams collect thousands of inspiration photos from stores, markets, and streetwear.
This app turns that image library into a usable, searchable source of inspiration.

## What to Build

### 1. Image Upload + AI Classification
- Upload garment photos via web app
- Multimodal AI returns natural-language description + structured attributes:
  garment type, style, material, color palette, pattern, season, occasion,
  consumer profile, trend notes, location context
- Store both descriptive output and structured metadata

### 2. Search + Filtering
- Visual grid display
- Dynamic filters: garment type, style, material, color palette, pattern,
  occasion, consumer profile, trend notes
- Contextual filters: location (continent/country/city), time (year/month/season), designer
- Filters dynamically generated from data, NOT hardcoded
- Full-text search (e.g. "embroidered neckline", "artisan market")

### 3. Designer Annotations
- Users add tags, notes, observations
- Searchable, clearly distinguished from AI output

## Deliverables
- Runs locally with minimal setup
- Clear README with setup instructions and architectural choices
- Model Evaluation: 50-100 test images, per-attribute accuracy, analysis
- Tests: unit (parser), integration (filters), e2e (upload→classify→filter)
- Repo: /app /eval /tests README.md
- Commit in logical increments

## Evaluation Criteria
- Functionality: core workflow end to end
- Model quality: classifier performance + evaluation methodology
- Code quality: well-structured, readable, tested
- Product thinking: sensible trade-offs
- Communication: README honest about limitations

## Tech Stack
- Backend: FastAPI + SQLAlchemy + SQLite
- Frontend: React + Vite
- AI: Anthropic Claude claude-sonnet-4-20250514 Vision API
- Search: SQLite FTS5 (LIKE matching on search_text field)
- Testing: pytest + playwright

## Directory Structure
fashion-inspiration-app/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/image.py
│   ├── schemas/image.py
│   ├── api/upload.py
│   ├── api/search.py
│   ├── api/filters.py
│   ├── api/annotations.py
│   ├── services/ai_classifier.py
│   ├── services/parser.py
│   └── static/
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── ImageGrid.jsx
│           ├── FilterPanel.jsx
│           ├── SearchBar.jsx
│           ├── UploadModal.jsx
│           └── AnnotationPanel.jsx
├── eval/
│   ├── test_images/
│   ├── ground_truth.json
│   └── run_eval.py
├── tests/
│   ├── unit/test_parser.py
│   ├── integration/test_filters.py
│   └── e2e/test_workflow.py
├── .env.example
├── requirements.txt
└── README.md

## Data Model (Image table)
- id, filename, filepath, uploaded_at, uploaded_by
- AI: ai_description, garment_type, style, material, color_palette,
  pattern, season, occasion, consumer_profile, trend_notes
- Location: location_city, location_country, location_continent
- Time: capture_year, capture_month
- User: user_tags, user_notes
- Search: search_text (ai_description + user_notes merged)

## Code Rules
- Python: type hints + docstring on every function
- AI calls: always try/except, return None on failure
- No hardcoded values, use config.py
- API response format: {"data": ..., "error": null}
- Frontend: functional components + hooks only

## Progress
- [ ] Module 1: Project skeleton
- [ ] Module 2: Database + models
- [ ] Module 3: AI classifier service
- [ ] Module 4: Upload API
- [ ] Module 5: Search + Filter API
- [ ] Module 6: Annotation API
- [ ] Module 7: Frontend UI
- [ ] Module 8: Tests
- [ ] Module 9: Eval script
- [ ] Module 10: README