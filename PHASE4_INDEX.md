# Phase 4: Metadata Extraction - Quick Reference Index

## Module: metadata_extractor.py

### Quick Import
```python
from metadata_extractor import (
    # ArXiv
    detect_arxiv_id,
    query_arxiv_api,
    extract_arxiv_metadata,
    
    # DOI/CrossRef
    detect_doi,
    query_crossref_api,
    extract_doi_metadata,
    
    # PDF Metadata
    extract_pdf_properties,
    extract_pdf_metadata,
    
    # Abstract
    extract_abstract_from_text,
    extract_abstract_from_sections,
    
    # Validation
    validate_metadata,
    normalize_metadata,
    normalize_author_names,
    normalize_title,
    normalize_venue,
    parse_date_flexible,
    
    # Worker
    metadata_extraction_worker,
)
```

---

## Core Functions Reference

### ArXiv Metadata (Step 4.1)

#### `detect_arxiv_id(filename: str, text: str = "") -> Optional[str]`
Detect arXiv ID from filename or text.

**Usage:**
```python
arxiv_id = detect_arxiv_id("arxiv-2301.12345.pdf")
# Returns: "2301.12345"
```

**Patterns Detected:**
- `2301.12345`
- `2301.12345v1`
- `arxiv:2301.12345`
- `arxiv-2301.12345`

---

#### `query_arxiv_api(arxiv_id: str) -> Optional[Dict[str, Any]]`
Query arXiv API for metadata.

**Usage:**
```python
metadata = query_arxiv_api("2301.12345")
if metadata:
    print(metadata['title'])
    print(metadata['authors'])
    print(metadata['abstract'])
```

**Returns:**
```python
{
    'title': str,
    'authors': List[str],
    'abstract': str,
    'published': str,  # ISO format date
    'updated': str,
    'categories': List[str],
    'arxiv_version': str,
    'arxiv_id': str
}
```

**Features:**
- Rate limiting (3s delay)
- Retry logic (3 attempts)
- XML parsing
- Error handling

---

#### `extract_arxiv_metadata(paper: PaperRecord, text: str = "") -> PaperRecord`
Extract and populate arXiv metadata.

**Usage:**
```python
paper = extract_arxiv_metadata(paper, full_text)
print(f"arXiv ID: {paper.arxiv_id}")
print(f"Is Preprint: {paper.is_preprint}")
```

**Updates:**
- `paper.arxiv_id`
- `paper.source = "arxiv"`
- `paper.is_preprint = True`
- `paper.title`
- `paper.authors`
- `paper.abstract_text`
- `paper.publish_date`
- `paper.year`

---

### DOI/CrossRef Metadata (Step 4.2)

#### `detect_doi(text: str) -> Optional[str]`
Detect DOI in text content.

**Usage:**
```python
doi = detect_doi("DOI: 10.1234/example.2023")
# Returns: "10.1234/example.2023"
```

**Pattern:** `10.NNNN/...`

---

#### `query_crossref_api(doi: str) -> Optional[Dict[str, Any]]`
Query CrossRef API for metadata.

**Usage:**
```python
metadata = query_crossref_api("10.1234/example.2023")
if metadata:
    print(metadata['title'])
    print(metadata['venue'])
    print(metadata['authors'])
```

**Returns:**
```python
{
    'title': str,
    'authors': List[str],
    'venue': str,
    'published_date': str,
    'type': str,
    'doi': str
}
```

**Features:**
- Rate limiting (1s delay)
- Retry logic (3 attempts)
- JSON parsing
- Error handling

---

#### `extract_doi_metadata(paper: PaperRecord, text: str = "") -> PaperRecord`
Extract and populate DOI metadata.

**Usage:**
```python
paper = extract_doi_metadata(paper, full_text)
print(f"DOI: {paper.doi}")
print(f"Venue: {paper.venue}")
```

**Updates:**
- `paper.doi`
- `paper.source = "doi"` (if no arXiv)
- `paper.is_preprint = False` (if no arXiv)
- `paper.title`
- `paper.authors`
- `paper.venue`
- `paper.publish_date`
- `paper.year`

---

### PDF Metadata (Step 4.3)

#### `extract_pdf_properties(file_path: str) -> Dict[str, Any]`
Extract PDF document properties.

**Usage:**
```python
props = extract_pdf_properties("/path/to/paper.pdf")
print(f"Title: {props['title']}")
print(f"Author: {props['author']}")
print(f"Created: {props['creation_date']}")
```

**Returns:**
```python
{
    'title': str,
    'author': str,
    'subject': str,
    'keywords': str,
    'creator': str,
    'producer': str,
    'creation_date': str,
    'mod_date': str,
    'format': str,
    'encryption': bool
}
```

---

#### `extract_pdf_metadata(paper: PaperRecord) -> PaperRecord`
Extract and populate PDF metadata.

**Usage:**
```python
paper = extract_pdf_metadata(paper)
# Uses PDF properties as fallback
```

**Updates** (only if not already set):
- `paper.title`
- `paper.authors`
- `paper.publish_date`
- `paper.year`

---

### Abstract Extraction (Step 4.4)

#### `extract_abstract_from_sections(sections: List[Dict], full_text: str) -> Optional[str]`
Extract abstract using section detection.

**Usage:**
```python
from pdf_parser import detect_sections

sections = detect_sections(full_text, pages)
abstract = extract_abstract_from_sections(sections, full_text)
```

**Requires:** Section data from `pdf_parser.detect_sections()`

---

#### `extract_abstract_from_text(text: str) -> Optional[str]`
Extract abstract using pattern matching.

**Usage:**
```python
abstract = extract_abstract_from_text(full_text)
if abstract:
    print(f"Abstract: {abstract[:100]}...")
```

**Finds:** Text after "Abstract" heading until next section

**Validates:**
- Minimum length: 50 chars
- Maximum length: 3000 chars

---

### Validation and Normalization (Step 4.5)

#### `parse_date_flexible(date_str: str) -> Optional[date]`
Flexible date parsing.

**Usage:**
```python
d = parse_date_flexible("2023-01-15")
d = parse_date_flexible("January 15, 2023")
d = parse_date_flexible("2023")
```

**Supports:**
- ISO format
- Natural language
- Partial dates (year only)
- International formats

---

#### `normalize_author_names(authors: List[str]) -> List[str]`
Normalize author names.

**Usage:**
```python
authors = normalize_author_names(["  John Doe  ", "", "Jane Smith"])
# Returns: ["John Doe", "Jane Smith"]
```

**Performs:**
- Whitespace cleanup
- Empty entry removal
- Artifact filtering

---

#### `normalize_title(title: str) -> str`
Normalize title string.

**Usage:**
```python
title = normalize_title("  Example\n Title.  ")
# Returns: "Example Title"
```

**Performs:**
- Whitespace normalization
- Newline removal
- Trailing period removal
- Artifact removal

---

#### `normalize_venue(venue: str) -> str`
Normalize venue name.

**Usage:**
```python
venue = normalize_venue("  Nature  Reviews  ")
# Returns: "Nature Reviews"
```

---

#### `validate_metadata(paper: PaperRecord) -> Dict[str, Any]`
Validate metadata quality.

**Usage:**
```python
validation = validate_metadata(paper)
print(f"Quality: {validation['quality_score']}")
print(f"Warnings: {validation['warnings']}")
```

**Returns:**
```python
{
    'quality_score': float,  # 0-1
    'has_title': bool,
    'has_authors': bool,
    'has_date': bool,
    'has_abstract': bool,
    'has_source': bool,
    'warnings': List[str]
}
```

**Quality Score Components:**
- Title: 0.25
- Authors: 0.25
- Date: 0.20
- Abstract: 0.20
- Source ID: 0.10

---

#### `normalize_metadata(paper: PaperRecord) -> PaperRecord`
Apply all normalizations.

**Usage:**
```python
paper = normalize_metadata(paper)
```

**Normalizes:**
- Title
- Authors
- Venue
- Ensures year matches date

---

### LangGraph Worker

#### `metadata_extraction_worker(paper_id: str, state: GraphState) -> GraphState`
Complete metadata extraction workflow.

**Usage:**
```python
state = metadata_extraction_worker(paper_id, state)
```

**Workflow:**
1. Retrieve paper from state
2. Extract text from chunks
3. Extract arXiv metadata
4. Extract DOI metadata
5. Extract PDF metadata
6. Extract abstract
7. Normalize metadata
8. Validate quality
9. Update state

**Updates State:**
- `state['papers'][paper_id]` with metadata
- Quality scores in `raw_text_stats`
- Timestamps

---

## Complete Pipeline Example

```python
from rag_models import PaperRecord, StateManager, create_default_config
from metadata_extractor import metadata_extraction_worker

# Setup
config = create_default_config()
state = StateManager.create_initial_state(config)

# Create paper
paper = PaperRecord(
    id="paper001",
    file_path="/path/to/arxiv-2301.12345.pdf",
    filename="arxiv-2301.12345.pdf",
    processing_status="parsed"
)

# Add to state
state = StateManager.add_paper(state, paper)

# Run metadata extraction
state = metadata_extraction_worker(paper.id, state)

# Check results
updated_paper = state['papers'][paper.id]
print(f"Title: {updated_paper.title}")
print(f"Authors: {updated_paper.authors}")
print(f"arXiv ID: {updated_paper.arxiv_id}")
print(f"Quality: {updated_paper.raw_text_stats.get('metadata_quality')}")
```

---

## Metadata Priority

The system uses this priority for metadata sources:

1. **arXiv API** (highest priority)
   - Used for preprints
   - Most complete metadata
   - Sets `is_preprint = True`

2. **CrossRef API** (via DOI)
   - Used for published papers
   - Good for venue information
   - Sets `is_preprint = False`

3. **PDF Properties** (fallback)
   - Used when APIs unavailable
   - Variable quality
   - Always extracted as backup

---

## Error Handling Patterns

### API Errors
```python
try:
    metadata = query_arxiv_api(arxiv_id)
except ImportError:
    # requests library not available
    pass
except Exception as e:
    # Network error, parse error, etc.
    logger.error(f"API error: {e}")
```

### File Errors
```python
try:
    props = extract_pdf_properties(file_path)
except FileNotFoundError:
    # PDF doesn't exist
    pass
except ImportError:
    # PyMuPDF not available
    pass
```

---

## Rate Limiting

### arXiv
- **Delay**: 3 seconds between requests
- **Retries**: Up to 3 attempts
- **Backoff**: Exponential (2^retry seconds)

### CrossRef
- **Delay**: 1 second between requests
- **Retries**: Up to 3 attempts
- **Backoff**: Exponential (2^retry seconds)

---

## Testing

### Run Tests
```bash
python test_phase4.py
```

### Run Examples
```bash
python examples_phase4.py
```

---

## Common Use Cases

### Case 1: ArXiv Paper
```python
# Paper with arXiv ID in filename
paper = PaperRecord(id="p1", filename="arxiv-2301.12345.pdf", ...)
paper = extract_arxiv_metadata(paper)
# Gets: title, authors, abstract, date from arXiv API
```

### Case 2: Published Paper with DOI
```python
# Paper with DOI in text
paper = extract_doi_metadata(paper, full_text)
# Gets: title, authors, venue, date from CrossRef
```

### Case 3: PDF-Only Paper
```python
# Paper with no arXiv/DOI
paper = extract_pdf_metadata(paper)
# Gets: title, authors from PDF properties (if available)
```

### Case 4: Complete Pipeline
```python
# Try all sources
paper = extract_arxiv_metadata(paper, text)
paper = extract_doi_metadata(paper, text)
paper = extract_pdf_metadata(paper)
paper = normalize_metadata(paper)
validation = validate_metadata(paper)
```

---

## See Also

- **PHASE4_COMPLETION.md** - Detailed implementation documentation
- **PHASE4_SUMMARY.md** - High-level summary
- **test_phase4.py** - Test suite
- **examples_phase4.py** - Usage examples
- **metadata_extractor.py** - Source code
