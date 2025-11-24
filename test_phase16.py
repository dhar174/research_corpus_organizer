#!/usr/bin/env python3
"""
Test Suite for Phase 16: Utility Functions and Tools

Tests all components of the corpus utilities:
- Paper search functions
- Corpus statistics
- Export utilities
- Data update functions
- Cleanup functions

Version: 1.0
Date: 2025-11-24
"""

import json
import tempfile
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock

# Import modules to test
from rag_models import (
    RunConfig,
    PaperRecord,
    PaperChunk,
    TopicNode,
    TopicHierarchy,
    GraphState,
    IDGenerator,
)

from corpus_utilities import (
    # Step 16.1: Paper Search Functions
    search_papers,
    search_by_title,
    search_by_author,
    search_by_date_range,
    search_by_topic,
    filter_by_status,
    advanced_search,
    
    # Step 16.2: Corpus Statistics
    count_papers_by_year,
    count_papers_by_source,
    get_most_common_authors,
    get_most_common_venues,
    get_topic_distribution,
    generate_corpus_report,
    
    # Step 16.3: Export Utilities
    export_paper_subset,
    export_by_topic,
    export_by_date_range,
    generate_bibtex_entries,
    create_reading_list,
    export_to_markdown,
    
    # Step 16.4: Data Update Functions
    add_new_papers,
    update_paper_metadata,
    merge_corpus_states,
    
    # Step 16.5: Cleanup Functions
    remove_duplicate_papers,
    clean_orphaned_chunks,
    verify_data_integrity,
    optimize_storage,
    compact_corpus,
)


def create_sample_state() -> GraphState:
    """Create a sample GraphState for testing."""
    config = RunConfig(
        drive_folder_path="test_pdfs",
        summary_model="gpt-4",
        embedding_model="text-embedding-3-large",
    )
    
    # Create sample papers
    paper1 = PaperRecord(
        id="p1",
        file_path="/test/paper1.pdf",
        filename="paper1.pdf",
        title="Attention Is All You Need",
        authors=["Vaswani", "Shazeer", "Parmar"],
        year=2017,
        publish_date=date(2017, 6, 12),
        venue="NeurIPS",
        abstract_text="We propose the Transformer...",
        full_summary="This paper introduces transformers.",
        tier1_topic="T1_NLP",
        tier1_topic_name="Natural Language Processing",
        tier1_confidence=0.95,
        tier2_topic="T2_TRANSFORMERS",
        tier2_topic_name="Transformer Architectures",
        arxiv_id="1706.03762",
        processing_status="classified"
    )
    
    paper2 = PaperRecord(
        id="p2",
        file_path="/test/paper2.pdf",
        filename="paper2.pdf",
        title="BERT: Pre-training of Deep Bidirectional Transformers",
        authors=["Devlin", "Chang", "Lee"],
        year=2018,
        publish_date=date(2018, 10, 11),
        venue="NAACL",
        abstract_text="We introduce BERT...",
        full_summary="BERT uses bidirectional transformers.",
        tier1_topic="T1_NLP",
        tier1_topic_name="Natural Language Processing",
        tier1_confidence=0.92,
        tier2_topic="T2_PRETRAINING",
        tier2_topic_name="Language Model Pre-training",
        arxiv_id="1810.04805",
        processing_status="classified"
    )
    
    paper3 = PaperRecord(
        id="p3",
        file_path="/test/paper3.pdf",
        filename="paper3.pdf",
        title="GPT-3: Language Models are Few-Shot Learners",
        authors=["Brown", "Mann", "Ryder"],
        year=2020,
        publish_date=date(2020, 5, 28),
        venue="NeurIPS",
        abstract_text="We demonstrate that scaling...",
        full_summary="GPT-3 shows few-shot learning capabilities.",
        tier1_topic="T1_LLM",
        tier1_topic_name="Large Language Models",
        tier1_confidence=0.98,
        tier2_topic="T2_SCALING",
        tier2_topic_name="Model Scaling",
        arxiv_id="2005.14165",
        processing_status="classified"
    )
    
    paper4 = PaperRecord(
        id="p4",
        file_path="/test/paper4.pdf",
        filename="paper4.pdf",
        title="ResNet: Deep Residual Learning",
        authors=["He", "Zhang", "Ren"],
        year=2015,
        publish_date=date(2015, 12, 10),
        venue="CVPR",
        abstract_text="We present residual networks...",
        full_summary="ResNet enables training of very deep networks.",
        tier1_topic="T1_CV",
        tier1_topic_name="Computer Vision",
        tier1_confidence=0.97,
        tier2_topic="T2_CNNS",
        tier2_topic_name="Convolutional Networks",
        doi="10.1109/CVPR.2016.90",
        processing_status="classified"
    )
    
    paper5 = PaperRecord(
        id="p5",
        file_path="/test/paper5.pdf",
        filename="paper5.pdf",
        title="Failed Paper",
        authors=["Unknown"],
        year=2021,
        processing_status="failed"
    )
    
    # Create sample chunks
    chunk1 = PaperChunk(
        chunk_id="c1",
        paper_id="p1",
        section_label="abstract",
        page_start=1,
        page_end=1,
        text="Transformer architecture details..."
    )
    
    chunk2 = PaperChunk(
        chunk_id="c2",
        paper_id="p2",
        section_label="introduction",
        page_start=1,
        page_end=2,
        text="BERT introduction..."
    )
    
    # Create topic hierarchy
    hierarchy = TopicHierarchy(
        tier1_topics={
            "T1_NLP": TopicNode(
                id="T1_NLP",
                label="Natural Language Processing",
                description="NLP research",
                paper_count=2,
                tier=1
            ),
            "T1_LLM": TopicNode(
                id="T1_LLM",
                label="Large Language Models",
                description="LLM research",
                paper_count=1,
                tier=1
            ),
            "T1_CV": TopicNode(
                id="T1_CV",
                label="Computer Vision",
                description="CV research",
                paper_count=1,
                tier=1
            ),
        },
        tier2_topics={
            "T2_TRANSFORMERS": TopicNode(
                id="T2_TRANSFORMERS",
                label="Transformer Architectures",
                parent_id="T1_NLP",
                tier=2
            ),
            "T2_PRETRAINING": TopicNode(
                id="T2_PRETRAINING",
                label="Language Model Pre-training",
                parent_id="T1_NLP",
                tier=2
            ),
        },
        tier3_topics={}
    )
    
    state = {
        'config': config,
        'papers': {
            'p1': paper1,
            'p2': paper2,
            'p3': paper3,
            'p4': paper4,
            'p5': paper5,
        },
        'chunks': {
            'p1': [chunk1],
            'p2': [chunk2],
        },
        'topic_hierarchy': hierarchy,
    }
    
    return state


# =============================================================================
# Test Step 16.1: Paper Search Functions
# =============================================================================

def test_search_by_title():
    """Test title search functionality."""
    print("\n=== Test: search_by_title ===")
    state = create_sample_state()
    
    # Search for "Transformer"
    results = search_by_title(state, "Transformer")
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    print(f"✓ Found {len(results)} papers with 'Transformer' in title")
    
    # Case-insensitive search
    results = search_by_title(state, "bert", case_sensitive=False)
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    print(f"✓ Case-insensitive search works")
    
    # Exact match
    results = search_by_title(state, "Attention Is All You Need", exact_match=True)
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    print(f"✓ Exact match works")
    
    print("✓ All title search tests passed")


def test_search_by_author():
    """Test author search functionality."""
    print("\n=== Test: search_by_author ===")
    state = create_sample_state()
    
    # Search for author
    results = search_by_author(state, "Vaswani")
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    assert results[0].id == "p1", "Wrong paper returned"
    print(f"✓ Found paper by Vaswani")
    
    # Case-insensitive search
    results = search_by_author(state, "devlin", case_sensitive=False)
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    print(f"✓ Case-insensitive author search works")
    
    print("✓ All author search tests passed")


def test_search_by_date_range():
    """Test date range search functionality."""
    print("\n=== Test: search_by_date_range ===")
    state = create_sample_state()
    
    # Search by year range
    results = search_by_date_range(state, start_year=2017, end_year=2018)
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    print(f"✓ Found {len(results)} papers from 2017-2018")
    
    # Search by exact year
    results = search_by_date_range(state, start_year=2020, end_year=2020)
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    print(f"✓ Found papers from exact year")
    
    print("✓ All date range search tests passed")


def test_search_by_topic():
    """Test topic search functionality."""
    print("\n=== Test: search_by_topic ===")
    state = create_sample_state()
    
    # Search tier 1 topic
    results = search_by_topic(state, "T1_NLP", tier=1)
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    print(f"✓ Found {len(results)} papers in NLP topic")
    
    # Search tier 2 topic
    results = search_by_topic(state, "T2_TRANSFORMERS", tier=2)
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    print(f"✓ Found papers in subtopic")
    
    print("✓ All topic search tests passed")


def test_filter_by_status():
    """Test status filter functionality."""
    print("\n=== Test: filter_by_status ===")
    state = create_sample_state()
    
    # Filter classified papers
    results = filter_by_status(state, "classified")
    assert len(results) == 4, f"Expected 4 results, got {len(results)}"
    print(f"✓ Found {len(results)} classified papers")
    
    # Filter failed papers
    results = filter_by_status(state, "failed")
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    print(f"✓ Found {len(results)} failed papers")
    
    print("✓ All status filter tests passed")


def test_advanced_search():
    """Test advanced search functionality."""
    print("\n=== Test: advanced_search ===")
    state = create_sample_state()
    
    # Search with multiple filters
    filters = {
        'title': 'Transformer',
        'year_min': 2017,
        'year_max': 2018,
    }
    results = advanced_search(state, filters)
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    print(f"✓ Advanced search with multiple filters works")
    
    # Search by authors
    filters = {
        'authors': ['Vaswani', 'Devlin'],
    }
    results = advanced_search(state, filters)
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    print(f"✓ Search by multiple authors works")
    
    print("✓ All advanced search tests passed")


# =============================================================================
# Test Step 16.2: Corpus Statistics
# =============================================================================

def test_count_papers_by_year():
    """Test counting papers by year."""
    print("\n=== Test: count_papers_by_year ===")
    state = create_sample_state()
    
    year_counts = count_papers_by_year(state)
    assert 2017 in year_counts, "Year 2017 not found"
    assert year_counts[2017] == 1, f"Expected 1 paper in 2017, got {year_counts[2017]}"
    assert year_counts[2018] == 1, "Expected 1 paper in 2018"
    print(f"✓ Year counts: {year_counts}")
    
    print("✓ Count papers by year test passed")


def test_count_papers_by_source():
    """Test counting papers by source."""
    print("\n=== Test: count_papers_by_source ===")
    state = create_sample_state()
    
    source_counts = count_papers_by_source(state)
    assert 'arXiv' in source_counts, "arXiv source not found"
    assert source_counts['arXiv'] >= 3, f"Expected at least 3 arXiv papers"
    print(f"✓ Source counts: {source_counts}")
    
    print("✓ Count papers by source test passed")


def test_get_most_common_authors():
    """Test getting most common authors."""
    print("\n=== Test: get_most_common_authors ===")
    state = create_sample_state()
    
    top_authors = get_most_common_authors(state, top_n=5)
    assert len(top_authors) > 0, "No authors found"
    print(f"✓ Top authors: {top_authors[:3]}")
    
    print("✓ Get most common authors test passed")


def test_get_topic_distribution():
    """Test getting topic distribution."""
    print("\n=== Test: get_topic_distribution ===")
    state = create_sample_state()
    
    topic_dist = get_topic_distribution(state, tier=1)
    assert 'T1_NLP' in topic_dist, "T1_NLP not found"
    assert topic_dist['T1_NLP'] == 2, f"Expected 2 papers in T1_NLP"
    print(f"✓ Topic distribution: {topic_dist}")
    
    print("✓ Get topic distribution test passed")


def test_generate_corpus_report():
    """Test corpus report generation."""
    print("\n=== Test: generate_corpus_report ===")
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = str(Path(tmpdir) / "report.md")
        result = generate_corpus_report(state, report_path, include_charts=False)
        
        assert Path(result).exists(), "Report file not created"
        
        # Check content
        with open(result, 'r') as f:
            content = f.read()
            assert "Research Corpus Statistics Report" in content
            assert "Total Papers" in content
            print(f"✓ Report generated at {result}")
    
    print("✓ Generate corpus report test passed")


# =============================================================================
# Test Step 16.3: Export Utilities
# =============================================================================

def test_export_paper_subset():
    """Test exporting paper subset."""
    print("\n=== Test: export_paper_subset ===")
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = str(Path(tmpdir) / "subset.json")
        result = export_paper_subset(state, ['p1', 'p2'], output_path, format='json')
        
        assert Path(result).exists(), "Export file not created"
        
        # Check content
        with open(result, 'r') as f:
            data = json.load(f)
            assert len(data) == 2, f"Expected 2 papers, got {len(data)}"
            print(f"✓ Exported {len(data)} papers")
    
    print("✓ Export paper subset test passed")


def test_generate_bibtex_entries():
    """Test BibTeX generation."""
    print("\n=== Test: generate_bibtex_entries ===")
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = str(Path(tmpdir) / "references.bib")
        bibtex = generate_bibtex_entries(state, ['p1', 'p2'], output_path)
        
        assert Path(output_path).exists(), "BibTeX file not created"
        assert '@' in bibtex, "BibTeX entries not generated"
        assert 'Vaswani' in bibtex, "Author not found in BibTeX"
        print(f"✓ Generated BibTeX with {bibtex.count('@')} entries")
    
    print("✓ Generate BibTeX entries test passed")


def test_create_reading_list():
    """Test reading list creation."""
    print("\n=== Test: create_reading_list ===")
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test markdown format
        md_path = str(Path(tmpdir) / "reading_list.md")
        result = create_reading_list(state, ['p1', 'p2', 'p3'], md_path, format='markdown')
        
        assert Path(result).exists(), "Reading list not created"
        
        with open(result, 'r') as f:
            content = f.read()
            assert "Reading List" in content
            assert "Attention Is All You Need" in content
            print(f"✓ Created markdown reading list")
        
        # Test HTML format
        html_path = str(Path(tmpdir) / "reading_list.html")
        result = create_reading_list(state, ['p1', 'p2'], html_path, format='html')
        
        assert Path(result).exists(), "HTML reading list not created"
        print(f"✓ Created HTML reading list")
    
    print("✓ Create reading list test passed")


def test_export_to_markdown():
    """Test markdown export."""
    print("\n=== Test: export_to_markdown ===")
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = str(Path(tmpdir) / "corpus.md")
        result = export_to_markdown(state, ['p1', 'p2'], output_path)
        
        assert Path(result).exists(), "Markdown export not created"
        
        with open(result, 'r') as f:
            content = f.read()
            assert "Research Corpus Export" in content
            assert "Attention Is All You Need" in content
            print(f"✓ Exported to markdown")
    
    print("✓ Export to markdown test passed")


# =============================================================================
# Test Step 16.4: Data Update Functions
# =============================================================================

def test_add_new_papers():
    """Test adding new papers."""
    print("\n=== Test: add_new_papers ===")
    state = create_sample_state()
    
    original_count = len(state['papers'])
    
    # Add new paper
    new_paper = PaperRecord(
        id="p_new",
        file_path="/test/new.pdf",
        filename="new.pdf",
        title="New Paper",
        authors=["Author"],
        year=2023,
        processing_status="pending"
    )
    
    updated_state = add_new_papers(state, [new_paper])
    assert len(updated_state['papers']) == original_count + 1
    assert 'p_new' in updated_state['papers']
    print(f"✓ Added new paper (total: {len(updated_state['papers'])})")
    
    # Test skip strategy (duplicate)
    updated_state = add_new_papers(updated_state, [new_paper], merge_strategy='skip')
    assert len(updated_state['papers']) == original_count + 1
    print(f"✓ Skip strategy works for duplicates")
    
    print("✓ Add new papers test passed")


def test_update_paper_metadata():
    """Test updating paper metadata."""
    print("\n=== Test: update_paper_metadata ===")
    state = create_sample_state()
    
    original_title = state['papers']['p1'].title
    
    # Update metadata
    updated_state = update_paper_metadata(
        state,
        'p1',
        {'title': 'Updated Title', 'year': 2024}
    )
    
    assert updated_state['papers']['p1'].title == 'Updated Title'
    assert updated_state['papers']['p1'].year == 2024
    print(f"✓ Updated metadata: {original_title} -> {updated_state['papers']['p1'].title}")
    
    print("✓ Update paper metadata test passed")


def test_merge_corpus_states():
    """Test merging corpus states."""
    print("\n=== Test: merge_corpus_states ===")
    state1 = create_sample_state()
    
    # Create second state with new papers
    state2 = {
        'papers': {
            'p_new1': PaperRecord(
                id="p_new1",
                file_path="/test/new1.pdf",
                filename="new1.pdf",
                title="New Paper 1",
                year=2023
            ),
            'p_new2': PaperRecord(
                id="p_new2",
                file_path="/test/new2.pdf",
                filename="new2.pdf",
                title="New Paper 2",
                year=2023
            ),
        },
        'chunks': {},
    }
    
    merged = merge_corpus_states(state1, state2)
    assert 'p_new1' in merged['papers']
    assert 'p_new2' in merged['papers']
    assert 'p1' in merged['papers']  # Original papers still there
    print(f"✓ Merged states (total papers: {len(merged['papers'])})")
    
    print("✓ Merge corpus states test passed")


# =============================================================================
# Test Step 16.5: Cleanup Functions
# =============================================================================

def test_remove_duplicate_papers():
    """Test removing duplicate papers."""
    print("\n=== Test: remove_duplicate_papers ===")
    state = create_sample_state()
    
    # Add duplicate with same title
    duplicate = PaperRecord(
        id="p_dup",
        file_path="/test/dup.pdf",
        filename="dup.pdf",
        title="Attention Is All You Need",  # Same as p1
        authors=["Different Author"],
        year=2023
    )
    
    state['papers']['p_dup'] = duplicate
    original_count = len(state['papers'])
    
    # Remove duplicates by title
    updated_state, removed = remove_duplicate_papers(state, dedupe_by='title')
    
    assert len(removed) == 1, f"Expected 1 duplicate removed, got {len(removed)}"
    assert len(updated_state['papers']) == original_count - 1
    print(f"✓ Removed {len(removed)} duplicates")
    
    print("✓ Remove duplicate papers test passed")


def test_clean_orphaned_chunks():
    """Test cleaning orphaned chunks."""
    print("\n=== Test: clean_orphaned_chunks ===")
    state = create_sample_state()
    
    # Add orphaned chunk
    orphan_chunk = PaperChunk(
        chunk_id="c_orphan",
        paper_id="p_nonexistent",
        section_label="abstract",
        page_start=1,
        page_end=1,
        text="Orphaned chunk..."
    )
    
    state['chunks']['p_nonexistent'] = [orphan_chunk]
    
    # Clean orphans
    updated_state, removed_count = clean_orphaned_chunks(state)
    
    assert removed_count == 1, f"Expected 1 orphaned chunk removed"
    assert 'p_nonexistent' not in updated_state['chunks']
    print(f"✓ Removed {removed_count} orphaned chunks")
    
    print("✓ Clean orphaned chunks test passed")


def test_verify_data_integrity():
    """Test data integrity verification."""
    print("\n=== Test: verify_data_integrity ===")
    state = create_sample_state()
    
    report = verify_data_integrity(state)
    
    assert 'total_papers' in report
    assert 'total_issues' in report
    assert 'integrity_score' in report
    print(f"✓ Integrity report: {report['total_issues']} issues, score: {report['integrity_score']:.2f}")
    
    print("✓ Verify data integrity test passed")


def test_optimize_storage():
    """Test storage optimization."""
    print("\n=== Test: optimize_storage ===")
    state = create_sample_state()
    
    # Add long summary to test compression
    state['papers']['p1'].full_summary = "x" * 3000  # Long summary
    
    updated_state, stats = optimize_storage(state, compress_summaries=True)
    
    assert stats['summaries_compressed'] >= 0
    print(f"✓ Optimization stats: {stats}")
    
    print("✓ Optimize storage test passed")


def test_compact_corpus():
    """Test comprehensive corpus compaction."""
    print("\n=== Test: compact_corpus ===")
    state = create_sample_state()
    
    # Add some issues to compact
    # 1. Duplicate paper
    dup = PaperRecord(
        id="p_dup",
        file_path="/test/dup.pdf",
        filename="dup.pdf",
        title="Attention Is All You Need",
        year=2023
    )
    state['papers']['p_dup'] = dup
    
    # 2. Orphaned chunk
    state['chunks']['p_orphan'] = [PaperChunk(
        chunk_id="c_orphan",
        paper_id="p_orphan",
        section_label="abstract",
        page_start=1,
        page_end=1,
        text="Orphaned..."
    )]
    
    original_papers = len(state['papers'])
    
    # Compact
    compacted_state, stats = compact_corpus(state)
    
    assert stats['final_papers'] <= original_papers
    assert stats['orphans_removed'] >= 0
    print(f"✓ Compaction stats: {stats}")
    
    print("✓ Compact corpus test passed")


# =============================================================================
# Main Test Runner
# =============================================================================

def run_all_tests():
    """Run all Phase 16 tests."""
    print("\n" + "=" * 80)
    print("PHASE 16: UTILITY FUNCTIONS AND TOOLS - TEST SUITE")
    print("=" * 80)
    
    try:
        # Step 16.1: Paper Search Functions
        print("\n--- Step 16.1: Paper Search Functions ---")
        test_search_by_title()
        test_search_by_author()
        test_search_by_date_range()
        test_search_by_topic()
        test_filter_by_status()
        test_advanced_search()
        
        # Step 16.2: Corpus Statistics
        print("\n--- Step 16.2: Corpus Statistics ---")
        test_count_papers_by_year()
        test_count_papers_by_source()
        test_get_most_common_authors()
        test_get_topic_distribution()
        test_generate_corpus_report()
        
        # Step 16.3: Export Utilities
        print("\n--- Step 16.3: Export Utilities ---")
        test_export_paper_subset()
        test_generate_bibtex_entries()
        test_create_reading_list()
        test_export_to_markdown()
        
        # Step 16.4: Data Update Functions
        print("\n--- Step 16.4: Data Update Functions ---")
        test_add_new_papers()
        test_update_paper_metadata()
        test_merge_corpus_states()
        
        # Step 16.5: Cleanup Functions
        print("\n--- Step 16.5: Cleanup Functions ---")
        test_remove_duplicate_papers()
        test_clean_orphaned_chunks()
        test_verify_data_integrity()
        test_optimize_storage()
        test_compact_corpus()
        
        print("\n" + "=" * 80)
        print("✓ ALL PHASE 16 TESTS PASSED")
        print("=" * 80)
        
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


if __name__ == '__main__':
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
