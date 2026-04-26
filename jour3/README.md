# Jour 3

## 当天目标

建立最小检索 baseline。

今天要搞懂：

- sparse retrieval 是什么
- dense retrieval 是什么
- 为什么比赛里 BM25 仍然值得作为 baseline

## 阅读清单

### P0. Dense Passage Retrieval for Open-Domain Question Answering

- 作者：Vladimir Karpukhin et al.
- 年份：2020
- 链接：<https://huggingface.co/papers/2004.04906>
- 备用链接：<https://nlp.cs.ucl.ac.uk/publications/2020-05-dense-passage-retrieval-for-open-domain-question-answering/>
- 为什么读：
  - dense retrieval 的经典起点
  - 帮你理解“问题和文档都编码成向量，再相似度匹配”
- 今天重点：
  - dual encoder
  - top-k retrieval

### P0. BEIR: A Heterogenous Benchmark for Zero-shot Evaluation of Information Retrieval Models

- 作者：Nandan Thakur et al.
- 年份：2021
- 链接：<https://huggingface.co/papers/2104.08663>
- 为什么读：
  - 帮你建立 IR baseline 观念
  - 它的重要结论之一是：`BM25 is a robust baseline`
- 对你的价值：
  - 比赛是法语、受限语料、禁止 web
  - 在这种条件下，BM25 不应该被跳过

### P1. Text Embeddings by Weakly-Supervised Contrastive Pre-training

- 作者：Liang Wang et al.
- 年份：2022
- 链接：<https://www.microsoft.com/en-us/research/publication/text-embeddings-by-weakly-supervised-contrastive-pre-training/>
- 备用链接：<https://papers.cool/arxiv/2212.03533>
- 为什么读：
  - 理解 E5 这类 embedding 模型的思想
  - 对你后面选开源 embedding baseline 有帮助

### P1. Multilingual E5 Text Embeddings: A Technical Report

- 作者：Liang Wang et al.
- 年份：2024
- 链接：<https://huggingface.co/papers/2402.05672>
- 为什么读：
  - 比赛文档是法语
  - 你需要尽快知道多语言 embedding 是怎么回事

### P2. Mr. TyDi: A Multi-lingual Benchmark for Dense Retrieval

- 作者：Xinyu Zhang et al.
- 年份：2021
- 链接：<https://huggingface.co/papers/2108.08787>
- 为什么读：
  - 让你知道多语言 dense retrieval 的现实难点
  - 帮你对“法语检索不一定天然简单”有心理预期

## 今天的输出

- 你自己的检索路线判断：
  - `BM25 only`
  - `dense only`
  - `hybrid`
- 一句话建议：默认从 `BM25 + dense` 混合开始

## 不要做的事

- 不要因为 dense 很潮就跳过 BM25
- 不要今天就追求最复杂检索结构
