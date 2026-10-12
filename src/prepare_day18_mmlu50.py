"""Freeze a reproducible 50-question MMLU sample for the Day 18 API experiment."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path

from datasets import load_dataset


DATASET = "cais/mmlu"
CONFIG = "all"
SPLIT = "test"
REVISION = "c30699e8356da336a370243923dbaf21066bb9fe"
SEED = 20261009
COUNT = 50
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "day18_mmlu_flash50.jsonl"
MANIFEST = ROOT / "data" / "day18_mmlu_flash50.manifest.json"


def make_prompt(row: dict) -> str:
    choices = row["choices"]
    if len(choices) != 4:
        raise ValueError("MMLU sample does not have four choices")
    lines = [
        "Answer the multiple-choice question. Reply with only one uppercase letter: A, B, C, or D. Do not explain.",
        "",
        f"Question: {row['question'].strip()}",
    ]
    lines.extend(f"{letter}. {choice.strip()}" for letter, choice in zip("ABCD", choices))
    lines.append("Answer:")
    return "\n".join(lines)


def main() -> None:
    dataset = load_dataset(DATASET, CONFIG, split=SPLIT, revision=REVISION)
    selected_indices = random.Random(SEED).sample(range(len(dataset)), COUNT)
    samples = []
    seen_questions = set()
    for sample_id, dataset_index in enumerate(selected_indices, 1):
        row = dataset[dataset_index]
        if not isinstance(row["answer"], int) or not 0 <= row["answer"] < 4:
            raise ValueError(f"Invalid answer at dataset index {dataset_index}")
        if row["question"] in seen_questions:
            raise ValueError(f"Duplicate sampled question at dataset index {dataset_index}")
        seen_questions.add(row["question"])
        samples.append(
            {
                "id": sample_id,
                "dataset_index": dataset_index,
                "subject": row["subject"],
                "question": make_prompt(row),
                "gold": "ABCD"[row["answer"]],
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(sample, ensure_ascii=False) + "\n" for sample in samples)
    OUT.write_text(content, encoding="utf-8", newline="\n")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    manifest = {
        "dataset": DATASET,
        "config": CONFIG,
        "split": SPLIT,
        "revision": REVISION,
        "dataset_rows": len(dataset),
        "sampling": "simple random sample without replacement",
        "seed": SEED,
        "count": COUNT,
        "prompt_version": "mmlu_0shot_letter_v1",
        "selected_indices": selected_indices,
        "input_sha256": digest,
        "subject_counts": dict(sorted(Counter(sample["subject"] for sample in samples).items())),
        "gold_counts": dict(sorted(Counter(sample["gold"] for sample in samples).items())),
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(samples)} questions from {len(dataset)} test rows")
    print(f"Subjects: {len(manifest['subject_counts'])}; answer counts: {manifest['gold_counts']}")
    print(f"Input: {OUT}")
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
