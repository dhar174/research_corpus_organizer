#!/usr/bin/env python3
"""
Test suite for Phase 11: Deep Analysis Pass (Optional - Pass 2)

Tests all functionality in deep_analysis_pass2.py including:
- Deep analysis flag checking
- Deep analysis generation with OpenAI API
- Prompt creation for detailed methodology/results analysis
- Batch processing and retry logic
- Deep analysis validation
- Cost estimation

Note: Some tests require OpenAI API key.
Mock tests are provided for environments without API access.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    PaperRecord,
    PaperChunk,
    StateManager,
    create_default_config,
    GraphState,
)

# Try importing the phase 11 module
try:
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
    DEEP_ANALYSIS_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import deep_analysis_pass2: {e}")
    DEEP_ANALYSIS_MODULE_AVAILABLE = False


# =============================================================================
# Test Step 11.1: Check Deep Analysis Flag
# =============================================================================

def test_should_perform_deep_analysis():
    """Test deep analysis flag checking."""
    if not DEEP_ANALYSIS_MODULE_AVAILABLE:
        print("Skipping test_should_perform_deep_analysis: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Deep Analysis Flag Checking")
    print("=" * 70)
    
    # Test with flag enabled
    config_enabled = create_default_config()
    config_enabled.enable_deep_analysis_pass = True
    
    result = should_perform_deep_analysis(config_enabled)
    print(f"\nWith flag enabled: {result}")
    assert result is True, "Should return True when flag is enabled"
    
    # Test with flag disabled
    config_disabled = create_default_config()
    config_disabled.enable_deep_analysis_pass = False
    
    result = should_perform_deep_analysis(config_disabled)
    print(f"With flag disabled: {result}")
    assert result is False, "Should return False when flag is disabled"
    
    print("\n✓ Deep analysis flag checking works correctly")


def test_check_deep_analysis_flag():
    """Test checking deep analysis flag from GraphState."""
    if not DEEP_ANALYSIS_MODULE_AVAILABLE:
        print("Skipping test_check_deep_analysis_flag: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Check Deep Analysis Flag from GraphState")
    print("=" * 70)
    
    # Create state with flag enabled
    config = create_default_config()
    config.enable_deep_analysis_pass = True
    
    state = GraphState(config=config)
    result = check_deep_analysis_flag(state)
    
    print(f"\nState with flag enabled: {result}")
    assert result is True, "Should return True for state with flag enabled"
    
    # Create state with flag disabled
    config.enable_deep_analysis_pass = False
    state = GraphState(config=config)
    result = check_deep_analysis_flag(state)
    
    print(f"State with flag disabled: {result}")
    assert result is False, "Should return False for state with flag disabled"
    
    print("\n✓ GraphState flag checking works correctly")


# =============================================================================
# Test Step 11.3: Deep Analysis Prompts
# =============================================================================

def test_deep_analysis_prompt_creation():
    """Test creation of deep analysis prompts."""
    if not DEEP_ANALYSIS_MODULE_AVAILABLE:
        print("Skipping test_deep_analysis_prompt_creation: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Deep Analysis Prompt Creation")
    print("=" * 70)
    
    # Create sample paper
    paper = PaperRecord(
        id="test_paper_1",
        file_path="/test/paper1.pdf",
        filename="paper1.pdf",
        title="Deep Learning for Computer Vision",
        abstract_text="This paper presents a novel deep learning approach...",
        full_summary="We propose a new architecture that improves accuracy by 15%..."
    )
    
    # Create sample chunks
    chunks = [
        PaperChunk(
            id="chunk_1",
            paper_id="test_paper_1",
            section_label="Methods",
            text="We used a convolutional neural network with residual connections...",
            cleaned_text="We used a convolutional neural network with residual connections...",
            page_start=3,
            page_end=5
        ),
        PaperChunk(
            id="chunk_2",
            paper_id="test_paper_1",
            section_label="Results",
            text="Our approach achieved 95% accuracy on the test set...",
            cleaned_text="Our approach achieved 95% accuracy on the test set...",
            page_start=6,
            page_end=8
        ),
    ]
    
    config = create_default_config()
    
    # Create prompts
    system_prompt, user_prompt = create_deep_analysis_prompt(paper, chunks, config)
    
    print("\nSystem Prompt Preview:")
    print(system_prompt[:200] + "...")
    
    print("\nUser Prompt Preview:")
    print(user_prompt[:300] + "...")
    
    # Validate prompts
    assert len(system_prompt) > 0, "System prompt should not be empty"
    assert len(user_prompt) > 0, "User prompt should not be empty"
    assert "methodology" in system_prompt.lower(), "System prompt should mention methodology"
    assert paper.title in user_prompt, "User prompt should include paper title"
    assert "Deep Analysis Requirements" in user_prompt, "User prompt should have analysis structure"
    
    # Check for key sections in user prompt
    assert "Detailed Methodology Breakdown" in user_prompt
    assert "Experimental Setup Details" in user_prompt
    assert "Key Results and Metrics" in user_prompt
    assert "Limitations and Constraints" in user_prompt
    assert "Future Work and Extensions" in user_prompt
    
    print("\n✓ Deep analysis prompts created correctly")


def test_deep_analysis_prompt_factory():
    """Test DeepAnalysisPromptFactory methods."""
    if not DEEP_ANALYSIS_MODULE_AVAILABLE:
        print("Skipping test_deep_analysis_prompt_factory: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Deep Analysis Prompt Factory")
    print("=" * 70)
    
    # Test system prompt creation
    system_prompt = DeepAnalysisPromptFactory.create_system_prompt()
    print(f"\nSystem prompt length: {len(system_prompt)} chars")
    assert len(system_prompt) > 100, "System prompt should be substantial"
    assert "methodology" in system_prompt.lower()
    assert "experimental" in system_prompt.lower()
    
    # Test user prompt creation
    user_prompt = DeepAnalysisPromptFactory.create_user_prompt(
        title="Test Paper",
        abstract="Test abstract text",
        full_summary="Test summary",
        methods_text="We used method X with parameter Y",
        results_text="We achieved result Z with confidence W",
        discussion_text="These results suggest...",
        conclusion_text="In conclusion...",
        max_length=100
    )
    
    print(f"User prompt length: {len(user_prompt)} chars")
    assert len(user_prompt) > 200, "User prompt should be comprehensive"
    assert "Test Paper" in user_prompt
    assert "Detailed Methodology Breakdown" in user_prompt
    assert "Key Results and Metrics" in user_prompt
    
    print("\n✓ DeepAnalysisPromptFactory works correctly")


# =============================================================================
# Test Step 11.4: Paper Selection and Batch Processing
# =============================================================================

def test_select_papers_for_deep_analysis():
    """Test paper selection for deep analysis."""
    if not DEEP_ANALYSIS_MODULE_AVAILABLE:
        print("Skipping test_select_papers_for_deep_analysis: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Paper Selection for Deep Analysis")
    print("=" * 70)
    
    # Create sample papers with different statuses
    papers = {
        "paper_1": PaperRecord(
            id="paper_1",
            file_path="/test/paper1.pdf",
            filename="paper1.pdf",
            processing_status="summarized",
            full_summary="Summary 1"
        ),
        "paper_2": PaperRecord(
            id="paper_2",
            file_path="/test/paper2.pdf",
            filename="paper2.pdf",
            processing_status="classified",
            full_summary="Summary 2",
            tier1_topic="T1_01",
            tier1_confidence=0.9
        ),
        "paper_3": PaperRecord(
            id="paper_3",
            file_path="/test/paper3.pdf",
            filename="paper3.pdf",
            processing_status="classified",
            full_summary="Summary 3",
            tier1_topic="T1_02",
            tier1_confidence=0.6
        ),
        "paper_4": PaperRecord(
            id="paper_4",
            file_path="/test/paper4.pdf",
            filename="paper4.pdf",
            processing_status="pending"
        ),
    }
    
    config = create_default_config()
    config.enable_deep_analysis_pass = True
    
    # Test selecting all eligible papers
    selected = select_papers_for_deep_analysis(papers, config, subset_criteria="all")
    print(f"\nSelected 'all': {len(selected)} papers")
    assert len(selected) == 3, "Should select 3 eligible papers (with summaries)"
    
    # Test selecting only classified papers
    selected = select_papers_for_deep_analysis(papers, config, subset_criteria="classified")
    print(f"Selected 'classified': {len(selected)} papers")
    assert len(selected) == 2, "Should select 2 classified papers"
    
    # Test selecting high confidence papers
    selected = select_papers_for_deep_analysis(papers, config, subset_criteria="high_confidence")
    print(f"Selected 'high_confidence': {len(selected)} papers")
    assert len(selected) == 1, "Should select 1 high-confidence paper"
    assert "paper_2" in selected, "Should select paper_2 with 0.9 confidence"
    
    # Test with specific paper IDs
    selected = select_papers_for_deep_analysis(papers, config, subset_criteria=["paper_1", "paper_2"])
    print(f"Selected by ID list: {len(selected)} papers")
    assert len(selected) == 2, "Should select 2 specified papers"
    
    # Test with flag disabled
    config.enable_deep_analysis_pass = False
    selected = select_papers_for_deep_analysis(papers, config)
    print(f"Selected with flag disabled: {len(selected)} papers")
    assert len(selected) == 0, "Should select 0 papers when flag is disabled"
    
    print("\n✓ Paper selection works correctly")


# =============================================================================
# Test Validation Functions
# =============================================================================

def test_validate_deep_analysis():
    """Test deep analysis validation."""
    if not DEEP_ANALYSIS_MODULE_AVAILABLE:
        print("Skipping test_validate_deep_analysis: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Deep Analysis Validation")
    print("=" * 70)
    
    # Test valid deep analysis
    valid_analysis = """
    Detailed Methodology Breakdown:
    The authors employed a novel transformer-based architecture with attention mechanisms.
    They used the ImageNet dataset with custom augmentation techniques.
    The approach includes residual connections and layer normalization for stability.
    
    Experimental Setup Details:
    Experiments were conducted on NVIDIA A100 GPUs with batch size 32.
    Training used Adam optimizer with learning rate 0.001 and weight decay 0.0001.
    The baseline comparison included ResNet-50 and EfficientNet models.
    Evaluation metrics included accuracy, F1-score, and inference time.
    
    Key Results and Metrics:
    The proposed model achieved 96.2% accuracy on the test set (p < 0.001).
    Compared to ResNet-50 baseline at 92.1%, this represents a 4.1% improvement.
    Inference time was reduced by 23% while maintaining higher accuracy.
    Statistical significance was confirmed using paired t-tests.
    
    Limitations and Constraints:
    The model requires significant GPU memory (24GB minimum).
    Performance degrades on out-of-distribution samples.
    The approach assumes high-quality labeled training data.
    
    Future Work and Extensions:
    Future research could explore few-shot learning scenarios.
    Extending the approach to video data is a promising direction.
    Investigating interpretability of attention patterns remains an open question.
    """
    
    is_valid, error = validate_deep_analysis(valid_analysis)
    print(f"\nValid analysis: {is_valid}")
    if error:
        print(f"Error: {error}")
    assert is_valid is True, "Should validate correct deep analysis"
    
    # Test empty analysis
    is_valid, error = validate_deep_analysis(None)
    print(f"\nEmpty analysis: {is_valid}")
    print(f"Error: {error}")
    assert is_valid is False, "Should reject empty analysis"
    
    # Test too short analysis
    is_valid, error = validate_deep_analysis("Too short")
    print(f"\nShort analysis: {is_valid}")
    print(f"Error: {error}")
    assert is_valid is False, "Should reject too short analysis"
    
    # Test analysis missing expected content
    incomplete_analysis = "This is a paper about machine learning. It has some results."
    is_valid, error = validate_deep_analysis(incomplete_analysis)
    print(f"\nIncomplete analysis: {is_valid}")
    print(f"Error: {error}")
    assert is_valid is False, "Should reject incomplete analysis"
    
    print("\n✓ Deep analysis validation works correctly")


def test_validate_paper_deep_analyses():
    """Test validation of multiple paper deep analyses."""
    if not DEEP_ANALYSIS_MODULE_AVAILABLE:
        print("Skipping test_validate_paper_deep_analyses: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Validate Multiple Deep Analyses")
    print("=" * 70)
    
    # Create papers with different analysis states
    papers = {
        "paper_1": PaperRecord(
            id="paper_1",
            file_path="/test/paper1.pdf",
            filename="paper1.pdf",
            title="Paper 1",
            deep_summary="""
            Detailed methodology using neural networks with experiments showing
            96% accuracy. Results demonstrate significant improvement. The approach
            has some limitations regarding computational resources. Future work
            could explore distributed training methods and alternative architectures.
            """
        ),
        "paper_2": PaperRecord(
            id="paper_2",
            file_path="/test/paper2.pdf",
            filename="paper2.pdf",
            title="Paper 2",
            deep_summary="Too short"  # Invalid
        ),
        "paper_3": PaperRecord(
            id="paper_3",
            file_path="/test/paper3.pdf",
            filename="paper3.pdf",
            title="Paper 3",
            deep_summary=None  # No analysis
        ),
    }
    
    results = validate_paper_deep_analyses(papers)
    
    print(f"\nValidation Results:")
    print(f"  Total papers: {results['total_papers']}")
    print(f"  Papers with deep analysis: {results['papers_with_deep_analysis']}")
    print(f"  Valid analyses: {results['valid_deep_analyses']}")
    print(f"  Invalid analyses: {results['invalid_deep_analyses']}")
    print(f"  Validation rate: {results['validation_rate']:.2%}")
    
    assert results['total_papers'] == 3
    assert results['papers_with_deep_analysis'] == 2
    assert results['valid_deep_analyses'] == 1
    assert results['invalid_deep_analyses'] == 1
    
    print("\n✓ Multiple deep analysis validation works correctly")


# =============================================================================
# Test Cost Estimation
# =============================================================================

def test_estimate_deep_analysis_cost():
    """Test deep analysis cost estimation."""
    if not DEEP_ANALYSIS_MODULE_AVAILABLE:
        print("Skipping test_estimate_deep_analysis_cost: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Deep Analysis Cost Estimation")
    print("=" * 70)
    
    # Estimate cost for 20 papers
    estimate = estimate_deep_analysis_cost(
        num_papers=20,
        avg_paper_length_chars=8000,
        model="gpt-5.1"
    )
    
    print(f"\nEstimate for 20 papers:")
    print(f"  Model: {estimate['model']}")
    print(f"  Avg paper length: {estimate['avg_paper_length_chars']:,} chars")
    print(f"  Input tokens: {estimate['estimated_input_tokens']:,}")
    print(f"  Output tokens: {estimate['estimated_output_tokens']:,}")
    print(f"  Total tokens: {estimate['estimated_total_tokens']:,}")
    print(f"  Estimated cost: ${estimate['estimated_cost_usd']:.4f}")
    print(f"  Cost per paper: ${estimate['cost_per_paper_usd']:.4f}")
    
    assert estimate['num_papers'] == 20
    assert estimate['estimated_total_tokens'] > 0
    assert estimate['estimated_cost_usd'] > 0
    assert estimate['cost_per_paper_usd'] > 0
    
    # Compare to smaller batch
    small_estimate = estimate_deep_analysis_cost(
        num_papers=5,
        avg_paper_length_chars=8000,
        model="gpt-5.1"
    )
    
    print(f"\nEstimate for 5 papers:")
    print(f"  Estimated cost: ${small_estimate['estimated_cost_usd']:.4f}")
    print(f"  Cost per paper: ${small_estimate['cost_per_paper_usd']:.4f}")
    
    # Cost per paper should be the same regardless of batch size
    assert abs(estimate['cost_per_paper_usd'] - small_estimate['cost_per_paper_usd']) < 0.01
    
    print("\n✓ Deep analysis cost estimation works correctly")


# =============================================================================
# Mock Tests (for environments without OpenAI API)
# =============================================================================

def test_deep_analysis_generator_mock():
    """Test DeepAnalysisGenerator with mocked API calls."""
    if not DEEP_ANALYSIS_MODULE_AVAILABLE:
        print("Skipping test_deep_analysis_generator_mock: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Deep Analysis Generator (Mocked)")
    print("=" * 70)
    
    # Create mock response - Responses API format
    mock_response = MagicMock()
    mock_output_item = MagicMock()
    mock_content_item = MagicMock()
    mock_content_item.text = """
    Detailed Methodology Breakdown: The paper uses a transformer-based approach
    with novel attention mechanisms. Experiments were conducted on ImageNet with
    custom data augmentation. The model architecture includes residual connections.
    
    Experimental Setup Details: Training used 8 NVIDIA V100 GPUs with batch size 64.
    The optimizer was AdamW with learning rate scheduling. Evaluation included
    accuracy, precision, recall, and F1 metrics across multiple datasets.
    
    Key Results and Metrics: Achieved 95.3% accuracy on ImageNet validation (baseline: 92.1%).
    Inference latency reduced by 18% compared to ResNet-50. Statistical significance
    confirmed with p-value < 0.001 using paired t-tests.
    
    Limitations and Constraints: Requires large amounts of training data and GPU memory.
    Performance drops on out-of-distribution samples. Computational cost is high.
    
    Future Work and Extensions: Exploring few-shot learning scenarios. Extending to
    video understanding tasks. Investigating model interpretability and explainability.
    
    Comprehensive Notes:
    - Novel attention mechanism improves feature extraction
    - Data augmentation crucial for generalization
    - Model achieves strong results with reasonable computational cost
    - Approach generalizes well to related vision tasks
    """
    mock_output_item.content = [mock_content_item]
    mock_response.output = [mock_output_item]
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 500
    mock_response.usage.completion_tokens = 400
    mock_response.usage.total_tokens = 900
    
    with patch('deep_analysis_pass2.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_client.responses.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create generator
        generator = DeepAnalysisGenerator(
            api_key="test_key",
            model="gpt-5.1",
            reasoning_effort="high"
        )
        
        # Generate deep analysis
        analysis, stats = generator.generate_deep_analysis(
            system_prompt="You are an expert researcher.",
            user_prompt="Analyze this paper..."
        )
        
        print(f"\nGenerated analysis preview:")
        print(analysis[:200] + "...")
        print(f"\nStats:")
        print(f"  Total tokens: {stats['total_tokens']}")
        print(f"  Prompt tokens: {stats['prompt_tokens']}")
        print(f"  Completion tokens: {stats['completion_tokens']}")
        
        assert len(analysis) > 100, "Should generate substantial analysis"
        assert stats['total_tokens'] == 900
        assert "methodology" in analysis.lower()
        
        # Verify API was called correctly
        assert mock_client.responses.create.called
        call_args = mock_client.responses.create.call_args
        assert call_args[1]['model'] == "gpt-5.1"
        assert call_args[1]['reasoning_effort'] == "high"
        
    print("\n✓ Mocked deep analysis generator works correctly")


# =============================================================================
# Run All Tests
# =============================================================================

def run_all_tests():
    """Run all test functions."""
    print("\n" + "=" * 70)
    print("PHASE 11 TEST SUITE: Deep Analysis Pass (Optional - Pass 2)")
    print("=" * 70)
    
    if not DEEP_ANALYSIS_MODULE_AVAILABLE:
        print("\n⚠ Deep analysis module not available. Skipping all tests.")
        return
    
    test_functions = [
        test_should_perform_deep_analysis,
        test_check_deep_analysis_flag,
        test_deep_analysis_prompt_creation,
        test_deep_analysis_prompt_factory,
        test_select_papers_for_deep_analysis,
        test_validate_deep_analysis,
        test_validate_paper_deep_analyses,
        test_estimate_deep_analysis_cost,
        test_deep_analysis_generator_mock,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ Test failed: {test_func.__name__}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ Test error: {test_func.__name__}")
            print(f"  Error: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
