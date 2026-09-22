"""
方差实验分析 —— 项目实验四（⭐ 全项目最有价值的产出）
================================================
读取多次重复评测的结果，量化"仅改随机种子时的分数波动"，并与理论标准误对比。

用法:
    # 1. 结果目录约定：runs/variance/<task>/seed<seed>_limit<limit>/results.json
    python src/variance.py --root runs/variance --out reports/04_variance.md
    # 2. 生成图（需要 matplotlib）
    python src/variance.py --root runs/variance --plot

设计说明:
    评测分数是一个随机变量，不是确定值。这个脚本的目的就是让这件事可见、可量化。
    面试时这张图就是你的核心证据。
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------- 结果解析

def find_result_files(root: Path) -> list[Path]:
    """递归找出所有 lm-eval 的结果 JSON。"""
    return sorted(p for p in root.rglob("*.json") if "results" in p.name or p.name.endswith(".json"))


def parse_meta_from_path(path: Path, root: Path) -> dict:
    """从目录/文件名里解析 task / seed / limit。

    约定目录结构: runs/variance/<task>/seed<seed>_limit<limit>/results.json
    这个约定由 scripts/run_variance.sh 保证。
    """
    rel = path.relative_to(root)
    parts = rel.parts
    meta: dict = {"task": None, "seed": None, "limit": None}

    if len(parts) >= 1:
        meta["task"] = parts[0]
    blob = str(rel)
    m = re.search(r"seed[_-]?(\d+)", blob)
    if m:
        meta["seed"] = int(m.group(1))
    m = re.search(r"limit[_-]?(\d+)", blob)
    if m:
        meta["limit"] = int(m.group(1))
    return meta


def extract_score(data: dict, task: str | None) -> dict | None:
    """从 lm-eval 结果 JSON 里取出分数与标准误。

    lm-eval 的结果结构大致是:
        {"results": {"<task>": {"acc": 0.7, "acc_stderr": 0.02, "acc_norm": ..., ...}}}
    不同版本字段名略有差异，所以这里做多路兼容 —— 包括顶层直接是 {"<task>": {...}}
    以及有人用自己的脚本产出的扁平结构。
    """
    results = data.get("results")
    if not isinstance(results, dict) or not results:
        # 兼容：顶层直接是 {task: {metric: value}} 的自制结果
        if all(isinstance(v, dict) for v in data.values()) and data:
            results = data
        else:
            return None

    key = task if (task and task in results) else next(iter(results))
    scores = results[key]
    if not isinstance(scores, dict):
        return None

    # 优先 acc_norm（对选项长度归一化），退到 acc
    for metric in ("acc_norm", "acc", "exact_match", "f1"):
        if metric in scores and isinstance(scores[metric], (int, float)):
            return {
                "task_key": key,
                "metric": metric,
                "value": float(scores[metric]),
                "stderr_reported": _as_float(scores.get(f"{metric}_stderr")),
                "n_samples": _as_float(scores.get("samples")) or _as_float(scores.get("n_samples")),
            }
    return None


def _as_float(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- 统计

def binom_stderr(p: float, n: int) -> float:
    """二项分布的标准误：sqrt(p(1-p)/n)。

    这是"仅由样本量带来的"理论误差下限。
    如果实测标准差明显高于它，说明还有别的方差来源（seed、few-shot 采样等）。
    """
    if n <= 0:
        return float("nan")
    return math.sqrt(max(p * (1 - p), 0) / n)


def ci95(mean: float, stderr: float) -> tuple[float, float]:
    """95% 置信区间（正态近似，1.96σ）。"""
    return mean - 1.96 * stderr, mean + 1.96 * stderr


# ---------------------------------------------------------------- 主流程

def collect(root: Path) -> dict:
    """收集所有结果，按 (task, limit) 分组。"""
    groups: dict[tuple[str, int | None], list[dict]] = defaultdict(list)
    skipped = 0

    for path in find_result_files(root):
        meta = parse_meta_from_path(path, root)
        try:
            # utf-8-sig 能同时处理带 BOM 和不带 BOM 的文件。
            # 这不是洁癖：Windows 工具链（PowerShell、记事本、Excel 导出）经常写 BOM，
            # 而 json.loads 遇到 BOM 会直接失败。中文数据集的编码问题同源。
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            skipped += 1
            print(f"[warn] 解析失败 {path}: {e}")
            continue
        score = extract_score(data, meta["task"])
        if not score:
            skipped += 1
            continue
        score.update({"seed": meta["seed"], "limit": meta["limit"], "path": str(path)})
        groups[(score["task_key"], meta["limit"])].append(score)

    if skipped:
        print(f"[warn] 跳过 {skipped} 个无法解析的文件")
    return groups


def analyze(groups: dict) -> dict:
    """对每个 (task, limit) 组计算统计量。"""
    out: dict = {}
    for (task, limit), runs in groups.items():
        values = [r["value"] for r in runs]
        if not values:
            continue
        mean = statistics.fmean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0.0
        n_seed = len(values)

        # 用声明样本量算理论标准误；没有就用 limit 兜底
        n_samples = next((int(r["n_samples"]) for r in runs if r.get("n_samples")), limit or 0)
        theo = binom_stderr(mean, n_samples) if n_samples else float("nan")

        # 框架自己报的标准误，取平均作参考
        reported = [r["stderr_reported"] for r in runs if r.get("stderr_reported")]
        rep_mean = statistics.fmean(reported) if reported else None

        lo, hi = ci95(mean, std / math.sqrt(n_seed) if n_seed > 1 else std) if std else (mean, mean)

        out[(task, limit)] = {
            "task": task,
            "limit": limit,
            "n_seed": n_seed,
            "n_samples": n_samples,
            "metric": runs[0]["metric"],
            "mean": mean,
            "std": std,
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values),
            "values": values,
            "seeds": [r["seed"] for r in runs],
            "theoretical_stderr": theo,
            "reported_stderr_mean": rep_mean,
            "ci95_low": lo,
            "ci95_high": hi,
        }
    return out


def render(stats: dict, root: Path) -> str:
    lines = [
        "# 评测方差分析",
        "",
        "> 由 `src/variance.py` 生成。",
        "",
        "## 核心问题",
        "",
        "同一个模型、同一个 benchmark，**只改随机种子**，分数会变多少？",
        "如果这个波动大于模型之间的差距，那么榜单上小差距的排名就是不可信的。",
        "",
        "## 结果",
        "",
        "| task | 样本量 | seed 数 | 均值 | 标准差 | 极差(min~max) | 理论标准误 | 框架报告 stderr |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for key in sorted(stats, key=lambda k: (str(k[0]), k[1] or 0)):
        s = stats[key]
        theo = f"{s['theoretical_stderr']:.4f}" if s["theoretical_stderr"] == s["theoretical_stderr"] else "-"
        rep = f"{s['reported_stderr_mean']:.4f}" if s["reported_stderr_mean"] else "-"
        lines.append(
            f"| {s['task']} | {s['limit'] or 'full'} | {s['n_seed']} | "
            f"{s['mean']:.4f} | {s['std']:.4f} | "
            f"{s['min']:.4f}~{s['max']:.4f} ({s['range']:.4f}) | {theo} | {rep} |"
        )

    lines += ["", "## 逐组明细", ""]
    for key in sorted(stats, key=lambda k: (str(k[0]), k[1] or 0)):
        s = stats[key]
        lines.append(f"### {s['task']} / limit={s['limit']}")
        lines.append("")
        lines.append(f"- 指标：`{s['metric']}`，样本量 {s['n_samples']}，重复 {s['n_seed']} 次")
        lines.append(f"- 各次分数：`{[round(v, 4) for v in s['values']]}`（seed={s['seeds']}）")
        lines.append(f"- 均值 {s['mean']:.4f}，标准差 {s['std']:.4f}，**极差 {s['range']:.4f}**")
        if s["theoretical_stderr"] == s["theoretical_stderr"]:
            ratio = s["std"] / s["theoretical_stderr"] if s["theoretical_stderr"] else float("nan")
            lines.append(
                f"- 理论标准误（仅样本量）{s['theoretical_stderr']:.4f}，"
                f"实测标准差 / 理论 = **{ratio:.2f}×**"
            )
            if ratio > 1.2:
                lines.append(
                    "  - ⭐ 实测方差高于理论值 → 除样本量外还有额外方差来源"
                    "（seed 影响 few-shot 示例采样、数据顺序等）"
                )
        lines.append("")

    lines += [
        "## 结论怎么用（写进 README 的话术）",
        "",
        "```",
        "在 n=<样本量> 时，同模型同 task 仅改 seed，分数极差达 <极差>。",
        "这意味着小于该幅度的模型差距在统计上不可区分。",
        "```",
        "",
        "## 局限",
        "",
        "- 重复次数偏少（seed 数较少），方差估计本身的置信区间较宽，",
        "  因此**定性结论（方差不可忽略）比定量结论（方差具体是多少）更可靠**。",
        "- 实验在 ~3B 规模模型上完成，未验证更大模型；但方差来源与模型规模无直接关系。",
        "",
        f"> 数据源：`{root}`",
    ]
    return "\n".join(lines)


def plot(stats: dict, out: Path) -> None:
    """画方差图 —— 面试时这张图最有说服力。"""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[skip] 未安装 matplotlib，跳过绘图：pip install matplotlib")
        return

    tasks = sorted({s["task"] for s in stats.values()})
    if not tasks:
        print("[skip] 无数据可画")
        return

    fig, axes = plt.subplots(1, len(tasks), figsize=(5 * len(tasks), 4.2), squeeze=False)
    for ax, task in zip(axes[0], tasks):
        rows = sorted(
            (s for s in stats.values() if s["task"] == task),
            key=lambda s: s["limit"] or 0,
        )
        xs = [s["limit"] or 0 for s in rows]
        means = [s["mean"] for s in rows]
        stds = [s["std"] for s in rows]

        # 每个 seed 的实际分数（散点）—— 让"波动"肉眼可见
        for x, s in zip(xs, rows):
            ax.scatter([x] * len(s["values"]), s["values"], alpha=0.65, s=28, zorder=3)

        ax.errorbar(xs, means, yerr=stds, marker="o", capsize=5,
                    linewidth=1.8, color="black", zorder=4, label="mean ± 1σ")
        ax.set_title(task)
        ax.set_xlabel("num samples (--limit)")
        ax.set_ylabel("score")
        ax.grid(alpha=0.3)

        # 标注极差，直接把结论写在图上
        for x, s in zip(xs, rows):
            ax.annotate(f"range {s['range']:.3f}", (x, s["max"]),
                        textcoords="offset points", xytext=(0, 8),
                        ha="center", fontsize=8)

    axes[0][0].legend(fontsize=8)
    fig.suptitle("Score variation across seeds (same model, same task)", fontsize=11)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=160)
    print(f"[ok] 已保存图 {out}")


def main() -> None:
    p = argparse.ArgumentParser(description="评测方差分析")
    p.add_argument("--root", default="runs/variance", help="结果目录")
    p.add_argument("--out", default="reports/04_variance.md")
    p.add_argument("--plot", action="store_true", help="生成方差图")
    p.add_argument("--plot-out", default="reports/figures/variance.png")
    args = p.parse_args()

    root = Path(args.root)
    if not root.exists():
        raise SystemExit(
            f"目录不存在：{root}\n"
            "请先运行方差实验，目录约定：runs/variance/<task>/seed<seed>_limit<limit>/"
        )

    groups = collect(root)
    if not groups:
        raise SystemExit(f"在 {root} 下没找到可解析的结果 JSON。检查目录结构是否符合约定。")

    stats = analyze(groups)
    report = render(stats, root)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"[ok] 已生成 {out}")

    # 终端速览
    print()
    print(f"{'task':<14}{'limit':>7}{'seeds':>7}{'mean':>9}{'std':>9}{'range':>9}")
    for s in sorted(stats.values(), key=lambda s: (s["task"], s["limit"] or 0)):
        print(
            f"{s['task']:<14}{s['limit'] or 0:>7}{s['n_seed']:>7}"
            f"{s['mean']:>9.4f}{s['std']:>9.4f}{s['range']:>9.4f}"
        )

    if args.plot:
        plot(stats, Path(args.plot_out))


if __name__ == "__main__":
    main()
