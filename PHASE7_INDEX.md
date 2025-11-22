# Phase 7: Initial CSV Export - Quick Reference Index

**Version:** 1.0  
**Module:** `export_manager.py`  
**Date:** 2025-11-22

---

## Quick Links

- [Full Documentation](PHASE7_COMPLETION.md)
- [Examples](examples_phase7.py)
- [Tests](test_phase6.py)
- [Source Code](export_manager.py)

---

## Core Functions

### Step 7.1: CSV Export Function

#### `export_papers_to_csv(papers, output_path, config=None, include_export_metadata=True)`
Main function to export papers to CSV format.

**Quick Start:**
```python
from export_manager import export_papers_to_csv

csv_path = export_papers_to_csv(
    papers=state["papers"],
    output_path="/drive/exports/papers.csv"
)
```

**Parameters:**
- `papers`: Dict[str, PaperRecord] - Papers to export
- `output_path`: str - Path to CSV file
- `config`: ExportConfig - Optional configuration
- `include_export_metadata`: bool - Add metadata columns

**Returns:** str - Path to created CSV file

---

#### `ExportConfig` Class
Configuration for export operations.

**Quick Start:**
```python
from export_manager import ExportConfig

config = ExportConfig(
    flatten_nested=True,
    include_metadata=True,
    timestamp_format="iso"
)
```

**Parameters:**
- `include_fields`: Set[str] - Fields to include (None = all)
- `exclude_fields`: Set[str] - Fields to exclude
- `flatten_nested`: bool - Flatten lists/dicts (default: True)
- `include_metadata`: bool - Add export metadata (default: True)
- `timestamp_format`: str - "iso" or "epoch" (default: "iso")

---

#### `flatten_paper_record(paper, config)`
Convert PaperRecord to flat dictionary.

**Use case:** Custom export formats or preprocessing

**Quick Start:**
```python
from export_manager import flatten_paper_record, ExportConfig

config = ExportConfig(flatten_nested=True)
flat_dict = flatten_paper_record(paper, config)
```

---

#### `filter_papers_for_export(papers, status_filter=None, require_summary=False, require_classification=False)`
Filter papers based on criteria.

**Quick Start:**
```python
from export_manager import filter_papers_for_export

# Only export summarized papers
filtered = filter_papers_for_export(
    papers=state["papers"],
    status_filter=["summarized", "classified"],
    require_summary=True
)
```

**Parameters:**
- `papers`: Dict[str, PaperRecord] - Papers to filter
- `status_filter`: List[str] - Acceptable statuses
- `require_summary`: bool - Must have full_summary
- `require_classification`: bool - Must have topic

**Returns:** Dict[str, PaperRecord] - Filtered papers

---

### Step 7.2: Initial Export After Pass 1

#### `export_after_pass1(state, output_path, include_partial=True, save_metadata=True)`
Export papers after summarization pass with metadata.

**Quick Start:**
```python
from export_manager import export_after_pass1

state = export_after_pass1(
    state=state,
    output_path="/drive/exports/papers_pass1.csv",
    include_partial=True,
    save_metadata=True
)

print(f"Exported to: {state['master_csv_path']}")
```

**Parameters:**
- `state`: GraphState - Current state with papers
- `output_path`: str - Path for CSV export
- `include_partial`: bool - Include in-progress papers
- `save_metadata`: bool - Save .metadata.json file

**Returns:** GraphState - Updated state

**State Updates:**
- Sets `state["master_csv_path"]`
- Adds `state["stats"]["export_metadata"]`

---

#### `create_export_metadata(state, export_path, export_type="csv")`
Generate export metadata dictionary.

**Quick Start:**
```python
from export_manager import create_export_metadata

metadata = create_export_metadata(
    state=state,
    export_path="/drive/exports/papers.csv",
    export_type="csv"
)
```

**Returns:** Dict with:
- `export_timestamp`: ISO timestamp
- `total_papers`: int
- `status_distribution`: Dict[status, count]
- `with_summary`: int
- `with_notes`: int
- `with_classification`: int
- `run_config`: Config summary

---

### Step 7.3: Parquet Export (Optional)

#### `export_papers_to_parquet(papers, output_path, compression="snappy", config=None)`
Export to Parquet format for large datasets.

**Quick Start:**
```python
from export_manager import export_papers_to_parquet

parquet_path = export_papers_to_parquet(
    papers=state["papers"],
    output_path="/drive/exports/papers.parquet",
    compression="snappy"
)
```

**Parameters:**
- `papers`: Dict[str, PaperRecord] - Papers to export
- `output_path`: str - Path to Parquet file
- `compression`: str - "snappy", "gzip", "brotli", "none"
- `config`: ExportConfig - Optional configuration

**Returns:** str - Path to created file

**Requires:** pandas, pyarrow

**Benefits:**
- 3-4x smaller files
- Preserves data types
- Faster loading

---

#### `export_papers_compressed(state, base_path, formats=None)`
Export in multiple formats.

**Quick Start:**
```python
from export_manager import export_papers_compressed

paths = export_papers_compressed(
    state=state,
    base_path="/drive/exports/papers",
    formats=["csv", "parquet"]
)
# Returns: {"csv": "...csv", "parquet": "...parquet"}
```

---

### Step 7.4: Export Validation

#### `validate_export(export_path, expected_count, expected_fields=None)`
Validate export file integrity.

**Quick Start:**
```python
from export_manager import validate_export

validation = validate_export(
    export_path="/drive/exports/papers.csv",
    expected_count=100,
    expected_fields={"id", "title", "full_summary"}
)

if validation["valid"]:
    print("✅ Export is valid")
else:
    print("❌ Issues:", validation["issues"])
```

**Returns:** Dict with:
- `valid`: bool - Overall result
- `issues`: List[str] - Critical problems
- `warnings`: List[str] - Minor concerns
- `file_size`: int - Bytes
- `row_count`: int - Number of rows
- `columns`: List[str] - Column names

---

#### `export_summary_statistics(export_path, state=None)`
Generate detailed export statistics.

**Quick Start:**
```python
from export_manager import export_summary_statistics

stats = export_summary_statistics(
    export_path="/drive/exports/papers.csv",
    state=state
)

print(f"Rows: {stats['row_count']}")
print(f"Size: {stats['file_size_mb']:.2f} MB")
```

**Returns:** Dict with:
- File info: path, name, size (bytes/KB/MB)
- Content: row_count, column_count, columns
- Distribution: status_distribution (if available)
- Statistics: processing_stats (if state provided)

---

## Common Patterns

### Pattern 1: Basic Export
```python
from export_manager import export_papers_to_csv

csv_path = export_papers_to_csv(
    papers=state["papers"],
    output_path="/drive/exports/papers.csv"
)
```

### Pattern 2: Export with Validation
```python
from export_manager import export_papers_to_csv, validate_export

# Export
csv_path = export_papers_to_csv(papers, output_path)

# Validate
validation = validate_export(csv_path, expected_count=len(papers))
if not validation["valid"]:
    print("Export failed validation!")
```

### Pattern 3: Filtered Export
```python
from export_manager import filter_papers_for_export, export_papers_to_csv

# Filter
filtered = filter_papers_for_export(
    papers=state["papers"],
    status_filter=["summarized"],
    require_summary=True
)

# Export
csv_path = export_papers_to_csv(filtered, output_path)
```

### Pattern 4: Complete Pass 1 Export
```python
from export_manager import export_after_pass1

state = export_after_pass1(
    state=state,
    output_path="/drive/exports/papers_pass1.csv",
    include_partial=True,
    save_metadata=True
)
```

### Pattern 5: Multi-Format Export
```python
from export_manager import export_papers_compressed

paths = export_papers_compressed(
    state=state,
    base_path="/drive/exports/papers",
    formats=["csv", "parquet"]
)
```

### Pattern 6: Custom Configuration
```python
from export_manager import ExportConfig, export_papers_to_csv

config = ExportConfig(
    exclude_fields={"error_reason", "error_stage"},
    flatten_nested=True,
    include_metadata=True
)

csv_path = export_papers_to_csv(papers, output_path, config=config)
```

---

## Data Handling

### Nested Data Flattening

**Lists:**
```python
# Input: authors = ["Alice", "Bob", "Charlie"]
# Output: "Alice; Bob; Charlie"
```

**Dicts:**
```python
# Input: raw_text_stats = {"pages": 10, "chars": 50000}
# Output: '{"pages": 10, "chars": 50000}'
```

**Datetimes:**
```python
# Input: created_at = datetime(2025, 11, 22, 18, 30)
# Output (iso): "2025-11-22T18:30:00.000000"
# Output (epoch): 1732298400.0
```

---

## Field Reference

### Always Exported Fields

Core identifiers:
- `id`, `file_path`, `filename`

Metadata:
- `title`, `authors`, `venue`, `publish_date`, `year`
- `arxiv_id`, `doi`, `source`

Content:
- `abstract_text`, `full_summary`, `initial_notes`

Classification:
- `tier1_topic`, `tier2_topic`, `tier3_topic`
- `tier1_confidence`, `tier2_confidence`, `tier3_confidence`

Status:
- `processing_status`, `error_reason`, `error_stage`

Timestamps:
- `created_at`, `last_updated`

### Optional Metadata Fields

If `include_export_metadata=True`:
- `export_timestamp`: When export was created
- `export_version`: Export format version

---

## File Format Examples

### CSV Output
```csv
id,title,authors,full_summary,processing_status,export_timestamp
abc123,"Paper Title","Alice; Bob","This paper...",summarized,2025-11-22T18:30:00
def456,"Another Paper","Charlie","Research on...",summarized,2025-11-22T18:30:00
```

### Metadata JSON
```json
{
  "export_timestamp": "2025-11-22T18:30:00.000Z",
  "export_type": "csv",
  "export_path": "/drive/exports/papers.csv",
  "total_papers": 100,
  "status_distribution": {
    "summarized": 85,
    "failed": 5,
    "pending": 10
  },
  "with_summary": 85,
  "with_notes": 80
}
```

---

## Performance Guidelines

### File Size Estimates

**CSV (100 papers):**
- With summaries: ~500 KB - 2 MB
- Gzipped: ~100 KB - 500 KB

**Parquet (100 papers):**
- Snappy compression: ~150 KB - 700 KB
- Gzip compression: ~100 KB - 400 KB

### When to Use Parquet

✅ Use Parquet when:
- > 1000 papers
- Need fast loading for analysis
- Want smaller file sizes
- Have pandas installed

❌ Stick with CSV when:
- < 500 papers
- Need human readability
- Sharing with non-technical users
- Pandas not available

---

## Troubleshooting

### "Module not found: pandas"
Parquet export requires pandas:
```bash
pip install pandas pyarrow
```

### "Permission denied"
Ensure Google Drive is mounted:
```python
from google.colab import drive
drive.mount('/content/drive')
```

### "Row count mismatch"
Check filter settings:
```python
# Include all papers
state = export_after_pass1(state, path, include_partial=True)
```

### "Missing fields"
Check ExportConfig:
```python
config = ExportConfig(exclude_fields=set())  # Don't exclude any
```

---

## Related Modules

- **rag_models.py**: PaperRecord, GraphState definitions
- **summarization_pass1.py**: Phase 6 (provides data for export)
- **drive_utils.py**: Google Drive integration
- **test_phase6.py**: Test suite

---

## See Also

- [PHASE7_COMPLETION.md](PHASE7_COMPLETION.md) - Complete documentation
- [PHASE7_SUMMARY.md](PHASE7_SUMMARY.md) - Executive summary
- [examples_phase7.py](examples_phase7.py) - Usage examples
- [FINAL_NOTEBOOK_ACTION_PLAN.md](FINAL_NOTEBOOK_ACTION_PLAN.md) - Overall plan

---

**Last Updated:** 2025-11-22  
**Status:** ✅ Complete and tested
