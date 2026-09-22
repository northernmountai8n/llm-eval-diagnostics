# RUNS.md — 实验台账

> 本文件由 `src/run_logger.py` 自动生成，请勿手工编辑。
> 每一次评测运行都记录完整参数与运行环境，保证结果可追溯、可复现。

共 **2** 次运行。

## 运行总表

| # | run_id | 运行时间 | 模型 | 权重版本 | task | few-shot | seed | limit | batch | GPU | 结果路径 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 20260922-212258-f671 | 2026-09-22 21:22 | Qwen/Qwen2.5-1.5B | main | arc_easy | 0 | 1234 | 100 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | runs/day02_limit100/Qwen__Qwen2.5-1.5B/results_2026-09-22T21-23-48.058308.json |
| 2 | 20260922-213153-e4dc | 2026-09-22 21:31 | Qwen/Qwen2.5-1.5B | main | arc_easy | 0 | 1234 | 500 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | runs/day02_limit500/Qwen__Qwen2.5-1.5B/results_2026-09-22T21-34-33.102021.json |

> `seed` 列填的是 **few-shot 采样种子**（0-shot 任务下不影响分数，但 few-shot 任务下它会改变示例抽取）。
> lm-eval 实际使用四个独立种子，完整取值见下方「复现命令」。

## 复现命令

每次运行的完整命令行与运行参数如下，**复制即用**。

### 1. `20260922-212258-f671`

- **运行时间**：2026-09-22 21:22:58
- **模型**：`Qwen/Qwen2.5-1.5B` @ `main`
- **权重指纹**：`8faed761d45a263340a0528343f099c05c9a4323`（`main` 是浮动引用；这是截至运行当日 `main` 指向的 commit）
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：未传 --seed，lm-eval 用默认 0/1234/1234/1234
- **原始结果**：`runs/day02_limit100/Qwen__Qwen2.5-1.5B/results_2026-09-22T21-23-48.058308.json`

```bash
lm_eval run --model hf --model_args pretrained=Qwen/Qwen2.5-1.5B --tasks arc_easy --limit 100 --batch_size 1 --device cuda:0
```

### 2. `20260922-213153-e4dc`

- **运行时间**：2026-09-22 21:31:53
- **模型**：`Qwen/Qwen2.5-1.5B` @ `main`
- **权重指纹**：`8faed761d45a263340a0528343f099c05c9a4323`（`main` 是浮动引用；这是截至运行当日 `main` 指向的 commit）
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：与 limit=100 成对，用于对照样本量影响
- **原始结果**：`runs/day02_limit500/Qwen__Qwen2.5-1.5B/results_2026-09-22T21-34-33.102021.json`

```bash
lm_eval run --model hf --model_args pretrained=Qwen/Qwen2.5-1.5B --tasks arc_easy --limit 500 --batch_size 1 --device cuda:0
```

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
| platform | Windows-11-10.0.26200-SP0 |
| git_commit | 0d4732d |

> 其中 `git_commit`、`lm_eval`、`transformers` 取自 lm-eval 结果文件（**运行当时**的值），其余为登记时刻采集。

## 为什么记录这些字段

- **权重版本 / 权重指纹**：HuggingFace 上的模型会被更新，只记模型名无法复现；`main` 是浮动引用，所以额外记录它当日指向的 commit hash
- **seed / few-shot / limit**：这三个参数直接影响分数，且 seed 影响 few-shot 示例采样
- **batch size**：batch shape 会改变 GPU kernel 的选择，进而让 logits 出现 ~1e-6 级差异，在近乎并列的选项上足以翻转 argmax —— 所以它是「口径」的一部分，不是性能开关
- **框架与依赖版本**：评测框架的口径会随版本变化
- **git_commit**：定位结果由哪版评测代码产出
- **原始结果路径**：没有原始输出的分数是不可审计的