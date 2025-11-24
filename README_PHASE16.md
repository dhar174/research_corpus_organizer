# Phase 16: Utility Functions and Tools - Documentation

**Version:** 1.0  
**Date:** 2025-11-24  
**Status:** Complete

## Overview

This document describes the utility functions implemented in Phase 16 of the RAG PDF Research Corpus System. These utilities provide comprehensive tools for searching, analyzing, managing, and maintaining your research corpus.

## Module: corpus_utilities.py

The `corpus_utilities.py` module contains all Phase 16 functionality organized into five main categories:

### 1. Paper Search Functions (Step 16.1)

Search and filter papers using various criteria.

#### `search_papers(state, query=None, author=None, year_range=None, topic_id=None, status=None, has_doi=None, has_arxiv=None)`

Generic search function with multiple filters.

```python
from corpus_utilities import search_papers

# Search for papers about transformers from 2017-2020
results = search_papers(
    state,
    query="transformer",
    year_range=(2017, 2020),
    has_arxiv=True
)
```

#### `search_by_title(state, keyword, case_sensitive=False, exact_match=False)`

Search papers by title keyword.

```python
from corpus_utilities import search_by_title

# Find papers with "BERT" in title
results = search_by_title(state, "BERT")

# Exact title match
results = search_by_title(state, "Attention Is All You Need", exact_match=True)
```

#### `search_by_author(state, author_name, case_sensitive=False, exact_match=False)`

Search papers by author name.

```python
from corpus_utilities import search_by_author

# Find papers by Vaswani
results = search_by_author(state, "Vaswani")

# Case-sensitive search
results = search_by_author(state, "Devlin", case_sensitive=True)
```

#### `search_by_date_range(state, start_date=None, end_date=None, start_year=None, end_year=None)`

Search papers by publication date or year range.

```python
from corpus_utilities import search_by_date_range
from datetime import date

# Find papers from 2017-2020
results = search_by_date_range(state, start_year=2017, end_year=2020)

# Find papers published in a specific date range
results = search_by_date_range(
    state,
    start_date=date(2020, 1, 1),
    end_date=date(2020, 12, 31)
)
```

#### `search_by_topic(state, topic_id, tier=1, include_children=False)`

Search papers by topic classification.

```python
from corpus_utilities import search_by_topic

# Find all papers in "Natural Language Processing" topic
results = search_by_topic(state, "T1_NLP", tier=1)

# Include papers in child topics
results = search_by_topic(state, "T1_NLP", tier=1, include_children=True)
```

#### `filter_by_status(state, status)`

Filter papers by processing status.

```python
from corpus_utilities import filter_by_status

# Get all classified papers
classified = filter_by_status(state, "classified")

# Get failed papers for reprocessing
failed = filter_by_status(state, "failed")
```

#### `advanced_search(state, filters)`

Advanced search with complex filter combinations.

```python
from corpus_utilities import advanced_search

# Complex multi-filter search
results = advanced_search(state, {
    'title': 'learning',
    'authors': ['Vaswani', 'Devlin'],
    'year_min': 2017,
    'year_max': 2020,
    'topics': ['T1_NLP', 'T1_LLM'],
    'has_summary': True,
    'min_pages': 10
})
```

---

### 2. Corpus Statistics (Step 16.2)

Generate statistics and visualizations for your corpus.

#### `count_papers_by_year(state)`

Count papers by publication year.

```python
from corpus_utilities import count_papers_by_year

year_counts = count_papers_by_year(state)
# Returns: {2017: 5, 2018: 12, 2019: 8, ...}
```

#### `count_papers_by_source(state)`

Count papers by source type (arXiv, journal, etc.).

```python
from corpus_utilities import count_papers_by_source

source_counts = count_papers_by_source(state)
# Returns: {'arXiv': 45, 'Journal/Conference': 23, 'Unknown': 2}
```

#### `get_most_common_authors(state, top_n=10)`

Get the most prolific authors in the corpus.

```python
from corpus_utilities import get_most_common_authors

top_authors = get_most_common_authors(state, top_n=10)
# Returns: [('Vaswani', 3), ('Devlin', 2), ...]
```

#### `get_most_common_venues(state, top_n=10)`

Get the most common publication venues.

```python
from corpus_utilities import get_most_common_venues

top_venues = get_most_common_venues(state, top_n=10)
# Returns: [('NeurIPS', 15), ('ICML', 12), ...]
```

#### `get_topic_distribution(state, tier=1)`

Get distribution of papers across topics.

```python
from corpus_utilities import get_topic_distribution

# Tier 1 topic distribution
topic_dist = get_topic_distribution(state, tier=1)
# Returns: {'T1_NLP': 25, 'T1_CV': 18, ...}
```

#### `generate_statistics_charts(state, output_dir, chart_types=None)`

Generate various statistics charts.

```python
from corpus_utilities import generate_statistics_charts

# Generate all charts
chart_paths = generate_statistics_charts(state, './charts')

# Generate specific charts
chart_paths = generate_statistics_charts(
    state,
    './charts',
    chart_types=['year', 'source', 'topics']
)
```

#### `generate_corpus_report(state, output_path, include_charts=True)`

Generate comprehensive corpus statistics report.

```python
from corpus_utilities import generate_corpus_report

# Generate full report with charts
report_path = generate_corpus_report(
    state,
    './reports/corpus_report.md',
    include_charts=True
)
```

---

### 3. Export Utilities (Step 16.3)

Export papers and metadata in various formats.

#### `export_paper_subset(state, paper_ids, output_path, format='json')`

Export a subset of papers.

```python
from corpus_utilities import export_paper_subset

# Export specific papers to JSON
export_paper_subset(state, ['p1', 'p2', 'p3'], './export/subset.json')

# Export to CSV
export_paper_subset(state, ['p1', 'p2'], './export/subset.csv', format='csv')
```

#### `export_by_topic(state, topic_id, output_path, tier=1, format='json')`

Export all papers in a specific topic.

```python
from corpus_utilities import export_by_topic

# Export all NLP papers
export_by_topic(state, 'T1_NLP', './export/nlp_papers.json', tier=1)
```

#### `export_by_date_range(state, start_year, end_year, output_path, format='json')`

Export papers from a date range.

```python
from corpus_utilities import export_by_date_range

# Export papers from 2020
export_by_date_range(state, 2020, 2020, './export/papers_2020.json')
```

#### `generate_bibtex_entries(state, paper_ids=None, output_path=None)`

Generate BibTeX entries for papers.

```python
from corpus_utilities import generate_bibtex_entries

# Generate BibTeX for all papers
bibtex = generate_bibtex_entries(state, output_path='./references.bib')

# Generate for specific papers
bibtex = generate_bibtex_entries(state, ['p1', 'p2', 'p3'])
```

#### `create_reading_list(state, paper_ids, output_path, title="Reading List", format='markdown')`

Create a formatted reading list.

```python
from corpus_utilities import create_reading_list

# Create markdown reading list
create_reading_list(
    state,
    ['p1', 'p2', 'p3'],
    './reading_lists/top_papers.md',
    title='Top NLP Papers 2020',
    format='markdown'
)

# Create HTML reading list
create_reading_list(
    state,
    paper_ids,
    './reading_lists/papers.html',
    format='html'
)
```

#### `export_to_markdown(state, paper_ids=None, output_path='corpus_export.md')`

Export papers to a comprehensive markdown document.

```python
from corpus_utilities import export_to_markdown

# Export all papers
export_to_markdown(state, output_path='./export/full_corpus.md')

# Export specific papers
export_to_markdown(state, ['p1', 'p2'], './export/selected_papers.md')
```

---

### 4. Data Update Functions (Step 16.4)

Update and maintain the corpus.

#### `add_new_papers(state, new_papers, merge_strategy='skip')`

Add new papers to the corpus.

```python
from corpus_utilities import add_new_papers
from rag_models import PaperRecord

new_paper = PaperRecord(
    id='p_new',
    title='New Research Paper',
    authors=['Smith', 'Jones'],
    year=2023
)

# Add with skip strategy (skip duplicates)
state = add_new_papers(state, [new_paper], merge_strategy='skip')

# Add with replace strategy (replace existing)
state = add_new_papers(state, [new_paper], merge_strategy='replace')

# Add with update strategy (merge fields)
state = add_new_papers(state, [new_paper], merge_strategy='update')
```

#### `reprocess_failed_papers(state, reprocess_fn, max_papers=None)`

Reprocess papers that failed during initial processing.

```python
from corpus_utilities import reprocess_failed_papers

# Reprocess all failed papers
state = reprocess_failed_papers(state, my_reprocess_function)

# Reprocess up to 10 failed papers
state = reprocess_failed_papers(state, my_reprocess_function, max_papers=10)
```

#### `update_paper_metadata(state, paper_id, metadata_updates)`

Update metadata for a specific paper.

```python
from corpus_utilities import update_paper_metadata

# Update paper metadata
state = update_paper_metadata(state, 'p1', {
    'venue': 'NeurIPS 2017 (Updated)',
    'page_count': 11,
    'doi': '10.1234/example'
})
```

#### `reclassify_papers(state, paper_ids=None, classifier_fn=None)`

Reclassify papers with a new taxonomy.

```python
from corpus_utilities import reclassify_papers

# Reclassify all papers
state = reclassify_papers(state, classifier_fn=my_classifier)

# Reclassify specific papers
state = reclassify_papers(state, ['p1', 'p2'], my_classifier)
```

#### `rebuild_faiss_index(state, openai_client=None, force=False)`

Rebuild the FAISS index from chunks.

```python
from corpus_utilities import rebuild_faiss_index
from openai import OpenAI

client = OpenAI(api_key='your-key')
state = rebuild_faiss_index(state, client, force=True)
```

#### `merge_corpus_states(state1, state2, merge_strategy='skip')`

Merge two corpus states.

```python
from corpus_utilities import merge_corpus_states

# Merge two corpora
merged_state = merge_corpus_states(state1, state2, merge_strategy='skip')
```

---

### 5. Cleanup Functions (Step 16.5)

Clean up and optimize the corpus.

#### `remove_duplicate_papers(state, dedupe_by='id')`

Remove duplicate papers.

```python
from corpus_utilities import remove_duplicate_papers

# Remove duplicates by ID
state, removed = remove_duplicate_papers(state, dedupe_by='id')

# Remove duplicates by title
state, removed = remove_duplicate_papers(state, dedupe_by='title')

# Remove duplicates by DOI
state, removed = remove_duplicate_papers(state, dedupe_by='doi')

print(f"Removed {len(removed)} duplicates")
```

#### `clean_orphaned_chunks(state)`

Remove chunks for papers that no longer exist.

```python
from corpus_utilities import clean_orphaned_chunks

state, chunks_removed = clean_orphaned_chunks(state)
print(f"Removed {chunks_removed} orphaned chunks")
```

#### `verify_data_integrity(state)`

Verify data integrity and report issues.

```python
from corpus_utilities import verify_data_integrity

report = verify_data_integrity(state)
print(f"Total issues: {report['total_issues']}")
print(f"Integrity score: {report['integrity_score']:.2%}")

# Check specific issues
if report['issues']['missing_titles']:
    print(f"Papers missing titles: {len(report['issues']['missing_titles'])}")
```

#### `optimize_storage(state, remove_embeddings=False, compress_summaries=False)`

Optimize storage by removing redundant data.

```python
from corpus_utilities import optimize_storage

# Optimize with defaults
state, stats = optimize_storage(state)

# Remove embeddings (keep in FAISS only)
state, stats = optimize_storage(state, remove_embeddings=True)

# Compress long summaries
state, stats = optimize_storage(state, compress_summaries=True)

print(f"Removed {stats['embeddings_removed']} embeddings")
print(f"Compressed {stats['summaries_compressed']} summaries")
```

#### `archive_old_versions(state_path, archive_dir, max_versions=5)`

Archive old versions of state files.

```python
from corpus_utilities import archive_old_versions

# Archive current state
archives = archive_old_versions(
    './state/corpus_state.json',
    './state/archives',
    max_versions=10
)

print(f"Archived to: {archives[-1]}")
```

#### `compact_corpus(state, remove_failed=True, deduplicate=True, clean_orphans=True, optimize=True)`

Comprehensive corpus cleanup and optimization.

```python
from corpus_utilities import compact_corpus

# Full compaction
state, stats = compact_corpus(state)

print(f"Papers before: {stats['original_papers']}")
print(f"Papers after: {stats['final_papers']}")
print(f"Removed: {stats['papers_saved']} papers, {stats['chunks_saved']} chunks")
```

---

## Usage Examples

See `examples_phase16.py` for comprehensive usage examples covering:

1. **Paper Search Functions** - Various search and filter operations
2. **Corpus Statistics** - Generating statistics and reports
3. **Export Utilities** - Exporting data in multiple formats
4. **Data Update Functions** - Adding and updating papers
5. **Cleanup Functions** - Maintaining corpus integrity

Run the examples:

```bash
python examples_phase16.py
```

---

## Testing

A comprehensive test suite is provided in `test_phase16.py`:

```bash
python test_phase16.py
```

The test suite covers:
- All search functions with various filter combinations
- Statistics generation and validation
- Export utilities in all supported formats
- Data update operations
- Cleanup and integrity verification

---

## Integration with Phase 15

These utilities complement the Phase 15 RAG query interface:

```python
from rag_query_interface import rag_query
from corpus_utilities import search_by_topic, generate_bibtex_entries

# 1. Find papers on a topic
nlp_papers = search_by_topic(state, 'T1_NLP', tier=1)

# 2. Query those papers specifically
result = rag_query("What are the key innovations in NLP?", state)

# 3. Generate BibTeX for cited papers
paper_ids = [p['paper_id'] for p in result['used_papers']]
bibtex = generate_bibtex_entries(state, paper_ids)
```

---

## Best Practices

### Search Efficiency

1. Use specific filters to narrow results
2. Combine multiple search functions for complex queries
3. Use `advanced_search` for multi-criteria searches

### Export Management

1. Export subsets rather than full corpus for large datasets
2. Use appropriate formats (JSON for structured data, markdown for reading)
3. Generate BibTeX only for papers you actually cite

### Maintenance Schedule

Recommended maintenance tasks:

```python
# Weekly: Verify integrity
report = verify_data_integrity(state)

# Monthly: Remove duplicates and orphans
state, _ = remove_duplicate_papers(state)
state, _ = clean_orphaned_chunks(state)

# Quarterly: Full compaction
state, stats = compact_corpus(state)

# Before major changes: Archive
archive_old_versions('./state/corpus_state.json', './archives')
```

---

## Dependencies

Optional dependencies for full functionality:

- **pandas** - CSV export support
- **matplotlib, seaborn** - Chart generation
- **faiss-cpu** - FAISS index operations
- **openai** - Embedding generation for index rebuilding

Install all optional dependencies:

```bash
pip install pandas matplotlib seaborn faiss-cpu openai
```

---

## API Reference

All functions return either:
- Updated `GraphState` for modification functions
- Results list for search functions
- Statistics dictionary for analysis functions
- File paths for export functions

See docstrings in `corpus_utilities.py` for detailed parameter descriptions and return types.

---

**Version:** 1.0  
**Last Updated:** 2025-11-24  
**Module:** corpus_utilities.py
