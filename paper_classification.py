#!/usr/bin/env python3
"""
RAG PDF Research Corpus System - Final Topic Classification (Phase 10)

This module implements Phase 10 of the FINAL_NOTEBOOK_ACTION_PLAN.md:
- Step 10.1: Create Classification Node (LangGraph)
- Step 10.2: Design Classification Prompts (GPT-5.1 with reasoning)
- Step 10.3: Batch Classification (with rate limiting)
- Step 10.4: Validate Classifications
- Step 10.5: Update Paper Records

Uses OpenAI Responses API with reasoning_effort parameter for GPT-5.1 models.

Version: 1.1
Date: 2025-11-23
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Literal
from collections import defaultdict

# OpenAI client
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not available. Install with: pip install openai")

# Progress bar
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from rag_models import (
    PaperRecord,
    TopicNode,
    TopicHierarchy,
    GraphState,
    RunConfig,
)

logger = logging.getLogger(__name__)

# Export list
__all__ = [
    # Step 10.1: Classification Node
    'classify_paper_node',
    'PaperClassifier',
    
    # Step 10.2: Classification Prompts
    'build_classification_prompt',
    'format_taxonomy_for_prompt',
    
    # Step 10.3: Batch Classification
    'batch_classify_papers',
    'classify_papers_with_rate_limit',
    
    # Step 10.4: Validate Classifications
    'validate_paper_classification',
    'validate_all_classifications',
    'check_tier_consistency',
    
    # Step 10.5: Update Paper Records
    'update_paper_with_classification',
    'update_papers_batch',
    
    # Worker
    'classification_worker',
]


# =============================================================================
# Step 10.2: Design Classification Prompts
# =============================================================================

def format_taxonomy_for_prompt(hierarchy: TopicHierarchy) -> str:
    """
    Format taxonomy hierarchy for inclusion in classification prompt.
    
    Creates a structured text representation of the 3-tier taxonomy
    that GPT-5.1 can use to classify papers.
    
    Args:
        hierarchy: TopicHierarchy with all tiers
        
    Returns:
        Formatted string representation of taxonomy
    """
    lines = ["=== TAXONOMY STRUCTURE ===", ""]
    
    # Build parent-child mappings
    tier2_by_parent = defaultdict(list)
    for topic in hierarchy.tier2:
        tier2_by_parent[topic.parent_id].append(topic)
    
    tier3_by_parent = defaultdict(list)
    for topic in hierarchy.tier3:
        tier3_by_parent[topic.parent_id].append(topic)
    
    # Format Tier 1 with children
    for t1 in hierarchy.tier1:
        lines.append(f"TIER 1: {t1.id} - {t1.label}")
        lines.append(f"  Description: {t1.description}")
        lines.append(f"  Paper count: {t1.paper_count}")
        
        # Tier 2 children
        for t2 in tier2_by_parent.get(t1.id, []):
            lines.append(f"  TIER 2: {t2.id} - {t2.label}")
            lines.append(f"    Description: {t2.description}")
            lines.append(f"    Paper count: {t2.paper_count}")
            
            # Tier 3 children
            for t3 in tier3_by_parent.get(t2.id, []):
                lines.append(f"    TIER 3: {t3.id} - {t3.label}")
                lines.append(f"      Description: {t3.description}")
                lines.append(f"      Paper count: {t3.paper_count}")
        
        lines.append("")
    
    return "\n".join(lines)


def build_classification_prompt(
    paper: PaperRecord,
    hierarchy: TopicHierarchy,
    reasoning_effort: Literal["none", "low", "medium", "high"] = "medium"
) -> str:
    """
    Build classification prompt for GPT-5.1 with Responses API.
    
    Creates a comprehensive prompt that includes:
    - The complete taxonomy structure
    - Paper metadata (title, authors, abstract)
    - Summary content
    - Classification instructions
    - Output format specification
    
    Note: The reasoning_effort parameter is passed to the OpenAI API
    separately and controls the model's reasoning depth.
    
    Args:
        paper: PaperRecord to classify
        hierarchy: TopicHierarchy to classify into
        reasoning_effort: Level of reasoning (passed to API, not used in prompt)
        
    Returns:
        Formatted prompt string
    """
    taxonomy_str = format_taxonomy_for_prompt(hierarchy)
    
    # Build paper context
    paper_context = []
    paper_context.append(f"Title: {paper.title or 'Unknown'}")
    
    if paper.authors:
        authors_str = ", ".join(paper.authors[:5])
        if len(paper.authors) > 5:
            authors_str += f" (and {len(paper.authors) - 5} more)"
        paper_context.append(f"Authors: {authors_str}")
    
    if paper.year:
        paper_context.append(f"Year: {paper.year}")
    
    if paper.venue:
        paper_context.append(f"Venue: {paper.venue}")
    
    if paper.abstract_text:
        # Truncate abstract if too long
        abstract = paper.abstract_text
        if len(abstract) > 1000:
            abstract = abstract[:1000] + "..."
        paper_context.append(f"\nAbstract:\n{abstract}")
    
    if paper.full_summary:
        # Truncate summary if too long
        summary = paper.full_summary
        if len(summary) > 1500:
            summary = summary[:1500] + "..."
        paper_context.append(f"\nSummary:\n{summary}")
    
    paper_info = "\n".join(paper_context)
    
    # Build prompt
    prompt = f"""You are an expert research paper classifier. Your task is to classify the following paper into a hierarchical topic taxonomy.

{taxonomy_str}

=== PAPER TO CLASSIFY ===

{paper_info}

=== CLASSIFICATION TASK ===

Analyze this paper and classify it into the most appropriate topics at all three tiers of the taxonomy:

1. **Tier 1 (Broad Topic)**: Select the single most appropriate Tier 1 topic that best represents the paper's main research area.

2. **Tier 2 (Mid-Level Topic)**: Within the selected Tier 1 topic, choose the most appropriate Tier 2 sub-topic.

3. **Tier 3 (Fine-Grained Topic)**: Within the selected Tier 2 topic, choose the most appropriate Tier 3 sub-topic.

For each tier, provide:
- **Topic ID**: The topic identifier (e.g., T1_00, T2_05, T3_12)
- **Confidence**: A confidence score from 0.0 to 1.0, where:
  - 1.0 = Perfect fit, paper clearly belongs to this topic
  - 0.8-0.9 = Strong fit, paper aligns well with topic
  - 0.6-0.7 = Good fit, paper relates to topic with some reservations
  - 0.4-0.5 = Weak fit, paper marginally relates to topic
  - <0.4 = Poor fit, topic may not be appropriate
- **Reasoning**: A brief explanation (1-3 sentences) for why this topic was selected

Ensure that:
- The Tier 2 topic's parent matches the selected Tier 1 topic
- The Tier 3 topic's parent matches the selected Tier 2 topic
- Confidence scores are realistic and reflect true fit
- Reasoning is specific to the paper's content

Return your response in JSON format:
{{
  "tier1": {{
    "topic_id": "T1_XX",
    "confidence": 0.0-1.0,
    "reasoning": "explanation"
  }},
  "tier2": {{
    "topic_id": "T2_XX",
    "confidence": 0.0-1.0,
    "reasoning": "explanation"
  }},
  "tier3": {{
    "topic_id": "T3_XX",
    "confidence": 0.0-1.0,
    "reasoning": "explanation"
  }},
  "overall_notes": "Any additional comments or observations about the classification"
}}
"""
    
    return prompt


# =============================================================================
# Step 10.1: Create Classification Node
# =============================================================================

class PaperClassifier:
    """
    Classifies papers into taxonomy topics using GPT-5.1 with Responses API.
    
    Uses OpenAI's reasoning_effort parameter to control the depth of analysis.
    Reasoning effort levels:
    - "none": Minimal reasoning, fastest
    - "low": Basic reasoning
    - "medium": Balanced reasoning (default)
    - "high": Deep reasoning, most thorough
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5-mini",
        reasoning_effort: Literal["none", "low", "medium", "high"] = "medium"
    ):
        """
        Initialize the paper classifier.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for classification (e.g., gpt-5-mini, gpt-5.1)
            reasoning_effort: Level of reasoning to apply via OpenAI Responses API
                - "none": Minimal reasoning, fastest
                - "low": Basic reasoning
                - "medium": Balanced reasoning (default)
                - "high": Deep reasoning, most thorough
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package required. Install with: pip install openai")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.reasoning_effort = reasoning_effort
        
        logger.info(f"Initialized PaperClassifier with model={model}, reasoning={reasoning_effort}")
    
    def classify_paper(
        self,
        paper: PaperRecord,
        hierarchy: TopicHierarchy
    ) -> Dict[str, Any]:
        """
        Classify a single paper using GPT-5 with Responses API.
        
        Args:
            paper: PaperRecord to classify
            hierarchy: TopicHierarchy to classify into
            
        Returns:
            Classification result dict with tier1/2/3 classifications
        """
        # Build prompt
        prompt = build_classification_prompt(paper, hierarchy, self.reasoning_effort)
        
        logger.debug(f"Classifying paper {paper.id}: {paper.title[:50] if paper.title else 'Untitled'}...")
        
        try:
            # Call GPT-5 using Responses API with reasoning effort
            response = self.client.responses.create(
                model=self.model,
                instructions="You are an expert research paper classifier. Always return valid JSON.",
                input=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent classification
                response_format={"type": "json_object"},
                reasoning_effort=self.reasoning_effort  # Pass reasoning effort to API
            )
            
            # Parse response
            result_text = response.choices[0].message.content
            classification = json.loads(result_text)
            
            logger.debug(f"Successfully classified paper {paper.id}")
            
            return classification
            
        except Exception as e:
            logger.error(f"Error classifying paper {paper.id}: {e}")
            return {
                "error": str(e),
                "tier1": None,
                "tier2": None,
                "tier3": None,
                "overall_notes": f"Classification failed: {str(e)}"
            }


def classify_paper_node(
    paper_id: str,
    state: GraphState,
    api_key: str
) -> GraphState:
    """
    LangGraph node for classifying a single paper.
    
    This node:
    1. Retrieves paper and taxonomy from state
    2. Classifies paper using GPT-5.1
    3. Updates paper record with classification
    4. Returns updated state
    
    Args:
        paper_id: ID of paper to classify
        state: GraphState with papers and taxonomy
        api_key: OpenAI API key
        
    Returns:
        Updated GraphState
    """
    config = state.get('config', RunConfig())
    papers = state.get('papers', {})
    hierarchy = state.get('topic_hierarchy')
    
    if not hierarchy:
        logger.error("No taxonomy in state, cannot classify")
        return state
    
    if paper_id not in papers:
        logger.error(f"Paper {paper_id} not found in state")
        return state
    
    paper = papers[paper_id]
    
    # Initialize classifier
    classifier = PaperClassifier(
        api_key=api_key,
        model=config.classification_model,
        reasoning_effort=config.classification_reasoning_effort
    )
    
    # Classify
    classification = classifier.classify_paper(paper, hierarchy)
    
    # Update paper record
    if "error" not in classification:
        updated_paper = update_paper_with_classification(
            paper=paper,
            classification=classification,
            taxonomy_version=hierarchy.taxonomy_version
        )
        papers[paper_id] = updated_paper
        state['papers'] = papers
    
    return state


# =============================================================================
# Step 10.3: Batch Classification
# =============================================================================

def classify_papers_with_rate_limit(
    papers: Dict[str, PaperRecord],
    hierarchy: TopicHierarchy,
    api_key: str,
    config: RunConfig,
    rate_limit_delay: float = 0.5,
    max_retries: int = 3
) -> Dict[str, Dict[str, Any]]:
    """
    Classify papers with rate limiting and retry logic.
    
    Args:
        papers: Dict of paper_id -> PaperRecord
        hierarchy: TopicHierarchy to classify into
        api_key: OpenAI API key
        config: RunConfig with model settings
        rate_limit_delay: Delay between API calls in seconds
        max_retries: Maximum retry attempts for failed classifications
        
    Returns:
        Dict of paper_id -> classification result
    """
    classifier = PaperClassifier(
        api_key=api_key,
        model=config.classification_model,
        reasoning_effort=config.classification_reasoning_effort
    )
    
    classifications = {}
    
    iterator = tqdm(papers.items(), desc="Classifying papers") if TQDM_AVAILABLE else papers.items()
    
    for paper_id, paper in iterator:
        # Skip if already classified (unless we want to reclassify)
        if paper.processing_status == "classified" and paper.tier1_topic:
            logger.debug(f"Paper {paper_id} already classified, skipping")
            continue
        
        # Classify with retry logic
        for attempt in range(max_retries):
            try:
                classification = classifier.classify_paper(paper, hierarchy)
                
                if "error" not in classification:
                    classifications[paper_id] = classification
                    logger.info(f"Classified {paper_id}: T1={classification.get('tier1', {}).get('topic_id')}")
                    break
                else:
                    logger.warning(f"Classification attempt {attempt + 1}/{max_retries} failed for {paper_id}")
                    if attempt < max_retries - 1:
                        time.sleep(rate_limit_delay * 2)  # Longer delay on error
            
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}/{max_retries} for {paper_id}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(rate_limit_delay * 2)
                else:
                    classifications[paper_id] = {
                        "error": str(e),
                        "tier1": None,
                        "tier2": None,
                        "tier3": None
                    }
        
        # Rate limiting
        time.sleep(rate_limit_delay)
    
    return classifications


def batch_classify_papers(
    state: GraphState,
    api_key: str,
    batch_size: Optional[int] = None
) -> GraphState:
    """
    Classify all papers in state in batches.
    
    Args:
        state: GraphState with papers and taxonomy
        api_key: OpenAI API key
        batch_size: Optional batch size (default: all papers)
        
    Returns:
        Updated GraphState with classified papers
    """
    config = state.get('config', RunConfig())
    papers = state.get('papers', {})
    hierarchy = state.get('topic_hierarchy')
    
    if not hierarchy:
        logger.error("No taxonomy in state, cannot classify")
        return state
    
    # Filter papers that need classification
    papers_to_classify = {
        pid: p for pid, p in papers.items()
        if p.processing_status in ["embedded", "deep_analyzed", "summarized"]
    }
    
    logger.info(f"Classifying {len(papers_to_classify)} papers")
    
    # Classify papers
    classifications = classify_papers_with_rate_limit(
        papers=papers_to_classify,
        hierarchy=hierarchy,
        api_key=api_key,
        config=config
    )
    
    # Update papers with classifications
    updated_count = 0
    for paper_id, classification in classifications.items():
        if "error" not in classification:
            paper = papers[paper_id]
            updated_paper = update_paper_with_classification(
                paper=paper,
                classification=classification,
                taxonomy_version=hierarchy.taxonomy_version
            )
            papers[paper_id] = updated_paper
            updated_count += 1
    
    state['papers'] = papers
    logger.info(f"Successfully classified {updated_count} papers")
    
    return state


# =============================================================================
# Step 10.4: Validate Classifications
# =============================================================================

def check_tier_consistency(
    tier1_id: str,
    tier2_id: str,
    tier3_id: str,
    hierarchy: TopicHierarchy
) -> Tuple[bool, List[str]]:
    """
    Check that tier assignments are consistent (parent-child relationships).
    
    Args:
        tier1_id: Tier 1 topic ID
        tier2_id: Tier 2 topic ID
        tier3_id: Tier 3 topic ID
        hierarchy: TopicHierarchy to validate against
        
    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []
    
    # Get topics
    tier1_topic = hierarchy.get_topic_by_id(tier1_id)
    tier2_topic = hierarchy.get_topic_by_id(tier2_id)
    tier3_topic = hierarchy.get_topic_by_id(tier3_id)
    
    if not tier1_topic:
        issues.append(f"Tier 1 topic {tier1_id} not found in taxonomy")
    
    if not tier2_topic:
        issues.append(f"Tier 2 topic {tier2_id} not found in taxonomy")
    else:
        # Check Tier 2 parent matches Tier 1
        if tier2_topic.parent_id != tier1_id:
            issues.append(
                f"Tier 2 topic {tier2_id} has parent {tier2_topic.parent_id}, "
                f"but Tier 1 is {tier1_id}"
            )
    
    if not tier3_topic:
        issues.append(f"Tier 3 topic {tier3_id} not found in taxonomy")
    else:
        # Check Tier 3 parent matches Tier 2
        if tier3_topic.parent_id != tier2_id:
            issues.append(
                f"Tier 3 topic {tier3_id} has parent {tier3_topic.parent_id}, "
                f"but Tier 2 is {tier2_id}"
            )
    
    return len(issues) == 0, issues


def validate_paper_classification(
    paper: PaperRecord,
    hierarchy: TopicHierarchy
) -> Dict[str, Any]:
    """
    Validate a paper's classification.
    
    Checks:
    - All tier topic IDs exist in taxonomy
    - Parent-child relationships are consistent
    - Confidence scores are in valid range [0, 1]
    - Processing status is appropriate
    
    Args:
        paper: PaperRecord with classification
        hierarchy: TopicHierarchy to validate against
        
    Returns:
        Validation result dict with 'valid' flag and issues list
    """
    issues = []
    
    # Check if classified
    if not paper.tier1_topic:
        issues.append("Paper has no Tier 1 topic assigned")
        return {"valid": False, "issues": issues}
    
    # Check tier consistency
    if paper.tier1_topic and paper.tier2_topic and paper.tier3_topic:
        is_consistent, consistency_issues = check_tier_consistency(
            paper.tier1_topic,
            paper.tier2_topic,
            paper.tier3_topic,
            hierarchy
        )
        if not is_consistent:
            issues.extend(consistency_issues)
    
    # Check confidence scores
    for tier, conf in [
        ("tier1", paper.tier1_confidence),
        ("tier2", paper.tier2_confidence),
        ("tier3", paper.tier3_confidence)
    ]:
        if conf is not None:
            if not (0.0 <= conf <= 1.0):
                issues.append(f"{tier} confidence {conf} not in range [0, 1]")
    
    # Check taxonomy version
    if not paper.taxonomy_version:
        issues.append("Paper missing taxonomy_version")
    elif paper.taxonomy_version != hierarchy.taxonomy_version:
        issues.append(
            f"Paper taxonomy_version {paper.taxonomy_version} does not match "
            f"current taxonomy {hierarchy.taxonomy_version}"
        )
    
    # Check processing status
    if paper.processing_status != "classified":
        issues.append(f"Processing status is {paper.processing_status}, expected 'classified'")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "paper_id": paper.id,
        "title": paper.title
    }


def validate_all_classifications(
    papers: Dict[str, PaperRecord],
    hierarchy: TopicHierarchy
) -> Dict[str, Any]:
    """
    Validate all paper classifications.
    
    Args:
        papers: Dict of paper_id -> PaperRecord
        hierarchy: TopicHierarchy to validate against
        
    Returns:
        Summary dict with validation results
    """
    results = {
        "total_papers": len(papers),
        "classified_count": 0,
        "valid_count": 0,
        "invalid_count": 0,
        "unclassified_count": 0,
        "issues_by_paper": {},
        "anomalies": []
    }
    
    for paper_id, paper in papers.items():
        if not paper.tier1_topic:
            results["unclassified_count"] += 1
            continue
        
        results["classified_count"] += 1
        
        validation = validate_paper_classification(paper, hierarchy)
        
        if validation["valid"]:
            results["valid_count"] += 1
        else:
            results["invalid_count"] += 1
            results["issues_by_paper"][paper_id] = validation["issues"]
        
        # Check for anomalies (low confidence)
        if paper.tier1_confidence and paper.tier1_confidence < 0.5:
            results["anomalies"].append({
                "paper_id": paper_id,
                "title": paper.title,
                "tier1_topic": paper.tier1_topic,
                "confidence": paper.tier1_confidence,
                "reason": "Low Tier 1 confidence"
            })
    
    logger.info(
        f"Validation: {results['valid_count']}/{results['classified_count']} valid, "
        f"{results['invalid_count']} invalid, {results['unclassified_count']} unclassified"
    )
    
    return results


# =============================================================================
# Step 10.5: Update Paper Records
# =============================================================================

def update_paper_with_classification(
    paper: PaperRecord,
    classification: Dict[str, Any],
    taxonomy_version: str
) -> PaperRecord:
    """
    Update a paper record with classification results.
    
    Args:
        paper: PaperRecord to update
        classification: Classification result from GPT-5.1
        taxonomy_version: Version of taxonomy used
        
    Returns:
        Updated PaperRecord
    """
    # Extract tier classifications
    tier1 = classification.get("tier1", {})
    tier2 = classification.get("tier2", {})
    tier3 = classification.get("tier3", {})
    
    # Combine reasoning into classification_notes
    notes_parts = []
    if tier1.get("reasoning"):
        notes_parts.append(f"Tier 1: {tier1['reasoning']}")
    if tier2.get("reasoning"):
        notes_parts.append(f"Tier 2: {tier2['reasoning']}")
    if tier3.get("reasoning"):
        notes_parts.append(f"Tier 3: {tier3['reasoning']}")
    if classification.get("overall_notes"):
        notes_parts.append(f"Overall: {classification['overall_notes']}")
    
    classification_notes = "\n".join(notes_parts)
    
    # Update paper
    paper.tier1_topic = tier1.get("topic_id")
    paper.tier1_confidence = tier1.get("confidence")
    
    paper.tier2_topic = tier2.get("topic_id")
    paper.tier2_confidence = tier2.get("confidence")
    
    paper.tier3_topic = tier3.get("topic_id")
    paper.tier3_confidence = tier3.get("confidence")
    
    paper.taxonomy_version = taxonomy_version
    paper.classification_notes = classification_notes
    paper.processing_status = "classified"
    paper.last_updated = datetime.now()
    
    logger.debug(f"Updated paper {paper.id} with classification")
    
    return paper


def update_papers_batch(
    papers: Dict[str, PaperRecord],
    classifications: Dict[str, Dict[str, Any]],
    taxonomy_version: str
) -> Dict[str, PaperRecord]:
    """
    Update multiple papers with classifications in batch.
    
    Args:
        papers: Dict of paper_id -> PaperRecord
        classifications: Dict of paper_id -> classification result
        taxonomy_version: Version of taxonomy used
        
    Returns:
        Updated papers dict
    """
    updated_papers = papers.copy()
    
    for paper_id, classification in classifications.items():
        if paper_id in updated_papers and "error" not in classification:
            updated_papers[paper_id] = update_paper_with_classification(
                paper=updated_papers[paper_id],
                classification=classification,
                taxonomy_version=taxonomy_version
            )
    
    logger.info(f"Updated {len(classifications)} papers with classifications")
    
    return updated_papers


# =============================================================================
# LangGraph Worker Integration
# =============================================================================

def classification_worker(
    state: GraphState,
    api_key: str,
    validate: bool = True
) -> GraphState:
    """
    Complete LangGraph worker for Phase 10 classification.
    
    This worker:
    1. Checks taxonomy exists in state
    2. Classifies all unclassified papers
    3. Updates paper records
    4. Validates classifications if requested
    5. Updates state phase marker
    
    Args:
        state: GraphState with papers and taxonomy
        api_key: OpenAI API key
        validate: Whether to validate classifications
        
    Returns:
        Updated GraphState
    """
    logger.info("=" * 60)
    logger.info("Starting Phase 10: Final Topic Classification")
    logger.info("=" * 60)
    
    hierarchy = state.get('topic_hierarchy')
    
    if not hierarchy:
        logger.error("No taxonomy found in state. Run Phase 8-9 first.")
        return state
    
    # Check if taxonomy is approved
    if state.get('taxonomy_approved') is False:
        logger.warning("Taxonomy not approved. Classification may use unreviewed taxonomy.")
    
    # Classify papers
    state = batch_classify_papers(state, api_key)
    
    # Validate if requested
    if validate:
        papers = state.get('papers', {})
        validation_results = validate_all_classifications(papers, hierarchy)
        
        logger.info(f"Validation results:")
        logger.info(f"  Classified: {validation_results['classified_count']}/{validation_results['total_papers']}")
        logger.info(f"  Valid: {validation_results['valid_count']}")
        logger.info(f"  Invalid: {validation_results['invalid_count']}")
        logger.info(f"  Anomalies: {len(validation_results['anomalies'])}")
        
        # Store validation results in state
        state['classification_validation'] = validation_results
    
    # Update phase marker
    state['current_phase'] = 'classification_complete'
    state['classification_timestamp'] = datetime.now()
    
    logger.info("=" * 60)
    logger.info("Phase 10: Final Topic Classification - COMPLETE")
    logger.info("=" * 60)
    
    return state
