#!/usr/bin/env python3
"""
Phase 7 Usage Examples: Initial CSV Export

This file demonstrates how to use the export module for various use cases.

Examples include:
- Basic CSV export
- Custom export configuration
- Export after summarization (Pass 1)
- Parquet export for large datasets
- Multi-format export
- Filtered export
- Export validation
- Export statistics
- Metadata generation
- Complete export pipeline

All examples use mock data for demonstration purposes.
"""

import sys
from pathlib import Path
import tempfile
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    PaperRecord,
    PaperChunk,
    StateManager,
    create_default_config,
)

from export_manager import (
    # Step 7.1
    export_papers_to_csv,
    export_papers_to_dict,
    flatten_paper_record,
    filter_papers_for_export,
    ExportConfig,
    
    # Step 7.2
    export_after_pass1,
    create_export_metadata,
    
    # Step 7.3
    export_papers_to_parquet,
    export_papers_compressed,
    
    # Step 7.4
    validate_export,
    export_summary_statistics,
)


# =============================================================================
# Helper Functions
# =============================================================================

def create_sample_papers(count=10):
    """Create sample papers for demonstration."""
    papers = {}
    
    for i in range(count):
        paper_id = f"paper_{i:03d}"
        
        paper = PaperRecord(
            id=paper_id,
            file_path=f"/drive/pdfs/paper_{i}.pdf",
            filename=f"paper_{i}.pdf",
            title=f"Sample Research Paper {i}",
            authors=["Alice Smith", "Bob Jones", "Charlie Brown"],
            venue="Sample Conference 2025",
            publish_date=datetime(2025, 1, 1 + i).date(),
            year=2025,
            abstract_text=f"This is the abstract for paper {i}. It describes the research problem and contributions.",
            full_summary=f"Summary of paper {i}: This paper presents novel approaches to solving problem X using method Y.",
            initial_notes=f"Key insights: 1) Novel approach 2) Good results 3) Practical applications",
            processing_status="summarized" if i < 8 else ("failed" if i == 8 else "pending"),
            error_reason="Parsing error" if i == 8 else None,
        )
        
        papers[paper_id] = paper
    
    return papers


def create_sample_state():
    """Create sample GraphState for demonstration."""
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    # Add sample papers
    papers = create_sample_papers(10)
    for paper_id, paper in papers.items():
        state = StateManager.add_paper(state, paper)
    
    # Add some stats
    state["stats"] = {
        "papers_summarized": 8,
        "papers_failed_summary": 1,
        "summarization_tokens": 50000,
        "summarization_cost_usd": 0.75,
    }
    
    return state


# =============================================================================
# Example 1: Basic CSV Export
# =============================================================================

def example_basic_csv_export():
    """Example: Basic CSV export of papers."""
    print("\n" + "=" * 70)
    print("Example 1: Basic CSV Export")
    print("=" * 70)
    
    # Create sample data
    papers = create_sample_papers(5)
    
    # Create temporary output path
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "papers.csv"
        
        print(f"\nExporting {len(papers)} papers to CSV...")
        
        # Export to CSV
        csv_path = export_papers_to_csv(
            papers=papers,
            output_path=str(output_path)
        )
        
        print(f"✅ Exported to: {csv_path}")
        
        # Check file
        file_size = Path(csv_path).stat().st_size
        print(f"   File size: {file_size} bytes ({file_size/1024:.1f} KB)")
        
        # Read and display first few lines
        with open(csv_path, 'r') as f:
            lines = f.readlines()
            print(f"   Rows: {len(lines) - 1} (excluding header)")
            print(f"\n   First row preview:")
            print(f"   {lines[0][:100]}...")
    
    print("\n💡 Tip: The CSV file includes all PaperRecord fields with nested data flattened.")


# =============================================================================
# Example 2: Custom Export Configuration
# =============================================================================

def example_custom_export_config():
    """Example: Customize export with ExportConfig."""
    print("\n" + "=" * 70)
    print("Example 2: Custom Export Configuration")
    print("=" * 70)
    
    papers = create_sample_papers(3)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Example 2a: Exclude error fields
        print("\n--- Configuration 1: Exclude error fields ---")
        
        config1 = ExportConfig(
            exclude_fields={"error_reason", "error_stage"},
            flatten_nested=True,
            include_metadata=True
        )
        
        output1 = Path(tmpdir) / "papers_no_errors.csv"
        export_papers_to_csv(papers, str(output1), config=config1)
        print(f"✅ Exported without error fields to: {output1.name}")
        
        # Example 2b: Only specific fields
        print("\n--- Configuration 2: Include only specific fields ---")
        
        config2 = ExportConfig(
            include_fields={"id", "title", "authors", "full_summary", "processing_status"},
            flatten_nested=True,
            include_metadata=False
        )
        
        output2 = Path(tmpdir) / "papers_minimal.csv"
        export_papers_to_csv(papers, str(output2), config=config2)
        print(f"✅ Exported minimal fields to: {output2.name}")
        
        # Example 2c: Custom timestamp format
        print("\n--- Configuration 3: Epoch timestamps ---")
        
        config3 = ExportConfig(
            timestamp_format="epoch",
            flatten_nested=True
        )
        
        output3 = Path(tmpdir) / "papers_epoch.csv"
        export_papers_to_csv(papers, str(output3), config=config3)
        print(f"✅ Exported with epoch timestamps to: {output3.name}")
    
    print("\n💡 Tip: Use ExportConfig to customize field selection and formatting.")


# =============================================================================
# Example 3: Export After Summarization (Pass 1)
# =============================================================================

def example_export_after_pass1():
    """Example: Export papers after Pass 1 with metadata."""
    print("\n" + "=" * 70)
    print("Example 3: Export After Summarization (Pass 1)")
    print("=" * 70)
    
    # Create sample state
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "papers_pass1.csv"
        
        print(f"\nBefore export:")
        print(f"  Total papers: {len(state['papers'])}")
        print(f"  Papers summarized: {state['stats']['papers_summarized']}")
        
        # Export after Pass 1
        state = export_after_pass1(
            state=state,
            output_path=str(output_path),
            include_partial=True,  # Include in-progress papers
            save_metadata=True     # Save metadata JSON
        )
        
        print(f"\n✅ Export complete!")
        print(f"   CSV path: {state['master_csv_path']}")
        
        # Check metadata
        if "export_metadata" in state["stats"]:
            metadata = state["stats"]["export_metadata"]
            print(f"\n📊 Export Metadata:")
            print(f"   Total papers: {metadata['total_papers']}")
            print(f"   With summaries: {metadata['with_summary']}")
            print(f"   With notes: {metadata['with_notes']}")
            print(f"   Status distribution: {metadata['status_distribution']}")
        
        # Check if metadata file was created
        metadata_file = Path(str(output_path).replace('.csv', '.metadata.json'))
        if metadata_file.exists():
            print(f"\n✅ Metadata file created: {metadata_file.name}")
    
    print("\n💡 Tip: export_after_pass1() is the recommended way to export after summarization.")


# =============================================================================
# Example 4: Parquet Export
# =============================================================================

def example_parquet_export():
    """Example: Export to Parquet format for large datasets."""
    print("\n" + "=" * 70)
    print("Example 4: Parquet Export")
    print("=" * 70)
    
    try:
        import pandas as pd
        
        papers = create_sample_papers(20)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Export to Parquet
            parquet_path = Path(tmpdir) / "papers.parquet"
            
            print(f"\nExporting {len(papers)} papers to Parquet...")
            
            result_path = export_papers_to_parquet(
                papers=papers,
                output_path=str(parquet_path),
                compression="snappy"
            )
            
            print(f"✅ Exported to: {parquet_path.name}")
            
            # Compare with CSV
            csv_path = Path(tmpdir) / "papers.csv"
            export_papers_to_csv(papers, str(csv_path))
            
            parquet_size = parquet_path.stat().st_size
            csv_size = csv_path.stat().st_size
            
            print(f"\n📊 Size Comparison:")
            print(f"   CSV:     {csv_size:,} bytes ({csv_size/1024:.1f} KB)")
            print(f"   Parquet: {parquet_size:,} bytes ({parquet_size/1024:.1f} KB)")
            print(f"   Savings: {(1 - parquet_size/csv_size)*100:.1f}%")
            
            # Load and verify
            df = pd.read_parquet(parquet_path)
            print(f"\n✅ Loaded {len(df)} rows from Parquet")
            print(f"   Columns: {len(df.columns)}")
    
    except ImportError:
        print("\n⚠️  pandas not available. Parquet export requires pandas and pyarrow.")
        print("   Install with: pip install pandas pyarrow")
    
    print("\n💡 Tip: Use Parquet for datasets with > 1000 papers for better compression.")


# =============================================================================
# Example 5: Multi-Format Export
# =============================================================================

def example_multi_format_export():
    """Example: Export in multiple formats at once."""
    print("\n" + "=" * 70)
    print("Example 5: Multi-Format Export")
    print("=" * 70)
    
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "papers"
        
        print(f"\nExporting to multiple formats...")
        
        # Export to both CSV and Parquet (if available)
        export_paths = export_papers_compressed(
            state=state,
            base_path=str(base_path),
            formats=["csv", "parquet"]  # Will use available formats
        )
        
        print(f"\n✅ Exports created:")
        for fmt, path in export_paths.items():
            file_path = Path(path)
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"   {fmt.upper():8s}: {file_path.name} ({size/1024:.1f} KB)")
    
    print("\n💡 Tip: Use export_papers_compressed() to create multiple format variants.")


# =============================================================================
# Example 6: Filtered Export
# =============================================================================

def example_filtered_export():
    """Example: Export only papers matching criteria."""
    print("\n" + "=" * 70)
    print("Example 6: Filtered Export")
    print("=" * 70)
    
    papers = create_sample_papers(10)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Filter 1: Only summarized papers
        print("\n--- Filter 1: Only summarized papers ---")
        
        summarized_papers = filter_papers_for_export(
            papers=papers,
            status_filter=["summarized"],
            require_summary=True
        )
        
        print(f"Filtered: {len(summarized_papers)}/{len(papers)} papers")
        
        path1 = Path(tmpdir) / "summarized_only.csv"
        export_papers_to_csv(summarized_papers, str(path1))
        print(f"✅ Exported to: {path1.name}")
        
        # Filter 2: Exclude failed papers
        print("\n--- Filter 2: Exclude failed papers ---")
        
        successful_papers = filter_papers_for_export(
            papers=papers,
            status_filter=["summarized", "classified", "pending"]
        )
        
        print(f"Filtered: {len(successful_papers)}/{len(papers)} papers")
        
        path2 = Path(tmpdir) / "successful_only.csv"
        export_papers_to_csv(successful_papers, str(path2))
        print(f"✅ Exported to: {path2.name}")
        
        # Filter 3: With summaries and notes
        print("\n--- Filter 3: With summaries (programmatic filter) ---")
        
        with_summaries = {
            pid: paper for pid, paper in papers.items()
            if paper.full_summary and paper.initial_notes
        }
        
        print(f"Filtered: {len(with_summaries)}/{len(papers)} papers")
        
        path3 = Path(tmpdir) / "with_summaries.csv"
        export_papers_to_csv(with_summaries, str(path3))
        print(f"✅ Exported to: {path3.name}")
    
    print("\n💡 Tip: Use filter_papers_for_export() for common filters or write custom logic.")


# =============================================================================
# Example 7: Export Validation
# =============================================================================

def example_export_validation():
    """Example: Validate export file integrity."""
    print("\n" + "=" * 70)
    print("Example 7: Export Validation")
    print("=" * 70)
    
    papers = create_sample_papers(10)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "papers.csv"
        
        # Export
        print(f"\nExporting {len(papers)} papers...")
        csv_path = export_papers_to_csv(papers, str(output_path))
        print(f"✅ Export complete")
        
        # Validate
        print(f"\nValidating export...")
        
        validation = validate_export(
            export_path=csv_path,
            expected_count=len(papers),
            expected_fields={"id", "title", "full_summary", "processing_status"}
        )
        
        print(f"\n📊 Validation Results:")
        print(f"   Valid: {validation['valid']}")
        print(f"   File size: {validation['file_size']:,} bytes")
        print(f"   Row count: {validation['row_count']}")
        print(f"   Column count: {validation['column_count']}")
        
        if validation["issues"]:
            print(f"\n❌ Issues:")
            for issue in validation["issues"]:
                print(f"   - {issue}")
        
        if validation["warnings"]:
            print(f"\n⚠️  Warnings:")
            for warning in validation["warnings"]:
                print(f"   - {warning}")
        
        if validation["valid"]:
            print(f"\n✅ Export validation passed!")
    
    print("\n💡 Tip: Always validate exports to catch issues early.")


# =============================================================================
# Example 8: Export Statistics
# =============================================================================

def example_export_statistics():
    """Example: Generate detailed export statistics."""
    print("\n" + "=" * 70)
    print("Example 8: Export Statistics")
    print("=" * 70)
    
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "papers.csv"
        
        # Export
        csv_path = export_papers_to_csv(state["papers"], str(output_path))
        
        # Generate statistics
        print(f"\nGenerating export statistics...")
        
        stats = export_summary_statistics(
            export_path=csv_path,
            state=state
        )
        
        print(f"\n📊 Export Statistics:")
        print(f"   File: {stats['file_name']}")
        print(f"   Size: {stats['file_size_kb']:.2f} KB ({stats['file_size_mb']:.4f} MB)")
        print(f"   Created: {stats.get('file_created', 'N/A')}")
        print(f"\n   Content:")
        print(f"   Rows: {stats['row_count']}")
        print(f"   Columns: {stats['column_count']}")
        
        if "status_distribution" in stats:
            print(f"\n   Status Distribution:")
            for status, count in stats["status_distribution"].items():
                print(f"   {status:15s}: {count:3d}")
        
        if "papers_with_summary" in stats:
            print(f"\n   Papers with summary: {stats['papers_with_summary']}")
        
        if "processing_stats" in stats:
            print(f"\n   Processing Stats:")
            for key, value in stats["processing_stats"].items():
                print(f"   {key}: {value}")
    
    print("\n💡 Tip: Use export_summary_statistics() for detailed reporting.")


# =============================================================================
# Example 9: Metadata Generation
# =============================================================================

def example_metadata_generation():
    """Example: Create export metadata."""
    print("\n" + "=" * 70)
    print("Example 9: Export Metadata Generation")
    print("=" * 70)
    
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "papers.csv"
        
        # Export
        csv_path = export_papers_to_csv(state["papers"], str(output_path))
        
        # Create metadata
        print(f"\nGenerating export metadata...")
        
        metadata = create_export_metadata(
            state=state,
            export_path=csv_path,
            export_type="csv"
        )
        
        print(f"\n📊 Export Metadata:")
        print(f"   Export timestamp: {metadata['export_timestamp']}")
        print(f"   Export type: {metadata['export_type']}")
        print(f"   Export path: {metadata['export_path']}")
        print(f"\n   Papers:")
        print(f"   Total: {metadata['total_papers']}")
        print(f"   With summaries: {metadata['with_summary']}")
        print(f"   With notes: {metadata['with_notes']}")
        print(f"   With classification: {metadata['with_classification']}")
        
        print(f"\n   Status Distribution:")
        for status, count in metadata['status_distribution'].items():
            print(f"   {status:15s}: {count:3d}")
        
        print(f"\n   Current Phase: {metadata['current_phase']}")
        
        print(f"\n   Run Configuration:")
        for key, value in metadata['run_config'].items():
            print(f"   {key}: {value}")
        
        # Save metadata to file
        import json
        metadata_file = Path(tmpdir) / "papers.metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n✅ Metadata saved to: {metadata_file.name}")
    
    print("\n💡 Tip: Metadata helps track export provenance and statistics.")


# =============================================================================
# Example 10: Complete Export Pipeline
# =============================================================================

def example_complete_pipeline():
    """Example: Complete export pipeline with all features."""
    print("\n" + "=" * 70)
    print("Example 10: Complete Export Pipeline")
    print("=" * 70)
    
    # Create state with papers
    state = create_sample_state()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\n1️⃣  Exporting papers after Pass 1...")
        
        # Step 1: Export after Pass 1
        output_path = Path(tmpdir) / "papers_pass1.csv"
        state = export_after_pass1(
            state=state,
            output_path=str(output_path),
            include_partial=True,
            save_metadata=True
        )
        
        print(f"   ✅ Export path: {state['master_csv_path']}")
        
        # Step 2: Validate export
        print(f"\n2️⃣  Validating export...")
        
        validation = validate_export(
            export_path=state["master_csv_path"],
            expected_count=len(state["papers"])
        )
        
        if validation["valid"]:
            print(f"   ✅ Validation passed")
        else:
            print(f"   ❌ Validation failed: {validation['issues']}")
        
        # Step 3: Generate statistics
        print(f"\n3️⃣  Generating statistics...")
        
        stats = export_summary_statistics(
            export_path=state["master_csv_path"],
            state=state
        )
        
        print(f"   ✅ File: {stats['file_name']}")
        print(f"   ✅ Size: {stats['file_size_kb']:.2f} KB")
        print(f"   ✅ Rows: {stats['row_count']}")
        
        # Step 4: Export filtered subset
        print(f"\n4️⃣  Exporting filtered subset (summarized only)...")
        
        summarized_papers = filter_papers_for_export(
            papers=state["papers"],
            status_filter=["summarized"],
            require_summary=True
        )
        
        filtered_path = Path(tmpdir) / "papers_summarized.csv"
        export_papers_to_csv(summarized_papers, str(filtered_path))
        
        print(f"   ✅ Exported {len(summarized_papers)} papers")
        
        # Step 5: Export to Parquet (if available)
        print(f"\n5️⃣  Attempting Parquet export...")
        
        try:
            parquet_path = Path(tmpdir) / "papers.parquet"
            export_papers_to_parquet(
                papers=state["papers"],
                output_path=str(parquet_path),
                compression="snappy"
            )
            print(f"   ✅ Parquet export successful")
        except ImportError:
            print(f"   ⚠️  Skipped (pandas not available)")
        
        print(f"\n📊 Pipeline Summary:")
        print(f"   Total papers: {len(state['papers'])}")
        print(f"   Exports created: 2+ formats")
        print(f"   Validation: {'Passed' if validation['valid'] else 'Failed'}")
        print(f"   Metadata: Saved")
        print(f"   Statistics: Generated")
    
    print("\n✅ Complete pipeline executed successfully!")
    print("\n💡 Tip: This pattern combines all Phase 7 features for production use.")


# =============================================================================
# Main
# =============================================================================

def main():
    """Run all examples."""
    print("=" * 70)
    print("Phase 7: Initial CSV Export - Usage Examples")
    print("=" * 70)
    
    examples = [
        ("Basic CSV Export", example_basic_csv_export),
        ("Custom Export Configuration", example_custom_export_config),
        ("Export After Summarization", example_export_after_pass1),
        ("Parquet Export", example_parquet_export),
        ("Multi-Format Export", example_multi_format_export),
        ("Filtered Export", example_filtered_export),
        ("Export Validation", example_export_validation),
        ("Export Statistics", example_export_statistics),
        ("Metadata Generation", example_metadata_generation),
        ("Complete Export Pipeline", example_complete_pipeline),
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        try:
            func()
        except Exception as e:
            print(f"\n❌ Error in example {i} ({name}): {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
