# Expérience PixelRAG + reranking VLM

Date : 24 juin 2026

## Résultats principaux

Cette expérience évalue un pipeline de recherche visuelle de pages avec PixelRAG, puis un reranking par modèle vision-langage (VLM) sur les candidats déjà rappelés par PixelRAG.

Résultat de référence :

```text
PixelRAG seul, top-5 : 22/30 = 73,3 %
MRR@5 : 0,589
```

Résultat de rappel élargi :

```text
PixelRAG top-10 : 24/30 = 80,0 %
PixelRAG top-20 : 25/30 = 83,3 %
PixelRAG top-50 : 28/30 = 93,3 %
```

Résultat après reranking VLM des cas difficiles :

```text
PixelRAG + VLM reranker, top-5 : 26/30 = 86,7 %
MRR@5 : 0,597
```

Effet du reranking VLM sur les cas difficiles :

```text
Q004 : page cible remontée au rang 4
Q005 : page cible remontée au rang 2
Q009 : page cible remontée au rang 4
Q010 : page cible remontée au rang 1
Q018 : page cible remontée au rang 5
Q026 : page cible remontée au rang 1
```

Conclusion principale :

```text
Le reranker VLM améliore le classement, mais il ne crée pas de nouveaux candidats.
Il peut promouvoir une page pertinente déjà présente dans le top-50 PixelRAG.
Il ne peut pas corriger les questions dont la page cible est absente du top-50.
```

Les deux cas encore bloquants sont :

```text
Q024
Q028
```

Pour ces deux questions, la page cible n'était pas rappelée dans le top-50 PixelRAG. Le problème relève donc du rappel initial, pas du reranking.

## Interprétation technique

Le pipeline final est un système en deux étapes :

```text
1. PixelRAG : rappel rapide de pages candidates à partir des images de pages.
2. VLM reranker : lecture visuelle fine des pages candidates et reclassement.
```

PixelRAG produit un classement par similarité d'embeddings :

```text
question -> embedding multimodal -> recherche FAISS -> pages candidates
```

Le VLM reranker reçoit ensuite :

```text
question + images des pages candidates + métadonnées doc/page/rang PixelRAG
```

Il attribue à chaque page :

```json
{
  "vlm_relevance": 0.98,
  "vlm_answerable": true,
  "vlm_rationale": "Visible 'COPIE : CDEC.' directly answers the question."
}
```

Le reclassement utilise :

```text
answerable -> relevance VLM -> rang PixelRAG comme tie-break
```

Le fichier `query_candidates.json` n'est pas donné au modèle VLM. Il sert uniquement après coup pour évaluer si la page cible est présente dans le top-k.

## Exemple concret

Pour Q026 :

```text
Question : Que se passe-t-il si l'opérateur ne complète pas son dossier de demande de dérogation ?
```

Avant reranking :

```text
PixelRAG plaçait la bonne page au rang 6.
La question était donc considérée comme échouée en top-5.
```

Après reranking VLM :

```text
La page 20 de 20230125_NP_DPID-DAME_Extrait-memento-ZICAD.pdf est remontée au rang 1.
Rationale VLM : Dit: rejet implicite dans les deux mois.
```

Ce cas montre que PixelRAG avait bien rappelé la page pertinente, mais que le VLM a mieux identifié la page qui répondait précisément à la question.

## Structure du dossier

```text
scripts/    Scripts Python utilisés pour l'expérience
notebooks/  Versions notebook pour exécution cellule par cellule
inputs/     Questions, labels, manifest et résumé d'index
runs/       Sorties de recherche et de reranking
reports/    Rapports d'évaluation
evidence/  Cache du reranking VLM
```

## Entrées principales

```text
inputs/questions_only.json
```

Liste des 30 questions visuelles en français.

```text
inputs/query_candidates.json
```

Questions candidates avec pages cibles. Ce fichier est utilisé comme référence d'évaluation, pas comme entrée du reranker.

```text
inputs/corpus_manifest.jsonl
```

Manifest des pages images utilisées par PixelRAG.

```text
inputs/index_summary.json
```

Résumé de l'index FAISS PixelRAG.

## Scripts archivés

```text
scripts/pixelrag_visual_experiment.py
```

Script principal : préparation du corpus, recherche PixelRAG, extraction OCR, fusion RRF et évaluation.

```text
scripts/pixelrag_top20_rerank_experiment.py
```

Diagnostic top-20 et reranking local OCR/texte.

```text
scripts/pixelrag_enhanced_recall_experiment.py
```

Rappel élargi top-50, OCR complet, BM25 sur textes/OCR et fusion de rappel.

```text
scripts/pixelrag_vlm_rerank_experiment.py
```

Reranking VLM avec l'API OpenAI Responses sur les images de pages candidates.

## Notebooks archivés

```text
notebooks/pixelrag_visual_experiment - evidence.ipynb
notebooks/pixelrag_vlm_rerank_experiment.ipynb
```

Le second notebook permet d'exécuter le reranking VLM cellule par cellule. Il nécessite une clé API OpenAI valide pour les appels réels.

## Sorties importantes

```text
runs/pixelrag.json
```

Résultat direct PixelRAG top-5, sans OCR ni VLM.

```text
runs/pixelrag_with_evidence.json
```

Résultat PixelRAG enrichi avec des extraits OCR Tesseract. L'OCR aide à l'inspection humaine mais ne modifie pas le classement PixelRAG.

```text
runs/pixelrag_top50.json
```

Résultat PixelRAG top-50. C'est le fichier clé qui montre que le rappel atteint 28/30.

```text
runs/vlm_reranked_pixelrag_hard_cases.json
```

Résultat après reranking VLM des cas difficiles Q004, Q005, Q009, Q010, Q018 et Q026.

## Rapports importants

```text
reports/pixelrag_direct_vs_candidates_report.json
reports/pixelrag_direct_vs_candidates_report.md
```

Évaluation de PixelRAG seul.

```text
reports/enhanced_recall_report.json
```

Évaluation du rappel top-50.

```text
reports/vlm_rerank_hard_cases_report.json
```

Évaluation du reranking VLM sur les cas difficiles.

## Chronologie expérimentale

### 1. Recherche PixelRAG directe

Fichier généré :

```text
runs/pixelrag.json
```

Résultat :

```text
22/30 en top-5, soit 73,3 %
```

### 2. Ajout de preuves OCR

Fichier généré :

```text
runs/pixelrag_with_evidence.json
```

L'OCR est produit par Tesseract. Il sert à inspecter les pages retrouvées, mais la qualité OCR est variable et ne doit pas être confondue avec la performance PixelRAG.

### 3. Baseline texte BM25 et fusion RRF

Fichiers générés :

```text
runs/text.json
runs/fusion.json
```

Observation :

```text
Le BM25 texte est faible pour ces questions visuelles.
La fusion initiale n'améliore pas PixelRAG seul.
```

### 4. Diagnostic top-20

Fichiers générés :

```text
runs/pixelrag_top20.json
runs/reranked_pixelrag.json
reports/pixelrag_top20_rerank_report.json
```

Résultat :

```text
hit@20 = 25/30 = 83,3 %
```

Conclusion : top-20 n'est pas suffisant pour viser 90 % en top-5.

### 5. Rappel élargi top-50

Fichiers générés :

```text
runs/pixelrag_top50.json
runs/text_full_ocr_top50.json
runs/enhanced_recall.json
reports/enhanced_recall_report.json
```

Résultat :

```text
hit@50 = 28/30 = 93,3 %
```

Conclusion : le top-50 contient assez de bonnes pages pour justifier un reranking visuel.

### 6. Reranking VLM des cas difficiles

Fichiers générés :

```text
runs/vlm_reranked_pixelrag_hard_cases.json
reports/vlm_rerank_hard_cases_report.json
evidence/vlm_rerank_cache.jsonl
```

Résultat :

```text
hit@5 = 26/30 = 86,7 %
```

Le reranking a corrigé les six cas où la bonne page était présente dans le top-50 mais trop bas classée.

## Commandes de reproduction

Vérifier que l'API PixelRAG locale fonctionne :

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:30001/status" -UseBasicParsing
```

Relancer le rappel top-50 depuis la racine du projet original :

```powershell
python pixelrag_enhanced_recall_experiment.py --api-url http://127.0.0.1:30001
```

Relancer le reranking VLM des cas difficiles :

```powershell
$env:OPENAI_API_KEY = "sk-proj-..."
python pixelrag_vlm_rerank_experiment.py `
  --input pixelrag_visual_experiment/runs/pixelrag_top50.json `
  --output pixelrag_visual_experiment/runs/vlm_reranked_pixelrag_hard_cases.json `
  --report pixelrag_visual_experiment/reports/vlm_rerank_hard_cases_report.json `
  --candidate-limit 50 `
  --batch-size 5 `
  --qids Q004 Q005 Q009 Q010 Q018 Q026
```

## Limites

- Le résultat `86,7 %` n'est pas le score de PixelRAG seul, mais celui du système PixelRAG + VLM reranker sur les cas difficiles.
- Le VLM reranker ne peut pas retrouver une page absente du top-50 PixelRAG.
- L'OCR Tesseract est utile pour inspection, mais sa qualité est irrégulière sur les pages scannées, les affiches et les tableaux.
- Le reranking VLM est plus coûteux et plus lent que PixelRAG seul.

## Fichiers non archivés

Les images de pages, les tuiles PixelRAG, le cache OCR complet et l'index FAISS complet ne sont pas copiés ici afin de garder le dossier léger. Ce sont des artefacts dérivés et volumineux. Le dossier conserve les scripts, notebooks, entrées minimales, runs JSON, rapports et cache VLM.

