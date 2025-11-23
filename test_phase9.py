#!/usr/bin/env python3
"""
Test suite for Phase 9: Taxonomy Review and Approval

Tests all functionality in taxonomy_review.py including:
- Displaying taxonomy for review
- Sample paper extraction
- Approval interface creation
- Processing approval decisions
- Saving approved taxonomy
- Taxonomy editing tools (label editing, paper reassignment, merging, splitting)
- LangGraph worker integration

Note: Tests use mock data and don't require external dependencies.
"""

import sys
from pathlib import Path
import json
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    PaperRecord,
    TopicNode,
    TopicHierarchy,
    StateManager,
    create_default_config,
)

# Import Phase 9 module
try:
    from taxonomy_review import (
        # Step 9.1
        TaxonomyReviewer,
        display_taxonomy_for_review,
        get_sample_papers_for_topic,
        format_topic_hierarchy,
        
        # Step 9.2
        ApprovalDecision,
        create_approval_interface,
        process_approval_decision,
        
        # Step 9.3
        export_taxonomy_to_json,
        update_state_with_approval,
        save_approved_taxonomy,
        
        # Step 9.4
        TaxonomyEditor,
        edit_topic_label,
        edit_topic_description,
        reassign_paper_to_topic,
        merge_topics,
        split_topic,
        
        # Worker
        taxonomy_review_worker,
    )
    TAXONOMY_REVIEW_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import taxonomy_review module: {e}")
    TAXONOMY_REVIEW_AVAILABLE = False


# =============================================================================
# Test Data Helpers
# =============================================================================

def create_mock_papers(n_papers: int = 20) -> dict:
    """Create mock papers for testing."""
    papers = {}
    for i in range(n_papers):
        paper_id = f"paper_{i:03d}"
        papers[paper_id] = PaperRecord(
            id=paper_id,
            file_path=f"/path/to/paper_{i}.pdf",
            filename=f"paper_{i}.pdf",
            title=f"Research Paper {i}: Topic Analysis",
            abstract_text=f"This paper explores topic {i % 5}.",
            authors=[f"Author {i}A", f"Author {i}B"],
            year=2020 + (i % 5),
            processing_status="classified"
        )
    return papers


def create_mock_taxonomy() -> TopicHierarchy:
    """Create a mock 3-tier taxonomy for testing."""
    # Tier 1 topics
    tier1_topics = [
        TopicNode(
            id="T1_00",
            label="Machine Learning",
            description="Research on machine learning algorithms and applications",
            paper_ids=[f"paper_{i:03d}" for i in range(0, 10)],
            parent_id=None
        ),
        TopicNode(
            id="T1_01",
            label="Natural Language Processing",
            description="Studies in natural language understanding and generation",
            paper_ids=[f"paper_{i:03d}" for i in range(10, 20)],
            parent_id=None
        ),
    ]
    
    # Tier 2 topics
    tier2_topics = [
        TopicNode(
            id="T2_00",
            label="Deep Learning",
            description="Neural network architectures and training",
            paper_ids=[f"paper_{i:03d}" for i in range(0, 5)],
            parent_id="T1_00"
        ),
        TopicNode(
            id="T2_01",
            label="Reinforcement Learning",
            description="Agent-based learning through interaction",
            paper_ids=[f"paper_{i:03d}" for i in range(5, 10)],
            parent_id="T1_00"
        ),
        TopicNode(
            id="T2_02",
            label="Text Generation",
            description="Language model based text synthesis",
            paper_ids=[f"paper_{i:03d}" for i in range(10, 15)],
            parent_id="T1_01"
        ),
        TopicNode(
            id="T2_03",
            label="Machine Translation",
            description="Automated translation between languages",
            paper_ids=[f"paper_{i:03d}" for i in range(15, 20)],
            parent_id="T1_01"
        ),
    ]
    
    # Tier 3 topics
    tier3_topics = [
        TopicNode(
            id="T3_00",
            label="Convolutional Networks",
            description="CNN architectures for vision tasks",
            paper_ids=[f"paper_{i:03d}" for i in range(0, 3)],
            parent_id="T2_00"
        ),
        TopicNode(
            id="T3_01",
            label="Recurrent Networks",
            description="RNN and LSTM models",
            paper_ids=[f"paper_{i:03d}" for i in range(3, 5)],
            parent_id="T2_00"
        ),
    ]
    
    hierarchy = TopicHierarchy(
        taxonomy_version="v1.0_test",
        created_at=datetime.now(),
        notes="Test taxonomy for Phase 9",
        total_papers=20,
        tier1=tier1_topics,
        tier2=tier2_topics,
        tier3=tier3_topics,
        clustering_method="kmeans",
        labeling_model="gpt-5.1-mini"
    )
    
    return hierarchy


# =============================================================================
# Step 9.1 Tests: Display Taxonomy for Review
# =============================================================================

def test_taxonomy_reviewer_initialization():
    """Test TaxonomyReviewer initialization."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    papers = create_mock_papers()
    
    reviewer = TaxonomyReviewer(hierarchy, papers)
    
    assert reviewer.hierarchy == hierarchy
    assert reviewer.papers == papers
    print("✓ test_taxonomy_reviewer_initialization passed")


def test_get_sample_papers():
    """Test getting sample papers for a topic."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    papers = create_mock_papers()
    
    reviewer = TaxonomyReviewer(hierarchy, papers)
    topic = hierarchy.tier1[0]
    
    samples = reviewer.get_sample_papers(topic, n_samples=3)
    
    assert len(samples) == 3
    assert all('paper_id' in s for s in samples)
    assert all('title' in s for s in samples)
    assert all('authors' in s for s in samples)
    print("✓ test_get_sample_papers passed")


def test_format_tier1_topic():
    """Test formatting Tier 1 topic for display."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    papers = create_mock_papers()
    
    reviewer = TaxonomyReviewer(hierarchy, papers)
    topic = hierarchy.tier1[0]
    
    formatted = reviewer.format_tier1_topic(topic)
    
    assert topic.id in formatted
    assert topic.label in formatted
    assert topic.description in formatted
    assert "Sample Papers:" in formatted
    assert "Tier 2 Sub-topics" in formatted
    print("✓ test_format_tier1_topic passed")


def test_display_complete_taxonomy():
    """Test displaying complete taxonomy."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    papers = create_mock_papers()
    
    reviewer = TaxonomyReviewer(hierarchy, papers)
    display = reviewer.display_complete_taxonomy()
    
    assert "TAXONOMY REVIEW" in display
    assert hierarchy.taxonomy_version in display
    assert "TIER 1 TOPICS" in display
    assert all(t.label in display for t in hierarchy.tier1)
    print("✓ test_display_complete_taxonomy passed")


def test_display_taxonomy_for_review():
    """Test display_taxonomy_for_review function."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    papers = create_mock_papers()
    
    # Test full display
    display = display_taxonomy_for_review(hierarchy, papers)
    assert "TAXONOMY REVIEW" in display
    assert len(display) > 100
    
    # Test tier-specific display
    tier1_display = display_taxonomy_for_review(hierarchy, papers, tier=1)
    assert "Tier 1" in tier1_display
    
    print("✓ test_display_taxonomy_for_review passed")


def test_format_topic_hierarchy():
    """Test formatting taxonomy as nested dict."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    
    formatted = format_topic_hierarchy(hierarchy)
    
    assert 'version' in formatted
    assert 'tiers' in formatted
    assert len(formatted['tiers']) == len(hierarchy.tier1)
    assert all('children' in tier for tier in formatted['tiers'])
    print("✓ test_format_topic_hierarchy passed")


# =============================================================================
# Step 9.2 Tests: Approval Interface
# =============================================================================

def test_approval_decision_creation():
    """Test creating ApprovalDecision."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    decision = ApprovalDecision(
        action="approve",
        notes="Looks good!",
        edit_instructions={'T1_00': {'label': 'New Label'}}
    )
    
    assert decision.action == "approve"
    assert decision.notes == "Looks good!"
    assert 'T1_00' in decision.edit_instructions
    assert isinstance(decision.timestamp, datetime)
    
    # Test to_dict
    decision_dict = decision.to_dict()
    assert 'action' in decision_dict
    assert 'timestamp' in decision_dict
    print("✓ test_approval_decision_creation passed")


def test_create_approval_interface():
    """Test creating approval interface text."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    
    interface = create_approval_interface(hierarchy)
    
    assert "TAXONOMY APPROVAL INTERFACE" in interface
    assert "APPROVE" in interface
    assert "REGENERATE" in interface
    assert "EDIT LABELS" in interface
    assert hierarchy.taxonomy_version in interface
    print("✓ test_create_approval_interface passed")


def test_process_approval_decision():
    """Test processing various approval decisions."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    state = StateManager.create_initial_state(create_default_config())
    
    # Test approve
    decision = process_approval_decision("approve", hierarchy, state)
    assert decision.action == "approve"
    
    # Test regenerate
    decision = process_approval_decision("regenerate_tier1", hierarchy, state, notes="Need more clusters")
    assert decision.action == "regenerate_tier1"
    assert decision.notes == "Need more clusters"
    
    # Test edit labels
    edits = {'T1_00': {'label': 'New Label'}}
    decision = process_approval_decision("edit_labels", hierarchy, state, edit_instructions=edits)
    assert decision.action == "edit_labels"
    assert len(decision.edit_instructions) > 0
    
    # Test invalid decision
    decision = process_approval_decision("invalid_action", hierarchy, state)
    assert decision.action == "reject"
    
    print("✓ test_process_approval_decision passed")


# =============================================================================
# Step 9.3 Tests: Save Approved Taxonomy
# =============================================================================

def test_export_taxonomy_to_json():
    """Test exporting taxonomy to JSON file."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "taxonomy.json"
        
        saved_path = export_taxonomy_to_json(hierarchy, str(output_path))
        
        assert Path(saved_path).exists()
        
        # Load and verify
        with open(saved_path, 'r') as f:
            data = json.load(f)
        
        assert 'taxonomy_version' in data
        assert 'tier1' in data
        assert 'export_metadata' in data
        assert len(data['tier1']) == len(hierarchy.tier1)
    
    print("✓ test_export_taxonomy_to_json passed")


def test_update_state_with_approval():
    """Test updating state with approval information."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    state = StateManager.create_initial_state(create_default_config())
    
    approval = ApprovalDecision(action="approve", notes="Approved")
    
    updated_state = update_state_with_approval(state, hierarchy, approval)
    
    assert updated_state['taxonomy_approved'] == True
    assert 'taxonomy_approval_timestamp' in updated_state
    assert updated_state['current_phase'] == 'taxonomy_approved'
    assert updated_state['topic_hierarchy'] == hierarchy
    
    print("✓ test_update_state_with_approval passed")


def test_save_approved_taxonomy():
    """Test saving approved taxonomy with full metadata."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    state = StateManager.create_initial_state(create_default_config())
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "approved_taxonomy.json"
        
        results = save_approved_taxonomy(
            hierarchy,
            str(output_path),
            state,
            approval_notes="Approved after review"
        )
        
        assert 'json_path' in results
        assert Path(results['json_path']).exists()
        assert results['version'] == hierarchy.taxonomy_version
        assert results['total_topics'] == len(hierarchy.tier1) + len(hierarchy.tier2) + len(hierarchy.tier3)
    
    print("✓ test_save_approved_taxonomy passed")


# =============================================================================
# Step 9.4 Tests: Editing Tools
# =============================================================================

def test_taxonomy_editor_initialization():
    """Test TaxonomyEditor initialization."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    editor = TaxonomyEditor(hierarchy)
    
    assert editor.hierarchy == hierarchy
    assert len(editor.edit_history) == 0
    print("✓ test_taxonomy_editor_initialization passed")


def test_edit_topic_label():
    """Test editing topic label and description."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    editor = TaxonomyEditor(hierarchy)
    
    topic_id = "T1_00"
    old_label = hierarchy.get_topic_by_id(topic_id).label
    new_label = "Advanced Machine Learning"
    new_description = "New description for the topic"
    
    success = editor.edit_topic_label(topic_id, new_label, new_description)
    
    assert success == True
    assert hierarchy.get_topic_by_id(topic_id).label == new_label
    assert hierarchy.get_topic_by_id(topic_id).description == new_description
    assert len(editor.edit_history) == 1
    assert editor.edit_history[0]['action'] == 'edit_label'
    
    # Test standalone function
    success = edit_topic_label(hierarchy, "T1_01", "NLP and Language")
    assert success == True
    
    print("✓ test_edit_topic_label passed")


def test_reassign_paper():
    """Test reassigning paper between topics."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    editor = TaxonomyEditor(hierarchy)
    
    paper_id = "paper_000"
    from_topic_id = "T1_00"
    to_topic_id = "T1_01"
    
    from_topic = hierarchy.get_topic_by_id(from_topic_id)
    to_topic = hierarchy.get_topic_by_id(to_topic_id)
    
    initial_from_count = from_topic.paper_count
    initial_to_count = to_topic.paper_count
    
    success = editor.reassign_paper(paper_id, from_topic_id, to_topic_id)
    
    assert success == True
    assert from_topic.paper_count == initial_from_count - 1
    assert to_topic.paper_count == initial_to_count + 1
    assert paper_id not in from_topic.paper_ids
    assert paper_id in to_topic.paper_ids
    assert len(editor.edit_history) == 1
    
    # Test standalone function
    success = reassign_paper_to_topic(hierarchy, "paper_001", from_topic_id, to_topic_id)
    assert success == True
    
    print("✓ test_reassign_paper passed")


def test_merge_topics():
    """Test merging two topics."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    editor = TaxonomyEditor(hierarchy)
    
    topic_id1 = "T2_00"
    topic_id2 = "T2_01"
    
    topic1 = hierarchy.get_topic_by_id(topic_id1)
    topic2 = hierarchy.get_topic_by_id(topic_id2)
    
    initial_count1 = topic1.paper_count
    initial_count2 = topic2.paper_count
    
    merged_id = editor.merge_topics(
        topic_id1,
        topic_id2,
        new_label="Merged Learning Topics"
    )
    
    assert merged_id == topic_id1
    merged_topic = hierarchy.get_topic_by_id(merged_id)
    assert merged_topic.paper_count == initial_count1 + initial_count2
    assert hierarchy.get_topic_by_id(topic_id2) is None
    assert len(editor.edit_history) == 1
    
    # Test standalone function
    merged_id = merge_topics(hierarchy, "T2_02", "T2_03", "Combined NLP")
    assert merged_id is not None
    
    print("✓ test_merge_topics passed")


def test_split_topic():
    """Test splitting a topic into multiple topics."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    
    topic_id = "T1_00"
    topic = hierarchy.get_topic_by_id(topic_id)
    
    # Split into 2 groups
    paper_groups = [
        topic.paper_ids[:5],
        topic.paper_ids[5:]
    ]
    new_labels = ["ML Subtopic 1", "ML Subtopic 2"]
    new_descriptions = ["Description 1", "Description 2"]
    
    initial_tier1_count = len(hierarchy.tier1)
    
    new_ids = split_topic(hierarchy, topic_id, paper_groups, new_labels, new_descriptions)
    
    assert len(new_ids) == 2
    assert hierarchy.get_topic_by_id(topic_id) is None  # Original removed
    assert len(hierarchy.tier1) == initial_tier1_count + 1  # 2 added - 1 removed
    
    # Verify new topics
    for new_id, label in zip(new_ids, new_labels):
        new_topic = hierarchy.get_topic_by_id(new_id)
        assert new_topic is not None
        assert new_topic.label == label
    
    print("✓ test_split_topic passed")


def test_edit_history():
    """Test edit history tracking."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    editor = TaxonomyEditor(hierarchy)
    
    # Perform multiple edits
    editor.edit_topic_label("T1_00", "New Label 1")
    editor.reassign_paper("paper_000", "T1_00", "T1_01")
    editor.merge_topics("T2_00", "T2_01")
    
    history = editor.get_edit_history()
    
    assert len(history) == 3
    assert history[0]['action'] == 'edit_label'
    assert history[1]['action'] == 'reassign_paper'
    assert history[2]['action'] == 'merge_topics'
    assert all('timestamp' in h for h in history)
    
    print("✓ test_edit_history passed")


# =============================================================================
# Worker Tests
# =============================================================================

def test_taxonomy_review_worker_auto_approve():
    """Test taxonomy review worker with auto-approve."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    papers = create_mock_papers()
    state = StateManager.create_initial_state(create_default_config())
    state['topic_hierarchy'] = hierarchy
    state['papers'] = papers
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "taxonomy.json"
        
        updated_state = taxonomy_review_worker(
            state,
            auto_approve=True,
            output_path=str(output_path)
        )
        
        assert updated_state['taxonomy_approved'] == True
        assert updated_state['current_phase'] == 'taxonomy_approved'
        assert Path(output_path).exists()
    
    print("✓ test_taxonomy_review_worker_auto_approve passed")


def test_taxonomy_review_worker_manual():
    """Test taxonomy review worker without auto-approve."""
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_mock_taxonomy()
    papers = create_mock_papers()
    state = StateManager.create_initial_state(create_default_config())
    state['topic_hierarchy'] = hierarchy
    state['papers'] = papers
    
    updated_state = taxonomy_review_worker(state, auto_approve=False)
    
    assert updated_state['current_phase'] == 'taxonomy_review_pending'
    assert updated_state['taxonomy_approved'] == False
    
    print("✓ test_taxonomy_review_worker_manual passed")


# =============================================================================
# Run All Tests
# =============================================================================

def run_all_tests():
    """Run all Phase 9 tests."""
    print("\n" + "=" * 80)
    print("Running Phase 9 Tests: Taxonomy Review and Approval")
    print("=" * 80 + "\n")
    
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("ERROR: taxonomy_review module not available")
        return
    
    # Step 9.1 tests
    print("\n--- Step 9.1: Display Taxonomy for Review ---")
    test_taxonomy_reviewer_initialization()
    test_get_sample_papers()
    test_format_tier1_topic()
    test_display_complete_taxonomy()
    test_display_taxonomy_for_review()
    test_format_topic_hierarchy()
    
    # Step 9.2 tests
    print("\n--- Step 9.2: Approval Interface ---")
    test_approval_decision_creation()
    test_create_approval_interface()
    test_process_approval_decision()
    
    # Step 9.3 tests
    print("\n--- Step 9.3: Save Approved Taxonomy ---")
    test_export_taxonomy_to_json()
    test_update_state_with_approval()
    test_save_approved_taxonomy()
    
    # Step 9.4 tests
    print("\n--- Step 9.4: Editing Tools ---")
    test_taxonomy_editor_initialization()
    test_edit_topic_label()
    test_reassign_paper()
    test_merge_topics()
    test_split_topic()
    test_edit_history()
    
    # Worker tests
    print("\n--- Worker Tests ---")
    test_taxonomy_review_worker_auto_approve()
    test_taxonomy_review_worker_manual()
    
    print("\n" + "=" * 80)
    print("All Phase 9 tests completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
