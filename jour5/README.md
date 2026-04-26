# Jour 5

## 当天目标

把系统输出对齐到比赛要求，并开始学习“带来源的回答”。

今天不是让你做很强的 citation system，而是让你知道：

- 比赛交付是 JSON
- 回答应该尽量可追溯
- 任务 2 不应等到最后一天再想

## 阅读清单

### P0. 比赛官方页面中的 JSON 格式部分

- 链接：<https://evalllm2026.sciencesconf.org/resource/page/id/2>
- 为什么读：
  - 你今天要据此写出正式输出模板
  - 必须清楚 `retrieved` 字段长什么样
- 今天重点：
  - `qid`
  - `question`
  - `retrieved[].rank/doc_name/page`
  - `answer`
  - `metadata`

### P0. Enabling Large Language Models to Generate Text with Citations

- 作者：Tianyu Gao et al.
- 年份：2023
- 链接：<https://huggingface.co/papers/2305.14627>
- 备用链接：<https://collaborate.princeton.edu/en/publications/enabling-large-language-models-to-generate-text-with-citations/>
- 为什么读：
  - 这是 citation-aware generation 的关键论文
  - 它提出了 ALCE benchmark
- 对你比赛的意义：
  - 任务 2 本质上和 citation / attribution 强相关
  - 你会知道“回答好”不等于“回答可验证”

### P1. RARR: Researching and Revising What Language Models Say, Using Language Models

- 链接：<https://deepai.org/publication/rarr-researching-and-revising-what-language-models-say-using-language-models>
- 为什么读：
  - 帮你理解“先生成，再校正并补证据”这条思路
  - 虽然它依赖 web 搜索的部分不适用于本比赛，但 attribution 思路值得借鉴

## 今天的输出

- 写出你自己的比赛输出 JSON 模板
- 规定你回答的写法，例如：
  - 先回答
  - 每句尽量能回指到证据页

## 不要做的事

- 不要等 baseline 做完再考虑 citation
- 不要输出无法映射到页码的证据
