# %% [markdown]
# # PixelRAG visual retrieval experiment
#
# Run this file one `# %%` cell at a time in VS Code or Jupyter. Execution
# switches are disabled by default, so running a definition cell has no side
# effects. The command-line subcommands remain available for automation.

# %%
"""Prepare, run, fuse, and evaluate a small PixelRAG page-image experiment.

The query file may remain empty while the corpus and PixelRAG index are prepared.
Run ``python pixelrag_visual_experiment.py --help`` for available commands.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any


# %% [markdown]
# ## 1. Paths and experiment configuration

# %%
PROJECT_ROOT = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
IMAGE_DIR = PROJECT_ROOT / "pymupdf_extract_output" / "ocr_review_page_renders"
OCR_DETAIL_CSV = PROJECT_ROOT / "pymupdf_extract_output" / "needs_ocr_pages_detail.csv"
EXPERIMENT_DIR = PROJECT_ROOT / "pixelrag_visual_experiment"
TILES_DIR = EXPERIMENT_DIR / "index" / "tiles"
EMBEDDINGS_DIR = EXPERIMENT_DIR / "index" / "embeddings"
INDEX_DIR = EXPERIMENT_DIR / "index"
MANIFEST_PATH = EXPERIMENT_DIR / "corpus_manifest.jsonl"
ARTICLES_PATH = INDEX_DIR / "articles.json"
# Active evaluation set. Change only this filename to switch query sets while
# keeping the original files intact.
QUERIES_FILENAME = "questions_only.json"
QUERIES_PATH = EXPERIMENT_DIR / QUERIES_FILENAME
RUNS_DIR = EXPERIMENT_DIR / "runs"
REPORTS_DIR = EXPERIMENT_DIR / "reports"
EVIDENCE_DIR = EXPERIMENT_DIR / "evidence"
OCR_CACHE_DIR = EVIDENCE_DIR / "ocr_cache"

IMAGE_NAME_RE = re.compile(r"^(?P<stem>.+)__p(?P<page>\d+)$")
DEFAULT_MODEL = "Qwen/Qwen3-VL-Embedding-2B"
DEFAULT_HF_ENDPOINT = "https://hf-mirror.com"
LOCAL_MODEL_PATH = Path(
    r"C:\Users\67600\.cache\huggingface\hub\models--Qwen--Qwen3-VL-Embedding-2B"
    r"\snapshots\9f2f7e710d6d81056aa5c0a4f04764fec6bb7bda"
)
DEFAULT_OCR_LANG = "fra+eng"
DEFAULT_TESSERACT_CMD = Path(r"E:\CodexWorkspace\ocr\tesseract.exe")
DEFAULT_TESSDATA_DIR = Path(r"E:\CodexWorkspace\ocr\tessdata")
PIXELRAG_VENV_DIR = PROJECT_ROOT / ".venv-pixelrag"


# %% [markdown]
# ## 2. Optional Python 3.12 environment setup
#
# This block can create a project-local environment before the PixelRAG stages
# are run. Package installation requires internet access. A running notebook
# cannot switch its own kernel; select `.venv-pixelrag` in the kernel picker
# after this block finishes.

# %%
def create_pixelrag_environment(
    venv_dir: Path = PIXELRAG_VENV_DIR,
    install_packages: bool = False,
) -> Path:
    """Create the Python 3.12 environment and optionally install dependencies."""
    python_path = venv_dir / "Scripts" / "python.exe"
    if not python_path.exists():
        command = ["py", "-3.12", "-m", "venv", str(venv_dir)]
        print("+", subprocess.list2cmdline(command))
        subprocess.run(command, check=True)
    else:
        print(f"Environment already exists: {venv_dir}")

    if install_packages:
        commands = [
            [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
            [
                str(python_path),
                "-m",
                "pip",
                "install",
                "pixelrag[index,serve]",
                "ipykernel",
            ],
        ]
        for command in commands:
            print("+", subprocess.list2cmdline(command))
            subprocess.run(command, check=True)

    print(f"PixelRAG Python: {python_path}")
    return python_path


# %% [markdown]
# ### Create/install the environment
#
# Set `RUN_CREATE_ENVIRONMENT` to `True` to create it. Set
# `INSTALL_ENVIRONMENT_PACKAGES` to `True` only when dependency downloads are
# intended.

# %%
RUN_CREATE_ENVIRONMENT = False
INSTALL_ENVIRONMENT_PACKAGES = False

if RUN_CREATE_ENVIRONMENT:
    pixelrag_python = create_pixelrag_environment(
        install_packages=INSTALL_ENVIRONMENT_PACKAGES
    )


# %% [markdown]
# ## 3. JSON and source-metadata helpers

# %%
def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_source_names() -> dict[str, str]:
    """Map rendered filename stems back to original PDF filenames."""
    if not OCR_DETAIL_CSV.exists():
        return {}
    import csv

    mapping: dict[str, str] = {}
    with OCR_DETAIL_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            source = (row.get("source_file") or "").strip()
            if source:
                mapping[Path(source).stem.casefold()] = source
    return mapping


# %% [markdown]
# ## 4. Scan page images and prepare PixelRAG tiles

# This stage does not require queries or PixelRAG model dependencies.

# %%
def scan_images() -> list[dict[str, Any]]:
    if not IMAGE_DIR.is_dir():
        raise FileNotFoundError(f"Image directory not found: {IMAGE_DIR}")
    source_names = load_source_names()
    records = []
    for image_path in sorted(IMAGE_DIR.glob("*.png"), key=lambda p: p.name.casefold()):
        match = IMAGE_NAME_RE.match(image_path.stem)
        if not match:
            raise ValueError(f"Unexpected image filename: {image_path.name}")
        stem = match.group("stem")
        page = int(match.group("page"))
        records.append(
            {
                "article_id": len(records),
                "doc_name": source_names.get(stem.casefold(), f"{stem}.pdf"),
                "page": page,
                "image_path": str(image_path.resolve()),
                "image_name": image_path.name,
            }
        )
    if not records:
        raise ValueError(f"No PNG images found in {IMAGE_DIR}")
    return records


def link_or_copy(source: Path, target: Path) -> str:
    if target.exists():
        return "existing"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, target)
        return "hardlink"
    except OSError:
        shutil.copy2(source, target)
        return "copy"


def prepare(force: bool = False) -> list[dict[str, Any]]:
    """Create PixelRAG's tile layout without duplicating images where possible."""
    records = scan_images()
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    link_modes: defaultdict[str, int] = defaultdict(int)

    for record in records:
        article_dir = TILES_DIR / f"{record['article_id']}.png.tiles"
        tile_path = article_dir / "tile_0000.png"
        if force and tile_path.exists():
            tile_path.unlink()
        mode = link_or_copy(Path(record["image_path"]), tile_path)
        link_modes[mode] += 1

        try:
            from PIL import Image

            with Image.open(tile_path) as image:
                width, height = image.size
        except ImportError:
            width, height = 0, 0

        tiles_meta = {
            "complete": True,
            "page_height": height,
            "viewport_width": width,
            "tile_height": height,
            "tiles": [tile_path.name],
        }
        write_json(article_dir / "tiles.json", tiles_meta)
        record.update({"width": width, "height": height, "tile_dir": str(article_dir.resolve())})

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    articles = [
        {
            "title": f"{record['doc_name']} - page {record['page']}",
            "url": "",
        }
        for record in records
    ]
    write_json(ARTICLES_PATH, articles)
    if not QUERIES_PATH.exists():
        write_json(QUERIES_PATH, {"schema_version": 1, "queries": []})
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    unique_docs = len({record["doc_name"] for record in records})
    print(f"Prepared {len(records)} page images from {unique_docs} documents.")
    print("Image materialization:", dict(link_modes))
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Empty query template: {QUERIES_PATH}")
    return records


# %% [markdown]
# ### Run corpus preparation
#
# Change `RUN_PREPARE` to `True` and run only this cell when needed.

# %%
RUN_PREPARE = False
PREPARE_FORCE = False

if RUN_PREPARE:
    prepared_records = prepare(force=PREPARE_FORCE)


# %% [markdown]
# ## 5. Build the PixelRAG visual index
#
# Run this cell in the separate Python 3.12 environment containing PixelRAG.

# %%
def run_command(command: list[str]) -> None:
    print("+", subprocess.list2cmdline(command))
    subprocess.run(command, check=True)


def build_index(
    device: str,
    model: str,
    backend: str,
    nlist: int,
    batch_size: int,
    max_pixels: int,
    hf_endpoint: str = DEFAULT_HF_ENDPOINT,
) -> None:
    if not MANIFEST_PATH.exists():
        prepare()
    if hf_endpoint:
        os.environ["HF_ENDPOINT"] = hf_endpoint
        print(f"HF_ENDPOINT={hf_endpoint}")
    python = sys.executable
    run_command(
        [python, "-m", "pixelrag_embed.chunk", "--shard-dir", str(TILES_DIR), "--workers", "1"]
    )
    if device == "cuda":
        command = [
            python,
            "-m",
            "pixelrag_embed.embed",
            "--shard-dir",
            str(TILES_DIR),
            "--output-dir",
            str(EMBEDDINGS_DIR),
            "--gpu-ids",
            "0",
            "--model",
            model,
            "--backend",
            backend,
            "--batch-size",
            str(batch_size),
            "--max-pixels",
            str(max_pixels),
        ]
    else:
        command = [
            python,
            "-m",
            "pixelrag_embed.embed_cpu",
            "--shard-dir",
            str(TILES_DIR),
            "--output-dir",
            str(EMBEDDINGS_DIR),
            "--model",
            model,
        ]
    run_command(command)
    run_command(
        [
            python,
            "-m",
            "pixelrag_embed.index",
            "build",
            "--embeddings-dir",
            str(EMBEDDINGS_DIR),
            "--output-dir",
            str(INDEX_DIR),
            "--nlist",
            str(nlist),
        ]
    )
    print("Index ready. Start the local API with:")
    print(
        subprocess.list2cmdline(
            [
                python,
                "-m",
                "pixelrag_serve.api",
                "--index-dir",
                str(INDEX_DIR),
                "--tiles-dir",
                str(TILES_DIR),
                "--articles-json",
                str(ARTICLES_PATH),
                "--model",
                model,
                "--device",
                device,
                "--port",
                "30001",
            ]
        )
    )


# %% [markdown]
# ### Run index construction
#
# This is the expensive stage. It is disabled by default and does not need
# `queries.json`.

# %%
RUN_BUILD_INDEX = False
BUILD_DEVICE = "cuda"
BUILD_MODEL = str(LOCAL_MODEL_PATH) if LOCAL_MODEL_PATH.exists() else DEFAULT_MODEL
BUILD_BACKEND = "direct_gpu"
BUILD_NLIST = 8
BUILD_BATCH_SIZE = 1
BUILD_MAX_PIXELS = 120000
BUILD_HF_ENDPOINT = DEFAULT_HF_ENDPOINT

if RUN_BUILD_INDEX:
    build_index(
        device=BUILD_DEVICE,
        model=BUILD_MODEL,
        backend=BUILD_BACKEND,
        nlist=BUILD_NLIST,
        batch_size=BUILD_BATCH_SIZE,
        max_pixels=BUILD_MAX_PIXELS,
        hf_endpoint=BUILD_HF_ENDPOINT,
    )


# %% [markdown]
# ## 6. Load manifest and optional queries

# An empty query list is valid. It only prevents retrieval and evaluation.

# %%
def load_manifest() -> dict[int, dict[str, Any]]:
    records = {}
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                item = json.loads(line)
                records[int(item["article_id"])] = item
    return records


def load_queries() -> list[dict[str, Any]]:
    data = read_json(QUERIES_PATH)
    queries = data.get("queries", [])
    if not queries and data.get("questions"):
        queries = [
            {
                "qid": f"Q{index:03d}",
                "question": question,
                "relevant_pages": [],
            }
            for index, question in enumerate(data["questions"], 1)
            if str(question).strip()
        ]
    for index, query in enumerate(queries, 1):
        if not query.get("qid") or not query.get("question"):
            raise ValueError(f"Query {index} must contain non-empty qid and question")
        query.setdefault("relevant_pages", [])
    return queries


def post_json(url: str, payload: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


# %% [markdown]
# ## 7. Search a running local PixelRAG API

# Start the API using the command printed by the index-building cell. Then set
# `RUN_SEARCH` to `True` after questions have been added.

# %%
def search(api_url: str, top_k: int, output: Path) -> None:
    queries = load_queries()
    print(f"Loaded {len(queries)} queries from {QUERIES_PATH}")
    if not queries:
        raise ValueError(
            f"No queries found in {QUERIES_PATH}. Expected either "
            '{"queries": [{"qid": "...", "question": "..."}]} or '
            '{"questions": ["..."]}.'
        )
    manifest = load_manifest()
    run_queries = []
    for query in queries:
        started = time.perf_counter()
        response = post_json(
            api_url.rstrip("/") + "/search",
            {"queries": [{"text": query["question"]}], "n_docs": max(top_k * 4, top_k)},
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
    print(f"Saved {len(run_queries)} query results to {output}")


# %% [markdown]
# ### Run visual retrieval

# %%
RUN_SEARCH = False
SEARCH_API_URL = "http://127.0.0.1:30001"
SEARCH_TOP_K = 5
SEARCH_OUTPUT = RUNS_DIR / "pixelrag.json"

if RUN_SEARCH:
    search(SEARCH_API_URL, SEARCH_TOP_K, SEARCH_OUTPUT)


# %% [markdown]
# ## 8. Extract readable evidence from rendered-image hits
#
# This post-processing stage reads the retrieved PNG page renders, runs OCR, and
# adds a short text evidence field to each visual hit. Install `pytesseract` and
# the Tesseract OCR executable with French language data before running it.

# %%
STOPWORDS = {
    "avec",
    "dans",
    "des",
    "du",
    "elle",
    "est",
    "ils",
    "les",
    "leur",
    "leurs",
    "pour",
    "que",
    "quel",
    "quelle",
    "quels",
    "quelles",
    "qui",
    "sont",
    "sur",
    "une",
}


def normalize_for_match(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text.casefold()


def question_terms(question: str) -> set[str]:
    words = re.findall(r"[a-zA-ZÀ-ÿ0-9]{4,}", normalize_for_match(question))
    return {word for word in words if word not in STOPWORDS}


def clean_ocr_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def ocr_rendered_image(image_path: Path, lang: str = DEFAULT_OCR_LANG) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "OCR evidence extraction requires Pillow and pytesseract. "
            "Install them in the active environment, and install the Tesseract "
            "OCR executable with French language data."
        ) from exc

    if DEFAULT_TESSERACT_CMD.exists():
        pytesseract.pytesseract.tesseract_cmd = str(DEFAULT_TESSERACT_CMD)
    if DEFAULT_TESSDATA_DIR.exists():
        os.environ.setdefault("TESSDATA_PREFIX", str(DEFAULT_TESSDATA_DIR))
    config = "--psm 6"
    if DEFAULT_TESSDATA_DIR.exists():
        config += f" --tessdata-dir {DEFAULT_TESSDATA_DIR}"

    with Image.open(image_path) as image:
        return clean_ocr_text(pytesseract.image_to_string(image, lang=lang, config=config))


def ocr_cache_path(hit: dict[str, Any]) -> Path:
    article_id = str(hit.get("article_id", "unknown"))
    image_stem = Path(str(hit["image_path"])).stem
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", image_stem)[:120]
    return OCR_CACHE_DIR / f"{article_id}_{safe_stem}.txt"


def load_or_create_ocr_text(hit: dict[str, Any], lang: str, force: bool = False) -> tuple[str, Path]:
    if "image_path" not in hit:
        return "", Path()
    image_path = Path(str(hit["image_path"]))
    cache_path = ocr_cache_path(hit)
    if cache_path.exists() and not force:
        return cache_path.read_text(encoding="utf-8"), cache_path
    text = ocr_rendered_image(image_path, lang=lang)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(text + "\n", encoding="utf-8")
    return text, cache_path


def select_evidence(question: str, ocr_text: str, max_lines: int = 3) -> str:
    lines = [line for line in ocr_text.splitlines() if len(line) >= 8]
    if not lines:
        return ""
    terms = question_terms(question)
    if not terms:
        return " ".join(lines[:max_lines])

    scored = []
    for index, line in enumerate(lines):
        normalized = normalize_for_match(line)
        overlap = sum(1 for term in terms if term in normalized)
        # Prefer relevant, information-dense lines without letting long headers dominate.
        score = overlap * 10 + min(len(line), 180) / 180 - index / 1000
        scored.append((score, index, line))
    best = sorted(scored, reverse=True)[:max_lines]
    ordered = [line for _, _, line in sorted(best, key=lambda item: item[1])]
    return " ".join(ordered)


def add_ocr_evidence(
    run_path: Path,
    output: Path,
    lang: str = DEFAULT_OCR_LANG,
    max_lines: int = 3,
    force_ocr: bool = False,
) -> None:
    run = read_json(run_path)
    updated_queries = []
    for query in run.get("queries", []):
        question = str(query.get("question", ""))
        hits = []
        for hit in query.get("hits", []):
            enriched = dict(hit)
            ocr_text, cache_path = load_or_create_ocr_text(enriched, lang=lang, force=force_ocr)
            enriched["evidence"] = select_evidence(question, ocr_text, max_lines=max_lines)
            enriched["evidence_source"] = "render_ocr"
            if cache_path:
                enriched["ocr_text_path"] = str(cache_path)
            hits.append(enriched)
        updated = dict(query)
        updated["hits"] = hits
        updated_queries.append(updated)
    enriched_run = dict(run)
    enriched_run["queries"] = updated_queries
    enriched_run["evidence"] = {"source": "render_ocr", "ocr_lang": lang, "max_lines": max_lines}
    write_json(output, enriched_run)
    print(f"Saved OCR-enriched run to {output}")


# %% [markdown]
# ### Run OCR evidence extraction

# %%
RUN_EVIDENCE_EXTRACTION = False
EVIDENCE_INPUT = RUNS_DIR / "pixelrag.json"
EVIDENCE_OUTPUT = RUNS_DIR / "pixelrag_with_evidence.json"
EVIDENCE_OCR_LANG = DEFAULT_OCR_LANG
EVIDENCE_MAX_LINES = 3
EVIDENCE_FORCE_OCR = False

if RUN_EVIDENCE_EXTRACTION:
    add_ocr_evidence(
        EVIDENCE_INPUT,
        EVIDENCE_OUTPUT,
        lang=EVIDENCE_OCR_LANG,
        max_lines=EVIDENCE_MAX_LINES,
        force_ocr=EVIDENCE_FORCE_OCR,
    )


# %% [markdown]
# ## 9. Fuse text and visual runs with Reciprocal Rank Fusion

# %%
def page_key(item: dict[str, Any]) -> tuple[str, int]:
    return str(item["doc_name"]).casefold(), int(item["page"])


def fuse_runs(input_paths: list[Path], output: Path, top_k: int, rrf_k: int) -> None:
    runs = [read_json(path) for path in input_paths]
    by_run = [{item["qid"]: item for item in run.get("queries", [])} for run in runs]
    qids = sorted(set().union(*(mapping.keys() for mapping in by_run)))
    fused_queries = []
    for qid in qids:
        scores: defaultdict[tuple[str, int], float] = defaultdict(float)
        pages: dict[tuple[str, int], dict[str, Any]] = {}
        question = ""
        for mapping in by_run:
            item = mapping.get(qid)
            if not item:
                continue
            question = question or item.get("question", "")
            for fallback_rank, hit in enumerate(item.get("hits", []), 1):
                key = page_key(hit)
                rank = int(hit.get("rank", fallback_rank))
                scores[key] += 1.0 / (rrf_k + rank)
                pages[key] = {"doc_name": hit["doc_name"], "page": int(hit["page"])}
        ranked = sorted(scores, key=scores.get, reverse=True)[:top_k]
        hits = [
            {"rank": rank, "score": scores[key], **pages[key]}
            for rank, key in enumerate(ranked, 1)
        ]
        fused_queries.append({"qid": qid, "question": question, "hits": hits})
    write_json(output, {"system": "rrf_fusion", "rrf_k": rrf_k, "queries": fused_queries})
    print(f"Saved fused run to {output}")


# %% [markdown]
# ### Run RRF fusion
#
# The text result file must use the same `qid` and page-level hit schema.

# %%
RUN_FUSION = False
FUSION_INPUTS = [RUNS_DIR / "text.json", RUNS_DIR / "pixelrag.json"]
FUSION_OUTPUT = RUNS_DIR / "fusion.json"
FUSION_TOP_K = 5
FUSION_RRF_K = 60

if RUN_FUSION:
    fuse_runs(FUSION_INPUTS, FUSION_OUTPUT, FUSION_TOP_K, FUSION_RRF_K)


# %% [markdown]
# ## 10. Evaluate page retrieval

# Queries without `relevant_pages` are intentionally skipped.

# %%
def metrics_for_query(hits: list[dict[str, Any]], relevant: set[tuple[str, int]], k: int) -> dict[str, float]:
    ranked = [page_key(hit) for hit in hits[:k]]
    gains = [1.0 if key in relevant else 0.0 for key in ranked]
    found = sum(gains)
    first_rank = next((rank for rank, gain in enumerate(gains, 1) if gain), None)
    dcg = sum(gain / math.log2(rank + 1) for rank, gain in enumerate(gains, 1))
    ideal_count = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_count + 1))
    return {
        f"hit@{k}": float(found > 0),
        f"recall@{k}": found / len(relevant),
        "reciprocal_rank": 1.0 / first_rank if first_rank else 0.0,
        f"ndcg@{k}": dcg / idcg if idcg else 0.0,
    }


def evaluate(run_paths: list[Path], output: Path, k: int) -> None:
    queries = load_queries()
    judged = {query["qid"]: query for query in queries if query.get("relevant_pages")}
    if not judged:
        print(f"No relevance judgments yet. Add relevant_pages to {QUERIES_PATH}.")
        write_json(output, {"evaluated_queries": 0, "systems": {}})
        return
    report: dict[str, Any] = {"evaluated_queries": len(judged), "k": k, "systems": {}}
    for path in run_paths:
        run = read_json(path)
        system = run.get("system") or path.stem
        results = {item["qid"]: item for item in run.get("queries", [])}
        per_query = []
        for qid, query in judged.items():
            relevant = {page_key(page) for page in query["relevant_pages"]}
            item = results.get(qid, {"hits": []})
            metrics = metrics_for_query(item.get("hits", []), relevant, k)
            metrics.update({"qid": qid, "category": query.get("category", "unspecified")})
            per_query.append(metrics)
        metric_names = [f"hit@{k}", f"recall@{k}", "reciprocal_rank", f"ndcg@{k}"]
        macro = {name: sum(item[name] for item in per_query) / len(per_query) for name in metric_names}
        report["systems"][system] = {"source": str(path), "macro": macro, "per_query": per_query}
    write_json(output, report)
    print(json.dumps({name: data["macro"] for name, data in report["systems"].items()}, indent=2))
    print(f"Saved evaluation report to {output}")


# %% [markdown]
# ### Run retrieval evaluation

# %%
RUN_EVALUATION = False
EVALUATION_RUNS = [
    RUNS_DIR / "pixelrag.json",
]
EVALUATION_OUTPUT = REPORTS_DIR / "retrieval_metrics.json"
EVALUATION_K = 5

if RUN_EVALUATION:
    evaluate(EVALUATION_RUNS, EVALUATION_OUTPUT, EVALUATION_K)


# %% [markdown]
# ## 11. Optional command-line interface
#
# This section is used only when the file is launched from a terminal. It is
# skipped in a Jupyter kernel so cell execution never consumes notebook args.

# %%
def export_notebook(output_path: Path) -> None:
    """Convert this `# %%` script into a native Jupyter notebook."""
    source_path = Path(__file__).resolve()
    lines = source_path.read_text(encoding="utf-8").splitlines(keepends=True)
    cells: list[dict[str, Any]] = []
    cell_type: str | None = None
    cell_lines: list[str] = []

    def append_cell() -> None:
        if cell_type is None:
            return
        source = cell_lines
        if cell_type == "markdown":
            source = [
                re.sub(r"^# ?", "", line) if line.startswith("#") else line
                for line in source
            ]
        cells.append(
            {
                "cell_type": cell_type,
                "metadata": {},
                "source": source,
                **(
                    {"execution_count": None, "outputs": []}
                    if cell_type == "code"
                    else {}
                ),
            }
        )

    for line in lines:
        marker = re.match(r"^# %%(?: \[markdown\])?\s*$", line.rstrip("\r\n"))
        if marker:
            append_cell()
            cell_type = "markdown" if "[markdown]" in line else "code"
            cell_lines = []
        else:
            cell_lines.append(line)
    append_cell()

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3.12",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    write_json(output_path, notebook)
    code_count = sum(cell["cell_type"] == "code" for cell in cells)
    markdown_count = len(cells) - code_count
    print(
        f"Notebook written to {output_path} "
        f"({code_count} code cells, {markdown_count} markdown cells)."
    )


# %%
def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="Create manifest and PixelRAG tile layout")
    prepare_parser.add_argument("--force", action="store_true")

    build_parser = subparsers.add_parser("build", help="Chunk, embed, and build the visual index")
    build_parser.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
    build_parser.add_argument("--model", default=DEFAULT_MODEL)
    build_parser.add_argument("--backend", default="direct_gpu")
    build_parser.add_argument("--nlist", type=int, default=8)
    build_parser.add_argument(
        "--batch-size", type=int, default=1, help="Conservative default for an 8 GB GPU"
    )
    build_parser.add_argument(
        "--max-pixels",
        type=int,
        default=120000,
        help="Resize each chunk before visual embedding to control VRAM",
    )
    build_parser.add_argument(
        "--hf-endpoint",
        default=DEFAULT_HF_ENDPOINT,
        help="Hugging Face endpoint used when the model is downloaded",
    )

    search_parser = subparsers.add_parser("search", help="Query a running local PixelRAG API")
    search_parser.add_argument("--api-url", default="http://127.0.0.1:30001")
    search_parser.add_argument("--top-k", type=int, default=5)
    search_parser.add_argument("--output", type=Path, default=RUNS_DIR / "pixelrag.json")

    evidence_parser = subparsers.add_parser(
        "evidence", help="Add OCR evidence snippets to a visual run"
    )
    evidence_parser.add_argument("--input", type=Path, default=RUNS_DIR / "pixelrag.json")
    evidence_parser.add_argument("--output", type=Path, default=RUNS_DIR / "pixelrag_with_evidence.json")
    evidence_parser.add_argument("--ocr-lang", default=DEFAULT_OCR_LANG)
    evidence_parser.add_argument("--max-lines", type=int, default=3)
    evidence_parser.add_argument("--force-ocr", action="store_true")

    fuse_parser = subparsers.add_parser("fuse", help="Fuse page-ranked JSON runs with RRF")
    fuse_parser.add_argument("inputs", type=Path, nargs="+")
    fuse_parser.add_argument("--output", type=Path, default=RUNS_DIR / "fusion.json")
    fuse_parser.add_argument("--top-k", type=int, default=5)
    fuse_parser.add_argument("--rrf-k", type=int, default=60)

    eval_parser = subparsers.add_parser("evaluate", help="Compute retrieval metrics")
    eval_parser.add_argument("runs", type=Path, nargs="+")
    eval_parser.add_argument("--output", type=Path, default=REPORTS_DIR / "retrieval_metrics.json")
    eval_parser.add_argument("-k", type=int, default=5)

    notebook_parser = subparsers.add_parser(
        "export-notebook", help="Create a native .ipynb file from the # %% blocks"
    )
    notebook_parser.add_argument(
        "--output", type=Path, default=PROJECT_ROOT / "pixelrag_visual_experiment.ipynb"
    )
    return parser


def main() -> None:
    args = make_parser().parse_args()
    if args.command == "prepare":
        prepare(force=args.force)
    elif args.command == "build":
        build_index(
            args.device,
            args.model,
            args.backend,
            args.nlist,
            args.batch_size,
            args.max_pixels,
            args.hf_endpoint,
        )
    elif args.command == "search":
        search(args.api_url, args.top_k, args.output)
    elif args.command == "evidence":
        add_ocr_evidence(args.input, args.output, args.ocr_lang, args.max_lines, args.force_ocr)
    elif args.command == "fuse":
        fuse_runs(args.inputs, args.output, args.top_k, args.rrf_k)
    elif args.command == "evaluate":
        evaluate(args.runs, args.output, args.k)
    elif args.command == "export-notebook":
        export_notebook(args.output)


if __name__ == "__main__" and "ipykernel" not in sys.modules:
    main()
