#!/usr/bin/env python3
"""
Test suite for Phase 17: Cost Tracking and Optimization

This module tests:
- Step 17.1: Cost tracking (API calls, token usage, cost estimation)
- Step 17.2: Cost optimization (tiered models, batching, caching)
- Step 17.3: Budget controls (limits, warnings, approval)

Version: 1.0
Date: 2025-11-24
"""

import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime

# Import models and cost tracking
from rag_models import (
    RunConfig,
    CostTracker,
    APICallRecord,
    CostReport,
    BudgetExceededError,
    GraphState,
    StateManager,
)


class TestCostTracking(unittest.TestCase):
    """Test Step 17.1: Cost tracking functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = RunConfig(
            drive_folder_path="test_pdfs",
            max_cost_per_run=10.0,
            cost_warning_threshold=0.8,
            enable_cost_tracking=True,
            enable_result_caching=True,
            batch_api_calls=True,
        )
        self.tracker = CostTracker(self.config)
    
    def test_cost_tracker_initialization(self):
        """Test CostTracker initializes correctly."""
        self.assertEqual(self.tracker.total_cost, 0.0)
        self.assertEqual(self.tracker.total_input_tokens, 0)
        self.assertEqual(self.tracker.total_output_tokens, 0)
        self.assertEqual(self.tracker.budget_limit, 10.0)
        self.assertEqual(len(self.tracker.api_calls), 0)
    
    def test_estimate_cost_gpt5_mini(self):
        """Test cost estimation for GPT-5-mini."""
        # GPT-5-mini: $0.10 per 1M input, $0.40 per 1M output
        cost = self.tracker.estimate_cost(
            model="gpt-5-mini",
            input_tokens=10000,
            output_tokens=5000,
            is_batch=False
        )
        expected = (10000 * 0.10 / 1_000_000) + (5000 * 0.40 / 1_000_000)
        self.assertAlmostEqual(cost, expected, places=6)
    
    def test_estimate_cost_embedding(self):
        """Test cost estimation for embeddings."""
        # text-embedding-3-large: $0.13 per 1M tokens
        cost = self.tracker.estimate_cost(
            model="text-embedding-3-large",
            input_tokens=10000,
            output_tokens=0,
            is_batch=False
        )
        expected = 10000 * 0.13 / 1_000_000
        self.assertAlmostEqual(cost, expected, places=6)
    
    def test_estimate_cost_with_batch_discount(self):
        """Test that batch API calls get 50% discount."""
        cost_regular = self.tracker.estimate_cost(
            model="gpt-5-mini",
            input_tokens=10000,
            output_tokens=5000,
            is_batch=False
        )
        cost_batch = self.tracker.estimate_cost(
            model="gpt-5-mini",
            input_tokens=10000,
            output_tokens=5000,
            is_batch=True
        )
        self.assertAlmostEqual(cost_batch, cost_regular * 0.5, places=6)
    
    def test_record_api_call(self):
        """Test recording API calls."""
        record = self.tracker.record_api_call(
            operation="summarization",
            model="gpt-5-mini",
            input_tokens=1000,
            output_tokens=500,
            paper_id="test_paper_001",
            batch_size=1,
            is_batch=False
        )
        
        self.assertIsInstance(record, APICallRecord)
        self.assertEqual(record.operation, "summarization")
        self.assertEqual(record.model, "gpt-5-mini")
        self.assertEqual(record.input_tokens, 1000)
        self.assertEqual(record.output_tokens, 500)
        self.assertEqual(record.total_tokens, 1500)
        self.assertEqual(record.paper_id, "test_paper_001")
        self.assertGreater(record.estimated_cost, 0)
        
        # Check that totals were updated
        self.assertEqual(len(self.tracker.api_calls), 1)
        self.assertEqual(self.tracker.total_input_tokens, 1000)
        self.assertEqual(self.tracker.total_output_tokens, 500)
        self.assertGreater(self.tracker.total_cost, 0)
    
    def test_multiple_api_calls(self):
        """Test tracking multiple API calls."""
        # Record several calls
        for i in range(5):
            self.tracker.record_api_call(
                operation="embedding",
                model="text-embedding-3-large",
                input_tokens=500,
                output_tokens=0,
                paper_id=f"paper_{i}",
            )
        
        self.assertEqual(len(self.tracker.api_calls), 5)
        self.assertEqual(self.tracker.total_input_tokens, 2500)
        self.assertEqual(self.tracker.total_output_tokens, 0)
        self.assertGreater(self.tracker.cost_by_operation["embedding"], 0)
    
    def test_cost_breakdown_by_operation(self):
        """Test that costs are categorized by operation type."""
        # Embedding
        self.tracker.record_api_call(
            operation="embedding",
            model="text-embedding-3-large",
            input_tokens=1000,
        )
        
        # Summarization
        self.tracker.record_api_call(
            operation="summarization",
            model="gpt-5-mini",
            input_tokens=1000,
            output_tokens=500,
        )
        
        # Classification
        self.tracker.record_api_call(
            operation="classification",
            model="gpt-5-mini",
            input_tokens=500,
            output_tokens=200,
        )
        
        # Check breakdown
        self.assertGreater(self.tracker.cost_by_operation["embedding"], 0)
        self.assertGreater(self.tracker.cost_by_operation["summarization"], 0)
        self.assertGreater(self.tracker.cost_by_operation["classification"], 0)
        self.assertEqual(self.tracker.cost_by_operation["taxonomy"], 0)


class TestBudgetControls(unittest.TestCase):
    """Test Step 17.3: Budget controls and limits."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = RunConfig(
            drive_folder_path="test_pdfs",
            max_cost_per_run=0.01,  # Very low budget for testing
            cost_warning_threshold=0.5,
            enable_cost_tracking=True,
        )
        self.tracker = CostTracker(self.config)
    
    def test_budget_exceeded_exception(self):
        """Test that BudgetExceededError is raised when budget exceeded."""
        # This should exceed the $0.01 budget
        with self.assertRaises(BudgetExceededError):
            # Record expensive calls until budget exceeded
            for _ in range(100):
                self.tracker.record_api_call(
                    operation="summarization",
                    model="gpt-5-mini",
                    input_tokens=10000,
                    output_tokens=5000,
                )
    
    def test_budget_warning(self):
        """Test that warnings are issued when approaching budget."""
        # Record calls that should trigger warning at 50% threshold
        initial_warnings = len(self.tracker.warnings_issued)
        
        # Spend about 60% of budget
        target_cost = self.config.max_cost_per_run * 0.6
        while self.tracker.total_cost < target_cost:
            try:
                self.tracker.record_api_call(
                    operation="summarization",
                    model="gpt-5-mini",
                    input_tokens=1000,
                    output_tokens=500,
                )
            except BudgetExceededError:
                break
        
        # Should have issued at least one warning
        self.assertGreater(len(self.tracker.warnings_issued), initial_warnings)
    
    def test_no_budget_limit(self):
        """Test that tracking works without budget limit."""
        config = RunConfig(
            drive_folder_path="test_pdfs",
            max_cost_per_run=None,  # No limit
            enable_cost_tracking=True,
        )
        tracker = CostTracker(config)
        
        # Should not raise exception regardless of cost
        for _ in range(100):
            tracker.record_api_call(
                operation="summarization",
                model="gpt-5-mini",
                input_tokens=10000,
                output_tokens=5000,
            )
        
        self.assertGreater(tracker.total_cost, 0)


class TestCostOptimization(unittest.TestCase):
    """Test Step 17.2: Cost optimization features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = RunConfig(
            drive_folder_path="test_pdfs",
            enable_cost_tracking=True,
            enable_result_caching=True,
            batch_api_calls=True,
        )
        self.tracker = CostTracker(self.config)
    
    def test_result_caching(self):
        """Test result caching functionality."""
        # Generate cache key
        cache_key = self.tracker.get_cache_key(
            operation="summarization",
            paper_id="test_001",
            model="gpt-5-mini"
        )
        
        # Initially no cached result
        self.assertIsNone(self.tracker.get_cached_result(cache_key))
        
        # Cache a result
        test_result = {"summary": "This is a test summary"}
        self.tracker.cache_result(cache_key, test_result)
        
        # Should now retrieve cached result
        cached = self.tracker.get_cached_result(cache_key)
        self.assertEqual(cached, test_result)
    
    def test_caching_disabled(self):
        """Test that caching respects configuration."""
        config = RunConfig(
            drive_folder_path="test_pdfs",
            enable_result_caching=False,
        )
        tracker = CostTracker(config)
        
        cache_key = "test_key"
        tracker.cache_result(cache_key, "test_value")
        
        # Should not return cached value when caching disabled
        self.assertIsNone(tracker.get_cached_result(cache_key))
    
    def test_cache_key_consistency(self):
        """Test that cache keys are consistent for same inputs."""
        key1 = self.tracker.get_cache_key(
            operation="test",
            param1="value1",
            param2="value2"
        )
        key2 = self.tracker.get_cache_key(
            operation="test",
            param1="value1",
            param2="value2"
        )
        
        # Same inputs should produce same key
        self.assertEqual(key1, key2)
        
        # Different inputs should produce different key
        key3 = self.tracker.get_cache_key(
            operation="test",
            param1="different",
            param2="value2"
        )
        self.assertNotEqual(key1, key3)


class TestCostReporting(unittest.TestCase):
    """Test cost reporting functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = RunConfig(
            drive_folder_path="test_pdfs",
            max_cost_per_run=10.0,
            enable_cost_tracking=True,
        )
        self.tracker = CostTracker(self.config)
        
        # Record some sample API calls
        self.tracker.record_api_call(
            operation="embedding",
            model="text-embedding-3-large",
            input_tokens=10000,
        )
        self.tracker.record_api_call(
            operation="summarization",
            model="gpt-5-mini",
            input_tokens=5000,
            output_tokens=2000,
        )
        self.tracker.record_api_call(
            operation="classification",
            model="gpt-5-mini",
            input_tokens=3000,
            output_tokens=1000,
        )
    
    def test_generate_report(self):
        """Test generating cost report."""
        report = self.tracker.generate_report()
        
        self.assertIsInstance(report, CostReport)
        self.assertEqual(report.total_cost, self.tracker.total_cost)
        self.assertEqual(report.total_api_calls, 3)
        self.assertGreater(report.embedding_cost, 0)
        self.assertGreater(report.summarization_cost, 0)
        self.assertGreater(report.classification_cost, 0)
        self.assertEqual(report.total_input_tokens, 18000)
        self.assertEqual(report.total_output_tokens, 3000)
        self.assertIsNotNone(report.budget_limit)
        self.assertIsNotNone(report.budget_remaining)
        self.assertIsNotNone(report.budget_utilization)
    
    def test_report_budget_calculation(self):
        """Test that budget calculations are correct."""
        report = self.tracker.generate_report()
        
        expected_remaining = self.config.max_cost_per_run - self.tracker.total_cost
        self.assertAlmostEqual(report.budget_remaining, expected_remaining, places=6)
        
        expected_utilization = self.tracker.total_cost / self.config.max_cost_per_run
        self.assertAlmostEqual(report.budget_utilization, expected_utilization, places=6)
    
    def test_report_to_formatted_string(self):
        """Test formatted report string generation."""
        report = self.tracker.generate_report()
        formatted = report.to_formatted_string()
        
        self.assertIsInstance(formatted, str)
        self.assertIn("COST REPORT", formatted)
        self.assertIn("TOTAL COST", formatted)
        self.assertIn("BUDGET", formatted)
        self.assertIn("TOKEN USAGE", formatted)
        self.assertIn("API CALLS", formatted)
    
    def test_recommendations_generation(self):
        """Test that recommendations are generated."""
        report = self.tracker.generate_report()
        
        # Should have some recommendations
        self.assertIsInstance(report.recommendations, list)
    
    def test_save_and_load_report(self):
        """Test saving report to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cost_report.json"
            
            # Save report
            saved_path = self.tracker.save_report(str(output_path))
            self.assertEqual(saved_path, str(output_path))
            self.assertTrue(output_path.exists())
            
            # Load and verify
            with open(output_path) as f:
                data = json.load(f)
            
            self.assertIn("total_cost", data)
            self.assertIn("total_api_calls", data)
            self.assertIn("embedding_cost", data)


class TestCostTrackerSerialization(unittest.TestCase):
    """Test serialization and deserialization of CostTracker."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = RunConfig(
            drive_folder_path="test_pdfs",
            max_cost_per_run=10.0,
            enable_cost_tracking=True,
        )
        self.tracker = CostTracker(self.config)
        
        # Record some calls
        for i in range(3):
            self.tracker.record_api_call(
                operation="embedding",
                model="text-embedding-3-large",
                input_tokens=1000 * (i + 1),
                paper_id=f"paper_{i}",
            )
    
    def test_to_dict(self):
        """Test converting CostTracker to dictionary."""
        data = self.tracker.to_dict()
        
        self.assertIsInstance(data, dict)
        self.assertIn("total_cost", data)
        self.assertIn("cost_by_operation", data)
        self.assertIn("total_input_tokens", data)
        self.assertIn("api_calls", data)
        self.assertEqual(len(data["api_calls"]), 3)
    
    def test_from_dict(self):
        """Test restoring CostTracker from dictionary."""
        # Save state
        original_cost = self.tracker.total_cost
        original_tokens = self.tracker.total_input_tokens
        data = self.tracker.to_dict()
        
        # Restore
        restored = CostTracker.from_dict(self.config, data)
        
        self.assertEqual(restored.total_cost, original_cost)
        self.assertEqual(restored.total_input_tokens, original_tokens)
        self.assertEqual(len(restored.api_calls), 3)


class TestGraphStateIntegration(unittest.TestCase):
    """Test integration of cost tracking with GraphState."""
    
    def test_state_includes_cost_tracking(self):
        """Test that GraphState includes cost tracking fields."""
        config = RunConfig(
            drive_folder_path="test_pdfs",
            enable_cost_tracking=True,
        )
        state = StateManager.create_initial_state(config)
        
        # Should have cost tracking fields
        self.assertIn("cost_tracker", state)
        self.assertIn("total_cost", state)
        self.assertIn("cost_breakdown", state)
        
        self.assertEqual(state["total_cost"], 0.0)
        self.assertIsInstance(state["cost_breakdown"], dict)


class TestAPICallRecord(unittest.TestCase):
    """Test APICallRecord model."""
    
    def test_create_record(self):
        """Test creating an API call record."""
        record = APICallRecord(
            operation="summarization",
            model="gpt-5-mini",
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            estimated_cost=0.0015,
            paper_id="test_001",
            batch_size=1,
        )
        
        self.assertEqual(record.operation, "summarization")
        self.assertEqual(record.model, "gpt-5-mini")
        self.assertEqual(record.input_tokens, 1000)
        self.assertEqual(record.output_tokens, 500)
        self.assertEqual(record.total_tokens, 1500)
        self.assertEqual(record.estimated_cost, 0.0015)
    
    def test_record_to_dict(self):
        """Test converting record to dictionary."""
        record = APICallRecord(
            operation="embedding",
            model="text-embedding-3-large",
            input_tokens=1000,
            estimated_cost=0.0013,
        )
        
        data = record.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["operation"], "embedding")
        self.assertEqual(data["model"], "text-embedding-3-large")


def run_tests():
    """Run all tests and print results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCostTracking))
    suite.addTests(loader.loadTestsFromTestCase(TestBudgetControls))
    suite.addTests(loader.loadTestsFromTestCase(TestCostOptimization))
    suite.addTests(loader.loadTestsFromTestCase(TestCostReporting))
    suite.addTests(loader.loadTestsFromTestCase(TestCostTrackerSerialization))
    suite.addTests(loader.loadTestsFromTestCase(TestGraphStateIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestAPICallRecord))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("PHASE 17 TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
