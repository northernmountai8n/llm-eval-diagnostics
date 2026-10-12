# Day 4：ARC-Easy 0-shot 与 5-shot 对照

同一模型 `Qwen/Qwen2.5-1.5B`，权重 SHA `8faed761d45a263340a0528343f099c05c9a4323`；同一任务配置版本 1、`test` 前 500 题、`batch_size=1`、`cuda:0`。`acc` 与 `acc_norm` 分别比较，不能交叉相减。

| shot | few-shot seed | 题数 | acc | acc_norm | 原始结果 |
|---:|---:|---:|---:|---:|---|
| 0 | 1234（未抽示例） | 500 | 0.752（376/500） | 0.714（357/500） | 本地 `runs/day02_limit500/Qwen__Qwen2.5-1.5B/results_*.json` |
| 5 | 1234 | 500 | 0.798（399/500） | 0.802（401/500） | 本地 `runs/day04_arc_easy_5shot_seed1234/Qwen__Qwen2.5-1.5B/results_*.json` |

在这 500 道题上，5-shot 的 `acc` 高 **4.6 个百分点**，`acc_norm` 高 **8.8 个百分点**。两次都只评测完整测试集 2376 题中的前 500 题，所以这是受限样本下的对照，不能当作完整 ARC-Easy 榜单成绩。两列 `stderr` 是各自分数的标准误，不能直接当成上述差值的标准误；0-shot 未保存逐题输出，当前无法从这两份汇总 JSON 做配对显著性检验。

5-shot 的逐题记录保存在本地 `runs/day04_arc_easy_5shot_seed1234/Qwen__Qwen2.5-1.5B/samples_arc_easy_*.jsonl`；原始结果和逐题文件不入库。其中首题 prompt 含 5 个已回答的训练样例，测试题只到 `Answer:`；每个候选答案作为独立 continuation 计算 loglikelihood。500 题共 1998 条请求，因为 498 题有 4 个选项，2 题有 3 个。
