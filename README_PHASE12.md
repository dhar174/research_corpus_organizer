# Phase 12: Final CSV/Parquet Export

**Status:** ✅ Complete  
**Version:** 1.0  
**Date:** 2025-11-24

---

## Overview

Phase 12 implements the final export stage of the RAG PDF Research Corpus System. After all processing is complete (parsing, summarization, classification), this phase exports the complete dataset with all metadata in multiple formats and generates comprehensive reports.

This phase builds on Phase 7's initial export functionality and adds:
- Complete metadata export with all classification fields
- Multiple export variants (full, summary, JSON)
- Comprehensive statistics and quality reports
- Artifact management and organization
- Google Drive integration

---

## Features

### Step 12.1: Final Data Export

Export all papers with complete metadata:
- ✅ All paper fields included
- ✅ All classification fields (tier1, tier2, tier3)
- ✅ Taxonomy version tracking
- ✅ All summaries (full_summary, deep_summary)
- ✅ All notes (initial_notes, classification_notes)
- ✅ Processing status and error tracking
- ✅ Multiple format support (CSV, Parquet)

### Step 12.2: Export Variants

Multiple export formats for different use cases:
- ✅ **Full CSV**: All fields for complete analysis
- ✅ **Summary CSV**: Key fields only for quick overview
- ✅ **Parquet**: Compressed format for large corpora
- ✅ **JSON**: Hierarchical data with taxonomy

### Step 12.3: Statistics and Quality Reports

Comprehensive analysis and reporting:
- ✅ Papers by processing status
- ✅ Papers by topic (all tiers)
- ✅ Processing statistics (tokens, costs, time)
- ✅ Data quality assessment
- ✅ Error tracking and analysis

### Step 12.4: Artifact Management

Save and organize all pipeline artifacts:
- ✅ Master CSV/Parquet files
- ✅ Taxonomy JSON
- ✅ FAISS index and metadata
- ✅ Error logs
- ✅ Processing logs
- ✅ Statistics reports
- ✅ GraphState updates with all paths

---

## Installation

Phase 12 uses the same dependencies as earlier phases:

```python
# Core dependencies (already installed in earlier phases)
import pandas  # Optional but recommended for Parquet
import json
from pathlib import Path
```

No additional installations required beyond Phase 7.

---

## Quick Start

### Basic Usage

```python
from rag_models import GraphState
from export_manager import save_all_artifacts

# After all processing is complete
artifact_paths = save_all_artifacts(
    state,
    output_dir="/content/drive/MyDrive/RAG_Outputs",
    base_filename="research_corpus",
    save_faiss=True,
    save_taxonomy=True,
    save_logs=True
)

# All artifacts are now saved and paths are in state
print(f"Master CSV: {artifact_paths['master_csv_path']}")
print(f"Taxonomy: {artifact_paths['taxonomy_json_path']}")
```

### Export Variants

```python
from export_manager import (
    export_full_csv,
    export_summary_csv,
    export_to_json,
    export_taxonomy_to_json
)

# Full CSV with all fields
export_full_csv(state, "/path/to/full.csv")

# Summary CSV with key fields only
export_summary_csv(state, "/path/to/summary.csv")

# JSON with papers and taxonomy
export_to_json(state, "/path/to/export.json", 
               include_taxonomy=True, 
               include_papers=True)

# Taxonomy only
export_taxonomy_to_json(state, "/path/to/taxonomy.json")
```

### Statistics and Quality

```python
from export_manager import (
    generate_statistics_report,
    generate_quality_report,
    display_export_summary
)

# Generate comprehensive statistics
stats = generate_statistics_report(state)
print(f"Total papers: {stats['total_papers']}")
print(f"Fully classified: {stats['classification']['fully_classified']}")

# Assess data quality
quality = generate_quality_report(state)
print(f"Quality score: {quality['overall_quality_score']:.1%}")

# Display summary to user
summary = display_export_summary(state, artifact_paths, verbose=True)
```

---

## Function Reference

### Step 12.1: Final Data Export

#### `export_final_data()`

Export all papers with complete metadata.

```python
export_paths = export_final_data(
    state: GraphState,
    output_dir: str,
    base_filename: str = "rag_corpus_final",
    formats: Optional[List[str]] = None  # ["csv", "parquet"]
) -> Dict[str, str]
```

**Returns:** Dictionary mapping format → file path

**Example:**
```python
paths = export_final_data(
    state,
    "/content/drive/MyDrive/Exports",
    "research_corpus_v1"
)
# Returns: {"csv": "...", "parquet": "...", "metadata": "..."}
```

#### `create_final_export_config()`

Create export configuration for final export.

```python
config = create_final_export_config()
# Includes all fields, no exclusions
```

---

### Step 12.2: Export Variants

#### `export_full_csv()`

Export full CSV with all fields.

```python
csv_path = export_full_csv(
    state: GraphState,
    output_path: str
) -> str
```

#### `export_summary_csv()`

Export summary CSV with key fields only.

```python
csv_path = export_summary_csv(
    state: GraphState,
    output_path: str,
    key_fields: Optional[Set[str]] = None  # Use defaults if None
) -> str
```

**Default key fields:**
- Identifiers: id, filename, arxiv_id, doi
- Metadata: title, authors, venue, year
- Summaries: full_summary, initial_notes
- Classification: tier1/2/3 topics with names and confidence
- Status: processing_status, error_reason

**Custom fields example:**
```python
custom_fields = {
    "id", "title", "authors", "year",
    "full_summary", "tier1_topic_name", "processing_status"
}
export_summary_csv(state, "custom.csv", key_fields=custom_fields)
```

#### `export_to_json()`

Export to JSON format (hierarchical data).

```python
json_path = export_to_json(
    state: GraphState,
    output_path: str,
    include_taxonomy: bool = True,
    include_papers: bool = True,
    pretty: bool = True
) -> str
```

**JSON structure:**
```json
{
  "export_metadata": {
    "timestamp": "2025-11-24T...",
    "version": "1.0",
    "total_papers": 100
  },
  "taxonomy": { ... },
  "papers": [ ... ],
  "config": { ... }
}
```

#### `export_taxonomy_to_json()`

Export taxonomy only to JSON.

```python
json_path = export_taxonomy_to_json(
    state: GraphState,
    output_path: str,
    pretty: bool = True
) -> str
```

---

### Step 12.3: Statistics and Quality Reports

#### `count_papers_by_status()`

Count papers by processing status.

```python
counts = count_papers_by_status(papers: Dict[str, PaperRecord])
# Returns: {"classified": 85, "summarized": 10, "failed": 5}
```

#### `count_papers_by_topic()`

Count papers by topic at a specific tier.

```python
counts = count_papers_by_topic(
    papers: Dict[str, PaperRecord],
    tier: int = 1  # 1, 2, or 3
) -> Dict[str, int]
# Returns: {"Machine Learning": 40, "NLP": 30, "Computer Vision": 30}
```

#### `generate_statistics_report()`

Generate comprehensive statistics report.

```python
stats = generate_statistics_report(state: GraphState)
```

**Report structure:**
```python
{
    "timestamp": "...",
    "total_papers": 100,
    "status_distribution": {...},
    "topic_distribution": {
        "tier1": {...},
        "tier2": {...},
        "tier3": {...}
    },
    "summaries": {
        "with_full_summary": 95,
        "with_deep_summary": 60,
        ...
    },
    "classification": {
        "tier1_classified": 85,
        "fully_classified": 80,
        ...
    },
    "errors": {
        "failed_papers": 5,
        "total_retries": 8
    },
    "taxonomy": {...}
}
```

#### `generate_quality_report()`

Generate data quality assessment.

```python
quality = generate_quality_report(state: GraphState)
```

**Quality metrics:**
- Metadata completeness (title, authors, abstract, etc.)
- Processing completeness
- Summary coverage
- Classification coverage
- Error rates
- Overall quality score (0-1)

**Example:**
```python
quality = generate_quality_report(state)
print(f"Quality score: {quality['overall_quality_score']:.1%}")
# Quality score: 92.5%

for metric, value in quality['quality_metrics'].items():
    print(f"{metric}: {value:.1%}")
# with_title: 98.0%
# with_summary: 95.0%
# with_classification: 90.0%
```

#### `display_export_summary()`

Display formatted export summary to user.

```python
summary = display_export_summary(
    state: GraphState,
    export_paths: Dict[str, str],
    verbose: bool = True
) -> str
```

**Output example:**
```
======================================================================
EXPORT SUMMARY
======================================================================

Exported Files:
  CSV          /content/drive/MyDrive/corpus.csv
               Size: 2.5 MB
  PARQUET      /content/drive/MyDrive/corpus.parquet
               Size: 850.2 KB

Total Papers: 100

Status Distribution:
  classified       85 ( 85.0%)
  summarized       10 ( 10.0%)
  failed            5 (  5.0%)

Tier 1 Topics (3 topics):
  Machine Learning               40 ( 40.0%)
  NLP                           30 ( 30.0%)
  Computer Vision               30 ( 30.0%)

Quality Score: 92.5%
======================================================================
```

---

### Step 12.4: Artifact Management

#### `save_all_artifacts()`

Save all artifacts from the pipeline (orchestration function).

```python
artifact_paths = save_all_artifacts(
    state: GraphState,
    output_dir: str,
    base_filename: str = "rag_corpus",
    save_faiss: bool = True,
    save_taxonomy: bool = True,
    save_logs: bool = True
) -> Dict[str, str]
```

**Saves:**
1. Master CSV and Parquet
2. Summary CSV
3. Full JSON export
4. Taxonomy JSON
5. FAISS index and metadata (if available)
6. Error logs
7. Processing logs
8. Statistics report
9. Quality report
10. Text summary

**Returns:** Dictionary of artifact_name → file_path

**Updates GraphState** with all artifact paths.

**Example:**
```python
paths = save_all_artifacts(
    state,
    "/content/drive/MyDrive/RAG_Outputs",
    "research_corpus_v1",
    save_faiss=True,
    save_taxonomy=True,
    save_logs=True
)

# Access paths
print(paths["master_csv_path"])
print(paths["taxonomy_json_path"])
print(paths["statistics"])
print(paths["quality_report"])
```

#### `save_error_logs()`

Save error logs to file.

```python
log_path = save_error_logs(
    state: GraphState,
    output_path: str
) -> str
```

**Log structure:**
```json
{
  "timestamp": "2025-11-24T...",
  "total_errors": 5,
  "errors": [
    {
      "paper_id": "abc123",
      "filename": "paper.pdf",
      "error_reason": "PDF parsing failed",
      "error_stage": "pdf_parsing",
      "retry_count": 2,
      "processing_status": "failed",
      "last_updated": "..."
    }
  ]
}
```

#### `save_processing_logs()`

Save processing logs and statistics.

```python
log_path = save_processing_logs(
    state: GraphState,
    output_path: str
) -> str
```

#### `update_state_with_paths()`

Update GraphState with artifact paths.

```python
state = update_state_with_paths(
    state: GraphState,
    artifact_paths: Dict[str, str]
) -> GraphState
```

**Updates:**
- `state["master_csv_path"]`
- `state["faiss_index_path"]`
- `state["faiss_meta_path"]`
- `state["taxonomy_json_path"]`
- `state["errors_log_path"]`
- `state["stats"]["artifact_paths"]` (all paths)

---

## Integration with Google Drive

### Save to Google Drive

```python
# Define Google Drive output directory
drive_output_dir = "/content/drive/MyDrive/RAG_Research_Corpus/Outputs"

# Save all artifacts
artifact_paths = save_all_artifacts(
    state,
    output_dir=drive_output_dir,
    base_filename="rag_corpus_v1",
    save_faiss=True,
    save_taxonomy=True,
    save_logs=True
)

# Files are now saved to Google Drive
print(f"Artifacts saved to Google Drive: {drive_output_dir}")
```

### Organize by Date

```python
from datetime import datetime

# Create dated output directory
date_str = datetime.now().strftime("%Y%m%d")
output_dir = f"/content/drive/MyDrive/RAG_Outputs/{date_str}"

artifact_paths = save_all_artifacts(state, output_dir)
```

---

## Complete Pipeline Example

Here's how Phase 12 fits into the complete pipeline:

```python
from rag_models import StateManager, create_default_config
from export_manager import save_all_artifacts, display_export_summary

# 1. Setup (Phases 0-2)
config = create_default_config()
state = StateManager.create_initial_state(config)

# 2. Process papers (Phases 3-11)
# ... parsing, metadata extraction, summarization, classification ...

# 3. Final Export (Phase 12)
output_dir = "/content/drive/MyDrive/RAG_Final_Output"

# Save all artifacts
artifact_paths = save_all_artifacts(
    state,
    output_dir=output_dir,
    base_filename="research_corpus",
    save_faiss=True,
    save_taxonomy=True,
    save_logs=True
)

# Display summary to user
display_export_summary(state, artifact_paths, verbose=True)

# Pipeline complete - ready for analysis and RAG queries
print(f"\n✅ Pipeline complete! All artifacts saved to: {output_dir}")
```

---

## Testing

Run the test suite:

```bash
python test_phase12.py
```

**Tests include:**
- Final data export
- All export variants
- Statistics generation
- Quality reporting
- Artifact management
- State updates

Run examples:

```bash
python examples_phase12.py
```

---

## File Outputs

### Directory Structure

After running `save_all_artifacts()`, your output directory will contain:

```
/output_dir/
├── research_corpus.csv                    # Master CSV (all fields)
├── research_corpus.parquet                # Master Parquet (compressed)
├── research_corpus_metadata.json          # Export metadata
├── research_corpus_summary.csv            # Summary CSV (key fields)
├── research_corpus_full.json              # Complete JSON (papers + taxonomy)
├── research_corpus_taxonomy.json          # Taxonomy only
├── research_corpus_errors.json            # Error logs
├── research_corpus_processing.json        # Processing logs
├── research_corpus_statistics.json        # Statistics report
├── research_corpus_quality.json           # Quality report
└── research_corpus_summary.txt            # Text summary
```

### File Sizes

Approximate sizes for 1000 papers:
- CSV: ~5-10 MB
- Parquet: ~2-4 MB (compressed)
- JSON (full): ~15-20 MB
- Taxonomy JSON: ~50-200 KB
- Logs and reports: ~100-500 KB each

---

## Best Practices

### 1. Export After Complete Processing

Only run final export after all processing phases are complete:
- ✅ All papers parsed
- ✅ All papers summarized (or attempted)
- ✅ Taxonomy created and approved
- ✅ All papers classified

### 2. Use Parquet for Large Corpora

For corpora with >1000 papers:
- Use Parquet format for better compression
- Preserves data types
- Faster to load for analysis

```python
export_final_data(state, output_dir, formats=["csv", "parquet"])
```

### 3. Review Quality Report

Always review the quality report before considering the pipeline complete:

```python
quality = generate_quality_report(state)

if quality['overall_quality_score'] < 0.85:
    print("⚠️ Quality score below 85% - review issues")
    for issue in quality['issues']:
        print(f"  - {issue}")
```

### 4. Save to Google Drive

Always save final outputs to Google Drive to preserve them:

```python
drive_dir = "/content/drive/MyDrive/RAG_Outputs"
save_all_artifacts(state, drive_dir)
```

### 5. Version Your Exports

Include version or date in filenames:

```python
from datetime import datetime

version = datetime.now().strftime("%Y%m%d_%H%M%S")
save_all_artifacts(
    state,
    output_dir,
    base_filename=f"corpus_v{version}"
)
```

---

## Troubleshooting

### Issue: Parquet export fails

**Solution:** Install pyarrow:
```python
!pip install pyarrow
```

Or use CSV only:
```python
export_final_data(state, output_dir, formats=["csv"])
```

### Issue: Low quality score

**Causes:**
- Many papers failed parsing
- Missing metadata
- Incomplete summaries
- Poor classification coverage

**Solution:** Review quality report and re-process failed papers:
```python
quality = generate_quality_report(state)
print(quality['issues'])
print(quality['warnings'])

# Identify failed papers
failed_papers = [
    p for p in state['papers'].values() 
    if p.processing_status == 'failed'
]
```

### Issue: Export files too large

**Solutions:**
1. Use Parquet instead of CSV (better compression)
2. Use summary CSV for quick analysis
3. Split by topic or date range

```python
# Export summary only
export_summary_csv(state, "summary.csv")

# Or use Parquet
export_final_data(state, output_dir, formats=["parquet"])
```

---

## Next Steps

After Phase 12 export:

1. **Phase 13:** LangGraph workflow integration
2. **Phase 14:** Quality control and validation
3. **Phase 15:** RAG query interface

Your data is now ready for:
- Analysis in pandas/Excel
- Visualization
- RAG querying
- Machine learning
- Publication

---

## API Reference

See `export_manager.py` for complete API documentation.

All Phase 12 functions are in the `export_manager` module with comprehensive docstrings.

---

## Version History

**v1.0** (2025-11-24)
- Initial Phase 12 implementation
- Final data export with complete metadata
- Export variants (full, summary, JSON)
- Statistics and quality reports
- Artifact management
- Complete integration with earlier phases

---

## Support

For issues or questions:
1. Check this README
2. Review `examples_phase12.py`
3. Run `test_phase12.py`
4. Check function docstrings in `export_manager.py`

---

**Phase 12 Complete!** 🎉

Your research corpus is now fully processed, exported, and ready for analysis and RAG-based querying.
