# RUNS.md — 实验台账

> 本文件由 `src/run_logger.py` 自动生成，请勿手工编辑。
> 每一次评测运行都记录完整参数与运行环境，保证结果可追溯、可复现。

共 **23** 次运行。

## 运行总表

| # | run_id | 运行时间 | 模型 | 权重版本 | task | few-shot | seed | limit | batch | GPU | 结果路径 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 20260922-212258-f671 | 2026-09-22 21:22 | Qwen/Qwen2.5-1.5B | main | arc_easy | 0 | 1234 | 100 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | runs/day02_limit100/Qwen__Qwen2.5-1.5B/results_2026-09-22T21-23-48.058308.json |
| 2 | 20260922-213153-e4dc | 2026-09-22 21:31 | Qwen/Qwen2.5-1.5B | main | arc_easy | 0 | 1234 | 500 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | runs/day02_limit500/Qwen__Qwen2.5-1.5B/results_2026-09-22T21-34-33.102021.json |
| 3 | 20260925-225758-fde6 | 2026-09-25 22:57 | Qwen/Qwen2.5-1.5B | 8faed761d45a263340a0528343f099c05c9a4323 | arc_easy | 5 | 1234 | 500 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | runs/day04_arc_easy_5shot_seed1234/Qwen__Qwen2.5-1.5B/results_2026-09-25T23-01-39.580769.json |
| 4 | 20260927-230614-98d7 | 2026-09-27 23:06 | Qwen/Qwen2.5-0.5B | 060db6499f32faf8b98477b0a26969ef7d8b9987 | arc_easy | 0 | 1234 | 200 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen05_arc_easy_s0_n200\Qwen__Qwen2.5-0.5B\results_2026-09-27T23-10-36.541018.json |
| 5 | 20260927-231146-a9ec | 2026-09-27 23:11 | Qwen/Qwen2.5-0.5B | 060db6499f32faf8b98477b0a26969ef7d8b9987 | hellaswag | 0 | 1234 | 200 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen05_hellaswag_s0_n200\Qwen__Qwen2.5-0.5B\results_2026-09-27T23-12-46.441912.json |
| 6 | 20260927-231306-ce38 | 2026-09-27 23:13 | Qwen/Qwen2.5-0.5B | 060db6499f32faf8b98477b0a26969ef7d8b9987 | mmlu | 5 | 1234 | 10 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen05_mmlu_s5_n10\Qwen__Qwen2.5-0.5B\results_2026-09-27T23-20-41.245814.json |
| 7 | 20260927-232102-dde0 | 2026-09-27 23:21 | Qwen/Qwen2.5-0.5B | 060db6499f32faf8b98477b0a26969ef7d8b9987 | gsm8k | 5 | 1234 | 200 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen05_gsm8k_s5_n200\Qwen__Qwen2.5-0.5B\results_2026-09-27T23-48-32.121588.json |
| 8 | 20260927-234851-7566 | 2026-09-27 23:48 | Qwen/Qwen2.5-0.5B | 060db6499f32faf8b98477b0a26969ef7d8b9987 | truthfulqa_mc2 | 0 | 1234 | 200 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen05_truthfulqa_mc2_s0_n200\Qwen__Qwen2.5-0.5B\results_2026-09-27T23-50-02.484603.json |
| 9 | 20260928-100703-72b4 | 2026-09-28 10:07 | Qwen/Qwen2.5-1.5B | 8faed761d45a263340a0528343f099c05c9a4323 | arc_easy | 0 | 1234 | 200 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen15_arc_easy_s0_n200\Qwen__Qwen2.5-1.5B\results_2026-09-28T10-07-58.956807.json |
| 10 | 20260928-100819-7e77 | 2026-09-28 10:08 | Qwen/Qwen2.5-1.5B | 8faed761d45a263340a0528343f099c05c9a4323 | hellaswag | 0 | 1234 | 200 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen15_hellaswag_s0_n200\Qwen__Qwen2.5-1.5B\results_2026-09-28T10-09-13.193049.json |
| 11 | 20260928-100932-6604 | 2026-09-28 10:09 | Qwen/Qwen2.5-1.5B | 8faed761d45a263340a0528343f099c05c9a4323 | mmlu | 5 | 1234 | 10 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen15_mmlu_s5_n10\Qwen__Qwen2.5-1.5B\results_2026-09-28T10-13-17.558889.json |
| 12 | 20260928-101337-a4e3 | 2026-09-28 10:13 | Qwen/Qwen2.5-1.5B | 8faed761d45a263340a0528343f099c05c9a4323 | gsm8k | 5 | 1234 | 200 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen15_gsm8k_s5_n200\Qwen__Qwen2.5-1.5B\results_2026-09-28T10-31-12.587461.json |
| 13 | 20260928-103133-14a3 | 2026-09-28 10:31 | Qwen/Qwen2.5-1.5B | 8faed761d45a263340a0528343f099c05c9a4323 | truthfulqa_mc2 | 0 | 1234 | 200 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen15_truthfulqa_mc2_s0_n200\Qwen__Qwen2.5-1.5B\results_2026-09-28T10-33-11.308500.json |
| 14 | 20260928-124220-797d | 2026-09-28 12:42 | Qwen/Qwen2.5-3B | 3aab1f1954e9cc14eb9509a215f9e5ca08227a9b | arc_easy | 0 | 1234 | 200 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen3_arc_easy_s0_n200\Qwen__Qwen2.5-3B\results_2026-09-28T12-43-37.475057.json |
| 15 | 20260928-131901-d1cd | 2026-09-28 13:19 | Qwen/Qwen2.5-3B | 3aab1f1954e9cc14eb9509a215f9e5ca08227a9b | hellaswag | 0 | 1234 | 200 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen3_hellaswag_s0_n200\Qwen__Qwen2.5-3B\results_2026-09-28T13-20-14.319824.json |
| 16 | 20260928-132036-4af3 | 2026-09-28 13:20 | Qwen/Qwen2.5-3B | 3aab1f1954e9cc14eb9509a215f9e5ca08227a9b | mmlu | 5 | 1234 | 10 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen3_mmlu_s5_n10\Qwen__Qwen2.5-3B\results_2026-09-28T13-26-48.528084.json |
| 17 | 20260928-132711-4b35 | 2026-09-28 13:27 | Qwen/Qwen2.5-3B | 3aab1f1954e9cc14eb9509a215f9e5ca08227a9b | gsm8k | 5 | 1234 | 200 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen3_gsm8k_s5_n200\Qwen__Qwen2.5-3B\results_2026-09-28T13-50-11.974380.json |
| 18 | 20260928-135037-1d43 | 2026-09-28 13:50 | Qwen/Qwen2.5-3B | 3aab1f1954e9cc14eb9509a215f9e5ca08227a9b | truthfulqa_mc2 | 0 | 1234 | 200 | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen3_truthfulqa_mc2_s0_n200\Qwen__Qwen2.5-3B\results_2026-09-28T13-53-29.185925.json |
| 19 | 20260929-164903-5536 | 2026-09-29 16:49 | Qwen/Qwen2.5-1.5B | 8faed761d45a263340a0528343f099c05c9a4323 | custom_ceval_computer_network | 0 | 1234 | - | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day08_ceval_computer_network_0shot\Qwen__Qwen2.5-1.5B\results_2026-09-29T16-53-16.881874.json |
| 20 | 20261002-133215-1046 | 2026-10-02 13:32 | Qwen/Qwen2.5-1.5B | 8faed761d45a263340a0528343f099c05c9a4323 | ceval-valid_computer_network | 0 | 1234 | - | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day09_ceval_builtin_0shot\Qwen__Qwen2.5-1.5B\results_2026-10-02T13-34-05.247414.json |
| 21 | 20261002-135250-ec04 | 2026-10-02 13:52 | Qwen/Qwen2.5-1.5B | 8faed761d45a263340a0528343f099c05c9a4323 | custom_ceval_computer_network_aligned | 0 | 1234 | - | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day09_ceval_custom_aligned_0shot\Qwen__Qwen2.5-1.5B\results_2026-10-02T13-53-16.905946.json |
| 22 | 20261002-135800-ebde | 2026-10-02 13:58 | Qwen/Qwen2.5-1.5B | 8faed761d45a263340a0528343f099c05c9a4323 | ceval-valid | 5 | 1234 | - | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day09_ceval_full_5shot\Qwen__Qwen2.5-1.5B\results_2026-10-02T14-07-40.746283.json |
| 23 | 20261002-141056-81a2 | 2026-10-02 14:10 | Qwen/Qwen2.5-1.5B | 8faed761d45a263340a0528343f099c05c9a4323 | custom_ceval_computer_network_5shot | 5 | 1234 | - | 1 | NVIDIA GeForce RTX 4060 Laptop GPU | D:\桌面\个人\工程\llm-eval-diagnostics\runs\day09_ceval_custom_5shot\Qwen__Qwen2.5-1.5B\results_2026-10-02T14-11-24.917138.json |

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

### 3. `20260925-225758-fde6`

- **运行时间**：2026-09-25 22:57:58
- **模型**：`Qwen/Qwen2.5-1.5B` @ `8faed761d45a263340a0528343f099c05c9a4323`
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 4 ARC-Easy 5-shot 500题；同 Day 2 基线对照
- **原始结果**：`runs/day04_arc_easy_5shot_seed1234/Qwen__Qwen2.5-1.5B/results_2026-09-25T23-01-39.580769.json`

```bash
lm_eval run --model hf --model_args pretrained=Qwen/Qwen2.5-1.5B,revision=8faed761d45a263340a0528343f099c05c9a4323 --tasks arc_easy --num_fewshot 5 --limit 500 --batch_size 1 --device cuda:0 --seed 0,1234,1234,1234 --output_path runs/day04_arc_easy_5shot_seed1234 --log_samples
```

### 4. `20260927-230614-98d7`

- **运行时间**：2026-09-27 23:06:14
- **模型**：`Qwen/Qwen2.5-0.5B` @ `060db6499f32faf8b98477b0a26969ef7d8b9987`
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 6 主结果表；有限样本试跑
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen05_arc_easy_s0_n200\Qwen__Qwen2.5-0.5B\results_2026-09-27T23-10-36.541018.json`

```bash
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-0.5B,revision=060db6499f32faf8b98477b0a26969ef7d8b9987,dtype=bfloat16' --tasks arc_easy --num_fewshot 0 --limit 200 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day06_qwen05_arc_easy_s0_n200' --log_samples
```

### 5. `20260927-231146-a9ec`

- **运行时间**：2026-09-27 23:11:46
- **模型**：`Qwen/Qwen2.5-0.5B` @ `060db6499f32faf8b98477b0a26969ef7d8b9987`
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 6 主结果表；有限样本试跑
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen05_hellaswag_s0_n200\Qwen__Qwen2.5-0.5B\results_2026-09-27T23-12-46.441912.json`

```bash
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-0.5B,revision=060db6499f32faf8b98477b0a26969ef7d8b9987,dtype=bfloat16' --tasks hellaswag --num_fewshot 0 --limit 200 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day06_qwen05_hellaswag_s0_n200' --log_samples
```

### 6. `20260927-231306-ce38`

- **运行时间**：2026-09-27 23:13:06
- **模型**：`Qwen/Qwen2.5-0.5B` @ `060db6499f32faf8b98477b0a26969ef7d8b9987`
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 6 主结果表；有限样本试跑
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen05_mmlu_s5_n10\Qwen__Qwen2.5-0.5B\results_2026-09-27T23-20-41.245814.json`

```bash
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-0.5B,revision=060db6499f32faf8b98477b0a26969ef7d8b9987,dtype=bfloat16' --tasks mmlu --num_fewshot 5 --limit 10 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day06_qwen05_mmlu_s5_n10' --log_samples
```

### 7. `20260927-232102-dde0`

- **运行时间**：2026-09-27 23:21:02
- **模型**：`Qwen/Qwen2.5-0.5B` @ `060db6499f32faf8b98477b0a26969ef7d8b9987`
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 6 主结果表；有限样本试跑
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen05_gsm8k_s5_n200\Qwen__Qwen2.5-0.5B\results_2026-09-27T23-48-32.121588.json`

```bash
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-0.5B,revision=060db6499f32faf8b98477b0a26969ef7d8b9987,dtype=bfloat16' --tasks gsm8k --num_fewshot 5 --limit 200 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day06_qwen05_gsm8k_s5_n200' --log_samples
```

### 8. `20260927-234851-7566`

- **运行时间**：2026-09-27 23:48:51
- **模型**：`Qwen/Qwen2.5-0.5B` @ `060db6499f32faf8b98477b0a26969ef7d8b9987`
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 6 主结果表；有限样本试跑
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen05_truthfulqa_mc2_s0_n200\Qwen__Qwen2.5-0.5B\results_2026-09-27T23-50-02.484603.json`

```bash
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-0.5B,revision=060db6499f32faf8b98477b0a26969ef7d8b9987,dtype=bfloat16' --tasks truthfulqa_mc2 --num_fewshot 0 --limit 200 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day06_qwen05_truthfulqa_mc2_s0_n200' --log_samples
```

### 9. `20260928-100703-72b4`

- **运行时间**：2026-09-28 10:07:03
- **模型**：`Qwen/Qwen2.5-1.5B` @ `8faed761d45a263340a0528343f099c05c9a4323`
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 6 main result table; limited-sample trial
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen15_arc_easy_s0_n200\Qwen__Qwen2.5-1.5B\results_2026-09-28T10-07-58.956807.json`

```bash
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-1.5B,revision=8faed761d45a263340a0528343f099c05c9a4323,dtype=bfloat16' --tasks arc_easy --num_fewshot 0 --limit 200 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day06_qwen15_arc_easy_s0_n200' --log_samples
```

### 10. `20260928-100819-7e77`

- **运行时间**：2026-09-28 10:08:19
- **模型**：`Qwen/Qwen2.5-1.5B` @ `8faed761d45a263340a0528343f099c05c9a4323`
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 6 main result table; limited-sample trial
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen15_hellaswag_s0_n200\Qwen__Qwen2.5-1.5B\results_2026-09-28T10-09-13.193049.json`

```bash
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-1.5B,revision=8faed761d45a263340a0528343f099c05c9a4323,dtype=bfloat16' --tasks hellaswag --num_fewshot 0 --limit 200 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day06_qwen15_hellaswag_s0_n200' --log_samples
```

### 11. `20260928-100932-6604`

- **运行时间**：2026-09-28 10:09:32
- **模型**：`Qwen/Qwen2.5-1.5B` @ `8faed761d45a263340a0528343f099c05c9a4323`
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 6 main result table; limited-sample trial
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen15_mmlu_s5_n10\Qwen__Qwen2.5-1.5B\results_2026-09-28T10-13-17.558889.json`

```bash
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-1.5B,revision=8faed761d45a263340a0528343f099c05c9a4323,dtype=bfloat16' --tasks mmlu --num_fewshot 5 --limit 10 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day06_qwen15_mmlu_s5_n10' --log_samples
```

### 12. `20260928-101337-a4e3`

- **运行时间**：2026-09-28 10:13:37
- **模型**：`Qwen/Qwen2.5-1.5B` @ `8faed761d45a263340a0528343f099c05c9a4323`
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 6 main result table; limited-sample trial
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen15_gsm8k_s5_n200\Qwen__Qwen2.5-1.5B\results_2026-09-28T10-31-12.587461.json`

```bash
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-1.5B,revision=8faed761d45a263340a0528343f099c05c9a4323,dtype=bfloat16' --tasks gsm8k --num_fewshot 5 --limit 200 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day06_qwen15_gsm8k_s5_n200' --log_samples
```

### 13. `20260928-103133-14a3`

- **运行时间**：2026-09-28 10:31:33
- **模型**：`Qwen/Qwen2.5-1.5B` @ `8faed761d45a263340a0528343f099c05c9a4323`
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 6 main result table; limited-sample trial
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen15_truthfulqa_mc2_s0_n200\Qwen__Qwen2.5-1.5B\results_2026-09-28T10-33-11.308500.json`

```bash
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-1.5B,revision=8faed761d45a263340a0528343f099c05c9a4323,dtype=bfloat16' --tasks truthfulqa_mc2 --num_fewshot 0 --limit 200 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day06_qwen15_truthfulqa_mc2_s0_n200' --log_samples
```

### 14. `20260928-124220-797d`

- **运行时间**：2026-09-28 12:42:20
- **模型**：`Qwen/Qwen2.5-3B` @ `3aab1f1954e9cc14eb9509a215f9e5ca08227a9b`
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 6 main result table; limited-sample trial
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen3_arc_easy_s0_n200\Qwen__Qwen2.5-3B\results_2026-09-28T12-43-37.475057.json`

```bash
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-3B,revision=3aab1f1954e9cc14eb9509a215f9e5ca08227a9b,dtype=bfloat16' --tasks arc_easy --num_fewshot 0 --limit 200 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day06_qwen3_arc_easy_s0_n200' --log_samples
```

### 15. `20260928-131901-d1cd`

- **运行时间**：2026-09-28 13:19:01
- **模型**：`Qwen/Qwen2.5-3B` @ `3aab1f1954e9cc14eb9509a215f9e5ca08227a9b`
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 6 main result table; limited-sample trial
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen3_hellaswag_s0_n200\Qwen__Qwen2.5-3B\results_2026-09-28T13-20-14.319824.json`

```bash
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-3B,revision=3aab1f1954e9cc14eb9509a215f9e5ca08227a9b,dtype=bfloat16' --tasks hellaswag --num_fewshot 0 --limit 200 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day06_qwen3_hellaswag_s0_n200' --log_samples
```

### 16. `20260928-132036-4af3`

- **运行时间**：2026-09-28 13:20:36
- **模型**：`Qwen/Qwen2.5-3B` @ `3aab1f1954e9cc14eb9509a215f9e5ca08227a9b`
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 6 main result table; limited-sample trial
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen3_mmlu_s5_n10\Qwen__Qwen2.5-3B\results_2026-09-28T13-26-48.528084.json`

```bash
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-3B,revision=3aab1f1954e9cc14eb9509a215f9e5ca08227a9b,dtype=bfloat16' --tasks mmlu --num_fewshot 5 --limit 10 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day06_qwen3_mmlu_s5_n10' --log_samples
```

### 17. `20260928-132711-4b35`

- **运行时间**：2026-09-28 13:27:11
- **模型**：`Qwen/Qwen2.5-3B` @ `3aab1f1954e9cc14eb9509a215f9e5ca08227a9b`
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 6 main result table; limited-sample trial
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen3_gsm8k_s5_n200\Qwen__Qwen2.5-3B\results_2026-09-28T13-50-11.974380.json`

```bash
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-3B,revision=3aab1f1954e9cc14eb9509a215f9e5ca08227a9b,dtype=bfloat16' --tasks gsm8k --num_fewshot 5 --limit 200 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day06_qwen3_gsm8k_s5_n200' --log_samples
```

### 18. `20260928-135037-1d43`

- **运行时间**：2026-09-28 13:50:37
- **模型**：`Qwen/Qwen2.5-3B` @ `3aab1f1954e9cc14eb9509a215f9e5ca08227a9b`
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 6 main result table; limited-sample trial
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day06_qwen3_truthfulqa_mc2_s0_n200\Qwen__Qwen2.5-3B\results_2026-09-28T13-53-29.185925.json`

```bash
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-3B,revision=3aab1f1954e9cc14eb9509a215f9e5ca08227a9b,dtype=bfloat16' --tasks truthfulqa_mc2 --num_fewshot 0 --limit 200 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day06_qwen3_truthfulqa_mc2_s0_n200' --log_samples
```

### 19. `20260929-164903-5536`

- **运行时间**：2026-09-29 16:49:03
- **模型**：`Qwen/Qwen2.5-1.5B` @ `8faed761d45a263340a0528343f099c05c9a4323`
- **权重指纹**：`8faed761d45a263340a0528343f099c05c9a4323`（`main` 是浮动引用；这是截至运行当日 `main` 指向的 commit）
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 8 custom C-Eval computer_network baseline; see notes/08-ceval接入.md
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day08_ceval_computer_network_0shot\Qwen__Qwen2.5-1.5B\results_2026-09-29T16-53-16.881874.json`

> ⚠️ 本次运行未记录 `command`，无法逐字复现。

### 20. `20261002-133215-1046`

- **运行时间**：2026-10-02 13:32:15
- **模型**：`Qwen/Qwen2.5-1.5B` @ `8faed761d45a263340a0528343f099c05c9a4323`
- **权重指纹**：`8faed761d45a263340a0528343f099c05c9a4323`（`main` 是浮动引用；这是截至运行当日 `main` 指向的 commit）
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 9 built-in 0-shot comparison; see notes/09-benchmark接入与对拍.md
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day09_ceval_builtin_0shot\Qwen__Qwen2.5-1.5B\results_2026-10-02T13-34-05.247414.json`

> ⚠️ 本次运行未记录 `command`，无法逐字复现。

### 21. `20261002-135250-ec04`

- **运行时间**：2026-10-02 13:52:50
- **模型**：`Qwen/Qwen2.5-1.5B` @ `8faed761d45a263340a0528343f099c05c9a4323`
- **权重指纹**：`8faed761d45a263340a0528343f099c05c9a4323`（`main` 是浮动引用；这是截至运行当日 `main` 指向的 commit）
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 9 aligned custom 0-shot; see notes/09-benchmark接入与对拍.md
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day09_ceval_custom_aligned_0shot\Qwen__Qwen2.5-1.5B\results_2026-10-02T13-53-16.905946.json`

> ⚠️ 本次运行未记录 `command`，无法逐字复现。

### 22. `20261002-135800-ebde`

- **运行时间**：2026-10-02 13:58:00
- **模型**：`Qwen/Qwen2.5-1.5B` @ `8faed761d45a263340a0528343f099c05c9a4323`
- **权重指纹**：`8faed761d45a263340a0528343f099c05c9a4323`（`main` 是浮动引用；这是截至运行当日 `main` 指向的 commit）
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 9 full 52-subject validation 5-shot; see notes/09-benchmark接入与对拍.md
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day09_ceval_full_5shot\Qwen__Qwen2.5-1.5B\results_2026-10-02T14-07-40.746283.json`

> ⚠️ 本次运行未记录 `command`，无法逐字复现。

### 23. `20261002-141056-81a2`

- **运行时间**：2026-10-02 14:10:56
- **模型**：`Qwen/Qwen2.5-1.5B` @ `8faed761d45a263340a0528343f099c05c9a4323`
- **权重指纹**：`8faed761d45a263340a0528343f099c05c9a4323`（`main` 是浮动引用；这是截至运行当日 `main` 指向的 commit）
- **随机种子**：`numpy_seed=1234`, `torch_seed=1234`, `fewshot_seed=1234`
- **batch size**：1
- **备注**：Day 9 custom computer_network 5-shot; see notes/09-benchmark接入与对拍.md
- **原始结果**：`D:\桌面\个人\工程\llm-eval-diagnostics\runs\day09_ceval_custom_5shot\Qwen__Qwen2.5-1.5B\results_2026-10-02T14-11-24.917138.json`

> ⚠️ 本次运行未记录 `command`，无法逐字复现。

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
| git_commit | d57569a |

> 其中 `git_commit`、`lm_eval`、`transformers` 取自 lm-eval 结果文件（**运行当时**的值），其余为登记时刻采集。

## 为什么记录这些字段

- **权重版本 / 权重指纹**：HuggingFace 上的模型会被更新，只记模型名无法复现；`main` 是浮动引用，所以额外记录它当日指向的 commit hash
- **seed / few-shot / limit**：这三个参数直接影响分数，且 seed 影响 few-shot 示例采样
- **batch size**：batch shape 会改变 GPU kernel 的选择，进而让 logits 出现 ~1e-6 级差异，在近乎并列的选项上足以翻转 argmax —— 所以它是「口径」的一部分，不是性能开关
- **框架与依赖版本**：评测框架的口径会随版本变化
- **git_commit**：定位结果由哪版评测代码产出
- **原始结果路径**：没有原始输出的分数是不可审计的