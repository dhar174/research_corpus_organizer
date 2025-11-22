#!/usr/bin/env python3
"""
Example usage of RAG models.

This script demonstrates how to use the data models and utilities
defined in rag_models.py for the RAG PDF Research Corpus System.
"""

from datetime import date
from rag_models import (
    PaperRecord,
    PaperChunk,
    TopicNode,
    TopicHierarchy,
    StateManager,
    MetadataExtractor,
    StatisticsTracker,
    IDGenerator,
    create_default_config,
    validate_paper_record,
)


def example_1_create_configuration():
    """Example 1: Create and configure the system."""
    print("=" * 60)
    print("Example 1: Creating Configuration")
    print("=" * 60)
    
    # Create configuration with defaults
    config = create_default_config(
        drive_folder_path="my_research_papers",
        max_papers_per_run=50,
        summary_model="gpt-4-turbo-preview",
        enable_ocr_fallback=True,
        summary_reasoning_effort="high"
    )
    
    print(config.display_config())
    print()


def example_2_create_paper_record():
    """Example 2: Create and manage a paper record."""
    print("=" * 60)
    print("Example 2: Creating Paper Records")
    print("=" * 60)
    
    # Generate a paper ID from file path
    file_path = "/content/drive/My Drive/PDFs/attention_is_all_you_need.pdf"
    paper_id = IDGenerator.generate_paper_id(file_path)
    
    # Create a paper record
    paper = PaperRecord(
        id=paper_id,
        file_path=file_path,
        filename="attention_is_all_you_need.pdf",
        source="arxiv",
        arxiv_id="1706.03762",
        title="Attention is All You Need",
        authors=["Vaswani, Ashish", "Shazeer, Noam", "Parmar, Niki"],
        venue="NeurIPS",
        publish_date=date(2017, 6, 12),
        year=2017,
        is_preprint=False
    )
    
    print(f"Paper ID: {paper.id}")
    print(f"Title: {paper.title}")
    print(f"Authors: {', '.join(paper.authors)}")
    print(f"Status: {paper.processing_status}")
    
    # Validate the paper
    validation = validate_paper_record(paper)
    print(f"\nValidation: {'✓ Valid' if validation['valid'] else '✗ Invalid'}")
    if validation['warnings']:
        print(f"Warnings: {', '.join(validation['warnings'])}")
    
    print()


def example_3_create_chunks():
    """Example 3: Create text chunks from a paper."""
    print("=" * 60)
    print("Example 3: Creating Text Chunks")
    print("=" * 60)
    
    paper_id = "abc123def456"
    
    # Create chunks with different sections
    chunks = []
    
    chunk1 = PaperChunk(
        paper_id=paper_id,
        chunk_id=IDGenerator.generate_chunk_id(paper_id, 0),
        section_label="abstract",
        page_start=1,
        page_end=1,
        text="The dominant sequence transduction models are based on complex "
             "recurrent or convolutional neural networks..."
    )
    chunks.append(chunk1)
    
    chunk2 = PaperChunk(
        paper_id=paper_id,
        chunk_id=IDGenerator.generate_chunk_id(paper_id, 1),
        section_label="introduction",
        page_start=1,
        page_end=2,
        text="Recurrent neural networks, long short-term memory and gated "
             "recurrent neural networks in particular..."
    )
    chunks.append(chunk2)
    
    for chunk in chunks:
        print(f"Chunk ID: {chunk.chunk_id}")
        print(f"Section: {chunk.section_label}")
        print(f"Pages: {chunk.page_start}-{chunk.page_end}")
        print(f"Text preview: {chunk.get_display_text(50)}")
        print()


def example_4_create_taxonomy():
    """Example 4: Build a topic taxonomy."""
    print("=" * 60)
    print("Example 4: Building Topic Taxonomy")
    print("=" * 60)
    
    # Create Tier 1 topics (broad areas)
    t1_llm = TopicNode(
        id="T1_LLM",
        label="Large Language Models",
        description="Research on large-scale language models and transformers",
        paper_ids=["p1", "p2", "p3", "p4", "p5"]
    )
    
    t1_cv = TopicNode(
        id="T1_CV",
        label="Computer Vision",
        description="Computer vision and image processing research",
        paper_ids=["p6", "p7"]
    )
    
    # Create Tier 2 topics (mid-level)
    t2_attention = TopicNode(
        id="T2_LLM_Attention",
        label="Attention Mechanisms",
        description="Attention mechanisms in transformers",
        parent_id="T1_LLM",
        paper_ids=["p1", "p2", "p3"]
    )
    
    t2_training = TopicNode(
        id="T2_LLM_Training",
        label="Training Methods",
        description="Training techniques for large language models",
        parent_id="T1_LLM",
        paper_ids=["p4", "p5"]
    )
    
    # Create Tier 3 topics (fine-grained)
    t3_efficient = TopicNode(
        id="T3_Attention_Efficient",
        label="Efficient Attention",
        description="Methods for efficient attention computation",
        parent_id="T2_LLM_Attention",
        paper_ids=["p1", "p2"]
    )
    
    # Build hierarchy
    hierarchy = TopicHierarchy(
        taxonomy_version="v1.0",
        total_papers=7,
        tier1=[t1_llm, t1_cv],
        tier2=[t2_attention, t2_training],
        tier3=[t3_efficient],
        clustering_method="agglomerative",
        labeling_model="gpt-4"
    )
    
    # Validate hierarchy
    validation = hierarchy.validate_hierarchy()
    print(f"Hierarchy valid: {validation['valid']}")
    print(f"Total topics: {validation['total_topics']}")
    
    # Get statistics
    stats = hierarchy.get_statistics()
    print(f"\nTaxonomy Statistics:")
    print(f"  Tier 1 topics: {stats['tier1_topics']}")
    print(f"  Tier 2 topics: {stats['tier2_topics']}")
    print(f"  Tier 3 topics: {stats['tier3_topics']}")
    print(f"  Avg papers per Tier 1: {stats['avg_papers_per_tier1']:.1f}")
    
    # Navigate hierarchy
    print(f"\nTier 2 topics under '{t1_llm.label}':")
    for topic in hierarchy.get_tier2_topics(parent_tier1_id="T1_LLM"):
        print(f"  - {topic.label} ({topic.paper_count} papers)")
    
    print()


def example_5_state_management():
    """Example 5: Manage workflow state with StateManager."""
    print("=" * 60)
    print("Example 5: Managing Workflow State")
    print("=" * 60)
    
    # Create initial state
    config = create_default_config(max_papers_per_run=10)
    state = StateManager.create_initial_state(config)
    
    print(f"Initial phase: {state['current_phase']}")
    
    # Add a paper
    paper = PaperRecord(
        id="paper1",
        file_path="/path/to/paper1.pdf",
        filename="paper1.pdf",
        title="Test Paper 1"
    )
    state = StateManager.add_paper(state, paper)
    
    # Add chunks for the paper
    chunks = [
        PaperChunk(
            paper_id="paper1",
            chunk_id="paper1_chunk_0001",
            section_label="abstract",
            page_start=1,
            page_end=1,
            text="This is the abstract."
        )
    ]
    state = StateManager.add_chunks(state, "paper1", chunks)
    
    # Update paper with summary
    state = StateManager.update_paper(state, "paper1", {
        "full_summary": "This paper presents...",
        "processing_status": "summarized"
    })
    
    # Mark as complete
    state = StateManager.mark_paper_complete(state, "paper1")
    
    # Get statistics
    stats = StateManager.get_stats(state)
    print(f"\nWorkflow Statistics:")
    print(f"  Total papers: {stats['total_papers']}")
    print(f"  Completed: {stats['completed']}")
    print(f"  Pending: {stats['pending']}")
    print(f"  Total chunks: {stats['total_chunks']}")
    
    print()


def example_6_helper_utilities():
    """Example 6: Use helper utilities."""
    print("=" * 60)
    print("Example 6: Using Helper Utilities")
    print("=" * 60)
    
    # Extract arXiv ID
    filename = "paper_2301.12345v2.pdf"
    arxiv_id = MetadataExtractor.extract_arxiv_id(filename)
    print(f"Extracted arXiv ID: {arxiv_id}")
    
    # Calculate text statistics
    sample_text = "This is a sample text with some content. " * 50
    stats = StatisticsTracker.calculate_text_stats(sample_text, page_count=2)
    print(f"\nText Statistics:")
    print(f"  Total characters: {stats['chars_total']}")
    print(f"  Chars per page: {stats['chars_per_page']:.1f}")
    print(f"  Alphanumeric ratio: {stats['alnum_ratio']:.3f}")
    print(f"  Parse quality: {stats['parse_quality_score']:.3f}")
    
    # Estimate tokens
    tokens = StatisticsTracker.estimate_tokens(sample_text)
    print(f"  Estimated tokens: {tokens}")
    
    # Generate IDs
    paper_id = IDGenerator.generate_paper_id("/path/to/paper.pdf")
    chunk_id = IDGenerator.generate_chunk_id(paper_id, 5)
    topic_id = IDGenerator.generate_topic_id(1, "Machine Learning", 0)
    print(f"\nGenerated IDs:")
    print(f"  Paper ID: {paper_id}")
    print(f"  Chunk ID: {chunk_id}")
    print(f"  Topic ID: {topic_id}")
    
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("RAG Models - Usage Examples")
    print("=" * 60)
    print()
    
    example_1_create_configuration()
    example_2_create_paper_record()
    example_3_create_chunks()
    example_4_create_taxonomy()
    example_5_state_management()
    example_6_helper_utilities()
    
    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
