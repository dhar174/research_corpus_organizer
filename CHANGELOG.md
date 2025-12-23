# Changelog

All notable changes to the RAG PDF Research Corpus System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-25

### Added

#### Phase 0: Environment Setup
- Python 3.10+ requirement and validation
- Comprehensive dependency installation (18 packages)
- GPU/CPU detection and system information display
- Import management with graceful fallbacks

#### Phase 1: Data Models
- `RunConfig` - Complete configuration schema with validation
- `PaperRecord` - Paper metadata and processing status tracking
- `PaperChunk` - Text chunks for RAG indexing
- `TopicNode` and `TopicHierarchy` - 3-tier topic taxonomy
- `GraphState` - LangGraph workflow state management
- Helper classes: `MetadataExtractor`, `StatisticsTracker`, `ErrorHandler`, `IDGenerator`

#### Phase 2: Google Drive Integration
- Google Drive mounting and validation
- Recursive PDF discovery with progress tracking
- Unique paper ID generation (deterministic hashing)
- File access validation and disk space monitoring

#### Phase 3: PDF Parsing and Chunking
- PDF text extraction using PyMuPDF
- OCR fallback for scanned PDFs (pytesseract)
- Section detection for academic papers (7 section types)
- Sentence-aware text chunking with configurable size and overlap
- Parse quality detection and validation

#### Phase 4: Metadata Extraction
- ArXiv ID detection and API integration
- CrossRef API integration for DOI lookup
- PDF document properties extraction
- Abstract extraction from parsed text
- Metadata normalization and quality scoring
- Rate limiting and retry logic for external APIs

#### Phase 5: Embedding Generation
- OpenAI embedding generation with batch processing
- FAISS vector index creation (CPU-based)
- Metadata mapping for chunk retrieval
- Index persistence with versioning
- Cost estimation and tracking

#### Phase 6: Summarization
- GPT-5/GPT-5-mini summarization with reasoning effort levels
- Structured prompt generation
- Initial analysis notes generation
- Batch processing with rate limiting
- Summary quality validation

#### Phase 7: Initial Export
- CSV export with all metadata
- Parquet export for large datasets
- Export validation and statistics

#### Phase 8: Topic Taxonomy
- Paper-level embedding generation
- 3-tier hierarchical taxonomy construction
- KMeans and Agglomerative clustering algorithms
- GPT-5-mini topic label generation
- Taxonomy visualization and statistics

#### Phase 9: Taxonomy Review
- Taxonomy display and review workflow
- Manual approval process
- Taxonomy export to JSON
- Topic editing utilities

#### Phase 10: Paper Classification
- GPT-5-mini paper classification into taxonomy
- Confidence scoring for classifications
- Tier consistency validation
- Batch classification processing

#### Phase 11: Deep Analysis (Optional)
- Optional detailed analysis pass (Pass 2)
- Methods and results section focus
- Deep summary generation

#### Phase 12: Final Export
- Complete data export (CSV, Parquet, JSON)
- Export variants (full, summary)
- Artifact management

#### Phase 13: LangGraph Workflow
- StateGraph workflow definition
- Supervisor pattern for stage coordination
- Checkpoint system with save/resume capability
- Multiple execution modes (full, ingestion, summarization, classification)
- Progress monitoring and visualization

#### Phase 14: Quality Control
- QC dashboard with overall statistics
- Data quality validation (30+ checks)
- Error analysis and categorization
- Consistency validation
- QC report generation (Markdown/HTML)

#### Phase 15: RAG Query Interface
- FAISS-based semantic search
- Query embedding generation
- Chunk retrieval and reranking
- Answer generation using Responses API
- Interactive query interface
- Query history tracking
- Search utilities (title, author, topic, date range)

#### Phase 16: Corpus Utilities
- Comprehensive search functions
- Statistical analysis and reporting
- Multi-format export (BibTeX, Markdown, HTML)
- Corpus maintenance and cleanup tools
- Data integrity verification
- Storage optimization

#### Phase 17: Cost Tracking
- Real-time API cost tracking
- Budget enforcement with configurable limits
- Batch API 50% discount calculation
- Result caching for duplicate avoidance
- Cost breakdown by operation
- Automated cost-saving recommendations
- Cost report generation (JSON and formatted output)

#### Phase 18: Error Handling
- Global error handler with context
- API error handling (rate limits, timeouts, quotas)
- Exponential backoff retry logic
- Checkpoint-based recovery
- Selective retry of failed papers
- Rollback capabilities

#### Phase 19: Documentation
- Comprehensive USER_GUIDE.md
- EXAMPLES.md with configuration and query examples
- README_SETUP.md for installation
- Inline documentation and docstrings

#### Phase 20: Testing
- Unit tests for all core functions
- Integration tests for pipeline stages
- Edge case tests (scanned PDFs, large/small papers, corrupted files)
- Performance benchmarks
- Quality validation tests

#### Phase 21: Deployment
- Version numbering and changelog
- Distribution package (setup.py)
- Example notebook creation
- Final code review and optimization
- Comprehensive README updates

### Models and APIs
- **Text Models**: GPT-5, GPT-5-mini (via Responses API)
- **Reasoning Models**: O4, O4-mini (with thinking/reasoning effort)
- **Embedding Models**: text-embedding-3-large, text-embedding-3-small
- **External APIs**: arXiv API, CrossRef API

### Dependencies
- Python 3.10+
- openai>=1.3.0
- langgraph>=0.0.30
- langchain>=0.1.0
- pymupdf>=1.23.0
- faiss-cpu>=1.7.4
- scikit-learn>=1.3.0
- pydantic>=2.0.0
- pandas>=2.0.0
- numpy>=1.24.0

## [Unreleased]

### Added
- PyPI packaging support with `pyproject.toml` (PEP 621/517 compliant)
- Package verification tests (`test_package_publish.py`)
- `MANIFEST.in` for source distribution control
- `GITHUB_ACTIONS_SETUP.md` with workflow configurations for Trusted Publishing
- Updated README with PyPI installation instructions
- PyPI badges in README

### Changed
- Simplified `setup.py` to thin wrapper for backward compatibility
- Updated `.gitignore` to include test_package_publish.py

### Planned
- Web interface (Gradio/Streamlit)
- Fine-tuned models for better classification
- Auto-update from arXiv
- Recommendation system
- Multi-language support
- Citation network analysis

---

For detailed implementation documentation, see:
- [FINAL_NOTEBOOK_ACTION_PLAN.md](FINAL_NOTEBOOK_ACTION_PLAN.md)
- [USER_GUIDE.md](USER_GUIDE.md)
- [EXAMPLES.md](EXAMPLES.md)
