#!/usr/bin/env python3
"""
Phase 6 Usage Examples: Summarization (Pass 1)

This file demonstrates how to use the summarization module
for various use cases.

Examples include:
- Cost estimation for summarization
- Generating summaries for papers
- Creating initial analysis notes
- Batch processing with retries
- Summary validation
- Exporting summarized papers
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    PaperRecord,
    PaperChunk,
    StateManager,
    create_default_config,
)

from summarization_pass1 import (
    # Step 6.1
    SummaryGenerator,
    summarize_paper_node,
    create_summary_generator,
    
    # Step 6.2
    SummaryPromptFactory,
    create_summary_prompt,
    create_notes_prompt,
    
    # Step 6.3
    generate_initial_notes,
    extract_key_insights,
    
    # Step 6.4
    batch_summarize_papers,
    summarize_papers_worker,
    
    # Step 6.5
    validate_summary,
    validate_paper_summaries,
    
    # Cost estimation
    estimate_summarization_cost,
)

from export_manager import (
    export_papers_to_csv,
    export_after_pass1,
    validate_export,
    export_summary_statistics,
)


# =============================================================================
# Example 1: Cost Estimation
# =============================================================================

def example_cost_estimation():
    """Example: Estimate costs before summarizing papers."""
    print("\n" + "=" * 70)
    print("Example 1: Summarization Cost Estimation")
    print("=" * 70)
    
    # Scenario: 50 papers, average 10,000 characters each
    num_papers = 50
    avg_length = 10000
    
    print(f"\nScenario: {num_papers} papers, {avg_length} chars each")
    
    # Estimate for different models
    models = [
        "gpt-5-mini",
        "gpt-5.1",
        "gpt-4-turbo",
    ]
    
    print("\nCost estimates by model (with notes):")
    for model in models:
        estimate = estimate_summarization_cost(
            num_papers=num_papers,
            avg_paper_length_chars=avg_length,
            model=model,
            include_notes=True
        )
        
        print(f"\n  {model}:")
        print(f"    Estimated tokens: {estimate['estimated_tokens']:,}")
        print(f"    Summary tokens: {estimate['estimated_tokens_summary']:,}")
        print(f"    Notes tokens: {estimate['estimated_tokens_notes']:,}")
        print(f"    Estimated cost: ${estimate['estimated_cost_usd']:.2f} USD")
        print(f"    Cost per paper: ${estimate['cost_per_paper_usd']:.3f} USD")
    
    print("\n💡 Tip: Use gpt-5.1-mini for cost-effective summarization")


# =============================================================================
# Example 2: Summary Prompt Design
# =============================================================================

def example_prompt_design():
    """Example: Design and customize summary prompts."""
    print("\n" + "=" * 70)
    print("Example 2: Summary Prompt Design")
    print("=" * 70)
    
    # Create sample paper
    paper = PaperRecord(
        id="paper1",
        file_path="/test/paper.pdf",
        filename="paper.pdf",
        title="Deep Learning for Natural Language Processing",
        authors=["Dr. Jane Smith", "Prof. John Doe"],
        abstract_text="This paper introduces a novel approach to NLP using transformers..."
    )
    
    # Create sample chunks
    chunks = [
        PaperChunk(
            paper_id="paper1",
            chunk_id="chunk1",
            section_label="abstract",
            page_start=1,
            page_end=1,
            text=paper.abstract_text
        ),
        PaperChunk(
            paper_id="paper1",
            chunk_id="chunk2",
            section_label="introduction",
            page_start=1,
            page_end=2,
            text="Natural language processing has seen tremendous progress..."
        ),
    ]
    
    config = create_default_config()
    
    # Create prompts
    system_prompt, user_prompt = create_summary_prompt(paper, chunks, config)
    
    print("\nSystem Prompt (excerpt):")
    print(system_prompt[:300] + "...")
    
    print("\nUser Prompt (excerpt):")
    print(user_prompt[:400] + "...")
    
    print("\n💡 Tip: Customize SummaryPromptFactory for domain-specific summaries")


# =============================================================================
# Example 3: Generate Summary for Single Paper
# =============================================================================

def example_single_paper_summary():
    """Example: Generate summary for a single paper."""
    print("\n" + "=" * 70)
    print("Example 3: Single Paper Summarization")
    print("=" * 70)
    
    # Create state with paper
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    paper = PaperRecord(
        id="paper1",
        file_path="/test/paper.pdf",
        filename="paper.pdf",
        title="Attention Is All You Need",
        abstract_text="We propose a new architecture based solely on attention mechanisms..."
    )
    
    state = StateManager.add_paper(state, paper)
    
    chunks = [
        PaperChunk(
            paper_id="paper1",
            chunk_id="chunk1",
            section_label="abstract",
            page_start=1,
            page_end=1,
            text=paper.abstract_text
        ),
    ]
    
    state = StateManager.add_chunks(state, "paper1", chunks)
    
    print("\nTo generate summary (requires API key):")
    print("""
    from summarization_pass1 import summarize_paper_node
    
    # Generate summary
    updated_state = summarize_paper_node(
        paper_id="paper1",
        state=state,
        api_key="your-api-key-here"
    )
    
    # Check result
    paper = updated_state["papers"]["paper1"]
    print(f"Summary: {paper.full_summary}")
    print(f"Status: {paper.processing_status}")
    
    # Check stats
    print(f"Tokens used: {updated_state['stats']['summarization_tokens']}")
    print(f"Cost: ${updated_state['stats']['summarization_cost_usd']:.4f}")
    """)


# =============================================================================
# Example 4: Batch Summarization
# =============================================================================

def example_batch_summarization():
    """Example: Batch process multiple papers."""
    print("\n" + "=" * 70)
    print("Example 4: Batch Summarization")
    print("=" * 70)
    
    # Create state with multiple papers
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    papers_data = [
        ("paper1", "Deep Learning Fundamentals"),
        ("paper2", "Neural Network Architectures"),
        ("paper3", "Transfer Learning in NLP"),
    ]
    
    for paper_id, title in papers_data:
        paper = PaperRecord(
            id=paper_id,
            file_path=f"/test/{paper_id}.pdf",
            filename=f"{paper_id}.pdf",
            title=title,
            abstract_text=f"Abstract for {title}..."
        )
        state = StateManager.add_paper(state, paper)
        
        chunks = [
            PaperChunk(
                paper_id=paper_id,
                chunk_id=f"{paper_id}_chunk1",
                section_label="abstract",
                page_start=1,
                page_end=1,
                text=f"Content for {title}..."
            ),
        ]
        state = StateManager.add_chunks(state, paper_id, chunks)
    
    print(f"\nCreated {len(papers_data)} papers")
    
    print("\nTo batch process (requires API key):")
    print("""
    from summarization_pass1 import batch_summarize_papers
    
    # Process all papers
    updated_state = batch_summarize_papers(
        state=state,
        api_key="your-api-key-here",
        include_notes=True,
        show_progress=True
    )
    
    # Check results
    print(f"Papers summarized: {updated_state['stats']['papers_summarized']}")
    print(f"Papers failed: {updated_state['stats']['papers_failed_summary']}")
    print(f"Total cost: ${updated_state['stats']['summarization_cost_usd']:.2f}")
    
    # Review summaries
    for paper_id, paper in updated_state["papers"].items():
        if paper.full_summary:
            print(f"\\n{paper.title}:")
            print(f"  Summary length: {len(paper.full_summary)} chars")
            print(f"  Has notes: {bool(paper.initial_notes)}")
    """)


# =============================================================================
# Example 5: Initial Notes Generation
# =============================================================================

def example_notes_generation():
    """Example: Generate initial analysis notes."""
    print("\n" + "=" * 70)
    print("Example 5: Initial Notes Generation")
    print("=" * 70)
    
    print("\nInitial notes provide researcher-friendly insights:")
    print("  - Key concepts and terminology")
    print("  - Methodological approach notes")
    print("  - Important insights and takeaways")
    print("  - Research context")
    
    print("\nTo generate notes (requires API key):")
    print("""
    from summarization_pass1 import generate_initial_notes
    
    # After generating summary
    updated_state = generate_initial_notes(
        paper_id="paper1",
        state=state,
        api_key="your-api-key-here"
    )
    
    # Access notes
    paper = updated_state["papers"]["paper1"]
    print(f"Initial Notes:\\n{paper.initial_notes}")
    
    # Extract key insights programmatically
    from summarization_pass1 import extract_key_insights
    insights = extract_key_insights(paper.full_summary, paper.initial_notes)
    for i, insight in enumerate(insights, 1):
        print(f"{i}. {insight}")
    """)


# =============================================================================
# Example 6: Summary Validation
# =============================================================================

def example_summary_validation():
    """Example: Validate generated summaries."""
    print("\n" + "=" * 70)
    print("Example 6: Summary Validation")
    print("=" * 70)
    
    # Sample summaries (good and bad)
    good_summary = """
**Main Contribution**: This paper introduces the Transformer architecture, 
which relies entirely on attention mechanisms without recurrence or convolutions.

**Problem Statement**: Previous sequence transduction models relied on recurrent 
or convolutional neural networks, which are slow to train on long sequences.

**Methodology**: The Transformer uses multi-head self-attention and position-wise 
feed-forward networks in an encoder-decoder structure.

**Key Findings**: The model achieves state-of-the-art results on machine translation 
tasks while being significantly faster to train than recurrent models.

**Significance**: This work fundamentally changed how sequence modeling is approached 
in NLP and enabled the development of modern large language models.
"""
    
    bad_summary = "This paper is about transformers."
    
    paper = PaperRecord(
        id="paper1",
        file_path="/test/paper.pdf",
        filename="paper.pdf",
        title="Test Paper"
    )
    
    print("\nValidating good summary:")
    validation = validate_summary(good_summary, paper)
    print(f"  Valid: {validation['valid']}")
    print(f"  Length: {validation['length']} words")
    print(f"  Issues: {validation['issues']}")
    print(f"  Warnings: {validation['warnings']}")
    
    print("\nValidating bad summary:")
    validation = validate_summary(bad_summary, paper)
    print(f"  Valid: {validation['valid']}")
    print(f"  Length: {validation['length']} words")
    print(f"  Issues: {validation['issues']}")
    print(f"  Warnings: {validation['warnings']}")
    
    print("\n💡 Tip: Validation catches common summary quality issues")


# =============================================================================
# Example 7: Complete Pipeline with Worker
# =============================================================================

def example_complete_pipeline():
    """Example: Complete summarization pipeline using worker."""
    print("\n" + "=" * 70)
    print("Example 7: Complete Pipeline with Worker")
    print("=" * 70)
    
    print("\nThe worker orchestrates the complete Phase 6 workflow:")
    print("  1. Batch process all papers for summarization")
    print("  2. Generate initial notes for each paper")
    print("  3. Validate all summaries")
    print("  4. Update state with statistics")
    
    print("\nUsage:")
    print("""
    from summarization_pass1 import summarize_papers_worker
    from rag_models import StateManager, create_default_config
    
    # Create state with papers and chunks (from previous phases)
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    # ... add papers and chunks to state ...
    
    # Run complete summarization workflow
    updated_state = summarize_papers_worker(
        state=state,
        api_key="your-api-key-here"
    )
    
    # Check results
    print(f"Phase: {updated_state['current_phase']}")  # "summarization_pass1"
    print(f"Papers summarized: {updated_state['stats']['papers_summarized']}")
    print(f"Valid summaries: {updated_state['stats']['summary_validation']['valid_count']}")
    print(f"Total cost: ${updated_state['stats']['summarization_cost_usd']:.2f}")
    print(f"Time: {updated_state['stats']['summarization_time_seconds']:.1f}s")
    """)


# =============================================================================
# Example 8: Export After Summarization
# =============================================================================

def example_export_after_pass1():
    """Example: Export papers after summarization."""
    print("\n" + "=" * 70)
    print("Example 8: Export After Pass 1")
    print("=" * 70)
    
    # Create state with summarized papers
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    paper = PaperRecord(
        id="paper1",
        file_path="/test/paper.pdf",
        filename="paper.pdf",
        title="Sample Paper",
        full_summary="This is a comprehensive summary...",
        initial_notes="Key concepts: transformers, attention...",
        processing_status="summarized"
    )
    
    state = StateManager.add_paper(state, paper)
    
    print("\nExporting papers to CSV:")
    print("""
    from export_manager import export_after_pass1
    
    # Export all papers (including partial)
    updated_state = export_after_pass1(
        state=state,
        output_path="/drive/exports/papers_pass1.csv",
        include_partial=True,
        save_metadata=True
    )
    
    print(f"Exported to: {updated_state['master_csv_path']}")
    
    # Validate export
    from export_manager import validate_export
    validation = validate_export(
        export_path=updated_state['master_csv_path'],
        expected_count=len(state["papers"])
    )
    
    print(f"Export valid: {validation['valid']}")
    print(f"Rows: {validation['row_count']}")
    print(f"File size: {validation['file_size'] / 1024:.1f} KB")
    
    # Get statistics
    from export_manager import export_summary_statistics
    stats = export_summary_statistics(updated_state['master_csv_path'], state)
    print(f"Papers with summary: {stats.get('papers_with_summary', 'N/A')}")
    """)


# =============================================================================
# Main Example Runner
# =============================================================================

def run_all_examples():
    """Run all Phase 6 examples."""
    print("\n" + "=" * 70)
    print("PHASE 6: SUMMARIZATION (PASS 1) - USAGE EXAMPLES")
    print("=" * 70)
    
    examples = [
        example_cost_estimation,
        example_prompt_design,
        example_single_paper_summary,
        example_batch_summarization,
        example_notes_generation,
        example_summary_validation,
        example_complete_pipeline,
        example_export_after_pass1,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n⚠️  Example error: {e}")
    
    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 70)
    print("\nNote: Some examples show code snippets. To run them:")
    print("  1. Install dependencies: pip install openai pandas tqdm")
    print("  2. Set your OpenAI API key")
    print("  3. Ensure you have papers and chunks from previous phases")
    print("  4. Run the code snippets in your environment")
    print("\nFor more details, see summarization_pass1.py and export_manager.py")
    print("=" * 70)


if __name__ == "__main__":
    run_all_examples()
