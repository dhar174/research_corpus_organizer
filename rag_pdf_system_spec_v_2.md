# RAG PDF Research Corpus System – LangGraph + GPT‑5.1 Thinking

**Version:** 2.1\
**Target environment:** Google Colab (ipynb), Google Drive, OpenAI API, LangGraph 1.x

---

## 0. Purpose & Scope

Build a **Google Colab–based notebook** that orchestrates a LangGraph workflow using **GPT‑5.1 Thinking** and advanced RAG techniques to:

1. **Ingest PDFs** from a user-specified **Google Drive folder**.
2. **Parse and chunk** each PDF into meaningful text segments.
3. **Extract metadata** (title, authors, publish date, venue, IDs) per paper.
4. **Generate high-quality summaries** and agent notes for each paper.
5. **Embed and index** all chunks in a FAISS vector store for RAG.
6. **Derive a three-tier topic taxonomy** (broad → mid → fine) from the corpus using clustering + GPT‑5.1.
7. **Classify each paper** into one topic at each tier, with confidence scores and reasoning notes.
8. **Persist results** into:
   - A **master CSV** (and/or Parquet) "database" of all papers.
   - A **FAISS index** and metadata mapping.
   - A **taxonomy JSON** with versioning.
9. Provide **basic QC and RAG query tools** for exploration.

The system is designed for **AI/ML/LLM research PDFs** (often from arXiv), but should be robust to other technical papers.

Non-goals (for now):

- Building a full web UI (Gradio/Streamlit) – this is Colab-focused.
- Fine-tuning models or running fully local LLMs in this notebook.

---

## 1. Environment, Dependencies, and Runtime Assumptions

### 1.1 Runtime

- **Google Colab** notebook (`.ipynb`).
- User has:
  - OpenAI API key.
  - A Google Drive folder with PDFs.

### 1.2 Core Libraries

Install (via `pip`) at top of notebook:

- **OpenAI Python SDK** (latest – supports GPT‑5.1 and embeddings).
- **LangGraph** (Python; workflows + durable checkpoints).
- **PyMuPDF (**``**)** for PDF parsing.
- **FAISS** (CPU) for vector indexing.
- **scikit-learn** for clustering (e.g., Agglomerative / KMeans).
- **hdbscan** (optional) for density-based clustering.
- **pandas**, **numpy**, **tqdm**, **matplotlib** for data & visualization.
- **python-dateutil** for date parsing.
- **requests** for arXiv / CrossRef API access.
- **pytesseract** and **Pillow** (optional) for OCR fallback.

---

## 2. High-Level Architecture

### 2.1 Architectural Style

- Orchestrated via **LangGraph** in a **supervisor–worker pattern**:
  - **Supervisor** state tracks global config, list of papers, taxonomy, progress.
  - **Workers** operate on a single `paper_id` at a time (parse, embed, summarize, classify).
- Multi-stage pipeline:
  1. **Ingestion Workflow** – parse, chunk, embed, metadata, initial summary, initial CSV.
  2. **Taxonomy Workflow** – cluster paper embeddings, build 3-tier taxonomy.
  3. **Classification Workflow** – assign final topics per tier with GPT‑5.1.

### 2.2 Main Stages

1. Setup, config & API keys.
2. Mount Google Drive & discover PDFs.
3. PDF parsing, section-aware chunking & OCR fallback.
4. Embedding and FAISS index creation.
5. Pass 1 – metadata + summary + initial notes.
6. Initial master CSV export (with status tracking).
7. Topic modeling & taxonomy construction (Tier1/2/3).
8. Taxonomy review & approval (human-in-the-loop step).
9. Pass 3 – final topic classification & classification notes.
10. Final CSV export (with taxonomy version) + QC & RAG query utilities.

---

## 3. Data Model & State Schemas

### 3.1 `RunConfig`

Pydantic model or TypedDict initialized by user in a config cell:

- `drive_folder_path: str` – Google Drive path to folder with PDFs.

- `max_papers_per_run: int | None` – cap to limit cost in a run.

- `max_pages_per_paper: int | None` – optional page cap.

- `max_chunks_per_paper: int` – upper bound on chunks per paper.

- `enable_ocr_fallback: bool` – whether to try OCR on low-text PDFs.

- `summary_model: str` – e.g., `"gpt-5.1-thinking"`.

- `taxonomy_model: str` – typically same as summary model.

- `classification_model: str` – typically same as summary model.

- `use_tiered_models: bool` – if `True`, allow cheaper models for bulk tasks later.

- `summary_reasoning_effort: Literal["none","low","medium","high"]`.

- `taxonomy_reasoning_effort: Literal[...]`.

- `classification_reasoning_effort: Literal[...]`.

- `embedding_model: str` – e.g., `"text-embedding-3-large"`.

- `cluster_tier1_target_k: int | None` – optional target cluster count.

- `cluster_tier2_target_k: int | None`.

- `cluster_tier3_target_k: int | None`.

- `enable_deep_analysis_pass: bool` – optional Pass 2 (deep methods/results summaries).

- `taxonomy_approval_required: bool` – if `True`, classification waits for user approval.

- Cost safety toggles:

  - `max_tokens_per_summary: int`.
  - `max_tokens_per_classification: int`.

### 3.2 `PaperRecord`

Represent each paper as a Pydantic model / TypedDict:

- `id: str` – internal ID (e.g., hash of `file_path`).

- `file_path: str` – absolute path in Colab.

- `filename: str`.

- `source: Literal["arxiv","doi","other"] | None`.

- `arxiv_id: str | None`.

- `doi: str | None`.

- `title: str | None`.

- `authors: list[str] | None`.

- `venue: str | None`.

- `publish_date: date | None`.

- `publish_date_source: Literal["arxiv","crossref","pdf","manual","unknown"]`.

- `is_preprint: bool | None`.

- `arxiv_version: str | None`.

- `raw_text_stats: dict` – e.g.:

  - `pages: int`.
  - `chars_total: int`.
  - `chars_per_page: float`.
  - `alnum_ratio: float`.
  - `parse_quality_score: float` (0–1).

- `abstract_text: str | None` – cleaned/normalized abstract.

- `full_summary: str | None` – high-level summary.

- `deep_summary: str | None` – optional deeper pass summary.

- `initial_notes: str | None` – notes from Pass 1 agent.

- `classification_notes: str | None` – reasoning behind topic assignment.

- `tier1_topic: str | None`.

- `tier2_topic: str | None`.

- `tier3_topic: str | None`.

- `tier1_confidence: float | None`.

- `tier2_confidence: float | None`.

- `tier3_confidence: float | None`.

- `taxonomy_version: str | None`.

- `processing_status: Literal[   "pending",   "parsed",   "summarized",   "embedded",   "deep_analyzed",   "classified",   "failed" ]`.

- `error_reason: str | None` – error message or notes if `failed`.

- `last_updated: datetime | None` – timestamp of last update.

### 3.3 `PaperChunk`

Chunk-level representation (for RAG & analysis):

- `paper_id: str`.
- `chunk_id: str`.
- `section_label: str` – e.g., `"abstract"`, `"introduction"`, `"methods"`, `"results"`, `"conclusion"`, `"other"`.
- `page_start: int`.
- `page_end: int`.
- `text: str`.
- `embedding_id: int | None` – index into FAISS index.

Vector values themselves are not stored here; they live in FAISS.

### 3.4 `TopicHierarchy`

JSON-serializable structure representing the 3-tier taxonomy:

```json
{
  "taxonomy_version": "v1.0",
  "created_at_iso": "2025-11-18T12:00:00Z",
  "notes": "Initial taxonomy for corpus of N papers",
  "tiers": {
    "tier1": [
      {
        "id": "T1_LLMs",
        "label": "LLMs",
        "description": "Large Language Models, architectures, and training.",
        "paper_ids": ["p1", "p5", "p9"],
        "embedding": [/* centroid vector or omitted */]
      }
    ],
    "tier2": [
      {
        "id": "T2_LLMs_Attention",
        "parent_tier1_id": "T1_LLMs",
        "label": "Transformer Attention",
        "description": "Attention mechanisms, efficient attention, and variants.",
        "paper_ids": ["p1", "p2"]
      }
    ],
    "tier3": [
      {
        "id": "T3_Attn_Efficient",
        "parent_tier2_id": "T2_LLMs_Attention",
        "label": "Efficient Attention Methods",
        "description": "Sparse, low-rank, kernelized, and approximate attention methods.",
        "paper_ids": ["p1"]
      }
    ]
  }
}
```

### 3.5 Supervisor State (`GraphState`)

LangGraph global state object:

- `config: RunConfig`.
- `papers: dict[str, PaperRecord]` – keyed by `paper_id`.
- `chunks: dict[str, list[PaperChunk]]` – per paper.
- `topic_hierarchy: TopicHierarchy | None`.
- `taxonomy_approved: bool` – set via notebook flag or user action.
- `faiss_index_path: str | None`.
- `faiss_meta_path: str | None`.
- `master_csv_path: str | None`.
- `errors_log_path: str | None`.

---

## 4. Google Drive Integration

### 4.1 Drive Mount Method

- Use Colab’s built-in mount:

```python
from google.colab import drive
drive.mount('/content/drive')
```

- The user supplies `drive_folder_path` relative to `"/content/drive/My Drive"`.

### 4.2 PDF Discovery

Notebook helper (not necessarily a node) to:

1. Resolve absolute folder path.
2. Recursively find all `*.pdf` files.
3. For each PDF path:
   - Compute `paper_id = hash(file_path)`.
   - Create `PaperRecord` if it does not already exist in `state.papers`.
   - Initialize `processing_status = "pending"`.

LangGraph node `list_pdfs` can be used to update state and handle re-runs.

---

## 5. PDF Parsing, Section-Aware Chunking & OCR Fallback

### 5.1 Node: `parse_and_chunk_worker`

**Type:** Worker node (per-paper) under supervisor control.

Input:

- `paper_id`.
- Global `state` with `config` and `papers`.

Steps:

1. **Status update**: set `processing_status = "parsed"` once successful, or `"failed"` with `error_reason` on error.

2. **Load PDF**:

   - Use PyMuPDF (`fitz.open(file_path)`).
   - Count pages.

3. **Extract page texts & stats**:

   - For each page:
     - Extract text using `page.get_text("text")`.
     - Compute `chars`, `alnum_ratio` (alpha-numeric / total characters).
   - Aggregate across pages to fill `raw_text_stats`.

4. **Detect low-quality / scanned PDF**:

   - If `chars_total < MIN_CHARS_THRESHOLD` or `alnum_ratio` very low:
     - Set `parse_quality_score` low.
     - If `config.enable_ocr_fallback`:
       - Use `pytesseract` on page images to extract extra text.
   - Else set `parse_quality_score` appropriately.

5. **Section detection** (heuristic):

   - Concatenate text with page markers.
   - Use regex / simple heuristics to find section headings:
     - Common headings: `"Abstract"`, `"1 Introduction"`, `"Conclusion"`, etc.
   - Tag portions of text with `section_label` based on headings and page positions.

6. **Chunking**:

   - For each section’s text:
     - Split into chunks of \~N tokens equivalent (e.g., \~1000–2000 characters), respecting sentence boundaries if possible.
     - Enforce `config.max_chunks_per_paper` cap.
   - For pages with no clear section, treat them as `"other"` and chunk by size.

7. **Create **``**s**:

   - For each chunk:
     - Assign `chunk_id`, `section_label`, `page_start`, `page_end`, `text`.
   - Save in `state.chunks[paper_id]`.

8. **Update **``:

   - `raw_text_stats` fields.
   - \`last\_u
