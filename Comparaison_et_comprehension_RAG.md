# Comparaison et compréhension du défi RAG

## Partie française

### 1. Ce que j'ai compris du défi

Ce défi n'évalue pas seulement si un grand modèle peut répondre à une question.  
Il évalue surtout si un système peut :

- retrouver les bonnes pages dans un ensemble documentaire fermé,
- générer une réponse fondée sur ces pages,
- et, autant que possible, attribuer clairement les sources.

Autrement dit, ce n'est pas un concours de "chatbot général".  
C'est un concours de **RAG évalué de manière contrôlée**.

### 2. La logique centrale du défi

Le point essentiel est le suivant :

- dans un système QA classique, on regarde surtout la qualité de la réponse finale ;
- dans ce défi, on regarde à la fois :
  - la qualité de la récupération,
  - la qualité de la génération,
  - et la traçabilité de la réponse.

Donc la réponse finale n'est qu'une partie du problème.  
Même une bonne réponse peut être insuffisante si :

- les pages récupérées ne sont pas les bonnes,
- la réponse n'est pas justifiable,
- ou la sortie ne respecte pas le format demandé.

### 3. Ce que cela change par rapport à un RAG "naïf"

Un RAG naïf fait souvent :

1. découpage des documents,
2. indexation vectorielle,
3. récupération top-k,
4. génération d'une réponse.

Mais ici, cela ne suffit pas vraiment.  
Le défi impose plusieurs contraintes supplémentaires :

- la granularité d'évaluation est la **page** ;
- les documents externes et la recherche web sont interdits ;
- le système doit rendre un JSON structuré ;
- la qualité de la source est importante, pas seulement la fluidité de la réponse.

Donc, par rapport à un RAG ordinaire, ce défi est plus proche d'un système :

- de **question-réponse ancré dans les documents**,
- de **récupération contrôlée**,
- et de **génération vérifiable**.

### 4. Comparaison des composantes à bien distinguer

#### a. Récupération vs génération

Il faut bien séparer :

- **retrieval** : retrouver les bons documents / bonnes pages ;
- **generation** : rédiger une réponse à partir des éléments retrouvés.

Si le retrieval échoue, la génération échouera souvent aussi.  
Si le retrieval est bon mais que la réponse est mauvaise, le problème vient alors du prompt, de l'ordre des preuves, du modèle ou de la stratégie de synthèse.

#### b. Chunk vs page

Dans la pratique, on peut découper en chunks pour mieux indexer.  
Mais du point de vue de l'évaluation, ce qui compte finalement est :

- `doc_name`
- `page`

Donc tout chunk doit garder un lien explicite vers sa page d'origine.

#### c. Réponse correcte vs réponse attribuée

Une réponse peut être correcte en apparence, mais non attribuée.  
Dans ce défi, une bonne réponse doit être autant que possible :

- correcte,
- fondée,
- traçable,
- et justifiable.

### 5. Ce que j'ai compris sur le niveau de difficulté

Le défi n'exige pas forcément un système ultra-complexe au départ.  
Pour un débutant, le plus important est de construire :

- un pipeline simple,
- stable,
- reproductible,
- et conforme aux règles.

Au début, un bon baseline vaut mieux qu'un système ambitieux mais fragile.

### 6. La compréhension comparative la plus importante

Je résume ainsi :

- un LLM seul répond "de mémoire" ou "par habitude" ;
- un système RAG répond "à partir de documents récupérés" ;
- ce défi exige un RAG qui ne fasse pas seulement cela, mais qui sache aussi **montrer d'où viennent ses réponses**.

Donc :

- ce n'est pas seulement "répondre",
- ce n'est pas seulement "retrouver",
- c'est "retrouver, répondre et relier la réponse à la source".

### 7. Conséquence pratique

Pour participer sérieusement, il faut penser le système dans cet ordre :

1. extraction du texte par page,
2. découpage contrôlé,
3. indexation,
4. récupération,
5. génération guidée par preuves,
6. attribution des pages,
7. sortie JSON conforme.

Le défi demande donc une vision plus rigoureuse qu'un simple notebook RAG de démonstration.

## 中文部分

### 1. 我对这个比赛的基本理解

这个比赛评测的，不只是“大模型会不会回答问题”。  
它更核心地在评测一个系统能否：

- 在一个封闭文档集合里找对相关页面，
- 基于这些页面生成答案，
- 并且尽可能把答案和来源对应起来。

换句话说，这不是普通的“聊天机器人比赛”，而是一个**受控评测的 RAG 比赛**。

### 2. 这个比赛的核心逻辑

最关键的一点是：

- 在普通问答系统里，人们往往最看重最终答案；
- 但在这个比赛里，需要同时看：
  - 检索质量，
  - 生成质量，
  - 以及答案是否可追溯。

所以最终答案只是问题的一部分。  
即使答案表面上看起来不错，如果：

- 找回来的页面不对，
- 答案无法被来源支撑，
- 或者提交格式不符合要求，

那仍然是不够的。

### 3. 它和“朴素 RAG”有什么不同

一个朴素的 RAG 往往就是：

1. 切文档，
2. 做向量索引，
3. 做 top-k 检索，
4. 让模型生成答案。

但这个比赛不止于此。  
它还额外要求：

- 评测粒度落在**页级**；
- 不允许加入外部文档，也不能 web 搜索；
- 必须输出结构化 JSON；
- 不只看回答流畅不流畅，还看来源是否合理。

所以和普通 RAG 相比，这个比赛更像一个：

- **文档锚定问答系统**
- **受控检索系统**
- **可验证生成系统**

### 4. 我认为必须区分的几组东西

#### a. 检索 和 生成

要明确分开：

- **retrieval**：找到正确文档 / 正确页面
- **generation**：基于找到的证据写出答案

如果检索错了，生成通常也会错。  
如果检索是对的，但答案写得不好，那问题就可能在 prompt、证据顺序、模型本身或总结策略上。

#### b. chunk 和 page

工程上可以按 chunk 检索，这样更灵活。  
但比赛最终看的是：

- `doc_name`
- `page`

所以每一个 chunk 从一开始就必须保留它来自哪一页。

#### c. 回答正确 和 回答可归因

一个回答可能“看起来是对的”，但没有来源支撑。  
在这个比赛里，更好的回答应该尽可能同时满足：

- 正确
- 有依据
- 可追溯
- 可解释

### 5. 我对比赛难度的理解

这个比赛并不要求一开始就做出极其复杂的系统。  
对新手来说，更重要的是先做一个：

- 简单
- 稳定
- 可复现
- 符合规则

的 baseline。

开始阶段，一个扎实的基础系统，比一个看起来很复杂但很脆弱的系统更有价值。

### 6. 最重要的“比较式理解”

我现在把它总结成一句更清楚的话：

- 单独的 LLM 更像是“凭记忆或习惯回答”；
- RAG 是“先找资料，再基于资料回答”；
- 而这个比赛要求的，不只是做到这一点，还要**说明答案从哪里来**。

所以，这个比赛不是单纯的：

- “会不会回答”

而是：

- “会不会找”
- “会不会答”
- “会不会把答案和来源关联起来”

### 7. 对实际做系统的直接影响

如果真的要参赛，系统应该按这个顺序来想：

1. 按页抽文本
2. 受控切块
3. 建索引
4. 做检索
5. 基于证据生成
6. 做页级归因
7. 输出符合要求的 JSON

所以这个比赛需要的不是一个“演示型 RAG notebook”，而是一套更严谨的、可验证的系统流程。
