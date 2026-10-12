"""Sample 50 reproducible GSM8K errors for Day 20 manual review."""

from __future__ import annotations

import csv
import json
import random
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/day06_qwen15_gsm8k_s5_n200/Qwen__Qwen2.5-1.5B"
OUTPUT = ROOT / "reports/day20_gsm8k_error_sample.csv"
SEED = 20261010
SAMPLE_SIZE = 50


def final_answer(solution: str) -> str:
    matches = re.findall(r"####\s*([^\n]+)", solution)
    if not matches:
        raise ValueError("GSM8K gold solution has no final answer marker")
    return matches[-1].strip()


def main() -> None:
    files = list(RUN.glob("samples_gsm8k_*.jsonl"))
    if len(files) != 1:
        raise ValueError(f"Expected one GSM8K sample log, found {len(files)}")
    with files[0].open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle]
    strict_rows = [row for row in rows if row["filter"] == "strict-match"]
    if len(strict_rows) != 200 or len({row["doc_id"] for row in strict_rows}) != 200:
        raise ValueError("Expected 200 unique strict-match questions")
    errors = sorted(
        (row for row in strict_rows if float(row["exact_match"]) == 0),
        key=lambda row: row["doc_id"],
    )
    if len(errors) != 76:
        raise ValueError(f"Expected 76 strict-match errors, found {len(errors)}")
    selected = sorted(random.Random(SEED).sample(errors, SAMPLE_SIZE), key=lambda row: row["doc_id"])
    OUTPUT.parent.mkdir(exist_ok=True)
    if OUTPUT.exists():
        with OUTPUT.open(encoding="utf-8-sig", newline="") as handle:
            existing = list(csv.DictReader(handle))
        expected_ids = [str(row["doc_id"]) for row in selected]
        if [row["doc_id"] for row in existing] != expected_ids:
            raise ValueError(f"Existing review sheet differs from the fixed sample: {OUTPUT}")
        print(f"Candidate strict-match errors: {len(errors)}/200")
        print(f"Existing {len(existing)}-row review sheet preserved: {OUTPUT}")
        return
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "doc_id",
                "question",
                "gold_final_answer",
                "model_extracted_answer",
                "model_full_response",
                "reference_solution",
                "error_category_fill_in",
                "evidence_note_fill_in",
            ],
        )
        writer.writeheader()
        for row in selected:
            writer.writerow(
                {
                    "doc_id": row["doc_id"],
                    "question": row["doc"]["question"],
                    "gold_final_answer": final_answer(row["doc"]["answer"]),
                    "model_extracted_answer": row["filtered_resps"][0],
                    "model_full_response": row["resps"][0][0],
                    "reference_solution": row["doc"]["answer"],
                    "error_category_fill_in": "",
                    "evidence_note_fill_in": "",
                }
            )
    print(f"Candidate strict-match errors: {len(errors)}/200")
    print(f"Selected: {len(selected)} with seed={SEED}")
    print(f"Review sheet: {OUTPUT}")


if __name__ == "__main__":
    main()
