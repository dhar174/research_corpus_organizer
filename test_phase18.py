#!/usr/bin/env python3
"""
Test suite for Phase 18: Error Handling and Resilience

This module tests:
- Step 18.1: Global error handler (try-except, logging, status updates)
- Step 18.2: API error handling (rate limits, exponential backoff, retries)
- Step 18.3: Data validation error handling (invalid PDFs, corrupt files)
- Step 18.4: Recovery mechanisms (checkpoints, retry, rollback)

Version: 1.0
Date: 2025-11-24
"""

import unittest
import tempfile
import json
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Import models and error handling
from rag_models import (
    RunConfig,
    PaperRecord,
    GraphState,
    ErrorHandler,
    APIError,
    RateLimitError,
    QuotaExceededError,
    TransientAPIError,
    RetryHandler,
    ValidationError,
    PDFValidationError,
    DataValidator,
)

# Import workflow orchestration and recovery
from workflow_orchestrator import (
    ErrorRecoveryManager,
    retry_failed_papers,
    list_failed_papers,
    get_recovery_options,
    create_recovery_checkpoint,
    rollback_to_checkpoint,
)


class TestErrorHandler(unittest.TestCase):
    """Test Step 18.1: Global error handler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        self.paper = PaperRecord(
            id="test_paper_1",
            file_path="/test/paper1.pdf",
            filename="paper1.pdf"
        )
    
    def test_log_error(self):
        """Test error logging with context."""
        error = ValueError("Test error message")
        context = {"test_key": "test_value"}
        
        self.error_handler.log_error(
            paper_id=self.paper.id,
            stage="parsing",
            error=error,
            context=context
        )
        
        self.assertEqual(len(self.error_handler.errors), 1)
        
        error_record = self.error_handler.errors[0]
        self.assertEqual(error_record["paper_id"], self.paper.id)
        self.assertEqual(error_record["stage"], "parsing")
        self.assertEqual(error_record["error_type"], "ValueError")
        self.assertEqual(error_record["error_message"], "Test error message")
        self.assertEqual(error_record["context"], context)
    
    def test_update_paper_on_error(self):
        """Test paper status update on error."""
        error = RuntimeError("Processing failed")
        
        updated_paper = self.error_handler.update_paper_on_error(
            paper=self.paper,
            stage="summarization",
            error=error,
            context={"step": "llm_call"}
        )
        
        self.assertEqual(updated_paper.processing_status, "failed")
        self.assertEqual(updated_paper.error_reason, "Processing failed")
        self.assertEqual(updated_paper.error_stage, "summarization")
        self.assertEqual(updated_paper.retry_count, 1)
        
        # Check error was logged
        self.assertEqual(len(self.error_handler.errors), 1)
    
    def test_get_errors_by_paper(self):
        """Test filtering errors by paper ID."""
        error1 = ValueError("Error 1")
        error2 = ValueError("Error 2")
        
        self.error_handler.log_error("paper1", "stage1", error1)
        self.error_handler.log_error("paper2", "stage1", error2)
        self.error_handler.log_error("paper1", "stage2", error1)
        
        paper1_errors = self.error_handler.get_errors_by_paper("paper1")
        self.assertEqual(len(paper1_errors), 2)
    
    def test_get_errors_by_stage(self):
        """Test filtering errors by stage."""
        error = ValueError("Test error")
        
        self.error_handler.log_error("paper1", "parsing", error)
        self.error_handler.log_error("paper2", "summarization", error)
        self.error_handler.log_error("paper3", "parsing", error)
        
        parsing_errors = self.error_handler.get_errors_by_stage("parsing")
        self.assertEqual(len(parsing_errors), 2)
    
    def test_get_error_summary(self):
        """Test error summary generation."""
        self.error_handler.log_error("paper1", "parsing", ValueError("Error 1"))
        self.error_handler.log_error("paper2", "parsing", RuntimeError("Error 2"))
        self.error_handler.log_error("paper3", "summarization", ValueError("Error 3"))
        
        summary = self.error_handler.get_error_summary()
        
        self.assertEqual(summary["total_errors"], 3)
        self.assertEqual(summary["by_stage"]["parsing"], 2)
        self.assertEqual(summary["by_stage"]["summarization"], 1)
        self.assertEqual(summary["by_type"]["ValueError"], 2)
        self.assertEqual(summary["by_type"]["RuntimeError"], 1)
        self.assertLessEqual(len(summary["recent_errors"]), 10)
    
    def test_export_errors(self):
        """Test exporting errors to JSON."""
        self.error_handler.log_error("paper1", "parsing", ValueError("Test"))
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            self.error_handler.export_errors(temp_path)
            
            # Verify file contents
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            self.assertIn("errors", data)
            self.assertIn("summary", data)
            self.assertEqual(len(data["errors"]), 1)
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestRetryHandler(unittest.TestCase):
    """Test Step 18.2: API error handling and retry logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.retry_handler = RetryHandler(
            max_retries=3,
            initial_delay=0.1,  # Fast for testing
            max_delay=1.0,
            backoff_factor=2.0
        )
    
    def test_calculate_delay(self):
        """Test exponential backoff delay calculation."""
        # Attempt 0: 0.1 seconds
        delay0 = self.retry_handler.calculate_delay(0)
        self.assertAlmostEqual(delay0, 0.1, places=2)
        
        # Attempt 1: 0.2 seconds
        delay1 = self.retry_handler.calculate_delay(1)
        self.assertAlmostEqual(delay1, 0.2, places=2)
        
        # Attempt 2: 0.4 seconds
        delay2 = self.retry_handler.calculate_delay(2)
        self.assertAlmostEqual(delay2, 0.4, places=2)
        
        # Should cap at max_delay
        delay_high = self.retry_handler.calculate_delay(10)
        self.assertLessEqual(delay_high, 1.0)
    
    def test_retry_success_on_first_attempt(self):
        """Test successful execution on first attempt."""
        mock_func = Mock(return_value="success")
        
        result = self.retry_handler.retry_with_backoff(mock_func)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 1)
    
    def test_retry_on_transient_error(self):
        """Test retry on transient errors."""
        mock_func = Mock(side_effect=[
            TransientAPIError("Network timeout"),
            TransientAPIError("Connection reset"),
            "success"
        ])
        
        result = self.retry_handler.retry_with_backoff(mock_func)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)
    
    def test_retry_on_rate_limit(self):
        """Test retry on rate limit errors."""
        mock_func = Mock(side_effect=[
            RateLimitError("Rate limit exceeded"),
            "success"
        ])
        
        result = self.retry_handler.retry_with_backoff(mock_func)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 2)
    
    def test_quota_exceeded_no_retry(self):
        """Test that quota exceeded errors are not retried."""
        mock_func = Mock(side_effect=QuotaExceededError("Quota exceeded"))
        
        with self.assertRaises(QuotaExceededError):
            self.retry_handler.retry_with_backoff(mock_func)
        
        self.assertEqual(mock_func.call_count, 1)
    
    def test_max_retries_exhausted(self):
        """Test behavior when max retries are exhausted."""
        mock_func = Mock(side_effect=TransientAPIError("Always fails"))
        
        with self.assertRaises(TransientAPIError):
            self.retry_handler.retry_with_backoff(mock_func)
        
        self.assertEqual(mock_func.call_count, 3)  # max_retries
    
    def test_detect_rate_limit_from_error_message(self):
        """Test detection of rate limit from error message."""
        # Simulate an error with rate limit in message
        mock_func = Mock(side_effect=[
            Exception("Error: rate limit exceeded"),
            "success"
        ])
        
        result = self.retry_handler.retry_with_backoff(mock_func)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 2)
    
    def test_detect_network_error_from_message(self):
        """Test detection of network error from message."""
        mock_func = Mock(side_effect=[
            Exception("Connection timeout"),
            "success"
        ])
        
        result = self.retry_handler.retry_with_backoff(mock_func)
        
        self.assertEqual(result, "success")


class TestDataValidator(unittest.TestCase):
    """Test Step 18.3: Data validation error handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        with self.assertRaises(PDFValidationError) as context:
            self.validator.validate_pdf_file("/nonexistent/file.pdf")
        
        self.assertIn("does not exist", str(context.exception))
    
    def test_validate_empty_file(self):
        """Test validation of empty file."""
        empty_file = Path(self.temp_dir) / "empty.pdf"
        empty_file.touch()
        
        with self.assertRaises(PDFValidationError) as context:
            self.validator.validate_pdf_file(str(empty_file))
        
        self.assertIn("empty", str(context.exception).lower())
    
    def test_validate_paper_record_missing_required_fields(self):
        """Test validation of paper with missing required fields."""
        paper = PaperRecord(
            id="",  # Empty ID (invalid)
            file_path="",  # Empty path (invalid)
            filename=""  # Empty filename (invalid)
        )
        
        result = self.validator.validate_paper_record(
            paper,
            required_fields=["id", "file_path", "filename"]
        )
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 3)  # 3 missing fields
    
    def test_validate_paper_record_failed_without_reason(self):
        """Test validation warns about failed status without error reason."""
        paper = PaperRecord(
            id="test_id",
            file_path="/test/file.pdf",
            filename="file.pdf",
            processing_status="failed",
            error_reason=None  # Missing error reason
        )
        
        result = self.validator.validate_paper_record(paper)
        
        self.assertGreater(len(result["warnings"]), 0)
    
    def test_validate_paper_record_tier_inconsistency(self):
        """Test validation detects tier classification inconsistency."""
        paper = PaperRecord(
            id="test_id",
            file_path="/test/file.pdf",
            filename="file.pdf",
            tier2_topic="topic2",  # Tier 2 set
            tier1_topic=None  # But Tier 1 missing (invalid)
        )
        
        result = self.validator.validate_paper_record(paper)
        
        self.assertFalse(result["valid"])
        self.assertTrue(any("tier1" in err.lower() for err in result["errors"]))


class TestErrorRecoveryManager(unittest.TestCase):
    """Test Step 18.4: Recovery mechanisms."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.recovery_manager = ErrorRecoveryManager(max_retries=3)
        
        # Create test state with some failed papers
        self.state = {
            "papers": {
                "paper1": PaperRecord(
                    id="paper1",
                    file_path="/test/paper1.pdf",
                    filename="paper1.pdf",
                    processing_status="failed",
                    error_reason="Parsing error",
                    error_stage="parsing",
                    retry_count=0
                ),
                "paper2": PaperRecord(
                    id="paper2",
                    file_path="/test/paper2.pdf",
                    filename="paper2.pdf",
                    processing_status="failed",
                    error_reason="Rate limit exceeded",
                    error_stage="summarization",
                    retry_count=1
                ),
                "paper3": PaperRecord(
                    id="paper3",
                    file_path="/test/paper3.pdf",
                    filename="paper3.pdf",
                    processing_status="classified",  # Not failed
                ),
            },
            "papers_failed": ["paper1", "paper2"],
            "papers_pending": [],
            "papers_completed": ["paper3"],
        }
    
    def test_get_failed_papers(self):
        """Test retrieving failed papers."""
        failed = self.recovery_manager.get_failed_papers(self.state)
        
        self.assertEqual(len(failed), 2)
        self.assertTrue(all(p.processing_status == "failed" for p in failed))
    
    def test_get_failed_papers_by_stage(self):
        """Test retrieving failed papers filtered by stage."""
        failed = self.recovery_manager.get_failed_papers_by_stage(
            self.state,
            "parsing"
        )
        
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].id, "paper1")
    
    def test_retry_paper(self):
        """Test retrying a single failed paper."""
        updated_state = self.recovery_manager.retry_paper(self.state, "paper1")
        
        paper1 = updated_state["papers"]["paper1"]
        self.assertEqual(paper1.processing_status, "pending")
        self.assertIsNone(paper1.error_reason)
        self.assertIsNone(paper1.error_stage)
        self.assertEqual(paper1.retry_count, 1)
        
        # Check queue updates
        self.assertIn("paper1", updated_state["papers_pending"])
        self.assertNotIn("paper1", updated_state["papers_failed"])
    
    def test_retry_paper_max_retries_reached(self):
        """Test that papers with max retries are not retried."""
        # Set paper to max retries
        self.state["papers"]["paper1"].retry_count = 3
        
        updated_state = self.recovery_manager.retry_paper(self.state, "paper1")
        
        # Should still be failed
        paper1 = updated_state["papers"]["paper1"]
        self.assertEqual(paper1.processing_status, "failed")
        self.assertEqual(paper1.retry_count, 3)
    
    def test_retry_failed_papers_selective_by_stage(self):
        """Test selective retry by stage."""
        updated_state = self.recovery_manager.retry_failed_papers_selective(
            self.state,
            filter_stage="parsing"
        )
        
        # Only paper1 should be retried
        paper1 = updated_state["papers"]["paper1"]
        paper2 = updated_state["papers"]["paper2"]
        
        self.assertEqual(paper1.processing_status, "pending")
        self.assertEqual(paper2.processing_status, "failed")  # Still failed
    
    def test_retry_failed_papers_selective_max_papers(self):
        """Test selective retry with max papers limit."""
        updated_state = self.recovery_manager.retry_failed_papers_selective(
            self.state,
            max_papers=1
        )
        
        # Only one paper should be retried
        retried_count = sum(
            1 for p in updated_state["papers"].values()
            if p.processing_status == "pending"
        )
        self.assertEqual(retried_count, 1)
    
    def test_get_recovery_options(self):
        """Test getting recovery options."""
        options = self.recovery_manager.get_recovery_options(self.state)
        
        self.assertEqual(options["total_failed"], 2)
        self.assertEqual(options["retryable"], 2)  # Both can be retried
        self.assertEqual(options["max_retries_reached"], 0)
        self.assertIn("parsing", options["failures_by_stage"])
        self.assertIn("summarization", options["failures_by_stage"])
        self.assertIsInstance(options["recommended_actions"], list)
    
    def test_recovery_recommendations(self):
        """Test recovery recommendations generation."""
        # Add more parsing failures to trigger recommendation
        for i in range(5):
            self.state["papers"][f"paper_parse_{i}"] = PaperRecord(
                id=f"paper_parse_{i}",
                file_path=f"/test/paper{i}.pdf",
                filename=f"paper{i}.pdf",
                processing_status="failed",
                error_reason="PDF parsing error",
                error_stage="parsing",
                retry_count=0
            )
        
        options = self.recovery_manager.get_recovery_options(self.state)
        recommendations = options["recommended_actions"]
        
        # Should recommend OCR for parsing failures
        self.assertTrue(any("parsing" in r.lower() for r in recommendations))


class TestIntegration(unittest.TestCase):
    """Integration tests for error handling and recovery."""
    
    def test_full_error_recovery_workflow(self):
        """Test complete error recovery workflow."""
        # Create state with failed papers
        state = {
            "papers": {
                "paper1": PaperRecord(
                    id="paper1",
                    file_path="/test/paper1.pdf",
                    filename="paper1.pdf",
                    processing_status="failed",
                    error_reason="Transient error",
                    error_stage="metadata",
                    retry_count=0
                ),
            },
            "papers_failed": ["paper1"],
            "papers_pending": [],
            "papers_completed": [],
        }
        
        # List failed papers
        failed_list = list_failed_papers(state)
        self.assertEqual(len(failed_list), 1)
        
        # Get recovery options
        options = get_recovery_options(state)
        self.assertEqual(options["total_failed"], 1)
        self.assertGreater(options["retryable"], 0)
        
        # Retry failed papers
        updated_state = retry_failed_papers(state, max_retries=3)
        
        # Verify paper was reset
        paper1 = updated_state["papers"]["paper1"]
        self.assertEqual(paper1.processing_status, "pending")
        self.assertEqual(paper1.retry_count, 1)


if __name__ == '__main__':
    unittest.main()
