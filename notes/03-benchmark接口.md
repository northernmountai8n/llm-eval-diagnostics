# Day 3 笔记：一个样本如何从数据集变成分数

> 评测实现与行号以**本机安装的 lm-eval 0.4.13 源码**为准：
> `D:\program\miniconda\envs\lmeval\Lib\site-packages\lm_eval\`
>
> ⚠️ **凡与调研报告冲突处，以本文为准**（本文是源码实测，调研报告里有两处把归一化口径写成了"字节长度"，已在下文标注）。

## 完成范围与证据

- 本日重点是**解释评测口径**，不是又跑一组模型：数值来自 Day 2 保存的 0-shot 结果，见 `runs/day02_limit100/` 与 `runs/day02_limit500/`。
- 已核对本机 `arc_easy.yaml`、`ConfigurableTask`、`ContextSampler` 与结果 JSON；并阅读[官方 Task Guide](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/task_guide.md)。官方 `main` 文档可能与本机 0.4.13 不完全一致，涉及本次运行的细节以本机源码和结果文件为准。
- 本文末尾补了 HellaSwag、MMLU 的配置对照，回答 Day 3 目标中的三个任务有何不同。

---

## 一、`arc_easy.yaml` 逐字段

路径：`lm_eval/tasks/arc/arc_easy.yaml`（全文 23 行）

```yaml
tag: [ai2_arc]                                    # 任务组标签，用于 group 聚合
task: arc_easy                                    # ⭐ 任务是这个名字，命令行 --tasks arc_easy 匹配它
dataset_path: allenai/ai2_arc
dataset_name: ARC-Easy                            # 同一个 dataset_path 下的子配置
output_type: multiple_choice                      # ⭐ 决定走哪条 construct_requests / process_results 分支
training_split: train
validation_split: validation
test_split: test                                  # 默认评测 test split（2376 条）
doc_to_text: "Question: {{question}}\nAnswer:"    # 题干模板
doc_to_target: "{{choices.label.index(answerKey)}}"  # ⭐ 把 "B" 这样的答案键转成选项下标 int
doc_to_choice: "{{choices.text}}"                # 选项文本列表
should_decontaminate: true                        # 与训练集做去污（Day 13 相关）
doc_to_decontamination_query: "Question: {{question}}\nAnswer:"
metric_list:
  - metric: acc
    aggregation: mean
    higher_is_better: true
  - metric: acc_norm
    aggregation: mean
    higher_is_better: true
metadata:
  version: 1.0                                    # 输出表里的 Version 列
```

**两个容易看漏的点：**

1. **`doc_to_target` 最终返回 int 下标，不是选项文本。** `{{choices.label.index(answerKey)}}` 经模板渲染先得到字符串（如 `"1"`），`ConfigurableTask.doc_to_target` 在 `api/task.py:1253-1255` 将纯数字字符串转为整数 `1`。所以 `process_results` 在 `:1525` 走 `isinstance(gold, int)` 分支。注意：`--log_samples` 保存的 `target` 字段可能显示字符串 `"0"`，那是记录格式，不能据此断言内部比较时还是字符串。
2. **`metric_list` 同时列了 `acc` 和 `acc_norm`**，两者共用 `aggregation: mean`。这就是你 Day 2 跑出两行数字的原因——不是框架默认给两个，是 YAML 明确要求的。

---

## 二、ARC-Easy 是 **0-shot**

**YAML 里没有 `num_fewshot` 字段**，所以 `config.num_fewshot is None`，框架回退到 0：

```python
# api/task.py:337-341
fewshot_ctx = self.fewshot_context(
    doc,
    num_fewshot=0 if self.config.num_fewshot is None else self.config.num_fewshot,
    ...
)
```

实测印证：Day 2 的运行输出里 `n-shot = 0`，且日志行是 `num_fewshot: None`（None 是"未指定"，不是"用了 0"——两者在框架内部才被等价化）。

> 本机版本中，命令行把 ARC-Easy 改成 5-shot 且没有 `fewshot_split` 时，`api/task.py:924-930` 会**警告并回退**，`Task.fewshot_docs()` 再优先取 `train`（`:204-219`）。不会仅因缺少 `fewshot_split` 直接报错。官方 Task Guide 的说明与本机行为有差异，复现本次实验应按本机源码与运行日志理解。

---

## 三、⭐ `acc` vs `acc_norm`：到底除以什么

### 结论：除以**选项文本的字符数**（`len(choice)`）——不是字节数，也不是 token 数

源码（`api/task.py:1489-1568`，位于 `ConfigurableTask.process_results`）：

```python
elif self.OUTPUT_TYPE == "multiple_choice":
    lls, is_greedy = zip(*results, strict=True)

    choices = self.doc_to_choice(doc)
    completion_len = np.array([float(len(i)) for i in choices])              # :1494  ← ⭐ 字符数
    byte_length    = np.array([float(len(i.encode("utf-8"))) for i in choices])  # :1495  另一码事

    pred      = np.argmax(lls)                                               # :1510
    pred_norm = np.argmax(lls / completion_len)                              # :1511  ← ⭐ acc_norm 的核心
    pred_byte = np.argmax(lls / byte_length)                                 # :1512  ← acc_bytes 用的

    acc       = 1.0 if pred      == gold else 0.0                            # :1545
    acc_norm  = 1.0 if pred_norm == gold else 0.0                            # :1546
    acc_bytes = 1.0 if pred_byte == gold else 0.0                            # :1547
```

**关键区分：**

| 指标 | 除数 | 代码 |
|---|---|---|
| `acc` | 不除，直接比 logprob | `np.argmax(lls)` |
| **`acc_norm`** | **`len(choice)` — Python 字符数** | `np.argmax(lls / completion_len)` |
| `acc_bytes` | `len(choice.encode("utf-8"))` — UTF-8 字节数 | `np.argmax(lls / byte_length)` |

⚠️ **`acc_bytes` 是独立指标**，ARC-Easy 的 `metric_list` 里没有它，所以这次没算。但对**中文 benchmark 至关重要**（见第五节）。

### 它解决什么问题

`lls` 是「整段 continuation 的 log 概率之和」。较长选项通常包含更多 token，求和项往往更多，直接比较总和可能偏向短选项。按**字符数**相除是缓解长度影响的一种评测口径；字符数不等于 token 数，也不能保证完全消除长度偏差。这里分母是 YAML 中的选项文本长度，而推理时的 continuation 还带有 `target_delimiter` 插入的前导空格。

### 为什么 Day 2 实测两者会翻转

| limit | acc | acc_norm |
|---|---|---|
| 100 | 0.710 | **0.760** |
| 500 | **0.752** | 0.714 |

这 100 题是 500 题的前 100 题，**两行不是独立重复实验**。前 100 题 `acc` 答对 71 题、`acc_norm` 答对 76 题；扩大到 500 题后分别答对 376、357 题。因此新加入的 400 题分别答对 305/400（76.25%）和 281/400（70.25%），高低顺序随题目构成改变。单项标准误在 n=100 时约 4.3–4.6 个百分点，在 n=500 时约 1.9–2.0 个百分点；不能只凭这两行汇总值判断两种指标谁“显著更好”，也不能把嵌套样本的差异称为运行随机波动。

---

## 四、数据流：一个样本如何变成分数

```
数据集样本  (allenai/ai2_arc, ARC-Easy, test, 2376 条)
    │
    │   ┌─ doc_to_text ────→ ctx = "Question: <题干>\nAnswer:"
    │   ├─ doc_to_choice ──→ choices = ["<A>", "<B>", "<C>", "<D>"]
    │   └─ doc_to_target ──→ gold = choices.label.index(answerKey)   → int 下标
    ▼
ConfigurableTask.build_all_requests()                        api/task.py:332
    │
    │   fewshot_context(doc, num_fewshot=0)                   api/task.py:337-341
    │        └─ YAML 无 num_fewshot ⇒ config 为 None ⇒ 0
    │
    ▼
construct_requests()                                         api/task.py:1374-1445
    │
    │   target_delimiter = " "                                config/task.py:112（默认值，ARC 未覆盖）
    │   对每个选项各生成一条 Instance：
    │
    │       Instance(request_type="loglikelihood",
    │                arguments=(ctx, " " + choice),   ← ⚠️ 前导空格是评测口径的一部分
    │                idx=i)                           ← idx 记住"第几个选项"
    │
    ▼
通常每道题 4 条 Instance；若某题只有 3 个选项则为 3 条。
实测 limit=500 → 1998 条请求：498 道四选题 + 2 道三选题。
    │
    ▼
LM.loglikelihood(ctx, " " + choice)                          models/huggingface.py
    │
    │   返回 (Σ log P(continuation|ctx), is_greedy)
    │
    ▼
process_results(doc, results)                                api/task.py:1489-1568
    │
    │   lls, is_greedy = zip(*results)                       :1490
    │   completion_len = [len(c) for c in choices]           :1494   ⭐ 字符数
    │   pred      = argmax(lls)                              :1510
    │   pred_norm = argmax(lls / completion_len)             :1511   ⭐ acc_norm
    │
    ▼
每条样本产出 {acc: 0/1, acc_norm: 0/1}
    │
    ▼
aggregation = mean                                           api/metrics.py:34-36
    │   sum(arr) / len(arr)  →  100 条样本的 mean
    ▼
stderr                                                       api/metrics.py:337-343
    │
    │   mean_stderr(arr) = sample_stddev(arr) / sqrt(len(arr))
    │                    = sqrt( Σ(x-μ)² / (n-1) ) / sqrt(n)
    │                    = sqrt( p(1-p) / (n-1) )        ← ⭐ 贝塞尔校正，不是 /n
    │
    ▼
输出表：  |arc_easy | 1 | none | 0 | acc | ↑ | 0.710 | ± | 0.0456 |
```

**注**：`Filter` 列显示 `none`，因为 `arc_easy.yaml` 没有配置自定义 filter pipeline。执行顺序是**模型响应 → `apply_filters()` → `process_results()` → 聚合**（本机 `evaluator.py:615,639-640`）；filter 可做 `regex` 抽取、`take_first` 等，并不是在算完每题指标后才处理。

---

## 五、额外发现（两处值得单独记）

### 5.1 `stderr` 的精确公式 —— 源码级确认

Day 2 我是**从实测数值反推**出 `stderr = sqrt(p(1-p)/(n-1))` 的（吻合到 `2.1e-17`）。今天在源码里找到了直接证据：

```python
# api/metrics.py:337-343
def sample_stddev(arr):
    mu = mean(arr)
    return math.sqrt(sum([(x - mu) ** 2 for x in arr]) / (len(arr) - 1))   # ← n-1

def mean_stderr(arr):
    return sample_stddev(arr) / math.sqrt(len(arr))                        # ← 再除 sqrt(n)
```

对 0/1 数据有 `Σ(x-μ)² = n·p(1-p)`，代入即得 `sqrt(p(1-p)/(n-1))`。**反推与源码互相印证。**

另外 `evaluator_utils.py:221-222` 有个边界条件：

```python
stderr_fn(items) if (stderr_fn and len(items) > 1) else "N/A"
```

**n=1 时 stderr 是 `"N/A"`**——这与我在 `src/variance.py` 里把 `n <= 1` 返回 `nan` 的处理一致。

### 5.2 `acc_bytes` 的存在，对中文 benchmark 是大事

`acc_norm` 按**字符数**归一化，`acc_bytes` 按 **UTF-8 字节数**归一化。纯 ASCII 文本中二者等价；含中文时分母的数值会不同：

| 选项文本 | `len()` 字符数 | `len(encode('utf-8'))` 字节数 |
|---|---|---|
| `"北京"` | 2 | 6 |
| `"中华人民共和国"` | 7 | 21 |

但**分母不同不等于预测一定不同**。若同一道题的所有选项都只由三字节汉字组成，每个字节长度都是字符长度的 3 倍，两个指标的选项排序仍然相同。只有选项间的 UTF-8 字节/字符比例不同（如中文与 ASCII 混合、不同标点混合）时，二者的排序才**可能**改变。Day 8 接入 C-Eval / CMMLU 时应检查真实选项，而不能预设分数必变。

⚠️ **调研报告里的错误**（已核对源码，均为笔误）：
- `调研报告\大模型预训练评测体系_技术现状报告.md:403`：「按选项的**字节长度**归一化」← **错，是字符长度**
- `06-调研资料索引.md:36`：同上
- `调研报告\LLM评测框架与自动化研发_工程实践报告.md:232` 写的是「按**字符长度**归一化」← **这条是对的**
- 同文件 `:263` 写「字符（字节）长度」← 含糊，实际只有字符

**以源码为准：`acc_norm` = 除以字符数。**

---

## 六、面试话术（可直接用）

**Q：`acc` 和 `acc_norm` 有什么区别？**

> `acc` 直接比各选项 loglikelihood 之和取最大；`acc_norm` 先把这个和除以选项的**字符数**再比。
>
> 为什么要除：log 概率逐 token 累加，较长选项通常累加项更多，直接比可能偏向短选项。字符长度归一化是缓解这种影响的一种口径，但不等于严格按 token 数求平均。
>
> 我核过源码（lm-eval 0.4.13 `api/task.py:1494,1511`），除数确实是**字符数** `len(choice)`，不是字节数也不是 token 数——框架另有 `acc_bytes` 指标用 UTF-8 字节数做归一化；中英混合选项时两种口径可能改变排序。
>
> 而且这两个指标**不总是同向**。我在 Qwen2.5-1.5B / ARC-Easy 上实测：前 100 题 acc_norm 比 acc 高 5 个点，前 500 题反而低 3.8 个点——**汇总值的大小关系变了**。这两个样本集合是嵌套的，不能将差异当成独立运行波动；报告分数时必须写清样本范围和指标口径。

**Q（追问）：ARC-Easy 是几 shot？**

> 0-shot。`arc_easy.yaml` 里没有 `num_fewshot` 字段，框架在 `api/task.py:337-341` 对 `None` 回退到 0。它同时报 `acc` 和 `acc_norm` 两个指标，这是 YAML 的 `metric_list` 明确列的，不是框架默认行为。

---

## 七、实测验证（用本机缓存的 ai2_arc 数据集离线核对）

上面全是从源码读出来的。但"读到了"不等于"验证过"——下面用**本地缓存的真实数据**核对每一条断言。
（Day 2 评测的正是 test split 的前 100 条，所以这些就是模型真正看到的样本。）

### 7.1 样本 0 的真实打分文本 —— 复现 `construct_requests`

```
ctx = 'Question: Which statement best explains why photosynthesis is the foundation of most food webs?\nAnswer:'

idx=0  continuation=' Sunlight is the source of energy for nearly all ecosystems.'
idx=1  continuation=' Most ecosystems are found on land instead of in water.'
idx=2  continuation=' Carbon dioxide is more available than other gases.'
idx=3  continuation=' The producers in all ecosystems are plants.'

gold: answerKey='A' -> label.index('A') = 0
```

**模型算的是 `P(" Sunlight is..." | ctx)`，不是 `P("Sunlight is..." | ctx)`** —— 那个前导空格来自
`target_delimiter` 的默认值 `" "`（`config/task.py:112`）。换掉这个空格就是换了个评测口径。

### 7.2 选项长度确实差异很大（`acc` 与 `acc_norm` 不同的原因）

| 统计量 | 前 100 条 |
|---|---|
| 同题内选项字符长度**极差** | 最小 0 / **中位 6** / **最大 39** |
| 最长选项字符数 | 79 |

中位极差 6 个字符，而答案平均长度约 23 字符——**约 26% 的长度差异**。这说明选项长度足以影响两种打分口径；要确定某一道题为何翻转，还需查看该题各选项的 loglikelihood。

### 7.3 ⚠️ 但"正确选项更短"这个直觉**不成立**

| | 前 100 条平均字符长度 |
|---|---|
| **正确**选项 | **23.08** |
| 错误选项 | 22.63 |
| 差值 | **−0.45**（正确选项反而略长） |

调研报告里"长选项天然更负，所以 `acc` 偏袒短选项"这句话描述的是**机制**（没错），但**不能推出**
"benchmark 里正确答案更短"。我实测的是正确选项**略长**。

所以更稳妥的表述是：`acc` 的总对数概率比较**可能**对长选项不利；这种影响是否有利于正确答案取决于数据，**不能预设方向**。`acc_norm` 用字符长度作近似调整，但不能保证完全消除 token 数、分词方式等因素的影响。

### 7.4 ⭐ 连"纯英文"基准都有非 ASCII 字符

扫描 ARC-Easy 全部三个 split（5197 条）：

```
含非 ASCII 字符的样本: 66 / 5197
```

| 字符 | 码位 | 次数 | 名称 |
|---|---|---|---|
| `°` | U+00B0 | 116 | DEGREE SIGN |
| `•` | U+2022 | 14 | BULLET |
| `’` | U+2019 | 8 | RIGHT SINGLE QUOTATION MARK |
| `º` | U+00BA | 3 | MASCULINE ORDINAL INDICATOR |
| `ñ` | U+00F1 | 3 | LATIN SMALL LETTER N WITH TILDE |
| `“` `”` | U+201C/201D | 各 1 | 弯引号 |
| `™` | U+2122 | 1 | TRADE MARK SIGN |
| `µ` | U+00B5 | 1 | MICRO SIGN |

样例：`If 1 kg of the compound toluene melts at -95°C, ...`（`train#67`）

**三个后果：**

1. **`acc_norm` 与 `acc_bytes` 在这些文本上的分母可能不同**（`°` 是 1 字符 / 2 字节）。前 100 条里有 1 条含非 ASCII 字符；是否改变最终预测还要比较该题各选项的实际长度比例与 loglikelihood。
2. **tokenization 受影响**：`°C` 与 `C` 不是同一个 token 序列，`-95°C` 的 token 数可能与预期不同。
3. **这是 Day 11「编码与脏字符」检查的真实素材**——`src/data_audit.py` 的第 6 类检查（全角/零宽/混用）
   在这里有了非虚构的命中案例，可以写进报告。

> 复现脚本思路：`load_dataset("allenai/ai2_arc", "ARC-Easy")`（离线用缓存），
> 对 `question / answerKey / choices.text / choices.label` 逐字符扫 `ord(c) > 127`。

---

## 八、官方 Task Guide 与另两个任务的口径

[官方 Task Guide](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/task_guide.md) 把任务配置分成数据集、prompt、评分、filter 等部分。复现一个分数，需要同时保留 YAML 配置与框架版本：只说“跑了 ARC-Easy”不足以还原 prompt 和判分方式。`doc_to_text` 组织题目，`doc_to_choice` 给出候选答案，`doc_to_target` 定义正确答案；`output_type: multiple_choice` 使框架分别计算各候选续写的 loglikelihood。若有 filter，它先处理模型响应，之后才逐题判分与聚合。官方文档还介绍 `!function` 预处理、YAML `include` 及 `filter_list`；未来可参考[去污染说明](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/decontamination.md)和[常见陷阱](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/footguns.md)。

本机 0.4.13 的三个任务配置对照（**以下是配置阅读结果，不是三个任务都已实测**）：

| 任务 | 评测集 / few-shot 来源 | 题目与候选答案 | 输出指标 |
|---|---|---|---|
| ARC-Easy | `test` / 未指定时回退 `train`；默认 0-shot，命令行可改 5-shot | `Question: ...\nAnswer:`；候选为选项全文 | `acc`、`acc_norm` |
| HellaSwag | `validation` / 未指定时回退 `train` | `process_docs` 先整理文本；候选为句子续写 | `acc`、`acc_norm` |
| MMLU 默认任务组 | 各学科 `test` / `dev`；`first_n` 取示例，具体 shot 数由运行配置决定 | 题干列出 A–D；候选是字母 `A/B/C/D` | 各学科 `acc`，任务组按样本量加权聚合 |

MMLU 在本机不是单个 `mmlu.yaml`：任务组定义在 `tasks/mmlu/default/_mmlu.yaml`，学科模板在 `tasks/mmlu/default/_default_template_yaml`。HellaSwag 的配置在 `tasks/hellaswag/hellaswag.yaml`。它们的 prompt、候选答案形式与 ARC-Easy 不同，因此不能把不同任务的分数直接当成同一种能力量尺。

---

## Day 4 衔接（截至 2026-09-25）

- [x] 已有 0-shot、500 题基线；5-shot、500 题结果保存在 `runs/day04_arc_easy_5shot_seed1234/`。
- [x] 已查看首题 prompt：前 5 道训练集示例各有答案，最后的测试题停在 `Answer:`，各选项另作为 continuation 打分。
- [x] 已核对 HellaSwag 配置及 few-shot 回退规则；缺失的 `fewshot_split` 不会阻止 ARC-Easy 的 5-shot 运行。
- [x] 已核对种子：`--seed 0,1234,1234,1234` 的第四位控制 few-shot 抽样；本机 `api/task.py:560-563` 把它传给 sampler，`api/samplers.py:57-62` 随机无放回取示例。
- [x] Day 4 的结果对照表、运行台账与面试题草稿已归档，见 `runs/day04_comparison.md`、`RUNS.md`、`notes/04-fewshot与prompt.md`。
- [ ] 不同 seed 的三次运行是加餐；当前只完成 seed 1234，尚不能报告 seed 波动范围。
