# Day 6 主结果表：三种模型规模 × 五项任务

数据直接核对自 `runs/day06_*` 下的 15 份 `results_*.json`；每份运行的完整命令、时间、环境和结果路径见 [`RUNS.md`](../RUNS.md)。这是使用 `--limit` 的**有限样本试跑**，不能当作完整 benchmark 成绩或公开榜单排名。三种模型都是 Qwen2.5 基础模型，本表比较的是**同一家族的规模变化**，不是不同模型家族。

| 模型 | ARC-Easy `acc` | HellaSwag `acc_norm` | MMLU `acc` | GSM8K `exact_match,strict-match` | TruthfulQA MC2 `acc` |
|---|---:|---:|---:|---:|---:|
| Qwen2.5-0.5B | 0.5950 | 0.5250 | 0.4912 | 0.2900 | 0.4022 |
| Qwen2.5-1.5B | 0.7150 | 0.6200 | 0.6596 | 0.6200 | 0.4666 |
| Qwen2.5-3B | 0.7250 | 0.6350 | 0.7070 | 0.7300 | 0.4762 |

## 评测口径

| 任务 | 实际使用的样本 | shot 数 | 表中指标的含义 |
|---|---:|---:|---|
| ARC-Easy | 测试集前 200 题 | 0 | 原始候选 loglikelihood 排名的逐题正确率；另有 `acc_norm`，本表未混用。 |
| HellaSwag | 验证集前 200 题 | 0 | 按选项长度归一化后排名的逐题正确率；另有 `acc`。 |
| MMLU | 57 个子任务各取前 10 题，共 570 题 | 5 | `mmlu` 组的汇总正确率；5-shot 已在每个子任务的 `n-shot` 中核对。 |
| GSM8K | 测试集前 200 题 | 5 | `strict-match` 答案提取后的 exact match；另有 `flexible-extract`，三模型分别为 0.2950、0.6200、0.7600。 |
| TruthfulQA MC2 | 验证集前 200 题 | 框架 `num_fewshot=0` | **不是 0/1 逐题正确率**。本机 `utils.process_results_mc2()` 将候选 loglikelihood 转为归一化概率，再汇总正确答案集合的概率质量；表中是该值的样本平均。任务模板另含固定问答示例。 |

共同设置：`batch_size=1`、`device=cuda:0`、`dtype=bfloat16`、`seed=0,1234,1234,1234`，未启用 `--apply_chat_template`，均保存了 `--log_samples` 的逐题输出。三模型权重 revision 固定在 [`day06_models.json`](day06_models.json)；各项实际命令和结果路径在 [`RUNS.md`](../RUNS.md)。

## 完成与解读

- 15 个“模型 × 任务”组合各有一份结果 JSON 和对应的台账记录；没有重复组合或缺失结果文件。MMLU 每次保存 57 个子任务的逐题 JSONL，其他任务每次各保存一个。
- 在这些**相同任务口径的有限样本**上，3B 的五列数值均高于 1.5B，1.5B 的五列数值均高于 0.5B。这是本次试跑的观察，不能据此推断所有任务或完整测试集也必然如此。
- 不要跨列直接比较数字。例如 MMLU 的 0.7070 与 TruthfulQA MC2 的 0.4762 测量内容和计分方法不同。
