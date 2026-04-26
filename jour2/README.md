# Jour 2

## 当天目标

学会把 PDF 文档按页抽出文本，并保住页码映射。

这一天不是理论日，重点是：

- 文本怎么从 PDF 里出来
- 页码怎么保住
- 后面怎么从 chunk 反查到页

## 阅读清单

### P0. PyMuPDF TextPage Documentation

- 链接：<https://pymupdf.readthedocs.io/en/latest/textpage.html>
- 为什么读：
  - 这是最直接可用的 PDF 文本抽取资料
  - 你很快就能据此写页级抽取脚本
- 今天重点看：
  - `extractText`
  - `extractBLOCKS`
  - `extractDICT`
  - `sort=True` 的作用

### P0. PyMuPDF Appendix 1: Details on Text Extraction

- 链接：<https://pymupdf.readthedocs.io/en/latest/app1.html>
- 为什么读：
  - 让你理解文本块、行、span 的层次
  - 帮你判断后面要不要按 block 切 chunk

### P1. MinerU: An Open-Source Solution for Precise Document Content Extraction

- 作者：Bin Wang et al.
- 年份：2024
- 链接：<https://huggingface.co/papers/2409.18839>
- 为什么读：
  - 让你知道高质量文档解析不仅是“抽文本”
  - 当你的 PDF 布局复杂时，这类思路有参考价值
- 这篇今天不必精读，知道“文档解析是一个独立问题”即可

### P2. GROBID Documentation: Introduction / How GROBID works

- 链接：<https://grobid.readthedocs.io/en/update-documentation/Introduction/>
- 链接：<https://grobid.readthedocs.io/en/latest/Principles/>
- 为什么读：
  - 如果比赛文档偏论文/报告式结构，这类工具思路有用
  - 不是你 baseline 的首选，但值得知道

## 今天的输出

- 设计一份页级数据结构，例如：
  - `doc_name`
  - `page`
  - `raw_text`
  - `blocks`
- 明确后续所有 chunk 都必须保留：
  - `doc_name`
  - `page`

## 不要做的事

- 不要今天就纠结高级 OCR
- 不要为了抽得“完美”而卡住 baseline
