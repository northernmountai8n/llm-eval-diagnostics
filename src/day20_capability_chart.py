"""Summarize the three pinned Day 6 MMLU runs and draw an SVG chart.

Run from any directory with the project's lmeval Python environment:
    python src/day20_capability_chart.py
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

from lm_eval.tasks.mmlu._generate_configs import SUBJECTS


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports"
MODELS = (
    ("0.5B", "05", "0.5B"),
    ("1.5B", "15", "1.5B"),
    ("3B", "3", "3B"),
)
GROUPS = (
    ("stem", "STEM"),
    ("humanities", "Humanities"),
    ("social_sciences", "Social sciences"),
    ("other", "Other"),
)
COLORS = ("#6D94CF", "#EFAB61", "#4EAD91")


def read_scores() -> dict[str, dict[str, list[float]]]:
    scores_by_model = {}
    reference_questions = None
    for label, short, size in MODELS:
        directory = (
            ROOT
            / "runs"
            / f"day06_qwen{short}_mmlu_s5_n10"
            / f"Qwen__Qwen2.5-{size}"
        )
        files = sorted(directory.glob("samples_mmlu_*.jsonl"))
        if len(files) != 57:
            raise ValueError(f"{label}: expected 57 subject files, found {len(files)}")
        scores = defaultdict(list)
        questions = set()
        for file in files:
            with file.open(encoding="utf-8") as handle:
                for line in handle:
                    row = json.loads(line)
                    doc = row["doc"]
                    subject = doc["subject"]
                    if subject not in SUBJECTS:
                        raise ValueError(f"Unmapped subject: {subject}")
                    questions.add((subject, row["doc_id"], doc["question"]))
                    scores[SUBJECTS[subject]].append(float(row["acc"]))
        if sum(map(len, scores.values())) != 570 or len(questions) != 570:
            raise ValueError(f"{label}: expected 570 distinct question records")
        if reference_questions is not None and questions != reference_questions:
            raise ValueError(f"{label}: question set differs from the first model")
        reference_questions = questions
        scores_by_model[label] = scores
    return scores_by_model


def write_csv(scores: dict[str, dict[str, list[float]]]) -> Path:
    path = OUTPUT / "day20_mmlu_by_category.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["category", "questions", "0.5B_percent", "1.5B_percent", "3B_percent", "3B_minus_0.5B_pp", "3B_minus_1.5B_pp"]
        )
        for group, _ in GROUPS:
            values = [100 * sum(scores[label][group]) / len(scores[label][group]) for label, _, _ in MODELS]
            writer.writerow(
                [group, len(scores["0.5B"][group]), *(f"{value:.2f}" for value in values), f"{values[2] - values[0]:.2f}", f"{values[2] - values[1]:.2f}"]
            )
    return path


def write_svg(scores: dict[str, dict[str, list[float]]]) -> Path:
    width, height = 820, 490
    left, top, plot_height = 76, 82, 300
    baseline = top + plot_height
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        "<title>Qwen2.5 MMLU accuracy by category and model size</title>",
        "<desc>Three base model sizes on the same 570 MMLU questions, five-shot. Each subject contributes its first ten test questions.</desc>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="76" y="31" font-family="Arial,sans-serif" font-size="19" font-weight="bold" fill="#182334">MMLU by category and model size</text>',
        '<text x="76" y="53" font-family="Arial,sans-serif" font-size="12" fill="#546174">Same 570 questions; 5-shot; accuracy (%)</text>',
    ]
    for tick in range(0, 101, 20):
        y = baseline - tick * plot_height / 100
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="790" y2="{y:.1f}" stroke="#e4e8ee"/>')
        parts.append(f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" font-family="Arial,sans-serif" font-size="11" fill="#657184">{tick}</text>')
    for group_index, (group, display_name) in enumerate(GROUPS):
        center = 165 + group_index * 177
        n = len(scores["0.5B"][group])
        for model_index, (label, _, _) in enumerate(MODELS):
            value = 100 * sum(scores[label][group]) / n
            x = center - 47 + model_index * 34
            y = baseline - value * plot_height / 100
            h = baseline - y
            parts.append(f'<rect x="{x}" y="{y:.1f}" width="29" height="{h:.1f}" fill="{COLORS[model_index]}"/>')
            parts.append(f'<text x="{x + 14.5:.1f}" y="{y - 6:.1f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="10" fill="#263449">{value:.1f}</text>')
        parts.append(f'<text x="{center}" y="{baseline + 21}" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#182334">{escape(display_name)}</text>')
        parts.append(f'<text x="{center}" y="{baseline + 37}" text-anchor="middle" font-family="Arial,sans-serif" font-size="10" fill="#657184">n={n}</text>')
    for index, (label, _, _) in enumerate(MODELS):
        x = 310 + index * 90
        parts.append(f'<rect x="{x}" y="446" width="15" height="12" fill="{COLORS[index]}"/>')
        parts.append(f'<text x="{x + 21}" y="457" font-family="Arial,sans-serif" font-size="12" fill="#263449">{label}</text>')
    parts.append("</svg>")
    path = OUTPUT / "day20_mmlu_by_category.svg"
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    scores = read_scores()
    csv_path = write_csv(scores)
    svg_path = write_svg(scores)
    print("Verified: 57 subjects x 10 questions x 3 models; question sets match.")
    print(f"Table: {csv_path}")
    print(f"Chart: {svg_path}")


if __name__ == "__main__":
    main()
