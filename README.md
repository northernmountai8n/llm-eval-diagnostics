# llm-eval-diagnostics

面向基础语言模型的**可复现评测与问题诊断**项目。它不只记录一个总分，还保留题目、提示词、模型版本、评分规则和逐题结果，用来回答：分数为何变化、变化是否来自模型，以及不同评测工具的结果能否比较。

## 项目做了什么

1. 用 `lm-evaluation-harness` 对固定 revision 的 Qwen2.5 base 0.5B、1.5B、3B 运行 ARC-Easy、HellaSwag、MMLU、GSM8K、TruthfulQA MC2 的有限样本实验；保存运行台账、配置和逐题日志。
2. 接入 C-Eval，自定义任务与 `lm-eval` 内置任务逐题对拍；用 OpenCompass 再跑同科目，检查两框架的提示词、候选评分与并列处理差异。
3. 审计数据质量、GSM8K 答案抽取和提示词改动、13-gram 文本重叠，以及 five-shot 示例 seed 带来的分数波动。
4. 把 MMLU 按学科类别拆分，人工复核 50 道 GSM8K 错题，并记录 Agent 评测与静态题库评测的差别。

完整方法、结果和边界见[两页项目报告](reports/PROJECT_REPORT.md)；逐项运行参数见[实验台账](RUNS.md)。

## 三个核心结果

| 实验 | 可核对的观察 | 解读边界 |
| --- | --- | --- |
| 三种 Qwen2.5 base 规模 | 同一批 MMLU 570 题、5-shot：0.5B **49.12%**，1.5B **65.96%**，3B **70.70%**；见[主结果表](results/main_table.md) | 每科只取前 10 题，不能代替完整 MMLU 或公开榜单。 |
| GSM8K 提示词 | 同一 200 题、同一模型和 seed；把 `Answer:` 改为 `Answer: Let's think step by step.` 后，严格抽取从 **124/200** 变为 **117/200**；见[对照报告](reports/12-extraction-and-prompt.md) | 这是一次配对的小样本观察，不能宣称该提示词普遍更差。 |
| few-shot seed 波动 | ARC-Easy 200 题、5 个 seed 的 `acc` 均值 **0.7670**、seed 间标准差 **0.0125**；见[方差报告](reports/17-variance.md) | 只有 5 个 seed；seed 间标准差与单次逐题 `stderr` 衡量不同来源。 |

三张图分别展示分数波动、能力维度与错题结构：

- [五个 seed 的分数波动](reports/figures/variance.svg)：点是单次 seed，线和误差线是均值 ± seed 间标准差；各面板纵轴范围不同。
- [MMLU 学科类别与模型规模](reports/day20_mmlu_by_category.svg)：同一批 570 题的四类结果。
- [GSM8K 50 道错题的主要类别](reports/day20_error_categories.svg)：比例的分母是抽出的错题，不是全部题。

## 环境与复现

以下命令面向 Windows PowerShell 和 NVIDIA GPU。项目用 Python 3.11；本机主环境的版本写在 [`requirements.txt`](requirements.txt)，PyTorch CUDA wheel 单独安装。模型权重、Hugging Face 数据集和原始 `runs/` 日志体积较大，未纳入 Git；**新克隆的仓库不能只运行分析脚本就重新算出全部图表，须先生成对应日志**。

```powershell
Set-Location '<你的仓库目录>\llm-eval-diagnostics'
conda create -n lmeval python=3.11 -y
conda activate lmeval
python -m pip install torch==2.14.0+cu126 --index-url https://download.pytorch.org/whl/cu126
python -m pip install -r .\requirements.txt
$env:HF_HOME = Join-Path (Get-Location) 'hf_cache'
$env:HF_HUB_DISABLE_XET = '1'
python .\src\check_env.py
```

完整模型实验用固定权重 revision，见 [`results/day06_models.json`](results/day06_models.json) 和 [`src/day06_resume.ps1`](src/day06_resume.ps1)。在**全新、无 Day 6 输出**的工作目录下，可逐个执行；模型下载及推理需要 GPU、磁盘空间和时间：

```powershell
. .\src\day06_resume.ps1
foreach ($m in $models) {
    foreach ($t in $tasks) { Invoke-Day6Run $m $t }
}
```

已有本地原始日志时，下列命令只重新生成或核对分析产物，不调用模型：

```powershell
python .\src\variance.py --root .\runs\variance --out .\reports\17-variance.md --plot
python .\src\day20_capability_chart.py
python .\src\day20_sample_errors.py
python .\src\day20_apply_labels.py
```

方差实验的批量运行入口是 [`scripts/run_variance.ps1`](scripts/run_variance.ps1)；它会检查已有完整结果并跳过。更多实验命令见各报告。OpenCompass 使用**独立 Conda 环境**，环境和成功判定见[实跑报告](reports/19-opencompass-qwen15-ceval19.md)。DeepSeek API 试验需要自己设置密钥，密钥不写入仓库；见[Day 18 报告](reports/18-deepseek-mmlu50.md)。

## 阅读顺序与目录

- [`results/main_table.md`](results/main_table.md)：三款模型 × 五项任务的有限样本总表及每列指标口径。
- [`reports/`](reports/)：数据审计、对照实验、方差、框架横评和能力拆解的报告与可提交图表。
- [`notes/`](notes/)：原理笔记与每周复盘。
- [`configs/`](configs/)：自定义任务及 OpenCompass 配置；[`src/`](src/)：分析、审计和实验脚本；[`scripts/`](scripts/)：批量运行入口。
- [`RUNS.md`](RUNS.md) 和 `runs/ledger.jsonl`：运行元信息；大型逐题日志默认被 Git 忽略。

## 结论边界

本项目多数结果使用 `--limit`，主要用于定位评测链路和观察有限样本变化，不是完整 benchmark 排名。跨任务指标含义不同：TruthfulQA MC2 是正确选项的概率质量均值，不能读作逐题 0/1 准确率。不同框架即使用相同题目与模型，prompt、候选评分和并列规则也可能不同；需要先对齐这些条件再比较分数。三种模型规模也不是同一训练过程的连续 checkpoint，不能据此判断训练退化。
