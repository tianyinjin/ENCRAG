# %% [markdown]
# # PixelRAG VLM rerank experiment
#
# This notebook/script reranks PixelRAG top-k page-image candidates with a
# vision-language model. Keep `--dry-run` for structure checks; real API calls
# require a valid `OPENAI_API_KEY`.

# %%
"""VLM rerank experiment over PixelRAG top-k candidates.

Input:
    pixelrag_visual_experiment/runs/pixelrag_top50.json

Output:
    pixelrag_visual_experiment/runs/vlm_reranked_pixelrag.json
    pixelrag_visual_experiment/reports/vlm_rerank_report.json

The script calls the OpenAI Responses API with page images and asks a vision
model to score whether each candidate page can answer the query. It batches
multiple page images per request to reduce API calls.
"""

from __future__ import annotations

import argparse
import base64
import getpass
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


# %% [markdown]
# ## Paths and defaults

# %%
PROJECT_ROOT = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
EXPERIMENT_DIR = PROJECT_ROOT / "pixelrag_visual_experiment"
RUNS_DIR = EXPERIMENT_DIR / "runs"
REPORTS_DIR = EXPERIMENT_DIR / "reports"
CANDIDATES_PATH = EXPERIMENT_DIR / "query_candidates.json"

DEFAULT_INPUT = RUNS_DIR / "pixelrag_top50.json"
DEFAULT_OUTPUT = RUNS_DIR / "vlm_reranked_pixelrag.json"
DEFAULT_CACHE = EXPERIMENT_DIR / "evidence" / "vlm_rerank_cache.jsonl"
DEFAULT_REPORT = REPORTS_DIR / "vlm_rerank_report.json"
DEFAULT_MODEL = "gpt-5.4-mini"
RESPONSES_URL = "https://api.openai.com/v1/responses"


# %% [markdown]
# ## JSON, text, and page helpers

# %%
def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_question(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).casefold()).strip()


def page_key(hit: dict[str, Any]) -> tuple[str, int]:
    return str(hit["doc_name"]).casefold(), int(hit["page"])


def data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


# %% [markdown]
# ## OpenAI Responses API helpers

# %%
def extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def post_openai(payload: dict[str, Any], api_key: str, timeout: int = 240) -> dict[str, Any]:
    request = urllib.request.Request(
        RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API HTTP {exc.code}: {body[:1000]}") from exc


def response_text(response: dict[str, Any]) -> str:
    if response.get("output_text"):
        return str(response["output_text"])
    chunks = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and "text" in content:
                chunks.append(str(content["text"]))
    return "\n".join(chunks)


# %% [markdown]
# ## Cache helpers

# %%
def load_cache(path: Path) -> dict[str, dict[str, Any]]:
    cache = {}
    if not path.exists():
        return cache
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = json.loads(line)
            cache[str(item["cache_key"])] = item
    return cache


def append_cache(path: Path, item: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False) + "\n")


# %% [markdown]
# ## VLM scoring prompt and batch request

# %%
def make_prompt(question: str, hits: list[dict[str, Any]]) -> str:
    candidates = []
    for index, hit in enumerate(hits, 1):
        candidates.append(
            {
                "id": f"C{index:02d}",
                "pixelrag_rank": hit.get("rank"),
                "pixelrag_score": hit.get("score"),
                "doc_name": hit.get("doc_name"),
                "page": hit.get("page"),
            }
        )
    return (
        "You are reranking document page images for visual retrieval.\n"
        "Question is in French. For each candidate page image, decide whether the page likely contains the answer.\n"
        "Use the image itself, including visible text, diagrams, tables, objects, captions, logos, and layout.\n"
        "Return only valid JSON with this exact shape:\n"
        '{"scores":[{"id":"C01","relevance":0.0,"answerable":false,"rationale":"short"}]}\n'
        "Rules:\n"
        "- relevance is a number from 0 to 1.\n"
        "- answerable is true only if the page appears sufficient to answer the question.\n"
        "- Do not reward pages that merely share a topic but do not answer the specific visual/text question.\n"
        "- Keep rationale under 20 words.\n\n"
        f"Question: {question}\n\n"
        f"Candidates metadata:\n{json.dumps(candidates, ensure_ascii=False, indent=2)}"
    )


def score_batch(
    question: str,
    hits: list[dict[str, Any]],
    model: str,
    detail: str,
    api_key: str,
    max_retries: int = 3,
) -> dict[str, dict[str, Any]]:
    content = [{"type": "input_text", "text": make_prompt(question, hits)}]
    for index, hit in enumerate(hits, 1):
        image_path = Path(str(hit["image_path"]))
        content.append({"type": "input_text", "text": f"Candidate C{index:02d}: {hit['doc_name']} page {hit['page']}"})
        content.append({"type": "input_image", "image_url": data_url(image_path), "detail": detail})

    payload = {
        "model": model,
        "input": [{"role": "user", "content": content}],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "page_rerank_scores",
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "scores": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "id": {"type": "string"},
                                    "relevance": {"type": "number"},
                                    "answerable": {"type": "boolean"},
                                    "rationale": {"type": "string"},
                                },
                                "required": ["id", "relevance", "answerable", "rationale"],
                            },
                        }
                    },
                    "required": ["scores"],
                },
            }
        },
    }

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = post_openai(payload, api_key)
            parsed = extract_json_object(response_text(response))
            scores = {}
            for item in parsed.get("scores", []):
                candidate_id = str(item.get("id", "")).strip()
                if candidate_id:
                    scores[candidate_id] = item
            return scores
        except (RuntimeError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if "HTTP 401" in str(exc):
                raise RuntimeError(
                    "OpenAI API returned 401 Unauthorized. Check that OPENAI_API_KEY is valid "
                    "and available in this shell before running the VLM reranker."
                ) from exc
            sleep_s = min(30, 2**attempt)
            print(f"Batch scoring failed on attempt {attempt}/{max_retries}: {exc}; sleeping {sleep_s}s")
            time.sleep(sleep_s)
    raise RuntimeError(f"VLM batch scoring failed after {max_retries} attempts: {last_error}")


# %% [markdown]
# ## Rerank PixelRAG candidates

# %%
def rerank(
    input_run: Path,
    output_run: Path,
    cache_path: Path,
    model: str,
    detail: str,
    candidate_limit: int,
    batch_size: int,
    output_top_k: int,
    limit_queries: int | None,
    qids: set[str] | None,
    dry_run: bool,
) -> None:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key and not dry_run:
        raise RuntimeError("OPENAI_API_KEY is not set. Set it or run with --dry-run.")

    run = read_json(input_run)
    cache = load_cache(cache_path)
    reranked_queries = []
    processed = 0
    for query in run.get("queries", []):
        if qids is not None and str(query.get("qid")) not in qids:
            reranked_queries.append(query)
            continue
        if limit_queries is not None and processed >= limit_queries:
            reranked_queries.append(query)
            continue
        processed += 1
        hits = list(query.get("hits", []))[:candidate_limit]
        scored_hits = []
        for start in range(0, len(hits), batch_size):
            batch = hits[start : start + batch_size]
            batch_key = "|".join(
                [
                    model,
                    detail,
                    str(query.get("qid")),
                    str(start),
                    *[f"{hit.get('doc_name')}#{hit.get('page')}#{hit.get('rank')}" for hit in batch],
                ]
            )
            if batch_key in cache:
                scores = cache[batch_key]["scores"]
            elif dry_run:
                scores = {
                    f"C{index:02d}": {
                        "id": f"C{index:02d}",
                        "relevance": max(0.0, 1.0 - (start + index - 1) / max(candidate_limit, 1)),
                        "answerable": False,
                        "rationale": "dry run",
                    }
                    for index, _ in enumerate(batch, 1)
                }
            else:
                scores = score_batch(query["question"], batch, model, detail, api_key)
                append_cache(
                    cache_path,
                    {
                        "cache_key": batch_key,
                        "qid": query.get("qid"),
                        "batch_start": start,
                        "model": model,
                        "detail": detail,
                        "scores": scores,
                    },
                )
            for local_index, hit in enumerate(batch, 1):
                candidate_id = f"C{local_index:02d}"
                item = scores.get(candidate_id, {})
                relevance = float(item.get("relevance", 0.0) or 0.0)
                enriched = dict(hit)
                enriched["pixelrag_rank"] = int(hit.get("rank", start + local_index))
                enriched["pixelrag_score"] = float(hit.get("score", 0.0) or 0.0)
                enriched["vlm_relevance"] = max(0.0, min(1.0, relevance))
                enriched["vlm_answerable"] = bool(item.get("answerable", False))
                enriched["vlm_rationale"] = str(item.get("rationale", ""))
                # Tie-break with the original PixelRAG score/rank so VLM scoring does not randomize close calls.
                enriched["score"] = enriched["vlm_relevance"] + 0.001 / max(enriched["pixelrag_rank"], 1)
                scored_hits.append(enriched)
        ranked = sorted(
            scored_hits,
            key=lambda hit: (hit["vlm_answerable"], hit["vlm_relevance"], -hit["pixelrag_rank"]),
            reverse=True,
        )[:output_top_k]
        for rank, hit in enumerate(ranked, 1):
            hit["rank"] = rank
        updated = dict(query)
        updated["hits"] = ranked
        reranked_queries.append(updated)
        print(f"Reranked {query.get('qid')} with {len(hits)} candidates")

    write_json(
        output_run,
        {
            "system": "openai_vlm_rerank",
            "source_run": str(input_run),
            "model": model,
            "detail": detail,
            "candidate_limit": candidate_limit,
            "batch_size": batch_size,
            "top_k": output_top_k,
            "dry_run": dry_run,
            "queries": reranked_queries,
        },
    )
    print(f"Saved VLM reranked run to {output_run}")


# %% [markdown]
# ## Evaluate reranked output

# %%
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
        targets[normalize_question(candidate["question"])] = {
            "candidate_qid": candidate.get("qid"),
            "category": candidate.get("category"),
            "target_pages": pages,
        }
    return targets


def evaluate(run_path: Path, report_path: Path, ks: list[int]) -> None:
    run = read_json(run_path)
    targets = load_candidate_targets()
    rows = []
    for query in run.get("queries", []):
        target = targets.get(normalize_question(query.get("question", "")), {})
        target_pages = set(target.get("target_pages", []))
        rank = None
        matched = None
        for hit in query.get("hits", []):
            if page_key(hit) in target_pages:
                rank = int(hit.get("rank", 0) or 0)
                matched = hit
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
                "top_hit": query.get("hits", [None])[0],
                "matched_hit": matched,
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
    write_json(report_path, {"run": str(run_path), "system": run.get("system"), "total": total, "metrics": metrics, "rows": rows})
    print(json.dumps(metrics, indent=2))
    print(f"Saved VLM rerank report to {report_path}")


# %% [markdown]
# ## Run from notebook
#
# Set `RUN_NOTEBOOK_RERANK = True` when you are ready to call the VLM reranker.
# Keep `NOTEBOOK_DRY_RUN = True` for a no-cost structure check. Real VLM calls
# require a valid `OPENAI_API_KEY`.

# %%
RUN_NOTEBOOK_RERANK = False
NOTEBOOK_DRY_RUN = True
NOTEBOOK_INPUT = DEFAULT_INPUT
NOTEBOOK_OUTPUT = RUNS_DIR / "vlm_reranked_pixelrag_notebook.json"
NOTEBOOK_CACHE = DEFAULT_CACHE
NOTEBOOK_REPORT = REPORTS_DIR / "vlm_rerank_notebook_report.json"
NOTEBOOK_MODEL = DEFAULT_MODEL
NOTEBOOK_DETAIL = "high"
NOTEBOOK_CANDIDATE_LIMIT = 20
NOTEBOOK_BATCH_SIZE = 5
NOTEBOOK_OUTPUT_TOP_K = 5
NOTEBOOK_LIMIT_QUERIES = 3
NOTEBOOK_QIDS = []
NOTEBOOK_OPENAI_API_KEY = ""
NOTEBOOK_FORCE_API_KEY_PROMPT = False

if RUN_NOTEBOOK_RERANK:
    if not NOTEBOOK_DRY_RUN and (NOTEBOOK_FORCE_API_KEY_PROMPT or not os.environ.get("OPENAI_API_KEY")):
        NOTEBOOK_OPENAI_API_KEY = NOTEBOOK_OPENAI_API_KEY or getpass.getpass("OpenAI API key: ")
        if NOTEBOOK_OPENAI_API_KEY:
            os.environ["OPENAI_API_KEY"] = NOTEBOOK_OPENAI_API_KEY
    rerank(
        input_run=NOTEBOOK_INPUT,
        output_run=NOTEBOOK_OUTPUT,
        cache_path=NOTEBOOK_CACHE,
        model=NOTEBOOK_MODEL,
        detail=NOTEBOOK_DETAIL,
        candidate_limit=NOTEBOOK_CANDIDATE_LIMIT,
        batch_size=NOTEBOOK_BATCH_SIZE,
        output_top_k=NOTEBOOK_OUTPUT_TOP_K,
        limit_queries=NOTEBOOK_LIMIT_QUERIES,
        qids=set(NOTEBOOK_QIDS) if NOTEBOOK_QIDS else None,
        dry_run=NOTEBOOK_DRY_RUN,
    )
    evaluate(NOTEBOOK_OUTPUT, NOTEBOOK_REPORT, [1, 3, 5])


# %% [markdown]
# ## Optional command-line entry point
#
# This block is skipped inside a Jupyter kernel unless explicitly run as a
# terminal script.

# %%
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--detail", default="high", choices=["low", "high", "original", "auto"])
    parser.add_argument("--candidate-limit", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--output-top-k", type=int, default=5)
    parser.add_argument("--limit-queries", type=int, default=None)
    parser.add_argument("--qids", nargs="*", default=None, help="Only rerank these qids, e.g. Q004 Q005")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rerank(
        input_run=args.input,
        output_run=args.output,
        cache_path=args.cache,
        model=args.model,
        detail=args.detail,
        candidate_limit=args.candidate_limit,
        batch_size=args.batch_size,
        output_top_k=args.output_top_k,
        limit_queries=args.limit_queries,
        qids=set(args.qids) if args.qids else None,
        dry_run=args.dry_run,
    )
    evaluate(args.output, args.report, [1, 3, 5])


if __name__ == "__main__" and "ipykernel" not in sys.modules:
    main()
