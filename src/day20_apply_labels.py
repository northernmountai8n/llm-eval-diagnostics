"""Merge manually reviewed Day 20 labels into the fixed GSM8K review sheet."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHEET = ROOT / "reports/day20_gsm8k_error_sample.csv"
LABELS = ROOT / "reports/day20_manual_labels.json"
CATEGORIES = {"知识缺失", "推理断裂", "格式错误", "指令误解", "题目本身有问题"}
CHART = ROOT / "reports/day20_error_categories.svg"


def write_chart(counts: Counter[str]) -> None:
    labels = (
        ("Instruction misread", "指令误解", "#db8d54"),
        ("Reasoning break", "推理断裂", "#668fcb"),
        ("Format / no final answer", "格式错误", "#8f7bbc"),
        ("Question / key issue", "题目本身有问题", "#71aa8b"),
        ("Knowledge gap", "知识缺失", "#aa9b6b"),
    )
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="810" height="370" viewBox="0 0 810 370" role="img">',
        '<title>Primary error categories in 50 reviewed GSM8K errors</title>',
        '<rect width="100%" height="100%" fill="#fff"/>',
        '<text x="42" y="35" font-family="Arial,sans-serif" font-size="21" font-weight="bold" fill="#172a40">GSM8K error audit</text>',
        '<text x="42" y="57" font-family="Arial,sans-serif" font-size="12" fill="#56667a">50 sampled strict-match errors from 76 errors in 200 questions; one primary label each</text>',
    ]
    for index, (display, category, color) in enumerate(labels):
        y = 88 + index * 52
        count = counts[category]
        width = count * 16
        parts.append(f'<text x="42" y="{y + 18}" font-family="Arial,sans-serif" font-size="13" fill="#263950">{display}</text>')
        parts.append(f'<rect x="270" y="{y}" width="{width}" height="26" fill="{color}"/>')
        parts.append(f'<text x="{280 + width}" y="{y + 18}" font-family="Arial,sans-serif" font-size="13" font-weight="bold" fill="#263950">{count}/50 ({count * 2}%)</text>')
    parts.append('<text x="42" y="352" font-family="Arial,sans-serif" font-size="11" fill="#66778b">Percentages describe the sampled errors, not all GSM8K questions.</text>')
    parts.append('</svg>')
    CHART.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    manual = json.loads(LABELS.read_text(encoding="utf-8"))["labels"]
    with SHEET.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames
        rows = list(reader)
    if columns is None or len(rows) != 50:
        raise ValueError("Expected the 50-row Day 20 review sheet")
    if {row["doc_id"] for row in rows} != set(manual):
        raise ValueError("Manual labels do not match the fixed sampled question IDs")
    for row in rows:
        finding = manual[row["doc_id"]]
        category = finding["category"]
        if category not in CATEGORIES or not finding["note"].strip():
            raise ValueError(f"Invalid or unsupported finding for ID {row['doc_id']}")
        prior = row["error_category_fill_in"].strip()
        if prior and prior != category:
            raise ValueError(f"Existing human label conflicts for ID {row['doc_id']}: {prior} vs {category}")
        row["error_category_fill_in"] = category
        if not row["evidence_note_fill_in"].strip():
            row["evidence_note_fill_in"] = finding["note"]
    with SHEET.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter(row["error_category_fill_in"] for row in rows)
    write_chart(counts)
    print(f"Reviewed: {len(rows)}; original user notes preserved")
    for category in ("知识缺失", "推理断裂", "格式错误", "指令误解", "题目本身有问题"):
        print(f"{category}: {counts[category]}/50 ({counts[category] * 2}%)")
    print(f"Review sheet: {SHEET}")
    print(f"Chart: {CHART}")


if __name__ == "__main__":
    main()
