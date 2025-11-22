#!/usr/bin/env python3
"""
Phase 7: Export Flows - Data Export Module

This module implements comprehensive export functionality for the RAG system:

- CSV export with all paper fields
- Parquet export for large datasets (optional)
- Export validation and integrity checks
- Flexible filtering and field selection
- Export metadata and versioning

Version: 1.0
Date: 2025-11-22
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
