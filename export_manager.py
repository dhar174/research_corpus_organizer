#!/usr/bin/env python3
"""
Phase 7 & 12: Export Flows - Data Export Module

This module implements comprehensive export functionality for the RAG system:

- CSV export with all paper fields
- Parquet export for large datasets (optional)
- Export validation and integrity checks
- Flexible filtering and field selection
- Export metadata and versioning
- Final data export with complete metadata (Phase 12)
- Export variants (full, summary, JSON)
- Statistics and quality reports
- Artifact management

Version: 2.0
Date: 2025-11-24
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from pathlib import Path
import logging
import json
import csv

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas not available. Some export features will be limited.")

from rag_models import (
    PaperRecord,
    GraphState,
    RunConfig,
    TopicHierarchy,
)

# Export list for clean imports
__all__ = [
    # Step 7.1
    'export_papers_to_csv',
    'export_papers_to_dict',
    'ExportConfig',
    
    # Step 7.2
    'export_after_pass1',
    'create_export_metadata',
    
    # Step 7.3
    'export_papers_to_parquet',
    'export_papers_compressed',
    
    # Step 7.4
    'validate_export',
    'export_summary_statistics',
    
    # Phase 12 - Step 12.1: Final Data Export
    'export_final_data',
    'create_final_export_config',
    
    # Phase 12 - Step 12.2: Export Variants
    'export_full_csv',
    'export_summary_csv',
    'export_to_json',
    'export_taxonomy_to_json',
    
    # Phase 12 - Step 12.3: Statistics and Quality Reports
    'generate_statistics_report',
    'count_papers_by_status',
    'count_papers_by_topic',
    'generate_quality_report',
    'display_export_summary',
    
    # Phase 12 - Step 12.4: Artifact Management
    'save_all_artifacts',
    'save_error_logs',
    'save_processing_logs',
    'update_state_with_paths',
    
    # Utility
    'flatten_paper_record',
    'filter_papers_for_export',
]


# =============================================================================
# Export Configuration
# =============================================================================

class ExportConfig:
    """Configuration for export operations."""
    
    def __init__(
        self,
        include_fields: Optional[Set[str]] = None,
        exclude_fields: Optional[Set[str]] = None,
        flatten_nested: bool = True,
        include_metadata: bool = True,
        timestamp_format: str = "iso",
    ):
        """
        Initialize export configuration.
        
        Args:
            include_fields: Set of field names to include (None = all)
            exclude_fields: Set of field names to exclude
            flatten_nested: Whether to flatten nested structures
            include_metadata: Whether to include export metadata columns
            timestamp_format: Format for timestamps ("iso" or "epoch")
        """
        self.include_fields = include_fields
        self.exclude_fields = exclude_fields or set()
        self.flatten_nested = flatten_nested
        self.include_metadata = include_metadata
        self.timestamp_format = timestamp_format


# =============================================================================
# Step 7.1: CSV Export Function
# =============================================================================

def flatten_paper_record(paper: PaperRecord, config: ExportConfig) -> Dict[str, Any]:
    """
    Flatten a PaperRecord for export.
    
    Handles nested data structures like lists and dicts.
    
    Args:
        paper: PaperRecord to flatten
        config: ExportConfig with flattening options
        
    Returns:
        Flattened dictionary
    """
    data = paper.to_dict()
    
    # Filter fields
    if config.include_fields:
        data = {k: v for k, v in data.items() if k in config.include_fields}
    
    if config.exclude_fields:
        data = {k: v for k, v in data.items() if k not in config.exclude_fields}
    
    # Flatten nested structures if requested
    if config.flatten_nested:
        flattened = {}
        
        for key, value in data.items():
            if isinstance(value, list):
                # Join lists as strings if all elements are strings
                if value and all(isinstance(item, str) for item in value):
                    flattened[key] = "; ".join(value)
                else:
                    flattened[key] = json.dumps(value)
            elif isinstance(value, dict):
                # Serialize dicts as JSON
                flattened[key] = json.dumps(value)
            elif isinstance(value, datetime):
                # Format timestamps
                if config.timestamp_format == "iso":
                    flattened[key] = value.isoformat()
                else:
                    flattened[key] = value.timestamp()
            else:
                flattened[key] = value
        
        return flattened
    
    return data


def filter_papers_for_export(
    papers: Dict[str, PaperRecord],
    status_filter: Optional[List[str]] = None,
    require_summary: bool = False,
    require_classification: bool = False
) -> Dict[str, PaperRecord]:
    """
    Filter papers based on criteria.
    
    Args:
        papers: Dictionary of papers
        status_filter: List of acceptable processing statuses
        require_summary: Whether to require full_summary
        require_classification: Whether to require topic classification
        
    Returns:
        Filtered dictionary of papers
    """
    filtered = {}
    
    for paper_id, paper in papers.items():
        # Check status filter
        if status_filter and paper.processing_status not in status_filter:
            continue
        
        # Check summary requirement
        if require_summary and not paper.full_summary:
            continue
        
        # Check classification requirement
        if require_classification and not paper.tier1_topic:
            continue
        
        filtered[paper_id] = paper
    
    return filtered


def export_papers_to_dict(
    papers: Dict[str, PaperRecord],
    config: Optional[ExportConfig] = None
) -> List[Dict[str, Any]]:
    """
    Export papers to list of dictionaries.
    
    Args:
        papers: Dictionary of PaperRecord objects
        config: Export configuration
        
    Returns:
        List of flattened paper dictionaries
    """
    if config is None:
        config = ExportConfig()
    
    data = []
    
    for paper in papers.values():
        flattened = flatten_paper_record(paper, config)
        data.append(flattened)
    
    return data


def export_papers_to_csv(
    papers: Dict[str, PaperRecord],
    output_path: str,
    config: Optional[ExportConfig] = None,
    include_export_metadata: bool = True
) -> str:
    """
    Export papers to CSV file.
    
    Args:
        papers: Dictionary of paper_id -> PaperRecord
        output_path: Path to output CSV file
        config: Export configuration
        include_export_metadata: Whether to add export metadata columns
        
    Returns:
        Path to created CSV file
    """
    if config is None:
        config = ExportConfig()
    
    logger.info(f"Exporting {len(papers)} papers to CSV: {output_path}")
    
    # Convert to list of dicts
    data = export_papers_to_dict(papers, config)
    
    if not data:
        logger.warning("No papers to export")
        # Create empty file
        Path(output_path).touch()
        return output_path
    
    # Add export metadata if requested
    if include_export_metadata and config.include_metadata:
        export_timestamp = datetime.now()
        for row in data:
            row["export_timestamp"] = export_timestamp.isoformat()
            row["export_version"] = "1.0"
    
    # Use pandas if available for better handling
    if PANDAS_AVAILABLE:
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
    else:
        # Fallback to csv module
        if data:
            keys = data[0].keys()
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)
    
    logger.info(f"Export complete: {output_path}")
    
    return output_path


# =============================================================================
# Step 7.2: Initial Export After Pass 1
# =============================================================================

def create_export_metadata(
    state: GraphState,
    export_path: str,
    export_type: str = "csv"
) -> Dict[str, Any]:
    """
    Create metadata about the export.
    
    Args:
        state: GraphState with papers and statistics
        export_path: Path to export file
        export_type: Type of export (csv, parquet, json)
        
    Returns:
        Dictionary with export metadata
    """
    papers = state["papers"]
    
    # Count papers by status
    status_counts = {}
    for paper in papers.values():
        status = paper.processing_status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Count papers with summaries
    with_summary = sum(1 for p in papers.values() if p.full_summary)
    with_notes = sum(1 for p in papers.values() if p.initial_notes)
    with_classification = sum(1 for p in papers.values() if p.tier1_topic)
    
    metadata = {
        "export_timestamp": datetime.now().isoformat(),
        "export_type": export_type,
        "export_path": export_path,
        "total_papers": len(papers),
        "status_distribution": status_counts,
        "with_summary": with_summary,
        "with_notes": with_notes,
        "with_classification": with_classification,
        "current_phase": state.get("current_phase", "unknown"),
        "run_config": {
            "drive_folder": state["config"].drive_folder_path,
            "summary_model": state["config"].summary_model,
            "taxonomy_model": state["config"].taxonomy_model,
        },
    }
    
    # Add stats if available
    if "stats" in state:
        metadata["processing_stats"] = state["stats"]
    
    return metadata


def export_after_pass1(
    state: GraphState,
    output_path: str,
    include_partial: bool = True,
    save_metadata: bool = True
) -> GraphState:
    """
    Export papers after Pass 1 (summarization) is complete.
    
    Args:
        state: GraphState with papers
        output_path: Path for CSV export
        include_partial: Whether to include partially-processed papers
        save_metadata: Whether to save export metadata
        
    Returns:
        Updated GraphState with export path
    """
    logger.info("Exporting papers after Pass 1 (summarization)")
    
    papers = state["papers"]
    
    # Filter papers if not including partial
    if not include_partial:
        papers = filter_papers_for_export(
            papers,
            status_filter=["summarized", "embedded", "classified"]
        )
        logger.info(f"Filtered to {len(papers)} fully processed papers")
    
    # Export to CSV
    export_config = ExportConfig(
        flatten_nested=True,
        include_metadata=True
    )
    
    csv_path = export_papers_to_csv(papers, output_path, export_config)
    
    # Update state
    state["master_csv_path"] = csv_path
    
    # Create and save metadata
    if save_metadata:
        metadata = create_export_metadata(state, csv_path, "csv")
        
        # Save metadata as JSON
        metadata_path = Path(output_path).with_suffix('.metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Export metadata saved to: {metadata_path}")
        
        # Store metadata in state
        if "stats" not in state:
            state["stats"] = {}
        state["stats"]["export_metadata"] = metadata
    
    logger.info(f"Pass 1 export complete: {csv_path}")
    
    return state


# =============================================================================
# Step 7.3: Optional Parquet Export
# =============================================================================

def export_papers_to_parquet(
    papers: Dict[str, PaperRecord],
    output_path: str,
    compression: str = "snappy",
    config: Optional[ExportConfig] = None
) -> str:
    """
    Export papers to Parquet format.
    
    Parquet provides better compression and preserves data types.
    
    Args:
        papers: Dictionary of PaperRecord objects
        output_path: Path to output Parquet file
        compression: Compression algorithm (snappy, gzip, brotli, none)
        config: Export configuration
        
    Returns:
        Path to created Parquet file
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("Pandas required for Parquet export. Install with: pip install pandas pyarrow")
    
    logger.info(f"Exporting {len(papers)} papers to Parquet: {output_path}")
    
    if config is None:
        config = ExportConfig(flatten_nested=False)  # Preserve types in Parquet
    
    # Convert to list of dicts
    data = export_papers_to_dict(papers, config)
    
    if not data:
        logger.warning("No papers to export")
        return output_path
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to Parquet
    df.to_parquet(
        output_path,
        compression=compression,
        index=False
    )
    
    logger.info(f"Parquet export complete: {output_path}")
    
    # Log file size
    file_size = Path(output_path).stat().st_size
    logger.info(f"File size: {file_size / 1024:.1f} KB")
    
    return output_path


def export_papers_compressed(
    state: GraphState,
    base_path: str,
    formats: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Export papers in multiple compressed formats.
    
    Args:
        state: GraphState with papers
        base_path: Base path for exports (extensions will be added)
        formats: List of formats to export (csv, parquet)
        
    Returns:
        Dictionary mapping format -> file path
    """
    if formats is None:
        formats = ["csv"]
        if PANDAS_AVAILABLE:
            formats.append("parquet")
    
    papers = state["papers"]
    export_paths = {}
    
    base = Path(base_path).with_suffix('')  # Remove extension if present
    
    for fmt in formats:
        if fmt == "csv":
            path = str(base) + ".csv"
            export_papers_to_csv(papers, path)
            export_paths["csv"] = path
        
        elif fmt == "parquet":
            if PANDAS_AVAILABLE:
                path = str(base) + ".parquet"
                export_papers_to_parquet(papers, path, compression="snappy")
                export_paths["parquet"] = path
            else:
                logger.warning("Pandas not available, skipping Parquet export")
    
    return export_paths


# =============================================================================
# Step 7.4: Export Validation
# =============================================================================

def validate_export(
    export_path: str,
    expected_count: int,
    expected_fields: Optional[Set[str]] = None
) -> Dict[str, Any]:
    """
    Validate an export file.
    
    Checks:
    - File exists
    - Row count matches expected
    - Required fields are present
    - Basic data integrity
    
    Args:
        export_path: Path to export file
        expected_count: Expected number of papers
        expected_fields: Set of required field names
        
    Returns:
        Dictionary with validation results
    """
    issues = []
    warnings = []
    
    # Check file exists
    file_path = Path(export_path)
    if not file_path.exists():
        return {
            "valid": False,
            "issues": ["Export file does not exist"],
            "warnings": [],
            "file_size": 0,
            "row_count": 0,
        }
    
    # Get file size
    file_size = file_path.stat().st_size
    
    # Determine file type and load
    if export_path.endswith('.csv'):
        if PANDAS_AVAILABLE:
            df = pd.read_csv(export_path)
            row_count = len(df)
            columns = set(df.columns)
        else:
            # Fallback to csv module
            with open(export_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                row_count = len(rows)
                columns = set(rows[0].keys()) if rows else set()
    
    elif export_path.endswith('.parquet'):
        if PANDAS_AVAILABLE:
            df = pd.read_parquet(export_path)
            row_count = len(df)
            columns = set(df.columns)
        else:
            issues.append("Cannot validate Parquet file without pandas")
            return {
                "valid": False,
                "issues": issues,
                "warnings": warnings,
                "file_size": file_size,
                "row_count": 0,
            }
    else:
        issues.append(f"Unknown file type: {export_path}")
        return {
            "valid": False,
            "issues": issues,
            "warnings": warnings,
            "file_size": file_size,
            "row_count": 0,
        }
    
    # Check row count
    if row_count != expected_count:
        diff = abs(row_count - expected_count)
        if diff > expected_count * 0.1:  # More than 10% difference
            issues.append(f"Row count mismatch: expected {expected_count}, got {row_count}")
        else:
            warnings.append(f"Minor row count difference: expected {expected_count}, got {row_count}")
    
    # Check required fields
    if expected_fields:
        missing_fields = expected_fields - columns
        if missing_fields:
            issues.append(f"Missing required fields: {missing_fields}")
    
    # Check for empty file
    if row_count == 0:
        warnings.append("Export file is empty")
    
    # Check file size
    if file_size == 0:
        issues.append("Export file has zero size")
    elif file_size < 100:
        warnings.append(f"Export file is very small ({file_size} bytes)")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "file_size": file_size,
        "row_count": row_count,
        "columns": sorted(columns),
        "column_count": len(columns),
    }


def export_summary_statistics(
    export_path: str,
    state: Optional[GraphState] = None
) -> Dict[str, Any]:
    """
    Generate summary statistics for an export.
    
    Args:
        export_path: Path to export file
        state: Optional GraphState for additional context
        
    Returns:
        Dictionary with statistics
    """
    file_path = Path(export_path)
    
    stats = {
        "file_path": str(file_path),
        "file_name": file_path.name,
        "file_size_bytes": 0,
        "file_size_kb": 0,
        "file_size_mb": 0,
        "row_count": 0,
        "column_count": 0,
        "export_timestamp": datetime.now().isoformat(),
    }
    
    # Get file size
    if file_path.exists():
        file_size = file_path.stat().st_size
        stats["file_size_bytes"] = file_size
        stats["file_size_kb"] = round(file_size / 1024, 2)
        stats["file_size_mb"] = round(file_size / (1024 * 1024), 2)
        stats["file_created"] = datetime.fromtimestamp(file_path.stat().st_ctime).isoformat()
    else:
        return stats
    
    # Load and analyze
    try:
        if export_path.endswith('.csv') and PANDAS_AVAILABLE:
            df = pd.read_csv(export_path)
            stats["row_count"] = len(df)
            stats["column_count"] = len(df.columns)
            stats["columns"] = list(df.columns)
            
            # Status distribution if available
            if "processing_status" in df.columns:
                stats["status_distribution"] = df["processing_status"].value_counts().to_dict()
            
            # Summary statistics
            if "full_summary" in df.columns:
                stats["papers_with_summary"] = df["full_summary"].notna().sum()
            
            if "tier1_topic" in df.columns:
                stats["papers_with_classification"] = df["tier1_topic"].notna().sum()
        
        elif export_path.endswith('.parquet') and PANDAS_AVAILABLE:
            df = pd.read_parquet(export_path)
            stats["row_count"] = len(df)
            stats["column_count"] = len(df.columns)
            stats["columns"] = list(df.columns)
    
    except Exception as e:
        logger.warning(f"Error generating statistics: {e}")
        stats["error"] = str(e)
    
    # Add state statistics if provided
    if state and "stats" in state:
        stats["processing_stats"] = state["stats"]
    
    return stats


# =============================================================================
# Phase 12 - Step 12.1: Final Data Export
# =============================================================================

def create_final_export_config() -> ExportConfig:
    """
    Create export configuration for final data export.
    
    Returns:
        ExportConfig with settings for complete metadata export
    """
    # No fields excluded - export everything
    return ExportConfig(
        include_fields=None,  # Include all fields
        exclude_fields=set(),  # Exclude nothing
        flatten_nested=True,
        include_metadata=True,
        timestamp_format="iso"
    )


def export_final_data(
    state: GraphState,
    output_dir: str,
    base_filename: str = "rag_corpus_final",
    formats: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Export all papers with complete metadata in multiple formats.
    
    This is the final export after all processing is complete, including:
    - All metadata fields
    - All classification fields (tier1, tier2, tier3)
    - Taxonomy version
    - All summaries (full_summary, deep_summary)
    - All notes (initial_notes, classification_notes)
    - Processing status and error tracking
    
    Args:
        state: GraphState with all processed papers
        output_dir: Directory for export files
        base_filename: Base filename (extensions will be added)
        formats: List of formats to export (default: ["csv", "parquet"])
        
    Returns:
        Dictionary mapping format -> file path
    """
    if formats is None:
        formats = ["csv"]
        if PANDAS_AVAILABLE:
            formats.append("parquet")
    
    logger.info(f"Exporting final data for {len(state['papers'])} papers")
    
    # Create output directory if needed
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    papers = state["papers"]
    export_paths = {}
    
    # Get final export config (all fields)
    config = create_final_export_config()
    
    # Export in each requested format
    for fmt in formats:
        if fmt == "csv":
            csv_path = output_path / f"{base_filename}.csv"
            export_papers_to_csv(papers, str(csv_path), config, include_export_metadata=True)
            export_paths["csv"] = str(csv_path)
            logger.info(f"Final CSV export saved: {csv_path}")
        
        elif fmt == "parquet":
            if PANDAS_AVAILABLE:
                parquet_path = output_path / f"{base_filename}.parquet"
                export_papers_to_parquet(papers, str(parquet_path), compression="snappy", config=config)
                export_paths["parquet"] = str(parquet_path)
                logger.info(f"Final Parquet export saved: {parquet_path}")
            else:
                logger.warning("Pandas not available, skipping Parquet export")
    
    # Create and save metadata
    metadata = create_export_metadata(state, export_paths.get("csv", ""), "final")
    metadata_path = output_path / f"{base_filename}_metadata.json"
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    export_paths["metadata"] = str(metadata_path)
    logger.info(f"Export metadata saved: {metadata_path}")
    
    return export_paths


# =============================================================================
# Phase 12 - Step 12.2: Export Variants
# =============================================================================

def export_full_csv(
    state: GraphState,
    output_path: str
) -> str:
    """
    Export full CSV with all fields.
    
    Args:
        state: GraphState with papers
        output_path: Path to output CSV file
        
    Returns:
        Path to created CSV file
    """
    config = create_final_export_config()
    papers = state["papers"]
    
    return export_papers_to_csv(papers, output_path, config, include_export_metadata=True)


def export_summary_csv(
    state: GraphState,
    output_path: str,
    key_fields: Optional[Set[str]] = None
) -> str:
    """
    Export summary CSV with key fields only.
    
    Default key fields include:
    - Identifiers (id, filename, arxiv_id, doi)
    - Metadata (title, authors, venue, year)
    - Summaries (full_summary, initial_notes)
    - Classification (tier1_topic, tier2_topic, tier3_topic with names)
    - Status (processing_status, error_reason)
    
    Args:
        state: GraphState with papers
        output_path: Path to output CSV file
        key_fields: Set of field names to include (None = use defaults)
        
    Returns:
        Path to created CSV file
    """
    if key_fields is None:
        # Default key fields for summary export
        key_fields = {
            # Identifiers
            "id",
            "filename",
            "arxiv_id",
            "doi",
            
            # Metadata
            "title",
            "authors",
            "venue",
            "year",
            "publish_date",
            
            # Content
            "abstract_text",
            "full_summary",
            "initial_notes",
            
            # Classification
            "tier1_topic",
            "tier1_topic_name",
            "tier1_confidence",
            "tier2_topic",
            "tier2_topic_name",
            "tier2_confidence",
            "tier3_topic",
            "tier3_topic_name",
            "tier3_confidence",
            "taxonomy_version",
            
            # Status
            "processing_status",
            "error_reason",
            "created_at",
            "last_updated",
        }
    
    config = ExportConfig(
        include_fields=key_fields,
        exclude_fields=set(),
        flatten_nested=True,
        include_metadata=True,
        timestamp_format="iso"
    )
    
    papers = state["papers"]
    
    return export_papers_to_csv(papers, output_path, config, include_export_metadata=True)


def export_to_json(
    state: GraphState,
    output_path: str,
    include_taxonomy: bool = True,
    include_papers: bool = True,
    pretty: bool = True
) -> str:
    """
    Export data to JSON format (hierarchical data).
    
    JSON export is ideal for:
    - Preserving hierarchical structures
    - Nested data (lists, dicts)
    - Importing into other systems
    - API integration
    
    Args:
        state: GraphState with papers and taxonomy
        output_path: Path to output JSON file
        include_taxonomy: Whether to include taxonomy
        include_papers: Whether to include papers
        pretty: Whether to pretty-print JSON
        
    Returns:
        Path to created JSON file
    """
    logger.info(f"Exporting to JSON: {output_path}")
    
    data = {
        "export_metadata": {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0",
            "total_papers": len(state.get("papers", {})),
        }
    }
    
    # Add taxonomy if requested
    if include_taxonomy and state.get("topic_hierarchy"):
        taxonomy = state["topic_hierarchy"]
        data["taxonomy"] = taxonomy.to_dict()
        logger.info(f"Included taxonomy with {len(taxonomy.tier1)} tier1 topics")
    
    # Add papers if requested
    if include_papers:
        papers_data = []
        for paper in state["papers"].values():
            paper_dict = paper.to_dict()
            papers_data.append(paper_dict)
        
        data["papers"] = papers_data
        logger.info(f"Included {len(papers_data)} papers")
    
    # Add configuration info
    if "config" in state:
        data["config"] = {
            "drive_folder": state["config"].drive_folder_path,
            "summary_model": state["config"].summary_model,
            "taxonomy_model": state["config"].taxonomy_model,
            "classification_model": state["config"].classification_model,
        }
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            json.dump(data, f, ensure_ascii=False)
    
    # Log file size
    file_size = Path(output_path).stat().st_size
    logger.info(f"JSON export complete: {output_path} ({file_size / 1024:.1f} KB)")
    
    return output_path


def export_taxonomy_to_json(
    state: GraphState,
    output_path: str,
    pretty: bool = True
) -> str:
    """
    Export taxonomy only to JSON file.
    
    Args:
        state: GraphState with taxonomy
        output_path: Path to output JSON file
        pretty: Whether to pretty-print JSON
        
    Returns:
        Path to created JSON file
    """
    if not state.get("topic_hierarchy"):
        logger.warning("No taxonomy found in state")
        # Create empty file with metadata
        data = {
            "error": "No taxonomy available",
            "timestamp": datetime.now().isoformat()
        }
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2 if pretty else None)
        return output_path
    
    taxonomy = state["topic_hierarchy"]
    data = taxonomy.to_dict()
    
    # Add export metadata
    data["export_metadata"] = {
        "timestamp": datetime.now().isoformat(),
        "version": "1.0",
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            json.dump(data, f, ensure_ascii=False)
    
    logger.info(f"Taxonomy exported to: {output_path}")
    
    return output_path


# =============================================================================
# Phase 12 - Step 12.3: Statistics and Quality Reports
# =============================================================================

def count_papers_by_status(papers: Dict[str, PaperRecord]) -> Dict[str, int]:
    """
    Count papers by processing status.
    
    Args:
        papers: Dictionary of PaperRecord objects
        
    Returns:
        Dictionary mapping status -> count
    """
    counts = {}
    
    for paper in papers.values():
        status = paper.processing_status
        counts[status] = counts.get(status, 0) + 1
    
    return counts


def count_papers_by_topic(
    papers: Dict[str, PaperRecord],
    tier: int = 1
) -> Dict[str, int]:
    """
    Count papers by topic at a specific tier.
    
    Args:
        papers: Dictionary of PaperRecord objects
        tier: Tier level (1, 2, or 3)
        
    Returns:
        Dictionary mapping topic_name -> count
    """
    counts = {}
    
    if tier == 1:
        field = "tier1_topic_name"
    elif tier == 2:
        field = "tier2_topic_name"
    elif tier == 3:
        field = "tier3_topic_name"
    else:
        raise ValueError(f"Invalid tier: {tier}. Must be 1, 2, or 3")
    
    for paper in papers.values():
        topic = getattr(paper, field, None)
        if topic:
            counts[topic] = counts.get(topic, 0) + 1
    
    return counts


def generate_statistics_report(state: GraphState) -> Dict[str, Any]:
    """
    Generate comprehensive statistics report.
    
    Args:
        state: GraphState with papers and taxonomy
        
    Returns:
        Dictionary with detailed statistics
    """
    papers = state.get("papers", {})
    taxonomy = state.get("topic_hierarchy")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_papers": len(papers),
    }
    
    # Count by status
    status_counts = count_papers_by_status(papers)
    report["status_distribution"] = status_counts
    
    # Count by topic (all tiers)
    report["topic_distribution"] = {}
    for tier in [1, 2, 3]:
        try:
            tier_counts = count_papers_by_topic(papers, tier)
            report["topic_distribution"][f"tier{tier}"] = tier_counts
            report[f"tier{tier}_unique_topics"] = len(tier_counts)
        except Exception as e:
            logger.warning(f"Error counting tier {tier} topics: {e}")
    
    # Taxonomy statistics
    if taxonomy:
        report["taxonomy"] = taxonomy.get_statistics()
    
    # Summary statistics
    report["summaries"] = {
        "with_full_summary": sum(1 for p in papers.values() if p.full_summary),
        "with_deep_summary": sum(1 for p in papers.values() if p.deep_summary),
        "with_initial_notes": sum(1 for p in papers.values() if p.initial_notes),
        "with_classification_notes": sum(1 for p in papers.values() if p.classification_notes),
    }
    
    # Classification statistics
    report["classification"] = {
        "tier1_classified": sum(1 for p in papers.values() if p.tier1_topic),
        "tier2_classified": sum(1 for p in papers.values() if p.tier2_topic),
        "tier3_classified": sum(1 for p in papers.values() if p.tier3_topic),
        "fully_classified": sum(
            1 for p in papers.values() 
            if p.tier1_topic and p.tier2_topic and p.tier3_topic
        ),
    }
    
    # Error statistics
    report["errors"] = {
        "failed_papers": sum(1 for p in papers.values() if p.processing_status == "failed"),
        "papers_with_errors": sum(1 for p in papers.values() if p.error_reason),
        "total_retries": sum(p.retry_count for p in papers.values()),
    }
    
    # Processing statistics from state
    if "stats" in state:
        report["processing_stats"] = state["stats"]
    
    return report


def generate_quality_report(state: GraphState) -> Dict[str, Any]:
    """
    Generate data quality report.
    
    Checks:
    - Completeness of metadata
    - Presence of required fields
    - Classification coverage
    - Error rates
    
    Args:
        state: GraphState with papers
        
    Returns:
        Dictionary with quality metrics and issues
    """
    papers = state.get("papers", {})
    total = len(papers)
    
    if total == 0:
        return {
            "error": "No papers to analyze",
            "timestamp": datetime.now().isoformat()
        }
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_papers": total,
        "quality_metrics": {},
        "issues": [],
        "warnings": [],
    }
    
    # Check metadata completeness
    metrics = report["quality_metrics"]
    
    metrics["with_title"] = sum(1 for p in papers.values() if p.title) / total
    metrics["with_authors"] = sum(1 for p in papers.values() if p.authors) / total
    metrics["with_abstract"] = sum(1 for p in papers.values() if p.abstract_text) / total
    metrics["with_venue"] = sum(1 for p in papers.values() if p.venue) / total
    metrics["with_year"] = sum(1 for p in papers.values() if p.year) / total
    
    # Check processing completeness
    metrics["fully_processed"] = sum(
        1 for p in papers.values() 
        if p.processing_status not in ["pending", "failed"]
    ) / total
    
    metrics["with_summary"] = sum(1 for p in papers.values() if p.full_summary) / total
    metrics["with_classification"] = sum(1 for p in papers.values() if p.tier1_topic) / total
    
    # Check for issues
    if metrics["with_title"] < 0.9:
        report["issues"].append(f"Only {metrics['with_title']:.1%} of papers have titles")
    
    if metrics["with_abstract"] < 0.8:
        report["warnings"].append(f"Only {metrics['with_abstract']:.1%} of papers have abstracts")
    
    if metrics["with_summary"] < 0.95:
        report["warnings"].append(f"Only {metrics['with_summary']:.1%} of papers have summaries")
    
    if metrics["with_classification"] < 0.9:
        report["warnings"].append(f"Only {metrics['with_classification']:.1%} of papers are classified")
    
    # Error rate
    error_rate = sum(1 for p in papers.values() if p.processing_status == "failed") / total
    metrics["error_rate"] = error_rate
    
    if error_rate > 0.05:
        report["issues"].append(f"High error rate: {error_rate:.1%} of papers failed")
    
    # Overall quality score (average of metrics)
    quality_score = sum([
        metrics.get("with_title", 0),
        metrics.get("with_authors", 0),
        metrics.get("with_summary", 0),
        metrics.get("with_classification", 0),
        metrics.get("fully_processed", 0),
    ]) / 5
    
    report["overall_quality_score"] = quality_score
    
    return report


def display_export_summary(
    state: GraphState,
    export_paths: Dict[str, str],
    verbose: bool = True
) -> str:
    """
    Display summary of export to user.
    
    Args:
        state: GraphState with papers
        export_paths: Dictionary of format -> file path
        verbose: If True, show detailed statistics
        
    Returns:
        Formatted summary string
    """
    lines = []
    lines.append("=" * 70)
    lines.append("EXPORT SUMMARY")
    lines.append("=" * 70)
    
    # Export files
    lines.append("\nExported Files:")
    for fmt, path in export_paths.items():
        if Path(path).exists():
            size = Path(path).stat().st_size
            size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
            lines.append(f"  {fmt.upper():12} {path}")
            lines.append(f"               Size: {size_str}")
    
    # Statistics
    papers = state.get("papers", {})
    lines.append(f"\nTotal Papers: {len(papers)}")
    
    # Status distribution
    status_counts = count_papers_by_status(papers)
    lines.append("\nStatus Distribution:")
    for status, count in sorted(status_counts.items()):
        pct = count / len(papers) * 100 if papers else 0
        lines.append(f"  {status:15} {count:5} ({pct:5.1f}%)")
    
    if verbose:
        # Topic distribution (Tier 1)
        tier1_counts = count_papers_by_topic(papers, tier=1)
        if tier1_counts:
            lines.append(f"\nTier 1 Topics ({len(tier1_counts)} topics):")
            sorted_topics = sorted(tier1_counts.items(), key=lambda x: x[1], reverse=True)
            for topic, count in sorted_topics[:10]:  # Show top 10
                pct = count / len(papers) * 100 if papers else 0
                lines.append(f"  {topic:30} {count:5} ({pct:5.1f}%)")
            if len(sorted_topics) > 10:
                lines.append(f"  ... and {len(sorted_topics) - 10} more")
        
        # Quality metrics
        quality = generate_quality_report(state)
        lines.append(f"\nQuality Score: {quality.get('overall_quality_score', 0):.1%}")
        
        if quality.get("issues"):
            lines.append("\nIssues:")
            for issue in quality["issues"]:
                lines.append(f"  ⚠️  {issue}")
        
        if quality.get("warnings"):
            lines.append("\nWarnings:")
            for warning in quality["warnings"]:
                lines.append(f"  ⚡ {warning}")
    
    lines.append("=" * 70)
    
    summary = "\n".join(lines)
    logger.info(summary)
    
    return summary


# =============================================================================
# Phase 12 - Step 12.4: Save All Artifacts
# =============================================================================

def save_error_logs(
    state: GraphState,
    output_path: str
) -> str:
    """
    Save error logs to file.
    
    Args:
        state: GraphState with error tracking
        output_path: Path to error log file
        
    Returns:
        Path to created log file
    """
    errors = []
    
    # Collect errors from papers
    for paper in state.get("papers", {}).values():
        if paper.error_reason:
            errors.append({
                "paper_id": paper.id,
                "filename": paper.filename,
                "error_reason": paper.error_reason,
                "error_stage": paper.error_stage,
                "retry_count": paper.retry_count,
                "processing_status": paper.processing_status,
                "last_updated": paper.last_updated.isoformat(),
            })
    
    # Collect errors from state
    if "errors" in state:
        for error in state["errors"]:
            errors.append(error)
    
    # Save to file
    error_log = {
        "timestamp": datetime.now().isoformat(),
        "total_errors": len(errors),
        "errors": errors,
    }
    
    with open(output_path, 'w') as f:
        json.dump(error_log, f, indent=2)
    
    logger.info(f"Error log saved: {output_path} ({len(errors)} errors)")
    
    return output_path


def save_processing_logs(
    state: GraphState,
    output_path: str
) -> str:
    """
    Save processing logs and statistics to file.
    
    Args:
        state: GraphState with processing statistics
        output_path: Path to processing log file
        
    Returns:
        Path to created log file
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "config": state.get("config", {}).to_dict() if hasattr(state.get("config", {}), "to_dict") else {},
        "current_phase": state.get("current_phase", "unknown"),
        "statistics": generate_statistics_report(state),
        "quality": generate_quality_report(state),
    }
    
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    logger.info(f"Processing log saved: {output_path}")
    
    return output_path


def update_state_with_paths(
    state: GraphState,
    artifact_paths: Dict[str, str]
) -> GraphState:
    """
    Update GraphState with artifact file paths.
    
    Args:
        state: GraphState to update
        artifact_paths: Dictionary of artifact_name -> file path
        
    Returns:
        Updated GraphState
    """
    # Update known paths in state
    if "master_csv_path" in artifact_paths:
        state["master_csv_path"] = artifact_paths["master_csv_path"]
    
    if "faiss_index_path" in artifact_paths:
        state["faiss_index_path"] = artifact_paths["faiss_index_path"]
    
    if "faiss_meta_path" in artifact_paths:
        state["faiss_meta_path"] = artifact_paths["faiss_meta_path"]
    
    if "taxonomy_json_path" in artifact_paths:
        state["taxonomy_json_path"] = artifact_paths["taxonomy_json_path"]
    
    if "errors_log_path" in artifact_paths:
        state["errors_log_path"] = artifact_paths["errors_log_path"]
    
    # Store all paths in stats for reference
    if "stats" not in state:
        state["stats"] = {}
    
    state["stats"]["artifact_paths"] = artifact_paths
    state["stats"]["artifacts_saved_at"] = datetime.now().isoformat()
    
    logger.info(f"Updated state with {len(artifact_paths)} artifact paths")
    
    return state


def save_all_artifacts(
    state: GraphState,
    output_dir: str,
    base_filename: str = "rag_corpus",
    save_faiss: bool = True,
    save_taxonomy: bool = True,
    save_logs: bool = True
) -> Dict[str, str]:
    """
    Save all artifacts from the RAG pipeline.
    
    This orchestration function saves:
    - Master CSV/Parquet files
    - Taxonomy JSON
    - Error logs
    - Processing logs
    - FAISS index and metadata (if available)
    
    Args:
        state: GraphState with all data
        output_dir: Directory for all artifacts
        base_filename: Base filename for artifacts
        save_faiss: Whether to save FAISS index (if available)
        save_taxonomy: Whether to save taxonomy
        save_logs: Whether to save error and processing logs
        
    Returns:
        Dictionary mapping artifact names to file paths
    """
    logger.info(f"Saving all artifacts to: {output_dir}")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    artifact_paths = {}
    
    # 1. Export master CSV and Parquet
    logger.info("Exporting master CSV/Parquet files...")
    export_paths = export_final_data(state, output_dir, base_filename)
    artifact_paths.update(export_paths)
    
    # Store master CSV path
    if "csv" in export_paths:
        artifact_paths["master_csv_path"] = export_paths["csv"]
    
    # 2. Export summary CSV
    summary_csv_path = output_path / f"{base_filename}_summary.csv"
    export_summary_csv(state, str(summary_csv_path))
    artifact_paths["summary_csv"] = str(summary_csv_path)
    
    # 3. Export full JSON
    json_path = output_path / f"{base_filename}_full.json"
    export_to_json(state, str(json_path), include_taxonomy=True, include_papers=True)
    artifact_paths["full_json"] = str(json_path)
    
    # 4. Save taxonomy JSON
    if save_taxonomy and state.get("topic_hierarchy"):
        taxonomy_path = output_path / f"{base_filename}_taxonomy.json"
        export_taxonomy_to_json(state, str(taxonomy_path))
        artifact_paths["taxonomy_json_path"] = str(taxonomy_path)
        logger.info(f"Taxonomy saved: {taxonomy_path}")
    
    # 5. Save FAISS index and metadata (if available)
    if save_faiss:
        if state.get("faiss_index_path"):
            # FAISS already saved, just record path
            artifact_paths["faiss_index_path"] = state["faiss_index_path"]
            logger.info(f"FAISS index path recorded: {state['faiss_index_path']}")
        
        if state.get("faiss_meta_path"):
            artifact_paths["faiss_meta_path"] = state["faiss_meta_path"]
            logger.info(f"FAISS metadata path recorded: {state['faiss_meta_path']}")
    
    # 6. Save error logs
    if save_logs:
        error_log_path = output_path / f"{base_filename}_errors.json"
        save_error_logs(state, str(error_log_path))
        artifact_paths["errors_log_path"] = str(error_log_path)
    
    # 7. Save processing logs
    if save_logs:
        processing_log_path = output_path / f"{base_filename}_processing.json"
        save_processing_logs(state, str(processing_log_path))
        artifact_paths["processing_log_path"] = str(processing_log_path)
    
    # 8. Generate and save statistics report
    stats_path = output_path / f"{base_filename}_statistics.json"
    stats = generate_statistics_report(state)
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    artifact_paths["statistics"] = str(stats_path)
    logger.info(f"Statistics report saved: {stats_path}")
    
    # 9. Generate and save quality report
    quality_path = output_path / f"{base_filename}_quality.json"
    quality = generate_quality_report(state)
    with open(quality_path, 'w') as f:
        json.dump(quality, f, indent=2)
    artifact_paths["quality_report"] = str(quality_path)
    logger.info(f"Quality report saved: {quality_path}")
    
    # 10. Update state with all paths
    update_state_with_paths(state, artifact_paths)
    
    # 11. Display summary
    summary = display_export_summary(state, artifact_paths, verbose=True)
    
    # Save summary to text file
    summary_path = output_path / f"{base_filename}_summary.txt"
    with open(summary_path, 'w') as f:
        f.write(summary)
    artifact_paths["summary_text"] = str(summary_path)
    
    logger.info(f"All artifacts saved successfully ({len(artifact_paths)} files)")
    
    return artifact_paths
