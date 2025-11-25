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

**Current Phase:** Phase 19 Complete ✓

- ✅ Phase 0: Environment setup and configuration
- ✅ Phase 1: Data models and schema definitions (COMPLETE - see PHASE1_COMPLETION.md)
- ✅ Phase 2: Google Drive integration and PDF discovery (COMPLETE - see PHASE2_COMPLETION.md)
- ✅ Phase 3: PDF parsing and chunking (COMPLETE - see PHASE3_COMPLETION.md)
- ✅ Phase 4: Metadata extraction (COMPLETE - see PHASE4_COMPLETION.md)
- ✅ Phase 5: Embedding generation and FAISS index (COMPLETE - see PHASE5_COMPLETION.md)
- ✅ Phase 6: Summarization (Pass 1) (COMPLETE - see PHASE6_COMPLETION.md)
- ✅ Phase 7: Initial CSV export (COMPLETE - see PHASE7_COMPLETION.md)
- ✅ Phase 8: Topic modeling and taxonomy (COMPLETE - see PHASE8_COMPLETION.md)
- ✅ Phase 9: Taxonomy review and approval (COMPLETE - see PHASE9_COMPLETION.md)
- ✅ Phase 10: Final topic classification (COMPLETE - see PHASE10_COMPLETION.md)
- ✅ Phase 11: Deep analysis pass (optional) (COMPLETE - see PHASE11_COMPLETION.md)
- ✅ Phase 12: Final CSV/Parquet export (COMPLETE - see PHASE12_COMPLETION.md)
- ✅ Phase 13: LangGraph workflow integration (COMPLETE - see PHASE13_COMPLETION.md)
- ✅ Phase 14: Quality control and validation (COMPLETE - see PHASE14_COMPLETION.md)
- ✅ Phase 15: RAG query interface (COMPLETE - see PHASE15_COMPLETION.md)
- ✅ Phase 16: Utility functions and tools (COMPLETE - see PHASE16_COMPLETION.md)
- ✅ Phase 17: Cost tracking and optimization (COMPLETE - see PHASE17_COMPLETION.md)
- ✅ Phase 18: Error handling and resilience (COMPLETE - see PHASE18_COMPLETION.md)
- ✅ Phase 19: Documentation and user guide (COMPLETE)
- ✅ Phase 20: Testing and validation (COMPLETE - see PHASE20_COMPLETION.md)
- 🔄 Phase 21: Deployment (planned)
- ✅ Phase 22b: Advanced visualizations (COMPLETE - see PHASE22B_COMPLETION.md)

## Cost Tracking and Budget Controls (Phase 17)

The system now includes comprehensive cost tracking for OpenAI API calls:

```python
from rag_models import RunConfig, CostTracker

config = RunConfig(
    # Enable cost tracking with budget limit
    enable_cost_tracking=True,
    max_cost_per_run=10.0,           # $10 budget
    cost_warning_threshold=0.8,      # Warn at 80%
    
    # Cost optimization
    batch_api_calls=True,            # 50% discount
    enable_result_caching=True,      # Avoid duplicate calls
)

# Automatic cost monitoring during pipeline execution
# View detailed cost report at any time
from workflow_orchestrator import print_cost_summary
print_cost_summary(state)
```

**Features:**
- ✅ Real-time cost tracking with token-level precision
- ✅ Budget enforcement with configurable limits
- ✅ 50% batch API discount calculation
- ✅ Result caching to avoid duplicate calls
- ✅ Automated cost-saving recommendations
- ✅ Comprehensive cost reports (JSON + formatted output)

**See [README_PHASE17.md](README_PHASE17.md) for complete cost tracking documentation.**

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

- **[USER_GUIDE.md](USER_GUIDE.md)** - Comprehensive user guide with step-by-step instructions
- **[EXAMPLES.md](EXAMPLES.md)** - Configuration examples, query examples, and use cases
- **[README_SETUP.md](README_SETUP.md)** - Setup guide and installation instructions
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
  - **CostTracker: API cost tracking and budget controls (Phase 17)**
  - **APICallRecord, CostReport: Cost tracking models (Phase 17)**
  - **BudgetExceededError: Budget limit exception (Phase 17)**
- `drive_utils.py` - Google Drive integration and PDF discovery (Phase 2)
  - mount_google_drive: Mount Google Drive in Colab
  - discover_pdfs: Recursively find and catalog PDFs
  - validate_file_access: File validation utilities
  - check_disk_space: Disk space monitoring
  - Helper functions for file management
- `pdf_parser.py` - PDF parsing and intelligent chunking (Phase 3)
  - parse_pdf: Extract text from PDFs using PyMuPDF
  - apply_ocr: OCR fallback for scanned PDFs
  - detect_sections: Heuristic section detection for academic papers
  - chunk_text: Sentence-aware text chunking
  - create_chunks_from_pages: Section-aware chunk creation
  - parse_and_chunk_worker: LangGraph worker node
  - Validation functions for parsing and chunks
- `metadata_extractor.py` - Metadata extraction from multiple sources (Phase 4)
  - extract_arxiv_metadata: Query arXiv API for paper metadata
  - extract_doi_metadata: Query CrossRef API via DOI
  - extract_pdf_metadata: Extract PDF document properties
  - extract_abstract_from_text: Pattern-based abstract extraction
  - normalize_metadata: Normalize and validate metadata
  - metadata_extraction_worker: LangGraph worker node
  - API integration with rate limiting and retry logic
- `embedding_generator.py` - Embedding generation and FAISS indexing (Phase 5)
  - EmbeddingGenerator: OpenAI embeddings with batch processing and retry logic
  - embed_all_chunks: Generate embeddings for all chunks in state
  - FaissIndexBuilder: Build and manage FAISS vector index
  - build_faiss_index: Create searchable index with metadata mapping
  - save_faiss_index/load_faiss_index: Persist and reload index
  - embedding_generation_worker: LangGraph worker node
  - Cost estimation and tracking
- `summarization_pass1.py` - Paper summarization with GPT-5 (Phase 6)
  - SummaryGenerator: Generate comprehensive paper summaries
  - SummaryPromptFactory: Create structured prompts
  - batch_summarize_papers: Process papers in batches
  - summarize_papers_worker: LangGraph worker node
  - Summary validation and quality checks
- `topic_taxonomy.py` - Topic modeling and 3-tier taxonomy (Phase 8)
  - build_tier1_taxonomy: Broad topic clustering
  - build_tier2_taxonomy: Mid-level topic clustering
  - build_tier3_taxonomy: Fine-grained topic clustering
  - TopicLabelGenerator: Generate topic labels with GPT-5
  - build_complete_taxonomy: Create full 3-tier hierarchy
  - Clustering with KMeans/Agglomerative algorithms
- `paper_classification.py` - Paper classification into taxonomy (Phase 10)
  - PaperClassifier: Classify papers into topics
  - build_classification_prompt: Create classification prompts
  - batch_classify_papers: Process papers in batches
  - classification_worker: LangGraph worker node
  - Validation and consistency checks
- `export_manager.py` - Data export and artifact management (Phases 7, 12)
  - export_final_data: Export all data and artifacts
  - export_full_csv/export_summary_csv: CSV exports
  - export_to_json: JSON export
  - generate_statistics_report: Create statistics
  - save_all_artifacts: Persist all outputs
- `workflow_orchestrator.py` - LangGraph workflow integration (Phase 13)
  - WorkflowBuilder: Build complete StateGraph
  - SupervisorCoordinator: Coordinate workflow execution
  - CheckpointManager: Save/load state, resume capability
  - WorkflowExecutor: User-friendly execution controller
  - QualityController: Data quality checks
  - ErrorRecoveryManager: Error handling and retry logic
  - run_full_pipeline: Complete end-to-end execution
  - **Cost tracking integration: Budget controls and monitoring (Phase 17)**
  - **initialize_cost_tracking, update_cost_tracking, check_budget_before_operation (Phase 17)**
  - run_ingestion_only/run_summarization_only: Selective execution
  - Visualization, monitoring, and progress tracking
- `quality_control.py` - Quality control and validation framework (Phase 14)
  - QCDashboard: Overall statistics and metrics
  - DataQualityChecker: Comprehensive data quality validation
  - ErrorAnalyzer: Error categorization and remediation
  - ConsistencyValidator: Taxonomy and data consistency checks
  - QCReportGenerator: Comprehensive QC reports (Markdown/HTML)
  - 30+ validation and analysis functions
- `rag_query_interface.py` - RAG query interface for corpus exploration (Phase 15)
  - RAGQueryEngine: Main query engine with FAISS retrieval
  - Query functions: rag_query, generate_query_embedding, retrieve_top_k_chunks
  - Reranking: rerank_chunks, calculate_relevance_score, boost_section_scores
  - Answer generation: generate_answer (via Responses API), create_context_from_chunks
  - Interactive interface: interactive_query, display_query_results
  - Query history: QueryHistory class, track_query, export_query_history
  - Search utilities: search_by_title_substring, search_by_author, list_papers_in_topic
- `corpus_utilities.py` - Comprehensive corpus utilities (Phase 16)
  - Search functions: search_papers, search_by_title, search_by_author, search_by_date_range, search_by_topic, filter_by_status, advanced_search
  - Statistics: count_papers_by_year, count_papers_by_source, get_most_common_authors, get_most_common_venues, get_topic_distribution, generate_statistics_charts, generate_corpus_report
  - Export utilities: export_paper_subset, export_by_topic, export_by_date_range, generate_bibtex_entries, create_reading_list, export_to_markdown
  - Update functions: add_new_papers, reprocess_failed_papers, update_paper_metadata, reclassify_papers, rebuild_faiss_index, merge_corpus_states
  - Cleanup functions: remove_duplicate_papers, clean_orphaned_chunks, verify_data_integrity, optimize_storage, archive_old_versions, compact_corpus

### Utilities
- `notebook_builder.py` - Generate complete standalone notebooks

## Features

### Implemented (Phases 0-13)
- ✅ Environment inspection (Python version, GPU/CPU, system resources)
- ✅ Dependency installation (18 packages with version pinning)
- ✅ Import management with error handling
- ✅ Comprehensive data models with Pydantic validation
- ✅ Configuration schema with sensible defaults
- ✅ Helper utilities for metadata extraction and statistics
- ✅ Google Drive mounting and validation
- ✅ PDF discovery with recursive folder traversal
- ✅ Unique paper ID generation (deterministic hashing)
- ✅ Initial PaperRecord creation
- ✅ Duplicate file handling
- ✅ File access validation
- ✅ Disk space monitoring
- ✅ PDF file validation
- ✅ PDF parsing with PyMuPDF
- ✅ OCR fallback for scanned PDFs (pytesseract)
- ✅ Section detection for academic papers (7 section types)
- ✅ Sentence-aware text chunking
- ✅ Section-aware chunk creation
- ✅ Parse quality detection
- ✅ Comprehensive validation (parsing & chunks)
- ✅ LangGraph worker integration
- ✅ ArXiv ID detection and API integration
- ✅ ArXiv metadata extraction (title, authors, abstract, dates)
- ✅ DOI detection in text content
- ✅ CrossRef API integration for published papers
- ✅ PDF document properties extraction
- ✅ Abstract extraction from sections and patterns
- ✅ Metadata normalization (authors, titles, venues, dates)
- ✅ Metadata quality validation and scoring
- ✅ API rate limiting and retry logic
- ✅ Multiple metadata source prioritization
- ✅ OpenAI embedding generation with batch processing
- ✅ Exponential backoff retry logic for embeddings
- ✅ Embedding cost estimation and tracking
- ✅ FAISS vector index creation (CPU-based)
- ✅ Metadata mapping for chunk retrieval
- ✅ Index persistence (save/load with versioning)
- ✅ Index validation and integrity checks
- ✅ Search functionality for RAG queries
- ✅ GPT-5 summarization with reasoning effort
- ✅ Structured prompt generation for summaries
- ✅ Initial analysis notes generation
- ✅ Batch processing with rate limiting
- ✅ Summary quality validation
- ✅ CSV export with all metadata
- ✅ Parquet export for large datasets
- ✅ Export validation and statistics
- ✅ Paper-level embedding generation
- ✅ 3-tier hierarchical taxonomy construction
- ✅ KMeans/Agglomerative clustering algorithms
- ✅ GPT-5 topic label generation
- ✅ Cluster visualization and statistics
- ✅ Taxonomy validation and consistency checks
- ✅ Taxonomy review and approval workflow
- ✅ Taxonomy export to JSON
- ✅ Topic classification with GPT-5 reasoning
- ✅ Confidence scoring for classifications
- ✅ Tier consistency validation
- ✅ Classification batch processing
- ✅ Deep analysis pass (optional, detailed summaries)
- ✅ Final data export (CSV, Parquet, JSON)
- ✅ Export variants (full, summary)
- ✅ Statistics and quality reports
- ✅ Artifact management (FAISS, taxonomy, exports)
- ✅ **LangGraph workflow orchestration**
- ✅ **Supervisor pattern for stage coordination**
- ✅ **Checkpoint system (save/resume)**
- ✅ **Google Drive checkpoint backup**
- ✅ **Multiple execution modes (full, partial, selective)**
- ✅ **Quality control checks and validation**
- ✅ **Cost and time tracking**
- ✅ **Error handling and retry logic**
- ✅ **Progress monitoring and visualization**
- ✅ **Workflow state display and reporting**
- ✅ **RAG query interface with Responses API**
- ✅ **Interactive query and answer generation**
- ✅ **Query history tracking and refinement**
- ✅ **Comprehensive corpus search utilities**
- ✅ **Statistical analysis and reporting**
- ✅ **Multi-format export (BibTeX, markdown, HTML)**
- ✅ **Corpus maintenance and cleanup tools**
- ✅ **Data integrity verification**
- ✅ **Storage optimization**

### Planned (Phases 17-22)
- 📋 Advanced features and enhancements
- 📋 Additional testing and optimization

### Planned (Phases 17-22)
- 📋 Advanced features and enhancements
- 📋 Additional testing and optimization

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

## Running Tests

To validate the implementation:

```bash
# Test Phase 1 models
python validate_models.py

# Test Phase 2 Google Drive integration
python test_phase2.py

# Test Phase 3 PDF parsing and chunking
python test_phase3.py

# Run Phase 3 examples
python examples_phase3.py

# Test Phase 4 metadata extraction
python test_phase4.py

# Run Phase 4 examples
python examples_phase4.py

# Test Phase 15 RAG query interface
python test_phase15.py

# Run Phase 15 examples
python examples_phase15.py

# Test Phase 16 utility functions
python test_phase16.py

# Run Phase 16 examples
python examples_phase16.py
```

---

**Version:** 1.4  
**Last Updated:** 2025-11-24  
**Status:** Phases 0-16 Complete - Ready for Advanced Features Development
