#!/usr/bin/env python3
"""Evaluate vision classifier against ``ground_truth.json`` (local test images).

Run from anywhere::

    python eval/run_eval.py

Regenerate ``ground_truth.json`` stubs from filenames in ``eval/test_images/``::

    python eval/run_eval.py --init-template
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Load project .env before importing app services
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from app.services.ai_classifier import classify_image # noqa: E402

MAX_CLASSIFY_RETRIES = 3
RETRY_DELAY_SEC = 5.0
CLASSIFY_TIMEOUT_SEC = 180.0

COMPARE_ATTRS = ("garment_type", "style", "material", "occasion")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

TEMPLATE_ROW = {
    "filename": "",
    "garment_type": "",
    "style": "",
    "material": "",
    "occasion": "",
    "location_country": "",
}


def _norm(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _is_blank(value: object) -> bool:
    if value is None:
        return True
    return str(value).strip() == ""


def classify_with_retries(image_path: str) -> dict | None:
    """Call ``classify_image`` with per-attempt timeout and up to ``MAX_CLASSIFY_RETRIES`` retries."""
    attempts = 1 + MAX_CLASSIFY_RETRIES
    for attempt in range(attempts):
        if attempt > 0:
            time.sleep(RETRY_DELAY_SEC)
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(classify_image, image_path)
                result = future.result(timeout=CLASSIFY_TIMEOUT_SEC)
        except FuturesTimeoutError:
            result = None
            print(
                f"  attempt {attempt + 1}/{attempts}: timeout after {CLASSIFY_TIMEOUT_SEC:.0f}s",
                file=sys.stderr,
                flush=True,
            )
        except Exception as exc:
            result = None
            print(
                f"  attempt {attempt + 1}/{attempts}: {type(exc).__name__}: {exc}",
                file=sys.stderr,
                flush=True,
            )
        if result is not None:
            return result
    return None


def write_ground_truth_template() -> None:
    """Create ``ground_truth.json`` with one empty row per image in ``test_images``."""
    img_dir = EVAL_DIR / "test_images"
    img_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    for path in sorted(img_dir.iterdir()):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        row = {**TEMPLATE_ROW, "filename": path.name}
        rows.append(row)
    out_path = EVAL_DIR / "ground_truth.json"
    out_path.write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(rows)} record(s) to {out_path}")


def run_evaluation() -> None:
    gt_path = EVAL_DIR / "ground_truth.json"
    if not gt_path.is_file():
        print(f"Missing {gt_path}", file=sys.stderr)
        sys.exit(1)

    rows = json.loads(gt_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        print("ground_truth.json must be a JSON array", file=sys.stderr)
        sys.exit(1)

    counts = {a: {"correct": 0, "total": 0} for a in COMPARE_ATTRS}
    items: list[dict] = []

    eligible: list[dict] = []
    for row in rows:
        filename = row.get("filename")
        if not filename or not isinstance(filename, str):
            continue
        img_path = EVAL_DIR / "test_images" / filename
        if not img_path.is_file():
            print(f"skip (file missing): {filename}", file=sys.stderr)
            continue
        eligible.append(row)

    total = len(eligible)
    for index, row in enumerate(eligible, start=1):
        filename = row["filename"]
        img_path = EVAL_DIR / "test_images" / filename

        prediction = classify_with_retries(str(img_path.resolve()))

        print(f"Processing {index}/{total}: {filename}", flush=True)

        if prediction is None:
            print(
                f"  skipped: no prediction after {1 + MAX_CLASSIFY_RETRIES} attempt(s)",
                file=sys.stderr,
                flush=True,
            )
            items.append(
                {
                    "filename": filename,
                    "prediction": None,
                    "skipped": True,
                    "reason": "classification_failed_or_timeout",
                    "per_attribute": {
                        a: "skipped_classification_failed" for a in COMPARE_ATTRS
                    },
                },
            )
            continue

        entry: dict = {
            "filename": filename,
            "prediction": prediction,
            "skipped": False,
            "per_attribute": {},
        }

        for attr in COMPARE_ATTRS:
            gt_val = row.get(attr, "")
            if _is_blank(gt_val):
                entry["per_attribute"][attr] = "skipped_no_label"
                continue

            counts[attr]["total"] += 1
            pred_val = prediction.get(attr) if prediction else None
            ok = _norm(gt_val) == _norm(pred_val)
            entry["per_attribute"][attr] = "correct" if ok else "wrong"
            if ok:
                counts[attr]["correct"] += 1

        items.append(entry)

    percents: dict[str, int | None] = {}
    for attr in COMPARE_ATTRS:
        t = counts[attr]["total"]
        if t == 0:
            percents[attr] = None
        else:
            percents[attr] = int(round(100 * counts[attr]["correct"] / t))

    valid = [p for p in percents.values() if p is not None]
    overall = int(round(sum(valid) / len(valid))) if valid else 0

    lines_out: list[str] = []
    for attr in COMPARE_ATTRS:
        p = percents[attr]
        if p is None:
            line = f"{attr}: n/a"
        else:
            line = f"{attr}: {p}%"
        print(line)
        lines_out.append(line)
    overall_line = f"overall: {overall}%"
    print(overall_line)
    lines_out.append(overall_line)

    results_path = EVAL_DIR / "results.json"
    results_path.write_text(
        json.dumps(
            {
                "summary_lines": lines_out,
                "metrics_percent": percents,
                "overall_percent": overall,
                "counts": counts,
                "items": items,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {results_path}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fashion classifier evaluation")
    parser.add_argument(
        "--init-template",
        action="store_true",
        help="Rewrite ground_truth.json from eval/test_images/ filenames (empty fields).",
    )
    args = parser.parse_args()
    if args.init_template:
        write_ground_truth_template()
    else:
        run_evaluation()


if __name__ == "__main__":
    main()
