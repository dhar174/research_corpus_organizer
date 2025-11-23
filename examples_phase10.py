#!/usr/bin/env python3
"""
Phase 10 Usage Examples: Final Topic Classification

This file demonstrates how to use the paper_classification module for various use cases.

Examples include:
- Building classification prompts
- Classifying individual papers with GPT-5.1
- Batch classification with rate limiting
- Validating classifications
- Updating paper records
- Complete classification workflow

All examples use mock data for demonstration purposes.
"""

import sys
from pathlib import Path
import tempfile
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    PaperRecord,
    TopicNode,
    TopicHierarchy,
    StateManager,
    create_default_config,
)

try:
    from paper_classification import (
        format_taxonomy_for_prompt,
        build_classification_prompt,
        PaperClassifier,
        classify_paper_node,
        classify_papers_with_rate_limit,
        batch_classify_papers,
        check_tier_consistency,
        validate_paper_classification,
        validate_all_classifications,
        update_paper_with_classification,
        update_papers_batch,
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
    """Create a sample taxonomy for examples."""
    tier1_topics = [
        TopicNode(
            id="T1_00",
            label="Machine Learning",
            description="Research on machine learning algorithms, deep learning, and applications",
            paper_ids=[f"paper_{i:03d}" for i in range(0, 15)],
            parent_id=None
        ),
        TopicNode(
            id="T1_01",
            label="Natural Language Processing",
            description="Studies in text analysis, language understanding, and generation",
            paper_ids=[f"paper_{i:03d}" for i in range(15, 30)],
            parent_id=None
        ),
    ]
    
    tier2_topics = [
        TopicNode(
            id="T2_00",
            label="Deep Learning",
            description="Neural network architectures and optimization",
            paper_ids=[f"paper_{i:03d}" for i in range(0, 8)],
            parent_id="T1_00"
        ),
        TopicNode(
            id="T2_01",
            label="Transfer Learning",
            description="Pre-training and fine-tuning strategies",
            paper_ids=[f"paper_{i:03d}" for i in range(8, 15)],
            parent_id="T1_00"
        ),
        TopicNode(
            id="T2_02",
            label="Language Models",
            description="Transformer-based language understanding",
            paper_ids=[f"paper_{i:03d}" for i in range(15, 22)],
            parent_id="T1_01"
        ),
        TopicNode(
            id="T2_03",
            label="Text Generation",
            description="Neural text synthesis and creative AI",
            paper_ids=[f"paper_{i:03d}" for i in range(22, 30)],
            parent_id="T1_01"
        ),
    ]
    
    tier3_topics = [
        TopicNode(
            id="T3_00",
            label="Convolutional Networks",
            description="CNN architectures for vision and sequence tasks",
            paper_ids=[f"paper_{i:03d}" for i in range(0, 4)],
            parent_id="T2_00"
        ),
        TopicNode(
            id="T3_01",
            label="Attention Mechanisms",
            description="Self-attention and cross-attention methods",
            paper_ids=[f"paper_{i:03d}" for i in range(4, 8)],
            parent_id="T2_00"
        ),
    ]
    
    return TopicHierarchy(
        taxonomy_version="v1.0_20251123",
        created_at=datetime.now(),
        notes="Sample taxonomy for demonstration",
        total_papers=30,
        tier1=tier1_topics,
        tier2=tier2_topics,
        tier3=tier3_topics,
        clustering_method="kmeans",
        labeling_model="gpt-5.1-mini"
    )


def create_sample_paper(paper_id="paper_001", topic="Machine Learning"):
    """Create sample papers."""
    return PaperRecord(
        id=paper_id,
        file_path=f"/papers/{paper_id}.pdf",
        filename=f"{paper_id}.pdf",
        title=f"{topic} Research: Study {paper_id}",
        abstract_text=f"This paper investigates {topic.lower()} with focus on novel techniques and applications.",
        full_summary=f"We propose new methods in {topic.lower()} that improve performance on benchmark tasks.",
        authors=[f"Author {paper_id}A", f"Author {paper_id}B"],
        year=2024,
        processing_status="embedded"
    )


# =============================================================================
# Example 1: Format Taxonomy for Prompts
# =============================================================================

def example_1_format_taxonomy():
    """Example 1: Format taxonomy structure for classification prompts."""
    print("\n" + "=" * 80)
    print("Example 1: Format Taxonomy for Prompts")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    hierarchy = create_sample_taxonomy()
    
    # Format taxonomy
    taxonomy_str = format_taxonomy_for_prompt(hierarchy)
    
    print("\n--- Formatted Taxonomy Structure ---")
    print(taxonomy_str[:500] + "...\n")
    
    print(f"Total length: {len(taxonomy_str)} characters")
    print(f"Includes all tiers: 1, 2, 3")
    print(f"Shows topic IDs, labels, descriptions, paper counts")
    
    print("\n✓ Example 1 complete: Taxonomy formatted for prompt")


# =============================================================================
# Example 2: Build Classification Prompt
# =============================================================================

def example_2_build_prompt():
    """Example 2: Build complete classification prompt for GPT-5.1."""
    print("\n" + "=" * 80)
    print("Example 2: Build Classification Prompt")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    hierarchy = create_sample_taxonomy()
    paper = create_sample_paper()
    
    # Build prompt
    prompt = build_classification_prompt(
        paper=paper,
        hierarchy=hierarchy,
        reasoning_effort="medium"
    )
    
    print("\n--- Classification Prompt ---")
    print(prompt[:600] + "...\n")
    
    print(f"Prompt includes:")
    print(f"  - Complete taxonomy structure")
    print(f"  - Paper title, authors, year, venue")
    print(f"  - Abstract and summary text")
    print(f"  - Classification instructions for all 3 tiers")
    print(f"  - JSON output format specification")
    print(f"  - Confidence score requirements")
    print(f"Total prompt length: {len(prompt)} characters")
    
    print("\n✓ Example 2 complete: Classification prompt built")


# =============================================================================
# Example 3: Classify Single Paper (Mocked)
# =============================================================================

def example_3_classify_paper():
    """Example 3: Classify a single paper using GPT-5.1 (mocked)."""
    print("\n" + "=" * 80)
    print("Example 3: Classify Single Paper")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    hierarchy = create_sample_taxonomy()
    paper = create_sample_paper()
    
    print(f"\nPaper to classify:")
    print(f"  ID: {paper.id}")
    print(f"  Title: {paper.title}")
    
    # Note: In real usage, you would use:
    # classifier = PaperClassifier(api_key=your_api_key)
    # classification = classifier.classify_paper(paper, hierarchy)
    
    # For this example, we'll simulate the response
    classification = {
        "tier1": {
            "topic_id": "T1_00",
            "confidence": 0.92,
            "reasoning": "Paper focuses on machine learning algorithms and neural network architectures."
        },
        "tier2": {
            "topic_id": "T2_00",
            "confidence": 0.88,
            "reasoning": "Specifically addresses deep learning methods and optimization techniques."
        },
        "tier3": {
            "topic_id": "T3_00",
            "confidence": 0.85,
            "reasoning": "Implements convolutional neural network architectures for the task."
        },
        "overall_notes": "Strong fit for Machine Learning > Deep Learning > Convolutional Networks taxonomy path."
    }
    
    print(f"\nClassification result:")
    print(f"  Tier 1: {classification['tier1']['topic_id']} (confidence: {classification['tier1']['confidence']})")
    print(f"    Reasoning: {classification['tier1']['reasoning']}")
    print(f"  Tier 2: {classification['tier2']['topic_id']} (confidence: {classification['tier2']['confidence']})")
    print(f"    Reasoning: {classification['tier2']['reasoning']}")
    print(f"  Tier 3: {classification['tier3']['topic_id']} (confidence: {classification['tier3']['confidence']})")
    print(f"    Reasoning: {classification['tier3']['reasoning']}")
    print(f"  Overall: {classification['overall_notes']}")
    
    print("\n✓ Example 3 complete: Paper classified")


# =============================================================================
# Example 4: Update Paper with Classification
# =============================================================================

def example_4_update_paper():
    """Example 4: Update paper record with classification results."""
    print("\n" + "=" * 80)
    print("Example 4: Update Paper with Classification")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    paper = create_sample_paper()
    
    print(f"\nBefore classification:")
    print(f"  Tier 1 topic: {paper.tier1_topic}")
    print(f"  Processing status: {paper.processing_status}")
    
    # Classification result
    classification = {
        "tier1": {
            "topic_id": "T1_00",
            "confidence": 0.92,
            "reasoning": "ML focus"
        },
        "tier2": {
            "topic_id": "T2_00",
            "confidence": 0.88,
            "reasoning": "DL methods"
        },
        "tier3": {
            "topic_id": "T3_00",
            "confidence": 0.85,
            "reasoning": "CNN arch"
        },
        "overall_notes": "Good fit"
    }
    
    # Update paper
    updated_paper = update_paper_with_classification(
        paper=paper,
        classification=classification,
        taxonomy_version="v1.0_20251123"
    )
    
    print(f"\nAfter classification:")
    print(f"  Tier 1: {updated_paper.tier1_topic} (confidence: {updated_paper.tier1_confidence})")
    print(f"  Tier 2: {updated_paper.tier2_topic} (confidence: {updated_paper.tier2_confidence})")
    print(f"  Tier 3: {updated_paper.tier3_topic} (confidence: {updated_paper.tier3_confidence})")
    print(f"  Taxonomy version: {updated_paper.taxonomy_version}")
    print(f"  Processing status: {updated_paper.processing_status}")
    print(f"  Classification notes: {updated_paper.classification_notes[:100]}...")
    
    print("\n✓ Example 4 complete: Paper updated with classification")


# =============================================================================
# Example 5: Validate Classifications
# =============================================================================

def example_5_validate():
    """Example 5: Validate paper classifications."""
    print("\n" + "=" * 80)
    print("Example 5: Validate Classifications")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    hierarchy = create_sample_taxonomy()
    
    # Create a valid classified paper
    paper1 = create_sample_paper("paper_001")
    paper1.tier1_topic = "T1_00"
    paper1.tier1_confidence = 0.9
    paper1.tier2_topic = "T2_00"
    paper1.tier2_confidence = 0.85
    paper1.tier3_topic = "T3_00"
    paper1.tier3_confidence = 0.8
    paper1.taxonomy_version = "v1.0_20251123"
    paper1.processing_status = "classified"
    
    # Validate
    validation1 = validate_paper_classification(paper1, hierarchy)
    
    print(f"\nPaper 1 validation:")
    print(f"  Valid: {validation1['valid']}")
    print(f"  Issues: {validation1['issues'] if validation1['issues'] else 'None'}")
    
    # Create an invalid classified paper (wrong parent)
    paper2 = create_sample_paper("paper_002")
    paper2.tier1_topic = "T1_00"
    paper2.tier1_confidence = 0.8
    paper2.tier2_topic = "T2_02"  # This is under T1_01, not T1_00!
    paper2.tier2_confidence = 0.7
    paper2.tier3_topic = "T3_00"
    paper2.tier3_confidence = 0.6
    paper2.taxonomy_version = "v1.0_20251123"
    paper2.processing_status = "classified"
    
    validation2 = validate_paper_classification(paper2, hierarchy)
    
    print(f"\nPaper 2 validation:")
    print(f"  Valid: {validation2['valid']}")
    print(f"  Issues: {validation2['issues']}")
    
    print("\n✓ Example 5 complete: Classifications validated")


# =============================================================================
# Example 6: Check Tier Consistency
# =============================================================================

def example_6_tier_consistency():
    """Example 6: Check tier consistency for classifications."""
    print("\n" + "=" * 80)
    print("Example 6: Check Tier Consistency")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    hierarchy = create_sample_taxonomy()
    
    # Check valid path
    print("\n--- Valid Tier Path ---")
    is_valid, issues = check_tier_consistency("T1_00", "T2_00", "T3_00", hierarchy)
    print(f"T1_00 -> T2_00 -> T3_00")
    print(f"  Valid: {is_valid}")
    print(f"  Issues: {issues if issues else 'None'}")
    
    # Check invalid path (wrong parent)
    print("\n--- Invalid Tier Path (Wrong Parent) ---")
    is_valid, issues = check_tier_consistency("T1_00", "T2_02", "T3_00", hierarchy)
    print(f"T1_00 -> T2_02 -> T3_00")
    print(f"  Valid: {is_valid}")
    print(f"  Issues: {issues}")
    
    # Check invalid path (non-existent topic)
    print("\n--- Invalid Tier Path (Non-existent Topic) ---")
    is_valid, issues = check_tier_consistency("T1_00", "T2_00", "T3_99", hierarchy)
    print(f"T1_00 -> T2_00 -> T3_99")
    print(f"  Valid: {is_valid}")
    print(f"  Issues: {issues}")
    
    print("\n✓ Example 6 complete: Tier consistency checked")


# =============================================================================
# Example 7: Batch Validate All Papers
# =============================================================================

def example_7_validate_all():
    """Example 7: Validate all paper classifications."""
    print("\n" + "=" * 80)
    print("Example 7: Validate All Classifications")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    hierarchy = create_sample_taxonomy()
    
    # Create a mix of papers
    papers = {}
    
    # Valid papers
    for i in range(5):
        paper = create_sample_paper(f"paper_{i:03d}")
        paper.tier1_topic = "T1_00"
        paper.tier1_confidence = 0.9 - (i * 0.05)
        paper.tier2_topic = "T2_00"
        paper.tier2_confidence = 0.85
        paper.tier3_topic = "T3_00"
        paper.tier3_confidence = 0.8
        paper.taxonomy_version = "v1.0_20251123"
        paper.processing_status = "classified"
        papers[f"paper_{i:03d}"] = paper
    
    # Invalid paper
    paper_invalid = create_sample_paper("paper_invalid")
    paper_invalid.tier1_topic = "T1_00"
    paper_invalid.tier2_topic = "T2_02"  # Wrong parent
    paper_invalid.tier3_topic = "T3_00"
    paper_invalid.taxonomy_version = "v1.0_20251123"
    paper_invalid.processing_status = "classified"
    papers["paper_invalid"] = paper_invalid
    
    # Unclassified paper
    papers["paper_unclassified"] = create_sample_paper("paper_unclassified")
    
    # Validate all
    results = validate_all_classifications(papers, hierarchy)
    
    print(f"\nValidation summary:")
    print(f"  Total papers: {results['total_papers']}")
    print(f"  Classified: {results['classified_count']}")
    print(f"  Valid: {results['valid_count']}")
    print(f"  Invalid: {results['invalid_count']}")
    print(f"  Unclassified: {results['unclassified_count']}")
    print(f"  Anomalies (low confidence): {len(results['anomalies'])}")
    
    if results['anomalies']:
        print(f"\nAnomaly details:")
        for anomaly in results['anomalies']:
            print(f"  {anomaly['paper_id']}: {anomaly['reason']} (conf: {anomaly['confidence']})")
    
    print("\n✓ Example 7 complete: All classifications validated")


# =============================================================================
# Example 8: Batch Update Papers
# =============================================================================

def example_8_batch_update():
    """Example 8: Update multiple papers with classifications."""
    print("\n" + "=" * 80)
    print("Example 8: Batch Update Papers")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    # Create unclassified papers
    papers = {
        f"paper_{i:03d}": create_sample_paper(f"paper_{i:03d}")
        for i in range(5)
    }
    
    # Simulated classifications
    classifications = {
        "paper_000": {
            "tier1": {"topic_id": "T1_00", "confidence": 0.9, "reasoning": "ML"},
            "tier2": {"topic_id": "T2_00", "confidence": 0.85, "reasoning": "DL"},
            "tier3": {"topic_id": "T3_00", "confidence": 0.8, "reasoning": "CNN"},
            "overall_notes": "Good fit"
        },
        "paper_001": {
            "tier1": {"topic_id": "T1_01", "confidence": 0.88, "reasoning": "NLP"},
            "tier2": {"topic_id": "T2_02", "confidence": 0.82, "reasoning": "LM"},
            "tier3": {"topic_id": "T3_01", "confidence": 0.75, "reasoning": "Attn"},
            "overall_notes": "Good fit"
        },
        "paper_002": {
            "tier1": {"topic_id": "T1_00", "confidence": 0.92, "reasoning": "ML"},
            "tier2": {"topic_id": "T2_01", "confidence": 0.87, "reasoning": "Transfer"},
            "tier3": {"topic_id": "T3_00", "confidence": 0.79, "reasoning": "CNN"},
            "overall_notes": "Good fit"
        }
    }
    
    print(f"\nBefore update:")
    for pid in ["paper_000", "paper_001", "paper_002"]:
        paper = papers[pid]
        print(f"  {pid}: tier1={paper.tier1_topic}, status={paper.processing_status}")
    
    # Batch update
    updated_papers = update_papers_batch(
        papers=papers,
        classifications=classifications,
        taxonomy_version="v1.0_20251123"
    )
    
    print(f"\nAfter update:")
    for pid in ["paper_000", "paper_001", "paper_002"]:
        paper = updated_papers[pid]
        print(f"  {pid}: tier1={paper.tier1_topic}, conf={paper.tier1_confidence}, status={paper.processing_status}")
    
    print("\n✓ Example 8 complete: Papers batch updated")


# =============================================================================
# Example 9: Complete Classification Workflow
# =============================================================================

def example_9_complete_workflow():
    """Example 9: Complete classification workflow with state."""
    print("\n" + "=" * 80)
    print("Example 9: Complete Classification Workflow")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("SKIP: paper_classification not available")
        return
    
    # Create state
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    # Add taxonomy
    hierarchy = create_sample_taxonomy()
    state['topic_hierarchy'] = hierarchy
    state['taxonomy_approved'] = True
    
    # Add papers
    papers = {
        f"paper_{i:03d}": create_sample_paper(f"paper_{i:03d}")
        for i in range(3)
    }
    state['papers'] = papers
    
    print("\n--- Step 1: Initial State ---")
    print(f"Papers: {len(state['papers'])}")
    print(f"Taxonomy: {hierarchy.taxonomy_version}")
    print(f"Unclassified papers: {sum(1 for p in papers.values() if not p.tier1_topic)}")
    
    print("\n--- Step 2: Classification (simulated) ---")
    # In real usage: state = classification_worker(state, api_key)
    # For demo, manually classify
    for pid, paper in state['papers'].items():
        classification = {
            "tier1": {"topic_id": "T1_00", "confidence": 0.9, "reasoning": "ML"},
            "tier2": {"topic_id": "T2_00", "confidence": 0.85, "reasoning": "DL"},
            "tier3": {"topic_id": "T3_00", "confidence": 0.8, "reasoning": "CNN"},
            "overall_notes": "Good"
        }
        state['papers'][pid] = update_paper_with_classification(
            paper, classification, hierarchy.taxonomy_version
        )
    
    print(f"Classified {len(papers)} papers")
    
    print("\n--- Step 3: Validation ---")
    validation = validate_all_classifications(state['papers'], hierarchy)
    print(f"Valid: {validation['valid_count']}/{validation['classified_count']}")
    print(f"Invalid: {validation['invalid_count']}")
    
    print("\n--- Step 4: Review Results ---")
    for pid, paper in state['papers'].items():
        print(f"{pid}:")
        print(f"  Classification: {paper.tier1_topic} -> {paper.tier2_topic} -> {paper.tier3_topic}")
        print(f"  Confidence: {paper.tier1_confidence:.2f}, {paper.tier2_confidence:.2f}, {paper.tier3_confidence:.2f}")
        print(f"  Status: {paper.processing_status}")
    
    print("\n✓ Example 9 complete: Full workflow executed")


# =============================================================================
# Run All Examples
# =============================================================================

def run_all_examples():
    """Run all Phase 10 examples."""
    print("\n" + "=" * 80)
    print("Phase 10 Usage Examples: Final Topic Classification")
    print("=" * 80)
    
    if not CLASSIFICATION_AVAILABLE:
        print("\nERROR: paper_classification module not available")
        print("Please ensure paper_classification.py is in the same directory")
        return
    
    example_1_format_taxonomy()
    example_2_build_prompt()
    example_3_classify_paper()
    example_4_update_paper()
    example_5_validate()
    example_6_tier_consistency()
    example_7_validate_all()
    example_8_batch_update()
    example_9_complete_workflow()
    
    print("\n" + "=" * 80)
    print("All examples completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_examples()
