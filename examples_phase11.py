#!/usr/bin/env python3
"""
Phase 11 Usage Examples: Deep Analysis Pass (Optional - Pass 2)

This file demonstrates how to use the deep analysis module
for various use cases.

Examples include:
- Cost estimation for deep analysis
- Checking if deep analysis should be performed
- Generating deep analysis for papers
- Selecting papers for deep analysis
- Batch processing with different criteria
- Deep analysis validation
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

from deep_analysis_pass2 import (
    # Step 11.1
    should_perform_deep_analysis,
    check_deep_analysis_flag,
    
    # Step 11.2
    DeepAnalysisGenerator,
    deep_analysis_node,
    create_deep_analysis_generator,
    
    # Step 11.3
    DeepAnalysisPromptFactory,
    create_deep_analysis_prompt,
    
    # Step 11.4
    batch_deep_analyze_papers,
    deep_analyze_papers_worker,
    select_papers_for_deep_analysis,
    
    # Validation
    validate_deep_analysis,
    validate_paper_deep_analyses,
    
    # Cost estimation
    estimate_deep_analysis_cost,
)


# =============================================================================
# Example 1: Cost Estimation
# =============================================================================

def example_cost_estimation():
    """Example: Estimate costs before performing deep analysis."""
    print("\n" + "=" * 70)
    print("Example 1: Deep Analysis Cost Estimation")
    print("=" * 70)
    
    # Scenario: 30 papers, average 12,000 characters each
    num_papers = 30
    avg_length = 12000
    
    print(f"\nScenario: {num_papers} papers, {avg_length} chars each")
    
    # Estimate for GPT-5.1 (recommended for deep analysis)
    estimate = estimate_deep_analysis_cost(
        num_papers=num_papers,
        avg_paper_length_chars=avg_length,
        model="gpt-5.1"
    )
    
    print(f"\nCost estimate for GPT-5.1:")
    print(f"  Estimated input tokens: {estimate['estimated_input_tokens']:,}")
    print(f"  Estimated output tokens: {estimate['estimated_output_tokens']:,}")
    print(f"  Total tokens: {estimate['estimated_total_tokens']:,}")
    print(f"  Price per 1M tokens: ${estimate['price_per_1m_tokens']:.2f}")
    print(f"  Total estimated cost: ${estimate['estimated_cost_usd']:.2f}")
    print(f"  Cost per paper: ${estimate['cost_per_paper_usd']:.4f}")
    
    # Compare with GPT-5-mini (cheaper but less capable for deep analysis)
    estimate_mini = estimate_deep_analysis_cost(
        num_papers=num_papers,
        avg_paper_length_chars=avg_length,
        model="gpt-5-mini"
    )
    
    print(f"\nCost estimate for GPT-5-mini (for comparison):")
    print(f"  Total estimated cost: ${estimate_mini['estimated_cost_usd']:.2f}")
    print(f"  Cost per paper: ${estimate_mini['cost_per_paper_usd']:.4f}")
    
    savings = estimate['estimated_cost_usd'] - estimate_mini['estimated_cost_usd']
    print(f"\nCost difference: ${savings:.2f} more for GPT-5.1")
    print("Note: GPT-5.1 recommended for deep analysis due to superior reasoning")


# =============================================================================
# Example 2: Checking Deep Analysis Flag
# =============================================================================

def example_check_flag():
    """Example: Check if deep analysis should be performed."""
    print("\n" + "=" * 70)
    print("Example 2: Checking Deep Analysis Flag")
    print("=" * 70)
    
    # Create config with deep analysis enabled
    config = create_default_config()
    config.enable_deep_analysis_pass = True
    
    should_perform = should_perform_deep_analysis(config)
    print(f"\nWith enable_deep_analysis_pass=True: {should_perform}")
    
    # Disable deep analysis
    config.enable_deep_analysis_pass = False
    should_perform = should_perform_deep_analysis(config)
    print(f"With enable_deep_analysis_pass=False: {should_perform}")
    
    print("\nUse this check at the start of Phase 11 to skip if disabled")


# =============================================================================
# Example 3: Creating Deep Analysis Prompts
# =============================================================================

def example_create_prompts():
    """Example: Create prompts for deep analysis."""
    print("\n" + "=" * 70)
    print("Example 3: Creating Deep Analysis Prompts")
    print("=" * 70)
    
    # Create a sample paper
    paper = PaperRecord(
        id="example_paper",
        file_path="/papers/transformer_paper.pdf",
        filename="transformer_paper.pdf",
        title="Attention Is All You Need",
        abstract_text="We propose a new simple network architecture, the Transformer...",
        full_summary="The paper introduces the Transformer architecture which relies entirely on attention mechanisms..."
    )
    
    # Create sample chunks with methods and results
    chunks = [
        PaperChunk(
            id="chunk_methods",
            paper_id="example_paper",
            section_label="Methods",
            text="The Transformer uses stacked self-attention and point-wise, fully connected layers for both the encoder and decoder. We employ multi-head attention mechanisms...",
            cleaned_text="The Transformer uses stacked self-attention and point-wise, fully connected layers for both the encoder and decoder. We employ multi-head attention mechanisms...",
            page_start=3,
            page_end=5
        ),
        PaperChunk(
            id="chunk_results",
            paper_id="example_paper",
            section_label="Results",
            text="On the WMT 2014 English-to-German translation task, our model achieves a new state-of-the-art BLEU score of 28.4, improving over the existing best results by over 2.0 BLEU...",
            cleaned_text="On the WMT 2014 English-to-German translation task, our model achieves a new state-of-the-art BLEU score of 28.4, improving over the existing best results by over 2.0 BLEU...",
            page_start=6,
            page_end=8
        ),
    ]
    
    config = create_default_config()
    
    # Create prompts
    system_prompt, user_prompt = create_deep_analysis_prompt(paper, chunks, config)
    
    print("\nSystem Prompt (first 300 chars):")
    print(system_prompt[:300] + "...")
    
    print("\n\nUser Prompt (first 500 chars):")
    print(user_prompt[:500] + "...")
    
    print("\n\nNote: The prompts are designed to extract:")
    print("  - Detailed methodology breakdown")
    print("  - Experimental setup details")
    print("  - Key results and metrics")
    print("  - Limitations and constraints")
    print("  - Future work and extensions")
    print("  - Comprehensive technical notes")


# =============================================================================
# Example 4: Paper Selection for Deep Analysis
# =============================================================================

def example_select_papers():
    """Example: Select papers for deep analysis based on criteria."""
    print("\n" + "=" * 70)
    print("Example 4: Selecting Papers for Deep Analysis")
    print("=" * 70)
    
    # Create sample papers with different statuses
    papers = {
        f"paper_{i}": PaperRecord(
            id=f"paper_{i}",
            file_path=f"/papers/paper_{i}.pdf",
            filename=f"paper_{i}.pdf",
            processing_status=status,
            full_summary=summary,
            tier1_topic=topic,
            tier1_confidence=confidence
        )
        for i, (status, summary, topic, confidence) in enumerate([
            ("summarized", "Summary 1", None, None),
            ("classified", "Summary 2", "T1_01", 0.95),
            ("classified", "Summary 3", "T1_02", 0.75),
            ("classified", "Summary 4", "T1_01", 0.85),
            ("embedded", "Summary 5", None, None),
            ("pending", None, None, None),
        ], start=1)
    }
    
    config = create_default_config()
    config.enable_deep_analysis_pass = True
    
    # Select all eligible papers
    all_selected = select_papers_for_deep_analysis(papers, config, subset_criteria="all")
    print(f"\nAll eligible papers: {len(all_selected)} papers")
    print(f"  IDs: {all_selected}")
    
    # Select only classified papers
    classified_selected = select_papers_for_deep_analysis(papers, config, subset_criteria="classified")
    print(f"\nClassified papers only: {len(classified_selected)} papers")
    print(f"  IDs: {classified_selected}")
    
    # Select high-confidence papers (confidence >= 0.8)
    high_conf_selected = select_papers_for_deep_analysis(papers, config, subset_criteria="high_confidence")
    print(f"\nHigh-confidence papers: {len(high_conf_selected)} papers")
    print(f"  IDs: {high_conf_selected}")
    
    # Select specific papers by ID
    specific_selected = select_papers_for_deep_analysis(
        papers, 
        config, 
        subset_criteria=["paper_1", "paper_2", "paper_3"]
    )
    print(f"\nSpecific papers by ID: {len(specific_selected)} papers")
    print(f"  IDs: {specific_selected}")
    
    print("\n\nRecommendation:")
    print("  - Use 'all' for comprehensive corpus analysis")
    print("  - Use 'classified' for papers that need deeper context after taxonomy")
    print("  - Use 'high_confidence' for focused deep analysis of well-classified papers")
    print("  - Use specific IDs for targeted analysis of important papers")


# =============================================================================
# Example 5: Validation
# =============================================================================

def example_validation():
    """Example: Validate deep analysis outputs."""
    print("\n" + "=" * 70)
    print("Example 5: Validating Deep Analysis Outputs")
    print("=" * 70)
    
    # Example of a good deep analysis
    good_analysis = """
    Detailed Methodology Breakdown:
    The authors employ a transformer-based architecture with multi-head self-attention.
    They use the WMT 2014 English-German dataset with 4.5M sentence pairs.
    The model incorporates positional encodings and layer normalization.
    Training uses the Adam optimizer with warm-up learning rate scheduling.
    
    Experimental Setup Details:
    Experiments were conducted using 8 NVIDIA P100 GPUs over 12 hours.
    The baseline comparison includes LSTM-based sequence-to-sequence models.
    Evaluation uses BLEU scores on newstest2014 test set.
    Hyperparameters: 6 layers, 8 attention heads, 512 embedding dimension.
    
    Key Results and Metrics:
    Achieved BLEU score of 28.4, beating previous best of 26.3 (8% improvement).
    Training converged in 100,000 steps with stable learning curves.
    Inference is 3x faster than LSTM baselines.
    Statistical significance confirmed with bootstrap resampling (p < 0.001).
    
    Limitations and Constraints:
    Requires large amounts of parallel training data (millions of sentence pairs).
    Performance drops on out-of-domain translation tasks.
    Computational cost is high for training, requiring multiple GPUs.
    
    Future Work and Extensions:
    Exploring application to other sequence tasks like summarization.
    Investigating model interpretability through attention visualization.
    Reducing model size for deployment on resource-constrained devices.
    
    Comprehensive Notes:
    - Self-attention mechanism is key innovation enabling parallelization
    - Positional encodings crucial for capturing sequence order
    - Model scales well to longer sequences compared to RNNs
    - Approach has influenced many subsequent NLP architectures
    """
    
    is_valid, error = validate_deep_analysis(good_analysis)
    print(f"\nValidating comprehensive analysis:")
    print(f"  Valid: {is_valid}")
    if error:
        print(f"  Error: {error}")
    
    # Example of insufficient analysis
    poor_analysis = "This paper is about transformers and they work well."
    
    is_valid, error = validate_deep_analysis(poor_analysis)
    print(f"\nValidating insufficient analysis:")
    print(f"  Valid: {is_valid}")
    print(f"  Error: {error}")
    
    # Validate multiple papers
    papers = {
        "paper_1": PaperRecord(
            id="paper_1",
            file_path="/test/p1.pdf",
            filename="p1.pdf",
            deep_summary=good_analysis
        ),
        "paper_2": PaperRecord(
            id="paper_2",
            file_path="/test/p2.pdf",
            filename="p2.pdf",
            deep_summary=poor_analysis
        ),
        "paper_3": PaperRecord(
            id="paper_3",
            file_path="/test/p3.pdf",
            filename="p3.pdf",
            deep_summary=None
        ),
    }
    
    results = validate_paper_deep_analyses(papers)
    
    print(f"\nBatch validation results:")
    print(f"  Total papers: {results['total_papers']}")
    print(f"  Papers with deep analysis: {results['papers_with_deep_analysis']}")
    print(f"  Valid analyses: {results['valid_deep_analyses']}")
    print(f"  Invalid analyses: {results['invalid_deep_analyses']}")
    print(f"  Validation rate: {results['validation_rate']:.1%}")


# =============================================================================
# Example 6: Complete Workflow
# =============================================================================

def example_complete_workflow():
    """Example: Complete deep analysis workflow."""
    print("\n" + "=" * 70)
    print("Example 6: Complete Deep Analysis Workflow")
    print("=" * 70)
    
    # Step 1: Check if deep analysis should be performed
    config = create_default_config()
    config.enable_deep_analysis_pass = True
    
    if not should_perform_deep_analysis(config):
        print("\nDeep analysis is disabled. Skipping Phase 11.")
        return
    
    print("\n✓ Step 1: Deep analysis is enabled")
    
    # Step 2: Estimate costs
    num_papers = 25
    estimate = estimate_deep_analysis_cost(
        num_papers=num_papers,
        avg_paper_length_chars=10000,
        model="gpt-5.1"
    )
    
    print(f"\n✓ Step 2: Cost estimation complete")
    print(f"    Estimated cost: ${estimate['estimated_cost_usd']:.2f} for {num_papers} papers")
    print(f"    Cost per paper: ${estimate['cost_per_paper_usd']:.4f}")
    
    # Step 3: Create sample papers
    papers = {
        f"paper_{i}": PaperRecord(
            id=f"paper_{i}",
            file_path=f"/papers/paper_{i}.pdf",
            filename=f"paper_{i}.pdf",
            processing_status="classified",
            full_summary=f"Summary for paper {i}",
            tier1_topic=f"T1_{i % 3 + 1:02d}",
            tier1_confidence=0.8 + (i % 3) * 0.05
        )
        for i in range(1, 6)
    }
    
    print(f"\n✓ Step 3: Created {len(papers)} sample papers")
    
    # Step 4: Select papers for deep analysis
    # Option A: All papers
    all_papers = select_papers_for_deep_analysis(papers, config, "all")
    print(f"\n✓ Step 4a: Selected all eligible papers: {len(all_papers)} papers")
    
    # Option B: Only high-confidence papers
    high_conf_papers = select_papers_for_deep_analysis(papers, config, "high_confidence")
    print(f"✓ Step 4b: Selected high-confidence papers: {len(high_conf_papers)} papers")
    
    # Step 5: Batch process would happen here (requires API key)
    print(f"\n✓ Step 5: Batch deep analysis (requires OpenAI API key)")
    print("    In production, call:")
    print("    batch_deep_analyze_papers(papers, chunks, config, api_key, 'high_confidence')")
    
    # Step 6: Validate results
    print(f"\n✓ Step 6: Validation (after analysis)")
    print("    In production, call:")
    print("    validate_paper_deep_analyses(papers)")
    
    print("\n" + "=" * 70)
    print("Workflow complete!")
    print("=" * 70)


# =============================================================================
# Run All Examples
# =============================================================================

def run_all_examples():
    """Run all example functions."""
    print("\n" + "=" * 70)
    print("PHASE 11 EXAMPLES: Deep Analysis Pass (Optional - Pass 2)")
    print("=" * 70)
    
    examples = [
        example_cost_estimation,
        example_check_flag,
        example_create_prompts,
        example_select_papers,
        example_validation,
        example_complete_workflow,
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n⚠ Example {example_func.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_examples()
