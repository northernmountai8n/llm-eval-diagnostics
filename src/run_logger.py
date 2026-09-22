"""
实验台账记录器 —— 可复现性的基础设施
================================================
把每次评测运行的完整参数追加到 runs/ledger.jsonl，并自动生成 RUNS.md。

为什么要有这个：
    评测最容易被质疑的地方是"这个数字哪来的、还能不能重现"。
    靠手记参数一定会漏（漏一个 seed，结果就不可复现了）。
    所以用代码自动记录环境信息 —— 人不可靠，脚本可靠。

用法:
    # 记录一次运行（在你跑完 lm_eval 之后调用）
    python src/run_logger.py add \
        --model Qwen/Qwen2.5-1.5B --revision main \
        --resolved-revision 8faed761d45a263340a0528343f099c05c9a4323 \
        --task arc_easy --num-fewshot 0 --limit 100 \
        --result-file runs/day02_limit100/Qwen__Qwen2.5-1.5B/results_2026-09-22T21-23-48.058308.json \
        --cmd "lm_eval run --model hf ..."

    # 重新生成 RUNS.md
    python src/run_logger.py render

    # 查看已记录的所有运行
    python src/run_logger.py list

自动提取（2026-09-22 加入，实测标定）:
    只要给了 --result-file，脚本会从 lm-eval 的结果 JSON 里读出**真实的运行时间**、
    **框架实际使用的 batch_size** 和**四个随机种子**。

    为什么必须自动提取：
      - 时间：盖当前时间在补录历史运行时会全部变成补录时刻，时间维度失效。
        lm-eval 结果 JSON 顶层有 `date`（评测开始时的 unix 时间戳），那才是真值。
      - batch_size：命令行不传时框架会自己选（实测 limit=100 时选了 1）。
        台账记 None 等于"未指定"，而实际是 1 —— 两者不是一回事。
      - seed：lm-eval 用四个独立种子（python / numpy / torch / fewshot，默认
        0/1234/1234/1234），单填一个整数必然丢信息。
    能用机器读出来的，就不要靠人填。
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

SEED_KEYS = ("seed", "numpy_seed", "torch_seed", "fewshot_seed")


# ---------------------------------------------------------------- 环境探测

def _pkg_version(name: str) -> str:
    """取包版本；取不到就返回 unknown，不抛异常。"""
    try:
        from importlib.metadata import version

        return version(name)
    except Exception:
        return "unknown"


def _platform_str() -> str:
    """平台字符串，并修正 Python 对 Windows 11 的误报。

    platform.platform() 至今仍把 Windows 11 报成 "Windows-10-10.0.26200-SP0"
    （历史遗留行为）。Windows 11 的 build 号 >= 22000，据此纠正。
    别小看这一栏 —— 面试报环境时写错系统版本会显得没核对过。
    """
    p = platform.platform()
    if sys.platform == "win32":
        try:
            if sys.getwindowsversion().build >= 22000:
                p = p.replace("Windows-10-", "Windows-11-", 1)
        except Exception:
            pass
    return p


def collect_env() -> dict:
    """采集环境信息 —— 这些字段少了任何一个，结果都可能无法复现。"""
    env = {
        "python": platform.python_version(),
        "platform": _platform_str(),
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


def probe_result_file(path: str | None) -> dict:
    """从 lm-eval 的结果 JSON 里读出"机器知道、但人不一定填对"的字段。

    任何一步失败都只跳过提取、不影响记录 —— 宁可少字段，不能丢记录。
    """
    info: dict = {}
    if not path:
        return info
    p = Path(path)
    if not p.exists():
        print(f"[warn] 结果文件不存在，跳过自动提取: {path}", file=sys.stderr)
        return info
    try:
        # utf-8-sig：同时兼容带 BOM 和不带 BOM 的文件
        # （Windows 工具链经常写 BOM，而 json.loads 遇到 BOM 会直接失败）
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception as e:
        print(f"[warn] 结果文件无法解析（{type(e).__name__}: {e}），跳过自动提取", file=sys.stderr)
        return info

    cfg = data.get("config") or {}

    ts = data.get("date")
    if isinstance(ts, (int, float)):
        info["run_at"] = datetime.fromtimestamp(ts).isoformat(timespec="seconds")

    if cfg.get("batch_size") is not None:
        info["batch_size"] = cfg["batch_size"]

    seeds = {k: cfg[k] for k in SEED_KEYS if cfg.get(k) is not None}
    if seeds:
        info["seeds"] = seeds

    if cfg.get("model_revision"):
        info["model_revision"] = cfg["model_revision"]

    # 运行当时的版本信息。lm-eval 自己会把这些写进结果 JSON：
    #   git_hash             = 运行时 CWD 的 git commit（git describe --always）
    #   lm_eval_version      = 框架版本
    #   transformers_version = 推理库版本
    # 这些比"登记时刻采集"的可信 —— 尤其 git_commit：补录历史运行时，
    # collect_env() 拿到的是当时的 HEAD，而不是产出这个结果的代码版本。
    for src_key, env_key in (
        ("git_hash", "git_commit"),
        ("lm_eval_version", "lm_eval"),
        ("transformers_version", "transformers"),
    ):
        if data.get(src_key):
            info[env_key] = str(data[src_key])

    return info


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
    probed = probe_result_file(args.result_file)

    # 运行时间：优先用结果文件里的真实时间（补录历史运行时这点是关键）
    run_at = probed.get("run_at") or datetime.now().isoformat(timespec="seconds")

    # batch_size：命令行没给，就用框架实际用的值
    batch_size = args.batch_size if args.batch_size is not None else probed.get("batch_size")

    # seed：命令行没给，就用结果文件里的 few-shot 种子（few-shot 采样由它决定）
    seed = args.seed if args.seed is not None else (probed.get("seeds") or {}).get("fewshot_seed")

    env = collect_env()
    # 结果文件里记录的是**运行当时**的版本，优先采用（见 probe_result_file 的说明）
    runtime_env = {k: probed[k] for k in ("git_commit", "lm_eval", "transformers") if probed.get(k)}
    env.update(runtime_env)

    record = {
        "run_id": args.run_id or datetime.fromisoformat(run_at).strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4],
        "timestamp": run_at,
        "model": args.model,
        "revision": args.revision,
        # 解析后的权重指纹（HF 上的 commit hash）。main 是浮动引用，
        # 这里记的是"截至运行当日，main 实际指向哪个 commit"。
        "revision_resolved": args.resolved_revision,
        "tasks": [t.strip() for t in args.task.split(",")],
        "num_fewshot": args.num_fewshot,
        "seed": seed,
        "seeds": probed.get("seeds"),
        "limit": args.limit,
        "batch_size": batch_size,
        "dtype": args.dtype,
        "apply_chat_template": args.apply_chat_template,
        "result_file": args.result_file,
        "command": args.cmd,
        "notes": args.notes,
        "env": env,
        "env_from_result_file": sorted(runtime_env),
        "probed": probed or None,
    }
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    if probed:
        got = ", ".join(k for k in ("run_at", "batch_size", "seeds") if k in probed)
        print(f"[ok] 已记录 run_id={record['run_id']}（自动提取: {got}）")
    else:
        print(f"[ok] 已记录 run_id={record['run_id']}")
    render()


def cmd_render(_: argparse.Namespace) -> None:
    render()


def cmd_list(_: argparse.Namespace) -> None:
    for r in load_ledger():
        print(
            f"{r['run_id']}  {r['timestamp']}  {r['model']:<28} "
            f"{','.join(r['tasks']):<22} fs={r['num_fewshot']} seed={r['seed']} "
            f"limit={r['limit']} batch={r['batch_size']}"
        )


def _cell(v) -> str:
    """表格单元格：None / 空串统一显示为 '-'，避免出现 'None' 这种噪音。"""
    if v is None or v == "":
        return "-"
    return str(v)


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
        "## 运行总表",
        "",
        "| # | run_id | 运行时间 | 模型 | 权重版本 | task | few-shot | seed | limit | batch | GPU | 结果路径 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(records, 1):
        env = r.get("env", {})
        lines.append(
            "| {i} | {run_id} | {ts} | {model} | {rev} | {tasks} | {fs} | {seed} | {limit} | {bs} | {gpu} | {rf} |".format(
                i=i,
                run_id=r["run_id"],
                ts=r["timestamp"][:16].replace("T", " "),
                model=r["model"],
                rev=_cell(r.get("revision")),
                tasks=", ".join(r["tasks"]),
                fs=r["num_fewshot"],
                seed=_cell(r.get("seed")),
                limit=_cell(r.get("limit")),
                bs=_cell(r.get("batch_size")),
                gpu=_cell(env.get("gpu")),
                rf=_cell(r.get("result_file")),
            )
        )

    lines += [
        "",
        "> `seed` 列填的是 **few-shot 采样种子**（0-shot 任务下不影响分数，但 few-shot 任务下它会改变示例抽取）。",
        "> lm-eval 实际使用四个独立种子，完整取值见下方「复现命令」。",
        "",
        "## 复现命令",
        "",
        "每次运行的完整命令行与运行参数如下，**复制即用**。",
        "",
    ]
    for i, r in enumerate(records, 1):
        parsed = {k: v for k, v in (r.get("seeds") or {}).items() if v is not None}
        lines.append(f"### {i}. `{r['run_id']}`")
        lines.append("")
        lines.append(f"- **运行时间**：{r['timestamp'].replace('T', ' ')}")
        lines.append(f"- **模型**：`{r['model']}` @ `{_cell(r.get('revision'))}`")
        if r.get("revision_resolved"):
            lines.append(
                f"- **权重指纹**：`{r['revision_resolved']}`"
                "（`main` 是浮动引用；这是截至运行当日 `main` 指向的 commit）"
            )
        if parsed:
            lines.append("- **随机种子**：" + ", ".join(f"`{k}={v}`" for k, v in parsed.items()))
        lines.append(f"- **batch size**：{_cell(r.get('batch_size'))}")
        if r.get("notes"):
            lines.append(f"- **备注**：{r['notes']}")
        lines.append(f"- **原始结果**：`{_cell(r.get('result_file'))}`")
        lines.append("")
        if r.get("command"):
            lines.append("```bash")
            lines.append(r["command"])
            lines.append("```")
        else:
            lines.append("> ⚠️ 本次运行未记录 `command`，无法逐字复现。")
        lines.append("")

    lines += [
        "## 运行环境快照（最近一次）",
        "",
    ]
    if records:
        env = records[-1].get("env", {})
        lines.append("| 组件 | 版本 |")
        lines.append("|---|---|")
        for key in ("python", "torch", "transformers", "lm_eval", "datasets", "cuda", "gpu", "platform", "git_commit"):
            lines.append(f"| {key} | {_cell(env.get(key))} |")
        src = records[-1].get("env_from_result_file") or []
        if src:
            lines.append("")
            lines.append(
                "> 其中 "
                + "、".join(f"`{k}`" for k in src)
                + " 取自 lm-eval 结果文件（**运行当时**的值），其余为登记时刻采集。"
            )
    lines += [
        "",
        "## 为什么记录这些字段",
        "",
        "- **权重版本 / 权重指纹**：HuggingFace 上的模型会被更新，只记模型名无法复现；"
        "`main` 是浮动引用，所以额外记录它当日指向的 commit hash",
        "- **seed / few-shot / limit**：这三个参数直接影响分数，且 seed 影响 few-shot 示例采样",
        "- **batch size**：batch shape 会改变 GPU kernel 的选择，进而让 logits 出现 ~1e-6 级差异，"
        "在近乎并列的选项上足以翻转 argmax —— 所以它是「口径」的一部分，不是性能开关",
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
    a.add_argument("--revision", default=None, help="HF 上的 revision，如 main 或某个 tag")
    a.add_argument("--resolved-revision", default=None, help="该 revision 解析后的 commit hash（权重指纹）")
    a.add_argument("--task", required=True, help="逗号分隔，如 arc_easy,hellaswag")
    a.add_argument("--num-fewshot", type=int, default=0)
    a.add_argument("--seed", type=int, default=None, help="不填则从结果文件自动读取 few-shot 种子")
    a.add_argument("--limit", type=int, default=None)
    a.add_argument("--batch-size", type=int, default=None, help="不填则从结果文件自动读取框架实际使用的值")
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
