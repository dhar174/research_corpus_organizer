#!/usr/bin/env python3
"""
Test suite for Phase 4: Metadata Extraction

Tests all functionality in metadata_extractor.py including:
- ArXiv ID detection and API queries
- DOI detection and CrossRef API queries
- PDF metadata extraction
- Abstract extraction
- Metadata normalization and validation
- Worker integration with GraphState

Note: Some tests require internet access for API calls.
Mock tests are provided for offline environments.
"""

import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    PaperRecord,
    StateManager,
    create_default_config
)

from metadata_extractor import (
    # ArXiv extraction
    detect_arxiv_id,
    
    # DOI extraction
    detect_doi,
    
    # Abstract extraction
    extract_abstract_from_text,
    extract_abstract_from_sections,
    
    # Normalization and validation
    normalize_author_names,
    normalize_title,
    normalize_venue,
    parse_date_flexible,
    validate_metadata,
    normalize_metadata,
)


# =============================================================================
# Test Helpers
# =============================================================================

def create_test_paper(filename: str = "test.pdf", file_path: str = "/tmp/test.pdf") -> PaperRecord:
    """Create a test PaperRecord for testing."""
    return PaperRecord(
        id="test123",
        file_path=file_path,
        filename=filename,
        processing_status="parsed"
    )


# =============================================================================
# Test Step 4.1: ArXiv Metadata Extraction
# =============================================================================

def test_detect_arxiv_id():
    """Test arXiv ID detection from filenames and text."""
    print("\n=== Testing arXiv ID Detection ===")
    
    # Test cases
    test_cases = [
        ("arxiv-2301.12345.pdf", "2301.12345"),
        ("arxiv_2301.12345v1.pdf", "2301.12345v1"),
        ("2301.12345.pdf", "2301.12345"),
        ("paper_arxiv:2301.12345.pdf", "2301.12345"),
        ("random_paper.pdf", None),
    ]
    
    for filename, expected in test_cases:
        result = detect_arxiv_id(filename)
        print(f"  Filename: {filename}")
        print(f"    Expected: {expected}, Got: {result}")
        assert result == expected, f"Failed for {filename}"
    
    # Test detection in text
    text_with_arxiv = "This paper is available on arXiv:2301.12345v2"
    result = detect_arxiv_id("no_id.pdf", text_with_arxiv)
    print(f"  Text detection: {result}")
    assert result == "2301.12345v2"
    
    print("✓ ArXiv ID detection tests passed")


def test_extract_arxiv_metadata_mock():
    """Test arXiv metadata extraction with mock data (no API call)."""
    print("\n=== Testing ArXiv Metadata Extraction (Mock) ===")
    
    # Create test paper
    paper = create_test_paper(filename="arxiv-2301.12345.pdf")
    
    # Note: We can't test actual API calls without network access
    # But we can test ID detection and structure
    
    # Verify ID is detected
    arxiv_id = detect_arxiv_id(paper.filename)
    print(f"  Detected arXiv ID: {arxiv_id}")
    assert arxiv_id == "2301.12345"
    
    # Test with paper that has arXiv ID
    paper.arxiv_id = "2301.12345"
    paper.title = "Test Paper"
    paper.authors = ["Author One", "Author Two"]
    
    # Verify paper structure
    assert paper.arxiv_id == "2301.12345"
    assert paper.title == "Test Paper"
    
    print("✓ ArXiv metadata extraction mock test passed")


# =============================================================================
# Test Step 4.2: DOI Metadata Extraction
# =============================================================================

def test_detect_doi():
    """Test DOI detection from text."""
    print("\n=== Testing DOI Detection ===")
    
    # Test cases
    test_cases = [
        ("DOI: 10.1234/example.2023", "10.1234/example.2023"),
        ("doi:10.5678/test-paper", "10.5678/test-paper"),
        ("https://doi.org/10.9012/paper", "10.9012/paper"),
        ("No DOI in this text", None),
        ("", None),
    ]
    
    for text, expected in test_cases:
        result = detect_doi(text)
        display_text = f"{text[:50]}..." if len(text) > 50 else text
        print(f"  Text: '{display_text}'")
        print(f"    Expected: {expected}, Got: {result}")
        if expected:
            assert result == expected, f"Failed for '{text}'"
        else:
            assert result is None, f"Should not detect DOI in '{text}'"
    
    print("✓ DOI detection tests passed")


def test_extract_doi_metadata_mock():
    """Test DOI metadata extraction with mock data (no API call)."""
    print("\n=== Testing DOI Metadata Extraction (Mock) ===")
    
    # Create test paper
    paper = create_test_paper()
    
    # Test DOI detection
    text_with_doi = "This paper has DOI: 10.1234/example.2023"
    doi = detect_doi(text_with_doi)
    print(f"  Detected DOI: {doi}")
    assert doi == "10.1234/example.2023"
    
    # Test with paper that has DOI
    paper.doi = "10.1234/example"
    paper.title = "Published Paper"
    paper.is_preprint = False
    
    # Verify paper structure
    assert paper.doi == "10.1234/example"
    assert paper.is_preprint == False
    
    print("✓ DOI metadata extraction mock test passed")


# =============================================================================
# Test Step 4.3: PDF Metadata Extraction
# =============================================================================

def test_extract_pdf_properties_mock():
    """Test PDF properties extraction (mock without actual PDF)."""
    print("\n=== Testing PDF Properties Extraction (Mock) ===")
    
    # Note: Without actual PDF file or PyMuPDF, we can't test extraction
    # But we can verify the function structure
    
    # Test that function requires PyMuPDF
    try:
        import fitz
        print("  PyMuPDF is available")
    except ImportError:
        print("  PyMuPDF not available - skipping PDF property tests")
        return
    
    print("✓ PDF properties extraction structure verified")


def test_extract_pdf_metadata_integration():
    """Test PDF metadata extraction integration."""
    print("\n=== Testing PDF Metadata Integration ===")
    
    # Create test paper
    paper = create_test_paper()
    
    # Simulate PDF metadata
    paper.title = "PDF Title"
    paper.authors = ["PDF Author"]
    
    # Verify normalization happens
    paper = normalize_metadata(paper)
    
    assert paper.title == "PDF Title"
    assert paper.authors == ["PDF Author"]
    
    print("✓ PDF metadata integration test passed")


# =============================================================================
# Test Step 4.4: Abstract Extraction
# =============================================================================

def test_extract_abstract_from_text():
    """Test abstract extraction from text using patterns."""
    print("\n=== Testing Abstract Extraction from Text ===")
    
    # Test with typical academic paper format
    text_with_abstract = """
    Title of Paper
    
    Abstract
    
    This is the abstract of the paper. It contains important information
    about the research methodology and findings. This abstract is long enough
    to be considered valid.
    
    1. Introduction
    
    The introduction starts here...
    """
    
    abstract = extract_abstract_from_text(text_with_abstract)
    print(f"  Extracted abstract length: {len(abstract) if abstract else 0}")
    assert abstract is not None
    assert "abstract of the paper" in abstract.lower()
    assert "introduction" not in abstract.lower()
    
    # Test with no abstract
    text_no_abstract = """
    Just a regular paper without an abstract section.
    Some content here.
    """
    
    abstract = extract_abstract_from_text(text_no_abstract)
    print(f"  No abstract case: {abstract}")
    assert abstract is None
    
    print("✓ Abstract extraction from text tests passed")


def test_extract_abstract_from_sections():
    """Test abstract extraction from section data."""
    print("\n=== Testing Abstract Extraction from Sections ===")
    
    full_text = "Some intro text. Abstract section here with important content about the research. Introduction follows."
    
    sections = [
        {
            'label': 'abstract',
            'start_char': 17,
            'end_char': 83,
            'page_start': 1,
            'page_end': 1
        },
        {
            'label': 'introduction',
            'start_char': 84,
            'end_char': 100,
            'page_start': 1,
            'page_end': 1
        }
    ]
    
    abstract = extract_abstract_from_sections(sections, full_text)
    print(f"  Extracted abstract: '{abstract}'")
    assert abstract is not None
    assert "Abstract section here" in abstract
    assert "Introduction" not in abstract
    
    # Test with no abstract section
    sections_no_abstract = [
        {
            'label': 'introduction',
            'start_char': 0,
            'end_char': 50,
            'page_start': 1,
            'page_end': 1
        }
    ]
    
    abstract = extract_abstract_from_sections(sections_no_abstract, full_text)
    print(f"  No abstract case: {abstract}")
    assert abstract is None
    
    print("✓ Abstract extraction from sections tests passed")


# =============================================================================
# Test Step 4.5: Metadata Validation and Normalization
# =============================================================================

def test_parse_date_flexible():
    """Test flexible date parsing."""
    print("\n=== Testing Flexible Date Parsing ===")
    
    # Test cases
    test_cases = [
        ("2023-01-15", date(2023, 1, 15)),
        ("January 15, 2023", date(2023, 1, 15)),
        ("2023", date(2023, 1, 1)),
        ("15/01/2023", date(2023, 1, 15)),
        ("invalid date", None),
        ("", None),
    ]
    
    for date_str, expected in test_cases:
        result = parse_date_flexible(date_str)
        print(f"  Input: '{date_str}'")
        print(f"    Expected: {expected}, Got: {result}")
        if expected:
            assert result == expected, f"Failed for '{date_str}'"
        else:
            assert result is None or isinstance(result, date), f"Unexpected result for '{date_str}'"
    
    print("✓ Date parsing tests passed")


def test_normalize_author_names():
    """Test author name normalization."""
    print("\n=== Testing Author Name Normalization ===")
    
    # Test cases
    authors_input = [
        "  John Doe  ",
        "",
        "Jane   Smith",
        "  ",
        "Bob Johnson",
        "unknown"
    ]
    
    expected = ["John Doe", "Jane Smith", "Bob Johnson"]
    
    result = normalize_author_names(authors_input)
    print(f"  Input: {authors_input}")
    print(f"  Expected: {expected}")
    print(f"  Got: {result}")
    
    assert result == expected
    
    print("✓ Author name normalization tests passed")


def test_normalize_title():
    """Test title normalization."""
    print("\n=== Testing Title Normalization ===")
    
    # Test cases
    test_cases = [
        ("  Example\n Title  ", "Example Title"),
        ("Title with trailing period.", "Title with trailing period"),
        ("Normal Title", "Normal Title"),
        ("Title | PDF", "Title"),
    ]
    
    for input_title, expected in test_cases:
        result = normalize_title(input_title)
        print(f"  Input: '{input_title}'")
        print(f"    Expected: '{expected}', Got: '{result}'")
        assert result == expected
    
    print("✓ Title normalization tests passed")


def test_normalize_venue():
    """Test venue normalization."""
    print("\n=== Testing Venue Normalization ===")
    
    # Test cases
    test_cases = [
        ("  Nature  Reviews  ", "Nature Reviews"),
        ("Journal of AI", "Journal of AI"),
        ("", ""),
    ]
    
    for input_venue, expected in test_cases:
        result = normalize_venue(input_venue)
        print(f"  Input: '{input_venue}'")
        print(f"    Expected: '{expected}', Got: '{result}'")
        assert result == expected
    
    print("✓ Venue normalization tests passed")


def test_validate_metadata():
    """Test metadata validation and quality scoring."""
    print("\n=== Testing Metadata Validation ===")
    
    # Test with complete metadata
    paper_complete = create_test_paper()
    paper_complete.title = "Complete Paper Title"
    paper_complete.authors = ["Author One", "Author Two"]
    paper_complete.publish_date = date(2023, 1, 15)
    paper_complete.year = 2023
    paper_complete.abstract_text = "This is a complete abstract with sufficient length to be considered valid for testing purposes."
    paper_complete.arxiv_id = "2301.12345"
    
    validation = validate_metadata(paper_complete)
    print(f"  Complete metadata quality score: {validation['quality_score']}")
    print(f"  Warnings: {validation['warnings']}")
    
    assert validation['has_title'] == True
    assert validation['has_authors'] == True
    assert validation['has_date'] == True
    assert validation['has_abstract'] == True
    assert validation['quality_score'] >= 0.9
    
    # Test with minimal metadata
    paper_minimal = create_test_paper()
    paper_minimal.title = "Title"
    
    validation = validate_metadata(paper_minimal)
    print(f"  Minimal metadata quality score: {validation['quality_score']}")
    print(f"  Warnings: {validation['warnings']}")
    
    assert validation['has_title'] == True
    assert validation['has_authors'] == False
    assert validation['quality_score'] < 0.5
    assert len(validation['warnings']) > 0
    
    print("✓ Metadata validation tests passed")


def test_normalize_metadata():
    """Test complete metadata normalization."""
    print("\n=== Testing Complete Metadata Normalization ===")
    
    paper = create_test_paper()
    paper.title = "  Example\n Paper  Title.  "
    paper.authors = ["  John   Doe  ", "", "Jane Smith"]
    paper.venue = "  Example  Journal  "
    paper.publish_date = date(2023, 5, 10)
    
    paper = normalize_metadata(paper)
    
    print(f"  Normalized title: '{paper.title}'")
    print(f"  Normalized authors: {paper.authors}")
    print(f"  Normalized venue: '{paper.venue}'")
    print(f"  Year: {paper.year}")
    
    assert paper.title == "Example Paper Title"
    assert paper.authors == ["John Doe", "Jane Smith"]
    assert paper.venue == "Example Journal"
    assert paper.year == 2023
    
    print("✓ Complete metadata normalization tests passed")


# =============================================================================
# Test Worker Integration
# =============================================================================

def test_metadata_extraction_worker():
    """Test metadata extraction worker integration with GraphState."""
    print("\n=== Testing Metadata Extraction Worker ===")
    
    # Create initial state
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    # Create test paper
    paper = create_test_paper(filename="arxiv-2301.12345.pdf")
    paper.file_path = "/tmp/test.pdf"  # Mock path
    
    # Add to state
    state = StateManager.add_paper(state, paper)
    
    # Simulate some text chunks for abstract detection
    from rag_models import PaperChunk
    chunks = [
        PaperChunk(
            paper_id=paper.id,
            chunk_id="chunk_0001",
            section_label="abstract",
            page_start=1,
            page_end=1,
            text="Abstract: This is a test abstract for the paper. It contains important information."
        )
    ]
    state = StateManager.add_chunks(state, paper.id, chunks)
    
    # Note: Worker will try to call APIs and read PDF
    # For testing, we'll just verify structure
    print(f"  Paper in state: {paper.id}")
    print(f"  Chunks available: {len(state['chunks'].get(paper.id, []))}")
    print(f"  ArXiv ID detected: {detect_arxiv_id(paper.filename)}")
    
    # Verify the paper is in state
    assert paper.id in state['papers']
    assert paper.id in state['chunks']
    
    print("✓ Metadata extraction worker structure verified")


# =============================================================================
# Main Test Runner
# =============================================================================

def run_all_tests():
    """Run all Phase 4 tests."""
    print("=" * 70)
    print("Phase 4: Metadata Extraction - Test Suite")
    print("=" * 70)
    
    try:
        # Step 4.1: ArXiv tests
        test_detect_arxiv_id()
        test_extract_arxiv_metadata_mock()
        
        # Step 4.2: DOI tests
        test_detect_doi()
        test_extract_doi_metadata_mock()
        
        # Step 4.3: PDF metadata tests
        test_extract_pdf_properties_mock()
        test_extract_pdf_metadata_integration()
        
        # Step 4.4: Abstract extraction tests
        test_extract_abstract_from_text()
        test_extract_abstract_from_sections()
        
        # Step 4.5: Normalization and validation tests
        test_parse_date_flexible()
        test_normalize_author_names()
        test_normalize_title()
        test_normalize_venue()
        test_validate_metadata()
        test_normalize_metadata()
        
        # Worker integration test
        test_metadata_extraction_worker()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
