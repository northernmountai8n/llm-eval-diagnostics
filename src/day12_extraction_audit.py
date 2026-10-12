"""复现 lm-eval 的 GSM8K 答案抽取，并核对 Day 6 逐题记录。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


INVALID = "[invalid]"
STRICT = re.compile(r"#### (\-?[0-9\.\,]+)")
FLEXIBLE = re.compile(r"(-?[$0-9.,]{2,})|(-?[0-9]+)")
FILTERS = ("strict-match", "flexible-extract")


def extract_strict(response: str) -> str:
    matches = STRICT.findall(response)
    return matches[0].strip() if matches else INVALID


def extract_flexible(response: str) -> str:
    matches = FLEXIBLE.findall(response)
    if not matches:
        return INVALID
    return next((part for part in matches[-1] if part), INVALID).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    paths = list(args.run_dir.glob("samples_gsm8k_*.jsonl"))
    if len(paths) != 1:
        parser.error(f"需要恰好一份 GSM8K 逐题文件，实际找到 {len(paths)} 份")
    rows = [json.loads(line) for line in paths[0].open(encoding="utf-8")]

    by_id: dict[int, dict[str, dict]] = {}
    for row in rows:
        name = row["filter"]
        if name not in FILTERS:
            continue
        doc_id = int(row["doc_id"])
        group = by_id.setdefault(doc_id, {})
        if name in group:
            raise ValueError(f"题号 {doc_id} 的 {name} 记录重复")
        group[name] = row

    missing = [doc_id for doc_id, group in by_id.items() if set(group) != set(FILTERS)]
    if missing:
        raise ValueError(f"有题目缺少过滤器记录：{missing[:10]}")

    strict_failed: list[dict] = []
    changed: list[dict] = []
    correct = {name: 0 for name in FILTERS}
    for doc_id in sorted(by_id):
        strict_row = by_id[doc_id]["strict-match"]
        flexible_row = by_id[doc_id]["flexible-extract"]
        response = strict_row["resps"][0][0]
        if response != flexible_row["resps"][0][0]:
            raise ValueError(f"题号 {doc_id} 的两条原始回答不同")

        strict_value = extract_strict(response)
        flexible_value = extract_flexible(response)
        if strict_value != strict_row["filtered_resps"][0]:
            raise ValueError(f"题号 {doc_id} 的严格抽取与 lm-eval 不一致")
        if flexible_value != flexible_row["filtered_resps"][0]:
            raise ValueError(f"题号 {doc_id} 的宽松抽取与 lm-eval 不一致")

        correct["strict-match"] += int(strict_row["exact_match"])
        correct["flexible-extract"] += int(flexible_row["exact_match"])
        detail = {
            "doc_id": doc_id,
            "gold": strict_row["target"].rsplit("####", 1)[-1].strip(),
            "strict": strict_value,
            "flexible": flexible_value,
            "strict_correct": bool(strict_row["exact_match"]),
            "flexible_correct": bool(flexible_row["exact_match"]),
            "response_tail": response[-400:],
        }
        if strict_value == INVALID:
            strict_failed.append(detail)
        if strict_value != flexible_value:
            changed.append(detail)

    n = len(by_id)
    flexible_failed = sum(
        extract_flexible(by_id[doc_id]["strict-match"]["resps"][0][0]) == INVALID
        for doc_id in by_id
    )
    result = {
        "source": str(paths[0]),
        "questions": n,
        "strict_failed": len(strict_failed),
        "strict_failure_rate": len(strict_failed) / n if n else 0,
        "flexible_failed": flexible_failed,
        "strict_correct": correct["strict-match"],
        "flexible_correct": correct["flexible-extract"],
        "score_delta_percentage_points":
            100 * (correct["flexible-extract"] - correct["strict-match"]) / n if n else 0,
        "strict_failed_examples": strict_failed,
        "different_extractions": changed,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"题目数：{n}")
    print(f"严格抽取失败：{len(strict_failed)}/{n}（{result['strict_failure_rate']:.1%}）")
    print(f"宽松抽取失败：{flexible_failed}/{n}")
    print(f"严格/宽松答对：{correct['strict-match']}/{n}、{correct['flexible-extract']}/{n}")
    print(f"抽取结果不同的题号：{[x['doc_id'] for x in changed]}")
    print(f"明细：{args.out}")


if __name__ == "__main__":
    main()
