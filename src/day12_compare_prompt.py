"""逐题比较 Day 6 原版 GSM8K 与 Day 12 提示词变体。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FILTERS = ("strict-match", "flexible-extract")
ORIGINAL_LABEL = "Answer:"
VARIANT_LABEL = "Answer: Let's think step by step."


def load_run(run_dir: Path) -> tuple[dict, dict[int, dict[str, dict]], Path]:
    result_paths = list(run_dir.glob("results_*.json"))
    sample_paths = list(run_dir.glob("samples_*.jsonl"))
    if len(result_paths) != 1 or len(sample_paths) != 1:
        raise ValueError(f"{run_dir} 应各有一份 results 和 samples 文件")
    result = json.loads(result_paths[0].read_text(encoding="utf-8"))
    rows: dict[int, dict[str, dict]] = {}
    for line in sample_paths[0].open(encoding="utf-8"):
        row = json.loads(line)
        doc_id, name = int(row["doc_id"]), row["filter"]
        if name not in FILTERS or name in rows.setdefault(doc_id, {}):
            raise ValueError(f"题号 {doc_id} 的过滤器异常：{name}")
        rows[doc_id][name] = row
    if any(set(group) != set(FILTERS) for group in rows.values()):
        raise ValueError(f"{sample_paths} 有题目缺少过滤器结果")
    return result, rows, sample_paths[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-run-dir", type=Path, required=True)
    parser.add_argument("--variant-run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    baseline_result, baseline, baseline_path = load_run(args.baseline_run_dir)
    variant_result, variant, variant_path = load_run(args.variant_run_dir)
    if set(baseline) != set(variant):
        raise ValueError("两次运行的题号集合不同")
    if baseline_result["config"] != variant_result["config"]:
        raise ValueError("两次运行的模型或评测参数不同")
    for key in ("lm_eval_version", "transformers_version", "git_hash"):
        if baseline_result.get(key) != variant_result.get(key):
            raise ValueError(f"两次运行的 {key} 不同")

    comparisons: dict[str, dict] = {}
    for name in FILTERS:
        improved, worsened, both_correct, both_wrong = [], [], [], []
        for doc_id in sorted(baseline):
            old, new = baseline[doc_id][name], variant[doc_id][name]
            if old["doc"] != new["doc"] or old["target"] != new["target"]:
                raise ValueError(f"题号 {doc_id} 的题目或标准答案不同")
            old_prompt = old["arguments"]["gen_args_0"]["arg_0"]
            new_prompt = new["arguments"]["gen_args_0"]["arg_0"]
            if new_prompt.replace(VARIANT_LABEL, ORIGINAL_LABEL) != old_prompt:
                raise ValueError(f"题号 {doc_id} 的输入不止回答提示发生变化")
            old_correct, new_correct = bool(old["exact_match"]), bool(new["exact_match"])
            category = (
                improved if new_correct and not old_correct else
                worsened if old_correct and not new_correct else
                both_correct if old_correct else both_wrong
            )
            category.append(doc_id)

        old_score = sum(bool(baseline[i][name]["exact_match"]) for i in baseline)
        new_score = sum(bool(variant[i][name]["exact_match"]) for i in variant)
        if old_score != len(both_correct) + len(worsened):
            raise ValueError("原版逐题分数统计不一致")
        if new_score != len(both_correct) + len(improved):
            raise ValueError("变体逐题分数统计不一致")
        comparisons[name] = {
            "baseline_correct": old_score,
            "variant_correct": new_score,
            "delta_percentage_points": 100 * (new_score - old_score) / len(baseline),
            "improved_ids": improved,
            "worsened_ids": worsened,
            "both_correct_count": len(both_correct),
            "both_wrong_count": len(both_wrong),
            "baseline_extraction_failed_ids": [
                i for i in sorted(baseline)
                if baseline[i][name]["filtered_resps"] == ["[invalid]"]
            ],
            "variant_extraction_failed_ids": [
                i for i in sorted(variant)
                if variant[i][name]["filtered_resps"] == ["[invalid]"]
            ],
        }

    report = {
        "baseline_samples": str(baseline_path),
        "variant_samples": str(variant_path),
        "questions": len(baseline),
        "controlled_variables_verified": True,
        "prompt_change": {"from": ORIGINAL_LABEL, "to": VARIANT_LABEL},
        "filters": comparisons,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"题目数：{len(baseline)}；相同题目、模型参数、版本及种子：已核对")
    for name, comparison in comparisons.items():
        print(
            f"{name}: {comparison['baseline_correct']} -> {comparison['variant_correct']}；"
            f"新答对 {len(comparison['improved_ids'])} 题，答错增加 {len(comparison['worsened_ids'])} 题；"
            f"净变化 {comparison['delta_percentage_points']:+.1f} 个百分点"
        )
        print(f"  新答对：{comparison['improved_ids']}")
        print(f"  新答错：{comparison['worsened_ids']}")
        print(
            f"  抽取失败题号：原版 {comparison['baseline_extraction_failed_ids']}；"
            f"变体 {comparison['variant_extraction_failed_ids']}"
        )
    print(f"明细：{args.out}")


if __name__ == "__main__":
    main()
