#!/usr/bin/env python3
"""
Phase 18 Examples: Error Handling and Resilience

This module demonstrates the usage of error handling and recovery features
implemented in Phase 18.

Examples:
- Using ErrorHandler for comprehensive error logging
- Using RetryHandler for API calls with exponential backoff
- Using DataValidator for pre-processing validation
- Using ErrorRecoveryManager for failed paper recovery

Version: 1.0
Date: 2025-11-24
"""

import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import error handling components
from rag_models import (
    RunConfig,
    PaperRecord,
    GraphState,
    ErrorHandler,
    RetryHandler,
    DataValidator,
    RateLimitError,
    TransientAPIError,
)

from workflow_orchestrator import (
    ErrorRecoveryManager,
    retry_failed_papers,
    list_failed_papers,
    get_recovery_options,
    create_recovery_checkpoint,
    rollback_to_checkpoint,
)


# =============================================================================
# Example 1: Using ErrorHandler for Error Logging
# =============================================================================

def example_error_handler():
    """
    Demonstrate comprehensive error handling and logging.
    """
    print("\n" + "="*60)
    print("Example 1: ErrorHandler for Error Logging")
    print("="*60)
    
    # Initialize error handler
    error_handler = ErrorHandler()
    
    # Create a sample paper
    paper = PaperRecord(
        id="sample_paper_1",
        file_path="/data/papers/sample.pdf",
        filename="sample.pdf"
    )
    
    # Simulate an error during processing
    try:
        # Simulated processing that fails
        raise ValueError("Failed to extract metadata from PDF")
    except Exception as e:
        # Log the error with context
        error_handler.log_error(
            paper_id=paper.id,
            stage="metadata_extraction",
            error=e,
            context={
                "file_size": 1024 * 512,
                "pdf_version": "1.4",
                "attempt": 1
            }
        )
        
        # Update paper status
        paper = error_handler.update_paper_on_error(
            paper=paper,
            stage="metadata_extraction",
            error=e,
            context={"step": "arxiv_lookup"}
        )
    
    # Display results
    print(f"\nPaper status: {paper.processing_status}")
    print(f"Error reason: {paper.error_reason}")
    print(f"Error stage: {paper.error_stage}")
    print(f"Retry count: {paper.retry_count}")
    
    # Get error summary
    summary = error_handler.get_error_summary()
    print(f"\nError Summary:")
    print(f"  Total errors: {summary['total_errors']}")
    print(f"  Errors by stage: {summary['by_stage']}")
    print(f"  Errors by type: {summary['by_type']}")
    
    return error_handler


# =============================================================================
# Example 2: Using RetryHandler for API Calls
# =============================================================================

def example_retry_handler():
    """
    Demonstrate API retry logic with exponential backoff.
    """
    print("\n" + "="*60)
    print("Example 2: RetryHandler for API Calls")
    print("="*60)
    
    # Initialize retry handler
    retry_handler = RetryHandler(
        max_retries=5,
        initial_delay=1.0,
        max_delay=30.0,
        backoff_factor=2.0
    )
    
    # Example 1: Successful API call after retries
    print("\n--- Simulating API call with transient failures ---")
    
    attempt_count = [0]  # Use list to allow mutation in nested function
    
    def api_call_with_failures():
        """Simulated API call that fails initially but succeeds."""
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            print(f"  Attempt {attempt_count[0]}: API call failed (transient error)")
            raise TransientAPIError("Network timeout")
        print(f"  Attempt {attempt_count[0]}: API call succeeded")
        return {"status": "success", "data": "sample_data"}
    
    try:
        result = retry_handler.retry_with_backoff(api_call_with_failures)
        print(f"\nResult: {result}")
    except Exception as e:
        print(f"\nFailed after retries: {e}")
    
    # Example 2: Rate limit handling
    print("\n--- Simulating rate limit error ---")
    
    rate_limit_attempts = [0]
    
    def api_call_with_rate_limit():
        """Simulated API call with rate limit."""
        rate_limit_attempts[0] += 1
        if rate_limit_attempts[0] < 2:
            print(f"  Attempt {rate_limit_attempts[0]}: Rate limit hit")
            raise RateLimitError("API rate limit exceeded, retry after 60s")
        print(f"  Attempt {rate_limit_attempts[0]}: API call succeeded")
        return {"status": "success"}
    
    try:
        result = retry_handler.retry_with_backoff(api_call_with_rate_limit)
        print(f"\nResult: {result}")
    except Exception as e:
        print(f"\nFailed: {e}")
    
    return retry_handler


# =============================================================================
# Example 3: Using DataValidator for Pre-Processing Validation
# =============================================================================

def example_data_validator():
    """
    Demonstrate data validation before processing.
    """
    print("\n" + "="*60)
    print("Example 3: DataValidator for Pre-Processing Validation")
    print("="*60)
    
    # Initialize validator
    validator = DataValidator()
    
    # Example 1: Validate paper record
    print("\n--- Validating PaperRecord ---")
    
    paper = PaperRecord(
        id="test_paper_1",
        file_path="/data/papers/test.pdf",
        filename="test.pdf",
        processing_status="failed",
        error_reason=None,  # Missing error reason (warning)
        tier2_topic="ML",
        tier1_topic=None  # Inconsistency: tier2 without tier1 (error)
    )
    
    result = validator.validate_paper_record(paper)
    
    print(f"Valid: {result['valid']}")
    if result['errors']:
        print(f"Errors:")
        for error in result['errors']:
            print(f"  - {error}")
    if result['warnings']:
        print(f"Warnings:")
        for warning in result['warnings']:
            print(f"  - {warning}")
    
    # Example 2: Check required fields
    print("\n--- Checking required fields ---")
    
    incomplete_paper = PaperRecord(
        id="",  # Missing
        file_path="",  # Missing
        filename="test.pdf"
    )
    
    result = validator.validate_paper_record(
        incomplete_paper,
        required_fields=["id", "file_path", "filename", "title"]
    )
    
    print(f"Valid: {result['valid']}")
    print(f"Errors: {len(result['errors'])}")
    for error in result['errors']:
        print(f"  - {error}")
    
    return validator


# =============================================================================
# Example 4: Using ErrorRecoveryManager for Failed Paper Recovery
# =============================================================================

def example_error_recovery():
    """
    Demonstrate error recovery and retry mechanisms.
    """
    print("\n" + "="*60)
    print("Example 4: ErrorRecoveryManager for Recovery")
    print("="*60)
    
    # Create a mock state with failed papers
    state: GraphState = {
        "papers": {
            "paper1": PaperRecord(
                id="paper1",
                file_path="/data/paper1.pdf",
                filename="paper1.pdf",
                processing_status="failed",
                error_reason="PDF parsing error: corrupted file",
                error_stage="parsing",
                retry_count=0
            ),
            "paper2": PaperRecord(
                id="paper2",
                file_path="/data/paper2.pdf",
                filename="paper2.pdf",
                processing_status="failed",
                error_reason="Rate limit exceeded",
                error_stage="summarization",
                retry_count=1
            ),
            "paper3": PaperRecord(
                id="paper3",
                file_path="/data/paper3.pdf",
                filename="paper3.pdf",
                processing_status="failed",
                error_reason="Network timeout",
                error_stage="metadata",
                retry_count=2
            ),
            "paper4": PaperRecord(
                id="paper4",
                file_path="/data/paper4.pdf",
                filename="paper4.pdf",
                processing_status="classified"  # Success
            ),
        },
        "papers_failed": ["paper1", "paper2", "paper3"],
        "papers_pending": [],
        "papers_completed": ["paper4"],
        "config": RunConfig(),
    }
    
    # Example 1: List failed papers
    print("\n--- Listing Failed Papers ---")
    failed_list = list_failed_papers(state)
    
    print(f"Total failed papers: {len(failed_list)}")
    for paper_info in failed_list:
        print(f"\n  Paper: {paper_info['filename']}")
        print(f"    Stage: {paper_info['error_stage']}")
        print(f"    Reason: {paper_info['error_reason']}")
        print(f"    Retries: {paper_info['retry_count']}")
    
    # Example 2: Get recovery options
    print("\n--- Getting Recovery Options ---")
    options = get_recovery_options(state, max_retries=3)
    
    print(f"\nRecovery Options:")
    print(f"  Total failed: {options['total_failed']}")
    print(f"  Retryable: {options['retryable']}")
    print(f"  Max retries reached: {options['max_retries_reached']}")
    print(f"\n  Failures by stage:")
    for stage, count in options['failures_by_stage'].items():
        print(f"    {stage}: {count}")
    
    print(f"\n  Recommended actions:")
    for i, action in enumerate(options['recommended_actions'], 1):
        print(f"    {i}. {action}")
    
    # Example 3: Selective retry by stage
    print("\n--- Selective Retry: Metadata Errors Only ---")
    
    # Create recovery checkpoint before retry
    checkpoint_path = create_recovery_checkpoint(state, checkpoint_dir="/tmp")
    print(f"Created checkpoint: {checkpoint_path}")
    
    # Retry only metadata errors
    updated_state = retry_failed_papers(
        state,
        max_retries=3,
        filter_stage="metadata"
    )
    
    # Check results
    retried_papers = [
        p for p in updated_state["papers"].values()
        if p.id in ["paper1", "paper2", "paper3"] and p.processing_status == "pending"
    ]
    
    print(f"Papers reset for retry: {len(retried_papers)}")
    for paper in retried_papers:
        print(f"  - {paper.filename} (retry #{paper.retry_count})")
    
    # Example 4: Retry all failed papers
    print("\n--- Retry All Failed Papers ---")
    
    updated_state = retry_failed_papers(state, max_retries=3)
    
    pending_count = sum(
        1 for p in updated_state["papers"].values()
        if p.processing_status == "pending"
    )
    
    print(f"Papers now pending: {pending_count}")
    
    return updated_state


# =============================================================================
# Example 5: Complete Error Handling Workflow
# =============================================================================

def example_complete_workflow():
    """
    Demonstrate a complete error handling workflow combining all components.
    """
    print("\n" + "="*60)
    print("Example 5: Complete Error Handling Workflow")
    print("="*60)
    
    # Initialize components
    error_handler = ErrorHandler()
    retry_handler = RetryHandler(max_retries=3)
    validator = DataValidator()
    recovery_manager = ErrorRecoveryManager(max_retries=3)
    
    # Step 1: Validate input data
    print("\n--- Step 1: Validate Input Data ---")
    
    paper = PaperRecord(
        id="workflow_paper",
        file_path="/data/research_paper.pdf",
        filename="research_paper.pdf"
    )
    
    validation_result = validator.validate_paper_record(paper)
    
    if not validation_result['valid']:
        print(f"Validation failed: {validation_result['errors']}")
        return
    
    print("Validation passed ✓")
    
    # Step 2: Process with error handling
    print("\n--- Step 2: Process with Error Handling ---")
    
    def process_paper_with_api():
        """Simulated paper processing with API calls."""
        print("  Attempting to process paper...")
        # Simulate API call that might fail
        raise TransientAPIError("Connection timeout")
    
    try:
        # Use retry handler for API calls
        result = retry_handler.retry_with_backoff(process_paper_with_api)
        print("Processing succeeded ✓")
    except Exception as e:
        print(f"Processing failed: {e}")
        
        # Log error with context
        error_handler.log_error(
            paper_id=paper.id,
            stage="processing",
            error=e,
            context={"api_endpoint": "summarization", "timeout": 30}
        )
        
        # Update paper status
        paper = error_handler.update_paper_on_error(
            paper=paper,
            stage="processing",
            error=e
        )
    
    # Step 3: Create state and check recovery options
    print("\n--- Step 3: Check Recovery Options ---")
    
    state: GraphState = {
        "papers": {paper.id: paper},
        "papers_failed": [paper.id] if paper.processing_status == "failed" else [],
        "papers_pending": [],
        "papers_completed": [],
        "config": RunConfig(),
    }
    
    if paper.processing_status == "failed":
        options = get_recovery_options(state)
        print(f"Recovery options:")
        print(f"  Retryable papers: {options['retryable']}")
        print(f"  Recommendations: {len(options['recommended_actions'])}")
        
        # Step 4: Attempt recovery
        print("\n--- Step 4: Attempt Recovery ---")
        
        if options['retryable'] > 0:
            # Create checkpoint before retry
            checkpoint_path = create_recovery_checkpoint(state)
            print(f"Checkpoint created: {checkpoint_path}")
            
            # Retry failed paper
            state = retry_failed_papers(state)
            print("Paper reset for retry ✓")
            
            # Check new status
            retried_paper = state["papers"][paper.id]
            print(f"New status: {retried_paper.processing_status}")
            print(f"Retry count: {retried_paper.retry_count}")
    
    print("\n--- Workflow Complete ---")
    
    # Display final error summary
    summary = error_handler.get_error_summary()
    print(f"\nFinal Error Summary:")
    print(f"  Total errors logged: {summary['total_errors']}")
    print(f"  Errors by type: {summary['by_type']}")


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("PHASE 18: ERROR HANDLING AND RESILIENCE EXAMPLES")
    print("="*60)
    
    # Run examples
    example_error_handler()
    example_retry_handler()
    example_data_validator()
    example_error_recovery()
    example_complete_workflow()
    
    print("\n" + "="*60)
    print("ALL EXAMPLES COMPLETED")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
