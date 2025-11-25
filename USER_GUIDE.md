# RAG PDF Research Corpus System - User Guide

**Version:** 1.0  
**Date:** 2025-11-25  
**Status:** Complete (Phases 0-18)

---

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites and Setup](#prerequisites-and-setup)
3. [Configuration Guide](#configuration-guide)
4. [Step-by-Step Usage](#step-by-step-usage)
5. [RAG Query Interface](#rag-query-interface)
6. [Best Practices](#best-practices)
7. [Common Use Cases](#common-use-cases)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)
10. [Reference](#reference)

---

## Introduction

### What is the RAG PDF Research Corpus System?

The RAG PDF Research Corpus System is a comprehensive pipeline for processing, organizing, and querying academic PDF research papers. It uses:

- **LangGraph** for workflow orchestration
- **GPT-5/GPT-5-mini** for summarization, taxonomy generation, and classification
- **FAISS** for vector indexing and semantic search
- **3-tier hierarchical topic taxonomy** for organizing papers by research area

### Key Features

- **Automatic PDF processing**: Extract text, detect sections, create intelligent chunks
- **Metadata extraction**: Pull metadata from arXiv, CrossRef, and PDF properties
- **Intelligent summarization**: Generate comprehensive paper summaries using GPT-5
- **Hierarchical taxonomy**: Automatically build a 3-tier topic hierarchy
- **Paper classification**: Classify papers into the taxonomy with confidence scores
- **RAG queries**: Ask natural language questions and get cited answers
- **Cost tracking**: Monitor and control API costs with budget limits
- **Quality control**: Comprehensive validation and error handling

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Google Drive PDFs                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              PDF Parsing & Chunking                      │
│  (PyMuPDF, section detection, OCR fallback)              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         Metadata Extraction & Summarization              │
│    (arXiv API, CrossRef, GPT-5 summaries)                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          Embedding Generation & FAISS Index              │
│         (OpenAI embeddings, vector storage)              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            Topic Taxonomy Construction                   │
│   (Clustering, GPT-5 labeling, 3-tier hierarchy)         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Paper Classification & Export                  │
│  (Topic assignment, confidence scores, CSV/Parquet)      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 RAG Query Interface                      │
│        (Semantic search, answer generation)              │
└─────────────────────────────────────────────────────────┘
```

---

## Prerequisites and Setup

### System Requirements

- **Python**: 3.10 or higher
- **Environment**: Google Colab (recommended) or Jupyter Notebook
- **Memory**: At least 8GB RAM recommended for larger corpora
- **Storage**: Google Drive with sufficient space for PDFs and outputs

### Required Accounts and API Keys

1. **Google Account** - For Google Colab and Google Drive
2. **OpenAI API Key** - For GPT-5 and embeddings
   - Get your API key at: https://platform.openai.com/api-keys
   - Ensure you have sufficient credits for API calls

### Installing Dependencies

In Google Colab, run the following cell:

```python
# Install all required dependencies
!pip install -q openai>=1.3.0
!pip install -q langgraph>=0.0.30
!pip install -q langchain>=0.1.0
!pip install -q pymupdf>=1.23.0
!pip install -q faiss-cpu>=1.7.4
!pip install -q scikit-learn>=1.3.0
!pip install -q hdbscan>=0.8.33
!pip install -q pandas>=2.0.0
!pip install -q numpy>=1.24.0
!pip install -q tqdm>=4.65.0
!pip install -q matplotlib>=3.7.0
!pip install -q seaborn>=0.12.0
!pip install -q python-dateutil>=2.8.2
!pip install -q requests>=2.31.0
!pip install -q pydantic>=2.0.0

# Optional: For OCR support
!apt-get install -y tesseract-ocr
!pip install -q pytesseract>=0.3.10
!pip install -q Pillow>=10.0.0

print("✓ All dependencies installed!")
```

### Setting Up Your Environment

1. **Upload your PDFs to Google Drive**:
   - Create a folder in your Google Drive (e.g., "Research_PDFs")
   - Upload your academic PDF papers to this folder
   - Subfolders are supported for organization

2. **Set up your API key**:
   ```python
   import os
   from getpass import getpass
   
   # Securely input your API key
   os.environ["OPENAI_API_KEY"] = getpass("Enter your OpenAI API key: ")
   ```

3. **Mount Google Drive**:
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```

---

## Configuration Guide

### Basic Configuration

```python
from rag_models import RunConfig, create_default_config

# Create configuration with defaults
config = create_default_config(
    drive_folder_path="Research_PDFs",  # Your PDF folder in Google Drive
    max_papers_per_run=50,              # Process up to 50 papers
)

# Display configuration
print(config.display_config())
```

### Complete Configuration Options

```python
from rag_models import RunConfig

config = RunConfig(
    # ===== File Paths =====
    drive_folder_path="Research_PDFs",  # Folder in Google Drive (relative to 'My Drive')
    
    # ===== Processing Limits =====
    max_papers_per_run=100,      # Maximum papers to process (None = all)
    max_pages_per_paper=None,    # Maximum pages per paper (None = all)
    max_chunks_per_paper=100,    # Maximum chunks per paper
    
    # ===== Model Selection =====
    summary_model="gpt-5-mini",           # Model for summaries
    taxonomy_model="gpt-5-mini",          # Model for taxonomy generation
    classification_model="gpt-5-mini",    # Model for paper classification
    embedding_model="text-embedding-3-large",  # Model for embeddings
    
    # ===== Reasoning Effort (for thinking models) =====
    summary_reasoning_effort="medium",       # none, low, medium, high
    taxonomy_reasoning_effort="high",        # Higher for better taxonomy
    classification_reasoning_effort="medium",
    
    # ===== Clustering Settings =====
    cluster_tier1_target_k=8,   # Number of Tier 1 broad topics
    cluster_tier2_target_k=3,   # Tier 2 subtopics per Tier 1
    cluster_tier3_target_k=2,   # Tier 3 fine topics per Tier 2
    
    # ===== Feature Flags =====
    enable_ocr_fallback=False,       # Enable OCR for scanned PDFs
    enable_deep_analysis_pass=False, # Enable detailed analysis (Pass 2)
    taxonomy_approval_required=True, # Require manual taxonomy approval
    
    # ===== Token Limits (for cost control) =====
    max_tokens_per_summary=2000,
    max_tokens_per_classification=1000,
    
    # ===== Chunk Settings =====
    chunk_size_chars=1500,    # Target chunk size
    chunk_overlap_chars=200,  # Overlap between chunks
    
    # ===== Budget Controls =====
    max_cost_per_run=10.0,         # Maximum cost in USD (None = unlimited)
    cost_warning_threshold=0.8,    # Warn at 80% of budget
    enable_cost_tracking=True,     # Track API costs
    enable_result_caching=True,    # Cache results to avoid duplicates
    batch_api_calls=True,          # Use batch API for 50% discount
)
```

### Configuration Presets

**For Small Corpora (<50 papers):**
```python
config = create_default_config(
    drive_folder_path="PDFs",
    max_papers_per_run=50,
    summary_model="gpt-5-mini",
    max_cost_per_run=5.0,
)
```

**For Large Corpora (100+ papers):**
```python
config = create_default_config(
    drive_folder_path="Large_Corpus",
    max_papers_per_run=200,
    summary_model="gpt-5-mini",
    batch_api_calls=True,
    enable_result_caching=True,
    max_cost_per_run=25.0,
    chunk_size_chars=2000,  # Larger chunks for efficiency
)
```

**For High-Quality Analysis:**
```python
config = create_default_config(
    drive_folder_path="PDFs",
    summary_model="gpt-5",  # Full GPT-5 for best quality
    taxonomy_model="gpt-5",
    summary_reasoning_effort="high",
    taxonomy_reasoning_effort="high",
    enable_deep_analysis_pass=True,
    embedding_model="text-embedding-3-large",
)
```

---

## Step-by-Step Usage

### Quick Start (Full Pipeline)

```python
# 1. Import modules
from rag_models import create_default_config, StateManager
from workflow_orchestrator import run_full_pipeline

# 2. Create configuration
config = create_default_config(
    drive_folder_path="Research_PDFs",
    max_papers_per_run=20,
    max_cost_per_run=5.0,
)

# 3. Run the complete pipeline
final_state = run_full_pipeline(config)

# 4. Check results
print(f"Processed {len(final_state['papers'])} papers")
print(f"Created {len(final_state['chunks'])} chunks")
print(f"Total cost: ${final_state.get('total_cost', 0):.2f}")
```

### Step-by-Step Execution

For more control, run each phase separately:

#### Phase 1: Discovery and Parsing

```python
from drive_utils import mount_google_drive, discover_pdfs
from pdf_parser import parse_and_chunk_worker
from rag_models import StateManager, create_default_config

# Mount Google Drive
mount_google_drive()

# Create config and initial state
config = create_default_config(drive_folder_path="PDFs")
state = StateManager.create_initial_state(config)

# Discover PDFs
papers = discover_pdfs(config.drive_folder_path, config, show_progress=True)
for paper_id, paper in papers.items():
    state = StateManager.add_paper(state, paper)

print(f"Found {len(papers)} PDFs")

# Parse each paper
for paper_id in state['papers_pending']:
    state = parse_and_chunk_worker(paper_id, state)
    print(f"Parsed: {state['papers'][paper_id].filename}")
```

#### Phase 2: Metadata Extraction

```python
from metadata_extractor import metadata_extraction_worker

# Extract metadata for all parsed papers
for paper_id, paper in state['papers'].items():
    if paper.processing_status == 'parsed':
        state = metadata_extraction_worker(paper_id, state)
        print(f"Metadata: {paper.title or paper.filename}")
```

#### Phase 3: Embedding Generation

```python
from embedding_generator import embedding_generation_worker
import os

api_key = os.getenv("OPENAI_API_KEY")
state = embedding_generation_worker(state, api_key)

print(f"Generated embeddings for {sum(len(c) for c in state['chunks'].values())} chunks")
```

#### Phase 4: Summarization

```python
from summarization_pass1 import summarize_papers_worker

state = summarize_papers_worker(state, api_key)

# View a summary
for paper in list(state['papers'].values())[:3]:
    print(f"\n{paper.title}:")
    print(f"{paper.full_summary[:300]}...")
```

#### Phase 5: Taxonomy Building

```python
from topic_taxonomy import build_complete_taxonomy
from embedding_generator import load_faiss_index, load_metadata_mapping

# Load embeddings
index = load_faiss_index(state['faiss_index_path'])
metadata = load_metadata_mapping(state['faiss_meta_path'])
embeddings = index.index.reconstruct_n(0, index.index.ntotal)

# Build taxonomy
hierarchy = build_complete_taxonomy(state, embeddings, {}, config, api_key)
state['topic_hierarchy'] = hierarchy

# Display taxonomy
for t1 in hierarchy.tier1:
    print(f"\n{t1.label} ({t1.paper_count} papers)")
    for t2 in hierarchy.get_tier2_topics(t1.id):
        print(f"  └─ {t2.label} ({t2.paper_count} papers)")
```

#### Phase 6: Classification

```python
from paper_classification import classification_worker

# Approve taxonomy first
state['taxonomy_approved'] = True

# Classify papers
state = classification_worker(state, api_key)

# View classifications
for paper in list(state['papers'].values())[:5]:
    print(f"{paper.title[:50]}... → {paper.tier1_topic_name}")
```

#### Phase 7: Export Results

```python
from export_manager import export_final_data

# Export all data
export_paths = export_final_data(state, "./exports")

print("Exported files:")
for key, path in export_paths.items():
    print(f"  {key}: {path}")
```

---

## RAG Query Interface

### Basic Queries

```python
from rag_query_interface import RAGQueryEngine, interactive_query

# Initialize query engine
engine = RAGQueryEngine(state)

# Simple query
result = engine.query(
    "What are the main approaches to transformer efficiency?",
    top_k=5
)

# Display answer
print(result['answer'])
print("\nSources:")
for source in result['sources']:
    print(f"  - {source['title']}")
```

### Interactive Queries

```python
# Interactive query with detailed output
result = interactive_query(
    state,
    query="How do large language models handle long context?",
    top_k=5,
    rerank=True,
    boost_sections=['abstract', 'conclusion']
)
```

### Query History

```python
from rag_query_interface import QueryHistory

# Track queries
history = QueryHistory()

# Execute and track queries
queries = [
    "What is attention mechanism?",
    "How to improve model efficiency?",
    "What are recent advances in NLP?"
]

for q in queries:
    result = engine.query(q)
    history.add_query(q, result)

# Export history
history.export_to_json("query_history.json")
```

### Search Functions

```python
from corpus_utilities import (
    search_by_title,
    search_by_author,
    search_by_topic,
    search_by_date_range
)

# Search by title keyword
papers = search_by_title(state, "transformer")

# Search by author
papers = search_by_author(state, "Vaswani")

# Search by topic
papers = search_by_topic(state, "T1_LLMs")

# Search by date range
from datetime import date
papers = search_by_date_range(state, date(2023, 1, 1), date(2024, 1, 1))
```

---

## Best Practices

### 1. Start Small

- Begin with 10-20 papers to test your setup
- Verify results before processing larger corpora
- Use `max_papers_per_run` to limit initial runs

### 2. Use Budget Controls

```python
config = create_default_config(
    max_cost_per_run=5.0,        # Set a budget limit
    cost_warning_threshold=0.8,  # Warn at 80%
    enable_cost_tracking=True,   # Track all costs
    batch_api_calls=True,        # 50% discount
)
```

### 3. Save Checkpoints

```python
from workflow_orchestrator import save_checkpoint

# Save state periodically
checkpoint_path = save_checkpoint(state)
print(f"Saved to: {checkpoint_path}")

# Resume from checkpoint
from workflow_orchestrator import load_checkpoint
state = load_checkpoint("checkpoint_20231201_143000")
```

### 4. Handle Errors Gracefully

```python
from workflow_orchestrator import retry_failed_papers, list_failed_papers

# Check for failed papers
failed = list_failed_papers(state)
print(f"Failed papers: {len(failed)}")

# Retry failures
state = retry_failed_papers(state)
```

### 5. Monitor Quality

```python
from quality_control import create_qc_dashboard, generate_qc_report

# Create QC dashboard
dashboard = create_qc_dashboard(state)
print(dashboard.get_summary())

# Generate detailed report
report = generate_qc_report(state, "./qc_report.md")
```

### 6. Organize Your PDFs

- Use descriptive filenames (arXiv IDs work well)
- Organize by topic or year in subfolders
- Remove duplicate or corrupted files before processing

---

## Common Use Cases

### Use Case 1: Literature Review

Process papers for a literature review on a specific topic:

```python
# 1. Configure for high-quality summaries
config = create_default_config(
    drive_folder_path="LitReview_Papers",
    summary_model="gpt-5-mini",
    summary_reasoning_effort="high",
    enable_deep_analysis_pass=True,  # Get detailed analysis
)

# 2. Run pipeline
state = run_full_pipeline(config)

# 3. Export summaries for review
from corpus_utilities import create_reading_list
reading_list = create_reading_list(
    state,
    sort_by="relevance",
    include_summaries=True,
    output_path="literature_review.md"
)
```

### Use Case 2: Research Exploration

Explore a large corpus to find relevant papers:

```python
# 1. Process corpus
config = create_default_config(
    drive_folder_path="Large_Corpus",
    max_papers_per_run=500,
)
state = run_full_pipeline(config)

# 2. Use RAG to explore
engine = RAGQueryEngine(state)

questions = [
    "What methods exist for efficient transformers?",
    "How do papers address model compression?",
    "What are common evaluation benchmarks?"
]

for q in questions:
    result = engine.query(q, top_k=3)
    print(f"\nQ: {q}")
    print(f"A: {result['answer'][:200]}...")
```

### Use Case 3: Paper Organization

Organize papers by topic automatically:

```python
# 1. Run pipeline with taxonomy
config = create_default_config(
    drive_folder_path="Unorganized_Papers",
    cluster_tier1_target_k=10,  # More broad topics
    cluster_tier2_target_k=4,   # More subtopics
)
state = run_full_pipeline(config)

# 2. Export by topic
from corpus_utilities import export_by_topic
for topic in state['topic_hierarchy'].tier1:
    export_by_topic(
        state,
        topic_id=topic.id,
        output_path=f"./organized/{topic.label}/"
    )
```

### Use Case 4: BibTeX Generation

Generate bibliography entries:

```python
from corpus_utilities import generate_bibtex_entries

# Generate BibTeX for all papers
bibtex = generate_bibtex_entries(state)
with open("bibliography.bib", "w") as f:
    f.write(bibtex)

# Generate for specific topic
bibtex = generate_bibtex_entries(
    state,
    filter_topic="T1_LLMs"
)
```

---

## Troubleshooting

### Common Issues

#### "OPENAI_API_KEY not set"

```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key-here"
# Or use getpass for security:
from getpass import getpass
os.environ["OPENAI_API_KEY"] = getpass("Enter API key: ")
```

#### "PyMuPDF (fitz) is not installed"

```python
!pip install pymupdf
```

#### "Rate limit exceeded" / Error 429

```python
# The system has built-in retry logic, but you can also:
# 1. Reduce batch sizes
config = create_default_config(
    max_papers_per_run=20,  # Process fewer papers
)

# 2. Enable longer delays
from rag_models import RetryHandler
handler = RetryHandler(
    max_retries=5,
    initial_delay=2.0,  # Start with 2 second delay
    max_delay=60.0,     # Cap at 60 seconds
)
```

#### "Budget exceeded"

```python
# 1. Increase budget
config = create_default_config(
    max_cost_per_run=20.0,  # Higher budget
)

# 2. Use cheaper models
config = create_default_config(
    summary_model="gpt-5-mini",       # Use mini model
    embedding_model="text-embedding-3-small",  # Smaller embeddings
)
```

#### "PDF parsing failed"

```python
# Enable OCR for scanned PDFs
config = create_default_config(
    enable_ocr_fallback=True,
)

# Check specific failures
from workflow_orchestrator import list_failed_papers
failed = list_failed_papers(state)
for f in failed:
    print(f"Failed: {f['filename']} - {f['error_reason']}")
```

#### Import Errors in Colab

```python
# Ensure modules are in the path
import sys
sys.path.append('/content/drive/MyDrive/path/to/repository')

# Or upload the .py files to the session
```

### Getting Help

1. **Check the logs**: Most functions use Python logging
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   ```

2. **View error details**:
   ```python
   for error in state.get('errors', []):
       print(f"Stage: {error['stage']}")
       print(f"Error: {error['error']}")
   ```

3. **Generate QC report**:
   ```python
   from quality_control import generate_qc_report
   report = generate_qc_report(state, "debug_report.md")
   ```

---

## FAQ

### Q: How much does it cost to process papers?

Approximate costs (using gpt-5-mini with batch API):
- **Embedding**: ~$0.0001 per chunk
- **Summarization**: ~$0.005 per paper
- **Classification**: ~$0.002 per paper

For 100 papers with ~50 chunks each:
- Embeddings: ~$0.50
- Summaries: ~$0.50
- Classification: ~$0.20
- **Total: ~$1.20**

Use `print_cost_summary(state)` to see actual costs.

### Q: How long does processing take?

Depends on corpus size and API speed:
- 10 papers: ~5-10 minutes
- 100 papers: ~30-60 minutes
- 500 papers: ~2-4 hours

Enable checkpointing for long runs.

### Q: Can I process non-English papers?

The system primarily supports English. Non-English papers may:
- Parse correctly
- Have reduced metadata extraction quality
- Generate summaries/classifications in the paper's language

### Q: How do I update an existing corpus?

```python
from corpus_utilities import add_new_papers

# Load existing state
state = load_checkpoint("previous_run")

# Add new papers
new_papers = discover_pdfs("New_Papers", config)
state = add_new_papers(state, new_papers)

# Process only new papers
# (existing papers won't be reprocessed)
```

### Q: Can I customize the taxonomy?

Yes! After taxonomy generation:
```python
# Review and modify
state['taxonomy_approved'] = False  # Require re-review

# Manually edit topics
from taxonomy_review import modify_topic_label
state = modify_topic_label(state, "T1_001", "New Label")

# Approve when satisfied
state['taxonomy_approved'] = True
```

---

## Reference

### Module Reference

| Module | Description |
|--------|-------------|
| `rag_models.py` | Core data models (PaperRecord, RunConfig, GraphState, etc.) |
| `drive_utils.py` | Google Drive integration and PDF discovery |
| `pdf_parser.py` | PDF parsing, section detection, chunking |
| `metadata_extractor.py` | Metadata extraction from arXiv, CrossRef |
| `embedding_generator.py` | Embedding generation and FAISS indexing |
| `summarization_pass1.py` | Paper summarization with GPT-5 |
| `topic_taxonomy.py` | Taxonomy construction and topic labeling |
| `paper_classification.py` | Paper classification into taxonomy |
| `export_manager.py` | Data export (CSV, Parquet, JSON) |
| `workflow_orchestrator.py` | LangGraph workflow and execution |
| `quality_control.py` | QC dashboard and validation |
| `rag_query_interface.py` | RAG query engine and search |
| `corpus_utilities.py` | Utility functions for corpus management |

### Key Classes

```python
# Configuration
from rag_models import RunConfig, create_default_config

# Paper data
from rag_models import PaperRecord, PaperChunk

# Taxonomy
from rag_models import TopicHierarchy, TopicNode

# State management
from rag_models import GraphState, StateManager

# Cost tracking
from rag_models import CostTracker, BudgetExceededError

# Error handling
from rag_models import RetryHandler, ErrorHandler
```

### Quick Reference Commands

```python
# Run full pipeline
from workflow_orchestrator import run_full_pipeline
state = run_full_pipeline(config)

# Check progress
from workflow_orchestrator import display_workflow_state
print(display_workflow_state(state))

# Save checkpoint
from workflow_orchestrator import save_checkpoint
save_checkpoint(state)

# Print cost summary
from workflow_orchestrator import print_cost_summary
print_cost_summary(state)

# Generate QC report
from quality_control import generate_qc_report
generate_qc_report(state, "report.md")

# Export data
from export_manager import export_final_data
export_final_data(state, "./exports")
```

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-25 | Initial comprehensive user guide |

---

**End of User Guide**

For technical specifications, see `rag_pdf_system_spec_v_2.md`.  
For implementation details, see `FINAL_NOTEBOOK_ACTION_PLAN.md`.
