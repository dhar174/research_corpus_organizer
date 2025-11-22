#!/usr/bin/env python3
"""
Example usage of Phase 3: PDF Parsing and Chunking

This script demonstrates how to use the pdf_parser module to:
1. Parse PDFs and extract text
2. Detect sections in academic papers
3. Create intelligent chunks
4. Apply OCR fallback if needed
5. Use the parse_and_chunk_worker for LangGraph integration

Run this script to see Phase 3 in action!
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    RunConfig,
    PaperRecord,
    GraphState,
    StateManager,
    IDGenerator,
    create_default_config
)

from pdf_parser import (
    parse_pdf,
    detect_sections,
    create_chunks_from_pages,
    parse_and_chunk_worker,
    needs_ocr,
    validate_parsing,
    validate_chunks
)


def example_1_basic_parsing():
    """Example 1: Basic PDF parsing."""
    print("\n" + "=" * 60)
    print("Example 1: Basic PDF Parsing")
    print("=" * 60)
    
    # Create a config
    config = create_default_config(
        max_pages_per_paper=10,
        enable_ocr_fallback=False
    )
    
    # Note: Replace with actual PDF path to test
    pdf_path = "/path/to/your/paper.pdf"
    
    print(f"\nAttempting to parse: {pdf_path}")
    
    # Parse the PDF
    result = parse_pdf(pdf_path, config)
    
    if result['success']:
        print(f"✅ Successfully parsed PDF!")
        print(f"   Pages: {result['page_count']}")
        print(f"   Total characters: {result['stats']['chars_total']}")
        print(f"   Chars per page: {result['stats']['chars_per_page']:.0f}")
        print(f"   Parse quality: {result['stats']['parse_quality_score']:.2f}")
        
        # Show first 200 characters
        preview = result['full_text'][:200].replace('\n', ' ')
        print(f"\n   Preview: {preview}...")
    else:
        print(f"❌ Failed to parse: {result.get('error', 'Unknown error')}")
        print("   (This is expected if the file doesn't exist)")


def example_2_section_detection():
    """Example 2: Section detection in academic papers."""
    print("\n" + "=" * 60)
    print("Example 2: Section Detection")
    print("=" * 60)
    
    # Sample academic paper text
    sample_text = """
Abstract

This paper presents a novel approach to machine learning.
We demonstrate significant improvements over baseline methods.

Introduction

Machine learning has revolutionized many fields.
In this work, we focus on improving model efficiency.

Methods

We used a dataset of 10,000 samples.
The model architecture consists of three layers.

Results

Our method achieved 95% accuracy on the test set.
This represents a 10% improvement over the baseline.

Discussion

The improved performance can be attributed to several factors.

Conclusion

We have presented a novel approach to machine learning.

References

Smith et al. (2020). Machine Learning Fundamentals.
"""
    
    # Create mock pages
    pages = [
        {'page_num': 1, 'text': sample_text[:len(sample_text)//2], 'char_count': len(sample_text)//2},
        {'page_num': 2, 'text': sample_text[len(sample_text)//2:], 'char_count': len(sample_text) - len(sample_text)//2}
    ]
    
    # Detect sections
    sections = detect_sections(sample_text, pages)
    
    print(f"\n✅ Detected {len(sections)} sections:")
    for section in sections:
        text_preview = sample_text[section['start_char']:section['start_char']+50].replace('\n', ' ')
        print(f"   {section['label']:15} | Pages {section['page_start']}-{section['page_end']} | {text_preview}...")


def example_3_chunking():
    """Example 3: Creating chunks from parsed text."""
    print("\n" + "=" * 60)
    print("Example 3: Text Chunking")
    print("=" * 60)
    
    # Sample text
    sample_text = """
Abstract

This paper presents a novel approach to machine learning.
We demonstrate significant improvements over baseline methods.
Our approach is based on a new architecture.

Introduction

Machine learning has revolutionized many fields.
In this work, we focus on improving model efficiency.
Previous work has shown that large models are effective.
However, they require significant computational resources.
We propose a more efficient alternative.

Methods

We used a dataset of 10,000 samples.
The model architecture consists of three layers.
Training was performed using Adam optimizer.
We ran experiments for 100 epochs.
"""
    
    # Create mock pages
    pages = [
        {'page_num': 1, 'text': sample_text, 'char_count': len(sample_text)}
    ]
    
    # Detect sections
    sections = detect_sections(sample_text, pages)
    
    # Create config
    config = create_default_config(
        chunk_size_chars=200,  # Small chunks for demo
        chunk_overlap_chars=50,
        max_chunks_per_paper=20
    )
    
    # Create chunks
    paper_id = "example_paper_123"
    chunks = create_chunks_from_pages(paper_id, pages, sections, config)
    
    print(f"\n✅ Created {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks[:5]):  # Show first 5
        preview = chunk.text[:80].replace('\n', ' ')
        print(f"\n   Chunk {i+1}:")
        print(f"      ID: {chunk.chunk_id}")
        print(f"      Section: {chunk.section_label}")
        print(f"      Pages: {chunk.page_start}-{chunk.page_end}")
        print(f"      Size: {chunk.char_count} chars, ~{chunk.token_count_estimate} tokens")
        print(f"      Text: {preview}...")
    
    if len(chunks) > 5:
        print(f"\n   ... and {len(chunks) - 5} more chunks")


def example_4_validation():
    """Example 4: Validating parsing and chunks."""
    print("\n" + "=" * 60)
    print("Example 4: Validation")
    print("=" * 60)
    
    # Create a mock parse result
    parse_result = {
        'success': True,
        'page_count': 10,
        'pages': [
            {'page_num': i, 'text': 'Sample text ' * 100, 'char_count': 1200}
            for i in range(1, 11)
        ],
        'full_text': 'Sample text ' * 1000,
        'stats': {
            'pages': 10,
            'chars_total': 12000,
            'chars_per_page': 1200,
            'alnum_ratio': 0.85,
            'parse_quality_score': 0.9
        }
    }
    
    # Create a mock paper
    paper = PaperRecord(
        id="test_paper",
        file_path="/path/to/test.pdf",
        filename="test.pdf"
    )
    
    # Validate parsing
    validation = validate_parsing(paper, parse_result)
    
    print(f"\nParsing Validation:")
    print(f"   Valid: {validation['valid']}")
    print(f"   Issues: {validation['issues'] or 'None'}")
    print(f"   Warnings: {validation['warnings'] or 'None'}")
    
    # Create some mock chunks
    from rag_models import PaperChunk
    
    chunks = [
        PaperChunk(
            paper_id="test_paper",
            chunk_id=f"test_paper_chunk_{i:04d}",
            section_label="introduction" if i < 3 else "methods",
            page_start=i // 2 + 1,
            page_end=i // 2 + 2,
            text="Sample chunk text " * 50,
            char_count=900
        )
        for i in range(8)
    ]
    
    # Validate chunks
    chunk_validation = validate_chunks(chunks, expected_page_count=10)
    
    print(f"\nChunk Validation:")
    print(f"   Valid: {chunk_validation['valid']}")
    print(f"   Issues: {chunk_validation['issues'] or 'None'}")
    print(f"   Warnings: {chunk_validation['warnings'] or 'None'}")
    print(f"\n   Statistics:")
    stats = chunk_validation['stats']
    print(f"      Total chunks: {stats['total_chunks']}")
    print(f"      Avg chars: {stats['avg_chars']:.0f}")
    print(f"      Size range: {stats['min_chars']}-{stats['max_chars']} chars")
    print(f"      Sections: {stats['sections']}")


def example_5_worker_integration():
    """Example 5: Using parse_and_chunk_worker with LangGraph."""
    print("\n" + "=" * 60)
    print("Example 5: LangGraph Worker Integration")
    print("=" * 60)
    
    # Create a config
    config = create_default_config(
        chunk_size_chars=500,
        chunk_overlap_chars=100,
        max_chunks_per_paper=50,
        enable_ocr_fallback=False
    )
    
    # Create initial state
    state = StateManager.create_initial_state(config)
    
    # Create a paper record
    paper_id = IDGenerator.generate_paper_id("/path/to/example.pdf")
    paper = PaperRecord(
        id=paper_id,
        file_path="/path/to/example.pdf",  # Non-existent file for demo
        filename="example.pdf"
    )
    
    # Add paper to state
    state = StateManager.add_paper(state, paper)
    
    print(f"\nCreated paper: {paper.id}")
    print(f"Initial status: {paper.processing_status}")
    
    # Run the worker
    print(f"\nRunning parse_and_chunk_worker...")
    state = parse_and_chunk_worker(paper_id, state)
    
    # Check results
    updated_paper = state['papers'][paper_id]
    print(f"\nWorker completed!")
    print(f"   Status: {updated_paper.processing_status}")
    
    if updated_paper.processing_status == "parsed":
        chunks = state['chunks'].get(paper_id, [])
        print(f"   Chunks created: {len(chunks)}")
        print(f"   Parse quality: {updated_paper.raw_text_stats.get('parse_quality_score', 'N/A')}")
    elif updated_paper.processing_status == "failed":
        print(f"   Error: {updated_paper.error_reason}")
        print(f"   (This is expected since the file doesn't exist)")
    
    # Show state statistics
    stats = StateManager.get_stats(state)
    print(f"\nState Statistics:")
    print(f"   Total papers: {stats['total_papers']}")
    print(f"   Pending: {stats['pending']}")
    print(f"   Completed: {stats['completed']}")
    print(f"   Failed: {stats['failed']}")
    print(f"   Total chunks: {stats['total_chunks']}")


def example_6_ocr_check():
    """Example 6: Checking if OCR is needed."""
    print("\n" + "=" * 60)
    print("Example 6: OCR Quality Check")
    print("=" * 60)
    
    # Example 1: Good quality - no OCR needed
    good_stats = {
        'parse_quality_score': 0.9,
        'chars_per_page': 2000,
        'alnum_ratio': 0.85
    }
    
    print("\nGood quality PDF stats:")
    print(f"   Quality score: {good_stats['parse_quality_score']}")
    print(f"   Chars per page: {good_stats['chars_per_page']}")
    print(f"   OCR needed? {needs_ocr(good_stats)}")
    
    # Example 2: Low quality - OCR needed
    low_quality_stats = {
        'parse_quality_score': 0.3,
        'chars_per_page': 300,
        'alnum_ratio': 0.4
    }
    
    print("\nLow quality PDF stats:")
    print(f"   Quality score: {low_quality_stats['parse_quality_score']}")
    print(f"   Chars per page: {low_quality_stats['chars_per_page']}")
    print(f"   OCR needed? {needs_ocr(low_quality_stats)}")
    
    # Example 3: Scanned document - OCR needed
    scanned_stats = {
        'parse_quality_score': 0.1,
        'chars_per_page': 50,
        'alnum_ratio': 0.1
    }
    
    print("\nScanned PDF stats:")
    print(f"   Quality score: {scanned_stats['parse_quality_score']}")
    print(f"   Chars per page: {scanned_stats['chars_per_page']}")
    print(f"   OCR needed? {needs_ocr(scanned_stats)}")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Phase 3: PDF Parsing and Chunking - Usage Examples")
    print("=" * 60)
    
    try:
        example_1_basic_parsing()
        example_2_section_detection()
        example_3_chunking()
        example_4_validation()
        example_5_worker_integration()
        example_6_ocr_check()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        print("\nNote: Example 1 will fail unless you provide a real PDF path.")
        print("All other examples use mock data and should work correctly.")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
