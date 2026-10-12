# 数据质检报告：cais/mmlu/abstract_algebra

- 样本数：**100**

| 检查项 | 计数 | 含义与影响 |
|---|---|---|
| 完全重复 | 0 | 变相加权部分知识点，扭曲分数构成 |
| 近重复 | 11 | 题干相似的候选题对；需结合选项和答案人工核对 |
| 缺失或空字段 | 0 | 题目无法可靠展示或判分 |
| 答案合法性 | 0 | 直接导致判分错误 —— 优先级最高 |
| 选项位置偏置 | 1 | 仅提示分布偏离；需结合样本量判断，不能据此认定系统性偏置 |
| 长度异常 | 0 | 相对长度离群，需人工复核；不能据此断言输入被截断 |
| 编码与脏字符 | 0 | 可能改变 prompt 与 tokenization；需逐例判断是否为问题 |

## 完全重复（0）


## 近重复（11）


例子：
```json
[
  {
    "indices": [
      0,
      35
    ],
    "similarity": 0.826,
    "question_a": "Find the degree for the given field extension Q(sqrt(2), sqrt(3), sqrt(18)) over Q.",
    "question_b": "Find the degree for the given field extension Q(sqrt(2), sqrt(3)) over Q.",
    "choices_a": [
      "0",
      "4",
      "2",
      "6"
    ],
    "choices_b": [
      "0",
      "4",
      "2",
      "6"
    ],
    "answer_a": "B",
    "answer_b": "B"
  },
  {
    "indices": [
      8,
      35
    ],
    "similarity": 0.891,
    "question_a": "Find the degree for the given field extension Q(sqrt(2) + sqrt(3)) over Q.",
    "question_b": "Find the degree for the given field extension Q(sqrt(2), sqrt(3)) over Q.",
    "choices_a": [
      "0",
      "4",
      "2",
      "6"
    ],
    "choices_b": [
      "0",
      "4",
      "2",
      "6"
    ],
    "answer_a": "B",
    "answer_b": "B"
  },
  {
    "indices": [
      8,
      71
    ],
    "similarity": 0.846,
    "question_a": "Find the degree for the given field extension Q(sqrt(2) + sqrt(3)) over Q.",
    "question_b": "Find the degree for the given field extension Q(sqrt(2)*sqrt(3)) over Q.",
    "choices_a": [
      "0",
      "4",
      "2",
      "6"
    ],
    "choices_b": [
      "0",
      "4",
      "2",
      "6"
    ],
    "answer_a": "B",
    "answer_b": "C"
  },
  {
    "indices": [
      9,
      96
    ],
    "similarity": 0.809,
    "question_a": "Find all zeros in the indicated finite field of the given polynomial with coefficients in that field. x^3 + 2x + 2 in Z_7",
    "question_b": "Find all zeros in the indicated finite field of the given polynomial with coefficients in that field. x^2 + 1 in Z_2",
    "choices_a": [
      "1",
      "2",
      "2,3",
      "6"
    ],
    "choices_b": [
      "0",
      "1",
      "0,1",
      "2"
    ],
    "answer_a": "C",
    "answer_b": "B"
  },
  {
    "indices": [
      14,
      93
    ],
    "similarity": 0.949,
    "question_a": "Find the maximum possible order for an element of S_n for n = 10.",
    "question_b": "Find the maximum possible order for an element of S_n for n = 6.",
    "choices_a": [
      "6",
      "12",
      "30",
      "105"
    ],
    "choices_b": [
      "6",
      "12",
      "30",
      "105"
    ],
    "answer_a": "C",
    "answer_b": "A"
  }
]
```

## 缺失或空字段（0）


## 答案合法性（0）


## 选项位置偏置（1）

分布：`{'A': 22.0, 'B': 26.0, 'C': 31.0, 'D': 21.0}`（均匀应为 25.0%）

例子：
```json
[
  {
    "position": "C",
    "pct": 31.0
  }
]
```

## 长度异常（0）

题干长度：`{'min': 41, 'p01': 41.0, 'median': 121.0, 'p99': 243.0, 'max': 243, 'mean': 123.8}`
离群阈值：`{'method': '1.5 × IQR（题干字符数）', 'lower': 0.0, 'upper': 339.5}`

## 编码与脏字符（0）


---

> 说明：本报告只量化问题，不做修改。
> 近重复计数是候选题对数；选项位置偏置计数是超出启发式阈值的位置数。各项计数不可相加。
> 判断某类问题是否需要修复，取决于它的规模是否足以影响结论。