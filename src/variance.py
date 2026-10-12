"""Summarize few-shot seed variation in saved lm-eval runs.

Usage: python src/variance.py --root runs/variance --out reports/17-variance.md --plot
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from xml.sax.saxutils import escape


METRICS = ("acc", "acc_norm")


def binom_stderr(p: float, n: int) -> float:
    """lm-eval's item-level sample standard error for a binary accuracy."""
    return math.sqrt(p * (1 - p) / (n - 1)) if n > 1 else float("nan")


def read_runs(root: Path) -> tuple[dict, set[str]]:
    """Read one result per (task, limit, metric, seed), verifying duplicates."""
    grouped = defaultdict(dict)
    duplicates = set()
    for path in sorted(root.rglob("results_*.json")):
        relative = path.relative_to(root)
        task = relative.parts[0]
        match = re.fullmatch(r"seed(\d+)_limit(\d+)", relative.parts[1]) if len(relative.parts) > 1 else None
        if not match:
            raise ValueError(f"Unexpected result path: {path}")
        seed, limit = map(int, match.groups())
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        config = data["config"]
        scores = data["results"][task]
        effective = int(data["n-samples"][task]["effective"])
        if int(config["fewshot_seed"]) != seed or int(config["limit"]) != limit or effective != limit:
            raise ValueError(f"Path and result metadata disagree: {path}")

        identity = (
            config["model"],
            json.dumps(config["model_args"], sort_keys=True),
            int(data["n-shot"][task]),
            int(config["random_seed"]),
            int(config["numpy_seed"]),
            int(config["torch_seed"]),
            config["device"],
            str(config["batch_size"]),
            data["lm_eval_version"],
        )
        for metric in METRICS:
            value_key = f"{metric},none" if f"{metric},none" in scores else metric
            stderr_key = f"{metric}_stderr,none" if f"{metric}_stderr,none" in scores else f"{metric}_stderr"
            if value_key not in scores:
                continue
            record = {
                "value": float(scores[value_key]),
                "stderr": float(scores[stderr_key]) if scores.get(stderr_key) is not None else None,
                "identity": identity,
                "path": str(path),
            }
            key = (task, limit, metric)
            prior = grouped[key].get(seed)
            if prior is not None:
                if (prior["value"], prior["stderr"], prior["identity"]) != (
                    record["value"], record["stderr"], record["identity"]
                ):
                    raise ValueError(f"Conflicting results for {key}, seed={seed}: {prior['path']} and {path}")
                duplicates.add(str(path))
                continue
            grouped[key][seed] = record

    if not grouped:
        raise ValueError(f"No results_*.json under {root}")
    for key, by_seed in grouped.items():
        identities = {item["identity"] for item in by_seed.values()}
        if len(identities) != 1:
            raise ValueError(f"Runs use different model/evaluation settings: {key}")
    return grouped, duplicates


def analyze(grouped: dict) -> dict:
    stats = {}
    for key, by_seed in grouped.items():
        if sorted(by_seed) != [1, 2, 3, 4, 5]:
            print(f"[skip] Incomplete seed set for {key}: {sorted(by_seed)}")
            continue
        seeds = sorted(by_seed)
        values = [by_seed[seed]["value"] for seed in seeds]
        stderrs = [by_seed[seed]["stderr"] for seed in seeds if by_seed[seed]["stderr"] is not None]
        stats[key] = {
            "seeds": seeds,
            "values": values,
            "mean": statistics.fmean(values),
            "seed_sd": statistics.stdev(values) if len(values) > 1 else float("nan"),
            "low": min(values),
            "high": max(values),
            "range": max(values) - min(values),
            "item_stderr_mean": statistics.fmean(stderrs) if stderrs else None,
            "identity": by_seed[seeds[0]]["identity"],
        }
    return stats


def subject_mix(root: Path, task: str, limit: int) -> str | None:
    """Describe subjects in the first seed's fixed MMLU test prefix."""
    folder = root / task / f"seed1_limit{limit}"
    samples = sorted(folder.rglob(f"samples_{task}_*.jsonl"))
    if not samples:
        return None
    counts = Counter()
    with samples[-1].open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            counts[row["doc"].get("subject", "unknown")] += 1
    return "、".join(f"{subject} {count}" for subject, count in counts.items())


def render(stats: dict, duplicates: set[str], root: Path) -> str:
    keys = sorted(stats, key=lambda k: (k[0], k[2], k[1]))
    first = stats[keys[0]]["identity"]
    model_args = json.loads(first[1])
    lines = [
        "# Day 17｜多任务 few-shot seed 波动",
        "",
        f"- 模型：`{model_args.get('pretrained')}`，revision `{model_args.get('revision')}`，dtype `{model_args.get('dtype')}`。",
        f"- 任务：{', '.join(sorted({key[0] for key in keys}))}；每个题量使用该任务的前 n 道评测题，5-shot；Python/NumPy/PyTorch seed 固定为 `{first[3]}/{first[4]}/{first[5]}`，只改变 few-shot seed。",
        f"- `lm-eval` 版本：`{first[8]}`；原始结果：`{root}`。",
        "- 同一题量内五次使用相同测试题。不同题量的题目集合不同，均值变化不能只归因于题量。",
        "- `custom_mmlu_all_random5` 是自定义实验：从 `cais/mmlu` 的 `all/validation` 随机选 5 个示例，评估 `all/test`；它与内置 MMLU 的固定 `dev` 示例口径不同，分数不能直接对拍。",
        "",
        "## 汇总",
        "",
        "| 任务 | 指标 | 题量 | seed 数 | 平均分 | seed 间标准差 | 最低～最高 | 极差 | 单次 stderr 均值 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for task, limit, metric in keys:
        s = stats[(task, limit, metric)]
        stderr = f"{s['item_stderr_mean']:.4f}" if s["item_stderr_mean"] is not None else "—"
        lines.append(
            f"| `{task}` | `{metric}` | {limit} | {len(s['seeds'])} | {s['mean']:.4f} | "
            f"{s['seed_sd']:.4f} | {s['low']:.4f}～{s['high']:.4f} | "
            f"{s['range']:.4f} | {stderr} |"
        )
    lines += ["", "![Five-seed score variation](figures/variance.svg)", "", "各面板为突出 seed 波动分别调整纵轴范围；跨任务比较请看上表的数值。", "", "## 观察", ""]
    for task in sorted({key[0] for key in keys}):
        for metric in METRICS:
            metric_keys = sorted((key for key in keys if key[0] == task and key[2] == metric), key=lambda key: key[1])
            if not metric_keys:
                continue
            items = [f"n={limit}: {stats[(task, limit, metric)]['seed_sd'] * 100:.2f} 个百分点" for _, limit, _ in metric_keys]
            sds = [stats[key]["seed_sd"] for key in metric_keys]
            if len(sds) < 2:
                trend = "只有一个题量，暂不判断趋势"
            else:
                trend = "这几组观测值依次下降" if all(a > b for a, b in zip(sds, sds[1:])) else "这几组观测值并未依次下降"
            lines.append(f"- `{task}` / `{metric}` 的 seed 间标准差：{'；'.join(items)}；{trend}。")
    mmlu_task = "custom_mmlu_all_random5"
    mmlu_limits = sorted(limit for task, limit, metric in keys if task == mmlu_task and metric == "acc")
    if mmlu_limits:
        lines += ["", "## MMLU 测试题学科构成", ""]
        for limit in mmlu_limits:
            mix = subject_mix(root, mmlu_task, limit)
            if mix:
                lines.append(f"- n={limit}：{mix}。")
        lines += [
            "",
            "MMLU 的 `all/test` 前缀按学科聚集；扩大 `--limit` 会加入新学科。三档平均分变化同时反映题目构成变化，不能解释成题量本身提高了模型能力。",
        ]
    lines += ["", "## 每个 seed 的原始分数", ""]
    for task, limit, metric in keys:
        s = stats[(task, limit, metric)]
        pairs = "、".join(f"{seed}: {value:.4f}" for seed, value in zip(s["seeds"], s["values"]))
        lines.append(f"- `{task}` / `{metric}` / n={limit}：{pairs}。")
    lines += [
        "",
        "## 如何解释",
        "",
        "- `seed 间标准差`描述固定题目和推理配置时，更换 5-shot 示例带来的五次分数波动；只有 5 个 seed，估计仍较粗。",
        "- `单次 stderr`由每次运行的逐题 0/1 正误估计，描述题目层面的标准误。两者对应不同的变化来源，不能直接相除来证明“额外方差”。",
        "- 200、500、1000 题采用测试集前缀，不能据此推断随机抽题时分数会如何波动。若要估计抽题不确定性，需要单独做随机抽样或逐题 bootstrap。",
        "- 某个题量下观察到的最高与最低分数差，也不能直接当作两个模型分数差异显著性的门槛；比较模型需要相同题目和逐题配对分析。",
        "- 本实验使用 `--limit`，结果只代表各任务选定的前 n 道题，不是完整 benchmark 分数。",
    ]
    if duplicates:
        lines += ["", f"重复结果文件：{len(duplicates)} 份；相同 seed 的配置和分数一致，汇总时只计一次。"]
    return "\n".join(lines) + "\n"


def plot(stats: dict, out: Path) -> None:
    tasks = sorted({task for task, _, _ in stats})
    width, height = 1100, 80 + len(tasks) * 290
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        '<title>Score variation across five few-shot seeds</title>',
        '<rect width="100%" height="100%" fill="#fff"/>',
        '<text x="70" y="34" font-family="Arial,sans-serif" font-size="22" font-weight="bold" fill="#14263b">Score variation across five few-shot seeds</text>',
        '<text x="70" y="55" font-family="Arial,sans-serif" font-size="13" fill="#50647a">Dots: individual seeds; line and bars: mean ± seed standard deviation; each panel has its own y-axis scale</text>',
    ]
    for row, task in enumerate(tasks):
        for col, metric in enumerate(METRICS):
            sizes = sorted(limit for t, limit, m in stats if t == task and m == metric)
            if not sizes:
                continue
            left, top, chart_w, chart_h = 85 + col * 535, 115 + row * 290, 410, 172
            bottom = top + chart_h
            all_values = [v for limit in sizes for v in stats[(task, limit, metric)]["values"]]
            low = max(0.0, math.floor((min(all_values) - 0.04) * 20) / 20)
            high = min(1.0, math.ceil((max(all_values) + 0.04) * 20) / 20)
            if high <= low:
                high = min(1.0, low + 0.05)
            min_size, max_size = min(sizes), max(sizes)
            x_at = lambda limit: left + (limit - min_size) / (max_size - min_size) * chart_w if max_size > min_size else left + chart_w / 2
            y_at = lambda value: bottom - (value - low) / (high - low) * chart_h
            parts.append(f'<text x="{left}" y="{top - 18}" font-family="Arial,sans-serif" font-size="15" font-weight="bold" fill="#14263b">{escape(task)} / {metric}</text>')
            for i in range(5):
                value = low + (high - low) * i / 4
                y = y_at(value)
                parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_w}" y2="{y:.1f}" stroke="#e4ebf2"/>')
                parts.append(f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" font-family="Arial,sans-serif" font-size="11" fill="#5c6d80">{value:.2f}</text>')
            for limit in sizes:
                x = x_at(limit)
                parts.append(f'<text x="{x:.1f}" y="{bottom + 21}" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#5c6d80">{limit}</text>')
                s = stats[(task, limit, metric)]
                for index, value in enumerate(s["values"]):
                    dot_x = x + (index - 2) * 4
                    parts.append(f'<circle cx="{dot_x:.1f}" cy="{y_at(value):.1f}" r="3.5" fill="#2b7a9b" opacity=".75"/>')
                upper, lower = y_at(s["mean"] + s["seed_sd"]), y_at(s["mean"] - s["seed_sd"])
                parts.append(f'<line x1="{x:.1f}" y1="{upper:.1f}" x2="{x:.1f}" y2="{lower:.1f}" stroke="#1e2f43" stroke-width="1.5"/>')
                for cap_y in (upper, lower):
                    parts.append(f'<line x1="{x - 5:.1f}" y1="{cap_y:.1f}" x2="{x + 5:.1f}" y2="{cap_y:.1f}" stroke="#1e2f43" stroke-width="1.5"/>')
            points = " ".join(f'{x_at(limit):.1f},{y_at(stats[(task, limit, metric)]["mean"]):.1f}' for limit in sizes)
            parts.append(f'<polyline points="{points}" fill="none" stroke="#1e2f43" stroke-width="1.5"/>')
            for limit in sizes:
                s = stats[(task, limit, metric)]
                parts.append(f'<circle cx="{x_at(limit):.1f}" cy="{y_at(s["mean"]):.1f}" r="4.5" fill="#1e2f43"/>')
            parts.append(f'<text x="{left + chart_w / 2:.1f}" y="{bottom + 40}" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#5c6d80">Number of test questions</text>')
    parts.append('</svg>')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize few-shot seed variation")
    parser.add_argument("--root", type=Path, default=Path("runs/variance"))
    parser.add_argument("--out", type=Path, default=Path("reports/17-variance.md"))
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--plot-out", type=Path, default=Path("reports/figures/variance.svg"))
    args = parser.parse_args()

    grouped, duplicates = read_runs(args.root)
    stats = analyze(grouped)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(stats, duplicates, args.root), encoding="utf-8")
    for (task, limit, metric), s in sorted(stats.items()):
        print(f"{task} n={limit} {metric}: mean={s['mean']:.4f}, seed_sd={s['seed_sd']:.4f}, range={s['range']:.4f}")
    print(f"Report: {args.out}; duplicate result files ignored: {len(duplicates)}")
    if args.plot:
        plot(stats, args.plot_out)
        print(f"Figure: {args.plot_out}")


if __name__ == "__main__":
    main()
