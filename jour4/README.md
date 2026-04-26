# Jour 4

## 当天目标

理解生成模块的边界：召回再多，不代表模型就会正确使用。

今天要重点理解：

- LLM 不是把所有召回内容都用好
- 长上下文有明显位置偏差
- 有些问题本质上不是普通 RAG，而是全局总结问题

## 阅读清单

### P0. Lost in the Middle: How Language Models Use Long Contexts

- 作者：Nelson F. Liu et al.
- 年份：2024
- 链接：<https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00638/119630/Lost-in-the-Middle-How-Language-Models-Use-Long>
- 备用链接：<https://huggingface.co/papers/2307.03172>
- 为什么读：
  - 这是你做 RAG 必须知道的一篇
  - 它说明：上下文越长越不一定更好，模型容易忽略中间证据
- 对比赛的直接意义：
  - top-k 不是越大越好
  - 证据摆放顺序会影响最终回答

### P1. From Local to Global: A Graph RAG Approach to Query-Focused Summarization

- 作者：Darren Edge et al.
- 年份：2024
- 链接：<https://huggingface.co/papers/2404.16130>
- 备用链接：<https://www.microsoft.com/en-us/research/publication/from-local-to-global-a-graph-rag-approach-to-query-focused-summarization/>
- 为什么读：
  - 帮你识别哪类问题不适合普通 chunk-level RAG
  - 比如“整个文档集的主题是什么”这类问题
- 对比赛的意义：
  - 如果测试题里出现“全局综合题”，你要知道 baseline 为什么会差

### P2. Retrieval-Augmented Generation for Large Language Models: A Survey

- 链接：<https://huggingface.co/papers/2312.10997>
- 今天回看重点：
  - pre-retrieval
  - post-retrieval
  - generation

## 今天的输出

- 为自己的 baseline 定一个简单生成原则：
  - 只喂 top-k 证据
  - 证据按相关性排序
  - 回答必须基于证据，不自由发挥

## 不要做的事

- 不要认为“模型上下文更长 = 问题自动解决”
- 不要把太多页硬塞给生成器
