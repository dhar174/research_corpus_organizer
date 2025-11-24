#!/usr/bin/env python3
"""
Phase 13: LangGraph Workflow Integration - Usage Examples

This module demonstrates how to use the workflow orchestration features:
- Running the full pipeline
- Running individual stages
- Managing checkpoints
- Monitoring progress
- Handling errors and recovery

Examples cover:
- Basic workflow execution
- Selective stage execution
- Checkpoint save/load
- Quality control
- Error recovery
- Workflow visualization
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    create_default_config,
    PaperRecord,
    StateManager,
    GraphState,
)

from workflow_orchestrator import (
    # Execution
    run_full_pipeline,
    run_ingestion_only,
    run_summarization_only,
    run_classification_only,
    rebuild_taxonomy,
    WorkflowExecutor,
    
    # Checkpointing
    save_checkpoint,
    load_checkpoint,
    CheckpointManager,
    
    # Visualization
    visualize_workflow,
    display_workflow_state,
    get_workflow_progress,
    
    # Quality Control
    check_data_quality,
    validate_pipeline_prerequisites,
    track_costs_and_time,
    
    # Error Recovery
    retry_failed_papers,
    list_failed_papers,
)


# =============================================================================
# Example 1: Basic Full Pipeline Execution
# =============================================================================

def example_full_pipeline():
    """
    Example: Run the complete RAG pipeline from start to finish.
    
    This is the simplest way to process a corpus of PDFs.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Full Pipeline Execution")
    print("=" * 70)
    
    # Create configuration
    config = create_default_config(
        drive_folder_path="/content/drive/MyDrive/PDFs",
        max_papers_per_run=50,
        summary_model="gpt-5-mini",
        taxonomy_model="gpt-5-mini",
        classification_model="gpt-5-mini",
        embedding_model="text-embedding-3-large",
        enable_deep_analysis_pass=False,
        taxonomy_approval_required=True,
    )
    
    print("\nConfiguration:")
    print(config.display_config())
    
    # Run full pipeline
    print("\nRunning full pipeline...")
    
    try:
        # In a real scenario, this would execute the complete workflow
        # For this example, we'll just show the structure
        
        # final_state = run_full_pipeline(config, checkpoint_dir="./checkpoints")
        
        print("✓ Pipeline would execute with:")
        print("  - PDF discovery from Google Drive")
        print("  - Parsing and chunking")
        print("  - Metadata extraction")
        print("  - Embedding generation")
        print("  - Summarization")
        print("  - Taxonomy building")
        print("  - Classification")
        print("  - Final export")
        
        print("\nPipeline execution complete!")
        
    except ImportError as e:
        print(f"⚠ Missing dependency: {e}")
        print("Install with: pip install langgraph")


# =============================================================================
# Example 2: Selective Stage Execution
# =============================================================================

def example_selective_execution():
    """
    Example: Run only specific stages of the pipeline.
    
    Useful when you want to:
    - Ingest papers first, review, then continue
    - Re-run summarization with different settings
    - Rebuild taxonomy with new parameters
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Selective Stage Execution")
    print("=" * 70)
    
    config = create_default_config(
        drive_folder_path="/content/drive/MyDrive/PDFs",
        max_papers_per_run=20
    )
    
    # Stage 1: Ingestion Only
    print("\n--- Stage 1: Ingestion Only ---")
    print("Running: Discovery → Parsing → Metadata → Embeddings")
    
    try:
        # ingested_state = run_ingestion_only(config)
        print("✓ Ingestion complete (simulated)")
        print("  Papers discovered, parsed, and embedded")
        
    except Exception as e:
        print(f"⚠ {e}")
    
    # Stage 2: Summarization (on already-ingested papers)
    print("\n--- Stage 2: Summarization ---")
    
    # Simulate having an ingested state
    ingested_state = StateManager.create_initial_state(config)
    
    # Add some sample papers
    for i in range(5):
        paper = PaperRecord(
            id=f"paper_{i:03d}",
            file_path=f"/test/paper_{i}.pdf",
            filename=f"paper_{i}.pdf",
            title=f"Sample Paper {i}",
            processing_status="parsed",
        )
        ingested_state = StateManager.add_paper(ingested_state, paper)
    
    try:
        # summarized_state = run_summarization_only(ingested_state)
        print("✓ Summarization complete (simulated)")
        
    except Exception as e:
        print(f"⚠ {e}")
    
    # Stage 3: Taxonomy Rebuild
    print("\n--- Stage 3: Rebuild Taxonomy ---")
    
    try:
        # new_taxonomy_state = rebuild_taxonomy(summarized_state)
        print("✓ Taxonomy rebuilt (simulated)")
        
    except Exception as e:
        print(f"⚠ {e}")
    
    # Stage 4: Classification
    print("\n--- Stage 4: Classification ---")
    
    # Would need taxonomy in state
    try:
        # classified_state = run_classification_only(new_taxonomy_state)
        print("✓ Classification complete (simulated)")
        
    except Exception as e:
        print(f"⚠ {e}")


# =============================================================================
# Example 3: Checkpoint Management
# =============================================================================

def example_checkpoints():
    """
    Example: Save and load workflow checkpoints.
    
    Checkpoints enable:
    - Resume after interruption
    - Experiment with different settings
    - Backup at key stages
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Checkpoint Management")
    print("=" * 70)
    
    # Create a sample state
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    # Add some papers
    for i in range(3):
        paper = PaperRecord(
            id=f"paper_{i:03d}",
            file_path=f"/test/paper_{i}.pdf",
            filename=f"paper_{i}.pdf",
            title=f"Paper {i}",
            processing_status="parsed",
        )
        state = StateManager.add_paper(state, paper)
    
    state["current_phase"] = "summarization"
    
    # Save checkpoint
    print("\n--- Saving Checkpoint ---")
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_path = save_checkpoint(state, checkpoint_dir=tmpdir)
        print(f"✓ Checkpoint saved: {checkpoint_path}")
        
        # List checkpoints
        manager = CheckpointManager(Path(tmpdir))
        checkpoints = manager.list_checkpoints()
        print(f"✓ Available checkpoints: {checkpoints}")
        
        # Load checkpoint
        print("\n--- Loading Checkpoint ---")
        checkpoint_name = checkpoints[0]
        loaded_state = load_checkpoint(checkpoint_name, checkpoint_dir=tmpdir)
        print(f"✓ Checkpoint loaded: {checkpoint_name}")
        print(f"  Papers: {len(loaded_state['papers'])}")
        print(f"  Current phase: {loaded_state['current_phase']}")
        
        # Resume from checkpoint
        print("\n--- Resume from Checkpoint ---")
        print("In production, would continue pipeline from loaded state")
        print("Example:")
        print("  executor = WorkflowExecutor(config)")
        print("  final_state = executor.resume_from_checkpoint('checkpoint_name')")


# =============================================================================
# Example 4: Progress Monitoring
# =============================================================================

def example_monitoring():
    """
    Example: Monitor workflow progress and state.
    
    Shows how to:
    - Display current workflow state
    - Calculate completion percentage
    - Track phase completion
    - View statistics
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Progress Monitoring")
    print("=" * 70)
    
    # Create state with various paper statuses
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    # Add papers in different states
    statuses = ["pending", "parsed", "summarized", "classified", "failed"]
    
    for i in range(20):
        status = statuses[i % len(statuses)]
        paper = PaperRecord(
            id=f"paper_{i:03d}",
            file_path=f"/test/paper_{i}.pdf",
            filename=f"paper_{i}.pdf",
            title=f"Paper {i}",
            processing_status=status,
        )
        state = StateManager.add_paper(state, paper)
        
        if status == "classified":
            state = StateManager.mark_paper_complete(state, paper.id)
        elif status == "failed":
            state = StateManager.mark_paper_failed(state, paper.id, "Test error")
    
    state["current_phase"] = "classification"
    
    # Display workflow state
    print("\n--- Workflow State Display ---")
    display = display_workflow_state(state)
    print(display)
    
    # Get detailed progress
    print("\n--- Detailed Progress ---")
    progress = get_workflow_progress(state)
    
    print(f"Current Phase: {progress['current_phase']}")
    print(f"Completion: {progress['completion_percentage']:.1f}%")
    print(f"Papers: {progress['papers_completed']}/{progress['papers_total']} completed")
    print(f"Failed: {progress['papers_failed']}")
    print(f"Errors: {progress['errors_count']}")
    
    print("\nPhases Complete:")
    for phase, complete in progress['phases_complete'].items():
        status = "✓" if complete else "✗"
        print(f"  {status} {phase}")


# =============================================================================
# Example 5: Quality Control
# =============================================================================

def example_quality_control():
    """
    Example: Check data quality and validate pipeline prerequisites.
    
    Quality checks help identify:
    - Missing metadata
    - Incomplete processing
    - Data consistency issues
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Quality Control")
    print("=" * 70)
    
    # Create state with varying quality
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    # Add papers with different quality levels
    papers_data = [
        ("paper_000", "Complete Paper", ["Author A", "Author B"], "classified", True),
        ("paper_001", "Missing Authors", None, "classified", False),
        ("paper_002", None, ["Author C"], "summarized", False),  # Missing title
        ("paper_003", "Failed Paper", ["Author D"], "failed", False),
    ]
    
    for paper_id, title, authors, status, has_summary in papers_data:
        paper = PaperRecord(
            id=paper_id,
            file_path=f"/test/{paper_id}.pdf",
            filename=f"{paper_id}.pdf",
            title=title,
            authors=authors,
            processing_status=status,
            full_summary="Summary text" if has_summary else None,
        )
        state = StateManager.add_paper(state, paper)
    
    # Check data quality
    print("\n--- Data Quality Check ---")
    quality_report = check_data_quality(state)
    
    print(f"Total Papers: {quality_report['total_papers']}")
    print(f"Papers with Issues: {quality_report['papers_with_issues']}")
    print(f"Average Quality Score: {quality_report['average_quality_score']:.2f}")
    
    print("\nQuality Distribution:")
    for level, count in quality_report['quality_distribution'].items():
        print(f"  {level}: {count}")
    
    # Validate prerequisites
    print("\n--- Prerequisite Validation ---")
    
    # Check for embedding stage
    can_embed = validate_pipeline_prerequisites(state, "embed")
    print(f"Can run embedding: {can_embed}")
    
    # Add chunks to enable embedding
    from rag_models import PaperChunk
    state["chunks"]["paper_000"] = [
        PaperChunk(
            paper_id="paper_000",
            chunk_id="chunk_001",
            section_label="abstract",
            page_start=1,
            page_end=1,
            text="Sample chunk text"
        )
    ]
    
    can_embed = validate_pipeline_prerequisites(state, "embed")
    print(f"Can run embedding (after adding chunks): {can_embed}")
    
    # Track costs
    print("\n--- Cost Tracking ---")
    cost_info = track_costs_and_time(state)
    
    print(f"Papers Processed: {cost_info['papers_processed']}")
    print(f"Chunks Processed: {cost_info['chunks_processed']}")
    print(f"\nEstimated Costs:")
    for component, cost in cost_info['estimated_costs'].items():
        if component != 'total':
            print(f"  {component}: ${cost:.4f}")
    print(f"  TOTAL: ${cost_info['estimated_costs']['total']:.4f} {cost_info['currency']}")
    print(f"\n{cost_info['note']}")


# =============================================================================
# Example 6: Error Handling and Recovery
# =============================================================================

def example_error_recovery():
    """
    Example: Handle errors and retry failed papers.
    
    Error recovery features:
    - List failed papers with error details
    - Retry failed papers with backoff
    - Track retry attempts
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Error Handling and Recovery")
    print("=" * 70)
    
    # Create state with failed papers
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    # Add mix of successful and failed papers
    for i in range(10):
        status = "failed" if i % 3 == 0 else "classified"
        error_reason = f"Processing error {i}" if status == "failed" else None
        error_stage = "parsing" if status == "failed" else None
        
        paper = PaperRecord(
            id=f"paper_{i:03d}",
            file_path=f"/test/paper_{i}.pdf",
            filename=f"paper_{i}.pdf",
            title=f"Paper {i}",
            processing_status=status,
            error_reason=error_reason,
            error_stage=error_stage,
        )
        state = StateManager.add_paper(state, paper)
        
        if status == "failed":
            state = StateManager.mark_paper_failed(state, paper.id, error_reason)
    
    # List failed papers
    print("\n--- Failed Papers ---")
    failed = list_failed_papers(state)
    
    print(f"Found {len(failed)} failed papers:")
    for paper_info in failed:
        print(f"  • {paper_info['filename']}")
        print(f"    Error: {paper_info['error_reason']}")
        print(f"    Stage: {paper_info['error_stage']}")
        print(f"    Retries: {paper_info['retry_count']}")
    
    # Retry failed papers
    print("\n--- Retrying Failed Papers ---")
    
    updated_state = retry_failed_papers(state, max_retries=3)
    
    # Check retry counts
    for paper in updated_state["papers"].values():
        if paper.retry_count > 0:
            print(f"  {paper.filename}: retry_count = {paper.retry_count}, status = {paper.processing_status}")
    
    print("\n✓ Failed papers reset for retry")
    print("  Papers moved from 'failed' to 'pending' queue")
    print("  Will be retried in next pipeline run")
    
    # Show updated statistics
    stats = StateManager.get_stats(updated_state)
    print(f"\nUpdated Statistics:")
    print(f"  Pending: {stats['pending']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Completed: {stats['completed']}")


# =============================================================================
# Example 7: Workflow Visualization
# =============================================================================

def example_visualization():
    """
    Example: Visualize the workflow graph.
    
    Shows the complete pipeline structure and flow.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Workflow Visualization")
    print("=" * 70)
    
    config = create_default_config()
    
    # Generate Mermaid diagram
    print("\n--- Mermaid Flowchart ---")
    mermaid = visualize_workflow(config, output_format="mermaid")
    print(mermaid)
    
    # Generate ASCII diagram
    print("\n--- ASCII Flowchart ---")
    ascii_diagram = visualize_workflow(config, output_format="ascii")
    print(ascii_diagram)
    
    print("\nNote: Copy the Mermaid diagram to a Markdown cell in Jupyter/Colab")
    print("to see an interactive flowchart visualization.")


# =============================================================================
# Example 8: Advanced Workflow Control
# =============================================================================

def example_advanced_control():
    """
    Example: Advanced workflow control with WorkflowExecutor.
    
    Demonstrates:
    - Custom checkpoint directories
    - Resuming from specific checkpoints
    - Conditional execution
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 8: Advanced Workflow Control")
    print("=" * 70)
    
    config = create_default_config(
        drive_folder_path="/content/drive/MyDrive/PDFs",
        max_papers_per_run=100
    )
    
    # Create executor with custom checkpoint directory
    print("\n--- Creating Workflow Executor ---")
    executor = WorkflowExecutor(config, checkpoint_dir="./my_checkpoints")
    print("✓ Executor created with checkpoint directory: ./my_checkpoints")
    
    # Run full pipeline with checkpointing
    print("\n--- Running Full Pipeline ---")
    print("Pipeline would:")
    print("  1. Execute all stages sequentially")
    print("  2. Save checkpoints at each stage")
    print("  3. Enable resume if interrupted")
    
    # Example code (commented as it would need real data):
    # final_state = executor.run_full_pipeline(save_checkpoints=True)
    
    # Resume from checkpoint
    print("\n--- Resume from Checkpoint ---")
    print("To resume after interruption:")
    print("  checkpoints = executor.checkpoint_manager.list_checkpoints()")
    print("  latest = checkpoints[-1]")
    print("  state = executor.resume_from_checkpoint(latest)")
    
    # Conditional execution based on state
    print("\n--- Conditional Execution ---")
    print("Example: Only run classification if taxonomy approved")
    print("")
    print("if state.get('taxonomy_approved'):")
    print("    state = run_classification_only(state)")
    print("else:")
    print("    print('Taxonomy not approved, skipping classification')")


# =============================================================================
# Run All Examples
# =============================================================================

def run_all_examples():
    """Run all example demonstrations."""
    print("=" * 70)
    print("PHASE 13: LANGGRAPH WORKFLOW INTEGRATION - EXAMPLES")
    print("=" * 70)
    
    examples = [
        example_full_pipeline,
        example_selective_execution,
        example_checkpoints,
        example_monitoring,
        example_quality_control,
        example_error_recovery,
        example_visualization,
        example_advanced_control,
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n✗ Example failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("EXAMPLES COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Copy these patterns to your notebook")
    print("2. Adapt configurations to your needs")
    print("3. Run on your PDF corpus")
    print("4. Monitor progress and handle errors")


if __name__ == "__main__":
    run_all_examples()
