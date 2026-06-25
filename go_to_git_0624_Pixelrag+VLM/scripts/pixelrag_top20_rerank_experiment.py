"""Run a separate PixelRAG top-20 diagnostic and local rerank experiment.

This script intentionally does not modify the notebook workflow. It can:

1. Query a running PixelRAG API and save top-20 page retrieval results.
2. Compare a run against query_candidates.json at k=5/10/20.
3. Produce a reranked run using local page text/OCR evidence as a lightweight
   reranker. This is not a true visual-language reranker; it is a local
   diagnostic rerank that can run without another model service.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import time
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
EXPERIMENT_DIR = PROJECT_ROOT / "pixelrag_visual_experiment"
RUNS_DIR = EXPERIMENT_DIR / "runs"
REPORTS_DIR = EXPERIMENT_DIR / "reports"
QUESTIONS_PATH = EXPERIMENT_DIR / "questions_only.json"
CANDIDATES_PATH = EXPERIMENT_DIR / "query_candidates.json"
MANIFEST_PATH = EXPERIMENT_DIR / "corpus_manifest.jsonl"
EXTRACTED_PAGES_PATH = PROJECT_ROOT / "pymupdf_extract_output" / "extracted_pages.jsonl"
OCR_CACHE_DIR = EXPERIMENT_DIR / "evidence" / "ocr_cache"

DEFAULT_API_URL = "http://127.0.0.1:30001"
DEFAULT_TOP20_RUN = RUNS_DIR / "pixelrag_top20.json"
DEFAULT_RERANKED_RUN = RUNS_DIR / "reranked_pixelrag.json"
DEFAULT_REPORT = REPORTS_DIR / "pixelrag_top20_rerank_report.json"

WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return unicodedata.normalize("NFKC", text).casefold()


def tokenize(text: str) -> list[str]:
    return [m.group(0) for m in WORD_RE.finditer(normalize_text(text)) if len(m.group(0)) >= 2]


def question_key(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(text)).casefold()).strip()


def page_key(item: dict[str, Any]) -> tuple[str, int]:
    return str(item["doc_name"]).casefold(), int(item["page"])


def load_queries() -> list[dict[str, Any]]:
    data = read_json(QUESTIONS_PATH)
    questions = data.get("questions", [])
    return [
        {"qid": f"Q{index:03d}", "question": str(question)}
        for index, question in enumerate(questions, 1)
        if str(question).strip()
    ]


def load_manifest() -> dict[int, dict[str, Any]]:
    records: dict[int, dict[str, Any]] = {}
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                item = json.loads(line)
                records[int(item["article_id"])] = item
    return records


def post_json(url: str, payload: dict[str, Any], timeout: int = 240) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def search_topk(api_url: str, top_k: int, output: Path, overfetch_multiplier: int = 5) -> None:
    queries = load_queries()
    manifest = load_manifest()
    run_queries = []
    for query in queries:
        started = time.perf_counter()
        response = post_json(
            api_url.rstrip("/") + "/search",
            {
                "queries": [{"text": query["question"]}],
                "n_docs": max(top_k * overfetch_multiplier, top_k),
            },
        )
        raw_hits = response.get("results", [{}])[0].get("hits", [])
        page_hits: dict[tuple[str, int], dict[str, Any]] = {}
        for hit in raw_hits:
            record = manifest.get(int(hit["article_id"]))
            if record is None:
                continue
            key = (record["doc_name"], int(record["page"]))
            candidate = {
                "score": float(hit["score"]),
                "doc_name": key[0],
                "page": key[1],
                "image_path": record["image_path"],
                "article_id": int(hit["article_id"]),
            }
            if key not in page_hits or candidate["score"] > page_hits[key]["score"]:
                page_hits[key] = candidate
        hits = sorted(page_hits.values(), key=lambda item: item["score"], reverse=True)[:top_k]
        for rank, hit in enumerate(hits, 1):
            hit["rank"] = rank
        run_queries.append(
            {
                "qid": query["qid"],
                "question": query["question"],
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "hits": hits,
            }
        )
    write_json(output, {"system": "pixelrag", "top_k": top_k, "queries": run_queries})
    print(f"Saved {len(run_queries)} top-{top_k} PixelRAG results to {output}")


def load_candidate_targets() -> dict[str, dict[str, Any]]:
    data = read_json(CANDIDATES_PATH)
    targets = {}
    for candidate in data.get("candidates", []):
        pages = [
            (str(page["doc_name"]).casefold(), int(page["page"]))
            for page in candidate.get("relevant_pages", [])
        ]
        if not pages and candidate.get("doc_name") and candidate.get("page"):
            pages = [(str(candidate["doc_name"]).casefold(), int(candidate["page"]))]
        targets[question_key(candidate["question"])] = {
            "candidate_qid": candidate.get("qid"),
            "category": candidate.get("category"),
            "answer": candidate.get("answer"),
            "target_pages": pages,
        }
    return targets


def evaluate_run(run_path: Path, ks: list[int]) -> dict[str, Any]:
    run = read_json(run_path)
    targets = load_candidate_targets()
    rows = []
    for item in run.get("queries", []):
        target = targets.get(question_key(item.get("question", "")), {})
        target_pages = set(target.get("target_pages", []))
        hits = item.get("hits", [])
        rank = None
        for hit in hits:
            if page_key(hit) in target_pages:
                rank = int(hit.get("rank", 0) or 0)
                break
        rows.append(
            {
                "qid": item.get("qid"),
                "candidate_qid": target.get("candidate_qid"),
                "category": target.get("category"),
                "question": item.get("question"),
                "target_pages": [
                    {"doc_name": doc_name, "page": page} for doc_name, page in target_pages
                ],
                "rank": rank,
                "top_hit": hits[0] if hits else None,
            }
        )

    total = len(rows)
    metrics = {}
    for k in ks:
        hits_at_k = sum(1 for row in rows if row["rank"] and row["rank"] <= k)
        metrics[f"hit@{k}"] = hits_at_k / total if total else 0.0
        metrics[f"count@{k}"] = hits_at_k
    max_k = max(ks) if ks else 0
    metrics[f"mrr@{max_k}"] = (
        sum(1.0 / row["rank"] for row in rows if row["rank"] and row["rank"] <= max_k) / total
        if total
        else 0.0
    )
    return {"run": str(run_path), "system": run.get("system"), "total": total, "metrics": metrics, "rows": rows}


def load_page_texts() -> dict[tuple[str, int], str]:
    texts: dict[tuple[str, int], str] = {}
    manifest = load_manifest()
    article_to_key = {}
    for article_id, item in manifest.items():
        key = (str(item["doc_name"]).casefold(), int(item["page"]))
        texts[key] = ""
        article_to_key[article_id] = key

    if EXTRACTED_PAGES_PATH.exists():
        with EXTRACTED_PAGES_PATH.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                item = json.loads(line)
                doc_name = str(item.get("relative_path") or item.get("source_file") or "").casefold()
                try:
                    page = int(item.get("page"))
                except (TypeError, ValueError):
                    continue
                key = (doc_name, page)
                if key in texts:
                    texts[key] = str(item.get("text") or "")

    if OCR_CACHE_DIR.exists():
        for path in OCR_CACHE_DIR.glob("*.txt"):
            match = re.match(r"^(\d+)_", path.name)
            if not match:
                continue
            key = article_to_key.get(int(match.group(1)))
            if key is None:
                continue
            ocr_text = path.read_text(encoding="utf-8", errors="replace").strip()
            if ocr_text:
                texts[key] = (texts.get(key, "") + "\n" + ocr_text).strip()
    return texts


def lexical_score(question: str, page_text: str, doc_name: str) -> float:
    q_terms = Counter(tokenize(question))
    if not q_terms:
        return 0.0
    text_terms = Counter(tokenize(page_text + "\n" + doc_name))
    if not text_terms:
        return 0.0
    overlap = 0.0
    for term, q_count in q_terms.items():
        tf = text_terms.get(term, 0)
        if tf:
            overlap += q_count * (1.0 + math.log(tf))
    return overlap / max(sum(q_terms.values()), 1)


def rerank_with_local_text(input_run: Path, output_run: Path, top_k: int = 5) -> None:
    run = read_json(input_run)
    page_texts = load_page_texts()
    reranked_queries = []
    for query in run.get("queries", []):
        hits = query.get("hits", [])
        if not hits:
            reranked_queries.append({**query, "hits": []})
            continue
        scores = [float(hit.get("score", 0.0)) for hit in hits]
        min_score = min(scores)
        max_score = max(scores)
        span = max(max_score - min_score, 1e-9)
        enriched = []
        for hit in hits:
            key = page_key(hit)
            page_text = page_texts.get(key, "")
            normalized_pixelrag = (float(hit.get("score", 0.0)) - min_score) / span
            local_text = lexical_score(query.get("question", ""), page_text, str(hit.get("doc_name", "")))
            combined = 0.75 * normalized_pixelrag + 0.25 * min(local_text, 3.0) / 3.0
            enriched_hit = dict(hit)
            enriched_hit["pixelrag_score"] = float(hit.get("score", 0.0))
            enriched_hit["local_text_score"] = local_text
            enriched_hit["rerank_score"] = combined
            enriched.append(enriched_hit)
        reranked = sorted(enriched, key=lambda item: item["rerank_score"], reverse=True)[:top_k]
        for rank, hit in enumerate(reranked, 1):
            hit["rank"] = rank
            hit["score"] = hit["rerank_score"]
        updated_query = dict(query)
        updated_query["hits"] = reranked
        reranked_queries.append(updated_query)

    write_json(
        output_run,
        {
            "system": "pixelrag_top20_local_text_rerank",
            "source_run": str(input_run),
            "top_k": top_k,
            "note": "Local text/OCR rerank over PixelRAG top-20; not a true VLM visual reranker.",
            "queries": reranked_queries,
        },
    )
    print(f"Saved reranked run to {output_run}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--top20-output", type=Path, default=DEFAULT_TOP20_RUN)
    parser.add_argument("--reranked-output", type=Path, default=DEFAULT_RERANKED_RUN)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--skip-search", action="store_true", help="Reuse an existing top-k run file.")
    parser.add_argument("--skip-rerank", action="store_true")
    args = parser.parse_args()

    if not args.skip_search:
        search_topk(args.api_url, args.top_k, args.top20_output)

    report = {"topk": evaluate_run(args.top20_output, [5, 10, args.top_k])}
    if not args.skip_rerank:
        rerank_with_local_text(args.top20_output, args.reranked_output, top_k=5)
        report["reranked"] = evaluate_run(args.reranked_output, [5])

    write_json(args.report_output, report)
    print(f"Saved report to {args.report_output}")
    print(json.dumps({name: item["metrics"] for name, item in report.items()}, indent=2))


if __name__ == "__main__":
    main()
