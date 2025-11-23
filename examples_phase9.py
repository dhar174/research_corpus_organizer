#!/usr/bin/env python3
"""
Phase 9 Usage Examples: Taxonomy Review and Approval

This file demonstrates how to use the taxonomy_review module for various use cases.

Examples include:
- Displaying taxonomy for review
- Creating approval interfaces
- Processing user approval decisions
- Saving approved taxonomies
- Editing topic labels
- Reassigning papers between topics
- Merging and splitting topics
- Complete review workflow

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
    from taxonomy_review import (
        display_taxonomy_for_review,
        create_approval_interface,
        process_approval_decision,
        save_approved_taxonomy,
        edit_topic_label,
        reassign_paper_to_topic,
        merge_topics,
        split_topic,
        TaxonomyReviewer,
        TaxonomyEditor,
    )
    TAXONOMY_REVIEW_AVAILABLE = True
except ImportError as e:
    print(f"Warning: taxonomy_review module not available: {e}")
    TAXONOMY_REVIEW_AVAILABLE = False


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
        taxonomy_version="v1.0_20251122",
        created_at=datetime.now(),
        notes="Sample taxonomy for demonstration",
        total_papers=30,
        tier1=tier1_topics,
        tier2=tier2_topics,
        tier3=tier3_topics,
        clustering_method="kmeans",
        labeling_model="gpt-5.1-mini"
    )


def create_sample_papers(n=30):
    """Create sample papers."""
    papers = {}
    topics = [
        "Machine Learning", "Deep Learning", "Neural Networks",
        "NLP", "Text Generation", "Language Models",
        "Computer Vision", "Reinforcement Learning"
    ]
    
    for i in range(n):
        paper_id = f"paper_{i:03d}"
        topic = topics[i % len(topics)]
        papers[paper_id] = PaperRecord(
            id=paper_id,
            file_path=f"/papers/paper_{i}.pdf",
            filename=f"paper_{i}.pdf",
            title=f"{topic} Research: Study {i}",
            abstract_text=f"This paper investigates {topic.lower()} with focus on novel techniques.",
            authors=[f"Author {i}A", f"Author {i}B"],
            year=2020 + (i % 5),
            processing_status="embedded"
        )
    return papers


# =============================================================================
# Example 1: Display Taxonomy for Review
# =============================================================================

def example_1_display_taxonomy():
    """Example 1: Display complete taxonomy for human review."""
    print("\n" + "=" * 80)
    print("Example 1: Display Taxonomy for Review")
    print("=" * 80)
    
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_sample_taxonomy()
    papers = create_sample_papers()
    
    # Display complete taxonomy
    print("\n--- Full Taxonomy Display ---")
    review_text = display_taxonomy_for_review(hierarchy, papers)
    print(review_text[:1000] + "...\n")  # Print first 1000 chars
    
    # Display specific tier
    print("\n--- Tier 1 Summary ---")
    tier1_summary = display_taxonomy_for_review(hierarchy, papers, tier=1)
    print(tier1_summary[:500] + "...\n")
    
    print("✓ Example 1 complete: Taxonomy displayed for review")


# =============================================================================
# Example 2: Create Approval Interface
# =============================================================================

def example_2_approval_interface():
    """Example 2: Create interactive approval interface."""
    print("\n" + "=" * 80)
    print("Example 2: Create Approval Interface")
    print("=" * 80)
    
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_sample_taxonomy()
    
    # Create approval interface
    interface = create_approval_interface(hierarchy)
    print(interface)
    
    print("\n✓ Example 2 complete: Approval interface created")


# =============================================================================
# Example 3: Process Approval Decisions
# =============================================================================

def example_3_process_approvals():
    """Example 3: Process different types of approval decisions."""
    print("\n" + "=" * 80)
    print("Example 3: Process Approval Decisions")
    print("=" * 80)
    
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_sample_taxonomy()
    state = StateManager.create_initial_state(create_default_config())
    
    # Example 1: Approve taxonomy
    print("\n--- Scenario 1: Approve Taxonomy ---")
    decision1 = process_approval_decision(
        decision="approve",
        hierarchy=hierarchy,
        state=state,
        notes="Taxonomy looks good, approved for use"
    )
    print(f"Decision: {decision1.action}")
    print(f"Notes: {decision1.notes}")
    print(f"Timestamp: {decision1.timestamp}")
    
    # Example 2: Request regeneration
    print("\n--- Scenario 2: Request Tier 1 Regeneration ---")
    decision2 = process_approval_decision(
        decision="regenerate_tier1",
        hierarchy=hierarchy,
        state=state,
        notes="Need more granular Tier 1 clusters",
        edit_instructions={'NEW_TIER1_K': 12}
    )
    print(f"Decision: {decision2.action}")
    print(f"Instructions: {decision2.edit_instructions}")
    
    # Example 3: Request label edits
    print("\n--- Scenario 3: Edit Labels ---")
    edits = {
        'T1_00': {
            'label': 'Advanced Machine Learning',
            'description': 'Modern ML techniques including deep learning and optimization'
        },
        'T2_02': {
            'label': 'Large Language Models'
        }
    }
    decision3 = process_approval_decision(
        decision="edit_labels",
        hierarchy=hierarchy,
        state=state,
        notes="Minor label improvements needed",
        edit_instructions=edits
    )
    print(f"Decision: {decision3.action}")
    print(f"Topics to edit: {list(edits.keys())}")
    
    print("\n✓ Example 3 complete: Various approval scenarios processed")


# =============================================================================
# Example 4: Save Approved Taxonomy
# =============================================================================

def example_4_save_taxonomy():
    """Example 4: Save approved taxonomy to JSON."""
    print("\n" + "=" * 80)
    print("Example 4: Save Approved Taxonomy")
    print("=" * 80)
    
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_sample_taxonomy()
    state = StateManager.create_initial_state(create_default_config())
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "approved_taxonomy.json"
        
        # Save taxonomy
        results = save_approved_taxonomy(
            hierarchy=hierarchy,
            output_path=str(output_path),
            state=state,
            approval_notes="Approved after review on 2025-11-22"
        )
        
        print(f"\nSaved taxonomy to: {results['json_path']}")
        print(f"Version: {results['version']}")
        print(f"Approved at: {results['approved_at']}")
        print(f"Total topics: {results['total_topics']}")
        print(f"Total papers: {results['total_papers']}")
        
        # Verify file contents
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        print(f"\nJSON structure includes:")
        print(f"  - taxonomy_version: {data['taxonomy_version']}")
        print(f"  - tier1 topics: {len(data['tier1'])}")
        print(f"  - tier2 topics: {len(data['tier2'])}")
        print(f"  - tier3 topics: {len(data['tier3'])}")
        print(f"  - export_metadata: {bool(data.get('export_metadata'))}")
    
    print("\n✓ Example 4 complete: Taxonomy saved to JSON")


# =============================================================================
# Example 5: Edit Topic Labels
# =============================================================================

def example_5_edit_labels():
    """Example 5: Edit topic labels and descriptions."""
    print("\n" + "=" * 80)
    print("Example 5: Edit Topic Labels")
    print("=" * 80)
    
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_sample_taxonomy()
    
    # Display original label
    topic = hierarchy.get_topic_by_id("T1_00")
    print(f"\nOriginal label: {topic.label}")
    print(f"Original description: {topic.description[:60]}...")
    
    # Edit label and description
    success = edit_topic_label(
        hierarchy,
        topic_id="T1_00",
        new_label="Advanced Machine Learning",
        new_description="Cutting-edge research in ML including deep learning, optimization, and novel architectures"
    )
    
    # Display updated label
    topic = hierarchy.get_topic_by_id("T1_00")
    print(f"\nUpdated label: {topic.label}")
    print(f"Updated description: {topic.description[:60]}...")
    print(f"Edit successful: {success}")
    
    print("\n✓ Example 5 complete: Topic labels edited")


# =============================================================================
# Example 6: Reassign Papers Between Topics
# =============================================================================

def example_6_reassign_papers():
    """Example 6: Reassign papers between topics."""
    print("\n" + "=" * 80)
    print("Example 6: Reassign Papers Between Topics")
    print("=" * 80)
    
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_sample_taxonomy()
    
    # Show initial state
    from_topic = hierarchy.get_topic_by_id("T1_00")
    to_topic = hierarchy.get_topic_by_id("T1_01")
    
    print(f"\nBefore reassignment:")
    print(f"  {from_topic.id} ({from_topic.label}): {from_topic.paper_count} papers")
    print(f"  {to_topic.id} ({to_topic.label}): {to_topic.paper_count} papers")
    
    # Reassign a paper
    paper_id = "paper_005"
    success = reassign_paper_to_topic(
        hierarchy,
        paper_id=paper_id,
        from_topic_id="T1_00",
        to_topic_id="T1_01"
    )
    
    # Show after state
    print(f"\nAfter reassignment of {paper_id}:")
    print(f"  {from_topic.id} ({from_topic.label}): {from_topic.paper_count} papers")
    print(f"  {to_topic.id} ({to_topic.label}): {to_topic.paper_count} papers")
    print(f"Reassignment successful: {success}")
    
    print("\n✓ Example 6 complete: Paper reassigned")


# =============================================================================
# Example 7: Merge Topics
# =============================================================================

def example_7_merge_topics():
    """Example 7: Merge two topics at the same tier."""
    print("\n" + "=" * 80)
    print("Example 7: Merge Topics")
    print("=" * 80)
    
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_sample_taxonomy()
    
    # Show initial state
    topic1 = hierarchy.get_topic_by_id("T2_00")
    topic2 = hierarchy.get_topic_by_id("T2_01")
    
    print(f"\nBefore merge:")
    print(f"  {topic1.id} ({topic1.label}): {topic1.paper_count} papers")
    print(f"  {topic2.id} ({topic2.label}): {topic2.paper_count} papers")
    print(f"  Total Tier 2 topics: {len(hierarchy.tier2)}")
    
    # Merge topics
    merged_id = merge_topics(
        hierarchy,
        topic_id1="T2_00",
        topic_id2="T2_01",
        new_label="Machine Learning Techniques",
        new_description="Combined topic covering deep learning and transfer learning approaches"
    )
    
    # Show after state
    merged_topic = hierarchy.get_topic_by_id(merged_id)
    print(f"\nAfter merge:")
    print(f"  {merged_topic.id} ({merged_topic.label}): {merged_topic.paper_count} papers")
    print(f"  Total Tier 2 topics: {len(hierarchy.tier2)}")
    print(f"  Topic {topic2.id} removed: {hierarchy.get_topic_by_id(topic2.id) is None}")
    
    print("\n✓ Example 7 complete: Topics merged")


# =============================================================================
# Example 8: Split Topics
# =============================================================================

def example_8_split_topics():
    """Example 8: Split a topic into multiple topics."""
    print("\n" + "=" * 80)
    print("Example 8: Split Topics")
    print("=" * 80)
    
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_sample_taxonomy()
    
    # Show initial state
    topic = hierarchy.get_topic_by_id("T1_00")
    print(f"\nBefore split:")
    print(f"  {topic.id} ({topic.label}): {topic.paper_count} papers")
    print(f"  Total Tier 1 topics: {len(hierarchy.tier1)}")
    
    # Split into 3 groups
    paper_ids = topic.paper_ids
    paper_groups = [
        paper_ids[:5],
        paper_ids[5:10],
        paper_ids[10:]
    ]
    new_labels = [
        "Deep Learning",
        "Classical ML",
        "Optimization Methods"
    ]
    new_descriptions = [
        "Neural network based approaches",
        "Traditional machine learning algorithms",
        "Optimization and training techniques"
    ]
    
    # Split topic
    new_ids = split_topic(
        hierarchy,
        topic_id="T1_00",
        paper_groups=paper_groups,
        new_labels=new_labels,
        new_descriptions=new_descriptions
    )
    
    # Show after state
    print(f"\nAfter split into {len(new_ids)} topics:")
    for new_id, label in zip(new_ids, new_labels):
        new_topic = hierarchy.get_topic_by_id(new_id)
        print(f"  {new_id} ({label}): {new_topic.paper_count} papers")
    print(f"  Total Tier 1 topics: {len(hierarchy.tier1)}")
    print(f"  Original topic removed: {hierarchy.get_topic_by_id('T1_00') is None}")
    
    print("\n✓ Example 8 complete: Topic split")


# =============================================================================
# Example 9: Complete Review Workflow
# =============================================================================

def example_9_complete_workflow():
    """Example 9: Complete taxonomy review and approval workflow."""
    print("\n" + "=" * 80)
    print("Example 9: Complete Review Workflow")
    print("=" * 80)
    
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("SKIP: taxonomy_review not available")
        return
    
    hierarchy = create_sample_taxonomy()
    papers = create_sample_papers()
    state = StateManager.create_initial_state(create_default_config())
    
    print("\n--- Step 1: Display Taxonomy ---")
    review_text = display_taxonomy_for_review(hierarchy, papers)
    print("Taxonomy displayed (truncated):", review_text[:200] + "...")
    
    print("\n--- Step 2: Show Approval Interface ---")
    interface = create_approval_interface(hierarchy)
    print("Approval interface shown")
    
    print("\n--- Step 3: User Makes Edits ---")
    # Edit a label
    edit_topic_label(hierarchy, "T1_00", new_label="Advanced ML")
    print("Edited T1_00 label")
    
    # Reassign a paper
    reassign_paper_to_topic(hierarchy, "paper_005", "T1_00", "T1_01")
    print("Reassigned paper_005")
    
    print("\n--- Step 4: Process Approval ---")
    approval = process_approval_decision(
        decision="approve",
        hierarchy=hierarchy,
        state=state,
        notes="Approved with minor edits"
    )
    print(f"Decision: {approval.action}")
    
    print("\n--- Step 5: Save Approved Taxonomy ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "final_taxonomy.json"
        results = save_approved_taxonomy(
            hierarchy,
            str(output_path),
            state,
            approval_notes="Approved after review and edits"
        )
        print(f"Saved to: {results['json_path']}")
        print(f"Version: {results['version']}")
    
    print("\n✓ Example 9 complete: Full workflow executed")


# =============================================================================
# Run All Examples
# =============================================================================

def run_all_examples():
    """Run all Phase 9 examples."""
    print("\n" + "=" * 80)
    print("Phase 9 Usage Examples: Taxonomy Review and Approval")
    print("=" * 80)
    
    if not TAXONOMY_REVIEW_AVAILABLE:
        print("\nERROR: taxonomy_review module not available")
        print("Please ensure taxonomy_review.py is in the same directory")
        return
    
    example_1_display_taxonomy()
    example_2_approval_interface()
    example_3_process_approvals()
    example_4_save_taxonomy()
    example_5_edit_labels()
    example_6_reassign_papers()
    example_7_merge_topics()
    example_8_split_topics()
    example_9_complete_workflow()
    
    print("\n" + "=" * 80)
    print("All examples completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_examples()
