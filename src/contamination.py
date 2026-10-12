"""用 Day 6 GSM8K 日志离线检查 13-word-gram 重叠。"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


QUESTION_RE = re.compile(r"(?ms)^Question: (.*?)\nAnswer:")


def words(text: str) -> list[str]:
    """NFKC、大小写合并，再按连续字母或数字切词。"""
    text = unicodedata.normalize("NFKC", text).casefold()
    return re.findall(r"\w+", text, flags=re.UNICODE)


def grams(text: str, n: int) -> set[tuple[str, ...]]:
    tokens = words(text)
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def load_samples(run_dir: Path) -> tuple[dict[int, dict], dict[int, str]]:
    paths = list(run_dir.glob("samples_gsm8k_*.jsonl"))
    if len(paths) != 1:
        raise ValueError(f"需要一份 Day 6 GSM8K 日志，在 {run_dir} 找到 {len(paths)} 份")
    tests: dict[int, dict] = {}
    fewshots: dict[str, dict] = {}
    for line in paths[0].open(encoding="utf-8"):
        row = json.loads(line)
        if row["filter"] != "strict-match":
            continue
        doc_id = int(row["doc_id"])
        if doc_id in tests:
            raise ValueError(f"题号 {doc_id} 重复")
        question = row["doc"]["question"]
        prompt = row["arguments"]["gen_args_0"]["arg_0"]
        prompt_questions = QUESTION_RE.findall(prompt)
        if len(prompt_questions) != 6 or prompt_questions[-1] != question:
            raise ValueError(f"题号 {doc_id} 的 5-shot 输入结构与预期不同")
        tests[doc_id] = {"question": question, "correct": bool(row["exact_match"])}
        for example in prompt_questions[:-1]:
            key = " ".join(words(example))
            if key not in fewshots:
                fewshots[key] = {"question": example, "seen_in_test_prompts": []}
            fewshots[key]["seen_in_test_prompts"].append(doc_id)
    return tests, {i: item["question"] for i, item in enumerate(fewshots.values())}


def overlap(
    tests: dict[int, dict], references: dict[int, str], n: int, *, self_compare: bool
) -> dict:
    index: dict[tuple[str, ...], set[int]] = defaultdict(set)
    for ref_id, question in references.items():
        for gram in grams(question, n):
            index[gram].add(ref_id)

    pairs: dict[tuple[int, int], set[tuple[str, ...]]] = defaultdict(set)
    for test_id, item in tests.items():
        for gram in grams(item["question"], n):
            for ref_id in index.get(gram, ()):
                if self_compare:
                    if ref_id == test_id:
                        continue
                    pair = (min(test_id, ref_id), max(test_id, ref_id))
                else:
                    pair = (test_id, ref_id)
                pairs[pair].add(gram)

    hit_ids = sorted({i for pair in pairs for i in pair} if self_compare else {i for i, _ in pairs})
    matched = [tests[i]["correct"] for i in hit_ids]
    unmatched = [item["correct"] for i, item in tests.items() if i not in hit_ids]
    examples = []
    for (test_id, ref_id), shared in sorted(pairs.items(), key=lambda x: (-len(x[1]), x[0]))[:10]:
        examples.append({
            "test_id": test_id,
            "reference_id": ref_id,
            "shared_ngram_count": len(shared),
            "example_shared_text": " ".join(sorted(shared)[0]),
            "test_question": tests[test_id]["question"],
            "reference_question": references[ref_id],
        })
    exact_pairs = [
        [test_id, ref_id] for test_id, ref_id in pairs
        if words(tests[test_id]["question"]) == words(references[ref_id])
    ]
    return {
        "test_questions_with_overlap": len(hit_ids),
        "test_question_ids_with_overlap": hit_ids,
        "question_pair_count": len(pairs),
        "exact_duplicate_pair_count": len(exact_pairs),
        "exact_duplicate_pairs": exact_pairs,
        "matched_correct": sum(matched),
        "matched_total": len(matched),
        "unmatched_correct": sum(unmatched),
        "unmatched_total": len(unmatched),
        "examples": examples,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--ngram", type=int, default=13)
    args = parser.parse_args()
    if args.ngram < 1:
        parser.error("--ngram 必须为正整数")

    tests, fewshots = load_samples(args.run_dir)
    if not tests:
        raise ValueError("没有找到测试题")
    within_test = overlap(tests, {i: x["question"] for i, x in tests.items()}, args.ngram, self_compare=True)
    against_fewshot = overlap(tests, fewshots, args.ngram, self_compare=False)
    too_short = [i for i, x in tests.items() if len(words(x["question"])) < args.ngram]

    sensitivity = None
    if args.ngram == 13:
        sensitivity = overlap(tests, {i: x["question"] for i, x in tests.items()}, 8, self_compare=True)

    result = {
        "source": str(args.run_dir),
        "method": f"{args.ngram} consecutive normalized words in question text",
        "normalization": "Unicode NFKC, casefold, Unicode word tokens; punctuation separates words",
        "test_question_count": len(tests),
        "unique_fewshot_question_count": len(fewshots),
        "test_questions_shorter_than_ngram": too_short,
        "within_test": within_test,
        "against_logged_fewshot_questions": against_fewshot,
        "within_test_8gram_sensitivity": sensitivity,
        "scope_warning": "Logged few-shot questions are only a subset of GSM8K train; neither comparison proves model pretraining exposure.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Day 13｜GSM8K 13-gram 重叠检测",
        "",
        "## 范围与方法",
        "",
        f"- 来源：`{args.run_dir}` 的 Day 6 日志；测试题 {len(tests)} 道，日志中不同的 5-shot 示例题 {len(fewshots)} 道。",
        f"- 只比较题干。Unicode NFKC 规范化、统一大小写、标点作为分隔符，再取连续 {args.ngram} 个词。",
        f"- 少于 {args.ngram} 个词、无法生成 n-gram 的测试题：{len(too_short)} 道，题号 {too_short}。",
        "- 这是测试集内部重叠和测试题对实际 few-shot 示例的重叠，不是对 Qwen 预训练语料的检测。",
        "- 概念区分：输入污染指测试题文本进入训练资料；标签污染还包含正确答案；语义污染指改写后仍是同一题。",
        "- GPT-3 论文附录 C 曾用 13-gram 检索清理训练数据；本文复现的是简化的题干重叠检查。",
        "",
        "## 结果",
        "",
        "| 对照范围 | 命中测试题 | 命中题对 | 完全重复题对 | 命中题正确数 | 未命中题正确数 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, data in (("测试集内部", within_test), ("对日志中的 few-shot 示例", against_fewshot)):
        matched_score = (
            f"{data['matched_correct']}/{data['matched_total']}"
            if data["matched_total"] else "无命中题"
        )
        lines.append(
            f"| {label} | {data['test_questions_with_overlap']}/{len(tests)} "
            f"({data['test_questions_with_overlap']/len(tests):.1%}) | "
            f"{data['question_pair_count']} | {data['exact_duplicate_pair_count']} | "
            f"{matched_score} | "
            f"{data['unmatched_correct']}/{data['unmatched_total']} |"
        )
    for label, data in (("测试集内部", within_test), ("对日志中的 few-shot 示例", against_fewshot)):
        lines.extend(["", f"## {label}：命中样例", ""])
        if not data["examples"]:
            lines.append("没有检出共享 13-gram；不能据此断言不存在语义相似或其他来源的训练污染。")
            continue
        for example in data["examples"][:5]:
            lines.extend([
                f"- 测试题 {example['test_id']} ↔ 对照题 {example['reference_id']}："
                f"共享 {example['shared_ngram_count']} 个 {args.ngram}-gram，示例片段："
                f"“{example['example_shared_text']}”。",
                f"  - 测试题：{example['test_question']}",
                f"  - 对照题：{example['reference_question']}",
            ])
    if sensitivity is not None:
        lines.extend([
            "", "## 阈值敏感性：8-gram", "",
            f"把阈值缩短到 8 个词后，测试集内部命中 "
            f"{sensitivity['test_questions_with_overlap']}/{len(tests)} 道题、"
            f"{sensitivity['question_pair_count']} 对题，完全重复 {sensitivity['exact_duplicate_pair_count']} 对。",
        ])
        for example in sensitivity["examples"][:3]:
            lines.append(
                f"- {example['test_id']} ↔ {example['reference_id']}："
                f"“{example['example_shared_text']}”。"
            )
        lines.append("这几个短片段是普通措辞；缩短阈值可能增加误报，需逐条检查完整题干。")
    lines.extend([
        "", "## 人工复核与结论", "",
        "逐条查看上方命中样例，区分相同题目、共享题干模板和普通措辞。",
        "n-gram 只检出字面连续重叠，无法识别改写后的语义重复。",
        "日志中的 few-shot 示例不是完整训练集；即使命中，也只说明评测输入中有相似示例，"
        "不能证明 Qwen 在预训练时见过测试题。",
        "命中与未命中题的正确率仅供描述；样本少时不能据此推断污染带来的分数增益。",
        "", "## 阅读资料", "",
        "- [GPT-3 论文，附录 C](https://arxiv.org/pdf/2005.14165)",
        "- [Benchmark Data Contamination of Large Language Models: A Survey](https://arxiv.org/abs/2406.04244)",
        "", f"逐题明细：`{args.out}`。", "",
    ])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    manual_marker = "\n## 本次人工复核记录\n"
    manual_section = ""
    if args.report.exists():
        _, marker, tail = args.report.read_text(encoding="utf-8").partition(manual_marker)
        if marker:
            manual_section = marker + tail
    args.report.write_text("\n".join(lines) + manual_section, encoding="utf-8")

    print(f"测试题：{len(tests)}；不同 few-shot 示例：{len(fewshots)}")
    for label, data in (("测试集内部", within_test), ("测试题对 few-shot", against_fewshot)):
        print(
            f"{label}：命中 {data['test_questions_with_overlap']}/{len(tests)} 道，"
            f"题对 {data['question_pair_count']}，完全重复题对 {data['exact_duplicate_pair_count']}"
        )
    print(f"明细：{args.out}")
    print(f"报告：{args.report}")


if __name__ == "__main__":
    main()
