# RUNS.md — 实验台账

> 本文件由 `src/run_logger.py` 自动生成，请勿手工编辑。
> 每一次评测运行都记录完整参数与运行环境，保证结果可追溯、可复现。

共 **2** 次运行。

| run_id | 时间 | 模型 | revision | task | few-shot | seed | limit | batch | GPU | 结果路径 |
|---|---|---|---|---|---|---|---|---|---|---|
| 20260922-230709-cda1 | 2026-09-22 23:07 | Qwen/Qwen2.5-1.5B | main | arc_easy | 0 | 1234 | 100 | None | NVIDIA GeForce RTX 4060 Laptop GPU | runs/day02_limit100/Qwen__Qwen2.5-1.5B/results_2026-09-22T21-23-48.058308.json |
| 20260922-230713-e4ba | 2026-09-22 23:07 | Qwen/Qwen2.5-1.5B | main | arc_easy | 0 | 1234 | 500 | None | NVIDIA GeForce RTX 4060 Laptop GPU | runs/day02_limit500/Qwen__Qwen2.5-1.5B/results_2026-09-22T21-34-33.102021.json |

## 运行环境快照（最近一次）

| 组件 | 版本 |
|---|---|
| python | 3.11.16 |
| torch | 2.14.0+cu126 |
| transformers | 5.17.0 |
| lm_eval | 0.4.13 |
| datasets | 5.0.1 |
| cuda | 12.6 |
| gpu | NVIDIA GeForce RTX 4060 Laptop GPU |
| platform | Windows-10-10.0.26200-SP0 |
| git_commit | 0d4732d |

## 复现方式

```bash
# 任取上表中一行，复制其 command 字段即可复现该次评测
# 完整命令与运行环境见 runs/ledger.jsonl
```

## 为什么记录这些字段

- **revision**：HuggingFace 上的模型会被更新，只记模型名无法复现
- **seed / few-shot / limit**：这三个参数直接影响分数，且 seed 影响 few-shot 示例采样
- **框架与依赖版本**：评测框架的口径会随版本变化
- **git_commit**：定位结果由哪版评测代码产出
- **原始结果路径**：没有原始输出的分数是不可审计的