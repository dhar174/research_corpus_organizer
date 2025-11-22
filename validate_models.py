#!/usr/bin/env python3
"""
Validation script for RAG models.

This script tests that all data models can be instantiated,
serialized, and validated correctly.
"""

import sys
from datetime import datetime, date
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    RunConfig,
    PaperRecord,
    PaperChunk,
    TopicNode,
    TopicHierarchy,
    GraphState,
    StateManager,
    MetadataExtractor,
    StatisticsTracker,
    ErrorHandler,
    IDGenerator,
    create_default_config,
    validate_paper_record,
)


def test_run_config():
    """Test RunConfig model."""
    print("Testing RunConfig...")
    
    # Create with defaults
    config = RunConfig()
    assert config.drive_folder_path == "PDFs"
    
    # Create with custom values
    config = create_default_config(
        drive_folder_path="my_pdfs",
        max_papers_per_run=10,
        summary_model="gpt-4-turbo-preview"
    )
    assert config.drive_folder_path == "my_pdfs"
    assert config.max_papers_per_run == 10
    
    # Test serialization
    config_dict = config.to_dict()
    assert isinstance(config_dict, dict)
    
    # Test deserialization
    config2 = RunConfig.from_dict(config_dict)
    assert config2.drive_folder_path == config.drive_folder_path
    
    # Test display
    display = config.display_config()
    assert "RAG PDF System Configuration" in display
    
    print("✓ RunConfig tests passed")


def test_paper_record():
    """Test PaperRecord model."""
    print("Testing PaperRecord...")
    
    # Create a paper record
    paper = PaperRecord(
        id="test123",
        file_path="/path/to/paper.pdf",
        filename="paper.pdf",
        title="Test Paper",
        authors=["Author One", "Author Two"],
        year=2024,
        publish_date=date(2024, 1, 15)
    )
    
    assert paper.id == "test123"
    assert paper.title == "Test Paper"
    assert len(paper.authors) == 2
    assert paper.processing_status == "pending"
    
    # Test confidence validation
    paper.tier1_confidence = 0.95
    assert paper.tier1_confidence == 0.95
    
    try:
        paper.tier1_confidence = 1.5
        assert False, "Should have raised validation error"
    except ValueError:
        pass
    
    # Test serialization
    paper_dict = paper.to_dict()
    assert isinstance(paper_dict, dict)
    assert paper_dict['id'] == "test123"
    
    # Test deserialization
    paper2 = PaperRecord.from_dict(paper_dict)
    assert paper2.id == paper.id
    assert paper2.title == paper.title
    
    # Test validation
    validation = validate_paper_record(paper)
    assert validation['valid']
    
    print("✓ PaperRecord tests passed")


def test_paper_chunk():
    """Test PaperChunk model."""
    print("Testing PaperChunk...")
    
    # Create a chunk
    chunk = PaperChunk(
        paper_id="test123",
        chunk_id="test123_chunk_0001",
        section_label="introduction",
        page_start=1,
        page_end=2,
        text="This is a test chunk with some content."
    )
    
    assert chunk.paper_id == "test123"
    assert chunk.section_label == "introduction"
    assert chunk.char_count > 0
    
    # Test serialization
    chunk_dict = chunk.to_dict()
    assert isinstance(chunk_dict, dict)
    
    # Test deserialization
    chunk2 = PaperChunk.from_dict(chunk_dict)
    assert chunk2.chunk_id == chunk.chunk_id
    
    # Test display text
    display = chunk.get_display_text(max_chars=20)
    assert len(display) <= 23  # 20 chars + "..."
    
    print("✓ PaperChunk tests passed")


def test_topic_hierarchy():
    """Test TopicHierarchy and TopicNode models."""
    print("Testing TopicHierarchy...")
    
    # Create topic nodes
    t1 = TopicNode(
        id="T1_AI",
        label="Artificial Intelligence",
        description="Broad AI research",
        paper_ids=["p1", "p2", "p3"]
    )
    
    assert t1.paper_count == 3
    
    t2 = TopicNode(
        id="T2_AI_ML",
        label="Machine Learning",
        description="ML within AI",
        parent_id="T1_AI",
        paper_ids=["p1", "p2"]
    )
    
    t3 = TopicNode(
        id="T3_AI_ML_Deep",
        label="Deep Learning",
        description="Deep learning methods",
        parent_id="T2_AI_ML",
        paper_ids=["p1"]
    )
    
    # Create hierarchy
    hierarchy = TopicHierarchy(
        taxonomy_version="v1.0",
        total_papers=3,
        tier1=[t1],
        tier2=[t2],
        tier3=[t3],
        clustering_method="agglomerative",
        labeling_model="gpt-4"
    )
    
    # Test hierarchy methods
    assert len(hierarchy.get_tier1_topics()) == 1
    assert len(hierarchy.get_tier2_topics()) == 1
    assert len(hierarchy.get_tier3_topics()) == 1
    
    # Test topic lookup
    found = hierarchy.get_topic_by_id("T1_AI")
    assert found is not None
    assert found.label == "Artificial Intelligence"
    
    # Test validation
    validation = hierarchy.validate_hierarchy()
    assert validation['valid']
    assert validation['tier1_count'] == 1
    
    # Test statistics
    stats = hierarchy.get_statistics()
    assert stats['total_topics'] == 3
    
    # Test serialization
    hier_dict = hierarchy.to_dict()
    assert isinstance(hier_dict, dict)
    
    # Test deserialization
    hierarchy2 = TopicHierarchy.from_dict(hier_dict)
    assert hierarchy2.taxonomy_version == hierarchy.taxonomy_version
    
    print("✓ TopicHierarchy tests passed")


def test_graph_state():
    """Test GraphState and StateManager."""
    print("Testing GraphState and StateManager...")
    
    # Create initial state
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    assert state['current_phase'] == "initialization"
    assert len(state['papers']) == 0
    
    # Add a paper
    paper = PaperRecord(
        id="test123",
        file_path="/path/to/paper.pdf",
        filename="paper.pdf"
    )
    state = StateManager.add_paper(state, paper)
    assert len(state['papers']) == 1
    assert "test123" in state['papers_pending']
    
    # Update paper
    state = StateManager.update_paper(state, "test123", {
        "title": "Updated Title",
        "processing_status": "parsed"
    })
    assert state['papers']["test123"].title == "Updated Title"
    
    # Add chunks
    chunks = [
        PaperChunk(
            paper_id="test123",
            chunk_id="test123_chunk_0001",
            section_label="abstract",
            page_start=1,
            page_end=1,
            text="Abstract text"
        )
    ]
    state = StateManager.add_chunks(state, "test123", chunks)
    assert len(state['chunks']["test123"]) == 1
    
    # Mark complete
    state = StateManager.mark_paper_complete(state, "test123")
    assert "test123" in state['papers_completed']
    assert "test123" not in state['papers_pending']
    
    # Get statistics
    stats = StateManager.get_stats(state)
    assert stats['total_papers'] == 1
    assert stats['completed'] == 1
    
    print("✓ GraphState and StateManager tests passed")


def test_helper_classes():
    """Test helper classes."""
    print("Testing helper classes...")
    
    # Test MetadataExtractor
    arxiv_id = MetadataExtractor.extract_arxiv_id("paper_2301.12345.pdf")
    assert arxiv_id == "2301.12345"
    
    authors = MetadataExtractor.normalize_authors(["  John Doe  ", "Jane Smith"])
    assert len(authors) == 2
    assert authors[0] == "John Doe"
    
    # Test StatisticsTracker
    text = "This is a test text with some content."
    stats = StatisticsTracker.calculate_text_stats(text, page_count=1)
    assert stats['pages'] == 1
    assert stats['chars_total'] > 0
    assert 'parse_quality_score' in stats
    
    tokens = StatisticsTracker.estimate_tokens(text)
    assert tokens > 0
    
    # Test ErrorHandler
    handler = ErrorHandler()
    handler.log_error(
        "test123",
        "parsing",
        ValueError("Test error"),
        {"detail": "test"}
    )
    assert len(handler.errors) == 1
    
    errors = handler.get_errors_by_paper("test123")
    assert len(errors) == 1
    
    # Test IDGenerator
    paper_id = IDGenerator.generate_paper_id("/path/to/file.pdf")
    assert len(paper_id) == 16
    
    chunk_id = IDGenerator.generate_chunk_id(paper_id, 5)
    assert "chunk_0005" in chunk_id
    
    topic_id = IDGenerator.generate_topic_id(1, "Machine Learning", 0)
    assert topic_id.startswith("T1_")
    
    print("✓ Helper classes tests passed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("RAG Models Validation")
    print("=" * 60)
    print()
    
    try:
        test_run_config()
        test_paper_record()
        test_paper_chunk()
        test_topic_hierarchy()
        test_graph_state()
        test_helper_classes()
        
        print()
        print("=" * 60)
        print("✓ All validation tests passed!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Validation failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
