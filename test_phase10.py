#!/usr/bin/env python3
"""
Test suite for Phase 10: Final Topic Classification

Tests all functionality in paper_classification.py including:
- Classification prompt building
- Paper classification with GPT-5.1 (mocked)
- Batch classification with rate limiting
- Classification validation
- Paper record updates
- LangGraph worker integration

Note: Tests use mock data and mocked API calls to avoid external dependencies.
"""

import sys
from pathlib import Path
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    PaperRecord,
    TopicNode,
    TopicHierarchy,
    StateManager,
    create_default_config,
)

# Import Phase 10 module
try:
    from paper_classification import (
        # Step 10.2
        format_taxonomy_for_prompt,
        build_classification_prompt,
        
        # Step 10.1
        PaperClassifier,
        classify_paper_node,
        
        # Step 10.3
        classify_papers_with_rate_limit,
        batch_classify_papers,
        
        # Step 10.4
        check_tier_consistency,
        validate_paper_classification,
        validate_all_classifications,
        
        # Step 10.5
        update_paper_with_classification,
        update_papers_batch,
        
        # Worker
        classification_worker,
    )
    CLASSIFICATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: paper_classification module not available: {e}")
    CLASSIFICATION_AVAILABLE = False


# =============================================================================
# Helper Functions
# =============================================================================

def create_sample_taxonomy():
    """Create a sample taxonomy for testing."""
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
            description="Studies in text analysis and language understanding",
            paper_ids=[f"paper_{i:03d}" for i in range(10, 20)],
            parent_id=None
        ),
    ]
    
    tier2_topics = [
        TopicNode(
            id="T2_00",
            label="Deep Learning",
            description="Neural network architectures and optimization",
            paper_ids=[f"paper_{i:03d}" for i in range(0, 5)],
            parent_id="T1_00"
        ),
        TopicNode(
            id="T2_01",
            label="Transfer Learning",
            description="Pre-training and fine-tuning strategies",
            paper_ids=[f"paper_{i:03d}" for i in range(5, 10)],
            parent_id="T1_00"
        ),
        TopicNode(
            id="T2_02",
            label="Language Models",
            description="Transformer-based language understanding",
            paper_ids=[f"paper_{i:03d}" for i in range(10, 15)],
            parent_id="T1_01"
        ),
        TopicNode(
            id="T2_03",
            label="Text Generation",
            description="Neural text synthesis",
            paper_ids=[f"paper_{i:03d}" for i in range(15, 20)],
            parent_id="T1_01"
        ),
    ]
    
    tier3_topics = [
        TopicNode(
            id="T3_00",
            label="Convolutional Networks",
            description="CNN architectures",
            paper_ids=[f"paper_{i:03d}" for i in range(0, 3)],
            parent_id="T2_00"
        ),
        TopicNode(
            id="T3_01",
            label="Attention Mechanisms",
            description="Self-attention and cross-attention",
            paper_ids=[f"paper_{i:03d}" for i in range(3, 5)],
            parent_id="T2_00"
        ),
    ]
    
    return TopicHierarchy(
        taxonomy_version="v1.0_test",
        created_at=datetime.now(),
        notes="Test taxonomy",
        total_papers=20,
        tier1=tier1_topics,
        tier2=tier2_topics,
        tier3=tier3_topics,
        clustering_method="kmeans",
        labeling_model="gpt-5.1-mini"
    )


def create_sample_paper(paper_id="paper_001"):
    """Create a sample paper for testing."""
    return PaperRecord(
        id=paper_id,
        file_path=f"/papers/{paper_id}.pdf",
        filename=f"{paper_id}.pdf",
        title="Deep Learning for Natural Language Processing",
        abstract_text="This paper investigates deep learning methods for NLP tasks.",
        full_summary="We propose a novel neural architecture for text understanding.",
        authors=["Author A", "Author B"],
        year=2024,
        processing_status="embedded"
    )


# =============================================================================
# Step 10.2: Classification Prompts Tests
# =============================================================================

def test_format_taxonomy_for_prompt():
    """Test formatting taxonomy for prompt."""
    print("\n" + "=" * 80)
    print("Test: format_taxonomy_for_prompt")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    hierarchy = create_sample_taxonomy()
    
    # Format taxonomy
    formatted = format_taxonomy_for_prompt(hierarchy)
    
    # Check structure
    assert "TAXONOMY STRUCTURE" in formatted
    assert "TIER 1: T1_00 - Machine Learning" in formatted
    assert "TIER 2: T2_00 - Deep Learning" in formatted
    assert "TIER 3: T3_00 - Convolutional Networks" in formatted
    assert "Description:" in formatted
    assert "Paper count:" in formatted
    
    print(f"✓ Formatted taxonomy ({len(formatted)} chars)")
    print(f"  Contains all tiers: Tier 1, 2, 3")
    print(f"  Sample:\n{formatted[:300]}...")


def test_build_classification_prompt():
    """Test building classification prompt."""
    print("\n" + "=" * 80)
    print("Test: build_classification_prompt")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    hierarchy = create_sample_taxonomy()
    paper = create_sample_paper()
    
    # Build prompt
    prompt = build_classification_prompt(paper, hierarchy, reasoning_effort="medium")
    
    # Check prompt contents
    assert "TAXONOMY STRUCTURE" in prompt
    assert paper.title in prompt
    assert "Title:" in prompt
    assert "Authors:" in prompt
    assert "Abstract:" in prompt
    assert "Summary:" in prompt
    assert "Tier 1 (Broad Topic)" in prompt
    assert "Tier 2 (Mid-Level Topic)" in prompt
    assert "Tier 3 (Fine-Grained Topic)" in prompt
    assert "JSON format" in prompt
    assert '"tier1"' in prompt
    assert '"confidence"' in prompt
    
    print(f"✓ Built classification prompt ({len(prompt)} chars)")
    print(f"  Includes: taxonomy, paper info, instructions")
    print(f"  Sample:\n{prompt[:200]}...")


# =============================================================================
# Step 10.1: Classification Node Tests
# =============================================================================

def test_paper_classifier_mock():
    """Test PaperClassifier with mocked API."""
    print("\n" + "=" * 80)
    print("Test: PaperClassifier (mocked)")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    hierarchy = create_sample_taxonomy()
    paper = create_sample_paper()
    
    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({
        "tier1": {
            "topic_id": "T1_00",
            "confidence": 0.9,
            "reasoning": "Paper focuses on deep learning methods"
        },
        "tier2": {
            "topic_id": "T2_00",
            "confidence": 0.85,
            "reasoning": "Specifically about deep neural networks"
        },
        "tier3": {
            "topic_id": "T3_00",
            "confidence": 0.8,
            "reasoning": "Uses convolutional architectures"
        },
        "overall_notes": "Strong fit for ML/Deep Learning/CNN topic"
    })
    
    with patch('paper_classification.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create classifier
        classifier = PaperClassifier(
            api_key="test-key",
            model="gpt-5.1-mini",
            reasoning_effort="medium"
        )
        
        # Classify paper
        classification = classifier.classify_paper(paper, hierarchy)
        
        # Verify classification
        assert "tier1" in classification
        assert classification["tier1"]["topic_id"] == "T1_00"
        assert classification["tier1"]["confidence"] == 0.9
        assert "tier2" in classification
        assert "tier3" in classification
        
        print(f"✓ PaperClassifier successfully classified paper")
        print(f"  Tier 1: {classification['tier1']['topic_id']} (conf: {classification['tier1']['confidence']})")
        print(f"  Tier 2: {classification['tier2']['topic_id']} (conf: {classification['tier2']['confidence']})")
        print(f"  Tier 3: {classification['tier3']['topic_id']} (conf: {classification['tier3']['confidence']})")


def test_classify_paper_node_mock():
    """Test classify_paper_node function."""
    print("\n" + "=" * 80)
    print("Test: classify_paper_node")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    # Create state
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    hierarchy = create_sample_taxonomy()
    paper = create_sample_paper()
    
    state['topic_hierarchy'] = hierarchy
    state['papers'] = {paper.id: paper}
    
    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({
        "tier1": {"topic_id": "T1_00", "confidence": 0.9, "reasoning": "ML focus"},
        "tier2": {"topic_id": "T2_00", "confidence": 0.85, "reasoning": "DL methods"},
        "tier3": {"topic_id": "T3_00", "confidence": 0.8, "reasoning": "CNN arch"},
        "overall_notes": "Good fit"
    })
    
    with patch('paper_classification.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Classify
        updated_state = classify_paper_node(paper.id, state, "test-key")
        
        # Verify paper was updated
        updated_paper = updated_state['papers'][paper.id]
        assert updated_paper.tier1_topic == "T1_00"
        assert updated_paper.tier1_confidence == 0.9
        assert updated_paper.tier2_topic == "T2_00"
        assert updated_paper.tier3_topic == "T3_00"
        assert updated_paper.processing_status == "classified"
        
        print(f"✓ classify_paper_node successfully updated paper")
        print(f"  Paper {paper.id} classified to {updated_paper.tier1_topic}")


# =============================================================================
# Step 10.3: Batch Classification Tests
# =============================================================================

def test_classify_papers_with_rate_limit_mock():
    """Test batch classification with rate limiting."""
    print("\n" + "=" * 80)
    print("Test: classify_papers_with_rate_limit")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    hierarchy = create_sample_taxonomy()
    config = create_default_config()
    
    # Create multiple papers
    papers = {
        f"paper_{i:03d}": create_sample_paper(f"paper_{i:03d}")
        for i in range(5)
    }
    
    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({
        "tier1": {"topic_id": "T1_00", "confidence": 0.9, "reasoning": "ML"},
        "tier2": {"topic_id": "T2_00", "confidence": 0.85, "reasoning": "DL"},
        "tier3": {"topic_id": "T3_00", "confidence": 0.8, "reasoning": "CNN"},
        "overall_notes": "Good"
    })
    
    with patch('paper_classification.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch('paper_classification.time.sleep'):  # Skip actual sleep in tests
            # Classify all papers
            classifications = classify_papers_with_rate_limit(
                papers=papers,
                hierarchy=hierarchy,
                api_key="test-key",
                config=config,
                rate_limit_delay=0.1
            )
            
            # Verify all classified
            assert len(classifications) == len(papers)
            
            for paper_id, classification in classifications.items():
                assert "tier1" in classification
                assert classification["tier1"]["topic_id"] == "T1_00"
            
            print(f"✓ Batch classified {len(classifications)} papers")
            print(f"  All papers classified to T1_00")


def test_batch_classify_papers_mock():
    """Test batch_classify_papers function."""
    print("\n" + "=" * 80)
    print("Test: batch_classify_papers")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    # Create state
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    hierarchy = create_sample_taxonomy()
    
    # Create papers
    papers = {
        f"paper_{i:03d}": create_sample_paper(f"paper_{i:03d}")
        for i in range(3)
    }
    
    state['topic_hierarchy'] = hierarchy
    state['papers'] = papers
    
    # Mock OpenAI
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({
        "tier1": {"topic_id": "T1_00", "confidence": 0.9, "reasoning": "ML"},
        "tier2": {"topic_id": "T2_00", "confidence": 0.85, "reasoning": "DL"},
        "tier3": {"topic_id": "T3_00", "confidence": 0.8, "reasoning": "CNN"},
        "overall_notes": "Good"
    })
    
    with patch('paper_classification.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch('paper_classification.time.sleep'):
            # Batch classify
            updated_state = batch_classify_papers(state, "test-key")
            
            # Verify all papers classified
            for paper_id, paper in updated_state['papers'].items():
                assert paper.tier1_topic == "T1_00"
                assert paper.processing_status == "classified"
            
            print(f"✓ Batch classified {len(papers)} papers in state")


# =============================================================================
# Step 10.4: Validation Tests
# =============================================================================

def test_check_tier_consistency():
    """Test tier consistency checking."""
    print("\n" + "=" * 80)
    print("Test: check_tier_consistency")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    hierarchy = create_sample_taxonomy()
    
    # Test valid consistency
    is_valid, issues = check_tier_consistency("T1_00", "T2_00", "T3_00", hierarchy)
    assert is_valid
    assert len(issues) == 0
    print(f"✓ Valid tier consistency: T1_00 -> T2_00 -> T3_00")
    
    # Test invalid: wrong parent
    is_valid, issues = check_tier_consistency("T1_00", "T2_02", "T3_00", hierarchy)
    assert not is_valid
    assert len(issues) > 0
    print(f"✓ Invalid tier consistency detected: {issues[0]}")
    
    # Test invalid: non-existent topic
    is_valid, issues = check_tier_consistency("T1_00", "T2_00", "T3_99", hierarchy)
    assert not is_valid
    assert "not found" in issues[0]
    print(f"✓ Non-existent topic detected: {issues[0]}")


def test_validate_paper_classification():
    """Test single paper classification validation."""
    print("\n" + "=" * 80)
    print("Test: validate_paper_classification")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    hierarchy = create_sample_taxonomy()
    
    # Create classified paper
    paper = create_sample_paper()
    paper.tier1_topic = "T1_00"
    paper.tier1_confidence = 0.9
    paper.tier2_topic = "T2_00"
    paper.tier2_confidence = 0.85
    paper.tier3_topic = "T3_00"
    paper.tier3_confidence = 0.8
    paper.taxonomy_version = "v1.0_test"
    paper.processing_status = "classified"
    
    # Validate
    validation = validate_paper_classification(paper, hierarchy)
    
    assert validation["valid"]
    assert len(validation["issues"]) == 0
    print(f"✓ Paper classification valid")
    
    # Test invalid confidence
    paper.tier1_confidence = 1.5  # Invalid
    validation = validate_paper_classification(paper, hierarchy)
    assert not validation["valid"]
    assert any("confidence" in issue for issue in validation["issues"])
    print(f"✓ Invalid confidence detected: {validation['issues'][0]}")


def test_validate_all_classifications():
    """Test validation of all papers."""
    print("\n" + "=" * 80)
    print("Test: validate_all_classifications")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    hierarchy = create_sample_taxonomy()
    
    # Create mix of valid and invalid papers
    papers = {}
    
    # Valid paper
    paper1 = create_sample_paper("paper_001")
    paper1.tier1_topic = "T1_00"
    paper1.tier1_confidence = 0.9
    paper1.tier2_topic = "T2_00"
    paper1.tier2_confidence = 0.85
    paper1.tier3_topic = "T3_00"
    paper1.tier3_confidence = 0.8
    paper1.taxonomy_version = "v1.0_test"
    paper1.processing_status = "classified"
    papers["paper_001"] = paper1
    
    # Invalid paper (wrong parent)
    paper2 = create_sample_paper("paper_002")
    paper2.tier1_topic = "T1_00"
    paper2.tier1_confidence = 0.8
    paper2.tier2_topic = "T2_02"  # Wrong parent
    paper2.tier2_confidence = 0.7
    paper2.tier3_topic = "T3_00"
    paper2.tier3_confidence = 0.6
    paper2.taxonomy_version = "v1.0_test"
    paper2.processing_status = "classified"
    papers["paper_002"] = paper2
    
    # Unclassified paper
    paper3 = create_sample_paper("paper_003")
    papers["paper_003"] = paper3
    
    # Validate all
    results = validate_all_classifications(papers, hierarchy)
    
    assert results["total_papers"] == 3
    assert results["classified_count"] == 2
    assert results["valid_count"] == 1
    assert results["invalid_count"] == 1
    assert results["unclassified_count"] == 1
    
    print(f"✓ Validated {results['total_papers']} papers")
    print(f"  Valid: {results['valid_count']}")
    print(f"  Invalid: {results['invalid_count']}")
    print(f"  Unclassified: {results['unclassified_count']}")


# =============================================================================
# Step 10.5: Update Paper Records Tests
# =============================================================================

def test_update_paper_with_classification():
    """Test updating paper with classification."""
    print("\n" + "=" * 80)
    print("Test: update_paper_with_classification")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    paper = create_sample_paper()
    
    classification = {
        "tier1": {
            "topic_id": "T1_00",
            "confidence": 0.9,
            "reasoning": "Focuses on machine learning"
        },
        "tier2": {
            "topic_id": "T2_00",
            "confidence": 0.85,
            "reasoning": "Uses deep learning methods"
        },
        "tier3": {
            "topic_id": "T3_00",
            "confidence": 0.8,
            "reasoning": "Implements CNNs"
        },
        "overall_notes": "Strong fit for ML/DL/CNN"
    }
    
    # Update paper
    updated_paper = update_paper_with_classification(
        paper=paper,
        classification=classification,
        taxonomy_version="v1.0_test"
    )
    
    # Verify updates
    assert updated_paper.tier1_topic == "T1_00"
    assert updated_paper.tier1_confidence == 0.9
    assert updated_paper.tier2_topic == "T2_00"
    assert updated_paper.tier2_confidence == 0.85
    assert updated_paper.tier3_topic == "T3_00"
    assert updated_paper.tier3_confidence == 0.8
    assert updated_paper.taxonomy_version == "v1.0_test"
    assert updated_paper.processing_status == "classified"
    assert "Tier 1:" in updated_paper.classification_notes
    assert "Tier 2:" in updated_paper.classification_notes
    
    print(f"✓ Paper updated with classification")
    print(f"  Tier 1: {updated_paper.tier1_topic} (conf: {updated_paper.tier1_confidence})")
    print(f"  Status: {updated_paper.processing_status}")
    print(f"  Notes length: {len(updated_paper.classification_notes)} chars")


def test_update_papers_batch():
    """Test batch updating papers."""
    print("\n" + "=" * 80)
    print("Test: update_papers_batch")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    # Create papers
    papers = {
        f"paper_{i:03d}": create_sample_paper(f"paper_{i:03d}")
        for i in range(3)
    }
    
    # Create classifications
    classifications = {
        "paper_000": {
            "tier1": {"topic_id": "T1_00", "confidence": 0.9, "reasoning": "ML"},
            "tier2": {"topic_id": "T2_00", "confidence": 0.85, "reasoning": "DL"},
            "tier3": {"topic_id": "T3_00", "confidence": 0.8, "reasoning": "CNN"},
            "overall_notes": "Good"
        },
        "paper_001": {
            "tier1": {"topic_id": "T1_01", "confidence": 0.88, "reasoning": "NLP"},
            "tier2": {"topic_id": "T2_02", "confidence": 0.82, "reasoning": "LM"},
            "tier3": {"topic_id": "T3_00", "confidence": 0.75, "reasoning": "Trans"},
            "overall_notes": "Good"
        }
    }
    
    # Update batch
    updated_papers = update_papers_batch(
        papers=papers,
        classifications=classifications,
        taxonomy_version="v1.0_test"
    )
    
    # Verify updates
    assert updated_papers["paper_000"].tier1_topic == "T1_00"
    assert updated_papers["paper_000"].processing_status == "classified"
    assert updated_papers["paper_001"].tier1_topic == "T1_01"
    assert updated_papers["paper_001"].processing_status == "classified"
    assert updated_papers["paper_002"].tier1_topic is None  # Not in classifications
    
    print(f"✓ Batch updated {len(classifications)} papers")
    print(f"  paper_000: {updated_papers['paper_000'].tier1_topic}")
    print(f"  paper_001: {updated_papers['paper_001'].tier1_topic}")
    print(f"  paper_002: {updated_papers['paper_002'].processing_status}")


# =============================================================================
# Worker Tests
# =============================================================================

def test_classification_worker_mock():
    """Test complete classification worker."""
    print("\n" + "=" * 80)
    print("Test: classification_worker")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    # Create state
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    hierarchy = create_sample_taxonomy()
    
    papers = {
        f"paper_{i:03d}": create_sample_paper(f"paper_{i:03d}")
        for i in range(3)
    }
    
    state['topic_hierarchy'] = hierarchy
    state['papers'] = papers
    state['taxonomy_approved'] = True
    
    # Mock OpenAI
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({
        "tier1": {"topic_id": "T1_00", "confidence": 0.9, "reasoning": "ML"},
        "tier2": {"topic_id": "T2_00", "confidence": 0.85, "reasoning": "DL"},
        "tier3": {"topic_id": "T3_00", "confidence": 0.8, "reasoning": "CNN"},
        "overall_notes": "Good"
    })
    
    with patch('paper_classification.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch('paper_classification.time.sleep'):
            # Run worker
            updated_state = classification_worker(state, "test-key", validate=True)
            
            # Verify state updates
            assert updated_state['current_phase'] == 'classification_complete'
            assert 'classification_timestamp' in updated_state
            assert 'classification_validation' in updated_state
            
            # Verify papers classified
            for paper_id, paper in updated_state['papers'].items():
                assert paper.tier1_topic == "T1_00"
                assert paper.processing_status == "classified"
            
            # Verify validation results
            validation = updated_state['classification_validation']
            assert validation['classified_count'] == 3
            assert validation['valid_count'] == 3
            
            print(f"✓ classification_worker completed successfully")
            print(f"  Phase: {updated_state['current_phase']}")
            print(f"  Classified: {validation['classified_count']}")
            print(f"  Valid: {validation['valid_count']}")


# =============================================================================
# Run All Tests
# =============================================================================

def run_all_tests():
    """Run all Phase 10 tests."""
    print("\n" + "=" * 80)
    print("Phase 10 Test Suite: Final Topic Classification")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("\nERROR: paper_classification module not available")
        print("Please ensure paper_classification.py is in the same directory")
        return
    
    # Step 10.2 tests
    test_format_taxonomy_for_prompt()
    test_build_classification_prompt()
    
    # Step 10.1 tests
    test_paper_classifier_mock()
    test_classify_paper_node_mock()
    
    # Step 10.3 tests
    test_classify_papers_with_rate_limit_mock()
    test_batch_classify_papers_mock()
    
    # Step 10.4 tests
    test_check_tier_consistency()
    test_validate_paper_classification()
    test_validate_all_classifications()
    
    # Step 10.5 tests
    test_update_paper_with_classification()
    test_update_papers_batch()
    
    # Worker tests
    test_classification_worker_mock()
    
    print("\n" + "=" * 80)
    print("All Phase 10 tests completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
