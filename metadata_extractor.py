"""
RAG PDF Research Corpus System - Metadata Extraction (Phase 4)

This module provides utilities for:
- ArXiv metadata extraction via API (Step 4.1)
- DOI/CrossRef metadata extraction (Step 4.2)
- PDF document properties extraction (Step 4.3)
- Abstract extraction from parsed text (Step 4.4)
- Metadata validation and normalization (Step 4.5)

Version: 1.0
Date: 2025-11-22
"""

import os
import re
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
from dateutil import parser as date_parser
from dateutil.parser import ParserError

try:
    import requests
except ImportError:
    requests = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from rag_models import (
    PaperRecord,
    RunConfig,
    GraphState,
    StateManager
)

logger = logging.getLogger(__name__)

# Export list for clean imports
__all__ = [
    # ArXiv extraction (Step 4.1)
    'extract_arxiv_metadata',
    'query_arxiv_api',
    'detect_arxiv_id',
    
    # DOI/CrossRef extraction (Step 4.2)
    'extract_doi_metadata',
    'query_crossref_api',
    'detect_doi',
    
    # PDF metadata extraction (Step 4.3)
    'extract_pdf_metadata',
    'extract_pdf_properties',
    
    # Abstract extraction (Step 4.4)
    'extract_abstract_from_text',
    'extract_abstract_from_sections',
    
    # Metadata validation and normalization (Step 4.5)
    'normalize_metadata',
    'validate_metadata',
    'normalize_author_names',
    'normalize_title',
    'normalize_venue',
    'parse_date_flexible',
    
    # Worker function for LangGraph
    'metadata_extraction_worker',
]

# =============================================================================
# Constants and Configuration
# =============================================================================

ARXIV_API_URL = "http://export.arxiv.org/api/query"
CROSSREF_API_URL = "https://api.crossref.org/works"

# Rate limiting
ARXIV_RATE_LIMIT_DELAY = 3.0  # seconds between requests
CROSSREF_RATE_LIMIT_DELAY = 1.0  # seconds between requests

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2.0

# Regex patterns
ARXIV_ID_PATTERN = r'(?:arxiv[:\s]?)?(\d{4}\.\d{4,5}(?:v\d+)?)'
DOI_PATTERN = r'10\.\d{4,}/[^\s]+'


# =============================================================================
# Step 4.1: ArXiv Metadata Extraction
# =============================================================================

def detect_arxiv_id(filename: str, text: str = "") -> Optional[str]:
    """
    Detect arXiv ID from filename or text content.
    
    Supports patterns like:
    - 2301.12345
    - 2301.12345v1
    - arxiv:2301.12345
    - arxiv-2301.12345
    
    Args:
        filename: Filename to search
        text: Text content to search (optional, checks first 5000 chars)
        
    Returns:
        arXiv ID if found, None otherwise
        
    Example:
        >>> detect_arxiv_id("arxiv-2301.12345.pdf")
        '2301.12345'
        >>> detect_arxiv_id("paper.pdf", "arXiv:2301.12345v1")
        '2301.12345v1'
    """
    # Try filename first
    patterns = [
        r'(?:arxiv[_:\s-])?(\d{4}\.\d{4,5}(?:v\d+)?)',
        r'(\d{4}\.\d{4,5}(?:v\d+)?)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            return match.group(1)
    
    # Try text content (first 5000 chars)
    if text:
        search_text = text[:5000]
        for pattern in patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                return match.group(1)
    
    return None


def query_arxiv_api(arxiv_id: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
    """
    Query arXiv API for paper metadata.
    
    Args:
        arxiv_id: arXiv identifier (e.g., "2301.12345" or "2301.12345v1")
        retry_count: Current retry attempt (for internal use)
        
    Returns:
        Dictionary with metadata if successful, None otherwise
        Contains: title, authors, abstract, published, updated, 
                 categories, arxiv_version
                 
    Raises:
        ImportError: If requests library not available
        
    Example:
        >>> metadata = query_arxiv_api("2301.12345")
        >>> if metadata:
        ...     print(metadata['title'])
    """
    if requests is None:
        raise ImportError("requests library required for arXiv API queries")
    
    # Clean version suffix for API query
    clean_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id
    
    try:
        # Query arXiv API
        params = {
            'id_list': clean_id,
            'max_results': 1
        }
        
        logger.info(f"Querying arXiv API for {arxiv_id}")
        response = requests.get(ARXIV_API_URL, params=params, timeout=10)
        response.raise_for_status()
        
        # Parse XML response
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        
        # Find the entry
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        
        entry = root.find('atom:entry', namespaces)
        if entry is None:
            logger.warning(f"No arXiv entry found for {arxiv_id}")
            return None
        
        # Extract metadata
        def get_text(path: str) -> Optional[str]:
            elem = entry.find(path, namespaces)
            return elem.text.strip() if elem is not None and elem.text else None
        
        # Extract authors
        authors = []
        for author in entry.findall('atom:author', namespaces):
            name_elem = author.find('atom:name', namespaces)
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text.strip())
        
        # Extract categories
        categories = []
        for category in entry.findall('atom:category', namespaces):
            term = category.get('term')
            if term:
                categories.append(term)
        
        # Extract version from arxiv:comment or id
        version = None
        if 'v' in arxiv_id:
            version = arxiv_id.split('v')[1]
        
        metadata = {
            'title': get_text('atom:title'),
            'authors': authors,
            'abstract': get_text('atom:summary'),
            'published': get_text('atom:published'),
            'updated': get_text('atom:updated'),
            'categories': categories,
            'arxiv_version': version,
            'arxiv_id': arxiv_id
        }
        
        # Apply rate limiting
        time.sleep(ARXIV_RATE_LIMIT_DELAY)
        
        logger.info(f"Successfully retrieved metadata for arXiv:{arxiv_id}")
        return metadata
        
    except requests.exceptions.RequestException as e:
        logger.error(f"arXiv API request failed for {arxiv_id}: {e}")
        
        # Retry logic
        if retry_count < MAX_RETRIES:
            wait_time = RETRY_BACKOFF_FACTOR ** retry_count
            logger.info(f"Retrying in {wait_time}s... (attempt {retry_count + 1}/{MAX_RETRIES})")
            time.sleep(wait_time)
            return query_arxiv_api(arxiv_id, retry_count + 1)
        
        return None
        
    except Exception as e:
        logger.error(f"Error parsing arXiv response for {arxiv_id}: {e}")
        return None


def extract_arxiv_metadata(paper: PaperRecord, text: str = "") -> PaperRecord:
    """
    Extract and populate arXiv metadata for a paper.
    
    This function:
    1. Detects arXiv ID in filename or text
    2. Queries arXiv API if ID found
    3. Populates PaperRecord with metadata
    4. Marks paper as preprint
    
    Args:
        paper: PaperRecord to update
        text: Paper text content (optional, for ID detection)
        
    Returns:
        Updated PaperRecord
        
    Example:
        >>> paper = PaperRecord(id="123", file_path="/path/to/arxiv-2301.12345.pdf", ...)
        >>> paper = extract_arxiv_metadata(paper)
        >>> print(paper.arxiv_id, paper.is_preprint)
        '2301.12345' True
    """
    # Detect arXiv ID
    arxiv_id = detect_arxiv_id(paper.filename, text)
    
    if not arxiv_id:
        logger.debug(f"No arXiv ID detected for {paper.filename}")
        return paper
    
    # Query arXiv API
    metadata = query_arxiv_api(arxiv_id)
    
    if not metadata:
        logger.warning(f"Failed to retrieve arXiv metadata for {arxiv_id}")
        paper.arxiv_id = arxiv_id
        return paper
    
    # Populate paper record
    paper.arxiv_id = arxiv_id
    paper.source = "arxiv"
    paper.is_preprint = True
    
    # Only update fields if not already set
    if not paper.title and metadata.get('title'):
        paper.title = normalize_title(metadata['title'])
    
    if not paper.authors and metadata.get('authors'):
        paper.authors = normalize_author_names(metadata['authors'])
    
    if not paper.abstract_text and metadata.get('abstract'):
        paper.abstract_text = metadata['abstract'].strip()
    
    # Parse publication date
    if metadata.get('published'):
        try:
            pub_date = date_parser.parse(metadata['published']).date()
            if not paper.publish_date:
                paper.publish_date = pub_date
                paper.publish_date_source = "arxiv"
                paper.year = pub_date.year
        except (ParserError, ValueError) as e:
            logger.warning(f"Failed to parse arXiv date: {e}")
    
    if metadata.get('arxiv_version'):
        paper.arxiv_version = metadata['arxiv_version']
    
    logger.info(f"Successfully extracted arXiv metadata for {paper.filename}")
    return paper


# =============================================================================
# Step 4.2: DOI Metadata Extraction
# =============================================================================

def detect_doi(text: str) -> Optional[str]:
    """
    Detect DOI in text content.
    
    Searches for DOI pattern: 10.NNNN/...
    
    Args:
        text: Text content to search (checks first 5000 chars)
        
    Returns:
        DOI string if found, None otherwise
        
    Example:
        >>> detect_doi("DOI: 10.1234/example.2023")
        '10.1234/example.2023'
    """
    if not text:
        return None
    
    # Search in first 5000 characters
    search_text = text[:5000]
    
    # Pattern: 10.NNNN/...
    match = re.search(DOI_PATTERN, search_text)
    if match:
        doi = match.group(0)
        # Clean up common trailing characters
        doi = doi.rstrip('.,;)}]')
        return doi
    
    return None


def query_crossref_api(doi: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
    """
    Query CrossRef API for paper metadata.
    
    Args:
        doi: DOI identifier (e.g., "10.1234/example.2023")
        retry_count: Current retry attempt (for internal use)
        
    Returns:
        Dictionary with metadata if successful, None otherwise
        Contains: title, authors, container_title (journal/venue), 
                 published_date, type, doi
                 
    Raises:
        ImportError: If requests library not available
        
    Example:
        >>> metadata = query_crossref_api("10.1234/example.2023")
        >>> if metadata:
        ...     print(metadata['title'])
    """
    if requests is None:
        raise ImportError("requests library required for CrossRef API queries")
    
    try:
        # Query CrossRef API
        url = f"{CROSSREF_API_URL}/{doi}"
        headers = {
            'User-Agent': 'RAG-PDF-System/1.0 (mailto:research@example.com)'
        }
        
        logger.info(f"Querying CrossRef API for DOI: {doi}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') != 'ok':
            logger.warning(f"CrossRef API returned non-OK status for {doi}")
            return None
        
        message = data.get('message', {})
        
        # Extract authors
        authors = []
        for author in message.get('author', []):
            given = author.get('given', '')
            family = author.get('family', '')
            if given and family:
                authors.append(f"{given} {family}")
            elif family:
                authors.append(family)
        
        # Extract publication date
        pub_date = None
        date_parts = message.get('published-print', {}).get('date-parts')
        if not date_parts:
            date_parts = message.get('published-online', {}).get('date-parts')
        if not date_parts:
            date_parts = message.get('created', {}).get('date-parts')
        
        if date_parts and len(date_parts) > 0 and len(date_parts[0]) > 0:
            parts = date_parts[0]
            year = parts[0] if len(parts) > 0 else None
            month = parts[1] if len(parts) > 1 else 1
            day = parts[2] if len(parts) > 2 else 1
            if year:
                pub_date = f"{year}-{month:02d}-{day:02d}"
        
        # Extract title (may be a list)
        title = None
        title_list = message.get('title', [])
        if title_list and len(title_list) > 0:
            title = title_list[0]
        
        # Extract venue
        venue = message.get('container-title', [])
        if venue and len(venue) > 0:
            venue = venue[0]
        else:
            venue = None
        
        metadata = {
            'title': title,
            'authors': authors,
            'venue': venue,
            'published_date': pub_date,
            'type': message.get('type'),
            'doi': doi
        }
        
        # Apply rate limiting
        time.sleep(CROSSREF_RATE_LIMIT_DELAY)
        
        logger.info(f"Successfully retrieved metadata for DOI: {doi}")
        return metadata
        
    except requests.exceptions.RequestException as e:
        logger.error(f"CrossRef API request failed for {doi}: {e}")
        
        # Retry logic
        if retry_count < MAX_RETRIES:
            wait_time = RETRY_BACKOFF_FACTOR ** retry_count
            logger.info(f"Retrying in {wait_time}s... (attempt {retry_count + 1}/{MAX_RETRIES})")
            time.sleep(wait_time)
            return query_crossref_api(doi, retry_count + 1)
        
        return None
        
    except Exception as e:
        logger.error(f"Error parsing CrossRef response for {doi}: {e}")
        return None


def extract_doi_metadata(paper: PaperRecord, text: str = "") -> PaperRecord:
    """
    Extract and populate DOI/CrossRef metadata for a paper.
    
    This function:
    1. Detects DOI in text content
    2. Queries CrossRef API if DOI found
    3. Populates PaperRecord with metadata
    4. Marks paper as published (not preprint)
    
    Args:
        paper: PaperRecord to update
        text: Paper text content (for DOI detection)
        
    Returns:
        Updated PaperRecord
        
    Example:
        >>> paper = PaperRecord(id="123", file_path="/path/to/paper.pdf", ...)
        >>> paper = extract_doi_metadata(paper, full_text)
        >>> print(paper.doi, paper.is_preprint)
        '10.1234/example' False
    """
    # Detect DOI
    doi = detect_doi(text)
    
    if not doi:
        logger.debug(f"No DOI detected for {paper.filename}")
        return paper
    
    # Query CrossRef API
    metadata = query_crossref_api(doi)
    
    if not metadata:
        logger.warning(f"Failed to retrieve CrossRef metadata for {doi}")
        paper.doi = doi
        return paper
    
    # Populate paper record
    paper.doi = doi
    
    # If we have DOI metadata and no arXiv ID, mark as published
    if not paper.arxiv_id:
        paper.source = "doi"
        paper.is_preprint = False
    
    # Only update fields if not already set (arXiv takes priority)
    if not paper.title and metadata.get('title'):
        paper.title = normalize_title(metadata['title'])
    
    if not paper.authors and metadata.get('authors'):
        paper.authors = normalize_author_names(metadata['authors'])
    
    if not paper.venue and metadata.get('venue'):
        paper.venue = normalize_venue(metadata['venue'])
    
    # Parse publication date
    if metadata.get('published_date'):
        try:
            pub_date = date_parser.parse(metadata['published_date']).date()
            if not paper.publish_date:
                paper.publish_date = pub_date
                paper.publish_date_source = "crossref"
                paper.year = pub_date.year
        except (ParserError, ValueError) as e:
            logger.warning(f"Failed to parse CrossRef date: {e}")
    
    logger.info(f"Successfully extracted CrossRef metadata for {paper.filename}")
    return paper


# =============================================================================
# Step 4.3: PDF Metadata Extraction
# =============================================================================

def extract_pdf_properties(file_path: str) -> Dict[str, Any]:
    """
    Extract PDF document properties using PyMuPDF.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Dictionary with PDF metadata properties:
        - title, author, subject, keywords
        - creator, producer
        - creation_date, mod_date
        - format, encryption
        
    Raises:
        ImportError: If PyMuPDF not available
        FileNotFoundError: If file doesn't exist
        
    Example:
        >>> props = extract_pdf_properties("/path/to/paper.pdf")
        >>> print(props['title'], props['author'])
    """
    if fitz is None:
        raise ImportError("PyMuPDF (fitz) required for PDF property extraction")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    try:
        doc = fitz.open(file_path)
        metadata = doc.metadata
        
        # Extract all available properties
        properties = {
            'title': metadata.get('title', '').strip() if metadata.get('title') else None,
            'author': metadata.get('author', '').strip() if metadata.get('author') else None,
            'subject': metadata.get('subject', '').strip() if metadata.get('subject') else None,
            'keywords': metadata.get('keywords', '').strip() if metadata.get('keywords') else None,
            'creator': metadata.get('creator', '').strip() if metadata.get('creator') else None,
            'producer': metadata.get('producer', '').strip() if metadata.get('producer') else None,
            'creation_date': metadata.get('creationDate', '').strip() if metadata.get('creationDate') else None,
            'mod_date': metadata.get('modDate', '').strip() if metadata.get('modDate') else None,
            'format': metadata.get('format', '').strip() if metadata.get('format') else None,
            'encryption': metadata.get('encryption'),
        }
        
        doc.close()
        
        return properties
        
    except Exception as e:
        logger.error(f"Failed to extract PDF properties from {file_path}: {e}")
        return {}


def extract_pdf_metadata(paper: PaperRecord) -> PaperRecord:
    """
    Extract and populate PDF document metadata.
    
    This function:
    1. Extracts PDF properties using PyMuPDF
    2. Parses and normalizes metadata fields
    3. Uses as fallback when API metadata unavailable
    4. Extracts creation/modification dates
    
    Args:
        paper: PaperRecord to update
        
    Returns:
        Updated PaperRecord
        
    Example:
        >>> paper = PaperRecord(id="123", file_path="/path/to/paper.pdf", ...)
        >>> paper = extract_pdf_metadata(paper)
        >>> print(paper.title)
    """
    properties = extract_pdf_properties(paper.file_path)
    
    if not properties:
        logger.debug(f"No PDF properties extracted for {paper.filename}")
        return paper
    
    # Use PDF metadata as fallback (don't override API metadata)
    if not paper.title and properties.get('title'):
        title = properties['title']
        # Filter out common junk titles
        if title and len(title) > 5 and not title.lower().startswith('microsoft word'):
            paper.title = normalize_title(title)
    
    if not paper.authors and properties.get('author'):
        # Parse author field (may contain multiple authors)
        author_str = properties['author']
        # Split on common delimiters
        authors = re.split(r'[,;]|\sand\s', author_str)
        authors = [a.strip() for a in authors if a.strip()]
        if authors:
            paper.authors = normalize_author_names(authors)
    
    # Parse creation/modification dates
    for date_field, source in [('creation_date', 'pdf'), ('mod_date', 'pdf')]:
        if properties.get(date_field):
            try:
                # PyMuPDF dates format: "D:YYYYMMDDHHmmSS..."
                date_str = properties[date_field]
                if date_str.startswith('D:'):
                    if len(date_str) >= 16:
                        date_str = date_str[2:16]  # Extract YYYYMMDDHHmmSS
                        parsed_date = datetime.strptime(date_str, '%Y%m%d%H%M%S').date()
                    else:
                        logger.debug(f"Malformed PDF date format: {date_str}")
                        continue
                else:
                    parsed_date = date_parser.parse(date_str).date()
                
                # Only use if no other date available
                if not paper.publish_date and date_field == 'creation_date':
                    paper.publish_date = parsed_date
                    paper.publish_date_source = source
                    paper.year = parsed_date.year
                    
            except (ParserError, ValueError) as e:
                logger.debug(f"Failed to parse PDF date {date_field}: {e}")
    
    logger.info(f"Extracted PDF metadata for {paper.filename}")
    return paper


# =============================================================================
# Step 4.4: Abstract Extraction
# =============================================================================

def extract_abstract_from_sections(sections: List[Dict[str, Any]], full_text: str) -> Optional[str]:
    """
    Extract abstract text from detected sections.
    
    Args:
        sections: List of section dictionaries from detect_sections()
        full_text: Full paper text
        
    Returns:
        Abstract text if found, None otherwise
        
    Example:
        >>> sections = detect_sections(full_text, pages)
        >>> abstract = extract_abstract_from_sections(sections, full_text)
    """
    for section in sections:
        if section.get('label') == 'abstract':
            start = section.get('start_char', 0)
            end = section.get('end_char', len(full_text))
            abstract_text = full_text[start:end].strip()
            
            # Clean up common artifacts
            # Remove "Abstract" header if present at start
            abstract_text = re.sub(r'^abstract[\s:]*', '', abstract_text, flags=re.IGNORECASE)
            
            # Clean up excess whitespace
            abstract_text = re.sub(r'\s+', ' ', abstract_text)
            
            if abstract_text and len(abstract_text) > 50:  # Minimum length check
                return abstract_text
    
    return None


def extract_abstract_from_text(text: str) -> Optional[str]:
    """
    Extract abstract from text using pattern matching.
    
    Searches for "Abstract" heading and extracts following text
    until next section or maximum length.
    
    Args:
        text: Full paper text
        
    Returns:
        Abstract text if found, None otherwise
        
    Example:
        >>> abstract = extract_abstract_from_text(full_text)
    """
    if not text:
        return None
    
    # Look for abstract section
    # Pattern: "Abstract" (case-insensitive) followed by text
    pattern = r'(?i)abstract[\s:]*\n\s*([^\n].{50,2000}?)(?:\n\s*(?:1\.|introduction|keywords|i\.|background)|\Z)'
    
    match = re.search(pattern, text[:5000], re.DOTALL | re.IGNORECASE)
    
    if match:
        abstract_text = match.group(1).strip()
        
        # Clean up
        abstract_text = re.sub(r'\s+', ' ', abstract_text)
        
        # Length check (abstracts typically 100-500 words)
        if 50 < len(abstract_text) < 3000:
            return abstract_text
    
    return None


# =============================================================================
# Step 4.5: Metadata Validation and Normalization
# =============================================================================

def parse_date_flexible(date_str: str) -> Optional[date]:
    """
    Parse date string with flexible format support.
    
    Supports:
    - ISO format (YYYY-MM-DD)
    - Various date formats
    - Partial dates (YYYY, YYYY-MM)
    
    Args:
        date_str: Date string to parse
        
    Returns:
        date object if successful, None otherwise
        
    Example:
        >>> parse_date_flexible("2023-01-15")
        datetime.date(2023, 1, 15)
        >>> parse_date_flexible("January 2023")
        datetime.date(2023, 1, 1)
    """
    if not date_str:
        return None
    
    try:
        # Use dateutil parser for flexible parsing
        parsed = date_parser.parse(date_str, default=datetime(1900, 1, 1))
        return parsed.date()
    except (ParserError, ValueError, TypeError):
        # Try year-only parsing
        year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if year_match:
            try:
                year = int(year_match.group(0))
                return date(year, 1, 1)
            except ValueError:
                pass
        
        logger.debug(f"Failed to parse date: {date_str}")
        return None


def normalize_author_names(authors: List[str]) -> List[str]:
    """
    Normalize author name formats.
    
    Performs:
    - Whitespace cleanup
    - Removal of empty entries
    - Basic name validation
    
    Args:
        authors: List of author name strings
        
    Returns:
        Normalized list of author names
        
    Example:
        >>> normalize_author_names(["  John Doe  ", "", "Jane Smith"])
        ['John Doe', 'Jane Smith']
    """
    normalized = []
    
    for author in authors:
        if not author:
            continue
        
        # Clean up whitespace
        author = re.sub(r'\s+', ' ', author.strip())
        
        # Skip if too short or looks invalid
        if len(author) < 2:
            continue
        
        # Skip common artifacts
        if author.lower() in ['unknown', 'anonymous', 'n/a', 'none']:
            continue
        
        normalized.append(author)
    
    return normalized


def normalize_title(title: str) -> str:
    """
    Normalize title string.
    
    Performs:
    - Whitespace cleanup
    - Newline removal
    - Excess punctuation removal
    
    Args:
        title: Title string
        
    Returns:
        Normalized title
        
    Example:
        >>> normalize_title("  Example\\n Title  ")
        'Example Title'
    """
    if not title:
        return ""
    
    # Remove newlines and excess whitespace
    title = re.sub(r'\s+', ' ', title.strip())
    
    # Remove trailing periods (common in PDF metadata)
    title = title.rstrip('.')
    
    # Remove common artifacts
    title = re.sub(r'\s*\|\s*PDF$', '', title, flags=re.IGNORECASE)
    
    return title


def normalize_venue(venue: str) -> str:
    """
    Normalize publication venue name.
    
    Performs:
    - Whitespace cleanup
    - Common abbreviation standardization
    
    Args:
        venue: Venue/journal name
        
    Returns:
        Normalized venue name
        
    Example:
        >>> normalize_venue("  Nature  Reviews  ")
        'Nature Reviews'
    """
    if not venue:
        return ""
    
    # Clean up whitespace
    venue = re.sub(r'\s+', ' ', venue.strip())
    
    # Common standardizations could be added here
    # For now, just basic cleanup
    
    return venue


def validate_metadata(paper: PaperRecord) -> Dict[str, Any]:
    """
    Validate paper metadata quality.
    
    Checks:
    - Required fields presence
    - Date validity
    - Author name quality
    - Title quality
    
    Args:
        paper: PaperRecord to validate
        
    Returns:
        Dictionary with validation results:
        - quality_score: float (0-1)
        - has_title, has_authors, has_date, has_abstract: bool
        - warnings: List[str]
        
    Example:
        >>> validation = validate_metadata(paper)
        >>> print(validation['quality_score'])
        0.85
    """
    warnings = []
    quality_score = 0.0
    
    # Check title
    has_title = bool(paper.title and len(paper.title) > 5)
    if has_title:
        quality_score += 0.25
    else:
        warnings.append("Missing or very short title")
    
    # Check authors
    has_authors = bool(paper.authors and len(paper.authors) > 0)
    if has_authors:
        quality_score += 0.25
    else:
        warnings.append("No authors found")
    
    # Check publication date
    has_date = bool(paper.publish_date)
    if has_date:
        quality_score += 0.20
        # Validate year is reasonable
        if paper.year and (paper.year < 1900 or paper.year > datetime.now().year + 1):
            warnings.append(f"Suspicious publication year: {paper.year}")
            quality_score -= 0.1
    else:
        warnings.append("No publication date found")
    
    # Check abstract
    has_abstract = bool(paper.abstract_text and len(paper.abstract_text) > 50)
    if has_abstract:
        quality_score += 0.20
    else:
        warnings.append("No abstract found")
    
    # Check source identifiers
    has_source = bool(paper.arxiv_id or paper.doi)
    if has_source:
        quality_score += 0.10
    
    # Clamp score to [0, 1]
    quality_score = max(0.0, min(1.0, quality_score))
    
    return {
        'quality_score': round(quality_score, 2),
        'has_title': has_title,
        'has_authors': has_authors,
        'has_date': has_date,
        'has_abstract': has_abstract,
        'has_source': has_source,
        'warnings': warnings
    }


def normalize_metadata(paper: PaperRecord) -> PaperRecord:
    """
    Apply all metadata normalization to a paper.
    
    Normalizes:
    - Title
    - Author names
    - Venue
    - Dates
    
    Args:
        paper: PaperRecord to normalize
        
    Returns:
        Normalized PaperRecord
        
    Example:
        >>> paper = normalize_metadata(paper)
    """
    # Normalize title
    if paper.title:
        paper.title = normalize_title(paper.title)
    
    # Normalize authors
    if paper.authors:
        paper.authors = normalize_author_names(paper.authors)
    
    # Normalize venue
    if paper.venue:
        paper.venue = normalize_venue(paper.venue)
    
    # Ensure year matches publish_date if both exist
    if paper.publish_date and not paper.year:
        paper.year = paper.publish_date.year
    
    return paper


# =============================================================================
# LangGraph Worker Function
# =============================================================================

def metadata_extraction_worker(paper_id: str, state: GraphState) -> GraphState:
    """
    LangGraph worker node for metadata extraction.
    
    This worker:
    1. Retrieves paper from state
    2. Extracts metadata from arXiv API (if applicable)
    3. Extracts metadata from CrossRef API (if applicable)
    4. Extracts PDF document properties
    5. Extracts abstract from text
    6. Validates and normalizes metadata
    7. Updates paper status
    8. Updates state
    
    Args:
        paper_id: ID of paper to process
        state: Current GraphState
        
    Returns:
        Updated GraphState
        
    Example:
        >>> state = metadata_extraction_worker(paper_id, state)
    """
    try:
        # Get paper and config
        paper = state['papers'].get(paper_id)
        if not paper:
            logger.error(f"Paper {paper_id} not found in state")
            return state
        
        config = state['config']
        
        logger.info(f"Starting metadata extraction for {paper.filename}")
        
        # Get text for ID/abstract detection
        full_text = ""
        chunks = state['chunks'].get(paper_id, [])
        if chunks:
            # Concatenate first few chunks for detection
            full_text = " ".join(chunk.text for chunk in chunks[:5])
        
        # Step 1: Extract arXiv metadata
        paper = extract_arxiv_metadata(paper, full_text)
        
        # Step 2: Extract DOI metadata (if no arXiv or as supplement)
        paper = extract_doi_metadata(paper, full_text)
        
        # Step 3: Extract PDF metadata (as fallback)
        paper = extract_pdf_metadata(paper)
        
        # Step 4: Extract abstract
        if not paper.abstract_text and chunks:
            # Try using section detection if available
            if hasattr(state, 'sections') and paper_id in state.get('sections', {}):
                sections = state['sections'][paper_id]
                abstract = extract_abstract_from_sections(sections, full_text)
                if abstract:
                    paper.abstract_text = abstract
            
            # Try pattern-based extraction
            if not paper.abstract_text:
                abstract = extract_abstract_from_text(full_text)
                if abstract:
                    paper.abstract_text = abstract
        
        # Step 5: Normalize metadata
        paper = normalize_metadata(paper)
        
        # Step 6: Validate metadata
        validation = validate_metadata(paper)
        
        # Store validation results in raw_text_stats for now
        if not paper.raw_text_stats:
            paper.raw_text_stats = {}
        paper.raw_text_stats['metadata_quality'] = validation['quality_score']
        paper.raw_text_stats['metadata_warnings'] = validation['warnings']
        
        # Update processing status
        paper.last_updated = datetime.now()
        
        # Update state
        state['papers'][paper_id] = paper
        
        logger.info(f"Metadata extraction complete for {paper.filename} "
                   f"(quality: {validation['quality_score']})")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in metadata extraction for {paper_id}: {e}")
        return StateManager.mark_paper_failed(
            state, paper_id, f"Metadata extraction failed: {str(e)}"
        )
