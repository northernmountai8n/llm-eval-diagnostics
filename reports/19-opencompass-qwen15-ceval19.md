# Day 19｜用 OpenCompass 实跑现有 Qwen2.5-1.5B

## 实验问题与结果

检验第二个评测框架能否在本机对**已经用过的 base 模型**完成真实的逐题推理和评分。OpenCompass 0.5.4 在 C-Eval 计算机网络验证集 **19 题中答对 15 题，accuracy = 78.95%**。已核对预测文件有 19 条、评估详情有 19 条，逐题 `prediction == gold` 为 15 条；本次不是仅有 CLI 帮助或空白汇总表的安装测试。

| 项目 | 固定设置 |
| --- | --- |
| 模型 | `Qwen/Qwen2.5-1.5B`（base），revision `8faed761d45a263340a0528343f099c05c9a4323` |
| 推理 | 本机 RTX 4060 Laptop GPU；PyTorch `2.14.1+cu126`；`bfloat16`；batch size 1 |
| 框架 | OpenCompass `0.5.4`，Transformers `4.57.3` |
| 数据 | `ceval/ceval-exam` / `computer_network`，revision `617524a00b307ff6f9933702f724131fe12ca7ce`；`val` 19 题，`dev` 5 题 |
| 任务口径 | OpenCompass C-Eval 配置的 5-shot、`PPLInferencer` 候选评分、`AccEvaluator`；固定使用全部 5 道 `dev` 题作示例 |

源数据通过 [`src/prepare_day19_ceval_opencompass.py`](../src/prepare_day19_ceval_opencompass.py)按固定 revision 导出为 OpenCompass 所需的 CSV；导出的副本位于忽略提交的 `data/day19_ceval_opencompass/`。评测配置为 [`configs/day19_opencompass_qwen15_ceval19.py`](../configs/day19_opencompass_qwen15_ceval19.py)。OpenCompass 内置配置原指向 `opencompass/ceval-exam`，本机无法从该仓库加载；本实验保留其题目模板、5-shot 检索和评分设置，只改成本地导出的同科目 C-Eval 数据。

成功运行的原始文件保存在本地 `runs/`，按仓库忽略规则不随代码发布：

- 逐题预测：`runs/day19_opencompass_qwen15_ceval19/20261009_204903/predictions/qwen2.5-1.5b-base-pinned/ceval-computer_network.json`
- 逐题评分与准确率：`runs/day19_opencompass_qwen15_ceval19/20261009_204903/results/qwen2.5-1.5b-base-pinned/ceval-computer_network.json`
- 汇总表：`runs/day19_opencompass_qwen15_ceval19/20261009_204903/summary/summary_20261009_204903.md`

## 与已有 lm-eval 结果怎样比较

本项目此前 `lm-eval` 的 C-Eval 计算机网络 5-shot 运行是 **14/19 = 73.68%**。两次使用同一个模型权重 revision、同一科目的 19 道验证题，标准答案逐题相同；逐题预测只有 **ID 16（“UDP 报头部长度为____。”）**不同：OpenCompass 选 A（正确），`lm-eval` 选 D。

但这**不是同一评测口径的框架精度对拍**：

- `lm-eval` 提示词只在开头给一次科目说明，并以 `答案：`（全角冒号）接选项；OpenCompass 在每道示例及测试题前重复科目说明，用 `答案:`（半角冒号）和不同换行。
- `lm-eval` 对 `" A"` 等候选续接取条件 loglikelihood 的最大值；OpenCompass 的该配置对候选提示词取 PPL 最小值。两种值及其归一化、候选位置不应直接视作相同。
- OpenCompass 有 **3 题候选最低 PPL 完全并列**：ID 0（C/D）、ID 4（A/D）、ID 16（A/D）；框架选择并列列表中的前一个。ID 16 的 A、D 都是 `1.1055331313819217`，因此这 1 题的总分差还受并列处理影响，不能简单归因为模型知识提升。

所以本次可证明**第二框架完成了真实推理与评分**；尚不能据 `15/19` 对 `14/19` 断言某框架更准确。若要做严格对拍，还需统一完整 prompt、候选评分和并列规则，再逐题比较。

## 复现命令（PowerShell）

```powershell
Set-Location 'D:\桌面\个人\工程\llm-eval-diagnostics'
conda activate opencompass
$env:HF_HOME = Join-Path (Get-Location) 'hf_cache'
$env:HF_HUB_DISABLE_XET = '1'
$env:TOKENIZERS_PARALLELISM = 'false'
python .\src\prepare_day19_ceval_opencompass.py
opencompass .\configs\day19_opencompass_qwen15_ceval19.py --dry-run --work-dir .\runs\day19_opencompass_qwen15_ceval19
opencompass .\configs\day19_opencompass_qwen15_ceval19.py --debug --work-dir .\runs\day19_opencompass_qwen15_ceval19 --dump-eval-details
```

**判定成功时必须打开本次新建的 `results/` 和 `predictions/` 文件核对。**这次调试中，OpenCompass 曾在模型下载失败、推理失败时仍以退出码 0 写出分数为 `-` 的汇总表；“命令退出 0”本身不能作为完成证据。

## 环境排障记录

1. OpenCompass 环境最初是 CPU 版 PyTorch，已换为官方 `2.14.1+cu126` Windows wheel；确认 `torch.cuda.is_available()` 为 `True`。
2. 安装所得 PyArrow 26 要求 NumPy 2，而环境是 NumPy 1.26.4；将 PyArrow 固定为 20.0.0，恢复 `opencompass --help`。
3. 首次权重下载遇到 Hugging Face Xet 的文件重建错误；设置 `HF_HUB_DISABLE_XET=1` 后把固定模型权重缓存在项目的 `hf_cache/`（D 盘）。[官方环境变量说明](https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables)。
4. OpenCompass 0.5.4 使用的 `batch_encode_plus` 已被 Transformers 5 移除；固定 Transformers 4.57.3，并将附属依赖固定为兼容版本。最后 `python -m pip check` 报 `No broken requirements found`。[OpenCompass 对应问题](https://github.com/open-compass/opencompass/issues/2635)。

上述两次失败与最终成功的调试日志保存在 `runs/day19_opencompass_qwen15_ceval19/debug_logs/`。

这个实验仅覆盖一个模型、一个 19 题科目及一种 5-shot PPL 配置，不能代表 OpenCompass 的整体表现，也不是 C-Eval 全量分数。
