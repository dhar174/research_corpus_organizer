# Phase 3: PDF Parsing and Chunking - Summary

**Date:** 2025-11-22  
**Version:** 1.0  
**Status:** ✅ COMPLETE

---

## Quick Reference

### Main Module: `pdf_parser.py`

PDF parsing, OCR fallback, section detection, and intelligent chunking for academic papers.

---

## Core Functions

### 1. PDF Parsing (Step 3.1)

```python
from pdf_parser import parse_pdf, parse_and_chunk_worker

# Parse a PDF file
result = parse_pdf("/path/to/paper.pdf", config)
# Returns: {success, page_count, pages, full_text, stats}

# Use in LangGraph workflow
state = parse_and_chunk_worker(paper_id, state)
# Updates state with chunks and paper statistics
```

**Key Features:**
- PyMuPDF integration for robust parsing
- Page-by-page text extraction
- Comprehensive text statistics
- Quality score calculation
- Respects max_pages_per_paper limit

---

### 2. OCR Fallback (Step 3.2)

```python
from pdf_parser import needs_ocr, apply_ocr

# Check if OCR is needed
if needs_ocr(parse_stats):
    # Apply OCR to scanned PDF
    ocr_result = apply_ocr("/path/to/scanned.pdf", config)
```

**Quality Thresholds:**
- Parse quality score < 0.5 → OCR needed
- Chars per page < 500 → OCR needed
- Customizable threshold

**Dependencies:**
- pytesseract
- Pillow (PIL)
- Tesseract OCR engine

---

### 3. Section Detection (Step 3.3)

```python
from pdf_parser import detect_sections, SectionDetector

# Detect sections in paper
sections = detect_sections(full_text, pages)
# Returns: [{label, start_char, end_char, page_start, page_end}, ...]

# Check if a line is a section heading
section_label = SectionDetector.detect_section("Introduction")
# Returns: "introduction" or None
```

**Detected Sections:**
- abstract
- introduction
- methods
- results
- discussion
- conclusion
- references
- other (fallback)

---

### 4. Text Chunking (Step 3.4)

```python
from pdf_parser import chunk_text, create_chunks_from_pages

# Create chunks from pages and sections
chunks = create_chunks_from_pages(paper_id, pages, sections, config)
# Returns: List[PaperChunk]

# Manual chunking
chunks = chunk_text(
    text,
    chunk_size=1500,
    overlap=200,
    section_label="introduction",
    page_start=1,
    page_end=3
)
```

**Chunking Features:**
- Sentence-aware (no mid-sentence breaks)
- Configurable size (default ~1500 chars)
- Configurable overlap (default ~200 chars)
- Section-aware (chunks don't cross sections)
- Respects max_chunks_per_paper limit

---

### 5. Validation (Step 3.5)

```python
from pdf_parser import validate_parsing, validate_chunks

# Validate parsing results
validation = validate_parsing(paper, parse_result)
# Returns: {valid, issues, warnings}

# Validate created chunks
chunk_validation = validate_chunks(chunks, page_count)
# Returns: {valid, issues, warnings, stats}
```

**Validation Checks:**
- Parse success and quality
- Page count and text extraction
- Chunk structure and content
- Page range validity
- Section label correctness

---

## Configuration

### RunConfig Parameters

```python
from rag_models import create_default_config

config = create_default_config(
    # Parsing limits
    max_pages_per_paper=None,      # None = all pages
    max_chunks_per_paper=100,       # Limit chunks per paper
    
    # OCR settings
    enable_ocr_fallback=False,      # Enable OCR for scanned PDFs
    
    # Chunking parameters
    chunk_size_chars=1500,          # Target chunk size
    chunk_overlap_chars=200,        # Overlap between chunks
)
```

---

## Typical Workflow

### End-to-End Processing

```python
from pdf_parser import parse_and_chunk_worker
from rag_models import StateManager, create_default_config

# 1. Create config
config = create_default_config()

# 2. Create initial state
state = StateManager.create_initial_state(config)

# 3. Add paper to state
state = StateManager.add_paper(state, paper)

# 4. Run worker
state = parse_and_chunk_worker(paper.id, state)

# 5. Check results
if paper.id in state['papers_completed']:
    chunks = state['chunks'][paper.id]
    print(f"Created {len(chunks)} chunks")
```

---

## Data Structures

### PaperChunk

```python
chunk = PaperChunk(
    paper_id="abc123...",
    chunk_id="abc123..._chunk_0000",
    section_label="introduction",
    page_start=1,
    page_end=2,
    text="Sample chunk text...",
    char_count=1234,
    token_count_estimate=308,
    embedding_id=None,           # Set in Phase 5
    embedding_model=None,        # Set in Phase 5
)
```

### Parse Result

```python
result = {
    'success': True,
    'page_count': 10,
    'pages': [
        {'page_num': 1, 'text': '...', 'char_count': 1234},
        # ...
    ],
    'full_text': "...",
    'stats': {
        'pages': 10,
        'chars_total': 12340,
        'chars_per_page': 1234.0,
        'alnum_ratio': 0.85,
        'parse_quality_score': 0.9
    }
}
```

### Section Dictionary

```python
section = {
    'label': 'introduction',
    'start_char': 0,
    'end_char': 1500,
    'page_start': 1,
    'page_end': 2
}
```

---

## Error Handling

### Common Errors

```python
# File not found
result = parse_pdf("/nonexistent.pdf", config)
# Returns: {success: False, error: "File not found: ..."}

# Missing dependencies
result = apply_ocr(pdf_path, config)
# Returns: {success: False, error: "OCR dependencies not installed..."}

# Parse failure
state = parse_and_chunk_worker(paper_id, state)
# Marks paper as failed in state
# Updates paper.processing_status = "failed"
# Sets paper.error_reason
```

### Logging

```python
import logging
logging.basicConfig(level=logging.INFO)

# INFO: Normal operations
# WARNING: Quality issues, chunk limits
# ERROR: Parse failures, OCR errors
```

---

## Performance

### Expected Performance

| PDF Size | Parse Time | OCR Time (if needed) |
|----------|------------|----------------------|
| < 10 pages | < 1 sec | 5-20 sec |
| 10-50 pages | 1-5 sec | 20-120 sec |
| 50-200 pages | 5-20 sec | 2-10 min |

### Optimization Tips

1. **Limit pages:** Set `max_pages_per_paper` for large PDFs
2. **Limit chunks:** Set `max_chunks_per_paper` to prevent memory issues
3. **OCR sparingly:** Only enable if needed (slow)
4. **Batch processing:** Process multiple papers in parallel (future enhancement)

---

## Testing

### Run Tests

```bash
python test_phase3.py
```

### Test Coverage

- ✅ Section detection
- ✅ Sentence splitting
- ✅ Text chunking
- ✅ Chunk creation
- ✅ OCR quality check
- ✅ Parsing validation
- ✅ Chunk validation
- ✅ Worker integration

---

## Integration with Other Phases

### Phase 1: Models
- Uses `RunConfig` for configuration
- Creates `PaperChunk` objects
- Updates `PaperRecord` statistics
- Uses `StatisticsTracker` and `IDGenerator`

### Phase 2: Drive Integration
- Receives file paths from `discover_pdfs()`
- Processes PDFs found in Google Drive

### Phase 4: Metadata (Future)
- Parse results can include abstract detection
- Section labels help identify abstract text

### Phase 5: Embeddings (Future)
- Chunks are ready for embedding generation
- `embedding_id` field prepared for FAISS index

---

## Examples

See `examples_phase3.py` for:
1. Basic PDF parsing
2. Section detection
3. Text chunking
4. Validation
5. LangGraph worker integration
6. OCR quality checks

---

## Dependencies

### Required
- `pymupdf` (fitz) - PDF parsing
- `rag_models` - Schema definitions

### Optional
- `pytesseract` - OCR (Step 3.2)
- `Pillow` - Image processing for OCR
- `tqdm` - Progress bars (recommended)

### Install

```bash
# Basic (required)
pip install pymupdf

# With OCR support (optional)
pip install pymupdf pytesseract Pillow

# Install Tesseract OCR engine (system package)
# Ubuntu/Debian: apt-get install tesseract-ocr
# macOS: brew install tesseract
# Windows: Download from GitHub
```

---

## Statistics

- **Module size:** ~900 lines
- **Test suite:** ~630 lines
- **Functions:** 14 public functions
- **Test functions:** 9 test functions
- **Classes:** 1 (SectionDetector)
- **Dependencies:** 3 required, 2 optional

---

## Next Steps

Phase 3 is complete. Ready to proceed with:

1. **Phase 4:** Metadata Extraction
   - arXiv API integration
   - CrossRef/DOI lookup
   - PDF metadata extraction
   - Abstract extraction from parsed text

2. **Phase 5:** Embeddings & FAISS
   - Generate embeddings for all chunks
   - Build FAISS vector index
   - Persist index to disk

---

## Quick Start

```python
# 1. Import
from pdf_parser import parse_and_chunk_worker
from rag_models import StateManager, create_default_config

# 2. Configure
config = create_default_config(
    chunk_size_chars=1500,
    enable_ocr_fallback=True
)

# 3. Create state
state = StateManager.create_initial_state(config)

# 4. Add papers (from Phase 2)
from drive_utils import discover_pdfs
papers = discover_pdfs(config.drive_folder_path, config)
for paper in papers.values():
    state = StateManager.add_paper(state, paper)

# 5. Process papers
for paper_id in list(state['papers_pending']):
    state = parse_and_chunk_worker(paper_id, state)

# 6. Check results
stats = StateManager.get_stats(state)
print(f"Processed {stats['completed']} papers")
print(f"Created {stats['total_chunks']} chunks")
```

---

**For complete documentation, see:** `PHASE3_COMPLETION.md`

**For usage examples, see:** `examples_phase3.py`

**For testing, see:** `test_phase3.py`
