"""
环境自检 —— Day 1 用这个确认你的机器准备好了
================================================
它会逐项检查并给出"能不能跑评测"的结论，以及失败时该怎么办。

用法:
    python src/check_env.py
"""

from __future__ import annotations

import platform
import shutil
import sys


def line(ok: bool | None, label: str, detail: str = "") -> None:
    mark = {True: "[ OK ]", False: "[FAIL]", None: "[SKIP]"}[ok]
    print(f"{mark} {label:<28} {detail}")


def main() -> int:
    print("=" * 68)
    print("评测环境自检")
    print("=" * 68)

    # 1. Python 版本
    major, minor = sys.version_info[:2]
    ok = (major, minor) >= (3, 9)
    line(ok, "Python 版本", f"{platform.python_version()}" + ("" if ok else "  ← 需要 3.9+"))

    # 2. 关键依赖
    deps = {
        "torch": "PyTorch（推理后端）",
        "transformers": "模型加载",
        "datasets": "数据集加载（质检脚本需要）",
    }
    versions: dict[str, str] = {}
    for mod, desc in deps.items():
        try:
            m = __import__(mod)
            v = getattr(m, "__version__", "?")
            versions[mod] = v
            line(True, mod, f"{v}  ({desc})")
        except ImportError:
            versions[mod] = ""
            line(False, mod, f"未安装  ← pip install {mod}")

    # lm-eval 的包名和导入名不一致，单独处理
    try:
        from importlib.metadata import version

        lv = version("lm-eval")
        line(True, "lm-eval", lv)
    except Exception:
        try:
            lv = version("lm_eval")
            line(True, "lm-eval", lv)
        except Exception:
            line(False, "lm-eval", "未安装  ← pip install lm-eval")

    # 3. CUDA / GPU —— 最关键的一项
    print("-" * 68)
    gpu_ok = False
    if versions.get("torch"):
        try:
            import torch

            cuda_ok = torch.cuda.is_available()
            line(cuda_ok, "CUDA 可用", "是" if cuda_ok else "否")
            if cuda_ok:
                name = torch.cuda.get_device_name(0)
                total = torch.cuda.get_device_properties(0).total_memory / 1024**3
                free = torch.cuda.mem_get_info()[0] / 1024**3
                line(True, "GPU", f"{name}")
                line(True, "显存", f"总 {total:.1f} GB / 当前空闲 {free:.1f} GB")
                line(True, "CUDA 版本", torch.version.cuda or "?")
                gpu_ok = True
                # 给出基于显存的模型规模建议
                if total < 6:
                    rec = "0.5B / 1.5B（bf16），需要 --batch_size 1"
                elif total < 10:
                    rec = "1.5B / 3B（bf16）流畅；7B 需 4-bit 量化"
                elif total < 20:
                    rec = "3B / 7B（bf16）"
                else:
                    rec = "7B 及以上"
                print(f"       → 建议模型规模：{rec}")
            else:
                line(False, "CUDA 可用", "torch 装成了 CPU 版  ← 重装 CUDA 版 torch")
        except Exception as e:
            line(False, "torch 检查", str(e)[:60])
    else:
        line(None, "CUDA 检查", "torch 未安装，跳过")

    # 4. nvidia-smi（驱动层）
    print("-" * 68)
    if shutil.which("nvidia-smi"):
        import subprocess

        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                text=True,
                timeout=10,
            ).strip()
            line(True, "nvidia-smi", out.replace("\n", " | "))
        except Exception as e:
            line(False, "nvidia-smi", str(e)[:60])
    else:
        line(False, "nvidia-smi", "未找到  ← 需安装 NVIDIA 驱动")

    # 5. 磁盘空间（模型权重很占地方）
    print("-" * 68)
    try:
        total, used, free = shutil.disk_usage(".")
        free_gb = free / 1024**3
        # 3 个 Qwen 模型 + 数据集缓存大约需要 15-20GB
        line(free_gb > 20, "磁盘剩余", f"{free_gb:.1f} GB" + ("" if free_gb > 20 else "  ← 建议保留 20GB+ 给模型缓存"))
    except Exception as e:
        line(None, "磁盘检查", str(e)[:60])

    # 6. 结论
    print("=" * 68)
    print("项目目录结构检查")
    print("=" * 68)
    from pathlib import Path

    for d in ("src", "scripts", "runs", "reports", "notes", "runs/figures"):
        p = Path(d)
        exists = p.exists()
        if not exists:
            p.mkdir(parents=True, exist_ok=True)
        line(True, d, "已存在" if exists else "已创建")

    print()
    if gpu_ok:
        print("结论：环境可用，可以开始 Day 2 的评测。")
        print()
        print("下一步（复制即用，先跑最小规模确认链路）：")
        print("  lm_eval --model hf \\")
        print("      --model_args pretrained=Qwen/Qwen2.5-1.5B,dtype=bfloat16 \\")
        print("      --tasks arc_easy --device cuda:0 --batch_size 4 --limit 20")
    else:
        print("结论：GPU 不可用，先解决环境问题。")
        print()
        print("排查顺序：")
        print("  1. 装了 CUDA 版 torch 吗？  → pip install torch --index-url https://download.pytorch.org/whl/cu121")
        print("  2. 驱动正常吗？             → nvidia-smi 能输出吗")
        print("  3. Windows 上坑较多，建议用 WSL2 (Ubuntu) 重试")
    return 0 if gpu_ok else 1


if __name__ == "__main__":
    sys.exit(main())
