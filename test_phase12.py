#!/usr/bin/env python3
"""
Test suite for Phase 12: Final CSV/Parquet Export

Tests all functionality in export_manager.py Phase 12 additions:
- Final data export with complete metadata
- Export variants (full, summary, JSON)
- Statistics and quality reports
- Artifact management
- GraphState updates

This test suite ensures comprehensive export functionality.
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
    TopicNode,
    TopicHierarchy,
    StateManager,
    create_default_config,
)

from export_manager import (
    # Phase 12 - Step 12.1
    export_final_data,
    create_final_export_config,
    
    # Phase 12 - Step 12.2
    export_full_csv,
    export_summary_csv,
    export_to_json,
    export_taxonomy_to_json,
    
    # Phase 12 - Step 12.3
    generate_statistics_report,
    count_papers_by_status,
    count_papers_by_topic,
    generate_quality_report,
    display_export_summary,
    
    # Phase 12 - Step 12.4
    save_all_artifacts,
    save_error_logs,
    save_processing_logs,
    update_state_with_paths,
)


# =============================================================================
# Helper Functions
# =============================================================================

def create_sample_papers(count=20):
    """Create sample papers with varied processing states."""
    papers = {}
    
    for i in range(count):
        paper_id = f"paper_{i:03d}"
        
        # Vary processing status
        if i < 15:
            status = "classified"
        elif i < 18:
            status = "summarized"
        elif i < 19:
            status = "failed"
        else:
            status = "pending"
        
        paper = PaperRecord(
            id=paper_id,
            file_path=f"/drive/pdfs/paper_{i}.pdf",
            filename=f"paper_{i}.pdf",
            arxiv_id=f"2024.{i:05d}" if i % 3 == 0 else None,
            doi=f"10.1000/test.{i}" if i % 2 == 0 else None,
            title=f"Sample Research Paper {i}: Novel Approaches to Problem {i % 5}",
            authors=["Alice Smith", "Bob Jones", "Charlie Brown"],
            venue="International Conference on Research 2025",
            publish_date=date(2025, 1, 1 + (i % 28)),
            year=2025,
            abstract_text=f"This is the abstract for paper {i}. " * 5,
            full_summary=f"Summary of paper {i}: Novel approaches..." if i < 18 else None,
            deep_summary=f"Deep analysis of paper {i}..." if i < 10 else None,
            initial_notes=f"Key insights from paper {i}" if i < 18 else None,
            classification_notes=f"Classification reasoning for paper {i}" if i < 15 else None,
            processing_status=status,
            error_reason="Parsing error" if status == "failed" else None,
            error_stage="pdf_parsing" if status == "failed" else None,
            tier1_topic=f"T1_{i % 3}" if i < 15 else None,
            tier1_topic_name=["Machine Learning", "NLP", "Computer Vision"][i % 3] if i < 15 else None,
            tier1_confidence=0.85 + (i % 10) * 0.01 if i < 15 else None,
            tier2_topic=f"T2_{i % 5}" if i < 15 else None,
            tier2_topic_name=["Deep Learning", "Transformers", "CNNs", "GANs", "RL"][i % 5] if i < 15 else None,
            tier2_confidence=0.80 + (i % 15) * 0.01 if i < 15 else None,
            tier3_topic=f"T3_{i % 7}" if i < 15 else None,
            tier3_topic_name=["BERT", "GPT", "ResNet", "YOLO", "DQN", "PPO", "SAC"][i % 7] if i < 15 else None,
            tier3_confidence=0.75 + (i % 20) * 0.01 if i < 15 else None,
            taxonomy_version="v1.0" if i < 15 else None,
            retry_count=1 if status == "failed" else 0,
        )
        
        papers[paper_id] = paper
    
    return papers


def create_sample_taxonomy():
    """Create sample taxonomy."""
    taxonomy = TopicHierarchy(
        taxonomy_version="v1.0",
        created_at=datetime.now(),
        notes="Sample taxonomy for testing",
        total_papers=15,
        clustering_method="kmeans",
        labeling_model="gpt-5-mini",
    )
    
    # Add Tier 1 topics
    for i in range(3):
        topic = TopicNode(
            id=f"T1_{i}",
            label=["Machine Learning", "NLP", "Computer Vision"][i],
            description=f"Tier 1 topic {i}",
            paper_ids=[f"paper_{j:03d}" for j in range(20) if j % 3 == i and j < 15],
        )
        taxonomy.add_topic(1, topic)
    
    # Add Tier 2 topics
    for i in range(5):
        parent_id = f"T1_{i % 3}"
        topic = TopicNode(
            id=f"T2_{i}",
            label=["Deep Learning", "Transformers", "CNNs", "GANs", "RL"][i],
            description=f"Tier 2 topic {i}",
            paper_ids=[f"paper_{j:03d}" for j in range(20) if j % 5 == i and j < 15],
            parent_id=parent_id,
        )
        taxonomy.add_topic(2, topic)
    
    return taxonomy


def create_sample_state():
    """Create sample GraphState for testing."""
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    # Add sample papers
    papers = create_sample_papers(20)
    for paper_id, paper in papers.items():
        state = StateManager.add_paper(state, paper)
    
    # Add taxonomy
    state["topic_hierarchy"] = create_sample_taxonomy()
    state["taxonomy_approved"] = True
    
    # Add some processing stats
    state["stats"] = {
        "total_processing_time": 3600,
        "total_cost": 12.50,
        "total_tokens": 500000,
    }
    
    # Add some errors
    state["errors"] = [
        {
            "paper_id": "paper_018",
            "error": "Failed to parse PDF",
            "timestamp": datetime.now().isoformat(),
        }
    ]
    
    state["current_phase"] = "phase12_export"
    
    return state


# =============================================================================
# Test Step 12.1: Final Data Export
# =============================================================================

def test_create_final_export_config():
    """Test creating final export configuration."""
    print("\n" + "=" * 70)
    print("Test: Create Final Export Config")
    print("=" * 70)
    
    config = create_final_export_config()
    
    print(f"\nExport Config:")
    print(f"  Include fields: {config.include_fields}")
    print(f"  Exclude fields: {config.exclude_fields}")
    print(f"  Flatten nested: {config.flatten_nested}")
    print(f"  Include metadata: {config.include_metadata}")
    print(f"  Timestamp format: {config.timestamp_format}")
    
    assert config.include_fields is None, "Should include all fields"
    assert len(config.exclude_fields) == 0, "Should exclude no fields"
    assert config.flatten_nested is True
    assert config.include_metadata is True
    
    print("\n✅ Final export config created successfully")


def test_export_final_data():
    """Test final data export."""
    print("\n" + "=" * 70)
    print("Test: Export Final Data")
    print("=" * 70)
    
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = tmpdir
        
        # Export in CSV format
        export_paths = export_final_data(
            state,
            output_dir,
            base_filename="test_final",
            formats=["csv"]
        )
        
        print(f"\nExport paths:")
        for fmt, path in export_paths.items():
            print(f"  {fmt}: {path}")
            assert Path(path).exists(), f"Export file should exist: {path}"
        
        # Check CSV file
        csv_path = export_paths["csv"]
        assert Path(csv_path).exists()
        
        # Check metadata file
        metadata_path = export_paths.get("metadata")
        assert metadata_path and Path(metadata_path).exists()
        
        with open(metadata_path) as f:
            metadata = json.load(f)
            print(f"\nMetadata:")
            print(f"  Total papers: {metadata.get('total_papers')}")
            print(f"  Export type: {metadata.get('export_type')}")
        
        print("\n✅ Final data export successful")


# =============================================================================
# Test Step 12.2: Export Variants
# =============================================================================

def test_export_full_csv():
    """Test full CSV export."""
    print("\n" + "=" * 70)
    print("Test: Export Full CSV")
    print("=" * 70)
    
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "full.csv"
        
        result_path = export_full_csv(state, str(output_path))
        
        assert Path(result_path).exists()
        
        # Check file size
        size = Path(result_path).stat().st_size
        print(f"\nFull CSV exported: {result_path}")
        print(f"File size: {size / 1024:.1f} KB")
        
        print("\n✅ Full CSV export successful")


def test_export_summary_csv():
    """Test summary CSV export."""
    print("\n" + "=" * 70)
    print("Test: Export Summary CSV")
    print("=" * 70)
    
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "summary.csv"
        
        result_path = export_summary_csv(state, str(output_path))
        
        assert Path(result_path).exists()
        
        # Check file size (should be smaller than full CSV)
        size = Path(result_path).stat().st_size
        print(f"\nSummary CSV exported: {result_path}")
        print(f"File size: {size / 1024:.1f} KB")
        
        print("\n✅ Summary CSV export successful")


def test_export_to_json():
    """Test JSON export."""
    print("\n" + "=" * 70)
    print("Test: Export to JSON")
    print("=" * 70)
    
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "export.json"
        
        result_path = export_to_json(
            state,
            str(output_path),
            include_taxonomy=True,
            include_papers=True
        )
        
        assert Path(result_path).exists()
        
        # Load and verify JSON structure
        with open(result_path) as f:
            data = json.load(f)
        
        print(f"\nJSON export created: {result_path}")
        print(f"Keys in JSON: {list(data.keys())}")
        print(f"Number of papers: {len(data.get('papers', []))}")
        print(f"Taxonomy included: {'taxonomy' in data}")
        
        assert "export_metadata" in data
        assert "papers" in data
        assert "taxonomy" in data
        assert len(data["papers"]) == 20
        
        print("\n✅ JSON export successful")


def test_export_taxonomy_to_json():
    """Test taxonomy-only JSON export."""
    print("\n" + "=" * 70)
    print("Test: Export Taxonomy to JSON")
    print("=" * 70)
    
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "taxonomy.json"
        
        result_path = export_taxonomy_to_json(state, str(output_path))
        
        assert Path(result_path).exists()
        
        # Load and verify
        with open(result_path) as f:
            data = json.load(f)
        
        print(f"\nTaxonomy JSON created: {result_path}")
        print(f"Taxonomy version: {data.get('taxonomy_version')}")
        print(f"Tier 1 topics: {len(data.get('tier1', []))}")
        print(f"Tier 2 topics: {len(data.get('tier2', []))}")
        
        assert "taxonomy_version" in data
        assert "tier1" in data
        assert len(data["tier1"]) == 3
        
        print("\n✅ Taxonomy export successful")


# =============================================================================
# Test Step 12.3: Statistics and Quality Reports
# =============================================================================

def test_count_papers_by_status():
    """Test counting papers by status."""
    print("\n" + "=" * 70)
    print("Test: Count Papers by Status")
    print("=" * 70)
    
    papers = create_sample_papers(20)
    counts = count_papers_by_status(papers)
    
    print(f"\nStatus counts:")
    for status, count in sorted(counts.items()):
        print(f"  {status:15} {count}")
    
    assert "classified" in counts
    assert "summarized" in counts
    assert "failed" in counts
    assert counts["classified"] == 15
    assert counts["failed"] == 1
    
    print("\n✅ Status counting successful")


def test_count_papers_by_topic():
    """Test counting papers by topic."""
    print("\n" + "=" * 70)
    print("Test: Count Papers by Topic")
    print("=" * 70)
    
    papers = create_sample_papers(20)
    
    for tier in [1, 2, 3]:
        counts = count_papers_by_topic(papers, tier=tier)
        
        print(f"\nTier {tier} topic counts:")
        for topic, count in sorted(counts.items()):
            print(f"  {topic:20} {count}")
        
        assert len(counts) > 0, f"Should have topics in tier {tier}"
    
    print("\n✅ Topic counting successful")


def test_generate_statistics_report():
    """Test generating statistics report."""
    print("\n" + "=" * 70)
    print("Test: Generate Statistics Report")
    print("=" * 70)
    
    state = create_sample_state()
    report = generate_statistics_report(state)
    
    print(f"\nStatistics Report:")
    print(f"  Total papers: {report.get('total_papers')}")
    print(f"  Status distribution: {report.get('status_distribution')}")
    print(f"  With full summary: {report.get('summaries', {}).get('with_full_summary')}")
    print(f"  With classification: {report.get('classification', {}).get('tier1_classified')}")
    print(f"  Failed papers: {report.get('errors', {}).get('failed_papers')}")
    
    assert report["total_papers"] == 20
    assert "status_distribution" in report
    assert "topic_distribution" in report
    assert "summaries" in report
    assert "classification" in report
    assert "errors" in report
    
    print("\n✅ Statistics report generated successfully")


def test_generate_quality_report():
    """Test generating quality report."""
    print("\n" + "=" * 70)
    print("Test: Generate Quality Report")
    print("=" * 70)
    
    state = create_sample_state()
    report = generate_quality_report(state)
    
    print(f"\nQuality Report:")
    print(f"  Overall quality score: {report.get('overall_quality_score', 0):.1%}")
    print(f"  Quality metrics:")
    for metric, value in report.get("quality_metrics", {}).items():
        print(f"    {metric:25} {value:.1%}")
    
    if report.get("issues"):
        print(f"  Issues: {len(report['issues'])}")
        for issue in report["issues"]:
            print(f"    - {issue}")
    
    if report.get("warnings"):
        print(f"  Warnings: {len(report['warnings'])}")
        for warning in report["warnings"]:
            print(f"    - {warning}")
    
    assert "overall_quality_score" in report
    assert "quality_metrics" in report
    assert 0 <= report["overall_quality_score"] <= 1
    
    print("\n✅ Quality report generated successfully")


def test_display_export_summary():
    """Test displaying export summary."""
    print("\n" + "=" * 70)
    print("Test: Display Export Summary")
    print("=" * 70)
    
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some export files
        export_paths = export_final_data(
            state,
            tmpdir,
            base_filename="test",
            formats=["csv"]
        )
        
        # Display summary
        summary = display_export_summary(state, export_paths, verbose=True)
        
        print(f"\nSummary length: {len(summary)} characters")
        assert len(summary) > 0
        assert "EXPORT SUMMARY" in summary
        assert "Total Papers" in summary
        
        print("\n✅ Export summary displayed successfully")


# =============================================================================
# Test Step 12.4: Artifact Management
# =============================================================================

def test_save_error_logs():
    """Test saving error logs."""
    print("\n" + "=" * 70)
    print("Test: Save Error Logs")
    print("=" * 70)
    
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "errors.json"
        
        result_path = save_error_logs(state, str(output_path))
        
        assert Path(result_path).exists()
        
        # Load and verify
        with open(result_path) as f:
            error_log = json.load(f)
        
        print(f"\nError log created: {result_path}")
        print(f"Total errors: {error_log.get('total_errors')}")
        print(f"Errors recorded: {len(error_log.get('errors', []))}")
        
        assert "total_errors" in error_log
        assert "errors" in error_log
        assert error_log["total_errors"] > 0
        
        print("\n✅ Error logs saved successfully")


def test_save_processing_logs():
    """Test saving processing logs."""
    print("\n" + "=" * 70)
    print("Test: Save Processing Logs")
    print("=" * 70)
    
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "processing.json"
        
        result_path = save_processing_logs(state, str(output_path))
        
        assert Path(result_path).exists()
        
        # Load and verify
        with open(result_path) as f:
            log_data = json.load(f)
        
        print(f"\nProcessing log created: {result_path}")
        print(f"Current phase: {log_data.get('current_phase')}")
        print(f"Has statistics: {'statistics' in log_data}")
        print(f"Has quality report: {'quality' in log_data}")
        
        assert "timestamp" in log_data
        assert "statistics" in log_data
        assert "quality" in log_data
        
        print("\n✅ Processing logs saved successfully")


def test_update_state_with_paths():
    """Test updating state with artifact paths."""
    print("\n" + "=" * 70)
    print("Test: Update State with Paths")
    print("=" * 70)
    
    state = create_sample_state()
    
    artifact_paths = {
        "master_csv_path": "/tmp/master.csv",
        "faiss_index_path": "/tmp/faiss.index",
        "faiss_meta_path": "/tmp/faiss_meta.json",
        "taxonomy_json_path": "/tmp/taxonomy.json",
        "errors_log_path": "/tmp/errors.json",
    }
    
    updated_state = update_state_with_paths(state, artifact_paths)
    
    print(f"\nState updated with paths:")
    for key, value in artifact_paths.items():
        if key in updated_state:
            print(f"  {key}: {updated_state[key]}")
    
    assert updated_state["master_csv_path"] == artifact_paths["master_csv_path"]
    assert updated_state["faiss_index_path"] == artifact_paths["faiss_index_path"]
    assert "artifact_paths" in updated_state["stats"]
    
    print("\n✅ State updated successfully")


def test_save_all_artifacts():
    """Test saving all artifacts."""
    print("\n" + "=" * 70)
    print("Test: Save All Artifacts")
    print("=" * 70)
    
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = tmpdir
        
        # Save all artifacts
        artifact_paths = save_all_artifacts(
            state,
            output_dir,
            base_filename="test_corpus",
            save_faiss=False,  # Skip FAISS for this test
            save_taxonomy=True,
            save_logs=True
        )
        
        print(f"\nArtifacts saved ({len(artifact_paths)} files):")
        for name, path in artifact_paths.items():
            exists = "✓" if Path(path).exists() else "✗"
            print(f"  {exists} {name:25} {path}")
        
        # Verify key artifacts exist
        assert "master_csv_path" in artifact_paths
        assert "taxonomy_json_path" in artifact_paths
        assert "errors_log_path" in artifact_paths
        assert "processing_log_path" in artifact_paths
        assert "statistics" in artifact_paths
        assert "quality_report" in artifact_paths
        
        # Verify all files exist
        for path in artifact_paths.values():
            assert Path(path).exists(), f"Artifact should exist: {path}"
        
        print("\n✅ All artifacts saved successfully")


# =============================================================================
# Main Test Runner
# =============================================================================

def run_all_tests():
    """Run all Phase 12 tests."""
    print("\n" + "=" * 70)
    print("PHASE 12 TEST SUITE")
    print("Final CSV/Parquet Export")
    print("=" * 70)
    
    tests = [
        # Step 12.1: Final Data Export
        ("12.1.1", test_create_final_export_config),
        ("12.1.2", test_export_final_data),
        
        # Step 12.2: Export Variants
        ("12.2.1", test_export_full_csv),
        ("12.2.2", test_export_summary_csv),
        ("12.2.3", test_export_to_json),
        ("12.2.4", test_export_taxonomy_to_json),
        
        # Step 12.3: Statistics and Quality Reports
        ("12.3.1", test_count_papers_by_status),
        ("12.3.2", test_count_papers_by_topic),
        ("12.3.3", test_generate_statistics_report),
        ("12.3.4", test_generate_quality_report),
        ("12.3.5", test_display_export_summary),
        
        # Step 12.4: Artifact Management
        ("12.4.1", test_save_error_logs),
        ("12.4.2", test_save_processing_logs),
        ("12.4.3", test_update_state_with_paths),
        ("12.4.4", test_save_all_artifacts),
    ]
    
    passed = 0
    failed = 0
    
    for test_id, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ Test {test_id} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ Test {test_id} ERROR: {e}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {passed / len(tests) * 100:.1f}%")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
