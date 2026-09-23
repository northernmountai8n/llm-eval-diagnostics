# Day 3 笔记：一个样本如何从数据集变成分数

> 全部结论来自**本机安装的 lm-eval 0.4.13 源码**，行号可直接跳转核对：
> `D:\program\miniconda\envs\lmeval\Lib\site-packages\lm_eval\`
>
> ⚠️ **凡与调研报告冲突处，以本文为准**（本文是源码实测，调研报告里有两处把归一化口径写成了"字节长度"，已在下文标注）。

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

1. **`doc_to_target` 返回的是 int 下标，不是文本。** `{{choices.label.index(answerKey)}}` 在 Jinja 里对 `choices.label`（如 `["A","B","C","D"]`）调 `.index("B")`，得到 `1`。所以 gold 是整数，后面 `task.py:1525` 走的正是 `isinstance(gold, int)` 分支。
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

> 顺带一个校验规则：如果 YAML 里写了 `num_fewshot > 0` 却没写 `fewshot_split`，框架会直接报错（`api/task.py:924-927`）。

---

## 三、⭐ `acc` vs `acc_norm`：到底除以什么

### 结论：除以 **continuation 的字符数**（`len(str)`）——不是字节数，也不是 token 数

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

`lls` 是「整段 continuation 的 log 概率之和」。选项文字越长，token 越多，求和项越多，log 概率和**天然更负**。直接比大小 → 系统性偏向短选项。除以长度，是把这个"项数效应"折掉，让比较落回"平均每个字符的似然"。

### 为什么 Day 2 实测两者会翻转

| limit | acc | acc_norm |
|---|---|---|
| 100 | 0.710 | **0.760** |
| 500 | **0.752** | 0.714 |

长度差异在样本量小时更容易被噪声掩盖或放大——**n=100 的 95% 置信区间宽达 18 个百分点**，足够容纳两个方向的结论。这正说明"口径差异"和"样本量"两个因素必须一起看。

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
每道题 4 条 Instance（实测 limit=100 → 约 399 条请求，即 100×4 减去末尾）
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

**注**：`Filter` 列显示 `none`，因为 `arc_easy.yaml` 没有配置 filter pipeline。filter 的作用是在 `process_results` **之后**对输出做再加工（如 `regex` 抽取、`take_first`），ARC 不需要。

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

`acc_norm` 按**字符数**归一化，`acc_bytes` 按 **UTF-8 字节数**归一化。对纯英文两者等价（1 字符 = 1 字节）；**对中文完全不同**：

| 选项文本 | `len()` 字符数 | `len(encode('utf-8'))` 字节数 |
|---|---|---|
| `"北京"` | 2 | 6 |
| `"中华人民共和国"` | 7 | 21 |

所以 Day 8 接入 **C-Eval / CMMLU** 时，这个选择会直接改变分数：两个中文选项如果字符数相同但字节数差 3 倍，`acc_norm` 和 `acc_bytes` 会给出**方向不同**的判断。

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
> 为什么要除：log 概率是逐 token 累加的，选项越长求和项越多、logprob 和天然越负，直接比会**系统性偏向短选项**。除以长度是把"项数效应"折掉。
>
> 我核过源码（lm-eval 0.4.13 `api/task.py:1494,1511`），除数确实是**字符数** `len(choice)`，不是字节数也不是 token 数——框架另有 `acc_bytes` 指标用 UTF-8 字节数做归一化，两者在中文上会给出不同结论。
>
> 而且这两个指标**不总是同向**。我在 Qwen2.5-1.5B / ARC-Easy 上实测：limit=100 时 acc_norm 比 acc 高 5 个点，limit=500 时反而低 3.8 个点——**大小关系翻转了**。所以报告分数时必须写清用哪个口径。

**Q（追问）：ARC-Easy 是几 shot？**

> 0-shot。`arc_easy.yaml` 里没有 `num_fewshot` 字段，框架在 `api/task.py:337-341` 对 `None` 回退到 0。它同时报 `acc` 和 `acc_norm` 两个指标，这是 YAML 的 `metric_list` 明确列的，不是框架默认行为。

---

## 待办（Day 4 衔接）

- [ ] 亲手跑 `--num_fewshot 0` / `5` 对照，验证 few-shot 示例是怎么从 `train` split 抽的
- [ ] 读 `lm_eval/tasks/hellaswag/hellaswag.yaml`，找 `fewshot_split` / `fewshot_delimiter`
- [ ] 确认 `--seed` 到底影响什么（日志显示 four seeds: 0 / 1234 / 1234 / 1234）
