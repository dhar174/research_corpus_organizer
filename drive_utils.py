"""
RAG PDF Research Corpus System - Google Drive Integration (Phase 2)

This module provides utilities for:
- Google Drive mounting and authentication (Step 2.1)
- PDF discovery and initial record creation (Step 2.2)
- File management and validation (Step 2.3)

Version: 1.0
Date: 2025-11-22
"""

import os
import shutil
from typing import Any, Dict, List, Tuple
import logging

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

from rag_models import PaperRecord, RunConfig, IDGenerator

logger = logging.getLogger(__name__)

# Export list for clean imports
__all__ = [
    # Drive Mounting (Step 2.1)
    'mount_google_drive',
    'validate_mount',
    'display_folder_structure',
    
    # PDF Discovery (Step 2.2)
    'discover_pdfs',
    'resolve_folder_path',
    'generate_paper_id',
    'handle_duplicates',
    
    # File Management (Step 2.3)
    'validate_file_access',
    'check_disk_space',
    'sanitize_file_path',
    'validate_pdf_file',
]


# =============================================================================
# Step 2.1: Google Drive Mounting
# =============================================================================

def mount_google_drive(mount_point: str = "/content/drive", force_remount: bool = False) -> bool:
    """
    Mount Google Drive in Google Colab environment.
    
    Args:
        mount_point: Path where Google Drive should be mounted
        force_remount: If True, unmount and remount even if already mounted
        
    Returns:
        True if mounted successfully, False otherwise
        
    Raises:
        ImportError: If not running in Google Colab environment
        
    Example:
        >>> if mount_google_drive():
        ...     print("Google Drive mounted successfully")
    """
    try:
        from google.colab import drive
    except ImportError:
        raise ImportError(
            "google.colab.drive is not available. "
            "This function must be run in a Google Colab environment."
        )
    
    # Check if already mounted
    if os.path.ismount(mount_point) and not force_remount:
        logger.info(f"Google Drive already mounted at {mount_point}")
        return True
    
    # Unmount if force_remount requested
    if force_remount and os.path.ismount(mount_point):
        logger.info(f"Unmounting existing mount at {mount_point}")
        try:
            drive.flush_and_unmount()
        except Exception as e:
            logger.warning(f"Error unmounting: {e}")
    
    # Mount Google Drive
    try:
        logger.info(f"Mounting Google Drive at {mount_point}...")
        drive.mount(mount_point, force_remount=force_remount)
        logger.info("Google Drive mounted successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to mount Google Drive: {e}")
        return False


def validate_mount(mount_point: str = "/content/drive") -> Dict[str, Any]:
    """
    Validate that Google Drive is properly mounted.
    
    Args:
        mount_point: Path where Google Drive should be mounted
        
    Returns:
        Dictionary with validation results:
            - mounted: bool
            - mount_point: str
            - my_drive_exists: bool
            - my_drive_path: str
            - is_writable: bool
            - error: Optional[str]
            
    Example:
        >>> result = validate_mount()
        >>> if result['mounted']:
        ...     print(f"Drive is mounted at {result['mount_point']}")
    """
    result = {
        'mounted': False,
        'mount_point': mount_point,
        'my_drive_exists': False,
        'my_drive_path': None,
        'is_writable': False,
        'error': None
    }
    
    # Check if mount point exists and is a mount
    if not os.path.exists(mount_point):
        result['error'] = f"Mount point {mount_point} does not exist"
        return result
    
    if not os.path.ismount(mount_point):
        result['error'] = f"{mount_point} is not a mount point"
        return result
    
    result['mounted'] = True
    
    # Check for My Drive folder
    my_drive_path = os.path.join(mount_point, "MyDrive")
    if os.path.exists(my_drive_path):
        result['my_drive_exists'] = True
        result['my_drive_path'] = my_drive_path
        
        # Check if writable
        result['is_writable'] = os.access(my_drive_path, os.W_OK)
    else:
        result['error'] = f"MyDrive folder not found at {my_drive_path}"
    
    return result


def display_folder_structure(
    root_path: str,
    max_depth: int = 2,
    show_files: bool = False
) -> str:
    """
    Display the folder structure of a directory.
    
    Args:
        root_path: Root directory to display
        max_depth: Maximum depth to traverse
        show_files: If True, show files in addition to folders
        
    Returns:
        Formatted string representation of folder structure
        
    Example:
        >>> structure = display_folder_structure("/content/drive/MyDrive/PDFs")
        >>> print(structure)
    """
    if not os.path.exists(root_path):
        return f"Path does not exist: {root_path}"
    
    lines = [f"Folder structure: {root_path}"]
    lines.append("=" * 60)
    
    def _walk_tree(path: str, prefix: str = "", depth: int = 0):
        if depth > max_depth:
            return
        
        try:
            items = sorted(os.listdir(path))
        except PermissionError:
            lines.append(f"{prefix}[Permission Denied]")
            return
        
        # Separate folders and files
        folders = [item for item in items if os.path.isdir(os.path.join(path, item))]
        files = [item for item in items if os.path.isfile(os.path.join(path, item))]
        
        # Display folders
        for i, folder in enumerate(folders):
            is_last_folder = (i == len(folders) - 1) and (not show_files or not files)
            connector = "└── " if is_last_folder else "├── "
            lines.append(f"{prefix}{connector}📁 {folder}/")
            
            # Recursively display subfolders
            extension = "    " if is_last_folder else "│   "
            folder_path = os.path.join(path, folder)
            _walk_tree(folder_path, prefix + extension, depth + 1)
        
        # Display files if requested
        if show_files:
            for i, file in enumerate(files):
                is_last = i == len(files) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}📄 {file}")
    
    _walk_tree(root_path)
    return "\n".join(lines)


# =============================================================================
# Step 2.2: PDF Discovery
# =============================================================================

def resolve_folder_path(
    drive_folder_path: str,
    mount_point: str = "/content/drive"
) -> str:
    """
    Resolve relative folder path to absolute path.
    
    Args:
        drive_folder_path: Relative path from MyDrive (e.g., "PDFs" or "Research/Papers")
        mount_point: Google Drive mount point
        
    Returns:
        Absolute path to the folder
        
    Raises:
        ValueError: If the resolved path doesn't exist
        
    Example:
        >>> abs_path = resolve_folder_path("PDFs")
        >>> print(abs_path)  # /content/drive/MyDrive/PDFs
    """
    # Remove leading/trailing slashes
    drive_folder_path = drive_folder_path.strip("/")
    
    # Build absolute path
    my_drive = os.path.join(mount_point, "MyDrive")
    abs_path = os.path.join(my_drive, drive_folder_path)
    
    # Normalize path
    abs_path = os.path.normpath(abs_path)
    
    # Validate path exists
    if not os.path.exists(abs_path):
        raise ValueError(f"Folder does not exist: {abs_path}")
    
    if not os.path.isdir(abs_path):
        raise ValueError(f"Path is not a directory: {abs_path}")
    
    return abs_path


def generate_paper_id(file_path: str) -> str:
    """
    Generate unique paper ID from file path.
    
    Uses SHA-256 hash of the canonical file path to ensure:
    - Deterministic IDs (same file always gets same ID)
    - Uniqueness (different files get different IDs)
    
    Args:
        file_path: Absolute or relative file path
        
    Returns:
        16-character hex string as paper ID
        
    Example:
        >>> paper_id = generate_paper_id("/path/to/paper.pdf")
        >>> len(paper_id)
        16
    """
    # Use canonical path for consistency
    canonical_path = os.path.normpath(os.path.abspath(file_path))
    return IDGenerator.generate_paper_id(canonical_path)


def discover_pdfs(
    drive_folder_path: str,
    config: RunConfig,
    mount_point: str = "/content/drive",
    show_progress: bool = True
) -> Dict[str, PaperRecord]:
    """
    Recursively discover all PDF files in a Google Drive folder.
    
    This function:
    1. Resolves the absolute folder path
    2. Recursively walks the folder tree
    3. Finds all .pdf files
    4. Generates unique paper IDs
    5. Creates initial PaperRecord entries
    6. Handles duplicate files
    7. Reports progress
    
    Args:
        drive_folder_path: Relative path from MyDrive (from RunConfig)
        config: RunConfig with processing limits and settings
        mount_point: Google Drive mount point
        show_progress: If True, show progress bar
        
    Returns:
        Dictionary mapping paper_id -> PaperRecord
        
    Example:
        >>> config = RunConfig(drive_folder_path="PDFs")
        >>> papers = discover_pdfs("PDFs", config)
        >>> print(f"Found {len(papers)} papers")
    """
    # Resolve absolute path
    try:
        abs_folder_path = resolve_folder_path(drive_folder_path, mount_point)
    except ValueError as e:
        logger.error(f"Failed to resolve folder path: {e}")
        return {}
    
    logger.info(f"Discovering PDFs in: {abs_folder_path}")
    
    # Find all PDF files
    pdf_files = []
    for root, dirs, files in os.walk(abs_folder_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                file_path = os.path.join(root, file)
                pdf_files.append(file_path)
    
    logger.info(f"Found {len(pdf_files)} PDF files")
    
    # Apply max_papers limit if specified
    if config.max_papers_per_run is not None:
        pdf_files = pdf_files[:config.max_papers_per_run]
        logger.info(f"Limited to {len(pdf_files)} papers (max_papers_per_run={config.max_papers_per_run})")
    
    # Create PaperRecord entries
    papers = {}
    duplicates = []
    
    # Set up progress bar
    iterator = pdf_files
    if show_progress and tqdm is not None:
        iterator = tqdm(pdf_files, desc="Discovering PDFs")
    
    for file_path in iterator:
        try:
            # Generate paper ID
            paper_id = generate_paper_id(file_path)
            
            # Check for duplicates
            if paper_id in papers:
                duplicates.append({
                    'paper_id': paper_id,
                    'existing_path': papers[paper_id].file_path,
                    'duplicate_path': file_path
                })
                logger.warning(f"Duplicate file detected: {file_path}")
                continue
            
            # Create initial PaperRecord
            paper = _create_initial_paper_record(file_path, paper_id, abs_folder_path)
            papers[paper_id] = paper
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            continue
    
    # Log duplicate handling results
    if duplicates:
        logger.warning(f"Found {len(duplicates)} duplicate files (kept first occurrence)")
        for dup in duplicates[:5]:  # Log first 5
            logger.warning(f"  - {dup['duplicate_path']}")
        if len(duplicates) > 5:
            logger.warning(f"  ... and {len(duplicates) - 5} more")
    
    # Log statistics
    _log_discovery_statistics(papers, abs_folder_path)
    
    return papers


def _create_initial_paper_record(
    file_path: str,
    paper_id: str,
    source_folder: str
) -> PaperRecord:
    """
    Create initial PaperRecord for a discovered PDF.
    
    Args:
        file_path: Absolute path to PDF file
        paper_id: Generated paper ID
        source_folder: Source folder path
        
    Returns:
        PaperRecord with initial metadata
    """
    filename = os.path.basename(file_path)
    
    return PaperRecord(
        id=paper_id,
        file_path=file_path,
        filename=filename,
        source_folder=source_folder,
        processing_status="pending"
    )


def _log_discovery_statistics(papers: Dict[str, PaperRecord], folder_path: str):
    """Log statistics about discovered papers."""
    if not papers:
        logger.info("No papers discovered")
        return
    
    # Calculate file sizes
    total_size = 0
    sizes = []
    for paper in papers.values():
        try:
            size = os.path.getsize(paper.file_path)
            sizes.append(size)
            total_size += size
        except OSError as e:
            logger.warning(f"Could not get size for file '{paper.file_path}': {e}")
    
    # Log statistics
    logger.info("=" * 60)
    logger.info("PDF Discovery Statistics")
    logger.info("=" * 60)
    logger.info(f"Folder: {folder_path}")
    logger.info(f"Total PDFs discovered: {len(papers)}")
    
    if sizes:
        avg_size = total_size / len(sizes)
        min_size = min(sizes)
        max_size = max(sizes)
        
        logger.info(f"Total size: {_format_bytes(total_size)}")
        logger.info(f"Average size: {_format_bytes(avg_size)}")
        logger.info(f"Size range: {_format_bytes(min_size)} - {_format_bytes(max_size)}")
    
    logger.info("=" * 60)


def _format_bytes(size: int) -> str:
    """Format byte size as human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def handle_duplicates(
    papers: Dict[str, PaperRecord],
    strategy: str = "keep_first"
) -> Tuple[Dict[str, PaperRecord], List[Dict[str, str]]]:
    """
    Handle duplicate PDF files.
    
    Duplicates are identified by having the same paper_id (hash of file path).
    This shouldn't normally happen in the discover_pdfs function, but this
    utility can be used if papers are discovered from multiple sources.
    
    Args:
        papers: Dictionary of paper_id -> PaperRecord
        strategy: Duplicate handling strategy:
            - "keep_first": Keep first occurrence (default)
            - "keep_shortest_path": Keep file with shortest path
            - "keep_newest": Keep most recently modified file
            
    Returns:
        Tuple of (deduplicated_papers, duplicate_records)
        
    Example:
        >>> papers, duplicates = handle_duplicates(papers, "keep_first")
        >>> print(f"Removed {len(duplicates)} duplicates")
    """
    # This is a placeholder for future enhancement
    # The discover_pdfs function already handles duplicates
    return papers, []


# =============================================================================
# Step 2.3: File Management Utilities
# =============================================================================

def validate_file_access(file_path: str) -> Dict[str, Any]:
    """
    Validate that a file exists and is accessible.
    
    Args:
        file_path: Path to file to validate
        
    Returns:
        Dictionary with validation results:
            - exists: bool
            - is_file: bool
            - readable: bool
            - size_bytes: Optional[int]
            - error: Optional[str]
            
    Example:
        >>> result = validate_file_access("/path/to/paper.pdf")
        >>> if result['readable']:
        ...     print(f"File is accessible ({result['size_bytes']} bytes)")
    """
    result = {
        'exists': False,
        'is_file': False,
        'readable': False,
        'size_bytes': None,
        'error': None
    }
    
    # Check if path exists
    if not os.path.exists(file_path):
        result['error'] = f"File does not exist: {file_path}"
        return result
    
    result['exists'] = True
    
    # Check if it's a file
    if not os.path.isfile(file_path):
        result['error'] = f"Path is not a file: {file_path}"
        return result
    
    result['is_file'] = True
    
    # Check if readable
    if not os.access(file_path, os.R_OK):
        result['error'] = f"File is not readable: {file_path}"
        return result
    
    result['readable'] = True
    
    # Get file size
    try:
        result['size_bytes'] = os.path.getsize(file_path)
    except OSError as e:
        result['error'] = f"Could not get file size: {e}"
    
    return result


def check_disk_space(path: str = "/content") -> Dict[str, Any]:
    """
    Check available disk space at a given path.
    
    Args:
        path: Path to check (default: /content for Colab)
        
    Returns:
        Dictionary with disk space information:
            - total_bytes: int
            - used_bytes: int
            - free_bytes: int
            - percent_used: float
            - total_gb: float
            - free_gb: float
            - warning: Optional[str]
            
    Example:
        >>> space = check_disk_space()
        >>> print(f"Free space: {space['free_gb']:.2f} GB")
    """
    try:
        stat = shutil.disk_usage(path)
        
        result = {
            'total_bytes': stat.total,
            'used_bytes': stat.used,
            'free_bytes': stat.free,
            'percent_used': (stat.used / stat.total * 100) if stat.total > 0 else 0,
            'total_gb': stat.total / (1024**3),
            'free_gb': stat.free / (1024**3),
            'warning': None
        }
        
        # Add warning if space is low
        if result['free_gb'] < 1.0:
            result['warning'] = f"Low disk space: only {result['free_gb']:.2f} GB free"
        elif result['percent_used'] > 90:
            result['warning'] = f"Disk {result['percent_used']:.1f}% full"
        
        return result
        
    except Exception as e:
        return {
            'error': f"Could not check disk space: {e}",
            'total_bytes': 0,
            'used_bytes': 0,
            'free_bytes': 0,
            'percent_used': 0,
            'total_gb': 0,
            'free_gb': 0,
            'warning': None
        }


def sanitize_file_path(file_path: str) -> str:
    """
    Sanitize and normalize a file path.
    
    This function:
    - Normalizes path separators
    - Resolves . and .. references
    - Removes redundant separators
    - Expands user home directory (~)
    
    Args:
        file_path: Raw file path
        
    Returns:
        Sanitized file path
        
    Example:
        >>> sanitized = sanitize_file_path("~/PDFs/../Papers/./paper.pdf")
        >>> print(sanitized)  # /home/user/Papers/paper.pdf
    """
    # Expand user home directory
    path = os.path.expanduser(file_path)
    
    # Normalize path (resolve .., ., remove redundant separators)
    path = os.path.normpath(path)
    
    # Convert to absolute path
    path = os.path.abspath(path)
    
    return path


def validate_pdf_file(file_path: str) -> Dict[str, Any]:
    """
    Validate that a file is a valid PDF.
    
    Performs basic validation:
    - File exists and is readable
    - File has .pdf extension
    - File starts with PDF magic bytes (%PDF-)
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Dictionary with validation results:
            - valid: bool
            - exists: bool
            - readable: bool
            - has_pdf_extension: bool
            - has_pdf_header: bool
            - size_bytes: Optional[int]
            - error: Optional[str]
            
    Example:
        >>> result = validate_pdf_file("/path/to/paper.pdf")
        >>> if result['valid']:
        ...     print("Valid PDF file")
    """
    result = {
        'valid': False,
        'exists': False,
        'readable': False,
        'has_pdf_extension': False,
        'has_pdf_header': False,
        'size_bytes': None,
        'error': None
    }
    
    # Check file access
    access_result = validate_file_access(file_path)
    result.update({
        'exists': access_result['exists'],
        'readable': access_result['readable'],
        'size_bytes': access_result.get('size_bytes')
    })
    
    if not access_result['readable']:
        result['error'] = access_result.get('error', 'File not accessible')
        return result
    
    # Check extension
    if file_path.lower().endswith('.pdf'):
        result['has_pdf_extension'] = True
    else:
        result['error'] = "File does not have .pdf extension"
    
    # Check PDF header (magic bytes)
    try:
        with open(file_path, 'rb') as f:
            header = f.read(5)
            if header == b'%PDF-':
                result['has_pdf_header'] = True
            else:
                result['error'] = "File does not have PDF header"
    except Exception as e:
        result['error'] = f"Could not read file header: {e}"
        return result
    
    # File is valid if it has extension and header
    result['valid'] = result['has_pdf_extension'] and result['has_pdf_header']
    
    return result


# =============================================================================
# Utility Functions
# =============================================================================

def get_mount_info() -> Dict[str, Any]:
    """
    Get information about the current Google Drive mount.
    
    Returns:
        Dictionary with mount information or None if not mounted
    """
    mount_point = "/content/drive"
    
    if not os.path.ismount(mount_point):
        return {
            'mounted': False,
            'mount_point': mount_point,
            'message': 'Google Drive is not mounted'
        }
    
    validation = validate_mount(mount_point)
    return validation


def list_pdfs_in_folder(folder_path: str, recursive: bool = True) -> List[str]:
    """
    List all PDF files in a folder.
    
    Args:
        folder_path: Path to folder
        recursive: If True, search recursively
        
    Returns:
        List of absolute paths to PDF files
    """
    pdf_files = []
    
    if recursive:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(folder_path):
            if file.lower().endswith('.pdf'):
                full_path = os.path.join(folder_path, file)
                if os.path.isfile(full_path):
                    pdf_files.append(full_path)
    
    return sorted(pdf_files)
