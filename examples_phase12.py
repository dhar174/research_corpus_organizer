#!/usr/bin/env python3
"""
Phase 12 Usage Examples: Final CSV/Parquet Export

This file demonstrates how to use Phase 12 export functionality for various use cases.

Examples include:
- Final data export with complete metadata
- Export variants (full, summary, JSON)
- Statistics and quality reports
- Artifact management
- Google Drive integration
- Complete export pipeline

All examples use mock data for demonstration purposes.
In production, these would be called after all processing phases are complete.
"""

import sys
from pathlib import Path
from datetime import datetime, date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    PaperRecord,
    TopicNode,
    TopicHierarchy,
    StateManager,
    create_default_config,
)

from export_manager import (
    # Step 12.1
    export_final_data,
    create_final_export_config,
    
    # Step 12.2
    export_full_csv,
    export_summary_csv,
    export_to_json,
    export_taxonomy_to_json,
    
    # Step 12.3
    generate_statistics_report,
    count_papers_by_status,
    count_papers_by_topic,
    generate_quality_report,
    display_export_summary,
    
    # Step 12.4
    save_all_artifacts,
    save_error_logs,
    save_processing_logs,
)


# =============================================================================
# Helper Functions
# =============================================================================

def create_sample_state_with_taxonomy():
    """Create a complete sample state with papers and taxonomy."""
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    # Create 50 sample papers
    for i in range(50):
        paper_id = f"paper_{i:03d}"
        
        # Vary status
        if i < 40:
            status = "classified"
        elif i < 45:
            status = "summarized"
        elif i < 48:
            status = "failed"
        else:
            status = "pending"
        
        paper = PaperRecord(
            id=paper_id,
            file_path=f"/content/drive/MyDrive/PDFs/paper_{i}.pdf",
            filename=f"paper_{i}.pdf",
            arxiv_id=f"2024.{i:05d}" if i % 3 == 0 else None,
            doi=f"10.1000/test.{i}" if i % 2 == 0 else None,
            title=f"Research Paper {i}: {['Deep Learning', 'NLP', 'Computer Vision', 'Robotics', 'Reinforcement Learning'][i % 5]}",
            authors=[f"Author {j}" for j in range((i % 4) + 1)],
            venue=["ICML", "NeurIPS", "CVPR", "ICLR", "AAAI"][i % 5],
            publish_date=date(2024, (i % 12) + 1, (i % 28) + 1),
            year=2024,
            abstract_text=f"This paper presents novel approaches to {['deep learning', 'natural language processing', 'computer vision', 'robotics', 'reinforcement learning'][i % 5]}. " * 3,
            full_summary=f"Summary: This paper introduces innovative methods for {i}..." if i < 48 else None,
            deep_summary=f"Detailed analysis: The paper provides comprehensive coverage of {i}..." if i < 30 else None,
            initial_notes=f"Key insights: Novel approach, strong results, practical applications" if i < 48 else None,
            classification_notes=f"Classified as {['ML', 'NLP', 'CV', 'Robotics', 'RL'][i % 5]} based on content" if i < 40 else None,
            processing_status=status,
            error_reason="PDF parsing failed" if status == "failed" else None,
            error_stage="pdf_parsing" if status == "failed" else None,
            tier1_topic=f"T1_{i % 3}" if i < 40 else None,
            tier1_topic_name=["Machine Learning", "NLP", "Computer Vision"][i % 3] if i < 40 else None,
            tier1_confidence=0.85 + (i % 10) * 0.015 if i < 40 else None,
            tier2_topic=f"T2_{i % 5}" if i < 40 else None,
            tier2_topic_name=["Deep Learning", "Transformers", "CNNs", "GANs", "RL"][i % 5] if i < 40 else None,
            tier2_confidence=0.80 + (i % 15) * 0.01 if i < 40 else None,
            tier3_topic=f"T3_{i % 7}" if i < 40 else None,
            tier3_topic_name=["BERT", "GPT", "ResNet", "YOLO", "DQN", "PPO", "SAC"][i % 7] if i < 40 else None,
            tier3_confidence=0.75 + (i % 20) * 0.01 if i < 40 else None,
            taxonomy_version="v1.0" if i < 40 else None,
        )
        
        state = StateManager.add_paper(state, paper)
    
    # Create taxonomy
    taxonomy = TopicHierarchy(
        taxonomy_version="v1.0",
        created_at=datetime.now(),
        notes="Production taxonomy for research corpus",
        total_papers=40,
        clustering_method="kmeans",
        labeling_model="gpt-5-mini",
    )
    
    # Add topics
    for i in range(3):
        topic = TopicNode(
            id=f"T1_{i}",
            label=["Machine Learning", "NLP", "Computer Vision"][i],
            description=f"Broad research area covering {['ML', 'NLP', 'CV'][i]}",
            paper_ids=[f"paper_{j:03d}" for j in range(50) if j % 3 == i and j < 40],
        )
        taxonomy.add_topic(1, topic)
    
    state["topic_hierarchy"] = taxonomy
    state["taxonomy_approved"] = True
    
    # Add processing stats
    state["stats"] = {
        "total_processing_time": 7200,
        "total_cost": 45.75,
        "total_tokens": 1500000,
        "papers_processed": 50,
    }
    
    state["current_phase"] = "phase12_final_export"
    
    return state


# =============================================================================
# Example 1: Basic Final Export
# =============================================================================

def example_1_basic_final_export():
    """
    Example 1: Basic final data export.
    
    Export all papers with complete metadata to CSV and Parquet.
    """
    print("\n" + "=" * 70)
    print("Example 1: Basic Final Data Export")
    print("=" * 70)
    
    state = create_sample_state_with_taxonomy()
    
    # Export to /tmp for demonstration
    output_dir = "/tmp/rag_exports"
    
    # Export in both CSV and Parquet formats
    export_paths = export_final_data(
        state,
        output_dir=output_dir,
        base_filename="research_corpus_final",
        formats=["csv", "parquet"]
    )
    
    print("\n✅ Final export complete!")
    print(f"\nExported files:")
    for fmt, path in export_paths.items():
        print(f"  {fmt.upper():12} {path}")
    
    return export_paths


# =============================================================================
# Example 2: Export Variants
# =============================================================================

def example_2_export_variants():
    """
    Example 2: Create multiple export variants.
    
    Generate:
    - Full CSV with all fields
    - Summary CSV with key fields only
    - JSON export with hierarchical data
    - Taxonomy-only JSON
    """
    print("\n" + "=" * 70)
    print("Example 2: Export Variants")
    print("=" * 70)
    
    state = create_sample_state_with_taxonomy()
    output_dir = "/tmp/rag_exports"
    
    # 1. Full CSV
    full_csv = f"{output_dir}/corpus_full.csv"
    export_full_csv(state, full_csv)
    print(f"\n✅ Full CSV: {full_csv}")
    
    # 2. Summary CSV
    summary_csv = f"{output_dir}/corpus_summary.csv"
    export_summary_csv(state, summary_csv)
    print(f"✅ Summary CSV: {summary_csv}")
    
    # 3. Complete JSON (papers + taxonomy)
    full_json = f"{output_dir}/corpus_complete.json"
    export_to_json(state, full_json, include_taxonomy=True, include_papers=True)
    print(f"✅ Complete JSON: {full_json}")
    
    # 4. Taxonomy-only JSON
    taxonomy_json = f"{output_dir}/taxonomy.json"
    export_taxonomy_to_json(state, taxonomy_json)
    print(f"✅ Taxonomy JSON: {taxonomy_json}")
    
    print("\n✅ All export variants created!")


# =============================================================================
# Example 3: Statistics and Quality Reports
# =============================================================================

def example_3_statistics_and_quality():
    """
    Example 3: Generate statistics and quality reports.
    
    Demonstrates:
    - Counting papers by status
    - Counting papers by topic
    - Generating comprehensive statistics
    - Quality assessment
    """
    print("\n" + "=" * 70)
    print("Example 3: Statistics and Quality Reports")
    print("=" * 70)
    
    state = create_sample_state_with_taxonomy()
    papers = state["papers"]
    
    # 1. Count by status
    print("\n1. Papers by Status:")
    status_counts = count_papers_by_status(papers)
    for status, count in sorted(status_counts.items()):
        pct = count / len(papers) * 100
        print(f"   {status:15} {count:3} ({pct:5.1f}%)")
    
    # 2. Count by topic (all tiers)
    for tier in [1, 2, 3]:
        print(f"\n2.{tier}. Papers by Tier {tier} Topic:")
        tier_counts = count_papers_by_topic(papers, tier=tier)
        sorted_topics = sorted(tier_counts.items(), key=lambda x: x[1], reverse=True)
        for topic, count in sorted_topics[:5]:  # Top 5
            pct = count / len(papers) * 100
            print(f"   {topic:30} {count:3} ({pct:5.1f}%)")
    
    # 3. Full statistics report
    print("\n3. Comprehensive Statistics Report:")
    stats = generate_statistics_report(state)
    print(f"   Total papers: {stats['total_papers']}")
    print(f"   With summaries: {stats['summaries']['with_full_summary']}")
    print(f"   With deep analysis: {stats['summaries']['with_deep_summary']}")
    print(f"   Fully classified: {stats['classification']['fully_classified']}")
    print(f"   Failed papers: {stats['errors']['failed_papers']}")
    
    # 4. Quality report
    print("\n4. Quality Assessment:")
    quality = generate_quality_report(state)
    print(f"   Overall quality score: {quality['overall_quality_score']:.1%}")
    print(f"   Metadata completeness:")
    for metric, value in quality['quality_metrics'].items():
        print(f"     {metric:25} {value:.1%}")
    
    if quality.get('issues'):
        print(f"\n   Issues found: {len(quality['issues'])}")
        for issue in quality['issues']:
            print(f"     ⚠️  {issue}")
    
    print("\n✅ Statistics and quality reports generated!")


# =============================================================================
# Example 4: Save All Artifacts
# =============================================================================

def example_4_save_all_artifacts():
    """
    Example 4: Save all artifacts from the pipeline.
    
    Saves:
    - Master CSV and Parquet
    - Taxonomy JSON
    - Error logs
    - Processing logs
    - Statistics reports
    - Quality reports
    """
    print("\n" + "=" * 70)
    print("Example 4: Save All Artifacts")
    print("=" * 70)
    
    state = create_sample_state_with_taxonomy()
    
    # Save all artifacts
    artifact_paths = save_all_artifacts(
        state,
        output_dir="/tmp/rag_artifacts",
        base_filename="research_corpus",
        save_faiss=False,  # Would save FAISS if index exists
        save_taxonomy=True,
        save_logs=True
    )
    
    print("\n✅ All artifacts saved!")
    print(f"\nArtifact Summary ({len(artifact_paths)} files):")
    for name, path in sorted(artifact_paths.items()):
        print(f"  {name:25} {path}")
    
    return artifact_paths


# =============================================================================
# Example 5: Export with Display Summary
# =============================================================================

def example_5_export_with_summary():
    """
    Example 5: Export data and display comprehensive summary.
    
    Combines export with detailed summary display.
    """
    print("\n" + "=" * 70)
    print("Example 5: Export with Display Summary")
    print("=" * 70)
    
    state = create_sample_state_with_taxonomy()
    
    # Export data
    export_paths = export_final_data(
        state,
        output_dir="/tmp/rag_exports",
        base_filename="corpus",
        formats=["csv", "parquet"]
    )
    
    # Display comprehensive summary
    summary = display_export_summary(state, export_paths, verbose=True)
    
    print("\n✅ Export with summary complete!")


# =============================================================================
# Example 6: Custom Key Fields Export
# =============================================================================

def example_6_custom_summary_csv():
    """
    Example 6: Export summary CSV with custom key fields.
    
    Demonstrates selecting specific fields for export.
    """
    print("\n" + "=" * 70)
    print("Example 6: Custom Summary CSV")
    print("=" * 70)
    
    state = create_sample_state_with_taxonomy()
    
    # Define custom key fields
    custom_fields = {
        "id",
        "title",
        "authors",
        "year",
        "full_summary",
        "tier1_topic_name",
        "tier2_topic_name",
        "processing_status",
    }
    
    output_path = "/tmp/rag_exports/corpus_custom.csv"
    export_summary_csv(state, output_path, key_fields=custom_fields)
    
    print(f"\n✅ Custom summary CSV created: {output_path}")
    print(f"Fields included: {len(custom_fields)}")


# =============================================================================
# Example 7: Complete Pipeline Integration
# =============================================================================

def example_7_complete_pipeline():
    """
    Example 7: Complete export pipeline integration.
    
    This is what you would call at the end of the full RAG pipeline.
    """
    print("\n" + "=" * 70)
    print("Example 7: Complete Pipeline Integration")
    print("=" * 70)
    
    # Simulate end of pipeline
    state = create_sample_state_with_taxonomy()
    state["current_phase"] = "phase12_final_export"
    
    # Define output directory (in production, this would be Google Drive)
    output_dir = "/tmp/rag_final_output"
    
    print("\n1. Saving all artifacts...")
    artifact_paths = save_all_artifacts(
        state,
        output_dir=output_dir,
        base_filename="rag_research_corpus",
        save_faiss=True,  # Save FAISS if available
        save_taxonomy=True,
        save_logs=True
    )
    
    print("\n2. Generating final reports...")
    stats = generate_statistics_report(state)
    quality = generate_quality_report(state)
    
    print("\n3. Displaying summary...")
    summary = display_export_summary(state, artifact_paths, verbose=True)
    
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE!")
    print("=" * 70)
    print(f"\nAll artifacts saved to: {output_dir}")
    print(f"Total files: {len(artifact_paths)}")
    print(f"Papers processed: {len(state['papers'])}")
    print(f"Quality score: {quality['overall_quality_score']:.1%}")
    print("\n✅ Ready for analysis and querying!")
    
    return artifact_paths


# =============================================================================
# Main Runner
# =============================================================================

def run_all_examples():
    """Run all Phase 12 examples."""
    print("\n" + "=" * 70)
    print("PHASE 12 EXAMPLES")
    print("Final CSV/Parquet Export")
    print("=" * 70)
    
    examples = [
        ("Example 1", example_1_basic_final_export),
        ("Example 2", example_2_export_variants),
        ("Example 3", example_3_statistics_and_quality),
        ("Example 4", example_4_save_all_artifacts),
        ("Example 5", example_5_export_with_summary),
        ("Example 6", example_6_custom_summary_csv),
        ("Example 7", example_7_complete_pipeline),
    ]
    
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_examples()
