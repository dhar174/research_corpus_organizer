#!/usr/bin/env python3
"""
Test suite for Phase 6: Summarization (Pass 1) and Phase 7: Export

Tests all functionality in summarization_pass1.py and export_manager.py including:
- Summary generation with OpenAI API
- Prompt creation and customization
- Initial notes generation
- Batch processing and retry logic
- Summary validation
- CSV/Parquet export
- Export validation

Note: Some tests require OpenAI API key.
Mock tests are provided for environments without API access.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    PaperRecord,
    PaperChunk,
    StateManager,
    create_default_config,
)

# Try importing the phase 6 modules
try:
    from summarization_pass1 import (
        SummaryGenerator,
        SummaryPromptFactory,
        create_summary_prompt,
        create_notes_prompt,
        summarize_paper_node,
        generate_initial_notes,
        extract_key_insights,
        batch_summarize_papers,
        validate_summary,
        validate_paper_summaries,
        estimate_summarization_cost,
    )
    SUMMARIZATION_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import summarization_pass1: {e}")
    SUMMARIZATION_MODULE_AVAILABLE = False

try:
    from export_manager import (
        export_papers_to_csv,
        export_papers_to_dict,
        export_after_pass1,
        validate_export,
        export_summary_statistics,
        flatten_paper_record,
        ExportConfig,
    )
    EXPORT_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import export_manager: {e}")
    EXPORT_MODULE_AVAILABLE = False


# =============================================================================
# Test Step 6.1: Summary Generator
# =============================================================================

def test_estimate_summarization_cost():
    """Test summarization cost estimation."""
    if not SUMMARIZATION_MODULE_AVAILABLE:
        print("Skipping test_estimate_summarization_cost: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Summarization Cost Estimation")
    print("=" * 70)
    
    # Estimate cost for 10 papers
    estimate = estimate_summarization_cost(
        num_papers=10,
        avg_paper_length_chars=5000,
        model="gpt-5.1-mini",
        include_notes=True
    )
    
    print(f"\nEstimate for 10 papers:")
    print(f"  Total tokens: {estimate['estimated_tokens']:,}")
    print(f"  Summary tokens: {estimate['estimated_tokens_summary']:,}")
    print(f"  Notes tokens: {estimate['estimated_tokens_notes']:,}")
    print(f"  Estimated cost: ${estimate['estimated_cost_usd']:.4f}")
    print(f"  Cost per paper: ${estimate['cost_per_paper_usd']:.4f}")
    
    assert estimate['num_papers'] == 10
    assert estimate['estimated_tokens'] > 0
    assert estimate['estimated_cost_usd'] > 0
    assert estimate['include_notes'] is True
    
    print("\n✓ Cost estimation working correctly")


def test_summary_prompt_factory():
    """Test summary prompt creation."""
    if not SUMMARIZATION_MODULE_AVAILABLE:
        print("Skipping test_summary_prompt_factory: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Summary Prompt Factory")
    print("=" * 70)
    
    # Test system prompt
    system_prompt = SummaryPromptFactory.create_system_prompt("research paper")
    print(f"\nSystem prompt created (length: {len(system_prompt)} chars)")
    assert "researcher" in system_prompt.lower()
    assert "summary" in system_prompt.lower()
    
    # Test user prompt
    user_prompt = SummaryPromptFactory.create_user_prompt(
        title="Test Paper",
        abstract="This is a test abstract.",
        intro_text="Introduction text...",
        methods_text=None,
        results_text=None,
        conclusion_text=None,
        max_length=100
    )
    
    print(f"User prompt created (length: {len(user_prompt)} chars)")
    assert "Test Paper" in user_prompt
    assert "test abstract" in user_prompt
    
    # Test notes prompt
    notes_prompt = SummaryPromptFactory.create_notes_prompt(
        title="Test Paper",
        abstract="Abstract text",
        summary="Summary text"
    )
    
    print(f"Notes prompt created (length: {len(notes_prompt)} chars)")
    assert "notes" in notes_prompt.lower()
    assert "Summary text" in notes_prompt
    
    print("\n✓ Prompt factory working correctly")


def test_create_summary_prompt():
    """Test creating prompts from paper and chunks."""
    if not SUMMARIZATION_MODULE_AVAILABLE:
        print("Skipping test_create_summary_prompt: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Create Summary Prompt from Paper")
    print("=" * 70)
    
    # Create test paper and chunks
    paper = PaperRecord(
        id="paper1",
        file_path="/test/paper.pdf",
        filename="paper.pdf",
        title="Deep Learning Paper",
        abstract_text="This paper explores deep learning...",
        is_preprint=True
    )
    
    chunks = [
        PaperChunk(
            paper_id="paper1",
            chunk_id="chunk1",
            section_label="abstract",
            page_start=1,
            page_end=1,
            text="Abstract content..."
        ),
        PaperChunk(
            paper_id="paper1",
            chunk_id="chunk2",
            section_label="introduction",
            page_start=1,
            page_end=2,
            text="Introduction content..."
        ),
    ]
    
    config = create_default_config()
    
    # Create prompts
    system_prompt, user_prompt = create_summary_prompt(paper, chunks, config)
    
    print(f"\nSystem prompt: {len(system_prompt)} chars")
    print(f"User prompt: {len(user_prompt)} chars")
    
    assert "preprint" in system_prompt.lower()
    assert paper.title in user_prompt
    assert len(system_prompt) > 0
    assert len(user_prompt) > 0
    
    print("\n✓ Summary prompt creation working correctly")


def test_summary_generator_mock():
    """Test SummaryGenerator with mocked OpenAI client."""
    if not SUMMARIZATION_MODULE_AVAILABLE:
        print("Skipping test_summary_generator_mock: dependencies not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: SummaryGenerator (Mock)")
    print("=" * 70)
    
    # Mock OpenAI response
    mock_summary = """**Main Contribution**: Novel architecture for deep learning.
**Problem Statement**: Previous models were slow.
**Methodology**: New attention mechanism.
**Key Findings**: Achieves state-of-the-art results.
**Significance**: Enables faster training."""
    
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content=mock_summary))]
    mock_response.usage = Mock(
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150
    )
    
    with patch('summarization_pass1.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create generator
        generator = SummaryGenerator(
            api_key="test_key",
            model="gpt-5.1-mini",
            reasoning_effort="medium",
            max_tokens=2000,
        )
        
        print(f"\nGenerator created: model={generator.model}")
        
        # Generate summary
        summary, usage_stats = generator.generate_summary(
            system_prompt="Test system prompt",
            user_prompt="Test user prompt"
        )
        
        print(f"\nGenerated summary:")
        print(f"  Length: {len(summary)} chars")
        print(f"  Tokens: {usage_stats['total_tokens']}")
        print(f"  Model: {usage_stats['model']}")
        
        assert len(summary) > 0
        assert "Main Contribution" in summary
        assert usage_stats['total_tokens'] == 150
        assert usage_stats['prompt_tokens'] == 100
        assert usage_stats['completion_tokens'] == 50
        
        # Check cumulative stats
        stats = generator.get_stats()
        print(f"\nCumulative stats:")
        print(f"  Total tokens: {stats['total_tokens']}")
        print(f"  API calls: {stats['api_calls']}")
        print(f"  Est. cost: ${stats['estimated_cost_usd']:.6f}")
        
        assert stats['total_tokens'] == 150
        assert stats['api_calls'] == 1
    
    print("\n✓ SummaryGenerator mock test passed")


# =============================================================================
# Test Step 6.2 & 6.3: Summarization Node and Notes
# =============================================================================

def test_summarize_paper_node_mock():
    """Test summarize_paper_node with mocked API."""
    if not SUMMARIZATION_MODULE_AVAILABLE:
        print("Skipping test_summarize_paper_node_mock: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Summarize Paper Node (Mock)")
    print("=" * 70)
    
    # Create state with paper
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    paper = PaperRecord(
        id="paper1",
        file_path="/test/paper.pdf",
        filename="paper.pdf",
        title="Test Paper"
    )
    
    state = StateManager.add_paper(state, paper)
    
    chunks = [
        PaperChunk(
            paper_id="paper1",
            chunk_id="chunk1",
            section_label="abstract",
            page_start=1,
            page_end=1,
            text="Abstract content..."
        ),
    ]
    
    state = StateManager.add_chunks(state, "paper1", chunks)
    
    # Mock API
    mock_summary = "This is a comprehensive summary of the paper."
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content=mock_summary))]
    mock_response.usage = Mock(prompt_tokens=50, completion_tokens=25, total_tokens=75)
    
    with patch('summarization_pass1.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Summarize paper
        updated_state = summarize_paper_node("paper1", state, "test_key")
        
        # Check results
        paper = updated_state["papers"]["paper1"]
        print(f"\nPaper summarized:")
        print(f"  Status: {paper.processing_status}")
        print(f"  Summary length: {len(paper.full_summary or '')} chars")
        print(f"  Tokens used: {updated_state['stats']['summarization_tokens']}")
        
        assert paper.processing_status == "summarized"
        assert paper.full_summary == mock_summary
        assert updated_state["stats"]["summarization_tokens"] == 75
        assert updated_state["stats"]["summarization_calls"] == 1
    
    print("\n✓ Summarize paper node test passed")


# =============================================================================
# Test Step 6.5: Summary Validation
# =============================================================================

def test_validate_summary():
    """Test summary validation."""
    if not SUMMARIZATION_MODULE_AVAILABLE:
        print("Skipping test_validate_summary: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Summary Validation")
    print("=" * 70)
    
    paper = PaperRecord(
        id="paper1",
        file_path="/test/paper.pdf",
        filename="paper.pdf"
    )
    
    # Test valid summary
    valid_summary = """
**Main Contribution**: Novel deep learning architecture.
**Problem Statement**: Previous models were inefficient.
**Methodology**: Introduced new attention mechanism.
**Key Findings**: Achieves 95% accuracy on benchmark.
**Significance**: Enables faster training times.
"""
    
    validation = validate_summary(valid_summary, paper)
    print(f"\nValid summary validation:")
    print(f"  Valid: {validation['valid']}")
    print(f"  Length: {validation['length']} words")
    print(f"  Issues: {validation['issues']}")
    print(f"  Warnings: {validation['warnings']}")
    
    assert validation['valid']
    assert validation['length'] > 50
    assert len(validation['issues']) == 0
    
    # Test invalid summary (too short)
    invalid_summary = "This paper is about deep learning."
    
    validation = validate_summary(invalid_summary, paper)
    print(f"\nInvalid summary validation:")
    print(f"  Valid: {validation['valid']}")
    print(f"  Length: {validation['length']} words")
    print(f"  Issues: {validation['issues']}")
    
    assert not validation['valid']
    assert len(validation['issues']) > 0
    
    # Test empty summary
    empty_validation = validate_summary("", paper)
    assert not empty_validation['valid']
    
    print("\n✓ Summary validation test passed")


def test_extract_key_insights():
    """Test extracting key insights from summary."""
    if not SUMMARIZATION_MODULE_AVAILABLE:
        print("Skipping test_extract_key_insights: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Extract Key Insights")
    print("=" * 70)
    
    summary = """
This paper introduces a novel approach to natural language processing.
The authors demonstrate significant improvements over baseline models.
The proposed method shows remarkable performance on benchmark datasets.
Traditional approaches contribute to computational inefficiency.
This work discovers new patterns in language understanding.
"""
    
    insights = extract_key_insights(summary)
    
    print(f"\nExtracted {len(insights)} insights:")
    for i, insight in enumerate(insights, 1):
        print(f"  {i}. {insight[:60]}...")
    
    assert len(insights) > 0
    assert isinstance(insights, list)
    
    print("\n✓ Key insights extraction test passed")


# =============================================================================
# Test Phase 7: Export Functions
# =============================================================================

def test_flatten_paper_record():
    """Test flattening paper record for export."""
    if not EXPORT_MODULE_AVAILABLE:
        print("Skipping test_flatten_paper_record: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Flatten Paper Record")
    print("=" * 70)
    
    paper = PaperRecord(
        id="paper1",
        file_path="/test/paper.pdf",
        filename="paper.pdf",
        title="Test Paper",
        authors=["Author 1", "Author 2"],
        year=2023,
        raw_text_stats={"chars": 10000, "pages": 10}
    )
    
    config = ExportConfig(flatten_nested=True)
    flattened = flatten_paper_record(paper, config)
    
    print(f"\nFlattened record:")
    print(f"  Fields: {len(flattened)}")
    print(f"  Authors type: {type(flattened.get('authors'))}")
    print(f"  Authors value: {flattened.get('authors')}")
    
    assert isinstance(flattened, dict)
    assert "title" in flattened
    # Authors should be flattened to string
    assert isinstance(flattened["authors"], str)
    assert "Author 1" in flattened["authors"]
    
    print("\n✓ Flatten paper record test passed")


def test_export_papers_to_csv():
    """Test CSV export."""
    if not EXPORT_MODULE_AVAILABLE:
        print("Skipping test_export_papers_to_csv: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Export Papers to CSV")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test papers
        papers = {
            "paper1": PaperRecord(
                id="paper1",
                file_path="/test/paper1.pdf",
                filename="paper1.pdf",
                title="Paper 1",
                full_summary="Summary 1",
                processing_status="summarized"
            ),
            "paper2": PaperRecord(
                id="paper2",
                file_path="/test/paper2.pdf",
                filename="paper2.pdf",
                title="Paper 2",
                full_summary="Summary 2",
                processing_status="summarized"
            ),
        }
        
        # Export
        output_path = Path(tmpdir) / "papers.csv"
        result_path = export_papers_to_csv(papers, str(output_path))
        
        print(f"\nExported to: {result_path}")
        assert Path(result_path).exists()
        
        # Validate
        file_size = Path(result_path).stat().st_size
        print(f"File size: {file_size} bytes")
        assert file_size > 0
        
        # Check content
        with open(result_path, 'r') as f:
            content = f.read()
            assert "Paper 1" in content
            assert "Paper 2" in content
            print(f"Content preview: {content[:200]}...")
    
    print("\n✓ CSV export test passed")


def test_validate_export():
    """Test export validation."""
    if not EXPORT_MODULE_AVAILABLE:
        print("Skipping test_validate_export: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Export Validation")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create and export papers
        papers = {
            f"paper{i}": PaperRecord(
                id=f"paper{i}",
                file_path=f"/test/paper{i}.pdf",
                filename=f"paper{i}.pdf",
                title=f"Paper {i}"
            )
            for i in range(5)
        }
        
        output_path = Path(tmpdir) / "papers.csv"
        export_papers_to_csv(papers, str(output_path))
        
        # Validate
        validation = validate_export(
            export_path=str(output_path),
            expected_count=5
        )
        
        print(f"\nValidation results:")
        print(f"  Valid: {validation['valid']}")
        print(f"  Row count: {validation['row_count']}")
        print(f"  File size: {validation['file_size']} bytes")
        print(f"  Issues: {validation['issues']}")
        print(f"  Warnings: {validation['warnings']}")
        
        assert validation['valid']
        assert validation['row_count'] == 5
        assert validation['file_size'] > 0
    
    print("\n✓ Export validation test passed")


def test_export_summary_statistics():
    """Test export statistics generation."""
    if not EXPORT_MODULE_AVAILABLE:
        print("Skipping test_export_summary_statistics: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Export Summary Statistics")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create and export papers
        papers = {
            "paper1": PaperRecord(
                id="paper1",
                file_path="/test/paper1.pdf",
                filename="paper1.pdf",
                title="Paper 1",
                processing_status="summarized"
            ),
        }
        
        output_path = Path(tmpdir) / "papers.csv"
        export_papers_to_csv(papers, str(output_path))
        
        # Get statistics
        stats = export_summary_statistics(str(output_path))
        
        print(f"\nExport statistics:")
        print(f"  File name: {stats['file_name']}")
        print(f"  Row count: {stats.get('row_count', 0)}")
        print(f"  File size: {stats['file_size_kb']} KB")
        
        assert stats['file_name'] == "papers.csv"
        assert stats['file_size_bytes'] > 0
    
    print("\n✓ Export statistics test passed")


# =============================================================================
# Main Test Runner
# =============================================================================

def run_all_tests():
    """Run all Phase 6 and 7 tests."""
    print("\n" + "=" * 70)
    print("PHASE 6 & 7: SUMMARIZATION AND EXPORT - TEST SUITE")
    print("=" * 70)
    
    if not SUMMARIZATION_MODULE_AVAILABLE:
        print("\nWARNING: summarization_pass1 module not available")
    
    if not EXPORT_MODULE_AVAILABLE:
        print("\nWARNING: export_manager module not available")
    
    if not (SUMMARIZATION_MODULE_AVAILABLE or EXPORT_MODULE_AVAILABLE):
        print("\nERROR: No modules available for testing")
        return
    
    tests = [
        # Phase 6: Summarization
        ("Cost Estimation", test_estimate_summarization_cost),
        ("Summary Prompt Factory", test_summary_prompt_factory),
        ("Create Summary Prompt", test_create_summary_prompt),
        ("Summary Generator (Mock)", test_summary_generator_mock),
        ("Summarize Paper Node (Mock)", test_summarize_paper_node_mock),
        ("Validate Summary", test_validate_summary),
        ("Extract Key Insights", test_extract_key_insights),
        
        # Phase 7: Export
        ("Flatten Paper Record", test_flatten_paper_record),
        ("Export Papers to CSV", test_export_papers_to_csv),
        ("Validate Export", test_validate_export),
        ("Export Summary Statistics", test_export_summary_statistics),
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ {test_name} FAILED: {e}")
            failed += 1
        except Exception as e:
            if "Skipping" in str(e) or "not available" in str(e):
                skipped += 1
            else:
                print(f"\n✗ {test_name} ERROR: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Skipped: {skipped}")
    print(f"Total:   {len(tests)}")
    print("=" * 70)
    
    if failed > 0:
        print("\n⚠️  Some tests failed. Please review the output above.")
    elif passed == len(tests):
        print("\n✓ All tests passed!")
    else:
        print(f"\n✓ {passed} tests passed, {skipped} skipped (missing dependencies)")


if __name__ == "__main__":
    run_all_tests()
