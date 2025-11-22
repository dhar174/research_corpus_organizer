# RAG PDF Research Corpus Organizer

A comprehensive system for processing and organizing academic PDF research papers using LangGraph workflows, GPT-5.1 Thinking, and RAG (Retrieval-Augmented Generation).

## Overview

This project implements an intelligent pipeline for:
- **Ingesting** PDFs from Google Drive
- **Parsing and chunking** documents with section awareness
- **Extracting metadata** from arXiv, CrossRef, and PDF sources
- **Generating summaries** using advanced LLMs
- **Building hierarchical topic taxonomies** through clustering
- **Classifying papers** into 3-tier topic hierarchies
- **Enabling RAG queries** for corpus exploration

## Project Status

**Current Phase:** Phase 0 and Phase 1 Complete ✓

- ✅ Phase 0: Environment setup and configuration
- ✅ Phase 1: Data models and schema definitions
- 🔄 Phases 2-22: PDF processing, embeddings, taxonomy, RAG interface (planned)

## Quick Start

### For Users

1. **Open the notebook:**
   - Upload `rag_pdf_system.ipynb` to Google Colab
   - Or open from GitHub

2. **Follow the setup guide:**
   - See [README_SETUP.md](README_SETUP.md) for detailed instructions
   - Run Phase 0 cells to install dependencies
   - Import data models from `rag_models.py`

3. **Configure your pipeline:**
   ```python
   from rag_models import RunConfig
   
   config = RunConfig(
       drive_folder_path="PDFs",
       max_papers_per_run=10,
       summary_model="gpt-4-turbo-preview",
       embedding_model="text-embedding-3-large"
   )
   ```

### For Developers

See [FINAL_NOTEBOOK_ACTION_PLAN.md](FINAL_NOTEBOOK_ACTION_PLAN.md) for the complete implementation roadmap.

## Documentation

- **[README_SETUP.md](README_SETUP.md)** - Setup guide and usage instructions
- **[FINAL_NOTEBOOK_ACTION_PLAN.md](FINAL_NOTEBOOK_ACTION_PLAN.md)** - Complete implementation plan (Phases 0-22)
- **[rag_pdf_system_spec_v_2.md](rag_pdf_system_spec_v_2.md)** - Technical specification v2.1

## Key Components

### Notebooks
- `rag_pdf_system.ipynb` - Main Google Colab notebook with Phase 0 implementation

### Python Modules
- `rag_models.py` - Core data models and schemas (Phase 1)
  - RunConfig: System configuration
  - PaperRecord: Paper metadata and processing state
  - PaperChunk: Text chunks for RAG
  - TopicHierarchy: 3-tier taxonomy
  - GraphState: LangGraph workflow state
  - Helper classes: MetadataExtractor, StatisticsTracker, ErrorHandler, IDGenerator

### Utilities
- `notebook_builder.py` - Generate complete standalone notebooks

## Features

### Implemented (Phase 0 & 1)
- ✅ Environment inspection (Python version, GPU/CPU, system resources)
- ✅ Dependency installation (18 packages with version pinning)
- ✅ Import management with error handling
- ✅ Comprehensive data models with Pydantic validation
- ✅ Configuration schema with sensible defaults
- ✅ Helper utilities for metadata extraction and statistics

### Planned (Phases 2-22)
- 📋 Google Drive integration and PDF discovery
- 📋 PDF parsing with PyMuPDF and OCR fallback
- 📋 Section-aware text chunking
- 📋 Metadata extraction (arXiv, DOI, CrossRef)
- 📋 OpenAI embedding generation
- 📋 FAISS vector indexing
- 📋 GPT-5.1 summarization (multiple passes)
- 📋 3-tier taxonomy generation via clustering
- 📋 Topic classification with reasoning
- 📋 RAG query interface
- 📋 Quality control and validation
- 📋 Cost tracking and optimization
- 📋 Comprehensive error handling
- 📋 Export to CSV/Parquet

## System Architecture

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
│    (arXiv API, CrossRef, GPT-5.1 summaries)              │
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
│   (Clustering, GPT-5.1 labeling, 3-tier hierarchy)       │
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

## Data Models

### PaperRecord
Comprehensive metadata for each paper including:
- Identifiers (ID, file path, arXiv ID, DOI)
- Metadata (title, authors, venue, dates)
- Text statistics and quality scores
- Summaries (full, deep, initial notes)
- Topic classifications (3 tiers with confidence scores)
- Processing status and error tracking

### TopicHierarchy
3-tier taxonomy structure:
- **Tier 1:** Broad research areas (e.g., "Large Language Models")
- **Tier 2:** Mid-level topics (e.g., "Transformer Architectures")
- **Tier 3:** Fine-grained topics (e.g., "Efficient Attention Mechanisms")

### GraphState
LangGraph workflow state tracking:
- Configuration
- Papers and chunks
- Taxonomy
- File paths
- Processing status
- Error logs

## Requirements

- Python 3.10+
- Google Colab (recommended) or Jupyter
- OpenAI API key (for GPT-5.1 and embeddings)
- Google Drive (for PDF storage)

### Dependencies
See `rag_pdf_system.ipynb` for complete list, including:
- openai>=1.3.0
- langgraph>=0.0.30
- pymupdf>=1.23.0
- faiss-cpu>=1.7.4
- scikit-learn>=1.3.0
- pydantic>=2.0.0
- pandas, numpy, tqdm, matplotlib, seaborn

## License

See repository license.

## Contributing

This project follows a phased implementation approach. See FINAL_NOTEBOOK_ACTION_PLAN.md for details on each phase.

---

**Version:** 1.0  
**Last Updated:** 2025-11-21  
**Status:** Phase 0 & 1 Complete - Ready for Phase 2 Development
