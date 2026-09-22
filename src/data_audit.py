"""
benchmark 数据质检脚本 —— 项目实验一
================================================
对 benchmark 数据集执行 6 类质量检查，输出带样本示例的报告。

用法:
    python src/data_audit.py --dataset ceval/ceval-exam --config high_school_physics
    python src/data_audit.py --dataset cais/mmlu --config abstract_algebra
    python src/data_audit.py --dataset ceval/ceval-exam --config high_school_physics --split val

设计说明（面试会问，所以写在代码里）:
    - 所有检查都是"只报告不修改"：先量化问题规模，再决定要不要修
    - 每个问题都输出"数量 + 具体例子 + 影响判断"，因为只报数量无法判断严重性
    - 检查项是防御性的：字段不存在就跳过该项而不是崩溃，因为不同数据集 schema 差异很大
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------- 常量

# C-Eval / CMMLU 用 A-D 作为列名；MMLU 用 choices 列表
CHOICE_KEYS = ("A", "B", "C", "D", "E", "F")
# 常见的大小写混用的答案字段名
ANSWER_KEYS = ("answer", "label", "target", "gold", "correct")
QUESTION_KEYS = ("question", "input", "prompt", "text")

# 近重复检测的 shingle 宽度（字符级 n-gram）
SHINGLE_SIZE = 5
# 近重复判定阈值（Jaccard 相似度）
NEAR_DUP_THRESHOLD = 0.8
# 长度异常的分位点
LOW_Q, HIGH_Q = 0.01, 0.99


# ---------------------------------------------------------------- 工具函数

def normalize(text: str) -> str:
    """归一化文本：统一 Unicode、转小写、压缩空白、去掉标点。

    为什么要归一化：'What is 2+2?' 和 'what is 2 + 2 ?' 在语义上重复，
    但原始字符串比较检不出来。近重复检测必须先归一化。
    """
    if not isinstance(text, str):
        return ""
    # NFKC 把全角字符转半角（中文 benchmark 常见问题）
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()


def shingles(text: str, k: int = SHINGLE_SIZE) -> set[str]:
    """字符级 k-gram 集合，用于近重复检测。"""
    text = normalize(text)
    if len(text) < k:
        return {text} if text else set()
    return {text[i : i + k] for i in range(len(text) - k + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def quantile(values: list[int], q: float) -> float:
    """简单分位数（不引入 numpy 依赖，保持脚本轻量）。"""
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(int(q * len(ordered)), len(ordered) - 1)
    return float(ordered[idx])


def pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.1f}%" if whole else "n/a"


# ---------------------------------------------------------------- 字段抽取

def get_question(row: dict[str, Any]) -> str:
    """从一行数据里取题干，兼容多种 schema。"""
    for key in QUESTION_KEYS:
        val = row.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def get_choices(row: dict[str, Any]) -> list[str]:
    """取选项列表，兼容 C-Eval 的 A/B/C/D 列 和 MMLU 的 choices 列表。"""
    if isinstance(row.get("choices"), (list, tuple)):
        return [str(c) for c in row["choices"]]
    out = []
    for key in CHOICE_KEYS:
        val = row.get(key)
        if isinstance(val, str) and val.strip():
            out.append(val)
    return out


def get_answer(row: dict[str, Any]) -> str:
    """取答案字段。"""
    for key in ANSWER_KEYS:
        val = row.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


# ---------------------------------------------------------------- 六类检查

def check_exact_duplicates(rows: list[dict]) -> dict:
    """检查 1: 完全重复。

    为什么重要：重复样本会变相加权某个知识点，让分数偏向该知识点的表现。
    """
    seen: dict[str, int] = {}
    dup_groups: dict[str, list[int]] = {}
    for i, row in enumerate(rows):
        key = hashlib.md5(
            (normalize(get_question(row)) + "||" + normalize(get_answer(row))).encode()
        ).hexdigest()
        if key in seen:
            dup_groups.setdefault(key, [seen[key]]).append(i)
        else:
            seen[key] = i
    examples = [
        {"indices": idxs, "question": get_question(rows[idxs[0]])[:120]}
        for idxs in list(dup_groups.values())[:5]
    ]
    return {
        "name": "完全重复",
        "count": sum(len(v) - 1 for v in dup_groups.values()),
        "groups": len(dup_groups),
        "examples": examples,
        "impact": "变相加权部分知识点，扭曲分数构成",
    }


def check_near_duplicates(rows: list[dict], cap: int = 3000) -> dict:
    """检查 2: 近重复（换皮重复）。

    为什么重要：改个标点、换个说法就能绕过完全重复检查，但仍然是重复。
    注意：O(n^2) 比较，样本多时截断（这里只做示范，生产要上 MinHash/LSH）。
    """
    items = [
        (i, shingles(get_question(r))) for i, r in enumerate(rows[:cap])
    ]
    pairs: list[dict] = []
    for a in range(len(items)):
        ia, sa = items[a]
        if not sa:
            continue
        for b in range(a + 1, len(items)):
            ib, sb = items[b]
            if not sb:
                continue
            sim = jaccard(sa, sb)
            if sim >= NEAR_DUP_THRESHOLD:
                pairs.append(
                    {
                        "indices": [ia, ib],
                        "similarity": round(sim, 3),
                        "question": get_question(rows[ia])[:100],
                    }
                )
    return {
        "name": "近重复",
        "count": len(pairs),
        "scanned": min(cap, len(rows)),
        "truncated": len(rows) > cap,
        "examples": pairs[:5],
        "impact": "与完全重复同源，但更隐蔽",
    }


def check_answer_validity(rows: list[dict]) -> dict:
    """检查 3: 答案合法性（越界 / 格式不一致）。

    为什么重要：这是唯一一类会"直接导致判分错误"的问题。
    答案字段是 'C' 但只有 3 个选项、或者答案是 'C.' 带标点，
    都会让判分逻辑失效。
    """
    out_of_range: list[dict] = []
    malformed: list[dict] = []
    for i, row in enumerate(rows):
        ans = get_answer(row)
        choices = get_choices(row)
        if not ans or not choices:
            continue
        letters = [k for k in CHOICE_KEYS[: len(choices)]]
        if ans not in letters:
            # 是不是数字索引或带标点
            if ans.strip().rstrip(".").upper() in letters:
                malformed.append({"index": i, "answer": ans})
            else:
                out_of_range.append(
                    {"index": i, "answer": ans, "n_choices": len(choices)}
                )
    return {
        "name": "答案合法性",
        "count": len(out_of_range) + len(malformed),
        "out_of_range": len(out_of_range),
        "malformed": len(malformed),
        "examples": (out_of_range[:3] + malformed[:3]),
        "impact": "直接导致判分错误 —— 优先级最高",
    }


def check_position_bias(rows: list[dict]) -> dict:
    """检查 4: 选项位置偏置。

    为什么重要：若正确答案系统性集中在某个位置，模型可能"学会猜位置"
    而非"学会知识"，分数会被高估。这是 benchmark 构建质量的直接指标。
    """
    counter: Counter[str] = Counter()
    for row in rows:
        ans = get_answer(row)
        choices = get_choices(row)
        if ans in CHOICE_KEYS[: len(choices)]:
            counter[ans] += 1
    total = sum(counter.values())
    if not total:
        return {"name": "选项位置偏置", "count": 0, "examples": [], "impact": "无法计算"}
    dist = {k: round(100 * v / total, 1) for k, v in sorted(counter.items())}
    expected = 100 / len(counter)
    # 偏离均匀分布超过 5 个百分点视为可疑
    suspicious = {k: v for k, v in dist.items() if abs(v - expected) > 5}
    return {
        "name": "选项位置偏置",
        "count": len(suspicious),
        "distribution": dist,
        "expected_uniform_pct": round(expected, 1),
        "examples": [{"position": k, "pct": v} for k, v in suspicious.items()],
        "impact": "正确答案集中 → 模型可能靠猜位置而非知识得分（虚高）",
    }


def check_length_anomalies(rows: list[dict]) -> dict:
    """检查 5: 长度异常。

    为什么重要：超长样本可能被 tokenizer 截断，造成"静默错误"——
    模型不报错、评测不报错，但模型看到的是被切掉的题。
    """
    q_lens = [len(get_question(r)) for r in rows]
    c_lens = [
        len(c) for r in rows for c in get_choices(r) if isinstance(c, str)
    ]
    if not q_lens:
        return {"name": "长度异常", "count": 0, "examples": [], "impact": "无题干"}
    lo, hi = quantile(q_lens, LOW_Q), quantile(q_lens, HIGH_Q)
    long_ones = [
        {"index": i, "length": len(get_question(r)), "preview": get_question(r)[:80]}
        for i, r in enumerate(rows)
        if len(get_question(r)) > hi
    ]
    short_ones = [
        {"index": i, "length": len(get_question(r)), "preview": get_question(r)[:80]}
        for i, r in enumerate(rows)
        if len(get_question(r)) < lo
    ]
    # 选项长度差异 → 会放大 acc 与 acc_norm 的差距
    mean_c = sum(c_lens) / len(c_lens) if c_lens else 0
    return {
        "name": "长度异常",
        "count": len(long_ones) + len(short_ones),
        "question_len": {
            "min": min(q_lens),
            "p01": lo,
            "median": quantile(q_lens, 0.5),
            "p99": hi,
            "max": max(q_lens),
            "mean": round(sum(q_lens) / len(q_lens), 1),
        },
        "choice_len_mean": round(mean_c, 1),
        "examples": (long_ones[:3] + short_ones[:3]),
        "impact": "超长样本可能被截断（静默错误）；选项长度差异会放大 acc 与 acc_norm 的分歧",
    }


def check_encoding(rows: list[dict]) -> dict:
    """检查 6: 编码与脏字符。

    为什么重要：中文 benchmark 高频问题。多余空白、不可见字符、
    全半角混用都会影响 prompt 拼装，进而影响分数。
    """
    issues: list[dict] = []
    for i, row in enumerate(rows):
        text = get_question(row) + "".join(get_choices(row))
        problems = []
        if "\u3000" in text:
            problems.append("全角空格")
        if re.search(r"[\u200b-\u200f\ufeff]", text):
            problems.append("零宽/不可见字符")
        if re.search(r"[ \t]{2,}", text):
            problems.append("连续空白")
        if re.search(r"[\uff01-\uff5e]", text) and re.search(r"[!-~]", text):
            problems.append("全半角混用")
        if problems:
            issues.append({"index": i, "problems": problems})
    summary = Counter(p for it in issues for p in it["problems"])
    return {
        "name": "编码与脏字符",
        "count": len(issues),
        "breakdown": dict(summary),
        "examples": issues[:5],
        "impact": "影响 prompt 拼装，可能改变 tokenization 与分数",
    }


# ---------------------------------------------------------------- 主流程

def audit(rows: list[dict], name: str) -> dict:
    checks = [
        check_exact_duplicates(rows),
        check_near_duplicates(rows),
        check_answer_validity(rows),
        check_position_bias(rows),
        check_length_anomalies(rows),
        check_encoding(rows),
    ]
    return {"dataset": name, "n_samples": len(rows), "checks": checks}


def render_markdown(result: dict) -> str:
    """渲染成 Markdown 报告 —— 这份报告会直接进你的项目仓库。"""
    lines = [
        f"# 数据质检报告：{result['dataset']}",
        "",
        f"- 样本数：**{result['n_samples']}**",
        "",
        "| 检查项 | 问题数 | 影响 |",
        "|---|---|---|",
    ]
    for c in result["checks"]:
        lines.append(f"| {c['name']} | {c['count']} | {c.get('impact', '')} |")

    lines.append("")
    for c in result["checks"]:
        lines.append(f"## {c['name']}（{c['count']}）")
        lines.append("")
        if c["name"] == "选项位置偏置" and c.get("distribution"):
            lines.append(f"分布：`{c['distribution']}`（均匀应为 {c.get('expected_uniform_pct')}%）")
        if c["name"] == "长度异常" and c.get("question_len"):
            lines.append(f"题干长度：`{c['question_len']}`")
        if c["name"] == "编码与脏字符" and c.get("breakdown"):
            lines.append(f"分类：`{c['breakdown']}`")
        if c.get("examples"):
            lines.append("")
            lines.append("例子：")
            lines.append("```json")
            lines.append(json.dumps(c["examples"], ensure_ascii=False, indent=2)[:1500])
            lines.append("```")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("> 说明：本报告只量化问题，不做修改。")
    lines.append("> 判断某类问题是否需要修复，取决于它的规模是否足以影响结论。")
    return "\n".join(lines)


def load_rows(dataset: str, config: str | None, split: str) -> list[dict]:
    """加载数据集。依赖 HuggingFace datasets。"""
    try:
        from datasets import load_dataset
    except ImportError:
        sys.exit("缺少依赖：pip install datasets")

    if config:
        ds = load_dataset(dataset, config, split=split)
    else:
        ds = load_dataset(dataset, split=split)
    return [dict(r) for r in ds]


def main() -> None:
    p = argparse.ArgumentParser(description="benchmark 数据质检")
    p.add_argument("--dataset", required=True, help="如 ceval/ceval-exam")
    p.add_argument("--config", default=None, help="如 high_school_physics")
    p.add_argument("--split", default="val", help="默认 val")
    p.add_argument("--out", default=None, help="输出 Markdown 路径")
    p.add_argument("--json", action="store_true", help="同时输出 JSON")
    args = p.parse_args()

    name = f"{args.dataset}" + (f"/{args.config}" if args.config else "")
    print(f"[load] {name} split={args.split}", file=sys.stderr)
    rows = load_rows(args.dataset, args.config, args.split)
    print(f"[load] {len(rows)} 条样本", file=sys.stderr)

    result = audit(rows, name)
    report = render_markdown(result)

    out = Path(args.out) if args.out else Path("reports") / f"data_audit_{args.config or 'all'}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"[write] {out}", file=sys.stderr)

    if args.json:
        js = out.with_suffix(".json")
        js.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[write] {js}", file=sys.stderr)

    # 终端上给个速览
    for c in result["checks"]:
        print(f"  {c['name']:<12} {c['count']}")


if __name__ == "__main__":
    main()
