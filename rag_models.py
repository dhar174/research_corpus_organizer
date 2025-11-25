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
from typing import Optional, Dict, List, Literal, Any, TypedDict, Callable
from pydantic import BaseModel, Field, field_validator, ConfigDict
import hashlib
import logging
import json

logger = logging.getLogger(__name__)

# Export list for clean imports
__all__ = [
    # Configuration
    'RunConfig',
    'create_default_config',
    
    # Core Models
    'PaperRecord',
    'PaperChunk',
    'TopicNode',
    'TopicHierarchy',
    'GraphState',
    
    # State Management
    'StateManager',
    
    # Helper Classes
    'MetadataExtractor',
    'StatisticsTracker',
    'ErrorHandler',
    'IDGenerator',
    
    # Cost Tracking (Phase 17)
    'CostTracker',
    'APICallRecord',
    'CostReport',
    'BudgetExceededError',
    
    # Error Handling & Retry (Phase 18)
    'APIError',
    'RateLimitError',
    'QuotaExceededError',
    'TransientAPIError',
    'RetryHandler',
    'ValidationError',
    'PDFValidationError',
    'DataValidator',
    
    # Utility Functions
    'validate_paper_record',
    'export_papers_to_csv',
    'load_papers_from_csv',
]


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
        default="gpt-5-mini",
        description="Model for generating summaries (use the latest available model; update as newer models become available)"
    )
    taxonomy_model: str = Field(
        default="gpt-5-mini",
        description="Model for taxonomy generation"
    )
    classification_model: str = Field(
        default="gpt-5-mini",
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
    
    # Budget and cost control (Phase 17)
    max_cost_per_run: Optional[float] = Field(
        default=None,
        description="Maximum cost per run in USD (None = no limit)"
    )
    cost_warning_threshold: float = Field(
        default=0.8,
        description="Warn when cost reaches this fraction of max_cost_per_run (0.0-1.0)"
    )
    enable_cost_tracking: bool = Field(
        default=True,
        description="Enable cost tracking and reporting"
    )
    enable_result_caching: bool = Field(
        default=True,
        description="Cache API results to avoid duplicate calls"
    )
    batch_api_calls: bool = Field(
        default=True,
        description="Use batch API calls where possible for cost savings"
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
    
    @field_validator("chunk_size_chars", "chunk_overlap_chars")
    @classmethod
    def validate_chunk_params(cls, v):
        if v <= 0:
            raise ValueError("Chunk size parameters must be positive")
        return v
    
    @field_validator("max_tokens_per_summary", "max_tokens_per_classification")
    @classmethod
    def validate_token_limits(cls, v):
        if v <= 0:
            raise ValueError("Token limits must be positive")
        return v
    
    @field_validator("max_cost_per_run")
    @classmethod
    def validate_max_cost(cls, v):
        if v is not None and v <= 0:
            raise ValueError("max_cost_per_run must be positive or None")
        return v
    
    @field_validator("cost_warning_threshold")
    @classmethod
    def validate_cost_threshold(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("cost_warning_threshold must be between 0.0 and 1.0")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert RunConfig to dictionary for serialization.
        
        Returns:
            Dictionary representation with all fields.
        """
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RunConfig':
        """
        Create RunConfig from dictionary.
        
        Args:
            data: Dictionary with configuration data
            
        Returns:
            RunConfig instance
        """
        return cls(**data)
    
    def display_config(self) -> str:
        """
        Get a formatted string representation of the configuration.
        
        Returns:
            Formatted configuration string
        """
        lines = [
            "=" * 60,
            "RAG PDF System Configuration",
            "=" * 60,
            f"Drive folder: {self.drive_folder_path}",
            f"Max papers per run: {self.max_papers_per_run or 'unlimited'}",
            f"Max pages per paper: {self.max_pages_per_paper or 'unlimited'}",
            f"Max chunks per paper: {self.max_chunks_per_paper}",
            "",
            "Models:",
            f"  Summary: {self.summary_model}",
            f"  Taxonomy: {self.taxonomy_model}",
            f"  Classification: {self.classification_model}",
            f"  Embedding: {self.embedding_model}",
            "",
            "Reasoning Effort:",
            f"  Summary: {self.summary_reasoning_effort}",
            f"  Taxonomy: {self.taxonomy_reasoning_effort}",
            f"  Classification: {self.classification_reasoning_effort}",
            "",
            "Clustering:",
            f"  Tier 1 target k: {self.cluster_tier1_target_k}",
            f"  Tier 2 target k: {self.cluster_tier2_target_k}",
            f"  Tier 3 target k: {self.cluster_tier3_target_k}",
            "",
            "Features:",
            f"  OCR fallback: {self.enable_ocr_fallback}",
            f"  Deep analysis: {self.enable_deep_analysis_pass}",
            f"  Taxonomy approval: {self.taxonomy_approval_required}",
            "",
            "Budget & Cost Controls:",
            f"  Max cost per run: ${self.max_cost_per_run if self.max_cost_per_run else 'unlimited'}",
            f"  Cost warning threshold: {self.cost_warning_threshold * 100}%",
            f"  Cost tracking: {self.enable_cost_tracking}",
            f"  Result caching: {self.enable_result_caching}",
            f"  Batch API calls: {self.batch_api_calls}",
            "=" * 60
        ]
        return "\n".join(lines)


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
    
    @field_validator("year")
    @classmethod
    def validate_year(cls, v):
        if v is not None:
            current_year = datetime.now().year
            if not (1900 <= v <= current_year + 1):
                raise ValueError(f"Year must be between 1900 and {current_year + 1}")
        return v
    
    @field_validator("retry_count")
    @classmethod
    def validate_retry_count(cls, v):
        if v < 0:
            raise ValueError("retry_count cannot be negative")
        return v
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert PaperRecord to dictionary for serialization.
        
        Returns:
            Dictionary representation with all fields.
        """
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaperRecord':
        """
        Create PaperRecord from dictionary.
        
        Args:
            data: Dictionary with paper data
            
        Returns:
            PaperRecord instance
        """
        # Handle datetime fields
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('last_updated'), str):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        if isinstance(data.get('publish_date'), str):
            try:
                from dateutil import parser as date_parser
                data['publish_date'] = date_parser.parse(data['publish_date']).date()
            except ModuleNotFoundError:
                # Fallback: try ISO format
                try:
                    data['publish_date'] = datetime.strptime(data['publish_date'], "%Y-%m-%d").date()
                except ValueError as e:
                    raise ValueError(f"Could not parse publish_date '{data['publish_date']}'. "
                                     "Install python-dateutil for more formats.") from e
        return cls(**data)


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
    
    @field_validator("page_start", "page_end")
    @classmethod
    def validate_page_numbers(cls, v):
        if v < 0:
            raise ValueError("Page numbers must be non-negative")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert PaperChunk to dictionary for serialization.
        
        Returns:
            Dictionary representation with all fields.
        """
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaperChunk':
        """
        Create PaperChunk from dictionary.
        
        Args:
            data: Dictionary with chunk data
            
        Returns:
            PaperChunk instance
        """
        return cls(**data)
    
    def get_display_text(self, max_chars: int = 100) -> str:
        """
        Get truncated text for display purposes.
        
        Args:
            max_chars: Maximum characters to return
            
        Returns:
            Truncated text with ellipsis if needed
        """
        text = self.cleaned_text if self.cleaned_text else self.text
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."


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
    
    model_config = ConfigDict(validate_assignment=True)
    
    @field_validator("paper_count", mode="after")
    @classmethod
    def set_paper_count(cls, v, info):
        if hasattr(info, 'data') and "paper_ids" in info.data:
            return len(info.data["paper_ids"])
        return v
    
    def add_paper(self, paper_id: str) -> None:
        """
        Add a paper to this topic.
        
        Args:
            paper_id: ID of paper to add
        """
        if paper_id not in self.paper_ids:
            self.paper_ids.append(paper_id)
            self.paper_count = len(self.paper_ids)
    
    def remove_paper(self, paper_id: str) -> bool:
        """
        Remove a paper from this topic.
        
        Args:
            paper_id: ID of paper to remove
            
        Returns:
            True if paper was removed, False if not found
        """
        if paper_id in self.paper_ids:
            self.paper_ids.remove(paper_id)
            self.paper_count = len(self.paper_ids)
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TopicNode':
        """Create from dictionary."""
        return cls(**data)


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
        },
        validate_assignment=True
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
    
    def add_topic(self, tier: int, topic: TopicNode) -> None:
        """
        Add a topic to the specified tier.
        
        Args:
            tier: Tier number (1, 2, or 3)
            topic: TopicNode to add
            
        Raises:
            ValueError: If tier is invalid
        """
        if tier == 1:
            self.tier1.append(topic)
        elif tier == 2:
            self.tier2.append(topic)
        elif tier == 3:
            self.tier3.append(topic)
        else:
            raise ValueError(f"Invalid tier: {tier}. Must be 1, 2, or 3.")
    
    def validate_hierarchy(self) -> Dict[str, Any]:
        """
        Validate the hierarchy structure.
        
        Returns:
            Dictionary with validation results and any issues found.
        """
        issues = []
        
        # Check parent references in Tier 2
        tier1_ids = {t.id for t in self.tier1}
        for t2 in self.tier2:
            if t2.parent_id and t2.parent_id not in tier1_ids:
                issues.append(f"Tier 2 topic {t2.id} has invalid parent {t2.parent_id}")
        
        # Check parent references in Tier 3
        tier2_ids = {t.id for t in self.tier2}
        for t3 in self.tier3:
            if t3.parent_id and t3.parent_id not in tier2_ids:
                issues.append(f"Tier 3 topic {t3.id} has invalid parent {t3.parent_id}")
        
        # Check for duplicate IDs
        all_ids = [t.id for t in self.tier1 + self.tier2 + self.tier3]
        if len(all_ids) != len(set(all_ids)):
            issues.append("Duplicate topic IDs found")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "tier1_count": len(self.tier1),
            "tier2_count": len(self.tier2),
            "tier3_count": len(self.tier3),
            "total_topics": len(all_ids)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert TopicHierarchy to dictionary for serialization.
        
        Returns:
            Dictionary representation with all fields.
        """
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TopicHierarchy':
        """
        Create TopicHierarchy from dictionary.
        
        Args:
            data: Dictionary with hierarchy data
            
        Returns:
            TopicHierarchy instance
        """
        # Handle datetime fields
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        # Convert tier lists to TopicNode objects
        if 'tier1' in data:
            data['tier1'] = [TopicNode(**t) if isinstance(t, dict) else t for t in data['tier1']]
        if 'tier2' in data:
            data['tier2'] = [TopicNode(**t) if isinstance(t, dict) else t for t in data['tier2']]
        if 'tier3' in data:
            data['tier3'] = [TopicNode(**t) if isinstance(t, dict) else t for t in data['tier3']]
        
        return cls(**data)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the taxonomy.
        
        Returns:
            Dictionary with taxonomy statistics.
        """
        return {
            "taxonomy_version": self.taxonomy_version,
            "created_at": self.created_at.isoformat(),
            "total_papers": self.total_papers,
            "tier1_topics": len(self.tier1),
            "tier2_topics": len(self.tier2),
            "tier3_topics": len(self.tier3),
            "total_topics": len(self.tier1) + len(self.tier2) + len(self.tier3),
            "clustering_method": self.clustering_method,
            "labeling_model": self.labeling_model,
            "avg_papers_per_tier1": sum(t.paper_count for t in self.tier1) / len(self.tier1) if self.tier1 else 0,
            "avg_papers_per_tier2": sum(t.paper_count for t in self.tier2) / len(self.tier2) if self.tier2 else 0,
            "avg_papers_per_tier3": sum(t.paper_count for t in self.tier3) / len(self.tier3) if self.tier3 else 0,
        }


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
    
    # Cost tracking (Phase 17)
    cost_tracker: Optional['CostTracker']
    total_cost: float
    cost_breakdown: Dict[str, float]


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
            stats={},
            cost_tracker=None,  # Will be initialized when needed
            total_cost=0.0,
            cost_breakdown={}
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
    Utility class for error handling and logging (Phase 18: Step 18.1).
    
    Enhanced to support:
    - Comprehensive error logging with context
    - Paper status updates
    - Error categorization and analysis
    - Structured error reporting
    """
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(f"{__name__}.ErrorHandler")
    
    def log_error(
        self,
        paper_id: str,
        stage: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log an error with context.
        
        Args:
            paper_id: ID of the paper where error occurred
            stage: Processing stage where error occurred
            error: Exception object
            context: Additional context information
        """
        error_record = {
            "paper_id": paper_id,
            "stage": stage,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        self.errors.append(error_record)
        self.logger.error(f"Error in {stage} for {paper_id}: {error}")
    
    def update_paper_on_error(
        self,
        paper: PaperRecord,
        stage: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> PaperRecord:
        """
        Update paper record when an error occurs (Phase 18: Step 18.1).
        
        Args:
            paper: PaperRecord to update
            stage: Processing stage where error occurred
            error: Exception object
            context: Additional context
            
        Returns:
            Updated PaperRecord with error information
        """
        # Log the error
        self.log_error(paper.id, stage, error, context)
        
        # Update paper status
        paper.processing_status = "failed"
        paper.error_reason = str(error)
        paper.error_stage = stage
        paper.retry_count += 1
        paper.last_updated = datetime.now()
        
        self.logger.warning(
            f"Paper {paper.id} failed at {stage}: {error} (retry #{paper.retry_count})"
        )
        
        return paper
    
    def get_errors_by_paper(self, paper_id: str) -> List[Dict[str, Any]]:
        """Get all errors for a specific paper."""
        return [e for e in self.errors if e["paper_id"] == paper_id]
    
    def get_errors_by_stage(self, stage: str) -> List[Dict[str, Any]]:
        """Get all errors for a specific stage."""
        return [e for e in self.errors if e["stage"] == stage]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of all errors (Phase 18: Step 18.1).
        
        Returns:
            Dictionary with error statistics and categorization
        """
        if not self.errors:
            return {
                "total_errors": 0,
                "by_stage": {},
                "by_type": {},
                "recent_errors": []
            }
        
        by_stage = {}
        by_type = {}
        
        for error in self.errors:
            stage = error["stage"]
            error_type = error["error_type"]
            
            by_stage[stage] = by_stage.get(stage, 0) + 1
            by_type[error_type] = by_type.get(error_type, 0) + 1
        
        # Get 10 most recent errors
        recent = sorted(self.errors, key=lambda e: e["timestamp"], reverse=True)[:10]
        
        return {
            "total_errors": len(self.errors),
            "by_stage": by_stage,
            "by_type": by_type,
            "recent_errors": recent
        }
    
    def export_errors(self, filepath: str):
        """Export errors to JSON file."""
        with open(filepath, 'w') as f:
            json.dump({
                "errors": self.errors,
                "summary": self.get_error_summary()
            }, f, indent=2)
        self.logger.info(f"Exported {len(self.errors)} errors to {filepath}")


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
    
    @staticmethod
    def generate_topic_id(tier: int, label: str, index: int) -> str:
        """
        Generate topic ID.
        
        Args:
            tier: Tier number (1, 2, or 3)
            label: Topic label
            index: Topic index within tier
            
        Returns:
            Topic ID string
        """
        # Clean label for use in ID
        clean_label = "".join(c if c.isalnum() else "_" for c in label)
        clean_label = clean_label[:20]  # Limit length
        return f"T{tier}_{clean_label}_{index}"


# =============================================================================
# Phase 18: API Error Handling and Retry Logic (Step 18.2)
# =============================================================================

class APIError(Exception):
    """Base exception for API-related errors."""
    pass


class RateLimitError(APIError):
    """Exception raised when API rate limit is hit."""
    pass


class QuotaExceededError(APIError):
    """Exception raised when API quota is exceeded."""
    pass


class TransientAPIError(APIError):
    """Exception for transient API errors that should be retried."""
    pass


class RetryHandler:
    """
    Handler for API retry logic with exponential backoff (Phase 18: Step 18.2).
    
    Implements:
    - Exponential backoff strategy
    - Rate limit handling (429 errors)
    - Transient failure retry
    - Quota exceeded handling
    """
    
    def __init__(
        self,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0
    ):
        """
        Initialize retry handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            backoff_factor: Multiplier for exponential backoff
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.logger = logging.getLogger(f"{__name__}.RetryHandler")
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for exponential backoff.
        
        Args:
            attempt: Current retry attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)
    
    def retry_with_backoff(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic and exponential backoff.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Result from function
            
        Raises:
            Exception: If all retries are exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            
            except RateLimitError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.calculate_delay(attempt)
                    self.logger.warning(
                        f"Rate limit hit (attempt {attempt + 1}/{self.max_retries}). "
                        f"Waiting {delay:.1f}s before retry..."
                    )
                    import time
                    time.sleep(delay)
                else:
                    self.logger.error(f"Rate limit: Max retries exhausted")
                    raise
            
            except TransientAPIError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.calculate_delay(attempt)
                    self.logger.warning(
                        f"Transient error (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Waiting {delay:.1f}s before retry..."
                    )
                    import time
                    time.sleep(delay)
                else:
                    self.logger.error(f"Transient error: Max retries exhausted")
                    raise
            
            except QuotaExceededError as e:
                self.logger.error(f"Quota exceeded: {e}")
                raise  # Don't retry quota errors
            
            except Exception as e:
                # Check if it's a known API error pattern
                error_str = str(e).lower()
                
                if "rate" in error_str and "limit" in error_str:
                    # Convert to RateLimitError and retry
                    last_exception = RateLimitError(str(e))
                    if attempt < self.max_retries - 1:
                        delay = self.calculate_delay(attempt)
                        self.logger.warning(
                            f"Detected rate limit (attempt {attempt + 1}/{self.max_retries}). "
                            f"Waiting {delay:.1f}s before retry..."
                        )
                        import time
                        time.sleep(delay)
                    else:
                        raise RateLimitError(str(e))
                
                elif "quota" in error_str or "exceeded" in error_str:
                    raise QuotaExceededError(str(e))
                
                elif any(keyword in error_str for keyword in ["timeout", "connection", "network"]):
                    # Transient network error
                    last_exception = TransientAPIError(str(e))
                    if attempt < self.max_retries - 1:
                        delay = self.calculate_delay(attempt)
                        self.logger.warning(
                            f"Network error (attempt {attempt + 1}/{self.max_retries}): {e}. "
                            f"Waiting {delay:.1f}s before retry..."
                        )
                        import time
                        time.sleep(delay)
                    else:
                        raise TransientAPIError(str(e))
                else:
                    # Unknown error, don't retry
                    raise
        
        # Should not reach here, but if we do, raise the last exception
        if last_exception:
            raise last_exception


# =============================================================================
# Phase 18: Data Validation Error Handling (Step 18.3)
# =============================================================================

class ValidationError(Exception):
    """Exception raised when data validation fails."""
    pass


class PDFValidationError(ValidationError):
    """Exception raised when PDF validation fails."""
    pass


class DataValidator:
    """
    Validator for data quality and format checking (Phase 18: Step 18.3).
    
    Handles:
    - PDF file validation
    - Corrupt file detection
    - Format verification
    - Pre-processing validation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.DataValidator")
    
    def validate_pdf_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate PDF file before processing.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with validation results
            
        Raises:
            PDFValidationError: If validation fails
        """
        import os
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "file_size": 0,
            "is_readable": False,
        }
        
        # Check file exists
        if not os.path.exists(file_path):
            validation_result["valid"] = False
            validation_result["errors"].append(f"File does not exist: {file_path}")
            raise PDFValidationError(f"File does not exist: {file_path}")
        
        # Check file size
        file_size = os.path.getsize(file_path)
        validation_result["file_size"] = file_size
        
        if file_size == 0:
            validation_result["valid"] = False
            validation_result["errors"].append("File is empty (0 bytes)")
            raise PDFValidationError(f"File is empty: {file_path}")
        
        if file_size < 100:  # Suspiciously small
            validation_result["warnings"].append(
                f"File is very small ({file_size} bytes), may be corrupt"
            )
        
        # Check file extension
        if not file_path.lower().endswith('.pdf'):
            validation_result["warnings"].append(
                f"File does not have .pdf extension: {file_path}"
            )
        
        # Try to open with PyMuPDF (basic check)
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            validation_result["is_readable"] = True
            validation_result["page_count"] = len(doc)
            
            if len(doc) == 0:
                validation_result["valid"] = False
                validation_result["errors"].append("PDF has 0 pages")
                doc.close()
                raise PDFValidationError(f"PDF has 0 pages: {file_path}")
            
            doc.close()
        
        except Exception as e:
            validation_result["valid"] = False
            validation_result["is_readable"] = False
            validation_result["errors"].append(f"Cannot open PDF: {str(e)}")
            raise PDFValidationError(f"Cannot open PDF {file_path}: {str(e)}")
        
        return validation_result
    
    def validate_paper_record(
        self,
        paper: PaperRecord,
        required_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate a PaperRecord for completeness and consistency.
        
        Args:
            paper: PaperRecord to validate
            required_fields: List of required field names
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }
        
        # Default required fields
        if required_fields is None:
            required_fields = ["id", "file_path", "filename"]
        
        # Check required fields
        for field in required_fields:
            value = getattr(paper, field, None)
            if value is None or value == "":
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["valid"] = False
        
        # Check processing status consistency
        if paper.processing_status == "failed":
            if not paper.error_reason:
                validation_result["warnings"].append(
                    "Paper marked as failed but no error_reason provided"
                )
        
        # Check metadata consistency
        if paper.year and paper.publish_date:
            if paper.year != paper.publish_date.year:
                validation_result["warnings"].append(
                    f"Year field ({paper.year}) doesn't match publish_date year ({paper.publish_date.year})"
                )
        
        # Check topic classification consistency
        if paper.tier2_topic and not paper.tier1_topic:
            validation_result["errors"].append(
                "Paper has tier2_topic but missing tier1_topic"
            )
            validation_result["valid"] = False
        
        if paper.tier3_topic and not paper.tier2_topic:
            validation_result["errors"].append(
                "Paper has tier3_topic but missing tier2_topic"
            )
            validation_result["valid"] = False
        
        return validation_result


# =============================================================================
# Additional Utility Functions
# =============================================================================

def create_default_config(**overrides) -> RunConfig:
    """
    Create a RunConfig with default values and optional overrides.
    
    Args:
        **overrides: Keyword arguments to override default values
        
    Returns:
        RunConfig instance
        
    Example:
        config = create_default_config(
            drive_folder_path="my_pdfs",
            max_papers_per_run=10
        )
    """
    return RunConfig(**overrides)


def validate_paper_record(paper: PaperRecord) -> Dict[str, Any]:
    """
    Validate a paper record and return validation results.
    
    Args:
        paper: PaperRecord to validate
        
    Returns:
        Dictionary with validation results
    """
    issues = []
    warnings = []
    
    # Check required metadata
    if not paper.title:
        warnings.append("Missing title")
    if not paper.authors:
        warnings.append("Missing authors")
    if not paper.publish_date:
        warnings.append("Missing publication date")
    
    # Check processing status
    if paper.processing_status == "failed" and not paper.error_reason:
        issues.append("Failed status but no error reason provided")
    
    # Check topic classifications
    if paper.processing_status == "classified":
        if not paper.tier1_topic:
            issues.append("Classified but missing Tier 1 topic")
        if not paper.tier2_topic:
            warnings.append("Classified but missing Tier 2 topic")
        if not paper.tier3_topic:
            warnings.append("Classified but missing Tier 3 topic")
    
    # Check confidence scores
    if paper.tier1_topic and paper.tier1_confidence is None:
        warnings.append("Tier 1 topic assigned but no confidence score")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "has_metadata": bool(paper.title and paper.authors),
        "has_summary": bool(paper.full_summary),
        "has_topics": bool(paper.tier1_topic),
    }


def export_papers_to_csv(papers: Dict[str, PaperRecord], output_path: str) -> str:
    """
    Export papers to CSV file.
    
    Args:
        papers: Dictionary of paper_id -> PaperRecord
        output_path: Path to output CSV file
        
    Returns:
        Path to created CSV file
    """
    import pandas as pd
    
    # Convert papers to list of dicts
    data = [paper.to_dict() for paper in papers.values()]
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    return output_path


def load_papers_from_csv(csv_path: str) -> Dict[str, PaperRecord]:
    """
    Load papers from CSV file.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        Dictionary of paper_id -> PaperRecord
    """
    import pandas as pd
    import ast
    
    df = pd.read_csv(csv_path)
    
    papers = {}
    for _, row in df.iterrows():
        paper_dict = row.to_dict()
        # Handle NaN values
        paper_dict = {k: (None if pd.isna(v) else v) for k, v in paper_dict.items()}
        
        # Handle list fields (authors)
        if 'authors' in paper_dict and isinstance(paper_dict['authors'], str):
            try:
                paper_dict['authors'] = ast.literal_eval(paper_dict['authors'])
            except (ValueError, SyntaxError):
                # If parsing fails, treat as empty list
                paper_dict['authors'] = None
        
        # Handle dict fields (raw_text_stats)
        if 'raw_text_stats' in paper_dict and isinstance(paper_dict['raw_text_stats'], str):
            try:
                paper_dict['raw_text_stats'] = ast.literal_eval(paper_dict['raw_text_stats'])
            except (ValueError, SyntaxError):
                # If parsing fails, use empty dict
                paper_dict['raw_text_stats'] = {}
        
        paper = PaperRecord.from_dict(paper_dict)
        papers[paper.id] = paper
    
    return papers


# =============================================================================
# Phase 17: Cost Tracking and Optimization
# =============================================================================

class BudgetExceededError(Exception):
    """Raised when the budget limit is exceeded."""
    pass


class APICallRecord(BaseModel):
    """
    Record of a single API call for cost tracking.
    """
    timestamp: datetime = Field(default_factory=datetime.now)
    operation: str = Field(description="Type of operation (embedding, completion, etc.)")
    model: str = Field(description="Model used")
    input_tokens: int = Field(default=0, description="Number of input tokens")
    output_tokens: int = Field(default=0, description="Number of output tokens")
    total_tokens: int = Field(default=0, description="Total tokens used")
    estimated_cost: float = Field(default=0.0, description="Estimated cost in USD")
    paper_id: Optional[str] = Field(default=None, description="Associated paper ID")
    batch_size: int = Field(default=1, description="Batch size if batched")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump(mode='json')


class CostReport(BaseModel):
    """
    Comprehensive cost report for a pipeline run.
    """
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = Field(default=None)
    total_cost: float = Field(default=0.0, description="Total cost in USD")
    
    # Cost breakdown by operation type
    embedding_cost: float = Field(default=0.0)
    summarization_cost: float = Field(default=0.0)
    taxonomy_cost: float = Field(default=0.0)
    classification_cost: float = Field(default=0.0)
    other_cost: float = Field(default=0.0)
    
    # Token statistics
    total_input_tokens: int = Field(default=0)
    total_output_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    
    # API call statistics
    total_api_calls: int = Field(default=0)
    api_calls_by_operation: Dict[str, int] = Field(default_factory=dict)
    
    # Budget information
    budget_limit: Optional[float] = Field(default=None)
    budget_remaining: Optional[float] = Field(default=None)
    budget_utilization: Optional[float] = Field(default=None)  # 0.0 to 1.0
    
    # Warnings and recommendations
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump(mode='json')
    
    def to_formatted_string(self) -> str:
        """
        Generate a formatted string representation of the cost report.
        
        Returns:
            Formatted cost report string
        """
        lines = [
            "=" * 70,
            "COST REPORT",
            "=" * 70,
            f"Period: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} - "
            f"{self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else 'In Progress'}",
            "",
            "TOTAL COST:",
            f"  ${self.total_cost:.4f} USD",
            ""
        ]
        
        if self.budget_limit:
            lines.extend([
                "BUDGET:",
                f"  Limit: ${self.budget_limit:.2f}",
                f"  Remaining: ${self.budget_remaining:.2f}",
                f"  Utilization: {self.budget_utilization * 100:.1f}%",
                ""
            ])
        
        lines.extend([
            "COST BREAKDOWN BY OPERATION:",
            f"  Embeddings:      ${self.embedding_cost:.4f}",
            f"  Summarization:   ${self.summarization_cost:.4f}",
            f"  Taxonomy:        ${self.taxonomy_cost:.4f}",
            f"  Classification:  ${self.classification_cost:.4f}",
            f"  Other:           ${self.other_cost:.4f}",
            "",
            "TOKEN USAGE:",
            f"  Input tokens:    {self.total_input_tokens:,}",
            f"  Output tokens:   {self.total_output_tokens:,}",
            f"  Total tokens:    {self.total_tokens:,}",
            "",
            "API CALLS:",
            f"  Total calls:     {self.total_api_calls}",
        ])
        
        if self.api_calls_by_operation:
            for op, count in sorted(self.api_calls_by_operation.items()):
                lines.append(f"    {op}: {count}")
        
        if self.warnings:
            lines.extend(["", "WARNINGS:"])
            for warning in self.warnings:
                lines.append(f"  ⚠ {warning}")
        
        if self.recommendations:
            lines.extend(["", "RECOMMENDATIONS:"])
            for rec in self.recommendations:
                lines.append(f"  💡 {rec}")
        
        lines.append("=" * 70)
        return "\n".join(lines)


class CostTracker:
    """
    Tracks API costs, token usage, and manages budget controls.
    
    This class is the main interface for Phase 17 cost tracking and optimization.
    It monitors all API calls, calculates costs, enforces budget limits, and
    provides recommendations for cost savings.
    
    Key Features:
        - Real-time cost tracking for all OpenAI API calls
        - Budget enforcement with configurable limits and warnings
        - Support for batch API 50% discount calculation
        - Result caching to avoid duplicate API calls
        - Cost breakdown by operation type
        - Automated cost-saving recommendations
    
    Usage:
        >>> from rag_models import RunConfig, CostTracker
        >>> config = RunConfig(max_cost_per_run=10.0)
        >>> tracker = CostTracker(config)
        >>> tracker.record_api_call("summarization", "gpt-5-mini", 1000, 500)
        >>> tracker.print_summary()
    
    See Also:
        - FINAL_NOTEBOOK_ACTION_PLAN.md Phase 17 for implementation details
        - README_PHASE17.md for complete documentation
    """
    
    # OpenAI API pricing (as of 2025-11, subject to change)
    # Source: https://openai.com/api/pricing/
    # NOTE: Update these values when pricing changes
    # CUSTOMIZATION POINT: Add new models here as they become available
    PRICING = {
        # GPT-5 models (Responses API)
        "gpt-5-mini": {
            "input": 0.10 / 1_000_000,   # $0.10 per 1M input tokens
            "output": 0.40 / 1_000_000,  # $0.40 per 1M output tokens
        },
        "gpt-5": {
            "input": 3.00 / 1_000_000,   # $3.00 per 1M input tokens
            "output": 15.00 / 1_000_000, # $15.00 per 1M output tokens
        },
        # O-series models (reasoning models)
        "o4-mini": {
            "input": 0.15 / 1_000_000,   # $0.15 per 1M input tokens
            "output": 0.60 / 1_000_000,  # $0.60 per 1M output tokens
        },
        "o4": {
            "input": 5.00 / 1_000_000,   # $5.00 per 1M input tokens
            "output": 20.00 / 1_000_000, # $20.00 per 1M output tokens
        },
        # Embedding models (input only, no output tokens)
        "text-embedding-3-small": {
            "input": 0.02 / 1_000_000,   # $0.02 per 1M tokens
            "output": 0.0,
        },
        "text-embedding-3-large": {
            "input": 0.13 / 1_000_000,   # $0.13 per 1M tokens
            "output": 0.0,
        },
        # Batch API discount (applies to offline/batch jobs)
        "batch_discount": 0.5,
    }
    
    def __init__(self, config: RunConfig):
        """
        Initialize CostTracker with configuration.
        
        Args:
            config: RunConfig with budget settings
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.CostTracker")
        
        # Call records - stores all API call history for reporting
        self.api_calls: List[APICallRecord] = []
        
        # Cost accumulators - track spending by operation type
        self.total_cost = 0.0
        self.cost_by_operation: Dict[str, float] = {
            "embedding": 0.0,       # text-embedding-* calls
            "summarization": 0.0,   # Summary generation calls
            "taxonomy": 0.0,        # Topic labeling calls
            "classification": 0.0,  # Paper classification calls
            "other": 0.0,           # Uncategorized calls
        }
        
        # Token accumulators - track total token usage
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        
        # Cache for deduplication - avoids duplicate API calls
        # Key: hash of operation+params, Value: cached result
        self.result_cache: Dict[str, Any] = {}
        
        # Budget tracking from config
        self.budget_limit = config.max_cost_per_run
        self.warning_threshold = config.cost_warning_threshold
        self.warnings_issued: List[str] = []  # Track which warnings already shown
        
        # Start time for duration tracking
        self.start_time = datetime.now()
        
        self.logger.info(f"CostTracker initialized. Budget: ${self.budget_limit if self.budget_limit else 'unlimited'}")
    
    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int = 0,
        is_batch: bool = False
    ) -> float:
        """
        Estimate the cost of an API call.
        
        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens (0 for embeddings)
            is_batch: Whether this is a batch API call (50% discount)
            
        Returns:
            Estimated cost in USD
        """
        # Normalize model name (handle variants)
        model_key = model.lower()
        if model_key == "gpt-5-mini" or model_key.startswith("gpt-5-mini-"):
            model_key = "gpt-5-mini"
        elif model_key == "gpt-5" or model_key.startswith("gpt-5-"):
            model_key = "gpt-5"
        elif model_key == "o4-mini" or model_key.startswith("o4-mini-"):
            model_key = "o4-mini"
        elif model_key == "o4" or model_key.startswith("o4-"):
            model_key = "o4"
        elif "text-embedding-3-small" in model_key:
            model_key = "text-embedding-3-small"
        elif "text-embedding-3-large" in model_key:
            model_key = "text-embedding-3-large"
        else:
            self.logger.warning(f"Unknown model '{model}', using gpt-5-mini pricing as fallback")
            model_key = "gpt-5-mini"
        
        # Get pricing
        pricing = self.PRICING.get(model_key, self.PRICING["gpt-5-mini"])
        
        # Calculate cost
        input_cost = input_tokens * pricing["input"]
        output_cost = output_tokens * pricing["output"]
        total_cost = input_cost + output_cost
        
        # Apply batch discount if applicable
        if is_batch and self.config.batch_api_calls:
            total_cost *= self.PRICING["batch_discount"]
        
        return total_cost
    
    def record_api_call(
        self,
        operation: str,
        model: str,
        input_tokens: int,
        output_tokens: int = 0,
        paper_id: Optional[str] = None,
        batch_size: int = 1,
        is_batch: bool = False
    ) -> APICallRecord:
        """
        Record an API call and update cost tracking.
        
        Args:
            operation: Type of operation (embedding, summarization, etc.)
            model: Model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            paper_id: Associated paper ID (if applicable)
            batch_size: Batch size if batched
            is_batch: Whether this is a batch API call
            
        Returns:
            APICallRecord with cost information
            
        Raises:
            BudgetExceededError: If budget limit is exceeded
        """
        # Estimate cost
        cost = self.estimate_cost(model, input_tokens, output_tokens, is_batch)
        
        # Create record
        record = APICallRecord(
            operation=operation,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost=cost,
            paper_id=paper_id,
            batch_size=batch_size
        )
        
        # Update accumulators
        self.api_calls.append(record)
        self.total_cost += cost
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        
        # Update operation-specific costs
        operation_key = operation.lower()
        if "embed" in operation_key:
            self.cost_by_operation["embedding"] += cost
        elif "summar" in operation_key:
            self.cost_by_operation["summarization"] += cost
        elif "taxon" in operation_key or "topic" in operation_key:
            self.cost_by_operation["taxonomy"] += cost
        elif "classif" in operation_key:
            self.cost_by_operation["classification"] += cost
        else:
            self.cost_by_operation["other"] += cost
        
        # Check budget
        self.check_budget()
        
        # Log
        self.logger.debug(
            f"API call recorded: {operation} ({model}) - "
            f"{input_tokens} in, {output_tokens} out, ${cost:.4f}"
        )
        
        return record
    
    def check_budget(self) -> None:
        """
        Check if budget limits are exceeded or approaching.
        
        Raises:
            BudgetExceededError: If budget limit is exceeded
        """
        if not self.budget_limit or not self.config.enable_cost_tracking:
            return
        
        utilization = self.total_cost / self.budget_limit
        
        # Check if budget exceeded
        if self.total_cost > self.budget_limit:
            msg = (
                f"Budget exceeded! Total cost: ${self.total_cost:.2f}, "
                f"Limit: ${self.budget_limit:.2f}"
            )
            self.logger.error(msg)
            raise BudgetExceededError(msg)
        
        # Check if approaching budget limit
        if utilization >= self.warning_threshold:
            warning_key = f"threshold_{int(utilization * 100)}"
            if warning_key not in self.warnings_issued:
                msg = (
                    f"Cost warning: {utilization * 100:.1f}% of budget used "
                    f"(${self.total_cost:.2f} / ${self.budget_limit:.2f})"
                )
                self.logger.warning(msg)
                self.warnings_issued.append(warning_key)
    
    def get_cache_key(self, operation: str, **kwargs) -> str:
        """
        Generate a cache key for result caching.
        
        Args:
            operation: Operation type
            **kwargs: Additional parameters to include in key
            
        Returns:
            Cache key string
        """
        import hashlib
        key_data = json.dumps({"op": operation, **kwargs}, sort_keys=True)
        # Using SHA256 for cache key generation (non-security use case)
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """
        Get a cached result if available.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached result or None
        """
        if not self.config.enable_result_caching:
            return None
        return self.result_cache.get(cache_key)
    
    def cache_result(self, cache_key: str, result: Any) -> None:
        """
        Cache a result.
        
        Args:
            cache_key: Cache key
            result: Result to cache
        """
        if self.config.enable_result_caching:
            self.result_cache[cache_key] = result
    
    def generate_report(self) -> CostReport:
        """
        Generate a comprehensive cost report.
        
        Returns:
            CostReport with all cost information
        """
        # Count API calls by operation
        api_calls_by_op = {}
        for call in self.api_calls:
            op = call.operation
            api_calls_by_op[op] = api_calls_by_op.get(op, 0) + 1
        
        # Calculate budget info
        budget_remaining = None
        budget_utilization = None
        if self.budget_limit:
            budget_remaining = self.budget_limit - self.total_cost
            budget_utilization = min(self.total_cost / self.budget_limit, 1.0)
        
        # Generate warnings
        warnings = []
        if self.budget_limit and self.total_cost > self.budget_limit * 0.9:
            warnings.append("Budget is nearly exhausted (>90% used)")
        if self.total_cost > 10.0:
            warnings.append("High total cost detected")
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Create report
        report = CostReport(
            start_time=self.start_time,
            end_time=datetime.now(),
            total_cost=self.total_cost,
            embedding_cost=self.cost_by_operation["embedding"],
            summarization_cost=self.cost_by_operation["summarization"],
            taxonomy_cost=self.cost_by_operation["taxonomy"],
            classification_cost=self.cost_by_operation["classification"],
            other_cost=self.cost_by_operation["other"],
            total_input_tokens=self.total_input_tokens,
            total_output_tokens=self.total_output_tokens,
            total_tokens=self.total_input_tokens + self.total_output_tokens,
            total_api_calls=len(self.api_calls),
            api_calls_by_operation=api_calls_by_op,
            budget_limit=self.budget_limit,
            budget_remaining=budget_remaining,
            budget_utilization=budget_utilization,
            warnings=warnings,
            recommendations=recommendations
        )
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """
        Generate cost-saving recommendations based on usage patterns.
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Check if batch API is enabled
        if not self.config.batch_api_calls:
            recommendations.append(
                "Enable batch_api_calls in config for 50% cost savings on bulk operations"
            )
        
        # Check if caching is enabled
        if not self.config.enable_result_caching:
            recommendations.append(
                "Enable enable_result_caching to avoid duplicate API calls"
            )
        
        # Check if using expensive models
        if self.config.summary_model == "gpt-5":
            recommendations.append(
                "Consider using gpt-5-mini for summarization (10-30x cheaper)"
            )
        
        if self.config.embedding_model == "text-embedding-3-large":
            recommendations.append(
                "Consider using text-embedding-3-small for embeddings (6.5x cheaper)"
            )
        
        # Check for high-cost operations (only if enough data)
        if self.total_cost > 0.01 and len(self.api_calls) >= 10 and self.cost_by_operation["summarization"] > self.total_cost * 0.5:
            recommendations.append(
                "Summarization is >50% of total cost. Consider reducing max_tokens_per_summary"
            )
        
        if self.total_cost > 0.01 and len(self.api_calls) >= 10 and self.cost_by_operation["embedding"] > self.total_cost * 0.5:
            recommendations.append(
                "Embeddings are >50% of total cost. Consider using smaller chunks or text-embedding-3-small"
            )
        
        # Check token usage
        avg_output_tokens = self.total_output_tokens / len(self.api_calls) if self.api_calls else 0
        if avg_output_tokens > 1000:
            recommendations.append(
                f"Average output tokens per call is high ({avg_output_tokens:.0f}). "
                "Consider reducing max_tokens parameters"
            )
        
        return recommendations
    
    def print_summary(self) -> None:
        """Print a summary of costs to the console."""
        report = self.generate_report()
        print(report.to_formatted_string())
    
    def save_report(self, output_path: str) -> str:
        """
        Save cost report to a JSON file.
        
        Args:
            output_path: Path to output file
            
        Returns:
            Path to saved file
        """
        report = self.generate_report()
        
        with open(output_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        self.logger.info(f"Cost report saved to {output_path}")
        return output_path
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert CostTracker state to dictionary for serialization.
        
        Returns:
            Dictionary with all tracking data
        """
        return {
            "start_time": self.start_time.isoformat(),
            "total_cost": self.total_cost,
            "cost_by_operation": self.cost_by_operation,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "budget_limit": self.budget_limit,
            "api_calls": [call.to_dict() for call in self.api_calls],
            "warnings_issued": self.warnings_issued,
        }
    
    @classmethod
    def from_dict(cls, config: RunConfig, data: Dict[str, Any]) -> 'CostTracker':
        """
        Restore CostTracker from dictionary.
        
        Args:
            config: RunConfig
            data: Dictionary with tracking data
            
        Returns:
            Restored CostTracker instance
        """
        tracker = cls(config)
        tracker.start_time = datetime.fromisoformat(data["start_time"])
        tracker.total_cost = data["total_cost"]
        tracker.cost_by_operation = data["cost_by_operation"]
        tracker.total_input_tokens = data["total_input_tokens"]
        tracker.total_output_tokens = data["total_output_tokens"]
        tracker.warnings_issued = data["warnings_issued"]
        
        # Restore API calls
        tracker.api_calls = [
            APICallRecord(**call_data) for call_data in data["api_calls"]
        ]
        
        return tracker
