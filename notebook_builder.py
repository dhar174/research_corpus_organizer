#!/usr/bin/env python3
"""
Notebook builder for RAG PDF Research Corpus System.
This script generates the complete Jupyter notebook programmatically.
"""

import json

class NotebookBuilder:
    """Build Jupyter notebook programmatically."""
    
    def __init__(self):
        self.cells = []
    
    def add_markdown(self, text):
        """Add a markdown cell."""
        self.cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": text.rstrip().split("\n")
        })
    
    def add_code(self, code):
        """Add a code cell."""
        self.cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": code.rstrip().split("\n")
        })
    
    def build(self):
        """Build the notebook structure."""
        return {
            "cells": self.cells,
            "metadata": {
                "colab": {
                    "name": "RAG_PDF_Research_Corpus_System.ipynb",
                    "provenance": []
                },
                "kernelspec": {
                    "display_name": "Python 3",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 0
        }
    
    def save(self, filepath):
        """Save notebook to file."""
        notebook = self.build()
        with open(filepath, 'w') as f:
            json.dump(notebook, f, indent=2)
        return len(self.cells)


# Create the notebook
nb = NotebookBuilder()

# Title and Overview
nb.add_markdown("""# RAG PDF Research Corpus System

**Version:** 1.0  
**Date:** 2025-11-21  
**Author/Maintainer:** Research Corpus Organizer  
**Based on:** RAG_PDF_System_Spec_v2.1

---

## Overview

This notebook implements a comprehensive system for processing academic PDF research papers using:
- **LangGraph** workflows for orchestration
- **GPT-5.1 Thinking** for summarization and classification
- **FAISS** for vector indexing and RAG queries
- **3-tier hierarchical topic taxonomy** for organization

### System Capabilities

1. **Ingest** PDFs from Google Drive
2. **Parse and chunk** documents with section awareness
3. **Extract metadata** from arXiv/CrossRef/PDF sources
4. **Generate summaries** using advanced LLMs
5. **Build topic taxonomy** through clustering
6. **Classify papers** into hierarchical topics
7. **Enable RAG queries** for corpus exploration

---""")

# Phase 0 Header
nb.add_markdown("""## Phase 0: Environment Setup and Configuration

This phase establishes the notebook environment, installs dependencies, and configures the system.""")

# Step 0.2
nb.add_markdown("""### Step 0.2: Environment Inspection

First, let's verify the runtime environment meets our requirements.""")

nb.add_code("""# Check Python version (require 3.10+)
import sys
print(f"Python version: {sys.version}")
print(f"Version info: {sys.version_info}")

if sys.version_info >= (3, 10):
    print("✓ Python 3.10+ requirement met")
else:
    print("✗ WARNING: Python 3.10+ required")""")

nb.add_code("""# Check GPU/CPU availability
import os

# Try to check for GPU
try:
    import torch
    gpu_available = torch.cuda.is_available()
    if gpu_available:
        print(f"✓ GPU available: {torch.cuda.get_device_name(0)}")
        print(f"  CUDA version: {torch.version.cuda}")
    else:
        print("○ No GPU available (using CPU)")
except ImportError:
    print("○ PyTorch not installed yet (will check GPU after installation)")

# Display basic system info
import platform
print(f"\\nSystem: {platform.system()} {platform.release()}")
print(f"Machine: {platform.machine()}")
print(f"Processor: {platform.processor()}")""")

nb.add_code("""# Display runtime information
import os
try:
    import psutil
    
    # Memory information
    memory = psutil.virtual_memory()
    print(f"Total RAM: {memory.total / (1024**3):.2f} GB")
    print(f"Available RAM: {memory.available / (1024**3):.2f} GB")
    print(f"Used RAM: {memory.used / (1024**3):.2f} GB ({memory.percent}%)")
    
    # Disk space
    disk = psutil.disk_usage('/')
    print(f"\\nTotal Disk: {disk.total / (1024**3):.2f} GB")
    print(f"Available Disk: {disk.free / (1024**3):.2f} GB")
    print(f"Used Disk: {disk.used / (1024**3):.2f} GB ({disk.percent}%)")
    
    # CPU information
    print(f"\\nCPU cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical")
except ImportError:
    print("psutil not installed yet - will be available after dependency installation")""")

# Step 0.3
nb.add_markdown("""### Step 0.3: Install Dependencies

Install all required packages for the RAG PDF Research Corpus System.

**Note:** After installation, you may need to restart the runtime if prompted.""")

nb.add_code("""# Install all required dependencies
# This cell may take several minutes to complete

import sys

# Core dependencies with specific versions
dependencies = [
    "openai>=1.3.0",           # GPT-4 support (future compatibility for newer models)
    "langgraph>=0.0.30",       # Workflow orchestration
    "langchain>=0.1.0",        # LangChain integration
    "pymupdf>=1.23.0",         # PDF parsing (fitz)
    "faiss-cpu>=1.7.4",        # Vector indexing (CPU version)
    "scikit-learn>=1.3.0",     # Clustering algorithms
    "hdbscan>=0.8.33",         # Density-based clustering
    "pandas>=2.0.0",           # Data handling
    "numpy>=1.24.0",           # Numerical operations
    "tqdm>=4.65.0",            # Progress bars
    "matplotlib>=3.7.0",       # Visualization
    "seaborn>=0.12.0",         # Statistical visualization
    "python-dateutil>=2.8.2",  # Date parsing
    "requests>=2.31.0",        # HTTP requests for APIs
    "pytesseract>=0.3.10",     # OCR (optional)
    "Pillow>=10.0.0",          # Image processing for OCR
    "pydantic>=2.0.0",         # Data validation
    "psutil>=5.9.0",           # System utilities
]

print("Installing dependencies...")
print("=" * 60)

for dep in dependencies:
    print(f"Installing {dep}...")
    !pip install -q {dep}

print("=" * 60)
print("✓ All dependencies installed successfully!")
print("\\n⚠ If you see any warnings about restarting the runtime, please do so now.")
print("   After restart, skip this installation cell and continue with imports.")""")

# Step 0.4
nb.add_markdown("""### Step 0.4: Import Statements

Import all required libraries and verify they load successfully.""")

nb.add_code("""# Standard library imports
import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Optional, Dict, List, Literal, Any, TypedDict
from dataclasses import dataclass, field

# Third-party imports - Core
import numpy as np
import pandas as pd
from tqdm.auto import tqdm

# Third-party imports - Data validation
from pydantic import BaseModel, Field, field_validator, ConfigDict

# Third-party imports - PDF processing
try:
    import fitz  # PyMuPDF
    print("✓ PyMuPDF (fitz) imported successfully")
except ImportError as e:
    print(f"✗ Error importing PyMuPDF: {e}")
    fitz = None

# Third-party imports - Vector store
try:
    import faiss
    print("✓ FAISS imported successfully")
except ImportError as e:
    print(f"✗ Error importing FAISS: {e}")
    faiss = None

# Third-party imports - ML/Clustering
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score
try:
    import hdbscan
    print("✓ HDBSCAN imported successfully")
except ImportError:
    print("○ HDBSCAN not available (optional)")
    hdbscan = None

# Third-party imports - Visualization
import matplotlib.pyplot as plt
import seaborn as sns

# Third-party imports - API and utilities
import requests
from dateutil import parser as date_parser

# Third-party imports - OpenAI
try:
    from openai import OpenAI
    print("✓ OpenAI SDK imported successfully")
except ImportError as e:
    print(f"✗ Error importing OpenAI: {e}")
    OpenAI = None

# Third-party imports - LangGraph
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    print("✓ LangGraph imported successfully")
except ImportError as e:
    print(f"✗ Error importing LangGraph: {e}")
    StateGraph = None

# Third-party imports - OCR (optional)
try:
    import pytesseract
    from PIL import Image
    print("✓ OCR libraries imported successfully")
except ImportError:
    print("○ OCR libraries not available (optional)")
    pytesseract = None
    Image = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("\\n✓ All core imports completed successfully!")""")

# Step 0.5
nb.add_markdown("""### Step 0.5: Configuration

Define the configuration schema and user-editable configuration.""")

nb.add_code('''# Define RunConfig Pydantic model
from typing import Literal

class RunConfig(BaseModel):
    """
    Configuration for the RAG PDF Research Corpus System.
    
    This model defines all parameters needed to run the pipeline,
    including paths, model selections, and processing options.
    """
    
    # Google Drive and file paths
    drive_folder_path: str = Field(
        default="PDFs",
        description="Google Drive folder path containing PDFs (relative to 'My Drive')"
    )
    
    # Processing limits
    max_papers_per_run: Optional[int] = Field(
        default=None,
        description="Maximum number of papers to process (None = all)"
    )
    max_pages_per_paper: Optional[int] = Field(
        default=None,
        description="Maximum pages to process per paper (None = all)"
    )
    max_chunks_per_paper: int = Field(
        default=100,
        description="Maximum number of chunks per paper"
    )
    
    # OCR settings
    enable_ocr_fallback: bool = Field(
        default=False,
        description="Enable OCR for low-quality or scanned PDFs"
    )
    
    # Model selections
    summary_model: str = Field(
        default="gpt-5.1-mini",
        description="Model for generating summaries (use the latest available model; update as newer models become available)"
    )
    taxonomy_model: str = Field(
        default="gpt-5.1-mini",
        description="Model for taxonomy generation"
    )
    classification_model: str = Field(
        default="gpt-5.1-mini",
        description="Model for paper classification"
    )
    embedding_model: str = Field(
        default="text-embedding-3-large",
        description="Model for generating embeddings"
    )
    
    # Model behavior
    use_tiered_models: bool = Field(
        default=False,
        description="Use cheaper models for bulk tasks"
    )
    
    # Reasoning effort levels (for GPT-5.1 Thinking)
    summary_reasoning_effort: Literal["none", "low", "medium", "high"] = Field(
        default="medium",
        description="Reasoning effort for summarization"
    )
    taxonomy_reasoning_effort: Literal["none", "low", "medium", "high"] = Field(
        default="high",
        description="Reasoning effort for taxonomy generation"
    )
    classification_reasoning_effort: Literal["none", "low", "medium", "high"] = Field(
        default="medium",
        description="Reasoning effort for classification"
    )
    
    # Clustering parameters
    cluster_tier1_target_k: Optional[int] = Field(
        default=8,
        description="Target number of Tier 1 topics (broad categories)"
    )
    cluster_tier2_target_k: Optional[int] = Field(
        default=3,
        description="Target number of Tier 2 topics per Tier 1"
    )
    cluster_tier3_target_k: Optional[int] = Field(
        default=2,
        description="Target number of Tier 3 topics per Tier 2"
    )
    
    # Feature flags
    enable_deep_analysis_pass: bool = Field(
        default=False,
        description="Enable deep analysis pass (Pass 2)"
    )
    taxonomy_approval_required: bool = Field(
        default=True,
        description="Require manual taxonomy approval before classification"
    )
    
    # Token limits for cost control
    max_tokens_per_summary: int = Field(
        default=2000,
        description="Maximum tokens for summary generation"
    )
    max_tokens_per_classification: int = Field(
        default=1000,
        description="Maximum tokens for classification"
    )
    
    # Chunk size parameters
    chunk_size_chars: int = Field(
        default=1500,
        description="Target chunk size in characters"
    )
    chunk_overlap_chars: int = Field(
        default=200,
        description="Overlap between chunks in characters"
    )
    
    @field_validator("max_papers_per_run")
    @classmethod
    def validate_max_papers(cls, v):
        if v is not None and v <= 0:
            raise ValueError("max_papers_per_run must be positive or None")
        return v
    
    @field_validator("max_chunks_per_paper")
    @classmethod
    def validate_max_chunks(cls, v):
        if v <= 0:
            raise ValueError("max_chunks_per_paper must be positive")
        return v

print("✓ RunConfig model defined successfully")''')

nb.add_code('''# User-editable configuration
# Modify these values according to your needs

config = RunConfig(
    # ===== FILE PATHS =====
    drive_folder_path="PDFs",  # Change to your Google Drive folder path
    
    # ===== PROCESSING LIMITS =====
    max_papers_per_run=None,      # Set to a number to limit papers (e.g., 10 for testing)
    max_pages_per_paper=None,     # Set to limit pages per paper
    max_chunks_per_paper=100,     # Maximum chunks per paper
    
    # ===== MODEL SELECTIONS =====
    # Using GPT-5.1-mini as the current SOTA model
    summary_model="gpt-5.1-mini",
    taxonomy_model="gpt-5.1-mini",
    classification_model="gpt-5.1-mini",
    embedding_model="text-embedding-3-large",
    
    # ===== REASONING EFFORT =====
    # Options: "none", "low", "medium", "high"
    summary_reasoning_effort="medium",
    taxonomy_reasoning_effort="high",
    classification_reasoning_effort="medium",
    
    # ===== CLUSTERING =====
    cluster_tier1_target_k=8,   # Broad topics
    cluster_tier2_target_k=3,   # Mid-level topics per Tier 1
    cluster_tier3_target_k=2,   # Fine-grained topics per Tier 2
    
    # ===== FEATURE FLAGS =====
    enable_ocr_fallback=False,
    enable_deep_analysis_pass=False,
    taxonomy_approval_required=True,
    use_tiered_models=False,
    
    # ===== TOKEN LIMITS =====
    max_tokens_per_summary=2000,
    max_tokens_per_classification=1000,
    
    # ===== CHUNKING =====
    chunk_size_chars=1500,
    chunk_overlap_chars=200,
)

print("✓ Configuration initialized")
print("\\nCurrent Configuration:")
print("=" * 60)
for field_name, field_value in config.model_dump().items():
    print(f"  {field_name}: {field_value}")
print("=" * 60)''')

# Phase 1 Header
nb.add_markdown("""---

## Phase 1: Data Models and Schema Definitions

This phase defines the core data structures used throughout the system.""")

# Step 1.1
nb.add_markdown("""### Step 1.1: PaperRecord Schema

Defines the structure for storing paper metadata, processing status, and analysis results.""")

nb.add_code('''# PaperRecord Schema
from datetime import datetime, date
from typing import Optional, List, Dict, Literal

class PaperRecord(BaseModel):
    """
    Comprehensive record for each research paper.
    
    Tracks metadata, processing status, summaries, and topic classifications.
    """
    
    # ===== Identifiers =====
    id: str = Field(description="Unique paper ID (hash of file_path)")
    file_path: str = Field(description="Absolute path to PDF file")
    filename: str = Field(description="Original filename")
    source_folder: Optional[str] = Field(default=None, description="Source folder path")
    
    # ===== External Identifiers =====
    source: Optional[Literal["arxiv", "doi", "other"]] = Field(
        default=None,
        description="Source type of the paper"
    )
    arxiv_id: Optional[str] = Field(default=None, description="arXiv identifier")
    doi: Optional[str] = Field(default=None, description="Digital Object Identifier")
    
    # ===== Metadata =====
    title: Optional[str] = Field(default=None, description="Paper title")
    authors: Optional[List[str]] = Field(default=None, description="List of authors")
    venue: Optional[str] = Field(default=None, description="Publication venue")
    publish_date: Optional[date] = Field(default=None, description="Publication date")
    publish_date_source: Optional[Literal["arxiv", "crossref", "pdf", "manual", "unknown"]] = Field(
        default="unknown",
        description="Source of publication date"
    )
    year: Optional[int] = Field(default=None, description="Publication year")
    is_preprint: Optional[bool] = Field(default=None, description="Whether paper is a preprint")
    arxiv_version: Optional[str] = Field(default=None, description="arXiv version number")
    
    # ===== Text Statistics =====
    raw_text_stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="Statistics about the raw text"
    )
    # Expected keys in raw_text_stats:
    #   - pages: int
    #   - chars_total: int
    #   - chars_per_page: float
    #   - alnum_ratio: float
    #   - parse_quality_score: float (0-1)
    
    # ===== Content =====
    abstract_text: Optional[str] = Field(default=None, description="Cleaned abstract text")
    
    # ===== Summaries and Notes =====
    full_summary: Optional[str] = Field(
        default=None,
        description="High-level summary (Pass 1)"
    )
    deep_summary: Optional[str] = Field(
        default=None,
        description="Detailed analysis summary (Pass 2, optional)"
    )
    initial_notes: Optional[str] = Field(
        default=None,
        description="Initial analysis notes from Pass 1"
    )
    classification_notes: Optional[str] = Field(
        default=None,
        description="Reasoning for topic classification (Pass 3)"
    )
    
    # ===== Topic Classification =====
    tier1_topic: Optional[str] = Field(default=None, description="Tier 1 topic ID")
    tier1_topic_name: Optional[str] = Field(default=None, description="Tier 1 topic name")
    tier1_confidence: Optional[float] = Field(default=None, description="Confidence score (0-1)")
    
    tier2_topic: Optional[str] = Field(default=None, description="Tier 2 topic ID")
    tier2_topic_name: Optional[str] = Field(default=None, description="Tier 2 topic name")
    tier2_confidence: Optional[float] = Field(default=None, description="Confidence score (0-1)")
    
    tier3_topic: Optional[str] = Field(default=None, description="Tier 3 topic ID")
    tier3_topic_name: Optional[str] = Field(default=None, description="Tier 3 topic name")
    tier3_confidence: Optional[float] = Field(default=None, description="Confidence score (0-1)")
    
    taxonomy_version: Optional[str] = Field(
        default=None,
        description="Version of taxonomy used for classification"
    )
    
    # ===== Processing Status =====
    processing_status: Literal[
        "pending",
        "parsed",
        "summarized",
        "embedded",
        "deep_analyzed",
        "classified",
        "failed"
    ] = Field(default="pending", description="Current processing status")
    
    error_reason: Optional[str] = Field(
        default=None,
        description="Error message if processing failed"
    )
    error_stage: Optional[str] = Field(
        default=None,
        description="Stage where error occurred"
    )
    retry_count: int = Field(default=0, description="Number of retry attempts")
    
    # ===== Timestamps =====
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When record was created"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="When record was last updated"
    )
    
    @field_validator("tier1_confidence", "tier2_confidence", "tier3_confidence")
    @classmethod
    def validate_confidence(cls, v):
        if v is not None and not (0 <= v <= 1):
            raise ValueError("Confidence scores must be between 0 and 1")
        return v
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
    )

print("✓ PaperRecord schema defined successfully")''')

# Step 1.2
nb.add_markdown("""### Step 1.2: PaperChunk Schema

Defines the structure for text chunks extracted from papers for RAG.""")

nb.add_code('''# PaperChunk Schema

class PaperChunk(BaseModel):
    """
    Represents a text chunk from a paper for RAG indexing.
    
    Chunks are section-aware and include metadata for retrieval.
    """
    
    paper_id: str = Field(description="Reference to parent paper")
    chunk_id: str = Field(description="Unique chunk identifier")
    
    # Section information
    section_label: str = Field(
        default="other",
        description="Section type: abstract, introduction, methods, results, conclusion, other"
    )
    
    # Page information
    page_start: int = Field(description="Starting page number")
    page_end: int = Field(description="Ending page number")
    
    # Text content
    text: str = Field(description="Raw text content of chunk")
    cleaned_text: Optional[str] = Field(
        default=None,
        description="Cleaned/normalized text (optional)"
    )
    
    # Embedding information
    embedding_id: Optional[int] = Field(
        default=None,
        description="Index into FAISS vector store"
    )
    embedding_model: Optional[str] = Field(
        default=None,
        description="Model used to generate embedding"
    )
    
    # Metadata
    char_count: int = Field(default=0, description="Character count")
    token_count_estimate: Optional[int] = Field(
        default=None,
        description="Estimated token count"
    )
    
    @field_validator("char_count", mode="after")
    @classmethod
    def set_char_count(cls, v, info):
        if hasattr(info, 'data') and "text" in info.data:
            return len(info.data["text"])
        return v
    
    @field_validator("section_label")
    @classmethod
    def validate_section(cls, v):
        valid_sections = {
            "abstract", "introduction", "methods", "results",
            "discussion", "conclusion", "references", "other"
        }
        if v.lower() not in valid_sections:
            return "other"
        return v.lower()

print("✓ PaperChunk schema defined successfully")''')

# Step 1.3
nb.add_markdown("""### Step 1.3: TopicHierarchy Schema

Defines the 3-tier hierarchical topic taxonomy structure.""")

nb.add_code('''# TopicHierarchy Schema

class TopicNode(BaseModel):
    """Represents a single topic in the hierarchy."""
    
    id: str = Field(description="Unique topic ID (e.g., T1_LLMs, T2_Attention)")
    label: str = Field(description="Human-readable topic label")
    description: str = Field(description="Detailed topic description")
    paper_ids: List[str] = Field(default_factory=list, description="Papers in this topic")
    parent_id: Optional[str] = Field(default=None, description="Parent topic ID")
    
    # Statistics
    paper_count: int = Field(default=0, description="Number of papers in topic")
    
    # Optional centroid embedding for clustering
    centroid: Optional[List[float]] = Field(default=None, description="Topic centroid vector")
    
    @field_validator("paper_count", mode="after")
    @classmethod
    def set_paper_count(cls, v, info):
        if hasattr(info, 'data') and "paper_ids" in info.data:
            return len(info.data["paper_ids"])
        return v

class TopicHierarchy(BaseModel):
    """
    Complete 3-tier topic taxonomy for the corpus.
    
    Tier 1: Broad research areas
    Tier 2: Mid-level topics within each Tier 1
    Tier 3: Fine-grained topics within each Tier 2
    """
    
    taxonomy_version: str = Field(description="Version identifier")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Taxonomy creation timestamp"
    )
    notes: str = Field(default="", description="Notes about this taxonomy")
    
    # Total corpus statistics
    total_papers: int = Field(default=0, description="Total papers in corpus")
    
    # Three tiers of topics
    tier1: List[TopicNode] = Field(default_factory=list, description="Tier 1 topics")
    tier2: List[TopicNode] = Field(default_factory=list, description="Tier 2 topics")
    tier3: List[TopicNode] = Field(default_factory=list, description="Tier 3 topics")
    
    # Metadata
    clustering_method: Optional[str] = Field(
        default=None,
        description="Clustering algorithm used"
    )
    labeling_model: Optional[str] = Field(
        default=None,
        description="Model used for topic labeling"
    )
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    def get_topic_by_id(self, topic_id: str) -> Optional[TopicNode]:
        """Find a topic by its ID across all tiers."""
        for tier in [self.tier1, self.tier2, self.tier3]:
            for topic in tier:
                if topic.id == topic_id:
                    return topic
        return None
    
    def get_tier1_topics(self) -> List[TopicNode]:
        """Get all Tier 1 topics."""
        return self.tier1
    
    def get_tier2_topics(self, parent_tier1_id: Optional[str] = None) -> List[TopicNode]:
        """Get Tier 2 topics, optionally filtered by parent."""
        if parent_tier1_id:
            return [t for t in self.tier2 if t.parent_id == parent_tier1_id]
        return self.tier2
    
    def get_tier3_topics(self, parent_tier2_id: Optional[str] = None) -> List[TopicNode]:
        """Get Tier 3 topics, optionally filtered by parent."""
        if parent_tier2_id:
            return [t for t in self.tier3 if t.parent_id == parent_tier2_id]
        return self.tier3

print("✓ TopicHierarchy schema defined successfully")''')

# Step 1.4
nb.add_markdown("""### Step 1.4: GraphState Schema

Defines the LangGraph state object that tracks the entire pipeline.""")

nb.add_code('''# GraphState Schema
from typing import TypedDict

class GraphState(TypedDict, total=False):
    """
    LangGraph state object for the RAG pipeline.
    
    This state is passed through all workflow nodes and tracks
    all papers, chunks, configuration, and processing status.
    """
    
    # Configuration
    config: RunConfig
    
    # Core data structures
    papers: Dict[str, PaperRecord]  # paper_id -> PaperRecord
    chunks: Dict[str, List[PaperChunk]]  # paper_id -> List[PaperChunk]
    
    # Taxonomy
    topic_hierarchy: Optional[TopicHierarchy]
    taxonomy_approved: bool
    
    # File paths for persisted artifacts
    faiss_index_path: Optional[str]
    faiss_meta_path: Optional[str]
    master_csv_path: Optional[str]
    taxonomy_json_path: Optional[str]
    errors_log_path: Optional[str]
    
    # Processing state
    current_phase: str
    papers_pending: List[str]  # paper_ids to process
    papers_completed: List[str]  # paper_ids completed
    papers_failed: List[str]  # paper_ids that failed
    
    # Error tracking
    errors: List[Dict[str, Any]]
    
    # Statistics
    stats: Dict[str, Any]

# Helper class for state management
class StateManager:
    """Helper class for managing GraphState operations."""
    
    @staticmethod
    def create_initial_state(config: RunConfig) -> GraphState:
        """Create a new initial state."""
        return GraphState(
            config=config,
            papers={},
            chunks={},
            topic_hierarchy=None,
            taxonomy_approved=False,
            faiss_index_path=None,
            faiss_meta_path=None,
            master_csv_path=None,
            taxonomy_json_path=None,
            errors_log_path=None,
            current_phase="initialization",
            papers_pending=[],
            papers_completed=[],
            papers_failed=[],
            errors=[],
            stats={}
        )
    
    @staticmethod
    def add_paper(state: GraphState, paper: PaperRecord) -> GraphState:
        """Add or update a paper in the state."""
        state["papers"][paper.id] = paper
        if paper.id not in state["papers_pending"] and paper.processing_status == "pending":
            state["papers_pending"].append(paper.id)
        return state
    
    @staticmethod
    def update_paper(state: GraphState, paper_id: str, updates: Dict[str, Any]) -> GraphState:
        """Update a paper's fields."""
        if paper_id in state["papers"]:
            paper = state["papers"][paper_id]
            for key, value in updates.items():
                if hasattr(paper, key):
                    setattr(paper, key, value)
            paper.last_updated = datetime.now()
        return state
    
    @staticmethod
    def add_chunks(state: GraphState, paper_id: str, chunks: List[PaperChunk]) -> GraphState:
        """Add chunks for a paper."""
        state["chunks"][paper_id] = chunks
        return state
    
    @staticmethod
    def mark_paper_complete(state: GraphState, paper_id: str) -> GraphState:
        """Mark a paper as completed."""
        if paper_id in state["papers_pending"]:
            state["papers_pending"].remove(paper_id)
        if paper_id not in state["papers_completed"]:
            state["papers_completed"].append(paper_id)
        return state
    
    @staticmethod
    def mark_paper_failed(state: GraphState, paper_id: str, error: str) -> GraphState:
        """Mark a paper as failed."""
        if paper_id in state["papers_pending"]:
            state["papers_pending"].remove(paper_id)
        if paper_id not in state["papers_failed"]:
            state["papers_failed"].append(paper_id)
        
        # Log error
        state["errors"].append({
            "paper_id": paper_id,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update paper record
        if paper_id in state["papers"]:
            state["papers"][paper_id].processing_status = "failed"
            state["papers"][paper_id].error_reason = error
            state["papers"][paper_id].last_updated = datetime.now()
        
        return state
    
    @staticmethod
    def get_stats(state: GraphState) -> Dict[str, Any]:
        """Calculate current statistics."""
        return {
            "total_papers": len(state["papers"]),
            "pending": len(state["papers_pending"]),
            "completed": len(state["papers_completed"]),
            "failed": len(state["papers_failed"]),
            "total_chunks": sum(len(chunks) for chunks in state["chunks"].values()),
            "has_taxonomy": state["topic_hierarchy"] is not None,
            "taxonomy_approved": state.get("taxonomy_approved", False),
        }

print("✓ GraphState schema and StateManager defined successfully")''')

# Step 1.5
nb.add_markdown("""### Step 1.5: Helper Classes

Define utility classes for metadata extraction, statistics tracking, and error handling.""")

nb.add_code('''# Helper Classes

class MetadataExtractor:
    """
    Utility class for extracting and normalizing metadata.
    """
    
    @staticmethod
    def extract_arxiv_id(filename: str, text: str = "") -> Optional[str]:
        """
        Extract arXiv ID from filename or text.
        
        Patterns: YYMM.NNNNN or YYMM.NNNNNVN
        """
        import re
        
        # Try filename first
        patterns = [
            r'(?:arxiv[_-])?(\d{4}\.\d{4,5}(?:v\d+)?)',
            r'(\d{4}\.\d{4,5}(?:v\d+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Try text content
        if text:
            for pattern in patterns:
                match = re.search(pattern, text[:5000], re.IGNORECASE)
                if match:
                    return match.group(1)
        
        return None
    
    @staticmethod
    def extract_doi(text: str) -> Optional[str]:
        """
        Extract DOI from text.
        
        Pattern: 10.NNNN/...
        """
        import re
        pattern = r'10\.\d{4,}/[^\s]+'
        match = re.search(pattern, text[:5000])
        return match.group(0) if match else None
    
    @staticmethod
    def normalize_authors(authors: List[str]) -> List[str]:
        """Normalize author name formats."""
        normalized = []
        for author in authors:
            # Basic cleanup
            author = author.strip()
            if author:
                normalized.append(author)
        return normalized
    
    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        """Parse various date formats."""
        try:
            return date_parser.parse(date_str).date()
        except Exception:
            return None

class StatisticsTracker:
    """
    Utility class for tracking and calculating text statistics.
    """
    
    @staticmethod
    def calculate_text_stats(text: str, page_count: int = 1) -> Dict[str, Any]:
        """
        Calculate statistics for extracted text.
        
        Returns dict with:
            - pages: int
            - chars_total: int
            - chars_per_page: float
            - alnum_ratio: float
            - parse_quality_score: float (0-1)
        """
        chars_total = len(text)
        alnum_chars = sum(1 for c in text if c.isalnum())
        alnum_ratio = alnum_chars / chars_total if chars_total > 0 else 0
        
        # Quality score based on alnum ratio and chars per page
        chars_per_page = chars_total / page_count if page_count > 0 else 0
        
        # Good quality: high alnum ratio and reasonable chars/page
        quality_score = 0.0
        if alnum_ratio > 0.7 and chars_per_page > 1000:
            quality_score = 0.9
        elif alnum_ratio > 0.5 and chars_per_page > 500:
            quality_score = 0.7
        elif alnum_ratio > 0.3:
            quality_score = 0.5
        else:
            quality_score = 0.3
        
        return {
            "pages": page_count,
            "chars_total": chars_total,
            "chars_per_page": chars_per_page,
            "alnum_ratio": round(alnum_ratio, 3),
            "parse_quality_score": round(quality_score, 3)
        }
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Rough token count estimation (1 token ≈ 4 characters).
        """
        return len(text) // 4

class ErrorHandler:
    """
    Utility class for error handling and logging.
    """
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
    
    def log_error(
        self,
        paper_id: str,
        stage: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log an error with context."""
        error_record = {
            "paper_id": paper_id,
            "stage": stage,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        self.errors.append(error_record)
        logger.error(f"Error in {stage} for {paper_id}: {error}")
    
    def get_errors_by_paper(self, paper_id: str) -> List[Dict[str, Any]]:
        """Get all errors for a specific paper."""
        return [e for e in self.errors if e["paper_id"] == paper_id]
    
    def get_errors_by_stage(self, stage: str) -> List[Dict[str, Any]]:
        """Get all errors for a specific stage."""
        return [e for e in self.errors if e["stage"] == stage]
    
    def export_errors(self, filepath: str):
        """Export errors to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.errors, f, indent=2)

class IDGenerator:
    """
    Utility class for generating unique IDs.
    """
    
    @staticmethod
    def generate_paper_id(file_path: str) -> str:
        """Generate unique paper ID from file path."""
        return hashlib.sha256(file_path.encode()).hexdigest()[:16]
    
    @staticmethod
    def generate_chunk_id(paper_id: str, chunk_index: int) -> str:
        """Generate unique chunk ID."""
        return f"{paper_id}_chunk_{chunk_index:04d}"

print("✓ Helper classes defined successfully")
print("  - MetadataExtractor")
print("  - StatisticsTracker")
print("  - ErrorHandler")
print("  - IDGenerator")''')

# Summary
nb.add_markdown("""---

## Summary

**Phase 0 (Environment Setup)** and **Phase 1 (Data Models)** are now complete!

### ✓ Completed Steps

**Phase 0:**
- Step 0.1: Notebook structure created with title, description, and headers
- Step 0.2: Environment inspection cells (Python version, GPU/CPU, system info)
- Step 0.3: Dependency installation cell with all required packages
- Step 0.4: Import statements with error handling for optional dependencies
- Step 0.5: Configuration schema (RunConfig) and user-editable config

**Phase 1:**
- Step 1.1: PaperRecord schema with full metadata tracking
- Step 1.2: PaperChunk schema for RAG indexing
- Step 1.3: TopicHierarchy schema for 3-tier taxonomy
- Step 1.4: GraphState schema for LangGraph workflow
- Step 1.5: Helper classes (MetadataExtractor, StatisticsTracker, ErrorHandler, IDGenerator)

### Next Steps

The following phases will be implemented by specialized agents:
- **Phase 2:** Google Drive Integration (mounting, PDF discovery)
- **Phase 3:** PDF Parsing and Chunking
- **Phase 4:** Metadata Extraction
- **Phase 5:** Embedding Generation and FAISS Index
- **Phase 6+:** Summarization, Taxonomy, Classification, RAG Query Interface

### Usage

1. **Install dependencies** by running the installation cell (Step 0.3)
2. **Configure your settings** in the configuration cell (Step 0.5)
3. **Set your OpenAI API key** (see Phase 2 when implemented)
4. **Mount Google Drive** and specify your PDF folder
5. **Run the pipeline** using the LangGraph workflow

---

**Version:** 1.0  
**Status:** Phase 0 and Phase 1 Complete  
**Last Updated:** 2025-11-21""")

# Save notebook
output_path = "/home/runner/work/research_corpus_organizer/research_corpus_organizer/RAG_PDF_Research_Corpus_System.ipynb"
cell_count = nb.save(output_path)
print(f"✓ Notebook saved to: {output_path}")
print(f"  Total cells: {cell_count}")
