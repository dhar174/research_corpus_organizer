# RAG PDF Research Corpus System - Setup Guide

**Version:** 1.0  
**Date:** 2025-11-21  
**Status:** Phase 0 and Phase 1 Complete

## Overview

This project implements a comprehensive system for processing and organizing academic PDF research papers using:
- **LangGraph** workflows for orchestration
- **GPT-5.1 Thinking** for summarization and classification
- **FAISS** for vector indexing and RAG queries
- **3-tier hierarchical topic taxonomy** for organization

## Project Structure

```
research_corpus_organizer/
├── rag_pdf_system.ipynb          # Main Google Colab notebook
├── rag_models.py                  # Data models and schemas (Phase 1)
├── notebook_builder.py            # Script to generate complete notebook
├── FINAL_NOTEBOOK_ACTION_PLAN.md  # Complete implementation plan
├── rag_pdf_system_spec_v_2.md     # Technical specification
└── README_SETUP.md                # This file
```

## Completed Implementation

### Phase 0: Environment Setup ✓

The notebook (`rag_pdf_system.ipynb`) includes:

1. **Step 0.1:** Notebook structure with title, description, and version info
2. **Step 0.2:** Environment inspection cells
   - Python version check (requires 3.10+)
   - GPU/CPU availability check
   - System resource information
3. **Step 0.3:** Dependency installation
   - OpenAI SDK (GPT-5.1 support)
   - LangGraph and LangChain
   - PyMuPDF (PDF parsing)
   - FAISS (vector indexing)
   - scikit-learn, hdbscan (clustering)
   - pandas, numpy, tqdm, matplotlib, seaborn
   - pydantic (data validation)
   - Other required libraries
4. **Step 0.4:** Import statements with error handling

**Note:** Step 0.5 (Configuration) is defined in `rag_models.py`

### Phase 1: Data Models and Schemas ✓

All core data structures are defined in `rag_models.py`:

1. **RunConfig:** System configuration with validation
2. **PaperRecord:** Paper metadata, summaries, and classifications
3. **PaperChunk:** Text chunks for RAG indexing
4. **TopicHierarchy:** 3-tier topic taxonomy (TopicNode, TopicHierarchy)
5. **GraphState:** LangGraph workflow state
6. **Helper Classes:**
   - StateManager: GraphState operations
   - MetadataExtractor: Extract arXiv IDs, DOIs, etc.
   - StatisticsTracker: Text statistics and quality scores
   - ErrorHandler: Error logging and tracking
   - IDGenerator: Generate unique IDs

## Usage

### Option 1: Use the Partial Notebook (Current State)

1. **Open the notebook in Google Colab:**
   - Upload `rag_pdf_system.ipynb` to Google Colab
   - Or open directly from GitHub

2. **Run Phase 0 setup cells:**
   ```python
   # Cell 1: Check Python version
   # Cell 2: Check GPU availability
   # Cell 3: Display runtime info
   # Cell 4: Install dependencies (may take several minutes)
   # Cell 5: Import libraries
   ```

3. **Import data models:**
   ```python
   # In a new cell, import the models
   from rag_models import (
       RunConfig,
       PaperRecord,
       PaperChunk,
       TopicHierarchy,
       TopicNode,
       GraphState,
       StateManager,
       MetadataExtractor,
       StatisticsTracker,
       ErrorHandler,
       IDGenerator
   )
   ```

4. **Create configuration:**
   ```python
   config = RunConfig(
       drive_folder_path="PDFs",
       max_papers_per_run=10,  # Limit for testing
       summary_model="gpt-5.1-mini",
       taxonomy_model="gpt-5.1-mini",
       classification_model="gpt-5.1-mini",
       embedding_model="text-embedding-3-large",
   )
   
   print("Configuration created successfully!")
   config.model_dump()
   ```

5. **Initialize state:**
   ```python
   state = StateManager.create_initial_state(config)
   print(f"Initial state created with {len(state['papers'])} papers")
   ```

### Option 2: Generate Complete Notebook (Requires Python Environment)

If you have a Python environment with the dependencies installed, you can generate the complete notebook:

```bash
# Run the notebook builder script
python notebook_builder.py

# This creates: RAG_PDF_Research_Corpus_System.ipynb
```

## Configuration Options

The `RunConfig` model includes all necessary parameters:

### File Paths
- `drive_folder_path`: Google Drive folder with PDFs

### Processing Limits
- `max_papers_per_run`: Limit number of papers (None = all)
- `max_pages_per_paper`: Limit pages per paper
- `max_chunks_per_paper`: Maximum chunks per paper (default: 100)

### Models
- `summary_model`: Model for summaries (e.g., "gpt-5.1-mini")
- `taxonomy_model`: Model for taxonomy generation
- `classification_model`: Model for paper classification
- `embedding_model`: Model for embeddings (e.g., "text-embedding-3-large")

### Reasoning Effort (GPT-5.1)
- `summary_reasoning_effort`: "none", "low", "medium", "high"
- `taxonomy_reasoning_effort`: "none", "low", "medium", "high"
- `classification_reasoning_effort`: "none", "low", "medium", "high"

### Clustering
- `cluster_tier1_target_k`: Number of Tier 1 topics (default: 8)
- `cluster_tier2_target_k`: Number of Tier 2 topics per Tier 1 (default: 3)
- `cluster_tier3_target_k`: Number of Tier 3 topics per Tier 2 (default: 2)

### Feature Flags
- `enable_ocr_fallback`: Enable OCR for scanned PDFs
- `enable_deep_analysis_pass`: Enable detailed analysis (Pass 2)
- `taxonomy_approval_required`: Require manual approval
- `use_tiered_models`: Use cheaper models for bulk tasks

### Token Limits
- `max_tokens_per_summary`: Max tokens for summaries (default: 2000)
- `max_tokens_per_classification`: Max tokens for classification (default: 1000)

### Chunking
- `chunk_size_chars`: Target chunk size (default: 1500)
- `chunk_overlap_chars`: Overlap between chunks (default: 200)

## Data Model Schemas

### PaperRecord Fields

```python
{
    "id": str,                      # Unique paper ID
    "file_path": str,               # Absolute path to PDF
    "filename": str,                # Original filename
    "source": "arxiv|doi|other",    # Source type
    "arxiv_id": str,                # arXiv identifier
    "doi": str,                     # DOI
    "title": str,                   # Paper title
    "authors": List[str],           # Authors list
    "venue": str,                   # Publication venue
    "publish_date": date,           # Publication date
    "year": int,                    # Publication year
    "raw_text_stats": dict,         # Text statistics
    "abstract_text": str,           # Abstract
    "full_summary": str,            # High-level summary
    "deep_summary": str,            # Detailed summary (optional)
    "initial_notes": str,           # Analysis notes
    "classification_notes": str,    # Classification reasoning
    "tier1_topic": str,             # Tier 1 topic ID
    "tier1_topic_name": str,        # Tier 1 topic name
    "tier1_confidence": float,      # Confidence (0-1)
    # ... tier2 and tier3 fields ...
    "processing_status": str,       # pending|parsed|summarized|embedded|classified|failed
    "error_reason": str,            # Error message if failed
    "created_at": datetime,         # Creation timestamp
    "last_updated": datetime        # Last update timestamp
}
```

### TopicHierarchy Structure

```python
{
    "taxonomy_version": "v1.0",
    "created_at": datetime,
    "notes": str,
    "total_papers": int,
    "tier1": [
        {
            "id": "T1_XXX",
            "label": "Topic Name",
            "description": "Topic description",
            "paper_ids": ["paper1", "paper2"],
            "paper_count": int
        }
    ],
    "tier2": [...],  # Similar structure with parent_id
    "tier3": [...]   # Similar structure with parent_id
}
```

## Next Phases

The following phases are planned for implementation:

- **Phase 2:** Google Drive Integration
- **Phase 3:** PDF Parsing and Chunking
- **Phase 4:** Metadata Extraction
- **Phase 5:** Embedding Generation and FAISS Index
- **Phase 6:** Summarization (Pass 1)
- **Phase 7:** Initial CSV Export
- **Phase 8:** Topic Modeling and Taxonomy
- **Phase 9:** Taxonomy Review and Approval
- **Phase 10:** Final Classification (Pass 3)
- **Phase 11:** Deep Analysis (Pass 2, Optional)
- **Phase 12:** Final Export
- **Phase 13:** LangGraph Workflow Integration
- **Phase 14:** Quality Control
- **Phase 15:** RAG Query Interface
- **Phases 16-22:** Utilities, Cost Tracking, Testing, Deployment

## Development Notes

### Why Separate `rag_models.py`?

The data models are separated into a dedicated Python module for several reasons:

1. **Reusability:** Models can be imported by multiple notebooks or scripts
2. **Maintainability:** Easier to update schemas in one place
3. **Testing:** Models can be unit tested independently
4. **Type Safety:** Better IDE support and type checking
5. **Version Control:** Cleaner diffs when models change

### Notebook Strategy

The current approach uses:
- **rag_pdf_system.ipynb:** Working notebook with Phase 0 implementation
- **rag_models.py:** All data models and helper classes
- **notebook_builder.py:** Script to generate a complete standalone notebook

This allows for flexible development while maintaining a clean separation of concerns.

## Testing Your Setup

To verify your setup is working:

```python
# Test creating a config
from rag_models import RunConfig

config = RunConfig()
print("✓ RunConfig created successfully")
print(config.model_dump_json(indent=2))

# Test creating a paper record
from rag_models import PaperRecord

paper = PaperRecord(
    id="test001",
    file_path="/path/to/paper.pdf",
    filename="paper.pdf"
)
print("✓ PaperRecord created successfully")

# Test state manager
from rag_models import StateManager

state = StateManager.create_initial_state(config)
state = StateManager.add_paper(state, paper)
print(f"✓ State has {len(state['papers'])} paper(s)")

# Test helper classes
from rag_models import IDGenerator, MetadataExtractor, StatisticsTracker

paper_id = IDGenerator.generate_paper_id("/test/path.pdf")
print(f"✓ Generated paper ID: {paper_id}")

arxiv_id = MetadataExtractor.extract_arxiv_id("2301.12345v2.pdf")
print(f"✓ Extracted arXiv ID: {arxiv_id}")

stats = StatisticsTracker.calculate_text_stats("Test text" * 100, page_count=1)
print(f"✓ Text stats: {stats}")

print("\n✓✓✓ All tests passed! Setup is working correctly.")
```

## Troubleshooting

### Import Errors

If you get import errors when trying to use `rag_models`:

1. Make sure `rag_models.py` is in the same directory as your notebook
2. In Google Colab, upload the file to the session
3. Or mount Google Drive and adjust the path:
   ```python
   import sys
   sys.path.append('/content/drive/MyDrive/path/to/models')
   from rag_models import RunConfig
   ```

### Pydantic Validator Issues

If you see deprecation warnings about validators:
- The code uses Pydantic v2 syntax
- Make sure you have `pydantic>=2.0.0` installed
- Update if necessary: `!pip install --upgrade pydantic`

### Missing Dependencies

If dependencies are missing:
- Run the installation cell in the notebook again
- Restart the runtime if prompted
- Check that all packages installed successfully

## Support and Documentation

- **Technical Specification:** See `rag_pdf_system_spec_v_2.md`
- **Implementation Plan:** See `FINAL_NOTEBOOK_ACTION_PLAN.md`
- **Issues:** Report issues on the GitHub repository

## License

This project is part of the research_corpus_organizer repository.

---

**Status:** Phase 0 and Phase 1 Complete  
**Last Updated:** 2025-11-21  
**Version:** 1.0
