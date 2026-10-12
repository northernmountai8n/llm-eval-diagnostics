"""Summarize the fixed Day 18 DeepSeek Flash / MMLU 50-question run."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "day18_mmlu_flash50.jsonl"
MANIFEST = ROOT / "data" / "day18_mmlu_flash50.manifest.json"
RESULTS = ROOT / "runs" / "day18_deepseek_mmlu50.jsonl"
REPORT = ROOT / "reports" / "18-deepseek-mmlu50.md"
EXPECTED_MODEL = "deepseek-flash"
EXPECTED_URL = "https://api.deepseek.com/chat/completions"
EXPECTED_OPTIONS = {"thinking": {"type": "disabled"}, "max_tokens": 16, "temperature": 0.0}


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON at {path}:{line_number}: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"Expected object at {path}:{line_number}")
        rows.append(row)
    return rows


def wilson_interval(correct: int, total: int) -> tuple[float, float]:
    z = 1.96
    p = correct / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half_width = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return center - half_width, center + half_width


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    digest = hashlib.sha256(INPUT.read_bytes()).hexdigest()
    if digest != manifest["input_sha256"]:
        raise ValueError("MMLU input hash differs from the frozen manifest")
    samples = read_jsonl(INPUT)
    if len(samples) != manifest["count"] or len({row["id"] for row in samples}) != len(samples):
        raise ValueError("MMLU input count or sample IDs differ from the manifest")
    sample_by_id = {row["id"]: row for row in samples}
    encoding_flags = [row["id"] for row in samples if "Õ" in row["question"] or "�" in row["question"]]
    results = read_jsonl(RESULTS)
    result_by_id = {}
    for row in results:
        sample_id = row.get("id")
        if sample_id not in sample_by_id or sample_id in result_by_id:
            raise ValueError(f"Unexpected or duplicate result ID: {sample_id}")
        sample = sample_by_id[sample_id]
        if (
            row.get("question") != sample["question"]
            or row.get("gold") != sample["gold"]
            or row.get("model") != EXPECTED_MODEL
            or row.get("url") != EXPECTED_URL
            or row.get("request_options") != EXPECTED_OPTIONS
        ):
            raise ValueError(f"Result ID {sample_id} does not match the frozen experiment config")
        answer = row.get("answer")
        if not isinstance(answer, str):
            raise ValueError(f"Result ID {sample_id} has no text answer")
        if row.get("exact_match") != int(answer.strip() == sample["gold"]):
            raise ValueError(f"Result ID {sample_id} has inconsistent exact_match")
        result_by_id[sample_id] = row

    missing = sorted(set(sample_by_id) - set(result_by_id))
    completed = len(result_by_id)
    correct = sum(row["exact_match"] for row in result_by_id.values())
    invalid = [
        row
        for row in result_by_id.values()
        if not (len(row["answer"].strip()) == 1 and row["answer"].strip() in "ABCD")
    ]
    truncated = [row for row in result_by_id.values() if row.get("finish_reason") == "length"]
    usage = Counter()
    for row in result_by_id.values():
        if isinstance(row.get("usage"), dict):
            for field in ("prompt_tokens", "completion_tokens", "total_tokens", "prompt_cache_hit_tokens"):
                value = row["usage"].get(field)
                if isinstance(value, int):
                    usage[field] += value

    lines = [
        "# Day 18｜DeepSeek Flash 的 MMLU 50 题 API 小实验",
        "",
        f"- 状态：{'完成' if not missing else f'未完成，已完成 {completed}/50 题'}。",
        f"- 数据：`{manifest['dataset']}` / `{manifest['config']}` / `{manifest['split']}`；revision `{manifest['revision']}`，共 {manifest['dataset_rows']} 道测试题。",
        f"- 抽样：固定种子 {manifest['seed']}，从整个 test 集简单随机、不放回抽取 {manifest['count']} 题；覆盖 {len(manifest['subject_counts'])} 个学科。题号、源数据索引和哈希见 `data/day18_mmlu_flash50.manifest.json`。",
        f"- 标准答案位置分布：{manifest['gold_counts']}。沿用源数据原文；可见编码异常待复核题 ID：{encoding_flags}。",
        "- 设置：0-shot 英文四选一提示词；请求模型 `deepseek-flash`；非思考模式、`temperature=0`、`max_tokens=16`；每题只接受原始回复去掉首尾空白后恰为大写 `A`/`B`/`C`/`D`。",
        "- 指标：答对数 / 50；多余文字、小写字母和其他格式记为格式无效并计错。这个口径与项目之前 5-shot、选项似然判分的 Qwen MMLU 实验不同。",
        "",
        "## 结果",
        "",
    ]
    if missing:
        lines.extend(
            [
                f"尚缺 {len(missing)} 题，ID：{missing}。**此时不报告最终准确率。**沿用同一结果文件重新运行即可续跑。",
                "",
            ]
        )
    else:
        lower, upper = wilson_interval(correct, len(samples))
        lines.extend(
            [
                f"- 正确：**{correct}/50 = {correct / 50:.1%}**。",
                f"- 95% Wilson 近似区间：**{lower:.1%}～{upper:.1%}**。这是 50 题抽样的不确定性提示，不是模型在完整 MMLU 上的保证。",
                f"- 格式无效：{len(invalid)}/50；因输出长度截断：{len(truncated)}/50。",
                "",
            ]
        )

    if completed:
        response_models = sorted({str(row.get("response_model")) for row in result_by_id.values()})
        fingerprints = sorted({str(row.get("system_fingerprint")) for row in result_by_id.values()})
        lines.extend(
            [
                f"- API 实际返回的 `model`：{response_models}；`system_fingerprint`：{fingerprints}。",
                "- API 用量：" + ("；".join(f"{key}={value}" for key, value in sorted(usage.items())) if usage else "响应未提供可汇总的 token 用量") + "。",
                "",
                "### 错题与格式异常（最多列前 10 条）",
                "",
                "| ID | 学科 | 标准答案 | 原始回复 |",
                "| ---: | --- | :---: | --- |",
            ]
        )
        wrong = [result_by_id[sample["id"]] for sample in samples if sample["id"] in result_by_id and result_by_id[sample["id"]]["exact_match"] == 0]
        for row in wrong[:10]:
            sample = sample_by_id[row["id"]]
            answer = row["answer"].replace("|", "\\|").replace("\n", " ")[:120]
            lines.append(f"| {row['id']} | {sample['subject']} | {sample['gold']} | {answer} |")
        if not wrong:
            lines.append("| — | — | — | 无 |")
        lines.append("")

    lines.extend(
        [
            "## 解读边界",
            "",
            "- 这是 50 题的探索性 0-shot API 实验，不是官方 MMLU 全量分数；样本少、跨学科，每学科题数也很少。",
            "- 严格单字母判分同时检验知识和输出格式；若要与其他模型公平比较，需让它们使用完全相同的题目、提示词、抽取规则和推理设置。",
            "- `deepseek-flash` 是服务端模型名，具体服务版本可能变化；因此保存实际响应模型和指纹（如果 API 提供）。温度为 0 也不保证跨服务版本逐位一致。",
            "- `usage` 是 API 返回的 token 数，不等于已核实的账单金额。重试还可能产生额外用量。",
            "",
            "原始题目：`data/day18_mmlu_flash50.jsonl`；原始响应：`runs/day18_deepseek_mmlu50.jsonl`。",
            "",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {REPORT}")
    print(f"Completed: {completed}/50; missing: {len(missing)}; correct among completed: {correct}")


if __name__ == "__main__":
    main()
