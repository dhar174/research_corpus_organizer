# Phase 1 Models - Quick Reference Guide

Quick reference for using the RAG PDF System data models.

---

## Quick Import

```python
from rag_models import (
    # Configuration
    RunConfig, create_default_config,
    
    # Core Models
    PaperRecord, PaperChunk, TopicNode, TopicHierarchy, GraphState,
    
    # State Management
    StateManager,
    
    # Helpers
    MetadataExtractor, StatisticsTracker, ErrorHandler, IDGenerator,
    
    # Utilities
    validate_paper_record, export_papers_to_csv, load_papers_from_csv,
)
```

---

## Common Tasks

### 1. Create Configuration

```python
# With defaults
config = create_default_config()

# With custom values
config = create_default_config(
    drive_folder_path="my_pdfs",
    max_papers_per_run=50,
    summary_model="gpt-4-turbo-preview",
    enable_ocr_fallback=True
)

# Display config
print(config.display_config())
```

### 2. Create Paper Record

```python
from datetime import date

paper_id = IDGenerator.generate_paper_id("/path/to/paper.pdf")

paper = PaperRecord(
    id=paper_id,
    file_path="/path/to/paper.pdf",
    filename="paper.pdf",
    title="My Research Paper",
    authors=["Author One", "Author Two"],
    year=2024,
    publish_date=date(2024, 1, 15)
)

# Serialize
paper_dict = paper.to_dict()

# Deserialize
paper2 = PaperRecord.from_dict(paper_dict)
```

### 3. Create Chunks

```python
chunk = PaperChunk(
    paper_id=paper.id,
    chunk_id=IDGenerator.generate_chunk_id(paper.id, 0),
    section_label="abstract",
    page_start=1,
    page_end=1,
    text="Abstract text here..."
)
```

### 4. Build Taxonomy

```python
# Create topics
t1 = TopicNode(
    id="T1_AI",
    label="Artificial Intelligence",
    description="AI research",
    paper_ids=["p1", "p2", "p3"]
)

t2 = TopicNode(
    id="T2_AI_ML",
    label="Machine Learning",
    description="ML within AI",
    parent_id="T1_AI",
    paper_ids=["p1", "p2"]
)

# Build hierarchy
hierarchy = TopicHierarchy(
    taxonomy_version="v1.0",
    total_papers=3,
    tier1=[t1],
    tier2=[t2],
    tier3=[]
)

# Validate
validation = hierarchy.validate_hierarchy()
if validation['valid']:
    print("Hierarchy is valid!")
```

### 5. Manage Workflow State

```python
# Initialize
config = create_default_config()
state = StateManager.create_initial_state(config)

# Add paper
state = StateManager.add_paper(state, paper)

# Add chunks
state = StateManager.add_chunks(state, paper.id, [chunk])

# Update paper
state = StateManager.update_paper(state, paper.id, {
    "full_summary": "Summary text...",
    "processing_status": "summarized"
})

# Mark complete
state = StateManager.mark_paper_complete(state, paper.id)

# Get stats
stats = StateManager.get_stats(state)
print(f"Total papers: {stats['total_papers']}")
```

### 6. Extract Metadata

```python
# Extract arXiv ID
arxiv_id = MetadataExtractor.extract_arxiv_id("paper_2301.12345.pdf")

# Extract DOI
doi = MetadataExtractor.extract_doi(text)

# Normalize authors
authors = MetadataExtractor.normalize_authors(["  John Doe  ", "Jane Smith"])

# Parse date
date_obj = MetadataExtractor.parse_date("2024-01-15")
```

### 7. Calculate Statistics

```python
text = "Sample paper text..."

# Calculate stats
stats = StatisticsTracker.calculate_text_stats(text, page_count=10)
print(f"Quality score: {stats['parse_quality_score']}")

# Estimate tokens
tokens = StatisticsTracker.estimate_tokens(text)
```

### 8. Handle Errors

```python
handler = ErrorHandler()

try:
    # Some operation
    process_paper(paper)
except Exception as e:
    handler.log_error(
        paper_id=paper.id,
        stage="parsing",
        error=e,
        context={"file": paper.file_path}
    )

# Get errors for paper
errors = handler.get_errors_by_paper(paper.id)

# Export to file
handler.export_errors("errors.json")
```

### 9. Validate Papers

```python
validation = validate_paper_record(paper)

if validation['valid']:
    print("✓ Paper is valid")
else:
    print("✗ Issues found:")
    for issue in validation['issues']:
        print(f"  - {issue}")

if validation['warnings']:
    print("Warnings:")
    for warning in validation['warnings']:
        print(f"  - {warning}")
```

### 10. Export/Import CSV

```python
# Export
papers = {
    "p1": paper1,
    "p2": paper2,
}
export_papers_to_csv(papers, "papers.csv")

# Import
papers = load_papers_from_csv("papers.csv")
```

---

## Model Field Reference

### RunConfig Fields
- `drive_folder_path`: Google Drive folder path
- `max_papers_per_run`: Limit papers per run
- `max_pages_per_paper`: Limit pages per paper
- `max_chunks_per_paper`: Limit chunks per paper
- `enable_ocr_fallback`: Enable OCR for scanned PDFs
- `summary_model`: Model for summaries
- `taxonomy_model`: Model for taxonomy
- `classification_model`: Model for classification
- `embedding_model`: Model for embeddings
- `summary_reasoning_effort`: "none"|"low"|"medium"|"high"
- `taxonomy_reasoning_effort`: "none"|"low"|"medium"|"high"
- `classification_reasoning_effort`: "none"|"low"|"medium"|"high"
- `cluster_tier1_target_k`: Target Tier 1 clusters
- `cluster_tier2_target_k`: Target Tier 2 clusters
- `cluster_tier3_target_k`: Target Tier 3 clusters
- `enable_deep_analysis_pass`: Enable Pass 2
- `taxonomy_approval_required`: Require manual approval
- `max_tokens_per_summary`: Token limit for summaries
- `max_tokens_per_classification`: Token limit for classification
- `chunk_size_chars`: Chunk size in characters
- `chunk_overlap_chars`: Overlap between chunks

### PaperRecord Fields
- `id`: Unique paper ID
- `file_path`: Absolute path to PDF
- `filename`: Original filename
- `source_folder`: Source folder path
- `source`: "arxiv"|"doi"|"other"
- `arxiv_id`: arXiv identifier
- `doi`: DOI
- `title`: Paper title
- `authors`: List of authors
- `venue`: Publication venue
- `publish_date`: Publication date
- `publish_date_source`: "arxiv"|"crossref"|"pdf"|"manual"|"unknown"
- `year`: Publication year
- `is_preprint`: Whether preprint
- `arxiv_version`: arXiv version
- `raw_text_stats`: Text statistics dict
- `abstract_text`: Abstract
- `full_summary`: High-level summary
- `deep_summary`: Deep analysis summary
- `initial_notes`: Initial notes
- `classification_notes`: Classification reasoning
- `tier1_topic`: Tier 1 topic ID
- `tier1_topic_name`: Tier 1 topic name
- `tier1_confidence`: Confidence score (0-1)
- `tier2_topic`: Tier 2 topic ID
- `tier2_topic_name`: Tier 2 topic name
- `tier2_confidence`: Confidence score (0-1)
- `tier3_topic`: Tier 3 topic ID
- `tier3_topic_name`: Tier 3 topic name
- `tier3_confidence`: Confidence score (0-1)
- `taxonomy_version`: Taxonomy version
- `processing_status`: "pending"|"parsed"|"summarized"|"embedded"|"deep_analyzed"|"classified"|"failed"
- `error_reason`: Error message
- `error_stage`: Stage where error occurred
- `retry_count`: Number of retries
- `created_at`: Creation timestamp
- `last_updated`: Last update timestamp

### PaperChunk Fields
- `paper_id`: Parent paper ID
- `chunk_id`: Unique chunk ID
- `section_label`: "abstract"|"introduction"|"methods"|"results"|"discussion"|"conclusion"|"references"|"other"
- `page_start`: Starting page
- `page_end`: Ending page
- `text`: Raw text
- `cleaned_text`: Cleaned text
- `embedding_id`: FAISS index ID
- `embedding_model`: Embedding model name
- `char_count`: Character count
- `token_count_estimate`: Estimated tokens

### TopicNode Fields
- `id`: Unique topic ID
- `label`: Topic label
- `description`: Topic description
- `paper_ids`: List of paper IDs
- `parent_id`: Parent topic ID
- `paper_count`: Number of papers
- `centroid`: Centroid vector

### GraphState Fields
- `config`: RunConfig
- `papers`: Dict[str, PaperRecord]
- `chunks`: Dict[str, List[PaperChunk]]
- `topic_hierarchy`: TopicHierarchy
- `taxonomy_approved`: bool
- `faiss_index_path`: Path to FAISS index
- `faiss_meta_path`: Path to FAISS metadata
- `master_csv_path`: Path to master CSV
- `taxonomy_json_path`: Path to taxonomy JSON
- `errors_log_path`: Path to errors log
- `current_phase`: Current phase name
- `papers_pending`: List of pending paper IDs
- `papers_completed`: List of completed paper IDs
- `papers_failed`: List of failed paper IDs
- `errors`: List of error dicts
- `stats`: Statistics dict

---

## For More Details

- **Full Documentation**: See `PHASE1_COMPLETION.md`
- **Usage Examples**: See `examples_usage.py`
- **Validation Tests**: See `validate_models.py`
- **Implementation**: See `rag_models.py`

---

**Quick Start:**

```python
from rag_models import create_default_config, StateManager

# 1. Configure
config = create_default_config(drive_folder_path="my_pdfs")

# 2. Initialize state
state = StateManager.create_initial_state(config)

# 3. Start processing!
```
