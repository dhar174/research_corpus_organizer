#!/usr/bin/env python3
"""
Examples for Phase 14: Quality Control and Validation

This module demonstrates how to use the quality control and validation
functionality implemented in quality_control.py.

Usage:
    python examples_phase14.py
"""

import sys
from pathlib import Path
from datetime import datetime, date

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
    # QC Dashboard
    create_qc_dashboard,
    display_qc_statistics,
    
    # Data Quality Checks
    verify_pdfs_processed,
    check_missing_metadata,
    validate_embedding_integrity,
    check_summary_completeness,
    verify_topic_assignments,
    
    # Error Analysis
    list_failed_papers,
    categorize_error_types,
    suggest_remediation,
    export_error_log,
    
    # Consistency Validation
    check_taxonomy_consistency,
    validate_hierarchical_relationships,
    verify_paper_counts,
    check_orphaned_records,
    validate_timestamp_sequences,
    
    # QC Report Generation
    generate_qc_report,
    export_report_markdown,
    export_report_html,
)


def create_example_state():
    """Create an example state for demonstration."""
    config = create_default_config()
    
    # Create sample papers
    papers = {
        "paper1": PaperRecord(
            id="paper1",
            file_path="/path/to/paper1.pdf",
            filename="paper1.pdf",
            processing_status="classified",
            title="Deep Learning for Computer Vision",
            authors=["John Doe", "Jane Smith"],
            publish_date=date(2024, 1, 15),
            full_summary="This paper explores deep learning techniques for computer vision tasks.",
            tier1_topic="ml",
            tier1_topic_name="Machine Learning",
            tier1_confidence=0.92,
            tier2_topic="dl",
            tier2_topic_name="Deep Learning",
            tier2_confidence=0.88,
        ),
        "paper2": PaperRecord(
            id="paper2",
            file_path="/path/to/paper2.pdf",
            filename="paper2.pdf",
            processing_status="classified",
            title="Natural Language Processing with Transformers",
            authors=["Alice Johnson"],
            publish_date=date(2024, 2, 10),
            full_summary="A comprehensive study of transformer models in NLP.",
            tier1_topic="ml",
            tier1_topic_name="Machine Learning",
            tier1_confidence=0.95,
            tier2_topic="nlp",
            tier2_topic_name="Natural Language Processing",
            tier2_confidence=0.90,
        ),
        "paper3": PaperRecord(
            id="paper3",
            file_path="/path/to/paper3.pdf",
            filename="paper3.pdf",
            processing_status="summarized",
            title="Quantum Computing Algorithms",
            authors=["Bob Wilson"],
            full_summary="This paper presents novel quantum computing algorithms.",
        ),
        "paper4": PaperRecord(
            id="paper4",
            file_path="/path/to/paper4.pdf",
            filename="paper4.pdf",
            processing_status="failed",
            error_stage="parsing",
            error_reason="PDF parsing failed: corrupted file",
            retry_count=2,
        ),
        "paper5": PaperRecord(
            id="paper5",
            file_path="/path/to/paper5.pdf",
            filename="paper5.pdf",
            processing_status="pending",
        ),
    }
    
    # Create chunks
    chunks = {
        "paper1": [
            PaperChunk(
                paper_id="paper1",
                chunk_id="paper1_chunk_0",
                section_label="abstract",
                text="Abstract text...",
            ),
            PaperChunk(
                paper_id="paper1",
                chunk_id="paper1_chunk_1",
                section_label="introduction",
                text="Introduction text...",
            ),
        ],
        "paper2": [
            PaperChunk(
                paper_id="paper2",
                chunk_id="paper2_chunk_0",
                section_label="abstract",
                text="Abstract text...",
            ),
        ],
    }
    
    # Create taxonomy
    taxonomy = TopicHierarchy(
        taxonomy_version="1.0",
        total_papers=2,
        tier1=[
            TopicNode(
                id="ml",
                name="Machine Learning",
                tier=1,
                paper_count=2,
            ),
        ],
        tier2=[
            TopicNode(
                id="dl",
                name="Deep Learning",
                tier=2,
                parent_id="ml",
                paper_count=1,
            ),
            TopicNode(
                id="nlp",
                name="Natural Language Processing",
                tier=2,
                parent_id="ml",
                paper_count=1,
            ),
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
        "papers_pending": ["paper5"],
        "papers_completed": ["paper1", "paper2"],
        "papers_failed": ["paper4"],
        "errors": [],
        "stats": {},
    }
    
    return state


def example_1_qc_dashboard():
    """Example 1: Using the QC Dashboard."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: QC Dashboard")
    print("=" * 70)
    
    state = create_example_state()
    
    # Create and use dashboard
    print("\n1. Creating QC Dashboard...")
    dashboard = create_qc_dashboard(state)
    
    print("\n2. Getting overall statistics...")
    stats = dashboard.get_overall_statistics()
    print(f"   Total papers: {stats['total_papers']}")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Status counts: {stats['status_counts']}")
    
    print("\n3. Displaying full QC statistics...")
    display = display_qc_statistics(state)
    print(display)


def example_2_data_quality_checks():
    """Example 2: Running data quality checks."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Data Quality Checks")
    print("=" * 70)
    
    state = create_example_state()
    
    print("\n1. Verifying PDFs processed...")
    pdf_result = verify_pdfs_processed(state)
    print(f"   Processed: {pdf_result['processed']} / {pdf_result['total_papers']}")
    print(f"   Success rate: {pdf_result['success_rate']:.1f}%")
    print(f"   Pending: {pdf_result['pending']}")
    print(f"   Failed: {pdf_result['failed']}")
    
    print("\n2. Checking missing metadata...")
    metadata_result = check_missing_metadata(state)
    print(f"   Missing counts:")
    for field, count in metadata_result['missing_counts'].items():
        print(f"     - {field}: {count}")
    
    print("\n3. Validating embedding integrity...")
    embed_result = validate_embedding_integrity(state)
    print(f"   Total chunks: {embed_result['total_chunks']}")
    print(f"   Status: {embed_result['integrity_status']}")
    
    print("\n4. Checking summary completeness...")
    summary_result = check_summary_completeness(state)
    print(f"   Papers needing summary: {summary_result['papers_needing_summary']}")
    print(f"   With summary: {summary_result['with_summary']}")
    print(f"   Completeness: {summary_result['completeness_rate']:.1f}%")
    
    print("\n5. Verifying topic assignments...")
    topic_result = verify_topic_assignments(state)
    print(f"   Papers needing classification: {topic_result['papers_needing_classification']}")
    print(f"   With Tier 1: {topic_result['with_tier1']}")
    print(f"   Classification rate: {topic_result['classification_rate']:.1f}%")


def example_3_error_analysis():
    """Example 3: Analyzing errors."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Error Analysis")
    print("=" * 70)
    
    state = create_example_state()
    
    print("\n1. Listing failed papers...")
    failed = list_failed_papers(state)
    print(f"   Total failed: {len(failed)}")
    for paper in failed:
        print(f"   - {paper['filename']}")
        print(f"     Stage: {paper['error_stage']}")
        print(f"     Reason: {paper['error_reason']}")
        print(f"     Retries: {paper['retry_count']}")
    
    print("\n2. Categorizing errors...")
    categories = categorize_error_types(state)
    print(f"   Total failures: {categories['total_failures']}")
    print(f"   By stage: {categories['by_stage']}")
    print(f"   By type: {categories['by_type']}")
    
    print("\n3. Getting remediation suggestions...")
    suggestions = suggest_remediation(state)
    print(f"   Suggestions for {len(suggestions)} error types:")
    for error_type, steps in suggestions.items():
        print(f"\n   {error_type}:")
        for step in steps[:3]:  # Show first 3 suggestions
            print(f"     - {step}")
    
    print("\n4. Exporting error log...")
    log_path = export_error_log(state, "/tmp/error_log_example.txt")
    print(f"   Error log saved to: {log_path}")


def example_4_consistency_validation():
    """Example 4: Validating consistency."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Consistency Validation")
    print("=" * 70)
    
    state = create_example_state()
    
    print("\n1. Checking taxonomy consistency...")
    taxonomy_result = check_taxonomy_consistency(state)
    print(f"   Status: {taxonomy_result['status']}")
    if 'validation_result' in taxonomy_result:
        print(f"   Valid: {taxonomy_result['validation_result']['valid']}")
        print(f"   Tier 1 topics: {taxonomy_result['validation_result']['tier1_count']}")
        print(f"   Tier 2 topics: {taxonomy_result['validation_result']['tier2_count']}")
    
    print("\n2. Validating hierarchical relationships...")
    hierarchy_result = validate_hierarchical_relationships(state)
    print(f"   Status: {hierarchy_result['status']}")
    print(f"   Issues found: {hierarchy_result['issues_count']}")
    if hierarchy_result['issues']:
        for issue in hierarchy_result['issues'][:3]:  # Show first 3
            print(f"     - {issue}")
    
    print("\n3. Verifying paper counts...")
    counts_result = verify_paper_counts(state)
    print(f"   Consistent: {counts_result['consistent']}")
    print(f"   Papers dict: {counts_result['papers_dict']}")
    print(f"   Queue total: {counts_result['queue_total']}")
    if counts_result['issues']:
        print(f"   Issues:")
        for issue in counts_result['issues']:
            print(f"     - {issue}")
    
    print("\n4. Checking orphaned records...")
    orphaned_result = check_orphaned_records(state)
    print(f"   Has orphaned: {orphaned_result['has_orphaned_records']}")
    print(f"   Total orphaned: {orphaned_result['total_orphaned']}")
    
    print("\n5. Validating timestamps...")
    timestamp_result = validate_timestamp_sequences(state)
    print(f"   Valid: {timestamp_result['valid']}")
    print(f"   Issues: {timestamp_result['issues_count']}")


def example_5_qc_report_generation():
    """Example 5: Generating QC reports."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: QC Report Generation")
    print("=" * 70)
    
    state = create_example_state()
    
    print("\n1. Generating comprehensive QC report...")
    report = generate_qc_report(state)
    print(f"   Generated at: {report['generated_at']}")
    print(f"   Total papers: {report['corpus_info']['total_papers']}")
    print(f"   Current phase: {report['corpus_info']['current_phase']}")
    
    print("\n2. Recommendations:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    print("\n3. Exporting report as Markdown...")
    md_path = export_report_markdown(state, "/tmp/qc_report_example.md")
    print(f"   Markdown report saved to: {md_path}")
    
    print("\n4. Exporting report as HTML...")
    html_path = export_report_html(state, "/tmp/qc_report_example.html")
    print(f"   HTML report saved to: {html_path}")
    
    print("\n5. Report sections included:")
    for section in report.keys():
        if section not in ['generated_at']:
            print(f"   - {section}")


def example_6_complete_workflow():
    """Example 6: Complete QC workflow."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Complete QC Workflow")
    print("=" * 70)
    
    state = create_example_state()
    
    print("\n=== Step 1: Dashboard Overview ===")
    dashboard = create_qc_dashboard(state)
    stats = dashboard.get_overall_statistics()
    print(f"Total papers: {stats['total_papers']}")
    print(f"Processing complete: {stats['status_counts'].get('classified', 0)} papers")
    
    print("\n=== Step 2: Data Quality Assessment ===")
    pdf_check = verify_pdfs_processed(state)
    print(f"Success rate: {pdf_check['success_rate']:.1f}%")
    
    metadata_check = check_missing_metadata(state)
    missing_total = sum(metadata_check['missing_counts'].values())
    print(f"Missing metadata fields: {missing_total}")
    
    print("\n=== Step 3: Error Analysis ===")
    failed = list_failed_papers(state)
    print(f"Failed papers: {len(failed)}")
    
    if failed:
        categories = categorize_error_types(state)
        print(f"Error types: {list(categories['by_type'].keys())}")
        
        suggestions = suggest_remediation(state)
        print(f"Remediation available for: {list(suggestions.keys())}")
    
    print("\n=== Step 4: Consistency Validation ===")
    taxonomy_check = check_taxonomy_consistency(state)
    print(f"Taxonomy status: {taxonomy_check['status']}")
    
    counts_check = verify_paper_counts(state)
    print(f"Paper counts consistent: {counts_check['consistent']}")
    
    orphaned_check = check_orphaned_records(state)
    print(f"Orphaned records: {orphaned_check['total_orphaned']}")
    
    print("\n=== Step 5: Report Generation ===")
    report = generate_qc_report(state)
    print(f"Full report generated with {len(report.keys())} sections")
    print(f"Recommendations: {len(report['recommendations'])}")
    
    # Export reports
    md_path = export_report_markdown(state, "/tmp/qc_workflow_report.md")
    html_path = export_report_html(state, "/tmp/qc_workflow_report.html")
    print(f"\nReports exported:")
    print(f"  - Markdown: {md_path}")
    print(f"  - HTML: {html_path}")
    
    print("\n=== QC Workflow Complete ===")
    print("All quality control checks passed!")


def main():
    """Run all examples."""
    print("=" * 70)
    print("PHASE 14: QUALITY CONTROL AND VALIDATION - EXAMPLES")
    print("=" * 70)
    
    examples = [
        example_1_qc_dashboard,
        example_2_data_quality_checks,
        example_3_error_analysis,
        example_4_consistency_validation,
        example_5_qc_report_generation,
        example_6_complete_workflow,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n✗ Example failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("EXAMPLES COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
