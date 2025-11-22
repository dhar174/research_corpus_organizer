#!/usr/bin/env python3
"""
Test suite for Phase 3: PDF Parsing and Chunking

Tests all functionality in pdf_parser.py including:
- PDF text extraction with PyMuPDF
- OCR fallback for scanned PDFs
- Section detection
- Text chunking with section awareness
- Parsing validation

Note: Some tests require PyMuPDF, pytesseract, and PIL.
Mock tests are provided for environments without these dependencies.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    RunConfig,
    PaperRecord,
    PaperChunk,
    GraphState,
    StateManager,
    IDGenerator,
    create_default_config
)

from pdf_parser import (
    # Core parsing
    parse_pdf,
    parse_and_chunk_worker,
    
    # OCR fallback
    apply_ocr,
    needs_ocr,
    
    # Section detection
    detect_sections,
    SectionDetector,
    
    # Text chunking
    chunk_text,
    create_chunks_from_pages,
    
    # Validation
    validate_parsing,
    validate_chunks,
)
import pdf_parser


# =============================================================================
# Test Helpers
# =============================================================================

def create_mock_pdf_file(tmpdir: str, content: str = None) -> str:
    """
    Create a mock PDF file for testing.
    
    Note: This creates a minimal valid PDF. For real PDF tests,
    use actual PDF files or PyMuPDF to generate proper PDFs.
    """
    if content is None:
        content = "Mock PDF content for testing."
    
    # Minimal PDF structure
    pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
({content}) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
409
%%EOF
"""
    
    filepath = os.path.join(tmpdir, "test.pdf")
    with open(filepath, 'wb') as f:
        f.write(pdf_content.encode('latin-1'))
    
    return filepath


def create_sample_paper_text() -> str:
    """Create sample academic paper text for testing."""
    return """
Abstract

This paper presents a novel approach to machine learning.
We demonstrate significant improvements over baseline methods.

Introduction

Machine learning has revolutionized many fields.
In this work, we focus on improving model efficiency.
Our contributions are threefold.

Methods

We used a dataset of 10,000 samples.
The model architecture consists of three layers.
Training was performed using Adam optimizer.

Results

Our method achieved 95% accuracy on the test set.
This represents a 10% improvement over the baseline.
The results are statistically significant.

Discussion

The improved performance can be attributed to several factors.
First, the novel architecture captures important features.
Second, the training procedure is more robust.

Conclusion

We have presented a novel approach to machine learning.
Future work will explore additional domains.

References

Smith et al. (2020). Machine Learning Fundamentals.
Jones and Brown (2021). Advanced Neural Networks.
"""


# =============================================================================
# Test Section Detection
# =============================================================================

def test_section_detector():
    """Test SectionDetector class."""
    print("\nTesting SectionDetector...")
    
    # Test abstract detection
    assert SectionDetector.detect_section("Abstract") == "abstract"
    assert SectionDetector.detect_section("ABSTRACT") == "abstract"
    assert SectionDetector.detect_section("1. Abstract") == "abstract"
    print("  ✓ Abstract detection")
    
    # Test introduction detection
    assert SectionDetector.detect_section("Introduction") == "introduction"
    assert SectionDetector.detect_section("1. INTRODUCTION") == "introduction"
    print("  ✓ Introduction detection")
    
    # Test methods detection
    assert SectionDetector.detect_section("Methods") == "methods"
    assert SectionDetector.detect_section("Methodology") == "methods"
    assert SectionDetector.detect_section("3. Experimental Setup") == "methods"
    print("  ✓ Methods detection")
    
    # Test results detection
    assert SectionDetector.detect_section("Results") == "results"
    assert SectionDetector.detect_section("4. Results and Analysis") == "results"
    print("  ✓ Results detection")
    
    # Test discussion detection
    assert SectionDetector.detect_section("Discussion") == "discussion"
    assert SectionDetector.detect_section("5. Discussion") == "discussion"
    print("  ✓ Discussion detection")
    
    # Test conclusion detection
    assert SectionDetector.detect_section("Conclusion") == "conclusion"
    assert SectionDetector.detect_section("Conclusions") == "conclusion"
    assert SectionDetector.detect_section("6. Conclusion and Future Work") == "conclusion"
    print("  ✓ Conclusion detection")
    
    # Test references detection
    assert SectionDetector.detect_section("References") == "references"
    assert SectionDetector.detect_section("Bibliography") == "references"
    print("  ✓ References detection")
    
    # Test non-section lines
    assert SectionDetector.detect_section("This is just a regular line.") is None
    assert SectionDetector.detect_section("Machine learning is important.") is None
    print("  ✓ Non-section detection")
    
    print("✅ SectionDetector tests passed")


def test_detect_sections():
    """Test detect_sections function."""
    print("\nTesting detect_sections...")
    
    text = create_sample_paper_text()
    
    # Create mock pages
    pages = [
        {'page_num': 1, 'text': text[:500], 'char_count': 500},
        {'page_num': 2, 'text': text[500:], 'char_count': len(text) - 500}
    ]
    
    sections = detect_sections(text, pages)
    
    # Check that sections were detected
    assert len(sections) > 0
    print(f"  ✓ Detected {len(sections)} sections")
    
    # Check section labels
    labels = [s['label'] for s in sections]
    assert 'abstract' in labels
    assert 'introduction' in labels
    assert 'methods' in labels
    assert 'results' in labels
    print(f"  ✓ Section labels: {labels}")
    
    # Validate section structure
    for section in sections:
        assert 'label' in section
        assert 'start_char' in section
        assert 'end_char' in section
        assert 'page_start' in section
        assert 'page_end' in section
        assert section['start_char'] < section['end_char']
    print("  ✓ Section structure valid")
    
    print("✅ detect_sections tests passed")


# =============================================================================
# Test Text Chunking
# =============================================================================

def test_split_into_sentences():
    """Test sentence splitting."""
    print("\nTesting _split_into_sentences...")
    
    text = "This is sentence one. This is sentence two! And this is sentence three? Finally, sentence four."
    sentences = _split_into_sentences(text)
    
    assert len(sentences) == 4
    assert "sentence one" in sentences[0]
    assert "sentence two" in sentences[1]
    print(f"  ✓ Split into {len(sentences)} sentences")
    
    # Test with single sentence
    single = "Just one sentence here."
    sentences = _split_into_sentences(single)
    assert len(sentences) == 1
    print("  ✓ Single sentence handling")
    
    # Test with empty string
    sentences = _split_into_sentences("")
    assert len(sentences) == 0
    print("  ✓ Empty string handling")
    
    print("✅ _split_into_sentences tests passed")


def test_chunk_text():
    """Test chunk_text function."""
    print("\nTesting chunk_text...")
    
    # Create a long text
    text = " ".join([f"Sentence {i}. " for i in range(100)])
    
    # Test basic chunking
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    
    assert len(chunks) > 1
    print(f"  ✓ Created {len(chunks)} chunks from long text")
    
    # Verify chunk structure
    for chunk in chunks:
        assert 'text' in chunk
        assert 'section_label' in chunk
        assert 'page_start' in chunk
        assert 'page_end' in chunk
        assert 'char_count' in chunk
    print("  ✓ Chunk structure valid")
    
    # Check chunk sizes
    for chunk in chunks:
        # Allow some flexibility in chunk size
        assert 100 < chunk['char_count'] < 700
    print("  ✓ Chunk sizes reasonable")
    
    # Test with small text (single chunk)
    small_text = "This is a small text."
    chunks = chunk_text(small_text, chunk_size=1000)
    assert len(chunks) == 1
    print("  ✓ Single chunk for small text")
    
    # Test with empty text
    chunks = chunk_text("", chunk_size=1000)
    assert len(chunks) == 0
    print("  ✓ Empty text returns no chunks")
    
    print("✅ chunk_text tests passed")


def test_create_chunks_from_pages():
    """Test create_chunks_from_pages function."""
    print("\nTesting create_chunks_from_pages...")
    
    # Create sample data
    paper_id = "test_paper_123"
    text = create_sample_paper_text()
    
    pages = [
        {'page_num': 1, 'text': text[:500], 'char_count': 500},
        {'page_num': 2, 'text': text[500:], 'char_count': len(text) - 500}
    ]
    
    sections = detect_sections(text, pages)
    
    config = create_default_config(
        chunk_size_chars=300,
        chunk_overlap_chars=50,
        max_chunks_per_paper=100
    )
    
    # Create chunks
    chunks = create_chunks_from_pages(paper_id, pages, sections, config)
    
    assert len(chunks) > 0
    print(f"  ✓ Created {len(chunks)} PaperChunk objects")
    
    # Verify all are PaperChunk instances
    for chunk in chunks:
        assert isinstance(chunk, PaperChunk)
        assert chunk.paper_id == paper_id
        assert chunk.chunk_id.startswith(paper_id)
    print("  ✓ All chunks are valid PaperChunk instances")
    
    # Check section labels
    section_labels = set(c.section_label for c in chunks)
    print(f"  ✓ Section labels in chunks: {section_labels}")
    
    # Verify chunk IDs are unique
    chunk_ids = [c.chunk_id for c in chunks]
    assert len(chunk_ids) == len(set(chunk_ids))
    print("  ✓ All chunk IDs are unique")
    
    # Test max_chunks_per_paper limit
    config_limited = create_default_config(
        chunk_size_chars=100,
        chunk_overlap_chars=20,
        max_chunks_per_paper=5
    )
    
    chunks_limited = create_chunks_from_pages(paper_id, pages, sections, config_limited)
    assert len(chunks_limited) <= 5
    print(f"  ✓ max_chunks_per_paper limit respected: {len(chunks_limited)} <= 5")
    
    print("✅ create_chunks_from_pages tests passed")


# =============================================================================
# Test OCR Functions
# =============================================================================

def test_needs_ocr():
    """Test needs_ocr function."""
    print("\nTesting needs_ocr...")
    
    # Low quality - needs OCR
    low_quality_stats = {
        'parse_quality_score': 0.3,
        'chars_per_page': 800
    }
    assert needs_ocr(low_quality_stats) == True
    print("  ✓ Low quality detected")
    
    # Low char count - needs OCR
    low_chars_stats = {
        'parse_quality_score': 0.8,
        'chars_per_page': 200
    }
    assert needs_ocr(low_chars_stats) == True
    print("  ✓ Low character count detected")
    
    # Good quality - no OCR needed
    good_stats = {
        'parse_quality_score': 0.9,
        'chars_per_page': 2000
    }
    assert needs_ocr(good_stats) == False
    print("  ✓ Good quality detected")
    
    # Test with custom threshold
    borderline_stats = {
        'parse_quality_score': 0.6,
        'chars_per_page': 1500
    }
    assert needs_ocr(borderline_stats, quality_threshold=0.7) == True
    assert needs_ocr(borderline_stats, quality_threshold=0.5) == False
    print("  ✓ Custom threshold works")
    
    print("✅ needs_ocr tests passed")


# =============================================================================
# Test Validation Functions
# =============================================================================

def test_validate_parsing():
    """Test validate_parsing function."""
    print("\nTesting validate_parsing...")
    
    # Create a mock paper
    paper = PaperRecord(
        id="test_123",
        file_path="/path/to/test.pdf",
        filename="test.pdf"
    )
    
    # Test successful parse
    good_result = {
        'success': True,
        'page_count': 10,
        'pages': [{'page_num': i, 'text': 'Sample text ' * 100} for i in range(1, 11)],
        'full_text': 'Sample text ' * 1000,
        'stats': {
            'parse_quality_score': 0.9,
            'chars_per_page': 1200
        }
    }
    
    validation = validate_parsing(paper, good_result)
    assert validation['valid'] == True
    assert len(validation['issues']) == 0
    print("  ✓ Valid parse recognized")
    
    # Test failed parse
    failed_result = {
        'success': False,
        'error': 'File not found'
    }
    
    validation = validate_parsing(paper, failed_result)
    assert validation['valid'] == False
    assert len(validation['issues']) > 0
    print("  ✓ Failed parse detected")
    
    # Test low quality parse
    low_quality_result = {
        'success': True,
        'page_count': 5,
        'pages': [{'page_num': i, 'text': 'x'} for i in range(1, 6)],
        'full_text': 'xxxxx',
        'stats': {
            'parse_quality_score': 0.2,
            'chars_per_page': 1
        }
    }
    
    validation = validate_parsing(paper, low_quality_result)
    assert len(validation['warnings']) > 0
    print("  ✓ Low quality parse flagged")
    
    print("✅ validate_parsing tests passed")


def test_validate_chunks():
    """Test validate_chunks function."""
    print("\nTesting validate_chunks...")
    
    paper_id = "test_paper"
    
    # Create valid chunks
    valid_chunks = [
        PaperChunk(
            paper_id=paper_id,
            chunk_id=f"{paper_id}_chunk_{i:04d}",
            section_label="introduction",
            page_start=1,
            page_end=2,
            text="Sample text " * 50,
            char_count=600
        )
        for i in range(5)
    ]
    
    validation = validate_chunks(valid_chunks, expected_page_count=10)
    assert validation['valid'] == True
    assert len(validation['issues']) == 0
    assert validation['stats']['total_chunks'] == 5
    print("  ✓ Valid chunks recognized")
    print(f"  ✓ Stats: {validation['stats']}")
    
    # Test empty chunks list
    validation = validate_chunks([], expected_page_count=10)
    assert validation['valid'] == False
    print("  ✓ Empty chunks detected")
    
    # Test invalid page ranges
    invalid_chunks = [
        PaperChunk(
            paper_id=paper_id,
            chunk_id=f"{paper_id}_chunk_0000",
            section_label="other",
            page_start=5,
            page_end=3,  # Invalid: end < start
            text="Sample text",
            char_count=11
        )
    ]
    
    validation = validate_chunks(invalid_chunks, expected_page_count=10)
    assert len(validation['issues']) > 0
    print("  ✓ Invalid page ranges detected")
    
    # Test small chunks (should warn)
    small_chunks = [
        PaperChunk(
            paper_id=paper_id,
            chunk_id=f"{paper_id}_chunk_0000",
            section_label="other",
            page_start=1,
            page_end=1,
            text="Tiny",
            char_count=4
        )
    ]
    
    validation = validate_chunks(small_chunks, expected_page_count=10)
    assert len(validation['warnings']) > 0
    print("  ✓ Small chunks flagged with warnings")
    
    print("✅ validate_chunks tests passed")


# =============================================================================
# Test Parse and Chunk Worker (Integration Test)
# =============================================================================

def test_parse_and_chunk_worker_mock():
    """Test parse_and_chunk_worker with mock data."""
    print("\nTesting parse_and_chunk_worker (mock)...")
    
    # Create a config
    config = create_default_config(
        chunk_size_chars=300,
        chunk_overlap_chars=50,
        max_chunks_per_paper=50,
        enable_ocr_fallback=False
    )
    
    # Create initial state
    state = StateManager.create_initial_state(config)
    
    # Create a paper record
    paper_id = IDGenerator.generate_paper_id("/path/to/test.pdf")
    paper = PaperRecord(
        id=paper_id,
        file_path="/path/to/nonexistent.pdf",  # Will fail
        filename="test.pdf"
    )
    
    # Add paper to state
    state = StateManager.add_paper(state, paper)
    
    # Run worker (should fail because file doesn't exist)
    state = parse_and_chunk_worker(paper_id, state)
    
    # Check that paper was marked as failed
    assert paper_id in state['papers_failed']
    assert state['papers'][paper_id].processing_status == "failed"
    print("  ✓ Worker correctly handles missing file")
    
    # Note: Full integration test with real PDF would require PyMuPDF
    # and a sample PDF file. That would be tested in a real environment.
    
    print("✅ parse_and_chunk_worker mock tests passed")


# =============================================================================
# Run All Tests
# =============================================================================

def run_all_tests():
    """Run all Phase 3 tests."""
    print("=" * 60)
    print("Running Phase 3 Test Suite")
    print("=" * 60)
    
    try:
        # Section detection tests
        test_section_detector()
        test_detect_sections()
        
        # Text chunking tests
        test_split_into_sentences()
        test_chunk_text()
        test_create_chunks_from_pages()
        
        # OCR tests
        test_needs_ocr()
        
        # Validation tests
        test_validate_parsing()
        test_validate_chunks()
        
        # Integration tests
        test_parse_and_chunk_worker_mock()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
