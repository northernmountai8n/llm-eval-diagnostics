# Day 9：C-Eval 接入与对拍

> 运行日期：2026-10-02。模型为 `Qwen/Qwen2.5-1.5B` 基座模型，权重 revision `8faed761d45a263340a0528343f099c05c9a4323`；`lm-eval 0.4.13`，`dtype=bfloat16`，`batch_size=1`，`cuda:0`，seed `0,1234,1234,1234`。以下本地数据均使用 C-Eval 的 `val`，未设置 `--limit`。

## 目标和配置

Day 8 的[最小任务](../configs/tasks/ceval_computer_network.yaml)仅覆盖「计算机网络」19 题、0-shot、`acc`。Day 9 做两份独立配置，以免改动 Day 8 的原始口径：

- [0-shot 对齐版](../configs/tasks/ceval_computer_network_aligned.yaml)：加入内置任务的科目说明，并同时报告 `acc` 与 `acc_norm`。
- [5-shot 版](../configs/tasks/ceval_computer_network_5shot.yaml)：在对齐版基础上，使用 `dev` 的前 5 题作为示例（`fewshot_split: dev`、`sampler: first_n`）。

这两份配置使用 `multiple_choice` 和 `loglikelihood` 给 A–D 选项计分，不做生成式答案的正则抽取。`doc_to_target` 把答案字母映射到 0–3；本次候选 continuation 都是一个空格加一个字母，因此 `acc_norm` 与 `acc` 相同。

## 我的分数与内置任务

| 任务 | 范围 | shot | 答对/题数 | acc | acc_norm |
|---|---|---:|---:|---:|---:|
| Day 8 原始自定义配置 | 计算机网络 `val` | 0 | 10/19 | 52.63% | 未配置 |
| `ceval-valid_computer_network` | 同上 | 0 | 11/19 | 57.89% | 57.89% |
| 自定义 0-shot 对齐版 | 同上 | 0 | 11/19 | 57.89% | 57.89% |
| `ceval-valid_computer_network`（完整组内） | 同上 | 5 | 14/19 | 73.68% | 73.68% |
| 自定义 5-shot 版 | 同上 | 5 | 14/19 | 73.68% | 73.68% |
| `ceval-valid` 完整组 | 52 科目 `val` | 5 | 923/1346 | **68.57%** | **68.57%** |

完整组的 `acc` 原始值为 `0.6857355126300149`，标准误为 `0.012157881485803242`。52 个科目各有一份逐题 JSONL；求和得到 1,346 题、923 题正确，与汇总值一致。完整组采用按题数加权的均值。

逐题文件按 `doc.id` 对齐后：

- 内置 0-shot 与自定义 0-shot 对齐版：19/19 道题的 `doc`、`target`、四条请求参数、`filtered_resps`、`acc`、`acc_norm` 全部相同。
- 内置 5-shot（完整组中的计算机网络科目）与自定义 5-shot：同样所有上述字段在 19/19 道题上相同。
- Day 8 原始 0-shot 与内置 0-shot 只在 `doc.id=11` 的对错上不同。原始配置没有科目说明，这一题预测 A；内置任务在题目前加入“以下是中国关于计算机网络的单项选择题，请选出其中的正确答案。”后预测 C，与标准答案 C 一致。加入同一句说明并重跑后，全部请求和响应与内置任务对齐。这把一题差异定位为 **prompt 前缀**，不是答案映射错误。
- 内置 0-shot 到 5-shot，计算机网络的 `doc.id=0,6,15` 由错变对，其余题目对错未变；该科目由 11/19 升为 14/19。这是本次运行的观察，不能推广为 few-shot 必然提高所有科目的分数。

## 我的分数 vs 公开分数

[PCMind-2.1-Kaiyuan-2B 技术报告](https://fangmingliu.github.io/files/PCMind_2_1_Kaiyuan_2B.pdf)表 2 报告基座模型 **Qwen2.5-1.5B 的 C-Eval 5-shot 为 68.63%**。本机完整验证集为 **68.57%**，低约 **0.06 个百分点**。这是一份第三方论文报告的参照值，并非 Qwen 官方发布的该模型 C-Eval 成绩。

两者**不能据数值接近就声称严格复现**：论文使用 OpenCompass，说明知识类任务采用 PPL，并在 multiple-choice formulation（MCF）与 completion formulation（CF）之间报告较高成绩；本机使用 `lm-eval` 的选项 loglikelihood。论文未在该处给出足以确认与本次完全相同的数据划分、prompt、权重 revision 和汇总细节。C-Eval [官方榜单](https://cevalbenchmark.com/static/leaderboard.html)已停止维护；Qwen2.5-1.5B [模型卡](https://huggingface.co/Qwen/Qwen2.5-1.5B)引向其公开评测报告，但没有直接给出该模型可按本机口径复现的 C-Eval 分数。

因此本次最强的验证证据是**与本机内置实现逐题完全一致**。公开的 68.63% 提供量级参照；若要做严格的跨框架复现，还需锁定 OpenCompass 的数据划分、prompt、选项计分、模型权重与聚合方式。

## 原始结果与命令

- [Day 8 原始 0-shot](../runs/day08_ceval_computer_network_0shot/)
- [内置单科 0-shot](../runs/day09_ceval_builtin_0shot/)
- [自定义对齐 0-shot](../runs/day09_ceval_custom_aligned_0shot/)
- [内置完整组 5-shot](../runs/day09_ceval_full_5shot/)
- [自定义单科 5-shot](../runs/day09_ceval_custom_5shot/)

```powershell
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-1.5B,revision=8faed761d45a263340a0528343f099c05c9a4323,dtype=bfloat16' --tasks ceval-valid_computer_network --num_fewshot 0 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day09_ceval_builtin_0shot' --log_samples
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-1.5B,revision=8faed761d45a263340a0528343f099c05c9a4323,dtype=bfloat16' --tasks custom_ceval_computer_network_aligned --include_path '.\configs\tasks' --num_fewshot 0 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day09_ceval_custom_aligned_0shot' --log_samples
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-1.5B,revision=8faed761d45a263340a0528343f099c05c9a4323,dtype=bfloat16' --tasks ceval-valid --num_fewshot 5 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day09_ceval_full_5shot' --log_samples
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-1.5B,revision=8faed761d45a263340a0528343f099c05c9a4323,dtype=bfloat16' --tasks custom_ceval_computer_network_5shot --include_path '.\configs\tasks' --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day09_ceval_custom_5shot' --log_samples
```

## 面试回答

“我先检查数据字段与答案映射，用 19 道题做最小验证；再把模型、权重、题目、shot、seed 和指标固定，与 `lm-eval` 内置 C-Eval 逐题比较。最初差 1 题，我定位到任务 prompt 少了科目说明；补齐后 0-shot、5-shot 的每条请求和分数都与内置实现一致。最后跑 52 科完整验证集，并将结果与公开的 5-shot 数字作量级对照，同时明确跨框架评分口径尚未完全一致。”
