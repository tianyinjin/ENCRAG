# Jour 7

## 当天目标

开始考虑来源归因、可信性、可复现性和最终参赛材料整理。

今天你要把系统从“能跑”推进到“像参赛作品”。

## 阅读清单

### P0. Enabling Large Language Models to Generate Text with Citations

- 链接：<https://huggingface.co/papers/2305.14627>
- 今天回看重点：
  - citation quality
  - correctness
  - fluency
- 为什么今天还读：
  - 它最接近你比赛任务 2 的思路

### P1. Model Internals-based Answer Attribution for Trustworthy Retrieval-Augmented Generation

- 作者：Jirui Qi et al.
- 年份：2024
- 链接：<https://huggingface.co/papers/2406.13663>
- 为什么读：
  - 这篇不是 baseline 必需品
  - 但它能帮你理解 attribution 不只是“在答案后面贴来源”

### P1. Source Attribution in Retrieval-Augmented Generation

- 作者：Ikhtiyor Nematov et al.
- 年份：2025
- 链接：<https://papers.cool/arxiv/2507.04480>
- 备用链接：<https://www.researchgate.net/publication/393477601_Source_Attribution_in_Retrieval-Augmented_Generation>
- 为什么读：
  - 这篇更直接讨论 RAG 中的 attribution
  - 能帮助你思考“哪些文档真正支撑了答案”

### P0. 比赛官方页面中“Comment participer”部分

- 链接：<https://evalllm2026.sciencesconf.org/resource/page/id/2>
- 为什么读：
  - 你要准备的不只是系统
  - 还包括：
    - 报告
    - 复现说明
    - 碳排记录
    - 参数记录

## 今天的输出

- 写一份参赛工程记录模板，至少包括：
  - 文本抽取方法
  - chunking 参数
  - embedding 模型
  - reranker 是否使用
  - generator 模型
  - prompt 模板
  - top-k
  - 输出格式说明
  - 资源消耗

## 不要做的事

- 不要最后才补实验记录
- 不要只留结果，不留参数
