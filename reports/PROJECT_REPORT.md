# 项目报告｜LLM 评测可靠性与错误诊断

## 问题与范围

一个模型跑出分数后，还需要回答三件事：**这个分数按什么规则得到？换评测设置会不会改变它？变化落在哪些题和哪些能力上？**本项目围绕 Qwen2.5 base 0.5B、1.5B、3B 建立有限样本评测记录，用 `lm-evaluation-harness` 跑五项任务，随后对数据、提示词、答案抽取、few-shot seed、跨框架口径和错题进行诊断。它是评测工程实践，不能充当完整基准榜单。

## 方法

模型权重固定为 40 位 revision，主实验统一使用 `bfloat16`、`batch_size=1`、`cuda:0`、种子 `0,1234,1234,1234`；三款模型使用同一任务口径，并保存逐题日志。MMLU 取 57 个学科各前 10 题、5-shot，共 570 题；GSM8K 取测试集前 200 题、5-shot、`strict-match`；其他任务的 shot、题数和指标见[主结果表](../results/main_table.md)。后续实验逐项控制变量：同题改提示词或抽取规则；固定题目只改 few-shot seed；C-Eval 对齐自定义与内置任务，再对照 OpenCompass；按 MMLU 学科类别汇总，并固定种子从 GSM8K 错题中抽 50 题人工分类。

## 主要结果

| 观察 | 证据 | 该怎么理解 |
| --- | --- | --- |
| MMLU 570 题：0.5B **49.12%**、1.5B **65.96%**、3B **70.70%** | [Day 6 主结果](../results/main_table.md)；[分学科图](day20_mmlu_by_category.svg) | 在相同有限样本上，大模型分数较高；从 1.5B 到 3B，STEM 从 **57.37%** 到 **68.42%**，其他类别的增幅较小。 |
| GSM8K 改提示词后，1.5B 从 **124/200** 变成 **117/200** | [逐题配对与抽取审计](12-extraction-and-prompt.md) | 总差 **−3.5 个百分点**，其中 12 题错变对、19 题对变错；不是每题都退步，也不能据一次实验推广到其他模型。 |
| ARC-Easy 200 题、5-shot、五个示例 seed：`acc` 均值 **0.7670**、seed 间标准差 **0.0125** | [方差图](figures/variance.svg)；[方差报告](17-variance.md) | 只改示例 seed 也会出现分数波动；这与单次运行的逐题标准误不是一回事。 |
| GSM8K 从 76 道错题随机抽 50 道：指令误解 **25**、推理断裂 **20**、格式错误 **2**、题目/参考答案问题 **2**、知识缺失 **1** | [错题图](day20_error_categories.svg)；[逐题标签与简要证据](day20_manual_labels.json) | 分类比例只描述这 50 道已判错题；两道题的题意或金标准需进一步复核，不能直接给模型加分。 |

数据审计发现 C-Eval 计算机网络 `val` 19 题和 MMLU abstract algebra `test` 100 题的答案字段均合法，但近重复、位置偏置、异常长度等提示需要人工看原文，不能把提示数量当作已证实错误；见 [Day 11 报告](day11_ceval_computer_network.md)、[MMLU 报告](day11_mmlu_abstract_algebra.md)。GSM8K 的 13-gram 检查在 200 道测试题内部、及测试题对实际使用的 few-shot 示例中均未检出字面连续重叠；这**不能证明**模型预训练语料没有污染，见[污染报告](13-contamination.md)。

## 框架对照与工程结论

自定义 C-Eval 任务补齐科目说明后，0-shot 与 `lm-eval` 内置任务在 19 题上逐题一致。OpenCompass 0.5.4 在同一模型、同一 C-Eval 科目 19 题的 5-shot 运行得到 **15/19**，已有 `lm-eval` 结果为 **14/19**；两者完整 prompt、候选评分和并列规则不同，不能把这一题差距写成框架性能优势。详细配置与预测见[OpenCompass 实跑](19-opencompass-qwen15-ceval19.md)。

项目给出的实务顺序是：**先核对评测链路与可比性，再分组和逐题看分数，最后才推断模型能力**。同分可能掩盖逐题翻转；`[invalid]` 可能是输出未完成或格式不符；答案金标准也需要复核。对 Agent 评测，SWE-bench、GAIA、τ-bench、Terminal-Bench 的任务流程与验收器不同，本项目目前只完成[范式笔记](../notes/20-agent-benchmark.md)，没有宣称实测这些基准。

## 局限与复现

多数实验采用测试集前缀 `--limit`；题量有限，且 MMLU 每学科只取 10 题。50 道错题的单主类标注含人工判断；数据没有可信的逐题难度标签。本项目比较的是不同大小的最终模型，不是同一训练过程的 checkpoint；DeepSeek Flash 的 50 题 API 试验也与本地 Qwen MMLU 的题目、shot 和判分方式不同。项目代码、固定模型 revision 和环境版本见[README](../README.md)、[模型清单](../results/day06_models.json)、[环境依赖](../requirements.txt)；全部主运行命令见[实验台账](../RUNS.md)。原始大体积日志不入 Git，重建图表需先重跑对应实验。
