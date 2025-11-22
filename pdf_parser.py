"""
RAG PDF Research Corpus System - PDF Parsing and Chunking (Phase 3)

This module provides utilities for:
- PDF text extraction with PyMuPDF (Step 3.1)
- OCR fallback for scanned PDFs (Step 3.2)
- Section detection and labeling (Step 3.3)
- Intelligent text chunking (Step 3.4)
- Parsing validation (Step 3.5)

Version: 1.0
Date: 2025-11-22
"""

import os
import re
from typing import Dict, List, Tuple, Optional, Any
import logging

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

from rag_models import (
    PaperRecord,
    PaperChunk,
    RunConfig,
    GraphState,
    IDGenerator,
    StatisticsTracker,
    StateManager
)

logger = logging.getLogger(__name__)

# Export list for clean imports
__all__ = [
    # Core parsing (Step 3.1)
    'parse_pdf',
    'parse_and_chunk_worker',
    
    # OCR fallback (Step 3.2)
    'apply_ocr',
    'needs_ocr',
    
    # Section detection (Step 3.3)
    'detect_sections',
    'SectionDetector',
    
    # Text chunking (Step 3.4)
    'chunk_text',
    'create_chunks_from_pages',
    
    # Validation (Step 3.5)
    'validate_parsing',
    'validate_chunks',
]


# =============================================================================
# Step 3.1: PDF Parser Worker
# =============================================================================

def parse_pdf(file_path: str, config: RunConfig) -> Dict[str, Any]:
    """
    Parse PDF file and extract text from all pages.
    
    Args:
        file_path: Absolute path to PDF file
        config: RunConfig with parsing settings
        
    Returns:
        Dictionary containing:
            - success: bool
            - page_count: int
            - pages: List[Dict] with text, page_num, char_count per page
            - full_text: str (concatenated text from all pages)
            - stats: Dict with text statistics
            - error: Optional[str]
            
    Example:
        >>> result = parse_pdf("/path/to/paper.pdf", config)
        >>> if result['success']:
        ...     print(f"Parsed {result['page_count']} pages")
    """
    if fitz is None:
        return {
            'success': False,
            'error': "PyMuPDF (fitz) is not installed. Install with: pip install pymupdf"
        }
    
    if not os.path.exists(file_path):
        return {
            'success': False,
            'error': f"File not found: {file_path}"
        }
    
    try:
        # Open PDF
        doc = fitz.open(file_path)
        page_count = len(doc)
        
        # Apply max_pages_per_paper limit if configured
        max_pages = config.max_pages_per_paper
        if max_pages and page_count > max_pages:
            logger.info(f"Limiting parsing to {max_pages} pages (total: {page_count})")
            page_count = max_pages
        
        # Extract text from each page
        pages = []
        for page_num in range(page_count):
            page = doc[page_num]
            text = page.get_text("text")
            
            pages.append({
                'page_num': page_num + 1,  # 1-indexed for human readability
                'text': text,
                'char_count': len(text)
            })
        
        # Concatenate all text
        full_text = "\n\n".join(p['text'] for p in pages)
        
        # Calculate statistics
        stats = StatisticsTracker.calculate_text_stats(full_text, page_count)
        
        doc.close()
        
        return {
            'success': True,
            'page_count': page_count,
            'pages': pages,
            'full_text': full_text,
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"Error parsing PDF {file_path}: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def parse_and_chunk_worker(paper_id: str, state: GraphState, config: Optional[RunConfig] = None) -> GraphState:
    """
    LangGraph worker node to parse PDF and create chunks.
    
    This function:
    1. Parses the PDF to extract text
    2. Detects sections
    3. Creates chunks with section awareness
    4. Updates the paper record with statistics
    5. Stores chunks in state
    
    Args:
        paper_id: ID of paper to process
        state: Current GraphState
        config: Optional RunConfig override (uses state['config'] if not provided)
        
    Returns:
        Updated GraphState
        
    Example:
        >>> state = parse_and_chunk_worker(paper_id, state)
        >>> print(f"Created {len(state['chunks'][paper_id])} chunks")
    """
    # Get config from state if not provided
    if config is None:
        config = state['config']
    
    # Get paper record
    if paper_id not in state['papers']:
        logger.error(f"Paper {paper_id} not found in state")
        return StateManager.mark_paper_failed(
            state, paper_id, "Paper not found in state"
        )
    
    paper = state['papers'][paper_id]
    
    try:
        # Step 1: Parse PDF
        logger.info(f"Parsing PDF: {paper.filename}")
        parse_result = parse_pdf(paper.file_path, config)
        
        if not parse_result['success']:
            return StateManager.mark_paper_failed(
                state, paper_id, f"Parse failed: {parse_result.get('error', 'Unknown error')}"
            )
        
        # Update paper with statistics
        paper.raw_text_stats = parse_result['stats']
        
        # Step 2: Check if OCR is needed
        if config.enable_ocr_fallback and needs_ocr(parse_result['stats']):
            logger.info(f"Low quality text detected, applying OCR to {paper.filename}")
            ocr_result = apply_ocr(paper.file_path, config)
            
            if ocr_result['success']:
                # Merge OCR text with extracted text
                parse_result['pages'] = ocr_result['pages']
                parse_result['full_text'] = ocr_result['full_text']
                parse_result['stats'] = ocr_result['stats']
                paper.raw_text_stats['ocr_applied'] = True
                paper.raw_text_stats.update(ocr_result['stats'])
        
        # Step 3: Detect sections
        sections = detect_sections(parse_result['full_text'], parse_result['pages'])
        
        # Step 4: Create chunks
        chunks = create_chunks_from_pages(
            paper_id,
            parse_result['pages'],
            sections,
            config
        )
        
        # Step 5: Validate chunks
        validation = validate_chunks(chunks, parse_result['page_count'])
        if not validation['valid']:
            logger.warning(f"Chunk validation issues for {paper.filename}: {validation['issues']}")
        
        # Update state
        state = StateManager.add_chunks(state, paper_id, chunks)
        
        # Update paper status
        paper.processing_status = "parsed"
        state = StateManager.update_paper(state, paper_id, {
            'processing_status': 'parsed',
            'raw_text_stats': paper.raw_text_stats
        })
        
        logger.info(f"Successfully parsed {paper.filename}: {len(chunks)} chunks created")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in parse_and_chunk_worker for {paper_id}: {e}")
        return StateManager.mark_paper_failed(
            state, paper_id, f"Worker error: {str(e)}"
        )


# =============================================================================
# Step 3.2: OCR Fallback
# =============================================================================

def needs_ocr(stats: Dict[str, Any], quality_threshold: float = 0.5) -> bool:
    """
    Determine if OCR is needed based on parse quality.
    
    Args:
        stats: Dictionary with parse statistics (from StatisticsTracker)
        quality_threshold: Minimum quality score (0-1) to avoid OCR
        
    Returns:
        True if OCR should be applied, False otherwise
        
    Example:
        >>> stats = {'parse_quality_score': 0.3, 'chars_per_page': 100}
        >>> if needs_ocr(stats):
        ...     print("Low quality, needs OCR")
    """
    quality_score = stats.get('parse_quality_score', 0)
    chars_per_page = stats.get('chars_per_page', 0)
    
    # OCR needed if quality is low OR very few chars per page
    if quality_score < quality_threshold:
        logger.info(f"Low quality score: {quality_score} < {quality_threshold}")
        return True
    
    if chars_per_page < 500:
        logger.info(f"Low character count: {chars_per_page} chars/page")
        return True
    
    return False


def apply_ocr(file_path: str, config: RunConfig) -> Dict[str, Any]:
    """
    Apply OCR to PDF pages using pytesseract.
    
    Args:
        file_path: Path to PDF file
        config: RunConfig with OCR settings
        
    Returns:
        Dictionary with same structure as parse_pdf() result
        
    Example:
        >>> result = apply_ocr("/path/to/scanned.pdf", config)
        >>> if result['success']:
        ...     print(f"OCR extracted {len(result['full_text'])} characters")
    """
    if fitz is None or Image is None or pytesseract is None:
        return {
            'success': False,
            'error': "OCR dependencies not installed. Install with: pip install pytesseract Pillow"
        }
    
    try:
        doc = fitz.open(file_path)
        page_count = len(doc)
        
        # Apply max_pages_per_paper limit
        max_pages = config.max_pages_per_paper
        if max_pages and page_count > max_pages:
            page_count = max_pages
        
        pages = []
        for page_num in range(page_count):
            page = doc[page_num]
            
            # Convert page to image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale for better OCR
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], img_data)
            
            # Apply OCR
            text = pytesseract.image_to_string(img)
            
            pages.append({
                'page_num': page_num + 1,
                'text': text,
                'char_count': len(text)
            })
        
        # Concatenate all text
        full_text = "\n\n".join(p['text'] for p in pages)
        
        # Calculate statistics
        stats = StatisticsTracker.calculate_text_stats(full_text, page_count)
        stats['ocr_applied'] = True
        
        doc.close()
        
        return {
            'success': True,
            'page_count': page_count,
            'pages': pages,
            'full_text': full_text,
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"Error applying OCR to {file_path}: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# =============================================================================
# Step 3.3: Section Detection
# =============================================================================

class SectionDetector:
    """
    Heuristic-based section detector for academic papers.
    
    Detects common sections:
    - Abstract
    - Introduction
    - Methods/Methodology
    - Results
    - Discussion
    - Conclusion
    - References
    """
    
    # Common section headings with variations
    SECTION_PATTERNS = {
        'abstract': [
            r'\babstract\b',
            r'\bsummary\b',
        ],
        'introduction': [
            r'\bintroduction\b',
            r'\bbackground\b',
        ],
        'methods': [
            r'\bmethods?\b',
            r'\bmethodology\b',
            r'\bexperimental\s+setup\b',
            r'\bexperimental\s+design\b',
            r'\bapproach\b',
        ],
        'results': [
            r'\bresults?\b',
            r'\bfindings?\b',
            r'\bexperiments?\b',
        ],
        'discussion': [
            r'\bdiscussion\b',
            r'\banalysis\b',
        ],
        'conclusion': [
            r'\bconclusions?\b',
            r'\bsummary\b',
            r'\bfuture\s+work\b',
        ],
        'references': [
            r'\breferences?\b',
            r'\bbibliography\b',
            r'\bcitations?\b',
        ],
    }
    
    @classmethod
    def detect_section(cls, line: str) -> Optional[str]:
        """
        Detect if a line is a section heading.
        
        Args:
            line: Text line to check
            
        Returns:
            Section label if detected, None otherwise
        """
        line_lower = line.lower().strip()
        
        # Skip very long lines (unlikely to be headings)
        if len(line_lower) > 100:
            return None
        
        # Check each section pattern
        for section, patterns in cls.SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, line_lower):
                    return section
        
        return None


def detect_sections(full_text: str, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect section boundaries in the paper text.
    
    Args:
        full_text: Complete text of the paper
        pages: List of page dictionaries with text
        
    Returns:
        List of section dictionaries with:
            - label: str (section type)
            - start_char: int (character offset in full_text)
            - end_char: int
            - page_start: int
            - page_end: int
            
    Example:
        >>> sections = detect_sections(full_text, pages)
        >>> for sec in sections:
        ...     print(f"{sec['label']}: pages {sec['page_start']}-{sec['page_end']}")
    """
    sections = []
    current_section = None
    current_start = 0
    current_page_start = 1
    
    # Track character position
    char_pos = 0
    
    # Process text line by line
    lines = full_text.split('\n')
    
    for i, line in enumerate(lines):
        # Check if this line is a section heading
        section_label = SectionDetector.detect_section(line)
        
        if section_label:
            # Close previous section
            if current_section:
                sections.append({
                    'label': current_section,
                    'start_char': current_start,
                    'end_char': char_pos,
                    'page_start': current_page_start,
                    'page_end': _get_page_at_char(char_pos, pages)
                })
            
            # Start new section
            current_section = section_label
            current_start = char_pos
            current_page_start = _get_page_at_char(char_pos, pages)
        
        char_pos += len(line) + 1  # +1 for newline
    
    # Close final section
    if current_section:
        sections.append({
            'label': current_section,
            'start_char': current_start,
            'end_char': len(full_text),
            'page_start': current_page_start,
            'page_end': len(pages)
        })
    
    # If no sections detected, create a single "other" section
    if not sections:
        sections.append({
            'label': 'other',
            'start_char': 0,
            'end_char': len(full_text),
            'page_start': 1,
            'page_end': len(pages)
        })
    
    return sections


def _get_page_at_char(char_pos: int, pages: List[Dict[str, Any]]) -> int:
    """
    Get page number at a given character position.
    
    Args:
        char_pos: Character offset in concatenated text
        pages: List of page dictionaries
        
    Returns:
        Page number (1-indexed)
    """
    current_pos = 0
    for page in pages:
        page_len = len(page['text']) + 2  # +2 for "\n\n" separator
        if char_pos < current_pos + page_len:
            return page['page_num']
        current_pos += page_len
    
    return pages[-1]['page_num'] if pages else 1


# =============================================================================
# Step 3.4: Text Chunking
# =============================================================================

def chunk_text(
    text: str,
    chunk_size: int = 1500,
    overlap: int = 200,
    section_label: str = "other",
    page_start: int = 1,
    page_end: int = 1
) -> List[Dict[str, Any]]:
    """
    Split text into chunks with sentence-aware boundaries.
    
    Args:
        text: Text to chunk
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks in characters
        section_label: Section label for all chunks
        page_start: Starting page number
        page_end: Ending page number
        
    Returns:
        List of chunk dictionaries with:
            - text: str
            - section_label: str
            - page_start: int
            - page_end: int
            - char_count: int
            
    Example:
        >>> chunks = chunk_text(text, chunk_size=1000, overlap=100)
        >>> print(f"Created {len(chunks)} chunks")
    """
    if not text or len(text) == 0:
        return []
    
    # Split into sentences (simple regex-based)
    sentences = _split_into_sentences(text)
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_len = len(sentence)
        
        # If adding this sentence exceeds chunk_size, finalize current chunk
        if current_size + sentence_len > chunk_size and current_chunk:
            chunk_text_str = " ".join(current_chunk)
            chunks.append({
                'text': chunk_text_str,
                'section_label': section_label,
                'page_start': page_start,
                'page_end': page_end,
                'char_count': len(chunk_text_str)
            })
            
            # Start new chunk with overlap
            # Keep last few sentences for context
            overlap_sentences = []
            overlap_size = 0
            for sent in reversed(current_chunk):
                # Add 1 for the space between sentences, except for the first sentence
                additional_space = 1 if overlap_sentences else 0
                if overlap_size + len(sent) + additional_space > overlap:
                    break
                overlap_sentences.insert(0, sent)
                overlap_size += len(sent) + additional_space
            
            current_chunk = overlap_sentences
            current_size = overlap_size
        
        current_chunk.append(sentence)
        current_size += sentence_len
    
    # Add final chunk
    if current_chunk:
        chunk_text_str = " ".join(current_chunk)
        chunks.append({
            'text': chunk_text_str,
            'section_label': section_label,
            'page_start': page_start,
            'page_end': page_end,
            'char_count': len(chunk_text_str)
        })
    
    return chunks


def _split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using simple heuristics.
    
    Args:
        text: Text to split
        
    Returns:
        List of sentences
    """
    # Simple sentence boundary detection
    # Split on ., !, ? followed by space and capital letter or end of string
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    
    # Filter out empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def create_chunks_from_pages(
    paper_id: str,
    pages: List[Dict[str, Any]],
    sections: List[Dict[str, Any]],
    config: RunConfig
) -> List[PaperChunk]:
    """
    Create PaperChunk objects from parsed pages and detected sections.
    
    Args:
        paper_id: ID of the paper
        pages: List of page dictionaries from parse_pdf
        sections: List of section dictionaries from detect_sections
        config: RunConfig with chunking parameters
        
    Returns:
        List of PaperChunk objects
        
    Example:
        >>> chunks = create_chunks_from_pages(paper_id, pages, sections, config)
        >>> print(f"Created {len(chunks)} PaperChunk objects")
    """
    # Reconstruct full text
    full_text = "\n\n".join(p['text'] for p in pages)
    
    all_chunks = []
    chunk_index = 0
    
    # Process each section
    for section in sections:
        section_text = full_text[section['start_char']:section['end_char']]
        
        # Chunk the section text
        section_chunks = chunk_text(
            section_text,
            chunk_size=config.chunk_size_chars,
            overlap=config.chunk_overlap_chars,
            section_label=section['label'],
            page_start=section['page_start'],
            page_end=section['page_end']
        )
        
        # Convert to PaperChunk objects
        for chunk_dict in section_chunks:
            chunk_id = IDGenerator.generate_chunk_id(paper_id, chunk_index)
            
            chunk = PaperChunk(
                paper_id=paper_id,
                chunk_id=chunk_id,
                section_label=chunk_dict['section_label'],
                page_start=chunk_dict['page_start'],
                page_end=chunk_dict['page_end'],
                text=chunk_dict['text'],
                char_count=chunk_dict['char_count'],
                token_count_estimate=StatisticsTracker.estimate_tokens(chunk_dict['text'])
            )
            
            all_chunks.append(chunk)
            chunk_index += 1
            
            # Check max_chunks_per_paper limit
            if chunk_index >= config.max_chunks_per_paper:
                logger.warning(
                    f"Reached max_chunks_per_paper limit ({config.max_chunks_per_paper}) "
                    f"for paper {paper_id}"
                )
                break
        
        if chunk_index >= config.max_chunks_per_paper:
            break
    
    return all_chunks


# =============================================================================
# Step 3.5: Parsing Validation
# =============================================================================

def validate_parsing(
    paper: PaperRecord,
    parse_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate PDF parsing results.
    
    Args:
        paper: PaperRecord being processed
        parse_result: Result from parse_pdf()
        
    Returns:
        Dictionary with validation results:
            - valid: bool
            - issues: List[str]
            - warnings: List[str]
            
    Example:
        >>> validation = validate_parsing(paper, parse_result)
        >>> if not validation['valid']:
        ...     print(f"Issues: {validation['issues']}")
    """
    issues = []
    warnings = []
    
    # Check parse success
    if not parse_result.get('success'):
        issues.append(f"Parse failed: {parse_result.get('error', 'Unknown error')}")
        return {'valid': False, 'issues': issues, 'warnings': warnings}
    
    # Check page count
    page_count = parse_result.get('page_count', 0)
    if page_count == 0:
        issues.append("No pages extracted")
    elif page_count < 2:
        warnings.append(f"Only {page_count} page(s) in document")
    
    # Check text extraction
    full_text = parse_result.get('full_text', '')
    if not full_text or len(full_text) < 100:
        issues.append("Very little text extracted (< 100 chars)")
    
    # Check parse quality
    stats = parse_result.get('stats', {})
    quality_score = stats.get('parse_quality_score', 0)
    if quality_score < 0.3:
        warnings.append(f"Low parse quality score: {quality_score}")
    
    # Check pages list
    pages = parse_result.get('pages', [])
    if len(pages) != page_count:
        issues.append(f"Page count mismatch: {page_count} vs {len(pages)} pages")
    
    # Verify all pages have text
    for page in pages:
        if 'text' not in page:
            issues.append(f"Page {page.get('page_num', '?')} missing text")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings
    }


def validate_chunks(chunks: List[PaperChunk], expected_page_count: int) -> Dict[str, Any]:
    """
    Validate created chunks.
    
    Args:
        chunks: List of PaperChunk objects
        expected_page_count: Total number of pages in paper
        
    Returns:
        Dictionary with validation results:
            - valid: bool
            - issues: List[str]
            - warnings: List[str]
            - stats: Dict with chunk statistics
            
    Example:
        >>> validation = validate_chunks(chunks, page_count)
        >>> print(f"Chunk stats: {validation['stats']}")
    """
    issues = []
    warnings = []
    
    # Check chunk count
    if len(chunks) == 0:
        issues.append("No chunks created")
        return {'valid': False, 'issues': issues, 'warnings': warnings, 'stats': {}}
    
    # Validate each chunk
    for i, chunk in enumerate(chunks):
        # Check chunk ID format
        if not chunk.chunk_id:
            issues.append(f"Chunk {i} missing chunk_id")
        
        # Check text content
        if not chunk.text or len(chunk.text) < 50:
            warnings.append(f"Chunk {chunk.chunk_id} has very little text (< 50 chars)")
        
        # Check page ranges
        if chunk.page_start < 1:
            issues.append(f"Chunk {chunk.chunk_id} has invalid page_start: {chunk.page_start}")
        
        if chunk.page_end < chunk.page_start:
            issues.append(f"Chunk {chunk.chunk_id} has page_end < page_start")
        
        if chunk.page_end > expected_page_count:
            warnings.append(
                f"Chunk {chunk.chunk_id} page_end ({chunk.page_end}) > "
                f"total pages ({expected_page_count})"
            )
        
        # Check section label
        valid_sections = {
            "abstract", "introduction", "methods", "results",
            "discussion", "conclusion", "references", "other"
        }
        if chunk.section_label not in valid_sections:
            warnings.append(f"Chunk {chunk.chunk_id} has unusual section: {chunk.section_label}")
    
    # Calculate statistics
    char_counts = [c.char_count for c in chunks]
    stats = {
        'total_chunks': len(chunks),
        'min_chars': min(char_counts) if char_counts else 0,
        'max_chars': max(char_counts) if char_counts else 0,
        'avg_chars': sum(char_counts) / len(char_counts) if char_counts else 0,
        'total_chars': sum(char_counts),
        'sections': {}
    }
    
    # Count chunks per section
    for chunk in chunks:
        section = chunk.section_label
        stats['sections'][section] = stats['sections'].get(section, 0) + 1
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'stats': stats
    }
