# Guide débutant pour participer au concours RAG

## Partie française

### 1. Si je débute complètement, par où commencer ?

Si tu es débutant, il ne faut pas commencer par des variantes compliquées de RAG.  
Il faut commencer par un **baseline minimal**.

L'objectif initial n'est pas :

- d'obtenir le meilleur score immédiatement,
- ni de construire un système très sophistiqué.

L'objectif initial est :

- de comprendre le pipeline,
- de respecter le règlement,
- et d'avoir une première soumission valide.

### 2. Ce qu'il faut comprendre en premier

Avant de coder beaucoup, il faut comprendre cinq notions simples :

1. `document`
2. `page`
3. `chunk`
4. `retrieval`
5. `generation`

Formule simple :

**RAG = retrouver des passages utiles, puis répondre à partir d'eux.**

Dans ce concours, il faut ajouter :

**les passages retrouvés doivent rester reliés à leur page d'origine.**

### 3. Ce qu'un débutant doit éviter

Au début, il faut éviter :

- de vouloir utiliser trop de modèles à la fois,
- de se disperser dans des lectures trop théoriques,
- de commencer directement par les techniques à la mode,
- d'oublier le format JSON de soumission,
- d'oublier la contrainte de page.

Le vrai risque d'un débutant n'est pas d'avoir un système trop simple.  
Le vrai risque est d'avoir un système incomplet ou non conforme.

### 4. Le meilleur plan d'action pour un débutant

#### Étape 1. Lire correctement les PDF

Il faut d'abord extraire le texte page par page.  
La chose la plus importante ici est :

- ne jamais perdre la correspondance entre texte et page.

#### Étape 2. Construire une base de récupération simple

Ensuite, il faut construire un système capable de répondre à :

- pour une question donnée,
- quelles sont les pages les plus pertinentes ?

Au début, il ne faut pas avoir peur d'utiliser :

- BM25,
- un embedding simple,
- ou un mélange des deux.

#### Étape 3. Ajouter une génération fondée sur les preuves

Une fois la récupération en place, on peut envoyer :

- la question,
- les passages récupérés,

à un modèle génératif qui répondra à partir de ces preuves.

Le principe à suivre :

- ne pas laisser le modèle improviser librement,
- lui demander de répondre à partir du contexte récupéré.

#### Étape 4. Produire une sortie conforme au concours

Un débutant doit très tôt vérifier :

- le format JSON,
- les champs attendus,
- l'ordre du ranking,
- et la structure des métadonnées.

### 5. Ce qu'il faut travailler en priorité

Pour un débutant, les priorités sont :

1. extraction correcte du texte,
2. conservation de `doc_name` et `page`,
3. récupération top-k stable,
4. réponse fondée sur les documents,
5. sortie JSON correcte.

Ce n'est qu'après cela qu'il faut améliorer :

- le reranking,
- l'attribution fine,
- l'optimisation des prompts,
- le choix précis des modèles.

### 6. Comment progresser sans se perdre

Le plus utile est d'avancer par couches :

#### Couche 1

Faire fonctionner tout le pipeline une fois.

#### Couche 2

Comparer plusieurs choix simples :

- taille des chunks,
- top-k,
- BM25 vs dense retrieval,
- ordre des passages dans le prompt.

#### Couche 3

Faire une analyse d'erreurs :

- erreur de retrieval,
- erreur de génération,
- erreur d'attribution,
- erreur de format.

### 7. Comment penser la tâche 2 dès le début

Même si la tâche 2 semble venir après, il vaut mieux y penser dès le début.  
Pourquoi ?

Parce que si ton système ne garde pas dès maintenant la trace des pages source, il sera beaucoup plus difficile ensuite :

- d'expliquer la réponse,
- de justifier les preuves,
- et de produire une attribution propre.

### 8. Ce qu'un bon baseline de débutant doit avoir

Un bon baseline de débutant doit être :

- simple,
- clair,
- reproductible,
- bien journalisé,
- et facile à améliorer.

Concrètement, il doit contenir :

- une extraction page par page,
- une indexation,
- une récupération top-k,
- une génération contrainte,
- un export JSON,
- des paramètres sauvegardés.

### 9. Le bon état d'esprit

Au début, il ne faut pas se demander :

- "Comment battre tout le monde ?"

Il vaut mieux se demander :

- "Comment construire un système propre et soumisable ?"

Si tu arrives à cela, tu auras déjà une base sérieuse pour progresser.

## 中文部分

### 1. 如果我是完全新手，应该从哪里开始？

如果你是新手，不应该一开始就去学很复杂的 RAG 变体。  
正确的起点应该是一个**最小 baseline**。

最开始的目标不是：

- 立刻冲最高分，
- 也不是做一个极其复杂的系统。

最开始的目标应该是：

- 看懂整条流程，
- 满足比赛规则，
- 做出一份可以提交的结果。

### 2. 新手最先应该理解什么

在大量写代码之前，先理解这五个概念：

1. `document`
2. `page`
3. `chunk`
4. `retrieval`
5. `generation`

一句最简单的话：

**RAG = 先找有用内容，再基于这些内容回答。**

但对这个比赛，还要再补一句：

**检索出来的内容必须一直和原始页码保持关联。**

### 3. 新手一开始最应该避免什么

一开始要避免：

- 同时尝试太多模型，
- 一上来就读太多很重的理论，
- 直接追热门技术而忽略基础流程，
- 忘了 JSON 提交格式，
- 忘了比赛是按页评测。

对新手来说，最大的风险不是系统太简单。  
最大的风险是系统不完整，或者根本不符合比赛要求。

### 4. 新手最合理的行动路线

#### 第一步：先把 PDF 按页读出来

首先要做的，是把文档按页抽出文本。  
这里最重要的不是文本有多漂亮，而是：

- 绝对不能丢掉文本和页码的对应关系。

#### 第二步：搭一个最简单的检索系统

接下来要让系统具备回答这个问题的能力：

- 给一个问题，
- 哪些页面最相关？

在这个阶段，不要排斥简单方法，例如：

- BM25
- 简单 embedding
- 或两者混合

#### 第三步：加入“基于证据回答”的生成

当检索部分能工作之后，再把：

- 问题
- 检索到的文本片段

交给生成模型，让它基于证据作答。

这一步要坚持一个原则：

- 不要让模型自由发挥，
- 要让它尽量只根据召回内容回答。

#### 第四步：尽早对齐比赛输出格式

新手非常容易忽视这一点。  
但实际上，你应该很早就检查：

- JSON 格式对不对，
- 字段对不对，
- 排名顺序对不对，
- metadata 结构对不对。

### 5. 新手最应该优先练的能力

对新手来说，优先级应该是：

1. 正确抽文本
2. 保住 `doc_name` 和 `page`
3. 做稳定的 top-k 检索
4. 做基于文档的回答
5. 输出正确 JSON

只有这些稳定之后，再去优化：

- reranker
- 更细的归因
- prompt 设计
- 模型选型

### 6. 如何不迷失地推进

最有效的方法是分层推进：

#### 第一层

先让整个流程完整跑通一次。

#### 第二层

再去比较一些最重要但不复杂的变量：

- chunk 大小
- top-k
- BM25 和 dense retrieval
- 证据在 prompt 里的排列顺序

#### 第三层

再开始做误差分析：

- 是检索错了？
- 是生成错了？
- 是来源归因错了？
- 还是提交格式错了？

### 7. 为什么一开始就要考虑任务 2

虽然任务 2 看起来像后面的事，但其实越早考虑越好。  
原因很简单：

如果你的系统从一开始就不保留来源页信息，那么后面就会很难：

- 解释答案从哪里来，
- 说明哪页是证据，
- 做出干净的来源归因。

### 8. 一个好的新手 baseline 应该具备什么

一个好的新手 baseline 应该是：

- 简单
- 清晰
- 可复现
- 有记录
- 容易继续改进

具体来说，它至少应该包含：

- 页级文本抽取
- 索引
- top-k 检索
- 受约束生成
- JSON 导出
- 参数记录

### 9. 新手最好的心态

一开始不要先想：

- “我怎么打败所有人？”

更好的问题是：

- “我怎么先做出一套干净、可提交、可解释的系统？”

只要先做到这一点，你就已经建立了非常扎实的参赛基础。
