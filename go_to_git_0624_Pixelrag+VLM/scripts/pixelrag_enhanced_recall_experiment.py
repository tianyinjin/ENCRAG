"""Enhanced recall experiment for PixelRAG page retrieval.

This separate script tries to improve recall beyond raw PixelRAG top-k by:

1. Running PixelRAG with a larger candidate pool, default top-50.
2. Ensuring OCR text exists for every page in the PixelRAG manifest.
3. Building a page-level BM25 run from extracted PDF text plus full-page OCR.
4. Combining PixelRAG and BM25 candidates with weighted reciprocal-rank fusion.

It writes new files only; it does not modify the notebook or previous runs.
"""

from __future__ import annotations

import argparse
import json
import math
import os
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
EVIDENCE_DIR = EXPERIMENT_DIR / "evidence"
OCR_CACHE_DIR = EVIDENCE_DIR / "ocr_cache"

QUESTIONS_PATH = EXPERIMENT_DIR / "questions_only.json"
CANDIDATES_PATH = EXPERIMENT_DIR / "query_candidates.json"
MANIFEST_PATH = EXPERIMENT_DIR / "corpus_manifest.jsonl"
EXTRACTED_PAGES_PATH = PROJECT_ROOT / "pymupdf_extract_output" / "extracted_pages.jsonl"

DEFAULT_TESSERACT_CMD = Path(r"E:\CodexWorkspace\ocr\tesseract.exe")
DEFAULT_TESSDATA_DIR = Path(r"E:\CodexWorkspace\ocr\tessdata")
DEFAULT_OCR_LANG = "fra+eng"
DEFAULT_API_URL = "http://127.0.0.1:30001"

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


def question_key(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(text)).casefold()).strip()


def tokenize(text: str) -> list[str]:
    return [m.group(0) for m in WORD_RE.finditer(normalize_text(text)) if len(m.group(0)) >= 2]


def page_key(item: dict[str, Any]) -> tuple[str, int]:
    return str(item["doc_name"]).casefold(), int(item["page"])


def load_manifest() -> list[dict[str, Any]]:
    records = []
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def load_queries() -> list[dict[str, str]]:
    data = read_json(QUESTIONS_PATH)
    return [
        {"qid": f"Q{index:03d}", "question": str(question)}
        for index, question in enumerate(data.get("questions", []), 1)
        if str(question).strip()
    ]


def post_json(url: str, payload: dict[str, Any], timeout: int = 300) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def search_pixelrag(api_url: str, top_k: int, output: Path, overfetch_multiplier: int = 5) -> None:
    queries = load_queries()
    manifest = {int(item["article_id"]): item for item in load_manifest()}
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
        page_hits: dict[tuple[str, int], dict[str, Any]] = {}
        for hit in response.get("results", [{}])[0].get("hits", []):
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
    print(f"Saved PixelRAG top-{top_k} run to {output}")


def clean_ocr_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def ocr_cache_path(record: dict[str, Any]) -> Path:
    image_stem = Path(str(record["image_path"])).stem
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", image_stem)[:120]
    return OCR_CACHE_DIR / f"{int(record['article_id'])}_{safe_stem}.txt"


def ensure_full_ocr(lang: str, psm: int, force: bool = False) -> dict[str, int]:
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Full OCR requires Pillow and pytesseract in the active environment.") from exc

    if DEFAULT_TESSERACT_CMD.exists():
        pytesseract.pytesseract.tesseract_cmd = str(DEFAULT_TESSERACT_CMD)
    if DEFAULT_TESSDATA_DIR.exists():
        os.environ.setdefault("TESSDATA_PREFIX", str(DEFAULT_TESSDATA_DIR))

    config = f"--psm {psm}"
    if DEFAULT_TESSDATA_DIR.exists():
        config += f" --tessdata-dir {DEFAULT_TESSDATA_DIR}"

    OCR_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    created = 0
    reused = 0
    failed = 0
    for record in load_manifest():
        cache_path = ocr_cache_path(record)
        if cache_path.exists() and not force:
            reused += 1
            continue
        try:
            with Image.open(record["image_path"]) as image:
                text = pytesseract.image_to_string(image, lang=lang, config=config)
            cache_path.write_text(clean_ocr_text(text) + "\n", encoding="utf-8")
            created += 1
        except Exception as exc:  # OCR failures should not abort the whole retrieval experiment.
            cache_path.write_text(f"\n[OCR_ERROR] {type(exc).__name__}: {exc}\n", encoding="utf-8")
            failed += 1
    stats = {"created": created, "reused": reused, "failed": failed}
    print(f"OCR cache stats: {stats}")
    return stats


def load_page_texts() -> dict[tuple[str, int], str]:
    manifest = load_manifest()
    page_texts = {(str(item["doc_name"]).casefold(), int(item["page"])): "" for item in manifest}
    article_to_key = {
        int(item["article_id"]): (str(item["doc_name"]).casefold(), int(item["page"]))
        for item in manifest
    }
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
                if key in page_texts:
                    page_texts[key] = str(item.get("text") or "")

    if OCR_CACHE_DIR.exists():
        for path in OCR_CACHE_DIR.glob("*.txt"):
            match = re.match(r"^(\d+)_", path.name)
            if not match:
                continue
            key = article_to_key.get(int(match.group(1)))
            if key is None:
                continue
            text = path.read_text(encoding="utf-8", errors="replace").strip()
            if text:
                page_texts[key] = (page_texts.get(key, "") + "\n" + text).strip()
    return page_texts


def build_bm25_run(output: Path, top_k: int = 50) -> None:
    manifest = load_manifest()
    page_texts = load_page_texts()
    docs = []
    for record in manifest:
        key = (str(record["doc_name"]).casefold(), int(record["page"]))
        text = f"{record['doc_name']} page {record['page']}\n{page_texts.get(key, '')}"
        tokens = tokenize(text)
        docs.append(
            {
                "doc_name": record["doc_name"],
                "page": int(record["page"]),
                "image_path": record["image_path"],
                "article_id": int(record["article_id"]),
                "tokens": tokens,
                "tf": Counter(tokens),
                "length": max(len(tokens), 1),
            }
        )
    n_docs = len(docs)
    avgdl = sum(doc["length"] for doc in docs) / max(n_docs, 1)
    df = Counter()
    for doc in docs:
        df.update(doc["tf"].keys())
    inverted: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for index, doc in enumerate(docs):
        for term, tf in doc["tf"].items():
            inverted[term].append((index, tf))

    k1 = 1.5
    b = 0.75
    run_queries = []
    for query in load_queries():
        q_terms = Counter(tokenize(query["question"]))
        scores: dict[int, float] = defaultdict(float)
        for term, q_count in q_terms.items():
            postings = inverted.get(term)
            if not postings:
                continue
            idf = math.log((n_docs - df[term] + 0.5) / (df[term] + 0.5) + 1.0)
            for index, tf in postings:
                doc = docs[index]
                denom = tf + k1 * (1.0 - b + b * doc["length"] / avgdl)
                scores[index] += idf * (tf * (k1 + 1.0) / denom) * q_count
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
        hits = []
        for rank, (index, score) in enumerate(ranked, 1):
            doc = docs[index]
            hits.append(
                {
                    "rank": rank,
                    "score": float(score),
                    "doc_name": doc["doc_name"],
                    "page": doc["page"],
                    "image_path": doc["image_path"],
                    "article_id": doc["article_id"],
                }
            )
        run_queries.append({"qid": query["qid"], "question": query["question"], "hits": hits})
    write_json(
        output,
        {
            "system": "bm25_full_page_text_ocr",
            "top_k": top_k,
            "retriever": {
                "source": "extracted_pages_jsonl_plus_full_ocr_cache",
                "pages": n_docs,
                "k1": k1,
                "b": b,
            },
            "queries": run_queries,
        },
    )
    print(f"Saved BM25 full-page text/OCR run to {output}")


def weighted_rrf(
    input_runs: list[tuple[Path, float]], output: Path, top_k: int = 20, rrf_k: int = 60
) -> None:
    runs = [(read_json(path), weight) for path, weight in input_runs]
    by_run = [({item["qid"]: item for item in run.get("queries", [])}, weight, run) for run, weight in runs]
    qids = sorted(set().union(*(mapping.keys() for mapping, _, _ in by_run)))
    fused_queries = []
    for qid in qids:
        scores: dict[tuple[str, int], float] = defaultdict(float)
        pages: dict[tuple[str, int], dict[str, Any]] = {}
        question = ""
        sources: dict[tuple[str, int], list[str]] = defaultdict(list)
        for mapping, weight, run in by_run:
            item = mapping.get(qid)
            if not item:
                continue
            question = question or item.get("question", "")
            system = run.get("system") or "run"
            for fallback_rank, hit in enumerate(item.get("hits", []), 1):
                key = page_key(hit)
                rank = int(hit.get("rank", fallback_rank))
                scores[key] += weight / (rrf_k + rank)
                pages[key] = {
                    "doc_name": hit["doc_name"],
                    "page": int(hit["page"]),
                    "image_path": hit.get("image_path"),
                    "article_id": hit.get("article_id"),
                }
                sources[key].append(f"{system}@{rank}")
        ranked = sorted(scores, key=scores.get, reverse=True)[:top_k]
        hits = []
        for rank, key in enumerate(ranked, 1):
            hit = {"rank": rank, "score": scores[key], **pages[key], "sources": sources[key]}
            hits.append(hit)
        fused_queries.append({"qid": qid, "question": question, "hits": hits})
    write_json(
        output,
        {
            "system": "weighted_rrf_pixelrag_bm25_full_ocr",
            "rrf_k": rrf_k,
            "inputs": [{"path": str(path), "weight": weight} for path, weight in input_runs],
            "top_k": top_k,
            "queries": fused_queries,
        },
    )
    print(f"Saved enhanced weighted-RRF run to {output}")


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
            "target_pages": pages,
        }
    return targets


def evaluate_run(run_path: Path, ks: list[int]) -> dict[str, Any]:
    run = read_json(run_path)
    targets = load_candidate_targets()
    rows = []
    for query in run.get("queries", []):
        target = targets.get(question_key(query.get("question", "")), {})
        target_pages = set(target.get("target_pages", []))
        rank = None
        for hit in query.get("hits", []):
            if page_key(hit) in target_pages:
                rank = int(hit.get("rank", 0) or 0)
                break
        rows.append(
            {
                "qid": query.get("qid"),
                "candidate_qid": target.get("candidate_qid"),
                "category": target.get("category"),
                "rank": rank,
                "target_pages": [
                    {"doc_name": doc_name, "page": page} for doc_name, page in target_pages
                ],
                "question": query.get("question"),
                "top_hit": query.get("hits", [None])[0],
            }
        )
    total = len(rows)
    metrics = {}
    for k in ks:
        count = sum(1 for row in rows if row["rank"] and row["rank"] <= k)
        metrics[f"count@{k}"] = count
        metrics[f"hit@{k}"] = count / total if total else 0.0
    max_k = max(ks)
    metrics[f"mrr@{max_k}"] = (
        sum(1.0 / row["rank"] for row in rows if row["rank"] and row["rank"] <= max_k) / total
        if total
        else 0.0
    )
    return {"run": str(run_path), "system": run.get("system"), "total": total, "metrics": metrics, "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--pixelrag-top-k", type=int, default=50)
    parser.add_argument("--bm25-top-k", type=int, default=50)
    parser.add_argument("--enhanced-top-k", type=int, default=20)
    parser.add_argument("--ocr-lang", default=DEFAULT_OCR_LANG)
    parser.add_argument("--ocr-psm", type=int, default=11)
    parser.add_argument("--force-ocr", action="store_true")
    parser.add_argument("--skip-search", action="store_true")
    parser.add_argument("--skip-ocr", action="store_true")
    parser.add_argument("--pixelrag-output", type=Path, default=RUNS_DIR / "pixelrag_top50.json")
    parser.add_argument("--bm25-output", type=Path, default=RUNS_DIR / "text_full_ocr_top50.json")
    parser.add_argument("--enhanced-output", type=Path, default=RUNS_DIR / "enhanced_recall.json")
    parser.add_argument("--report-output", type=Path, default=REPORTS_DIR / "enhanced_recall_report.json")
    args = parser.parse_args()

    if not args.skip_search:
        search_pixelrag(args.api_url, args.pixelrag_top_k, args.pixelrag_output)
    if not args.skip_ocr:
        ocr_stats = ensure_full_ocr(args.ocr_lang, args.ocr_psm, force=args.force_ocr)
    else:
        ocr_stats = {"created": 0, "reused": 0, "failed": 0, "skipped": 1}

    build_bm25_run(args.bm25_output, top_k=args.bm25_top_k)
    weighted_rrf(
        [(args.pixelrag_output, 1.0), (args.bm25_output, 0.75)],
        args.enhanced_output,
        top_k=args.enhanced_top_k,
    )

    ks = sorted(set([5, 10, 20, args.pixelrag_top_k]))
    report = {
        "ocr": ocr_stats,
        "pixelrag": evaluate_run(args.pixelrag_output, ks),
        "bm25_full_ocr": evaluate_run(args.bm25_output, [5, 10, 20, args.bm25_top_k]),
        "enhanced": evaluate_run(args.enhanced_output, [5, 10, args.enhanced_top_k]),
    }
    write_json(args.report_output, report)
    print(f"Saved enhanced recall report to {args.report_output}")
    print(json.dumps({name: data["metrics"] for name, data in report.items() if "metrics" in data}, indent=2))


if __name__ == "__main__":
    main()
