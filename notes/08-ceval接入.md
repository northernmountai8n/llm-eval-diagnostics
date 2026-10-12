# Day 8：自定义 C-Eval 任务的最小接入

> 实际运行：2026-09-29。本次只验证一个科目的任务接入，不把分数当作完整 C-Eval 成绩。

## 任务与数据

- 自定义任务定义：[`configs/tasks/ceval_computer_network.yaml`](../configs/tasks/ceval_computer_network.yaml)。任务名 `custom_ceval_computer_network`，通过 `--include_path .\configs\tasks` 加载；没有修改 `site-packages`。
- 数据集：`ceval/ceval-exam`，`computer_network` 配置，`val` split，共 **19 题**。字段为 `id`、`question`、`A`、`B`、`C`、`D`、`answer`、`explanation`。
- 0-shot、多选、`acc`。题干包含问题和 A–D 选项，以 `答案：` 结束；候选 continuation 为带前导空格的 ` A`、` B`、` C`、` D`。`answer` 的字母映射到 0–3 下标。
- 本机 `lm-eval 0.4.13` 已内置 C-Eval 与 CMMLU。本任务的价值是练习维护和验证项目内的任务配置；不能称为给框架新增此前不存在的 benchmark。

## 运行与结果

模型是 `Qwen/Qwen2.5-1.5B`，revision 固定为 `8faed761d45a263340a0528343f099c05c9a4323`，`dtype=bfloat16`，`batch_size=1`，`device=cuda:0`，seed 为 `0,1234,1234,1234`。验证集只有 19 题，因此没有使用 `--limit`。完整运行命令：

```powershell
lm_eval run --model hf --model_args 'pretrained=Qwen/Qwen2.5-1.5B,revision=8faed761d45a263340a0528343f099c05c9a4323,dtype=bfloat16' --tasks custom_ceval_computer_network --include_path '.\configs\tasks' --num_fewshot 0 --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '.\runs\day08_ceval_computer_network_0shot' --log_samples
```

**结果：`acc=0.5263`，标准误 `0.1177`，即 19 题答对 10 题。**每题四个选项，共运行 76 条 `loglikelihood` 请求。原始汇总与逐题记录保存在 [`runs/day08_ceval_computer_network_0shot/`](../runs/day08_ceval_computer_network_0shot/) 下。

运行时曾发生 Hugging Face Hub SSL 握手超时，自动重试后继续成功；不能把重试日志当成评测失败。日志提示 YAML 已将 `num_fewshot` 设为 0，因而忽略命令行手动配置；两处取值相同，不影响本次 0-shot 设置。

## 逐题验证

对全部 JSONL 样本检查，得到 **19 条记录、`acc` 合计 10、答案字母与目标下标不一致 0 条**。首题原始答案为 `C`，保存的 `target` 为 `2`；prompt 含完整题干及 A–D 选项。候选 loglikelihood 分别为 A `-3.453125`、B `-3.078125`、C `-3.203125`、D `-3.203125`，模型预测 B，故该题 `acc=0`。响应中的 `False` 是 `is_greedy` 标志，不是该选项的正确性。

## 结论与下一步

本次完成了 Day 8 的**中文任务最小接入与小样本验证**，证实了数据字段、prompt、选项和标准答案映射可正常运行。19 题来自单一科目的验证集，不能代表完整 C-Eval。内置 C-Eval 配置还包含科目说明，并同时报告 `acc_norm`；Day 9 对拍前必须对齐 prompt、shot、split、评分指标与模型参数，不能直接比较两个不同协议的汇总分数。
