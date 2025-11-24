#!/usr/bin/env python3
"""
Test suite for Phase 14: Quality Control and Validation

Tests all functionality in quality_control.py:
- Step 14.1: QC Dashboard
- Step 14.2: Data Quality Checks
- Step 14.3: Error Analysis
- Step 14.4: Consistency Validation
- Step 14.5: QC Report Generation

This test suite ensures comprehensive quality control and validation.
"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime, date
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    PaperRecord,
    PaperChunk,
    TopicNode,
    TopicHierarchy,
    create_default_config,
    GraphState,
)

from quality_control import (
    # Step 14.1: QC Dashboard
    QCDashboard,
    create_qc_dashboard,
    display_qc_statistics,
    
    # Step 14.2: Data Quality Checks
    DataQualityChecker,
    verify_pdfs_processed,
    check_missing_metadata,
    validate_embedding_integrity,
    check_summary_completeness,
    verify_topic_assignments,
    
    # Step 14.3: Error Analysis
    ErrorAnalyzer,
    list_failed_papers,
    categorize_error_types,
    suggest_remediation,
    export_error_log,
    
    # Step 14.4: Consistency Validation
    ConsistencyValidator,
    check_taxonomy_consistency,
    validate_hierarchical_relationships,
    verify_paper_counts,
    check_orphaned_records,
    validate_timestamp_sequences,
    
    # Step 14.5: QC Report Generation
    QCReportGenerator,
    generate_qc_report,
    export_report_markdown,
    export_report_html,
    save_report_to_drive,
)


# =============================================================================
# Helper Functions
# =============================================================================

def create_sample_state(num_papers=5, include_failures=True, include_taxonomy=True):
    """Create sample state with papers for testing."""
    config = create_default_config()
    
    papers = {}
    chunks = {}
    
    # Create sample papers with various statuses
    for i in range(num_papers):
        paper_id = f"paper_{i}"
        
        if i == 0 and include_failures:
            # Failed paper
            paper = PaperRecord(
                id=paper_id,
                file_path=f"/path/to/{paper_id}.pdf",
                filename=f"{paper_id}.pdf",
                processing_status="failed",
                error_stage="parsing",
                error_reason="PDF parsing failed: corrupted file",
                retry_count=2,
            )
        elif i == 1:
            # Pending paper
            paper = PaperRecord(
                id=paper_id,
                file_path=f"/path/to/{paper_id}.pdf",
                filename=f"{paper_id}.pdf",
                processing_status="pending",
            )
        elif i == 2:
            # Parsed paper with some metadata
            paper = PaperRecord(
                id=paper_id,
                file_path=f"/path/to/{paper_id}.pdf",
                filename=f"{paper_id}.pdf",
                processing_status="parsed",
                title=f"Paper {i} Title",
                authors=["Author A", "Author B"],
            )
        elif i == 3:
            # Summarized paper
            paper = PaperRecord(
                id=paper_id,
                file_path=f"/path/to/{paper_id}.pdf",
                filename=f"{paper_id}.pdf",
                processing_status="summarized",
                title=f"Paper {i} Title",
                authors=["Author C"],
                publish_date=date(2024, 1, 1),
                full_summary="This is a summary of the paper.",
            )
        else:
            # Classified paper
            paper = PaperRecord(
                id=paper_id,
                file_path=f"/path/to/{paper_id}.pdf",
                filename=f"{paper_id}.pdf",
                processing_status="classified",
                title=f"Paper {i} Title",
                authors=["Author D", "Author E"],
                publish_date=date(2024, 2, 1),
                full_summary="This is a summary of the paper.",
                tier1_topic="tier1_1",
                tier1_topic_name="Machine Learning",
                tier1_confidence=0.85,
                tier2_topic="tier2_1",
                tier2_topic_name="Deep Learning",
                tier2_confidence=0.80,
            )
        
        papers[paper_id] = paper
        
        # Add chunks for parsed and later stages
        if paper.processing_status in ["parsed", "summarized", "classified"]:
            chunks[paper_id] = [
                PaperChunk(
                    paper_id=paper_id,
                    chunk_id=f"{paper_id}_chunk_0",
                    section_label="abstract",
                    text="This is the abstract text.",
                ),
                PaperChunk(
                    paper_id=paper_id,
                    chunk_id=f"{paper_id}_chunk_1",
                    section_label="introduction",
                    text="This is the introduction text.",
                ),
            ]
    
    # Create sample taxonomy
    taxonomy = None
    if include_taxonomy:
        taxonomy = TopicHierarchy(
            taxonomy_version="1.0",
            total_papers=num_papers - 2,  # Exclude failed and pending
            tier1=[
                TopicNode(
                    id="tier1_1",
                    name="Machine Learning",
                    tier=1,
                    paper_count=2,
                )
            ],
            tier2=[
                TopicNode(
                    id="tier2_1",
                    name="Deep Learning",
                    tier=2,
                    parent_id="tier1_1",
                    paper_count=1,
                )
            ],
            tier3=[],
        )
    
    state: GraphState = {
        "config": config,
        "papers": papers,
        "chunks": chunks,
        "topic_hierarchy": taxonomy,
        "taxonomy_approved": True,
        "faiss_index_path": "/path/to/index.faiss",
        "faiss_meta_path": "/path/to/index_meta.pkl",
        "current_phase": "classification",
        "papers_pending": ["paper_1"],
        "papers_completed": ["paper_3", "paper_4"],
        "papers_failed": ["paper_0"],
        "errors": [],
        "stats": {},
    }
    
    return state


# =============================================================================
# Test Step 14.1: QC Dashboard
# =============================================================================

def test_qc_dashboard_creation():
    """Test QCDashboard creation."""
    print("\n=== Test: QC Dashboard Creation ===")
    
    state = create_sample_state()
    dashboard = create_qc_dashboard(state)
    
    assert isinstance(dashboard, QCDashboard)
    assert dashboard.state == state
    assert len(dashboard.papers) == 5
    print("✓ QC Dashboard created successfully")


def test_get_overall_statistics():
    """Test overall statistics retrieval."""
    print("\n=== Test: Overall Statistics ===")
    
    state = create_sample_state()
    dashboard = QCDashboard(state)
    stats = dashboard.get_overall_statistics()
    
    assert stats["total_papers"] == 5
    assert stats["total_chunks"] == 6  # 3 papers with 2 chunks each
    assert "status_counts" in stats
    assert "metadata_completeness" in stats
    assert "summary_completeness" in stats
    assert "topic_assignments" in stats
    
    print(f"  Total papers: {stats['total_papers']}")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Status counts: {stats['status_counts']}")
    print("✓ Overall statistics retrieved successfully")


def test_get_status_distribution():
    """Test status distribution."""
    print("\n=== Test: Status Distribution ===")
    
    state = create_sample_state()
    dashboard = QCDashboard(state)
    dist = dashboard.get_status_distribution()
    
    assert dist["failed"] == 1
    assert dist["pending"] == 1
    assert dist["parsed"] == 1
    assert dist["summarized"] == 1
    assert dist["classified"] == 1
    
    print(f"  Distribution: {dist}")
    print("✓ Status distribution calculated successfully")


def test_get_failed_papers():
    """Test failed papers retrieval."""
    print("\n=== Test: Failed Papers ===")
    
    state = create_sample_state()
    dashboard = QCDashboard(state)
    failed = dashboard.get_failed_papers()
    
    assert len(failed) == 1
    assert failed[0]["id"] == "paper_0"
    assert failed[0]["error_stage"] == "parsing"
    assert "error_reason" in failed[0]
    
    print(f"  Failed papers: {len(failed)}")
    print(f"  First failure: {failed[0]['filename']} - {failed[0]['error_reason']}")
    print("✓ Failed papers retrieved successfully")


def test_get_quality_score_distribution():
    """Test quality score distribution."""
    print("\n=== Test: Quality Score Distribution ===")
    
    state = create_sample_state()
    dashboard = QCDashboard(state)
    quality = dashboard.get_quality_score_distribution()
    
    assert "distribution" in quality
    assert "average_score" in quality
    assert quality["average_score"] >= 0
    assert quality["average_score"] <= 1
    
    print(f"  Average score: {quality['average_score']:.2f}")
    print(f"  Distribution: {quality['distribution']}")
    print("✓ Quality score distribution calculated successfully")


def test_get_topic_distribution():
    """Test topic distribution."""
    print("\n=== Test: Topic Distribution ===")
    
    state = create_sample_state()
    dashboard = QCDashboard(state)
    topics = dashboard.get_topic_distribution()
    
    assert "tier1" in topics
    assert "tier2" in topics
    assert "tier3" in topics
    assert "unclassified" in topics
    
    print(f"  Tier 1 topics: {topics['tier1']}")
    print(f"  Tier 2 topics: {topics['tier2']}")
    print(f"  Unclassified: {topics['unclassified']}")
    print("✓ Topic distribution calculated successfully")


def test_display_qc_statistics():
    """Test QC statistics display."""
    print("\n=== Test: Display QC Statistics ===")
    
    state = create_sample_state()
    display = display_qc_statistics(state)
    
    assert isinstance(display, str)
    assert "QUALITY CONTROL DASHBOARD" in display
    assert "OVERALL STATISTICS" in display
    assert "PROCESSING STATUS" in display
    
    print(display)
    print("✓ QC statistics displayed successfully")


# =============================================================================
# Test Step 14.2: Data Quality Checks
# =============================================================================

def test_verify_pdfs_processed():
    """Test PDF processing verification."""
    print("\n=== Test: Verify PDFs Processed ===")
    
    state = create_sample_state()
    result = verify_pdfs_processed(state)
    
    assert result["total_papers"] == 5
    assert result["pending"] == 1
    assert result["failed"] == 1
    assert result["processed"] == 4
    assert "success_rate" in result
    
    print(f"  Total: {result['total_papers']}")
    print(f"  Processed: {result['processed']}")
    print(f"  Success rate: {result['success_rate']:.1f}%")
    print("✓ PDF processing verification completed")


def test_check_missing_metadata():
    """Test missing metadata check."""
    print("\n=== Test: Check Missing Metadata ===")
    
    state = create_sample_state()
    result = check_missing_metadata(state)
    
    assert "missing_counts" in result
    assert "missing_details" in result
    assert "papers_with_complete_metadata" in result
    
    print(f"  Missing counts: {result['missing_counts']}")
    print(f"  Papers with complete metadata: {result['papers_with_complete_metadata']}")
    print("✓ Missing metadata check completed")


def test_validate_embedding_integrity():
    """Test embedding integrity validation."""
    print("\n=== Test: Validate Embedding Integrity ===")
    
    state = create_sample_state()
    result = validate_embedding_integrity(state)
    
    assert "total_chunks" in result
    assert "papers_with_chunks" in result
    assert "integrity_status" in result
    
    print(f"  Total chunks: {result['total_chunks']}")
    print(f"  Papers with chunks: {result['papers_with_chunks']}")
    print(f"  Status: {result['integrity_status']}")
    print("✓ Embedding integrity validation completed")


def test_check_summary_completeness():
    """Test summary completeness check."""
    print("\n=== Test: Check Summary Completeness ===")
    
    state = create_sample_state()
    result = check_summary_completeness(state)
    
    assert "papers_needing_summary" in result
    assert "with_summary" in result
    assert "completeness_rate" in result
    
    print(f"  Papers needing summary: {result['papers_needing_summary']}")
    print(f"  With summary: {result['with_summary']}")
    print(f"  Completeness rate: {result['completeness_rate']:.1f}%")
    print("✓ Summary completeness check completed")


def test_verify_topic_assignments():
    """Test topic assignment verification."""
    print("\n=== Test: Verify Topic Assignments ===")
    
    state = create_sample_state()
    result = verify_topic_assignments(state)
    
    assert "papers_needing_classification" in result
    assert "with_tier1" in result
    assert "classification_rate" in result
    
    print(f"  Papers needing classification: {result['papers_needing_classification']}")
    print(f"  With Tier 1: {result['with_tier1']}")
    print(f"  Classification rate: {result['classification_rate']:.1f}%")
    print("✓ Topic assignment verification completed")


# =============================================================================
# Test Step 14.3: Error Analysis
# =============================================================================

def test_list_failed_papers():
    """Test failed papers listing."""
    print("\n=== Test: List Failed Papers ===")
    
    state = create_sample_state()
    failed = list_failed_papers(state)
    
    assert len(failed) == 1
    assert failed[0]["id"] == "paper_0"
    assert "error_stage" in failed[0]
    assert "error_reason" in failed[0]
    
    print(f"  Failed papers: {len(failed)}")
    for f in failed:
        print(f"    - {f['filename']}: {f['error_reason']}")
    print("✓ Failed papers listed successfully")


def test_categorize_error_types():
    """Test error categorization."""
    print("\n=== Test: Categorize Error Types ===")
    
    state = create_sample_state()
    result = categorize_error_types(state)
    
    assert "by_stage" in result
    assert "by_type" in result
    assert "total_failures" in result
    
    print(f"  By stage: {result['by_stage']}")
    print(f"  By type: {result['by_type']}")
    print(f"  Total failures: {result['total_failures']}")
    print("✓ Error categorization completed")


def test_suggest_remediation():
    """Test remediation suggestions."""
    print("\n=== Test: Suggest Remediation ===")
    
    state = create_sample_state()
    suggestions = suggest_remediation(state)
    
    assert isinstance(suggestions, dict)
    # Should have suggestions for the pdf_parsing error type
    assert len(suggestions) > 0
    
    print("  Remediation suggestions:")
    for error_type, steps in suggestions.items():
        print(f"    {error_type}:")
        for step in steps:
            print(f"      - {step}")
    print("✓ Remediation suggestions generated")


def test_export_error_log():
    """Test error log export."""
    print("\n=== Test: Export Error Log ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        state = create_sample_state()
        output_path = str(Path(tmpdir) / "error_log.txt")
        
        result_path = export_error_log(state, output_path)
        
        assert Path(result_path).exists()
        
        # Read and check content
        with open(result_path, 'r') as f:
            content = f.read()
        
        assert "ERROR LOG" in content
        assert "paper_0" in content
        
        print(f"  Error log exported to: {result_path}")
        print("✓ Error log export completed")


# =============================================================================
# Test Step 14.4: Consistency Validation
# =============================================================================

def test_check_taxonomy_consistency():
    """Test taxonomy consistency check."""
    print("\n=== Test: Check Taxonomy Consistency ===")
    
    state = create_sample_state()
    result = check_taxonomy_consistency(state)
    
    assert "status" in result
    assert result["status"] in ["VALID", "INVALID", "NO_TAXONOMY"]
    
    print(f"  Status: {result['status']}")
    if "validation_result" in result:
        print(f"  Validation: {result['validation_result']}")
    print("✓ Taxonomy consistency check completed")


def test_validate_hierarchical_relationships():
    """Test hierarchical relationship validation."""
    print("\n=== Test: Validate Hierarchical Relationships ===")
    
    state = create_sample_state()
    result = validate_hierarchical_relationships(state)
    
    assert "status" in result
    assert "issues" in result
    
    print(f"  Status: {result['status']}")
    print(f"  Issues found: {len(result['issues'])}")
    print("✓ Hierarchical relationship validation completed")


def test_verify_paper_counts():
    """Test paper count verification."""
    print("\n=== Test: Verify Paper Counts ===")
    
    state = create_sample_state()
    result = verify_paper_counts(state)
    
    assert "papers_dict" in result
    assert "papers_pending" in result
    assert "papers_completed" in result
    assert "papers_failed" in result
    assert "consistent" in result
    
    print(f"  Papers dict: {result['papers_dict']}")
    print(f"  Queue total: {result['queue_total']}")
    print(f"  Consistent: {result['consistent']}")
    if not result['consistent']:
        print(f"  Issues: {result['issues']}")
    print("✓ Paper count verification completed")


def test_check_orphaned_records():
    """Test orphaned records check."""
    print("\n=== Test: Check Orphaned Records ===")
    
    state = create_sample_state()
    result = check_orphaned_records(state)
    
    assert "has_orphaned_records" in result
    assert "orphaned_chunks" in result
    assert "total_orphaned" in result
    
    print(f"  Has orphaned records: {result['has_orphaned_records']}")
    print(f"  Total orphaned: {result['total_orphaned']}")
    print("✓ Orphaned records check completed")


def test_validate_timestamp_sequences():
    """Test timestamp sequence validation."""
    print("\n=== Test: Validate Timestamp Sequences ===")
    
    state = create_sample_state()
    result = validate_timestamp_sequences(state)
    
    assert "valid" in result
    assert "issues" in result
    
    print(f"  Valid: {result['valid']}")
    print(f"  Issues: {len(result['issues'])}")
    print("✓ Timestamp sequence validation completed")


# =============================================================================
# Test Step 14.5: QC Report Generation
# =============================================================================

def test_generate_qc_report():
    """Test comprehensive QC report generation."""
    print("\n=== Test: Generate QC Report ===")
    
    state = create_sample_state()
    report = generate_qc_report(state)
    
    assert "generated_at" in report
    assert "corpus_info" in report
    assert "dashboard" in report
    assert "data_quality" in report
    assert "error_analysis" in report
    assert "consistency_validation" in report
    assert "recommendations" in report
    
    print(f"  Generated at: {report['generated_at']}")
    print(f"  Total papers: {report['corpus_info']['total_papers']}")
    print(f"  Recommendations: {len(report['recommendations'])}")
    print("✓ QC report generated successfully")


def test_export_report_markdown():
    """Test Markdown report export."""
    print("\n=== Test: Export Report as Markdown ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        state = create_sample_state()
        output_path = str(Path(tmpdir) / "qc_report.md")
        
        result_path = export_report_markdown(state, output_path)
        
        assert Path(result_path).exists()
        
        # Read and check content
        with open(result_path, 'r') as f:
            content = f.read()
        
        assert "# Quality Control Report" in content
        assert "## Corpus Overview" in content
        assert "## Recommendations" in content
        
        print(f"  Report exported to: {result_path}")
        print(f"  Report size: {len(content)} characters")
        print("✓ Markdown report export completed")


def test_export_report_html():
    """Test HTML report export."""
    print("\n=== Test: Export Report as HTML ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        state = create_sample_state()
        output_path = str(Path(tmpdir) / "qc_report.html")
        
        result_path = export_report_html(state, output_path)
        
        assert Path(result_path).exists()
        
        # Read and check content
        with open(result_path, 'r') as f:
            content = f.read()
        
        assert "<!DOCTYPE html>" in content
        assert "<title>Quality Control Report</title>" in content
        assert "<h1>Quality Control Report</h1>" in content
        
        print(f"  Report exported to: {result_path}")
        print(f"  Report size: {len(content)} characters")
        print("✓ HTML report export completed")


# =============================================================================
# Integration Tests
# =============================================================================

def test_full_qc_workflow():
    """Test complete QC workflow."""
    print("\n=== Test: Full QC Workflow ===")
    
    state = create_sample_state()
    
    # Run dashboard checks
    dashboard = create_qc_dashboard(state)
    stats = dashboard.get_overall_statistics()
    print(f"  1. Dashboard created - {stats['total_papers']} papers")
    
    # Run data quality checks
    pdf_check = verify_pdfs_processed(state)
    metadata_check = check_missing_metadata(state)
    print(f"  2. Data quality checks - {pdf_check['success_rate']:.1f}% success rate")
    
    # Run error analysis
    failed = list_failed_papers(state)
    errors = categorize_error_types(state)
    print(f"  3. Error analysis - {errors['total_failures']} failures")
    
    # Run consistency validation
    taxonomy_check = check_taxonomy_consistency(state)
    counts_check = verify_paper_counts(state)
    print(f"  4. Consistency validation - taxonomy {taxonomy_check['status']}")
    
    # Generate report
    report = generate_qc_report(state)
    print(f"  5. Report generated - {len(report['recommendations'])} recommendations")
    
    print("✓ Full QC workflow completed successfully")


# =============================================================================
# Main Test Runner
# =============================================================================

def run_all_tests():
    """Run all Phase 14 tests."""
    print("=" * 70)
    print("PHASE 14: QUALITY CONTROL AND VALIDATION - TEST SUITE")
    print("=" * 70)
    
    tests = [
        # Step 14.1: QC Dashboard
        ("14.1.1", test_qc_dashboard_creation),
        ("14.1.2", test_get_overall_statistics),
        ("14.1.3", test_get_status_distribution),
        ("14.1.4", test_get_failed_papers),
        ("14.1.5", test_get_quality_score_distribution),
        ("14.1.6", test_get_topic_distribution),
        ("14.1.7", test_display_qc_statistics),
        
        # Step 14.2: Data Quality Checks
        ("14.2.1", test_verify_pdfs_processed),
        ("14.2.2", test_check_missing_metadata),
        ("14.2.3", test_validate_embedding_integrity),
        ("14.2.4", test_check_summary_completeness),
        ("14.2.5", test_verify_topic_assignments),
        
        # Step 14.3: Error Analysis
        ("14.3.1", test_list_failed_papers),
        ("14.3.2", test_categorize_error_types),
        ("14.3.3", test_suggest_remediation),
        ("14.3.4", test_export_error_log),
        
        # Step 14.4: Consistency Validation
        ("14.4.1", test_check_taxonomy_consistency),
        ("14.4.2", test_validate_hierarchical_relationships),
        ("14.4.3", test_verify_paper_counts),
        ("14.4.4", test_check_orphaned_records),
        ("14.4.5", test_validate_timestamp_sequences),
        
        # Step 14.5: QC Report Generation
        ("14.5.1", test_generate_qc_report),
        ("14.5.2", test_export_report_markdown),
        ("14.5.3", test_export_report_html),
        
        # Integration
        ("14.6", test_full_qc_workflow),
    ]
    
    passed = 0
    failed = 0
    
    for test_id, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ Test {test_id} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test {test_id} ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
