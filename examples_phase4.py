#!/usr/bin/env python3
"""
Phase 4 Usage Examples: Metadata Extraction

This file demonstrates how to use the metadata extraction module
for various use cases.

Examples include:
- Extracting arXiv metadata
- Extracting DOI/CrossRef metadata
- Extracting PDF properties
- Extracting abstracts
- Validating and normalizing metadata
- Using the LangGraph worker
"""

import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    PaperRecord,
    StateManager,
    create_default_config,
    PaperChunk
)

from metadata_extractor import (
    # ArXiv
    detect_arxiv_id,
    
    # DOI
    detect_doi,
    
    # Abstract
    extract_abstract_from_text,
    
    # Normalization
    normalize_metadata,
    validate_metadata,
)


# =============================================================================
# Example 1: Detect and Extract arXiv Metadata
# =============================================================================

def example_arxiv_extraction():
    """Example: Extract metadata from arXiv paper."""
    print("\n" + "=" * 70)
    print("Example 1: ArXiv Metadata Extraction")
    print("=" * 70)
    
    # Create a paper record with arXiv ID in filename
    paper = PaperRecord(
        id="paper001",
        file_path="/path/to/arxiv-2301.12345.pdf",
        filename="arxiv-2301.12345.pdf",
        processing_status="parsed"
    )
    
    # Detect arXiv ID
    arxiv_id = detect_arxiv_id(paper.filename)
    print(f"\n1. Detected arXiv ID: {arxiv_id}")
    
    # Extract metadata (would query API if available)
    # Note: This example shows structure; actual API call requires internet
    print("\n2. Extracting arXiv metadata (mock)...")
    
    # Simulate what extract_arxiv_metadata would do
    paper.arxiv_id = arxiv_id
    paper.source = "arxiv"
    paper.is_preprint = True
    paper.title = "Example Paper on Large Language Models"
    paper.authors = ["John Doe", "Jane Smith"]
    paper.abstract_text = "This is an example abstract from arXiv."
    paper.publish_date = date(2023, 1, 15)
    paper.year = 2023
    
    print(f"\n3. Extracted Metadata:")
    print(f"   arXiv ID: {paper.arxiv_id}")
    print(f"   Title: {paper.title}")
    print(f"   Authors: {', '.join(paper.authors)}")
    print(f"   Is Preprint: {paper.is_preprint}")
    print(f"   Date: {paper.publish_date}")
    print(f"   Abstract: {paper.abstract_text[:100]}...")


# =============================================================================
# Example 2: Detect and Extract DOI/CrossRef Metadata
# =============================================================================

def example_doi_extraction():
    """Example: Extract metadata from DOI via CrossRef."""
    print("\n" + "=" * 70)
    print("Example 2: DOI/CrossRef Metadata Extraction")
    print("=" * 70)
    
    # Sample paper text with DOI
    paper_text = """
    This is a published research paper.
    DOI: 10.1234/example.journal.2023
    Published in Example Journal.
    """
    
    # Detect DOI
    doi = detect_doi(paper_text)
    print(f"\n1. Detected DOI: {doi}")
    
    # Create paper record
    paper = PaperRecord(
        id="paper002",
        file_path="/path/to/published_paper.pdf",
        filename="published_paper.pdf",
        processing_status="parsed"
    )
    
    # Extract metadata (would query CrossRef API if available)
    print("\n2. Extracting CrossRef metadata (mock)...")
    
    # Simulate what extract_doi_metadata would do
    paper.doi = doi
    paper.source = "doi"
    paper.is_preprint = False
    paper.title = "Example Published Paper"
    paper.authors = ["Alice Johnson", "Bob Williams"]
    paper.venue = "Example Journal"
    paper.publish_date = date(2023, 6, 1)
    paper.year = 2023
    
    print(f"\n3. Extracted Metadata:")
    print(f"   DOI: {paper.doi}")
    print(f"   Title: {paper.title}")
    print(f"   Authors: {', '.join(paper.authors)}")
    print(f"   Venue: {paper.venue}")
    print(f"   Is Preprint: {paper.is_preprint}")
    print(f"   Date: {paper.publish_date}")


# =============================================================================
# Example 3: Extract PDF Document Properties
# =============================================================================

def example_pdf_metadata():
    """Example: Extract metadata from PDF properties."""
    print("\n" + "=" * 70)
    print("Example 3: PDF Document Properties Extraction")
    print("=" * 70)
    
    # Create paper record
    paper = PaperRecord(
        id="paper003",
        file_path="/path/to/paper.pdf",
        filename="paper.pdf",
        processing_status="parsed"
    )
    
    print("\n1. Extracting PDF properties...")
    print("   (Would use PyMuPDF to read PDF metadata)")
    
    # Simulate PDF metadata extraction
    # In real usage: paper = extract_pdf_metadata(paper)
    paper.title = "Title from PDF Metadata"
    paper.authors = ["PDF Author One", "PDF Author Two"]
    
    print(f"\n2. Extracted from PDF:")
    print(f"   Title: {paper.title}")
    print(f"   Authors: {', '.join(paper.authors)}")
    
    print("\n3. Note: PDF metadata is used as fallback when")
    print("   arXiv/CrossRef metadata is not available")


# =============================================================================
# Example 4: Extract Abstract from Text
# =============================================================================

def example_abstract_extraction():
    """Example: Extract abstract from paper text."""
    print("\n" + "=" * 70)
    print("Example 4: Abstract Extraction")
    print("=" * 70)
    
    # Sample paper text with abstract
    paper_text = """
    Title of the Research Paper
    
    Abstract
    
    This paper presents a novel approach to solving the problem
    of metadata extraction from academic papers. We propose a
    comprehensive system that combines multiple sources including
    arXiv, CrossRef, and PDF metadata to build complete paper
    records with high accuracy.
    
    1. Introduction
    
    In recent years, the volume of academic papers has grown
    exponentially...
    """
    
    print("\n1. Extracting abstract from text...")
    abstract = extract_abstract_from_text(paper_text)
    
    if abstract:
        print(f"\n2. Extracted Abstract:")
        print(f"   {abstract}")
        print(f"\n3. Abstract length: {len(abstract)} characters")
    else:
        print("\n2. No abstract found")


# =============================================================================
# Example 5: Metadata Validation and Normalization
# =============================================================================

def example_metadata_validation():
    """Example: Validate and normalize metadata."""
    print("\n" + "=" * 70)
    print("Example 5: Metadata Validation and Normalization")
    print("=" * 70)
    
    # Create paper with messy metadata
    paper = PaperRecord(
        id="paper005",
        file_path="/path/to/paper.pdf",
        filename="paper.pdf",
        processing_status="parsed"
    )
    
    # Messy metadata
    paper.title = "  Example\n  Paper   Title.  "
    paper.authors = ["  John   Doe  ", "", "  Jane  Smith  ", "unknown"]
    paper.venue = "  Nature    Reviews  "
    paper.publish_date = date(2023, 3, 15)
    
    print("\n1. Before normalization:")
    print(f"   Title: '{paper.title}'")
    print(f"   Authors: {paper.authors}")
    print(f"   Venue: '{paper.venue}'")
    
    # Normalize metadata
    paper = normalize_metadata(paper)
    
    print("\n2. After normalization:")
    print(f"   Title: '{paper.title}'")
    print(f"   Authors: {paper.authors}")
    print(f"   Venue: '{paper.venue}'")
    print(f"   Year: {paper.year}")
    
    # Validate metadata
    validation = validate_metadata(paper)
    
    print("\n3. Validation Results:")
    print(f"   Quality Score: {validation['quality_score']}")
    print(f"   Has Title: {validation['has_title']}")
    print(f"   Has Authors: {validation['has_authors']}")
    print(f"   Has Date: {validation['has_date']}")
    print(f"   Has Abstract: {validation['has_abstract']}")
    
    if validation['warnings']:
        print(f"\n4. Warnings:")
        for warning in validation['warnings']:
            print(f"   - {warning}")


# =============================================================================
# Example 6: Complete Metadata Extraction Pipeline
# =============================================================================

def example_complete_pipeline():
    """Example: Complete metadata extraction workflow."""
    print("\n" + "=" * 70)
    print("Example 6: Complete Metadata Extraction Pipeline")
    print("=" * 70)
    
    # Create paper with arXiv ID
    paper = PaperRecord(
        id="paper006",
        file_path="/path/to/arxiv-2301.12345.pdf",
        filename="arxiv-2301.12345.pdf",
        processing_status="parsed"
    )
    
    # Sample text for abstract extraction
    paper_text = """
    Title
    
    Abstract
    
    This is the abstract of the paper with sufficient length
    to be considered valid for extraction purposes.
    
    Introduction
    
    The paper continues here...
    """
    
    print("\n1. Starting metadata extraction pipeline...")
    
    # Step 1: Try arXiv
    print("\n   Step 1: Checking for arXiv metadata...")
    arxiv_id = detect_arxiv_id(paper.filename)
    if arxiv_id:
        print(f"   ✓ Found arXiv ID: {arxiv_id}")
        # paper = extract_arxiv_metadata(paper, paper_text)
        # Simulate
        paper.arxiv_id = arxiv_id
        paper.is_preprint = True
        paper.title = "Example Paper Title"
        paper.authors = ["Author One", "Author Two"]
    
    # Step 2: Try DOI (if no arXiv or as supplement)
    print("\n   Step 2: Checking for DOI...")
    doi = detect_doi(paper_text)
    if doi:
        print(f"   ✓ Found DOI: {doi}")
        # paper = extract_doi_metadata(paper, paper_text)
    else:
        print("   No DOI found")
    
    # Step 3: PDF metadata as fallback
    print("\n   Step 3: Extracting PDF metadata...")
    # paper = extract_pdf_metadata(paper)
    print("   ✓ PDF metadata extracted (fallback)")
    
    # Step 4: Extract abstract
    print("\n   Step 4: Extracting abstract...")
    abstract = extract_abstract_from_text(paper_text)
    if abstract:
        paper.abstract_text = abstract
        print(f"   ✓ Abstract extracted ({len(abstract)} chars)")
    
    # Step 5: Normalize
    print("\n   Step 5: Normalizing metadata...")
    paper = normalize_metadata(paper)
    print("   ✓ Metadata normalized")
    
    # Step 6: Validate
    print("\n   Step 6: Validating metadata...")
    validation = validate_metadata(paper)
    print(f"   ✓ Quality score: {validation['quality_score']}")
    
    print("\n2. Final Paper Metadata:")
    print(f"   ID: {paper.id}")
    print(f"   Title: {paper.title}")
    print(f"   Authors: {', '.join(paper.authors)}")
    print(f"   arXiv ID: {paper.arxiv_id}")
    print(f"   Is Preprint: {paper.is_preprint}")
    print(f"   Abstract: {paper.abstract_text[:100] if paper.abstract_text else 'N/A'}...")
    print(f"   Quality: {validation['quality_score']}")


# =============================================================================
# Example 7: Using the LangGraph Worker
# =============================================================================

def example_langgraph_worker():
    """Example: Use metadata extraction worker with LangGraph state."""
    print("\n" + "=" * 70)
    print("Example 7: LangGraph Worker Integration")
    print("=" * 70)
    
    # Create configuration
    config = create_default_config()
    
    # Create initial state
    state = StateManager.create_initial_state(config)
    
    print("\n1. Creating test paper and adding to state...")
    
    # Create paper
    paper = PaperRecord(
        id="worker_test",
        file_path="/path/to/arxiv-2301.12345.pdf",
        filename="arxiv-2301.12345.pdf",
        processing_status="parsed"
    )
    
    # Add to state
    state = StateManager.add_paper(state, paper)
    
    # Add some chunks for abstract extraction
    chunks = [
        PaperChunk(
            paper_id=paper.id,
            chunk_id="chunk_0001",
            section_label="abstract",
            page_start=1,
            page_end=1,
            text="Abstract: This is the paper abstract with important information."
        ),
        PaperChunk(
            paper_id=paper.id,
            chunk_id="chunk_0002",
            section_label="introduction",
            page_start=1,
            page_end=2,
            text="Introduction: The paper begins here..."
        )
    ]
    state = StateManager.add_chunks(state, paper.id, chunks)
    
    print(f"   ✓ Paper added: {paper.id}")
    print(f"   ✓ Chunks added: {len(chunks)}")
    
    print("\n2. Running metadata extraction worker...")
    print("   (Would call APIs and extract metadata)")
    
    # In real usage:
    # state = metadata_extraction_worker(paper.id, state)
    
    # Simulate worker results
    updated_paper = state['papers'][paper.id]
    updated_paper.arxiv_id = "2301.12345"
    updated_paper.title = "Example Paper"
    updated_paper.authors = ["Author One"]
    
    print(f"\n3. Worker completed:")
    print(f"   Paper ID: {updated_paper.id}")
    print(f"   Title: {updated_paper.title}")
    print(f"   Status: {updated_paper.processing_status}")
    
    print("\n4. State Statistics:")
    stats = StateManager.get_stats(state)
    print(f"   Total papers: {stats['total_papers']}")
    print(f"   Total chunks: {stats['total_chunks']}")


# =============================================================================
# Main Example Runner
# =============================================================================

def run_all_examples():
    """Run all Phase 4 examples."""
    print("\n" + "=" * 70)
    print("PHASE 4: METADATA EXTRACTION - USAGE EXAMPLES")
    print("=" * 70)
    
    example_arxiv_extraction()
    example_doi_extraction()
    example_pdf_metadata()
    example_abstract_extraction()
    example_metadata_validation()
    example_complete_pipeline()
    example_langgraph_worker()
    
    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 70)
    print("\nNote: Some examples show mock data. In real usage:")
    print("  - API calls require internet access")
    print("  - PDF extraction requires PyMuPDF and actual PDF files")
    print("  - See metadata_extractor.py for full implementation")
    print("=" * 70)


if __name__ == "__main__":
    run_all_examples()
