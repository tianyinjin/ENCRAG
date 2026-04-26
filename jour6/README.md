# Jour 6

## 当天目标

开始做系统评测和检索优化。

今天要搞懂：

- 检索评测和答案评测不是一回事
- 哪些自动指标值得看
- reranker 为什么常常有用

## 阅读清单

### P0. BEIR: A Heterogenous Benchmark for Zero-shot Evaluation of Information Retrieval Models

- 链接：<https://huggingface.co/papers/2104.08663>
- 今天回看重点：
  - NDCG
  - Recall
  - zero-shot robustness
  - BM25 / dense / reranker 的 trade-off

### P0. ColBERTv2: Effective and Efficient Retrieval via Lightweight Late Interaction

- 作者：Keshav Santhanam et al.
- 年份：2021
- 链接：<https://huggingface.co/papers/2112.01488>
- 为什么读：
  - 帮你理解 reranking / late interaction 为什么常常比纯单向量更强
  - 不要求你今天就实现 ColBERT，但要知道它代表什么方向

### P1. BERTScore: Evaluating Text Generation with BERT

- 作者：Tianyi Zhang et al.
- 年份：2019
- 链接：<https://openreview.net/forum?id=SkeHuCVFDr>
- 备用链接：<https://huggingface.co/papers/1904.09675>
- 为什么读：
  - 比赛页面提到会用 lexical / neural metrics
  - 这篇是神经文本评测的经典代表

### P1. RAGAS: Automated Evaluation of Retrieval Augmented Generation

- 作者：Shahul Es et al.
- 年份：2023
- 链接：<https://huggingface.co/papers/2309.15217>
- 为什么读：
  - 帮你建立 RAG 多维评测意识
  - 虽然比赛有自己的官方评测，但你平时调系统时可以借鉴 RAGAS 的评估维度

## 今天的输出

- 建立一份误差分析表，至少区分：
  - 没召回正确页
  - 召回对了但生成没用好
  - 回答对了但没法归因

## 不要做的事

- 不要只盯最终回答文本
- 不要忽略 retrieval 侧的指标
