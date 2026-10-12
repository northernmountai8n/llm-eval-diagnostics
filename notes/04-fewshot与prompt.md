# Day 4 笔记：few-shot 与 prompt 会怎样改变分数

## 今日问题与一句话结论

**问题**：同一模型、同一任务、同一批测试题，只把提示词从 0-shot 改成 5-shot，分数会怎样变化？

**观察**：Qwen2.5-1.5B 在 ARC-Easy 前 500 道测试题上，`acc` 从 75.2% 到 79.8%，`acc_norm` 从 71.4% 到 80.2%。这是当前配置下的实验观察，不是“5-shot 在所有模型和任务上必然更好”的结论。

## 一、实验设置与结果

两组共用 `Qwen/Qwen2.5-1.5B` 权重 SHA `8faed761d45a263340a0528343f099c05c9a4323`、ARC-Easy 配置版本 1、`test` 前 500 题、`batch_size=1` 和 `cuda:0`。0-shot 复用 Day 2 已保存的基线，Day 4 只新增一次 5-shot 运行。模型、任务版本、题数、设备和 batch size 已从两份原始 JSON 对照核验。结果文件见 [`runs/day04_comparison.md`](../runs/day04_comparison.md)，命令与时间见自动生成的 [`RUNS.md`](../RUNS.md)。

| 设置 | 题数 | `acc` | `acc_norm` |
|---|---:|---:|---:|
| 0-shot，few-shot seed 1234（未抽示例） | 500 | 75.2%（376/500） | 71.4%（357/500） |
| 5-shot，few-shot seed 1234 | 500 | 79.8%（399/500） | 80.2%（401/500） |
| 5-shot 减 0-shot | 同一批题 | **+4.6 个百分点** | **+8.8 个百分点** |

`acc` 和 `acc_norm` 是**两种不同的选项排序口径**，比较时必须同列相减。0-shot 与 5-shot 的 `acc` 净差是 23 道，`acc_norm` 净差是 44 道；它们是答对题数的**净变化**，不能据此推断具体有多少道题从错变对，因为 0-shot 没有保存逐题样本。

5-shot 输出的 `acc_stderr=0.0180`、`acc_norm_stderr=0.0178` 是各自分数的标准误，不能直接当作 0-shot 与 5-shot **差值**的标准误。`--limit 500` 只覆盖完整测试集 2376 题中的前 500 题；运行时的 `--limit SHOULD ONLY BE USED FOR TESTING` 是提醒不要把它当完整榜单成绩，不表示运行失败。

### 可复现命令（PowerShell）

```powershell
& 'D:\program\miniconda\shell\condabin\conda-hook.ps1'
conda activate lmeval
Set-Location 'D:\桌面\个人\工程\llm-eval-diagnostics'
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-1.5B,revision=8faed761d45a263340a0528343f099c05c9a4323' --tasks arc_easy --num_fewshot 5 --limit 500 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day04_arc_easy_5shot_seed1234' --log_samples
```

命令已跑完，日常复习无需重跑。`Overwriting default num_fewshot ... from None to 5` 表示命令覆盖了任务默认 shot 数。500 题一共产生 1998 条 loglikelihood 请求：498 题有 4 个选项，2 题有 3 个；**1998 是候选答案请求数，500 是题数**。

终端结果表中，`Version=1` 是 ARC-Easy YAML 的版本号，`Filter=none` 表示本任务没有自定义响应过滤流水线，`n-shot=5` 是当前 prompt 前置的示例数。`acc` 和 `acc_norm` 是 500 题逐题 0/1 得分的平均值，`Stderr` 是每一列均值自己的标准误。未登录 HF Hub 的提示只涉及请求限额，与已保存的本地评测结果无关。

## 二、模型实际看到的 prompt：最后的 `Answer:` 为什么留空

逐题记录在本地生成的 `runs/day04_arc_easy_5shot_seed1234/Qwen__Qwen2.5-1.5B/samples_arc_easy_*.jsonl`（原始日志不入库）。首题的 `arguments.gen_args_0.arg_0` 是所有选项共用的上下文，结构是：

```text
Question: Which of these resources will most likely be depleted first?
Answer: Fossil fuels

...（中间还有 4 个带答案的训练示例）...

Question: Which statement best explains why photosynthesis is the foundation of most food webs?
Answer:
```

前 5 组是示范；**第 6 组是测试题，答案刻意留空**，否则就泄露标准答案。框架并不在这里自由生成答案，而是把每个候选文本分别作为 `arguments.gen_args_i.arg_1` 接在末尾，用 `loglikelihood` 给候选续写打分。候选文本前的空格来自默认 `target_delimiter = " "`；`acc_norm` 的分母却只算选项文本的字符数，不计这个前导空格。

首题的真实打分如下。loglikelihood 越大（负数越接近 0）越好；`acc_norm` 先除以选项字符数再比较：

| 选项 | 原始 loglikelihood | 选项字符数 | 每字符分数（约） |
|---|---:|---:|---:|
| A | **−23.375** | 59 | **−0.3962** |
| B | −37.000 | 54 | −0.6852 |
| C | −33.250 | 50 | −0.6650 |
| D | −27.750 | 43 | −0.6453 |

两种口径都选 A；数据集的正确标签也是 A，因此首题 `acc=1`、`acc_norm=1`。可以在 PowerShell 中查看同一条记录：

```powershell
$s = Get-ChildItem '.\runs\day04_arc_easy_5shot_seed1234' -Recurse -Filter 'samples_arc_easy_*.jsonl' | Select-Object -First 1
$x = Get-Content $s.FullName -TotalCount 1 | ConvertFrom-Json
$x.arguments.gen_args_0.arg_0  # 五个示例 + 待评测题
$x.arguments.gen_args_0.arg_1  # 候选 A，注意开头空格
$x.doc.answerKey               # 标准答案；此字段没有放进待评测 prompt
```

## 三、few-shot 来源、分隔符与种子

- 本机 `hellaswag.yaml` 和 `arc_easy.yaml` 都未显式设置 `fewshot_split` / `fewshot_delimiter`。这两个**是可配置的 YAML 字段**，此处只是没有写，所以使用默认值：`fewshot_split=None`、`fewshot_delimiter="\n\n"`、`target_delimiter=" "`。未指定 `num_fewshot` 时等价于 0-shot。
- 本机 0.4.13 对 `num_fewshot > 0` 且没有 `fewshot_split` 的 ARC-Easy 给出警告，再经 `Task.fewshot_docs()` 优先回退到 `training_split=train`，不是报错。HellaSwag 也是 `training_split=train`，但本日**没有运行 HellaSwag 分数**，只阅读了它的 YAML。相关本机源码：`config/task.py:97-116`、`api/task.py:204-219,924-930`。
- `--seed 0,1234,1234,1234` 的顺序是 Python、NumPy、Torch、few-shot。第四位通过 `set_fewshot_seed()` 注入 sampler；默认 sampler 在 `api/samplers.py:57-62` 使用随机无放回抽样。对于本次确定性 loglikelihood 评测，第四位直接决定抽到哪些示例；前三位保留固定值，避免引入别的随机差异。

**离线抽样核对**：本地 ARC-Easy `train` 有 2251 题。对首道测试题按默认 sampler 取 5 个示例，seed 1234 的训练集下标是 `[1805, 478, 30, 371, 143]`，与保存的首题 prompt 一致；若只把 few-shot seed 改成 42，下标变为 `[456, 102, 1126, 1003, 914]`，这两组首题示例**重叠 0 个**。这是对抽样机制的离线验证，**不是 seed 42 的模型评测结果**。随着测试题推进，sampler 状态也会推进，因此同一轮中不同测试题通常取到不同示例；固定 seed 才能复现整轮抽样顺序。

本次只完成了 few-shot seed 1234 的一次 5-shot 模型运行。计划里的“三个 seed 看分数波动”是加餐，还不能填写波动范围。

## 四、面试题草稿：模型 A 比 B 高 2 分，能说 A 更强吗？

不能只看“高 2 分”。先确认两者使用相同的测试题、prompt、shot 数、few-shot 示例或种子、评分指标、模型版本和框架版本；再看样本量与逐题结果。若评测同一批题，应比较逐题对错并做配对分析，而不是仅凭两个汇总分数或各自的 `stderr` 下结论。还要检查 few-shot seed 和任务选择的敏感性。只有在这些口径一致且差异足够稳定时，才能限定地说“A 在这套评测上更好”，不能直接推广成“A 在所有能力上更强”。本次同一模型从 0-shot 到 5-shot 的提升就是评测设置会影响结论的例子。

## 五、完成检查与后续

- [x] 同模型、同任务、500 题的 0-shot / 5-shot 对照与原始结果。
- [x] 查看 HellaSwag YAML、默认分隔符和 few-shot 来源；抽查真实 5-shot prompt。
- [x] 确认并记录四个 seed 的顺序及 few-shot seed 作用。
- [x] 对照表保存到 `runs/`，5-shot 运行登记到 `RUNS.md`。
- [x] 面试题答案草稿。
- [ ] 加餐：另用两个不同 few-shot seed 运行，合计三个 seed 比较分数范围。
