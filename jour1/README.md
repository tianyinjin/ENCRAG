# Jour 1

## 当天目标

搞懂比赛在评什么，以及 RAG 最小闭环是什么。

你今天不需要学会优化，只需要回答两个问题：

1. 比赛到底要求我输出什么？
2. RAG 的最小系统由哪几部分组成？

## 阅读清单

### P0. 比赛官方页面

- 标题：`EvalLLM2026 Challenge RAG`
- 链接：<https://evalllm2026.sciencesconf.org/resource/page/id/2>
- 为什么读：
  - 明确两项任务
  - 明确 JSON 提交格式
  - 明确评测按 `(doc_name, page)` 粒度
  - 明确不能加外部文档、不能 web 搜索
- 今天必须搞清楚的点：
  - 任务 1 是“检索 + 回答”
  - 任务 2 是“来源归因”
  - 结果既评 retrieval，也评 answer quality

### P0. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks

- 作者：Patrick Lewis et al.
- 年份：2020
- 链接：<https://nlp.cs.ucl.ac.uk/publications/2020-05-retrieval-augmented-generation-for-knowledge-intensive-nlp-tasks/>
- 备用链接：<https://huggingface.co/papers/2005.11401>
- 为什么读：
  - 这是 RAG 的经典起点论文
  - 帮你建立“先检索，再生成”的基本框架
- 读法建议：
  - 先看 abstract
  - 再看方法图
  - 最后只抓住 `retriever + generator`

### P1. Retrieval-Augmented Generation for Large Language Models: A Survey

- 作者：Yunfan Gao et al.
- 年份：2023
- 链接：<https://huggingface.co/papers/2312.10997>
- 备用链接：<https://arxiv.gg/abs/2312.10997>
- 为什么读：
  - 给你一张全景图
  - 帮你区分 naive RAG、advanced RAG、modular RAG
- 读法建议：
  - 只看总览图和 taxonomy
  - 不要今天深挖每个分支

## 今天的输出

- 自己写一页中文摘要，内容只包括：
  - 比赛在评什么
  - RAG 最小流程是什么
  - 你接下来 7 天要做什么

## 不要做的事

- 不要今天就研究 reranker、GraphRAG、agentic RAG
- 不要今天就纠结哪家模型最强
