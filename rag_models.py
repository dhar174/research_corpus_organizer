"""
RAG PDF Research Corpus System - Data Models and Schemas

This module defines all core data structures for the RAG PDF pipeline:
- RunConfig: System configuration
- PaperRecord: Paper metadata and processing status
- PaperChunk: Text chunks for RAG indexing
- TopicHierarchy: 3-tier topic taxonomy
- GraphState: LangGraph workflow state
- Helper classes for metadata, statistics, and error handling

Version: 1.0
Date: 2025-11-21
"""

from datetime import datetime, date
from typing import Optional, Dict, List, Literal, Any, TypedDict
from pydantic import BaseModel, Field, field_validator, ConfigDict
import hashlib
import logging
import json

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration Schema
# =============================================================================

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
        default="gpt-4-turbo-preview",
        description="Model for generating summaries (use the latest available model; update as newer models become available)"
    )
    taxonomy_model: str = Field(
        default="gpt-4-turbo-preview",
        description="Model for taxonomy generation"
    )
    classification_model: str = Field(
        default="gpt-4-turbo-preview",
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


# =============================================================================
# Paper Record Schema
# =============================================================================

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


# =============================================================================
# Paper Chunk Schema
# =============================================================================

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


# =============================================================================
# Topic Hierarchy Schema
# =============================================================================

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


# =============================================================================
# Graph State Schema
# =============================================================================

class GraphState(TypedDict, total=False):
    """
    LangGraph state object for the RAG pipeline.
    
    This state is passed through all workflow nodes and tracks
    all papers, chunks, configuration, and processing status.
    """
    
    # Configuration
    config: RunConfig
    
    # Core data structures
    papers: Dict[str, PaperRecord]
    chunks: Dict[str, List[PaperChunk]]
    
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
    papers_pending: List[str]
    papers_completed: List[str]
    papers_failed: List[str]
    
    # Error tracking
    errors: List[Dict[str, Any]]
    
    # Statistics
    stats: Dict[str, Any]


# =============================================================================
# State Manager
# =============================================================================

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


# =============================================================================
# Helper Classes
# =============================================================================

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
        from dateutil import parser as date_parser
        from dateutil.parser import ParserError
        try:
            return date_parser.parse(date_str).date()
        except (ParserError, ValueError, TypeError):
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
