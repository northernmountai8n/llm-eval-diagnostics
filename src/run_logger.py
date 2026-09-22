"""
实验台账记录器 —— 可复现性的基础设施
================================================
把每次评测运行的完整参数追加到 runs/ledger.jsonl，并自动生成 RUNS.md 表格。

为什么要有这个：
    评测最容易被质疑的地方是"这个数字哪来的、还能不能重现"。
    靠手记参数一定会漏（漏一个 seed，结果就不可复现了）。
    所以用代码自动记录环境信息 —— 人不可靠，脚本可靠。

用法:
    # 记录一次运行（在你跑完 lm_eval 之后调用）
    python src/run_logger.py add \
        --model Qwen/Qwen2.5-1.5B --revision main \
        --task arc_easy --num-fewshot 0 --seed 42 --limit 200 \
        --result-file runs/day02_arc_easy/results.json \
        --cmd "lm_eval --model hf ..."

    # 重新生成 RUNS.md
    python src/run_logger.py render

    # 查看已记录的所有运行
    python src/run_logger.py list
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

LEDGER = Path("runs/ledger.jsonl")
RUNS_MD = Path("RUNS.md")


# ---------------------------------------------------------------- 环境探测

def _pkg_version(name: str) -> str:
    """取包版本；取不到就返回 unknown，不抛异常。"""
    try:
        from importlib.metadata import version

        return version(name)
    except Exception:
        return "unknown"


def collect_env() -> dict:
    """采集环境信息 —— 这些字段少了任何一个，结果都可能无法复现。"""
    env = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "torch": _pkg_version("torch"),
        "transformers": _pkg_version("transformers"),
        "lm_eval": _pkg_version("lm-eval") if _pkg_version("lm-eval") != "unknown" else _pkg_version("lm_eval"),
        "datasets": _pkg_version("datasets"),
        "cuda": "unknown",
        "gpu": "unknown",
    }
    try:
        import torch

        env["cuda"] = torch.version.cuda or "none"
        if torch.cuda.is_available():
            env["gpu"] = torch.cuda.get_device_name(0)
    except Exception:
        pass
    # 记录 git commit，方便追溯是哪版评测代码产出的结果
    try:
        env["git_commit"] = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except Exception:
        env["git_commit"] = "no-git"
    return env


def load_ledger() -> list[dict]:
    if not LEDGER.exists():
        return []
    out = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"[warn] 跳过损坏行: {line[:60]}", file=sys.stderr)
    return out


# ---------------------------------------------------------------- 命令

def cmd_add(args: argparse.Namespace) -> None:
    record = {
        "run_id": args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4],
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model": args.model,
        "revision": args.revision,
        "tasks": [t.strip() for t in args.task.split(",")],
        "num_fewshot": args.num_fewshot,
        "seed": args.seed,
        "limit": args.limit,
        "batch_size": args.batch_size,
        "dtype": args.dtype,
        "apply_chat_template": args.apply_chat_template,
        "result_file": args.result_file,
        "command": args.cmd,
        "notes": args.notes,
        "env": collect_env(),
    }
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"[ok] 已记录 run_id={record['run_id']}")
    render()


def cmd_render(_: argparse.Namespace) -> None:
    render()


def cmd_list(_: argparse.Namespace) -> None:
    for r in load_ledger():
        print(
            f"{r['run_id']}  {r['timestamp']}  {r['model']:<28} "
            f"{','.join(r['tasks']):<22} fs={r['num_fewshot']} seed={r['seed']} limit={r['limit']}"
        )


def render() -> None:
    records = load_ledger()
    lines = [
        "# RUNS.md — 实验台账",
        "",
        "> 本文件由 `src/run_logger.py` 自动生成，请勿手工编辑。",
        "> 每一次评测运行都记录完整参数与运行环境，保证结果可追溯、可复现。",
        "",
        f"共 **{len(records)}** 次运行。",
        "",
        "| run_id | 时间 | 模型 | revision | task | few-shot | seed | limit | batch | GPU | 结果路径 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in records:
        env = r.get("env", {})
        lines.append(
            "| {run_id} | {ts} | {model} | {rev} | {tasks} | {fs} | {seed} | {limit} | {bs} | {gpu} | {rf} |".format(
                run_id=r["run_id"],
                ts=r["timestamp"][:16].replace("T", " "),
                model=r["model"],
                rev=r.get("revision") or "-",
                tasks=", ".join(r["tasks"]),
                fs=r["num_fewshot"],
                seed=r["seed"],
                limit=r["limit"],
                bs=r["batch_size"],
                gpu=env.get("gpu", "-"),
                rf=r.get("result_file") or "-",
            )
        )

    lines += [
        "",
        "## 运行环境快照（最近一次）",
        "",
    ]
    if records:
        env = records[-1].get("env", {})
        lines.append("| 组件 | 版本 |")
        lines.append("|---|---|")
        for key in ("python", "torch", "transformers", "lm_eval", "datasets", "cuda", "gpu", "platform", "git_commit"):
            lines.append(f"| {key} | {env.get(key, '-')} |")
    lines += [
        "",
        "## 复现方式",
        "",
        "```bash",
        "# 任取上表中一行，复制其 command 字段即可复现该次评测",
        "# 完整命令与运行环境见 runs/ledger.jsonl",
        "```",
        "",
        "## 为什么记录这些字段",
        "",
        "- **revision**：HuggingFace 上的模型会被更新，只记模型名无法复现",
        "- **seed / few-shot / limit**：这三个参数直接影响分数，且 seed 影响 few-shot 示例采样",
        "- **框架与依赖版本**：评测框架的口径会随版本变化",
        "- **git_commit**：定位结果由哪版评测代码产出",
        "- **原始结果路径**：没有原始输出的分数是不可审计的",
    ]
    RUNS_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] 已生成 {RUNS_MD}（{len(records)} 次运行）")


def main() -> None:
    p = argparse.ArgumentParser(description="实验台账记录器")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="记录一次运行")
    a.add_argument("--model", required=True)
    a.add_argument("--revision", default=None)
    a.add_argument("--task", required=True, help="逗号分隔，如 arc_easy,hellaswag")
    a.add_argument("--num-fewshot", type=int, default=0)
    a.add_argument("--seed", type=int, default=42)
    a.add_argument("--limit", type=int, default=None)
    a.add_argument("--batch-size", type=int, default=None)
    a.add_argument("--dtype", default="bfloat16")
    a.add_argument("--apply-chat-template", action="store_true")
    a.add_argument("--result-file", default=None)
    a.add_argument("--cmd", default=None, help="完整命令行（强烈建议填）")
    a.add_argument("--notes", default=None)
    a.add_argument("--run-id", default=None)
    a.set_defaults(func=cmd_add)

    r = sub.add_parser("render", help="重新生成 RUNS.md")
    r.set_defaults(func=cmd_render)

    l = sub.add_parser("list", help="列出所有运行")
    l.set_defaults(func=cmd_list)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
