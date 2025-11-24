#!/usr/bin/env python3
"""
Phase 17 Examples: Cost Tracking and Optimization

This module provides practical examples of using the cost tracking system.

Examples:
1. Basic cost tracking
2. Budget controls and warnings
3. Cost optimization with caching
4. Generating cost reports
5. Integration with pipeline

Version: 1.0
Date: 2025-11-24
"""

import os
from rag_models import (
    RunConfig,
    CostTracker,
    BudgetExceededError,
    StateManager,
)


def example_1_basic_cost_tracking():
    """
    Example 1: Basic cost tracking for API calls.
    
    Demonstrates:
    - Creating a CostTracker
    - Recording API calls
    - Viewing cost breakdown
    """
    print("=" * 70)
    print("EXAMPLE 1: Basic Cost Tracking")
    print("=" * 70)
    
    # Create configuration with cost tracking enabled
    config = RunConfig(
        drive_folder_path="PDFs",
        enable_cost_tracking=True,
        max_cost_per_run=None,  # No budget limit for this example
    )
    
    # Create cost tracker
    tracker = CostTracker(config)
    
    # Simulate some API calls
    print("\nRecording API calls...")
    
    # Embedding generation
    tracker.record_api_call(
        operation="embedding",
        model="text-embedding-3-large",
        input_tokens=10000,
        output_tokens=0,
        paper_id="paper_001",
    )
    print(f"✓ Embedding recorded. Current cost: ${tracker.total_cost:.4f}")
    
    # Summarization
    tracker.record_api_call(
        operation="summarization",
        model="gpt-5-mini",
        input_tokens=5000,
        output_tokens=2000,
        paper_id="paper_001",
    )
    print(f"✓ Summarization recorded. Current cost: ${tracker.total_cost:.4f}")
    
    # Classification
    tracker.record_api_call(
        operation="classification",
        model="gpt-5-mini",
        input_tokens=3000,
        output_tokens=1000,
        paper_id="paper_001",
    )
    print(f"✓ Classification recorded. Current cost: ${tracker.total_cost:.4f}")
    
    # Print summary
    print("\n" + "-" * 70)
    tracker.print_summary()


def example_2_budget_controls():
    """
    Example 2: Budget controls and warnings.
    
    Demonstrates:
    - Setting budget limits
    - Budget warnings
    - BudgetExceededError handling
    """
    print("\n" * 2)
    print("=" * 70)
    print("EXAMPLE 2: Budget Controls")
    print("=" * 70)
    
    # Create configuration with strict budget
    config = RunConfig(
        drive_folder_path="PDFs",
        enable_cost_tracking=True,
        max_cost_per_run=0.01,  # $0.01 budget
        cost_warning_threshold=0.5,  # Warn at 50%
    )
    
    tracker = CostTracker(config)
    print(f"\nBudget set to: ${config.max_cost_per_run:.2f}")
    print(f"Warning threshold: {config.cost_warning_threshold * 100:.0f}%")
    
    # Record calls until budget warning
    print("\nProcessing papers...")
    paper_count = 0
    
    try:
        for i in range(100):  # Try to process many papers
            # Simulate embedding + summarization for each paper
            tracker.record_api_call(
                operation="embedding",
                model="text-embedding-3-large",
                input_tokens=1000,
                paper_id=f"paper_{i}",
            )
            
            tracker.record_api_call(
                operation="summarization",
                model="gpt-5-mini",
                input_tokens=500,
                output_tokens=200,
                paper_id=f"paper_{i}",
            )
            
            paper_count += 1
            
    except BudgetExceededError as e:
        print(f"\n❌ {e}")
        print(f"✓ Successfully processed {paper_count} papers before budget limit")
    
    # Print final report
    print("\nFinal cost report:")
    tracker.print_summary()


def example_3_cost_optimization_caching():
    """
    Example 3: Cost optimization with result caching.
    
    Demonstrates:
    - Using cache to avoid duplicate API calls
    - Cost savings from caching
    """
    print("\n" * 2)
    print("=" * 70)
    print("EXAMPLE 3: Cost Optimization with Caching")
    print("=" * 70)
    
    # Configuration with caching enabled
    config = RunConfig(
        drive_folder_path="PDFs",
        enable_cost_tracking=True,
        enable_result_caching=True,
    )
    
    tracker = CostTracker(config)
    
    # Simulate processing the same paper twice
    print("\nScenario: Processing the same paper twice")
    print("-" * 70)
    
    paper_id = "duplicate_paper"
    paper_text = "This is sample paper text for summarization"
    
    # First processing - no cache
    cache_key = tracker.get_cache_key(
        operation="summarization",
        paper_id=paper_id,
        text_hash=hash(paper_text),
    )
    
    cached_result = tracker.get_cached_result(cache_key)
    
    if cached_result is None:
        print("\n1st attempt: Cache miss - calling API")
        tracker.record_api_call(
            operation="summarization",
            model="gpt-5-mini",
            input_tokens=5000,
            output_tokens=2000,
            paper_id=paper_id,
        )
        # Simulate caching the result
        summary_result = {"summary": "Sample summary"}
        tracker.cache_result(cache_key, summary_result)
        print(f"   Cost: ${tracker.total_cost:.4f}")
    
    # Second processing - should hit cache
    cost_before = tracker.total_cost
    cached_result = tracker.get_cached_result(cache_key)
    
    if cached_result is not None:
        print("\n2nd attempt: Cache hit - no API call needed!")
        print(f"   Cost: ${tracker.total_cost:.4f} (no change)")
        print(f"   Savings: ${cost_before:.4f}")
    
    print("\n" + "-" * 70)
    print(f"Total cost with caching: ${tracker.total_cost:.4f}")
    print(f"Cost without caching would be: ${tracker.total_cost * 2:.4f}")
    print(f"Savings: ${tracker.total_cost:.4f} (50%)")


def example_4_batch_api_savings():
    """
    Example 4: Cost savings with batch API.
    
    Demonstrates:
    - 50% discount with batch API
    - Comparing batch vs. non-batch costs
    """
    print("\n" * 2)
    print("=" * 70)
    print("EXAMPLE 4: Batch API Cost Savings")
    print("=" * 70)
    
    # Create two trackers for comparison
    config_no_batch = RunConfig(
        drive_folder_path="PDFs",
        enable_cost_tracking=True,
        batch_api_calls=False,
    )
    
    config_with_batch = RunConfig(
        drive_folder_path="PDFs",
        enable_cost_tracking=True,
        batch_api_calls=True,
    )
    
    tracker_no_batch = CostTracker(config_no_batch)
    tracker_with_batch = CostTracker(config_with_batch)
    
    # Simulate processing 10 papers
    num_papers = 10
    print(f"\nProcessing {num_papers} papers for summarization...")
    
    for i in range(num_papers):
        # Without batch
        tracker_no_batch.record_api_call(
            operation="summarization",
            model="gpt-5-mini",
            input_tokens=5000,
            output_tokens=2000,
            paper_id=f"paper_{i}",
            is_batch=False,
        )
        
        # With batch
        tracker_with_batch.record_api_call(
            operation="summarization",
            model="gpt-5-mini",
            input_tokens=5000,
            output_tokens=2000,
            paper_id=f"paper_{i}",
            is_batch=True,
        )
    
    print("\n" + "-" * 70)
    print("COMPARISON:")
    print(f"  Without batch API: ${tracker_no_batch.total_cost:.4f}")
    print(f"  With batch API:    ${tracker_with_batch.total_cost:.4f}")
    print(f"  Savings:           ${tracker_no_batch.total_cost - tracker_with_batch.total_cost:.4f} (50%)")
    print("-" * 70)


def example_5_cost_report_generation():
    """
    Example 5: Generating comprehensive cost reports.
    
    Demonstrates:
    - Running a complete pipeline simulation
    - Generating detailed cost report
    - Saving report to file
    """
    print("\n" * 2)
    print("=" * 70)
    print("EXAMPLE 5: Cost Report Generation")
    print("=" * 70)
    
    config = RunConfig(
        drive_folder_path="PDFs",
        enable_cost_tracking=True,
        max_cost_per_run=5.0,
        cost_warning_threshold=0.8,
        batch_api_calls=True,
        enable_result_caching=True,
    )
    
    tracker = CostTracker(config)
    
    # Simulate complete pipeline for 5 papers
    num_papers = 5
    print(f"\nSimulating complete pipeline for {num_papers} papers...")
    
    for i in range(num_papers):
        paper_id = f"paper_{i:03d}"
        
        # 1. Embedding generation
        tracker.record_api_call(
            operation="embedding",
            model="text-embedding-3-large",
            input_tokens=8000,
            paper_id=paper_id,
            is_batch=True,
        )
        
        # 2. Summarization
        tracker.record_api_call(
            operation="summarization",
            model="gpt-5-mini",
            input_tokens=6000,
            output_tokens=2000,
            paper_id=paper_id,
            is_batch=True,
        )
        
        # 3. Classification
        tracker.record_api_call(
            operation="classification",
            model="gpt-5-mini",
            input_tokens=3000,
            output_tokens=1000,
            paper_id=paper_id,
        )
    
    # Taxonomy generation (once)
    tracker.record_api_call(
        operation="taxonomy",
        model="gpt-5-mini",
        input_tokens=10000,
        output_tokens=5000,
    )
    
    print(f"✓ Pipeline complete for {num_papers} papers")
    
    # Generate and display report
    print("\n" + "=" * 70)
    tracker.print_summary()
    
    # Save report to file
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = os.path.join(tmpdir, "cost_report.json")
        saved_path = tracker.save_report(report_path)
        print(f"\n✓ Cost report saved to: {saved_path}")
        
        # Show file size
        file_size = os.path.getsize(saved_path)
        print(f"  Report size: {file_size} bytes")


def example_6_integration_with_state():
    """
    Example 6: Integration with GraphState.
    
    Demonstrates:
    - Creating state with cost tracking
    - Updating costs during pipeline
    - Retrieving cost information from state
    """
    print("\n" * 2)
    print("=" * 70)
    print("EXAMPLE 6: Integration with GraphState")
    print("=" * 70)
    
    # Create configuration and state
    config = RunConfig(
        drive_folder_path="PDFs",
        enable_cost_tracking=True,
        max_cost_per_run=10.0,
    )
    
    state = StateManager.create_initial_state(config)
    
    # Initialize cost tracker in state
    state["cost_tracker"] = CostTracker(config)
    
    print("\nInitial state:")
    print(f"  Total cost: ${state['total_cost']:.4f}")
    print(f"  Cost breakdown: {state['cost_breakdown']}")
    
    # Simulate pipeline operations
    print("\nSimulating pipeline operations...")
    
    # Operation 1: Embeddings
    state["cost_tracker"].record_api_call(
        operation="embedding",
        model="text-embedding-3-large",
        input_tokens=5000,
    )
    state["total_cost"] = state["cost_tracker"].total_cost
    state["cost_breakdown"]["embedding"] = state["cost_tracker"].cost_by_operation["embedding"]
    
    print(f"  After embeddings: ${state['total_cost']:.4f}")
    
    # Operation 2: Summarization
    state["cost_tracker"].record_api_call(
        operation="summarization",
        model="gpt-5-mini",
        input_tokens=4000,
        output_tokens=1500,
    )
    state["total_cost"] = state["cost_tracker"].total_cost
    state["cost_breakdown"]["summarization"] = state["cost_tracker"].cost_by_operation["summarization"]
    
    print(f"  After summarization: ${state['total_cost']:.4f}")
    
    # Display final state
    print("\nFinal state:")
    print(f"  Total cost: ${state['total_cost']:.4f}")
    print(f"  Cost breakdown:")
    for operation, cost in state["cost_breakdown"].items():
        print(f"    {operation}: ${cost:.4f}")


def run_all_examples():
    """Run all examples in sequence."""
    print("\n" + "=" * 70)
    print("PHASE 17: COST TRACKING AND OPTIMIZATION EXAMPLES")
    print("=" * 70)
    
    examples = [
        ("Basic Cost Tracking", example_1_basic_cost_tracking),
        ("Budget Controls", example_2_budget_controls),
        ("Cost Optimization with Caching", example_3_cost_optimization_caching),
        ("Batch API Savings", example_4_batch_api_savings),
        ("Cost Report Generation", example_5_cost_report_generation),
        ("Integration with GraphState", example_6_integration_with_state),
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        try:
            func()
        except Exception as e:
            print(f"\n❌ Example {i} ({name}) failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run_all_examples()
