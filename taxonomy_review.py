#!/usr/bin/env python3
"""
RAG PDF Research Corpus System - Taxonomy Review and Approval (Phase 9)

This module implements Phase 9 of the FINAL_NOTEBOOK_ACTION_PLAN.md:
- Step 9.1: Display Taxonomy for Review
- Step 9.2: Create Approval Interface
- Step 9.3: Save Approved Taxonomy
- Step 9.4: Taxonomy Editing Tools (Optional)

Version: 1.0
Date: 2025-11-22
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal, Tuple
from collections import defaultdict

from rag_models import (
    TopicNode,
    TopicHierarchy,
    PaperRecord,
    GraphState,
)

logger = logging.getLogger(__name__)

# Export list
__all__ = [
    # Step 9.1: Display Taxonomy
    'display_taxonomy_for_review',
    'format_topic_hierarchy',
    'get_sample_papers_for_topic',
    'TaxonomyReviewer',
    
    # Step 9.2: Approval Interface
    'create_approval_interface',
    'process_approval_decision',
    'ApprovalDecision',
    
    # Step 9.3: Save Approved Taxonomy
    'save_approved_taxonomy',
    'export_taxonomy_to_json',
    'update_state_with_approval',
    
    # Step 9.4: Editing Tools
    'edit_topic_label',
    'edit_topic_description',
    'reassign_paper_to_topic',
    'merge_topics',
    'split_topic',
    'TaxonomyEditor',
    
    # Worker
    'taxonomy_review_worker',
]


# =============================================================================
# Step 9.1: Display Taxonomy for Review
# =============================================================================

class TaxonomyReviewer:
    """
    Displays taxonomy for human review with comprehensive information.
    """
    
    def __init__(
        self,
        hierarchy: TopicHierarchy,
        papers: Optional[Dict[str, PaperRecord]] = None
    ):
        """
        Initialize the taxonomy reviewer.
        
        Args:
            hierarchy: TopicHierarchy to review
            papers: Optional dict of papers for displaying sample titles
        """
        self.hierarchy = hierarchy
        self.papers = papers or {}
        logger.info("Initialized TaxonomyReviewer")
    
    def get_sample_papers(self, topic: TopicNode, n_samples: int = 3) -> List[Dict[str, str]]:
        """
        Get sample papers for a topic with titles.
        
        Args:
            topic: TopicNode to get samples for
            n_samples: Number of samples to return
            
        Returns:
            List of dicts with paper_id and title
        """
        samples = []
        for paper_id in topic.paper_ids[:n_samples]:
            if paper_id in self.papers:
                paper = self.papers[paper_id]
                samples.append({
                    'paper_id': paper_id,
                    'title': paper.title or 'Untitled',
                    'authors': ', '.join(paper.authors[:2]) if paper.authors else 'Unknown',
                    'year': str(paper.year) if paper.year else 'N/A'
                })
            else:
                samples.append({
                    'paper_id': paper_id,
                    'title': 'Unknown',
                    'authors': 'Unknown',
                    'year': 'N/A'
                })
        return samples
    
    def format_tier1_topic(self, topic: TopicNode) -> str:
        """
        Format a Tier 1 topic for display.
        
        Args:
            topic: Tier 1 TopicNode
            
        Returns:
            Formatted string
        """
        lines = [
            f"\n{'=' * 80}",
            f"{topic.id}: {topic.label}",
            f"{'=' * 80}",
            f"Papers: {topic.paper_count}",
            f"\nDescription:",
            f"{topic.description}",
            f"\nSample Papers:",
        ]
        
        samples = self.get_sample_papers(topic, n_samples=3)
        for i, sample in enumerate(samples, 1):
            lines.append(f"  {i}. {sample['title']}")
            lines.append(f"     Authors: {sample['authors']} ({sample['year']})")
        
        # Show Tier 2 children
        tier2_children = self.hierarchy.get_tier2_topics(topic.id)
        if tier2_children:
            lines.append(f"\nTier 2 Sub-topics ({len(tier2_children)}):")
            for t2 in tier2_children:
                lines.append(f"  • {t2.id}: {t2.label} ({t2.paper_count} papers)")
                lines.append(f"    {t2.description[:100]}...")
        
        return "\n".join(lines)
    
    def format_tier2_topic(self, topic: TopicNode) -> str:
        """
        Format a Tier 2 topic for display.
        
        Args:
            topic: Tier 2 TopicNode
            
        Returns:
            Formatted string
        """
        parent = self.hierarchy.get_topic_by_id(topic.parent_id) if topic.parent_id else None
        parent_label = f" (under {parent.label})" if parent else ""
        
        lines = [
            f"\n{'-' * 80}",
            f"{topic.id}: {topic.label}{parent_label}",
            f"{'-' * 80}",
            f"Papers: {topic.paper_count}",
            f"\nDescription:",
            f"{topic.description}",
            f"\nSample Papers:",
        ]
        
        samples = self.get_sample_papers(topic, n_samples=2)
        for i, sample in enumerate(samples, 1):
            lines.append(f"  {i}. {sample['title']}")
        
        # Show Tier 3 children
        tier3_children = self.hierarchy.get_tier3_topics(topic.id)
        if tier3_children:
            lines.append(f"\nTier 3 Sub-topics ({len(tier3_children)}):")
            for t3 in tier3_children:
                lines.append(f"  • {t3.id}: {t3.label} ({t3.paper_count} papers)")
        
        return "\n".join(lines)
    
    def display_complete_taxonomy(self) -> str:
        """
        Create a complete formatted display of the taxonomy.
        
        Returns:
            Formatted string with complete taxonomy
        """
        lines = [
            "=" * 80,
            "TAXONOMY REVIEW",
            "=" * 80,
            f"Version: {self.hierarchy.taxonomy_version}",
            f"Created: {self.hierarchy.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Papers: {self.hierarchy.total_papers}",
            f"Clustering Method: {self.hierarchy.clustering_method or 'N/A'}",
            f"Labeling Model: {self.hierarchy.labeling_model or 'N/A'}",
            "",
            "STATISTICS:",
            f"  Tier 1 Topics: {len(self.hierarchy.tier1)}",
            f"  Tier 2 Topics: {len(self.hierarchy.tier2)}",
            f"  Tier 3 Topics: {len(self.hierarchy.tier3)}",
            f"  Total Topics: {len(self.hierarchy.tier1) + len(self.hierarchy.tier2) + len(self.hierarchy.tier3)}",
            "",
            "=" * 80,
            "TIER 1 TOPICS (BROAD CATEGORIES)",
            "=" * 80,
        ]
        
        # Display all Tier 1 topics
        for t1 in self.hierarchy.tier1:
            lines.append(self.format_tier1_topic(t1))
        
        lines.extend([
            "",
            "=" * 80,
            "END OF TAXONOMY REVIEW",
            "=" * 80,
        ])
        
        return "\n".join(lines)
    
    def display_tier_summary(self, tier: int) -> str:
        """
        Display summary for a specific tier.
        
        Args:
            tier: Tier number (1, 2, or 3)
            
        Returns:
            Formatted string with tier summary
        """
        if tier == 1:
            topics = self.hierarchy.tier1
            tier_name = "Tier 1 (Broad Categories)"
        elif tier == 2:
            topics = self.hierarchy.tier2
            tier_name = "Tier 2 (Mid-Level Topics)"
        elif tier == 3:
            topics = self.hierarchy.tier3
            tier_name = "Tier 3 (Fine-Grained Topics)"
        else:
            raise ValueError(f"Invalid tier: {tier}")
        
        lines = [
            f"\n{'=' * 80}",
            tier_name,
            f"{'=' * 80}",
            f"Total Topics: {len(topics)}",
            f"Total Papers Assigned: {sum(t.paper_count for t in topics)}",
            "",
        ]
        
        for topic in topics:
            parent_info = ""
            if topic.parent_id:
                parent = self.hierarchy.get_topic_by_id(topic.parent_id)
                parent_info = f" (parent: {parent.label if parent else 'Unknown'})"
            
            lines.append(f"{topic.id}: {topic.label}{parent_info}")
            lines.append(f"  Papers: {topic.paper_count}")
            lines.append(f"  Description: {topic.description[:80]}...")
            lines.append("")
        
        return "\n".join(lines)


def display_taxonomy_for_review(
    hierarchy: TopicHierarchy,
    papers: Optional[Dict[str, PaperRecord]] = None,
    tier: Optional[int] = None
) -> str:
    """
    Display taxonomy for human review.
    
    Args:
        hierarchy: TopicHierarchy to display
        papers: Optional dict of papers for displaying sample titles
        tier: Optional tier number to display (1, 2, or 3). If None, display all.
        
    Returns:
        Formatted string for display/printing
    """
    reviewer = TaxonomyReviewer(hierarchy, papers)
    
    if tier is not None:
        return reviewer.display_tier_summary(tier)
    else:
        return reviewer.display_complete_taxonomy()


def get_sample_papers_for_topic(
    topic: TopicNode,
    papers: Dict[str, PaperRecord],
    n_samples: int = 5
) -> List[Dict[str, str]]:
    """
    Get sample papers for a specific topic.
    
    Args:
        topic: TopicNode to get samples for
        papers: Dict of all papers
        n_samples: Number of samples to return
        
    Returns:
        List of dicts with paper information
    """
    reviewer = TaxonomyReviewer(TopicHierarchy(taxonomy_version="temp"), papers)
    return reviewer.get_sample_papers(topic, n_samples)


def format_topic_hierarchy(hierarchy: TopicHierarchy) -> Dict[str, Any]:
    """
    Format taxonomy hierarchy as nested dict for easy review.
    
    Args:
        hierarchy: TopicHierarchy to format
        
    Returns:
        Nested dict representation
    """
    result = {
        'version': hierarchy.taxonomy_version,
        'created_at': hierarchy.created_at.isoformat(),
        'total_papers': hierarchy.total_papers,
        'tiers': []
    }
    
    for t1 in hierarchy.tier1:
        tier1_dict = {
            'id': t1.id,
            'label': t1.label,
            'description': t1.description,
            'paper_count': t1.paper_count,
            'children': []
        }
        
        # Add Tier 2 children
        tier2_children = hierarchy.get_tier2_topics(t1.id)
        for t2 in tier2_children:
            tier2_dict = {
                'id': t2.id,
                'label': t2.label,
                'description': t2.description,
                'paper_count': t2.paper_count,
                'children': []
            }
            
            # Add Tier 3 children
            tier3_children = hierarchy.get_tier3_topics(t2.id)
            for t3 in tier3_children:
                tier3_dict = {
                    'id': t3.id,
                    'label': t3.label,
                    'description': t3.description,
                    'paper_count': t3.paper_count,
                }
                tier2_dict['children'].append(tier3_dict)
            
            tier1_dict['children'].append(tier2_dict)
        
        result['tiers'].append(tier1_dict)
    
    return result


# =============================================================================
# Step 9.2: Create Approval Interface
# =============================================================================

class ApprovalDecision:
    """Represents a user's decision about the taxonomy."""
    
    def __init__(
        self,
        action: Literal["approve", "regenerate_tier1", "regenerate_tier2", "regenerate_tier3", "edit_labels", "reject"],
        notes: str = "",
        edit_instructions: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize approval decision.
        
        Args:
            action: User's decision action
            notes: Optional notes about the decision
            edit_instructions: Optional dict with editing instructions
        """
        self.action = action
        self.notes = notes
        self.edit_instructions = edit_instructions or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'action': self.action,
            'notes': self.notes,
            'edit_instructions': self.edit_instructions,
            'timestamp': self.timestamp.isoformat()
        }


def create_approval_interface(hierarchy: TopicHierarchy) -> str:
    """
    Create an interactive approval interface prompt.
    
    Args:
        hierarchy: TopicHierarchy to approve
        
    Returns:
        Formatted string with approval instructions
    """
    lines = [
        "",
        "=" * 80,
        "TAXONOMY APPROVAL INTERFACE",
        "=" * 80,
        "",
        "Please review the taxonomy above and choose one of the following options:",
        "",
        "1. APPROVE - Accept taxonomy as-is and proceed to classification",
        "   Set: TAXONOMY_DECISION = 'approve'",
        "",
        "2. REGENERATE TIER 1 - Rebuild Tier 1 topics with different parameters",
        "   Set: TAXONOMY_DECISION = 'regenerate_tier1'",
        "   Optionally set: NEW_TIER1_K = <number>",
        "",
        "3. REGENERATE TIER 2 - Rebuild Tier 2 topics for specific Tier 1 topic",
        "   Set: TAXONOMY_DECISION = 'regenerate_tier2'",
        "   Set: TARGET_TIER1_ID = 'T1_XX'",
        "   Optionally set: NEW_TIER2_K = <number>",
        "",
        "4. REGENERATE TIER 3 - Rebuild Tier 3 topics for specific Tier 2 topic",
        "   Set: TAXONOMY_DECISION = 'regenerate_tier3'",
        "   Set: TARGET_TIER2_ID = 'T2_XX'",
        "   Optionally set: NEW_TIER3_K = <number>",
        "",
        "5. EDIT LABELS - Modify topic labels and descriptions",
        "   Set: TAXONOMY_DECISION = 'edit_labels'",
        "   Define: LABEL_EDITS = {",
        "       'T1_00': {'label': 'New Label', 'description': 'New description'},",
        "       'T2_05': {'label': 'Another Label'},",
        "   }",
        "",
        "6. REJECT - Reject taxonomy and stop",
        "   Set: TAXONOMY_DECISION = 'reject'",
        "   Set: REJECTION_REASON = 'Reason for rejection'",
        "",
        "Example usage:",
        "  # To approve:",
        "  TAXONOMY_DECISION = 'approve'",
        "  decision = process_approval_decision(TAXONOMY_DECISION, hierarchy, state)",
        "",
        "=" * 80,
        "",
        f"Taxonomy Version: {hierarchy.taxonomy_version}",
        f"Total Topics: {len(hierarchy.tier1)} Tier1, {len(hierarchy.tier2)} Tier2, {len(hierarchy.tier3)} Tier3",
        f"Total Papers: {hierarchy.total_papers}",
        "",
        "=" * 80,
    ]
    
    return "\n".join(lines)


def process_approval_decision(
    decision: str,
    hierarchy: TopicHierarchy,
    state: GraphState,
    notes: str = "",
    edit_instructions: Optional[Dict[str, Any]] = None
) -> ApprovalDecision:
    """
    Process user's approval decision.
    
    Args:
        decision: User's decision string
        hierarchy: Current TopicHierarchy
        state: GraphState
        notes: Optional notes
        edit_instructions: Optional editing instructions
        
    Returns:
        ApprovalDecision object
    """
    valid_decisions = ["approve", "regenerate_tier1", "regenerate_tier2", "regenerate_tier3", "edit_labels", "reject"]
    
    if decision not in valid_decisions:
        logger.warning(f"Invalid decision '{decision}', defaulting to 'reject'")
        decision = "reject"
        notes = f"Invalid decision provided: {decision}"
    
    approval = ApprovalDecision(
        action=decision,
        notes=notes,
        edit_instructions=edit_instructions
    )
    
    logger.info(f"Processed approval decision: {decision}")
    
    if decision == "approve":
        logger.info("Taxonomy approved by user")
    elif decision.startswith("regenerate"):
        logger.info(f"User requested regeneration: {decision}")
    elif decision == "edit_labels":
        logger.info(f"User requested label edits: {len(edit_instructions or {})} topics")
    elif decision == "reject":
        logger.warning(f"Taxonomy rejected: {notes}")
    
    return approval


# =============================================================================
# Step 9.3: Save Approved Taxonomy
# =============================================================================

def export_taxonomy_to_json(
    hierarchy: TopicHierarchy,
    output_path: str,
    include_metadata: bool = True
) -> str:
    """
    Export taxonomy to JSON file.
    
    Args:
        hierarchy: TopicHierarchy to export
        output_path: Path to save JSON file
        include_metadata: Whether to include metadata
        
    Returns:
        Path to saved file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict
    taxonomy_dict = hierarchy.to_dict()
    
    # Add export metadata
    if include_metadata:
        taxonomy_dict['export_metadata'] = {
            'exported_at': datetime.now().isoformat(),
            'format_version': '1.0',
            'notes': f'Taxonomy export for {hierarchy.total_papers} papers'
        }
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(taxonomy_dict, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"Exported taxonomy to {output_path}")
    return str(output_path)


def update_state_with_approval(
    state: GraphState,
    hierarchy: TopicHierarchy,
    approval: ApprovalDecision
) -> GraphState:
    """
    Update GraphState with approval information.
    
    Args:
        state: Current GraphState
        hierarchy: Approved TopicHierarchy
        approval: ApprovalDecision object
        
    Returns:
        Updated GraphState
    """
    # Update taxonomy in state
    state['topic_hierarchy'] = hierarchy
    
    # Add approval metadata
    state['taxonomy_approved'] = (approval.action == 'approve')
    state['taxonomy_approval_timestamp'] = approval.timestamp
    state['taxonomy_approval_notes'] = approval.notes
    state['taxonomy_approval_decision'] = approval.to_dict()
    
    # Update phase marker
    if approval.action == 'approve':
        state['current_phase'] = 'taxonomy_approved'
        logger.info("Taxonomy approved and state updated")
    else:
        state['current_phase'] = 'taxonomy_review_pending'
        logger.info(f"Taxonomy review pending: {approval.action}")
    
    return state


def save_approved_taxonomy(
    hierarchy: TopicHierarchy,
    output_path: str,
    state: Optional[GraphState] = None,
    approval_notes: str = ""
) -> Dict[str, Any]:
    """
    Save approved taxonomy with full metadata.
    
    Args:
        hierarchy: TopicHierarchy to save
        output_path: Path to save JSON file
        state: Optional GraphState to update
        approval_notes: Optional approval notes
        
    Returns:
        Dict with save results
    """
    # Export to JSON
    json_path = export_taxonomy_to_json(hierarchy, output_path, include_metadata=True)
    
    # Create approval decision
    approval = ApprovalDecision(
        action="approve",
        notes=approval_notes
    )
    
    # Update state if provided
    if state is not None:
        state = update_state_with_approval(state, hierarchy, approval)
    
    results = {
        'json_path': json_path,
        'version': hierarchy.taxonomy_version,
        'approved_at': approval.timestamp.isoformat(),
        'total_topics': len(hierarchy.tier1) + len(hierarchy.tier2) + len(hierarchy.tier3),
        'total_papers': hierarchy.total_papers,
        'notes': approval_notes
    }
    
    logger.info(f"Saved approved taxonomy: {results}")
    return results


# =============================================================================
# Step 9.4: Taxonomy Editing Tools (Optional)
# =============================================================================

class TaxonomyEditor:
    """
    Provides tools for editing taxonomy structure and labels.
    """
    
    def __init__(self, hierarchy: TopicHierarchy):
        """
        Initialize taxonomy editor.
        
        Args:
            hierarchy: TopicHierarchy to edit
        """
        self.hierarchy = hierarchy
        self.edit_history: List[Dict[str, Any]] = []
        logger.info("Initialized TaxonomyEditor")
    
    def edit_topic_label(
        self,
        topic_id: str,
        new_label: Optional[str] = None,
        new_description: Optional[str] = None
    ) -> bool:
        """
        Edit topic label and/or description.
        
        Args:
            topic_id: Topic ID to edit
            new_label: New label (optional)
            new_description: New description (optional)
            
        Returns:
            True if successful, False otherwise
        """
        topic = self.hierarchy.get_topic_by_id(topic_id)
        if not topic:
            logger.error(f"Topic {topic_id} not found")
            return False
        
        old_label = topic.label
        old_description = topic.description
        
        if new_label:
            topic.label = new_label
        if new_description:
            topic.description = new_description
        
        # Record edit
        self.edit_history.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'edit_label',
            'topic_id': topic_id,
            'changes': {
                'old_label': old_label,
                'new_label': new_label or old_label,
                'old_description': old_description,
                'new_description': new_description or old_description
            }
        })
        
        logger.info(f"Edited topic {topic_id}: '{old_label}' -> '{new_label or old_label}'")
        return True
    
    def reassign_paper(
        self,
        paper_id: str,
        from_topic_id: str,
        to_topic_id: str
    ) -> bool:
        """
        Reassign a paper from one topic to another.
        
        Args:
            paper_id: Paper ID to reassign
            from_topic_id: Source topic ID
            to_topic_id: Destination topic ID
            
        Returns:
            True if successful, False otherwise
        """
        from_topic = self.hierarchy.get_topic_by_id(from_topic_id)
        to_topic = self.hierarchy.get_topic_by_id(to_topic_id)
        
        if not from_topic or not to_topic:
            logger.error(f"Topic not found: {from_topic_id} or {to_topic_id}")
            return False
        
        # Remove from source
        if paper_id not in from_topic.paper_ids:
            logger.error(f"Paper {paper_id} not in topic {from_topic_id}")
            return False
        
        from_topic.remove_paper(paper_id)
        to_topic.add_paper(paper_id)
        
        # Record edit
        self.edit_history.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'reassign_paper',
            'paper_id': paper_id,
            'from_topic': from_topic_id,
            'to_topic': to_topic_id
        })
        
        logger.info(f"Reassigned paper {paper_id}: {from_topic_id} -> {to_topic_id}")
        return True
    
    def merge_topics(
        self,
        topic_id1: str,
        topic_id2: str,
        new_label: Optional[str] = None,
        new_description: Optional[str] = None
    ) -> Optional[str]:
        """
        Merge two topics at the same tier.
        
        Args:
            topic_id1: First topic ID (will be kept)
            topic_id2: Second topic ID (will be removed)
            new_label: Optional new label for merged topic
            new_description: Optional new description
            
        Returns:
            ID of merged topic, or None if failed
        """
        topic1 = self.hierarchy.get_topic_by_id(topic_id1)
        topic2 = self.hierarchy.get_topic_by_id(topic_id2)
        
        if not topic1 or not topic2:
            logger.error(f"Topic not found: {topic_id1} or {topic_id2}")
            return None
        
        # Check same tier and parent
        if topic1.parent_id != topic2.parent_id:
            logger.error("Cannot merge topics with different parents")
            return None
        
        # Merge paper lists
        for paper_id in topic2.paper_ids:
            if paper_id not in topic1.paper_ids:
                topic1.add_paper(paper_id)
        
        # Update label/description if provided
        if new_label:
            topic1.label = new_label
        if new_description:
            topic1.description = new_description
        
        # Remove topic2 from hierarchy
        if topic1.parent_id is None:  # Tier 1
            self.hierarchy.tier1 = [t for t in self.hierarchy.tier1 if t.id != topic_id2]
        elif topic2 in self.hierarchy.tier2:  # Tier 2
            self.hierarchy.tier2 = [t for t in self.hierarchy.tier2 if t.id != topic_id2]
        elif topic2 in self.hierarchy.tier3:  # Tier 3
            self.hierarchy.tier3 = [t for t in self.hierarchy.tier3 if t.id != topic_id2]
        
        # Record edit
        self.edit_history.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'merge_topics',
            'kept_topic': topic_id1,
            'removed_topic': topic_id2,
            'new_label': new_label,
            'merged_paper_count': topic1.paper_count
        })
        
        logger.info(f"Merged topics {topic_id2} into {topic_id1}")
        return topic_id1
    
    def get_edit_history(self) -> List[Dict[str, Any]]:
        """Get edit history."""
        return self.edit_history.copy()


def edit_topic_label(
    hierarchy: TopicHierarchy,
    topic_id: str,
    new_label: Optional[str] = None,
    new_description: Optional[str] = None
) -> bool:
    """
    Edit a topic's label and/or description.
    
    Args:
        hierarchy: TopicHierarchy to edit
        topic_id: Topic ID to edit
        new_label: New label (optional)
        new_description: New description (optional)
        
    Returns:
        True if successful, False otherwise
    """
    editor = TaxonomyEditor(hierarchy)
    return editor.edit_topic_label(topic_id, new_label, new_description)


def edit_topic_description(
    hierarchy: TopicHierarchy,
    topic_id: str,
    new_description: str
) -> bool:
    """
    Edit a topic's description.
    
    Args:
        hierarchy: TopicHierarchy to edit
        topic_id: Topic ID to edit
        new_description: New description
        
    Returns:
        True if successful, False otherwise
    """
    return edit_topic_label(hierarchy, topic_id, new_description=new_description)


def reassign_paper_to_topic(
    hierarchy: TopicHierarchy,
    paper_id: str,
    from_topic_id: str,
    to_topic_id: str
) -> bool:
    """
    Reassign a paper from one topic to another.
    
    Args:
        hierarchy: TopicHierarchy to edit
        paper_id: Paper ID to reassign
        from_topic_id: Source topic ID
        to_topic_id: Destination topic ID
        
    Returns:
        True if successful, False otherwise
    """
    editor = TaxonomyEditor(hierarchy)
    return editor.reassign_paper(paper_id, from_topic_id, to_topic_id)


def merge_topics(
    hierarchy: TopicHierarchy,
    topic_id1: str,
    topic_id2: str,
    new_label: Optional[str] = None,
    new_description: Optional[str] = None
) -> Optional[str]:
    """
    Merge two topics at the same tier.
    
    Args:
        hierarchy: TopicHierarchy to edit
        topic_id1: First topic ID (will be kept)
        topic_id2: Second topic ID (will be removed)
        new_label: Optional new label for merged topic
        new_description: Optional new description
        
    Returns:
        ID of merged topic, or None if failed
    """
    editor = TaxonomyEditor(hierarchy)
    return editor.merge_topics(topic_id1, topic_id2, new_label, new_description)


def split_topic(
    hierarchy: TopicHierarchy,
    topic_id: str,
    paper_groups: List[List[str]],
    new_labels: List[str],
    new_descriptions: Optional[List[str]] = None
) -> List[str]:
    """
    Split a topic into multiple topics.
    
    Args:
        hierarchy: TopicHierarchy to edit
        topic_id: Topic ID to split
        paper_groups: List of paper ID lists for each new topic
        new_labels: Labels for new topics
        new_descriptions: Optional descriptions for new topics
        
    Returns:
        List of new topic IDs
    """
    topic = hierarchy.get_topic_by_id(topic_id)
    if not topic:
        logger.error(f"Topic {topic_id} not found")
        return []
    
    if len(paper_groups) != len(new_labels):
        logger.error("Number of paper groups must match number of labels")
        return []
    
    new_descriptions = new_descriptions or ["" for _ in new_labels]
    
    # Determine which tier this topic is in
    tier = None
    if topic in hierarchy.tier1:
        tier = 1
    elif topic in hierarchy.tier2:
        tier = 2
    elif topic in hierarchy.tier3:
        tier = 3
    
    if tier is None:
        logger.error(f"Could not determine tier for topic {topic_id}")
        return []
    
    new_topic_ids = []
    
    # Create new topics
    for i, (papers, label, description) in enumerate(zip(paper_groups, new_labels, new_descriptions)):
        # Generate new ID based on tier
        if tier == 1:
            new_id = f"T1_{len(hierarchy.tier1):02d}"
        elif tier == 2:
            new_id = f"T2_{len(hierarchy.tier2):02d}"
        else:
            new_id = f"T3_{len(hierarchy.tier3):02d}"
        
        new_topic = TopicNode(
            id=new_id,
            label=label,
            description=description,
            paper_ids=papers.copy(),
            parent_id=topic.parent_id,
            centroid=topic.centroid  # Copy centroid from original
        )
        
        hierarchy.add_topic(tier, new_topic)
        new_topic_ids.append(new_id)
    
    # Remove original topic
    if tier == 1:
        hierarchy.tier1 = [t for t in hierarchy.tier1 if t.id != topic_id]
    elif tier == 2:
        hierarchy.tier2 = [t for t in hierarchy.tier2 if t.id != topic_id]
    else:
        hierarchy.tier3 = [t for t in hierarchy.tier3 if t.id != topic_id]
    
    logger.info(f"Split topic {topic_id} into {len(new_topic_ids)} new topics")
    return new_topic_ids


# =============================================================================
# LangGraph Worker
# =============================================================================

def taxonomy_review_worker(
    state: GraphState,
    auto_approve: bool = False,
    output_path: Optional[str] = None
) -> GraphState:
    """
    LangGraph worker node for taxonomy review (Phase 9).
    
    Args:
        state: Current GraphState
        auto_approve: If True, automatically approve without user interaction
        output_path: Optional path to save approved taxonomy
        
    Returns:
        Updated GraphState with approval status
    """
    hierarchy = state.get('topic_hierarchy')
    if not hierarchy:
        raise ValueError("No taxonomy found in state. Run Phase 8 first.")
    
    logger.info("Starting taxonomy review worker (Phase 9)")
    
    papers = state.get('papers', {})
    
    # Display taxonomy for review
    review_text = display_taxonomy_for_review(hierarchy, papers)
    print(review_text)
    
    # Display approval interface
    interface_text = create_approval_interface(hierarchy)
    print(interface_text)
    
    if auto_approve:
        # Auto-approve for automated workflows
        logger.info("Auto-approving taxonomy")
        approval = ApprovalDecision(action="approve", notes="Auto-approved")
        state = update_state_with_approval(state, hierarchy, approval)
        
        # Save if output path provided
        if output_path:
            save_approved_taxonomy(hierarchy, output_path, state, "Auto-approved")
    else:
        # Mark as pending user approval
        state['current_phase'] = 'taxonomy_review_pending'
        state['taxonomy_approved'] = False
        logger.info("Taxonomy displayed for user review. Awaiting approval decision.")
    
    return state
