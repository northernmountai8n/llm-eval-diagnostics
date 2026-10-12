# Day 18｜DeepSeek Flash 的 MMLU 50 题 API 小实验

- 状态：完成。
- 数据：`cais/mmlu` / `all` / `test`；revision `c30699e8356da336a370243923dbaf21066bb9fe`，共 14042 道测试题。
- 抽样：固定种子 20261009，从整个 test 集简单随机、不放回抽取 50 题；覆盖 26 个学科。题号、源数据索引和哈希见 `data/day18_mmlu_flash50.manifest.json`。
- 标准答案位置分布：{'A': 13, 'B': 10, 'C': 11, 'D': 16}。沿用源数据原文；可见编码异常待复核题 ID：[1]。
- 设置：0-shot 英文四选一提示词；请求模型 `deepseek-flash`；非思考模式、`temperature=0`、`max_tokens=16`；每题只接受原始回复去掉首尾空白后恰为大写 `A`/`B`/`C`/`D`。
- 指标：答对数 / 50；多余文字、小写字母和其他格式记为格式无效并计错。这个口径与项目之前 5-shot、选项似然判分的 Qwen MMLU 实验不同。

## 结果

- 正确：**42/50 = 84.0%**。
- 95% Wilson 近似区间：**71.5%～91.7%**。这是 50 题抽样的不确定性提示，不是模型在完整 MMLU 上的保证。
- 格式无效：0/50；因输出长度截断：0/50。

- API 实际返回的 `model`：['deepseek-flash']；`system_fingerprint`：['aeb56401ca74e127821c4f9126dcb669']。
- API 用量：completion_tokens=50；prompt_cache_hit_tokens=0；prompt_tokens=6835；total_tokens=6885。

### 错题与格式异常（最多列前 10 条）

| ID | 学科 | 标准答案 | 原始回复 |
| ---: | --- | :---: | --- |
| 6 | elementary_mathematics | B | D |
| 7 | high_school_statistics | B | A |
| 9 | high_school_chemistry | C | B |
| 10 | professional_law | C | A |
| 23 | high_school_mathematics | B | A |
| 24 | high_school_statistics | C | D |
| 32 | moral_scenarios | A | B |
| 40 | moral_scenarios | A | B |

## 解读边界

- 这是 50 题的探索性 0-shot API 实验，不是官方 MMLU 全量分数；样本少、跨学科，每学科题数也很少。
- 严格单字母判分同时检验知识和输出格式；若要与其他模型公平比较，需让它们使用完全相同的题目、提示词、抽取规则和推理设置。
- `deepseek-flash` 是服务端模型名，具体服务版本可能变化；因此保存实际响应模型和指纹（如果 API 提供）。温度为 0 也不保证跨服务版本逐位一致。
- `usage` 是 API 返回的 token 数，不等于已核实的账单金额。重试还可能产生额外用量。

原始题目：`data/day18_mmlu_flash50.jsonl`；原始响应：`runs/day18_deepseek_mmlu50.jsonl`。
