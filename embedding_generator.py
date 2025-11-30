#!/usr/bin/env python3
"""
RAG PDF Research Corpus System - Embedding Generation and FAISS Index (Phase 5)

This module implements Phase 5 of the FINAL_NOTEBOOK_ACTION_PLAN.md:
- Step 5.1: Create Embedding Generator (OpenAI embeddings client, batch processing, rate limiting)
- Step 5.2: Embed All Chunks (iterate chunks, generate embeddings, track costs)
- Step 5.3: Build FAISS Index (create index, add embeddings, metadata mapping)
- Step 5.4: Save FAISS Index and Metadata (serialize, persist to disk)
- Step 5.5: Create Index Loading Function (load, validate, error handling)

Version: 1.0
Date: 2025-11-22
"""

import json
import logging
import pickle
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

# OpenAI client
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not available. Install with: pip install openai")

# FAISS
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS package not available. Install with: pip install faiss-cpu")

# Progress bar
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    logging.warning("tqdm not available. Install with: pip install tqdm")

from rag_models import (
    PaperChunk,
    PaperRecord,
    GraphState,
    RunConfig,
)

logger = logging.getLogger(__name__)

# Pricing per 1M tokens (as of Nov 2025 - verify at https://openai.com/pricing)
EMBEDDING_MODEL_PRICING = {
    "text-embedding-3-small": 0.02,
    "text-embedding-3-large": 0.13,
    "text-embedding-ada-002": 0.10,
}

# Paper statuses that are eligible for embedding status update
# Papers must be in one of these statuses to be updated to "embedded"
ELIGIBLE_FOR_EMBEDDING_UPDATE = ["parsed", "pending"]

# Export list
__all__ = [
    # Step 5.1: Embedding Generator
    'EmbeddingGenerator',
    'create_embedding_generator',
    'generate_embeddings',
    'estimate_embedding_cost',
    
    # Step 5.2: Embed All Chunks
    'embed_all_chunks',
    'embed_chunks_batch',
    
    # Step 5.3: Build FAISS Index
    'FaissIndexBuilder',
    'build_faiss_index',
    'create_metadata_mapping',
    
    # Step 5.4: Save Index
    'save_faiss_index',
    'save_metadata_mapping',
    
    # Step 5.5: Load Index
    'load_faiss_index',
    'load_metadata_mapping',
    'validate_index',
    
    # Worker
    'embedding_generation_worker',
]


# =============================================================================
# Step 5.1: Create Embedding Generator
# =============================================================================

class EmbeddingGenerator:
    """
    Handles embedding generation using OpenAI API with rate limiting,
    retry logic, and cost tracking.
    
    Features:
    - Batch processing for efficiency
    - Exponential backoff retry logic
    - Rate limiting to respect API limits
    - Cost tracking and estimation
    - Progress logging
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-large",
        batch_size: int = 100,
        rate_limit_delay: float = 1.0,
        max_retries: int = 3,
    ):
        """
        Initialize the embedding generator.
        
        Args:
            api_key: OpenAI API key
            model: Embedding model to use
            batch_size: Number of texts to embed in one API call
            rate_limit_delay: Delay between API calls in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package required. Install with: pip install openai")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.batch_size = batch_size
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        
        # Cost tracking
        self.total_tokens = 0
        self.total_api_calls = 0
        self.failed_calls = 0
        
        logger.info(f"EmbeddingGenerator initialized with model: {model}")
    
    def generate_embeddings(
        self,
        texts: List[str],
        show_progress: bool = True,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Generate embeddings for a list of texts with batching and retry logic.
        
        Args:
            texts: List of text strings to embed
            show_progress: Whether to show progress bar
            
        Returns:
            Tuple of (embeddings array, statistics dict)
            - embeddings: numpy array of shape (len(texts), embedding_dim)
            - stats: dictionary with token usage and cost information
        """
        if not texts:
            return np.array([]).reshape(0, 0), {"total_tokens": 0, "api_calls": 0}
        
        embeddings = []
        total_tokens = 0
        api_calls = 0
        
        # Process in batches
        num_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        
        iterator = range(num_batches)
        if show_progress and TQDM_AVAILABLE:
            iterator = tqdm(iterator, desc="Generating embeddings", unit="batch")
        
        for batch_idx in iterator:
            start_idx = batch_idx * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(texts))
            batch_texts = texts[start_idx:end_idx]
            
            # Generate embeddings for batch with retry logic
            batch_embeddings, batch_tokens = self._generate_batch_with_retry(batch_texts)
            
            embeddings.extend(batch_embeddings)
            total_tokens += batch_tokens
            api_calls += 1
            
            # Rate limiting
            if batch_idx < num_batches - 1:
                time.sleep(self.rate_limit_delay)
        
        # Update tracking
        self.total_tokens += total_tokens
        self.total_api_calls += api_calls
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        stats = {
            "total_tokens": total_tokens,
            "api_calls": api_calls,
            "num_embeddings": len(embeddings),
            "embedding_dim": embeddings_array.shape[1] if len(embeddings) > 0 else 0,
            "estimated_cost_usd": self._estimate_cost(total_tokens),
        }
        
        logger.info(f"Generated {len(embeddings)} embeddings using {total_tokens} tokens")
        
        return embeddings_array, stats
    
    def _generate_batch_with_retry(
        self,
        texts: List[str],
    ) -> Tuple[List[List[float]], int]:
        """
        Generate embeddings for a batch with exponential backoff retry.
        
        Args:
            texts: List of text strings
            
        Returns:
            Tuple of (embeddings list, token count)
        """
        for attempt in range(self.max_retries):
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts,
                )
                
                embeddings = [item.embedding for item in response.data]
                tokens = response.usage.total_tokens
                
                return embeddings, tokens
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * self.rate_limit_delay
                    logger.warning(
                        f"Embedding API error (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Embedding API failed after {self.max_retries} attempts: {e}")
                    self.failed_calls += 1
                    raise
        
        # Should never reach here
        raise RuntimeError("Unexpected error in retry logic")
    
    def _estimate_cost(self, tokens: int) -> float:
        """
        Estimate cost in USD for the given number of tokens.
        
        Uses EMBEDDING_MODEL_PRICING constant for pricing data.
        
        Args:
            tokens: Number of tokens
            
        Returns:
            Estimated cost in USD
        """
        price_per_million = EMBEDDING_MODEL_PRICING.get(self.model, 0.10)  # Default to ada-002 pricing
        return (tokens / 1_000_000) * price_per_million
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cumulative statistics."""
        return {
            "total_tokens": self.total_tokens,
            "total_api_calls": self.total_api_calls,
            "failed_calls": self.failed_calls,
            "estimated_cost_usd": self._estimate_cost(self.total_tokens),
            "model": self.model,
        }


def create_embedding_generator(
    api_key: str,
    config: Optional[RunConfig] = None,
) -> EmbeddingGenerator:
    """
    Create an EmbeddingGenerator with configuration.
    
    Args:
        api_key: OpenAI API key
        config: Optional RunConfig for parameters
        
    Returns:
        EmbeddingGenerator instance
    """
    if config:
        model = config.embedding_model
    else:
        model = "text-embedding-3-large"
    
    return EmbeddingGenerator(
        api_key=api_key,
        model=model,
        batch_size=100,
        rate_limit_delay=1.0,
        max_retries=3,
    )


def generate_embeddings(
    texts: List[str],
    api_key: str,
    model: str = "text-embedding-3-large",
    show_progress: bool = True,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Convenience function to generate embeddings.
    
    Args:
        texts: List of text strings
        api_key: OpenAI API key
        model: Embedding model
        show_progress: Show progress bar
        
    Returns:
        Tuple of (embeddings array, statistics)
    """
    generator = EmbeddingGenerator(api_key=api_key, model=model)
    return generator.generate_embeddings(texts, show_progress=show_progress)


def estimate_embedding_cost(
    num_texts: int,
    avg_chars_per_text: int,
    model: str = "text-embedding-3-large",
) -> Dict[str, Any]:
    """
    Estimate cost for embedding generation.
    
    Args:
        num_texts: Number of texts to embed
        avg_chars_per_text: Average characters per text
        model: Embedding model
        
    Returns:
        Dictionary with cost estimates
    """
    # Rough estimate: 1 token ≈ 4 characters
    estimated_tokens = (num_texts * avg_chars_per_text) // 4
    
    price_per_million = EMBEDDING_MODEL_PRICING.get(model, 0.10)
    estimated_cost = (estimated_tokens / 1_000_000) * price_per_million
    
    return {
        "num_texts": num_texts,
        "avg_chars_per_text": avg_chars_per_text,
        "estimated_tokens": estimated_tokens,
        "model": model,
        "estimated_cost_usd": estimated_cost,
    }


# =============================================================================
# Step 5.2: Embed All Chunks
# =============================================================================

def embed_all_chunks(
    state: GraphState,
    api_key: str,
    show_progress: bool = True,
) -> GraphState:
    """
    Generate embeddings for all chunks in the state.
    
    Args:
        state: GraphState containing chunks
        api_key: OpenAI API key
        show_progress: Show progress bar
        
    Returns:
        Updated GraphState with embedded chunks
    """
    logger.info("Starting embedding generation for all chunks")
    
    # Get configuration
    config = state.get("config")
    if not config:
        raise ValueError("RunConfig not found in state")
    
    # Create embedding generator
    generator = create_embedding_generator(api_key, config)
    
    # Collect all chunks and texts
    all_chunks = []
    all_texts = []
    chunk_ids = []
    
    for paper_id, chunks in state["chunks"].items():
        for chunk in chunks:
            all_chunks.append(chunk)
            # Use cleaned text if available, otherwise raw text
            text = chunk.cleaned_text if chunk.cleaned_text else chunk.text
            all_texts.append(text)
            chunk_ids.append(chunk.chunk_id)
    
    if not all_texts:
        logger.warning("No chunks found to embed")
        return state
    
    logger.info(f"Embedding {len(all_texts)} chunks from {len(state['chunks'])} papers")
    
    # Generate embeddings
    embeddings, stats = generator.generate_embeddings(all_texts, show_progress=show_progress)
    
    # Update chunks with embedding IDs
    for idx, chunk in enumerate(all_chunks):
        chunk.embedding_id = idx
        chunk.embedding_model = config.embedding_model
    
    # Store embeddings in state (for FAISS index creation)
    if "embeddings" not in state:
        state["embeddings"] = {}
    
    state["embeddings"]["chunk_embeddings"] = embeddings
    state["embeddings"]["chunk_ids"] = chunk_ids
    state["embeddings"]["stats"] = stats
    state["embeddings"]["model"] = config.embedding_model
    state["embeddings"]["generated_at"] = datetime.now().isoformat()
    
    # Update state statistics
    if "stats" not in state:
        state["stats"] = {}
    
    state["stats"]["embedding_count"] = len(embeddings)
    state["stats"]["embedding_tokens"] = stats["total_tokens"]
    state["stats"]["embedding_cost_usd"] = stats["estimated_cost_usd"]
    
    logger.info(
        f"Generated {len(embeddings)} embeddings. "
        f"Cost: ${stats['estimated_cost_usd']:.4f} USD"
    )
    
    return state


def embed_chunks_batch(
    chunks: List[PaperChunk],
    api_key: str,
    model: str = "text-embedding-3-large",
    show_progress: bool = True,
) -> Tuple[np.ndarray, List[PaperChunk], Dict[str, Any]]:
    """
    Generate embeddings for a batch of chunks.
    
    Args:
        chunks: List of PaperChunk objects
        api_key: OpenAI API key
        model: Embedding model
        show_progress: Show progress bar
        
    Returns:
        Tuple of (embeddings array, updated chunks, statistics)
    """
    generator = EmbeddingGenerator(api_key=api_key, model=model)
    
    # Extract texts
    texts = [chunk.cleaned_text if chunk.cleaned_text else chunk.text for chunk in chunks]
    
    # Generate embeddings
    embeddings, stats = generator.generate_embeddings(texts, show_progress=show_progress)
    
    # Update chunks with embedding IDs
    for idx, chunk in enumerate(chunks):
        chunk.embedding_id = idx
        chunk.embedding_model = model
    
    return embeddings, chunks, stats


# =============================================================================
# Step 5.3: Build FAISS Index
# =============================================================================

class FaissIndexBuilder:
    """
    Builds and manages FAISS index for chunk embeddings.
    
    Features:
    - CPU-based FAISS index
    - Metadata mapping for retrieval
    - Index integrity validation
    - Support for different index types
    """
    
    def __init__(
        self,
        embedding_dim: int,
        index_type: str = "FlatIP",  # Inner Product (cosine similarity)
    ):
        """
        Initialize the FAISS index builder.
        
        Args:
            embedding_dim: Dimension of embeddings
            index_type: Type of FAISS index ("FlatIP", "FlatL2", etc.)
        """
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS package required. Install with: pip install faiss-cpu")
        
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        self.index = None
        self.metadata_map = {}
        
        logger.info(f"FaissIndexBuilder initialized with dim={embedding_dim}, type={index_type}")
    
    def build_index(
        self,
        embeddings: np.ndarray,
        metadata: List[Dict[str, Any]],
        normalize: bool = True,
    ) -> None:
        """
        Build FAISS index from embeddings and metadata.
        
        Args:
            embeddings: numpy array of shape (n, embedding_dim)
            metadata: List of metadata dicts, one per embedding
            normalize: Whether to normalize embeddings (for cosine similarity)
        """
        if embeddings.shape[0] != len(metadata):
            raise ValueError(
                f"Embeddings count ({embeddings.shape[0]}) must match "
                f"metadata count ({len(metadata)})"
            )
        
        logger.info(f"Building FAISS index with {len(embeddings)} embeddings")
        
        # Normalize embeddings for cosine similarity
        if normalize:
            faiss.normalize_L2(embeddings)
        
        # Create index
        if self.index_type == "FlatIP":
            self.index = faiss.IndexFlatIP(self.embedding_dim)
        elif self.index_type == "FlatL2":
            self.index = faiss.IndexFlatL2(self.embedding_dim)
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")
        
        # Add embeddings to index
        self.index.add(embeddings)
        
        # Create metadata mapping
        for idx, meta in enumerate(metadata):
            self.metadata_map[idx] = meta
        
        logger.info(
            f"FAISS index built successfully. "
            f"Total vectors: {self.index.ntotal}"
        )
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        normalize: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray, List[Dict[str, Any]]]:
        """
        Search the index for similar embeddings.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            normalize: Whether to normalize query
            
        Returns:
            Tuple of (distances, indices, metadata_list)
        """
        if self.index is None:
            raise ValueError("Index not built yet")
        
        # Reshape query if needed
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Normalize query
        if normalize:
            faiss.normalize_L2(query_embedding)
        
        # Search
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Get metadata for results
        metadata_list = [self.metadata_map[int(idx)] for idx in indices[0]]
        
        return distances[0], indices[0], metadata_list
    
    def validate_index(self) -> Dict[str, Any]:
        """
        Validate index integrity.
        
        Returns:
            Dictionary with validation results
        """
        if self.index is None:
            return {
                "valid": False,
                "error": "Index not built"
            }
        
        issues = []
        
        # Check vector count
        if self.index.ntotal != len(self.metadata_map):
            issues.append(
                f"Vector count mismatch: index has {self.index.ntotal}, "
                f"metadata has {len(self.metadata_map)}"
            )
        
        # Check dimension
        if self.index.d != self.embedding_dim:
            issues.append(
                f"Dimension mismatch: expected {self.embedding_dim}, "
                f"got {self.index.d}"
            )
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "ntotal": self.index.ntotal,
            "dimension": self.index.d,
            "metadata_count": len(self.metadata_map),
        }


def build_faiss_index(
    embeddings: np.ndarray,
    chunks: List[PaperChunk],
    papers: Dict[str, PaperRecord],
    index_type: str = "FlatIP",
    normalize: bool = True,
) -> FaissIndexBuilder:
    """
    Build FAISS index from embeddings and chunks.
    
    Args:
        embeddings: Embedding vectors
        chunks: List of PaperChunk objects
        papers: Dictionary of paper_id -> PaperRecord
        index_type: Type of FAISS index
        normalize: Whether to normalize embeddings
        
    Returns:
        FaissIndexBuilder with built index
    """
    embedding_dim = embeddings.shape[1]
    builder = FaissIndexBuilder(embedding_dim, index_type)
    
    # Create metadata for each embedding
    metadata = []
    for chunk in chunks:
        paper = papers.get(chunk.paper_id)
        meta = {
            "chunk_id": chunk.chunk_id,
            "paper_id": chunk.paper_id,
            "section_label": chunk.section_label,
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
            "paper_title": paper.title if paper else None,
            "paper_authors": paper.authors if paper else None,
        }
        metadata.append(meta)
    
    # Build index
    builder.build_index(embeddings, metadata, normalize=normalize)
    
    return builder


def create_metadata_mapping(
    chunks: List[PaperChunk],
    papers: Dict[str, PaperRecord],
) -> Dict[int, Dict[str, Any]]:
    """
    Create metadata mapping for FAISS index.
    
    Args:
        chunks: List of PaperChunk objects
        papers: Dictionary of paper_id -> PaperRecord
        
    Returns:
        Dictionary mapping embedding_id to metadata
    """
    metadata_map = {}
    
    for idx, chunk in enumerate(chunks):
        paper = papers.get(chunk.paper_id)
        
        metadata_map[idx] = {
            "embedding_id": idx,
            "chunk_id": chunk.chunk_id,
            "paper_id": chunk.paper_id,
            "section_label": chunk.section_label,
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
            "char_count": chunk.char_count,
            "paper_title": paper.title if paper else None,
            "paper_authors": paper.authors if paper else None,
            "paper_year": paper.year if paper else None,
            "paper_venue": paper.venue if paper else None,
        }
    
    return metadata_map


# =============================================================================
# Step 5.4: Save FAISS Index and Metadata
# =============================================================================

def save_faiss_index(
    index_builder: FaissIndexBuilder,
    index_path: str,
    version: str = "1.0",
) -> str:
    """
    Save FAISS index to disk.
    
    Args:
        index_builder: FaissIndexBuilder with built index
        index_path: Path to save index file
        version: Version identifier
        
    Returns:
        Path to saved index file
    """
    if index_builder.index is None:
        raise ValueError("Index not built yet")
    
    # Ensure parent directory exists
    Path(index_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save index
    faiss.write_index(index_builder.index, index_path)
    
    logger.info(f"FAISS index saved to: {index_path}")
    
    # Save version info alongside index
    version_path = str(Path(index_path).with_suffix('.version.json'))
    version_info = {
        "version": version,
        "saved_at": datetime.now().isoformat(),
        "ntotal": index_builder.index.ntotal,
        "dimension": index_builder.index.d,
        "index_type": index_builder.index_type,
    }
    
    with open(version_path, 'w') as f:
        json.dump(version_info, f, indent=2)
    
    logger.info(f"Version info saved to: {version_path}")
    
    return index_path


def save_metadata_mapping(
    metadata_map: Dict[int, Dict[str, Any]],
    metadata_path: str,
    format: str = "json",
) -> str:
    """
    Save metadata mapping to disk.
    
    Args:
        metadata_map: Metadata mapping dictionary
        metadata_path: Path to save metadata
        format: Format to use ("json" or "pickle")
        
    Returns:
        Path to saved metadata file
    """
    # Ensure parent directory exists
    Path(metadata_path).parent.mkdir(parents=True, exist_ok=True)
    
    if format == "json":
        # Convert int keys to strings for JSON
        json_map = {str(k): v for k, v in metadata_map.items()}
        with open(metadata_path, 'w') as f:
            json.dump(json_map, f, indent=2)
    elif format == "pickle":
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata_map, f)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    logger.info(f"Metadata mapping ({len(metadata_map)} entries) saved to: {metadata_path}")
    
    return metadata_path


# =============================================================================
# Step 5.5: Create Index Loading Function
# =============================================================================

def load_faiss_index(
    index_path: str,
    validate: bool = True,
) -> faiss.Index:
    """
    Load FAISS index from disk.
    
    Args:
        index_path: Path to index file
        validate: Whether to validate after loading
        
    Returns:
        Loaded FAISS index
    """
    if not FAISS_AVAILABLE:
        raise ImportError("FAISS package required. Install with: pip install faiss-cpu")
    
    if not Path(index_path).exists():
        raise FileNotFoundError(f"Index file not found: {index_path}")
    
    # Load index
    index = faiss.read_index(index_path)
    
    logger.info(
        f"FAISS index loaded from: {index_path}. "
        f"Vectors: {index.ntotal}, Dimension: {index.d}"
    )
    
    # Load and check version info
    version_path = str(Path(index_path).with_suffix('.version.json'))
    if Path(version_path).exists():
        with open(version_path, 'r') as f:
            version_info = json.load(f)
            logger.info(f"Index version: {version_info.get('version')}, "
                       f"created: {version_info.get('saved_at')}")
    
    # Validate
    if validate:
        if index.ntotal == 0:
            logger.warning("Loaded index is empty (ntotal=0)")
        else:
            logger.info("Index validation passed")
    
    return index


def load_metadata_mapping(
    metadata_path: str,
    format: str = "json",
) -> Dict[int, Dict[str, Any]]:
    """
    Load metadata mapping from disk.
    
    Args:
        metadata_path: Path to metadata file
        format: Format of the file ("json" or "pickle")
        
    Returns:
        Metadata mapping dictionary
    """
    if not Path(metadata_path).exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    if format == "json":
        with open(metadata_path, 'r') as f:
            json_map = json.load(f)
        # Convert string keys back to int
        metadata_map = {int(k): v for k, v in json_map.items()}
    elif format == "pickle":
        with open(metadata_path, 'rb') as f:
            metadata_map = pickle.load(f)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    logger.info(f"Metadata mapping ({len(metadata_map)} entries) loaded from: {metadata_path}")
    
    return metadata_map


def validate_index(
    index: faiss.Index,
    metadata_map: Dict[int, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate FAISS index and metadata mapping.
    
    Args:
        index: FAISS index
        metadata_map: Metadata mapping
        
    Returns:
        Dictionary with validation results
    """
    issues = []
    
    # Check vector count matches metadata count
    if index.ntotal != len(metadata_map):
        issues.append(
            f"Vector count mismatch: index has {index.ntotal}, "
            f"metadata has {len(metadata_map)}"
        )
    
    # Check metadata IDs are sequential
    expected_ids = set(range(len(metadata_map)))
    actual_ids = set(metadata_map.keys())
    if expected_ids != actual_ids:
        issues.append("Metadata IDs are not sequential")
    
    # Check for required fields in metadata
    if metadata_map:
        sample_meta = next(iter(metadata_map.values()))
        required_fields = ["chunk_id", "paper_id"]
        missing_fields = [f for f in required_fields if f not in sample_meta]
        if missing_fields:
            issues.append(f"Missing required fields in metadata: {missing_fields}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "index_ntotal": index.ntotal,
        "index_dimension": index.d,
        "metadata_count": len(metadata_map),
    }


# =============================================================================
# LangGraph Worker
# =============================================================================

def embedding_generation_worker(
    state: GraphState,
    api_key: str,
) -> GraphState:
    """
    LangGraph worker node for embedding generation and FAISS index creation.
    
    This orchestrates the complete Phase 5 workflow:
    1. Generate embeddings for all chunks
    2. Build FAISS index
    3. Create metadata mapping
    4. Save index and metadata
    5. Update GraphState
    
    Args:
        state: Current GraphState
        api_key: OpenAI API key
        
    Returns:
        Updated GraphState
    """
    logger.info("Starting embedding generation worker")
    
    try:
        # Step 1: Generate embeddings for all chunks
        state = embed_all_chunks(state, api_key, show_progress=True)
        
        # Get embeddings and chunks
        embeddings = state["embeddings"]["chunk_embeddings"]
        
        # Collect chunks in order
        all_chunks = []
        for paper_id, chunks in state["chunks"].items():
            all_chunks.extend(chunks)
        
        # Step 2: Build FAISS index
        logger.info("Building FAISS index")
        index_builder = build_faiss_index(
            embeddings=embeddings,
            chunks=all_chunks,
            papers=state["papers"],
            index_type="FlatIP",
            normalize=True,
        )
        
        # Step 3: Validate index
        validation = index_builder.validate_index()
        if not validation["valid"]:
            logger.warning(f"Index validation issues: {validation['issues']}")
        
        # Step 4: Save index and metadata
        # Default paths (can be overridden in state)
        index_path = state.get("faiss_index_path", "./faiss_index.bin")
        metadata_path = state.get("faiss_meta_path", "./faiss_metadata.json")
        
        save_faiss_index(index_builder, index_path, version="1.0")
        save_metadata_mapping(index_builder.metadata_map, metadata_path, format="json")
        
        # Update state with paths
        state["faiss_index_path"] = index_path
        state["faiss_meta_path"] = metadata_path
        
        # Step 5: Update paper statuses to "embedded"
        # This ensures downstream stages (classification, etc.) can select these papers
        papers_embedded = 0
        for paper_id, chunks in state["chunks"].items():
            if paper_id in state["papers"]:
                paper = state["papers"][paper_id]
                # Only update papers that were successfully parsed (have chunks)
                if paper.processing_status in ELIGIBLE_FOR_EMBEDDING_UPDATE and len(chunks) > 0:
                    paper.processing_status = "embedded"
                    papers_embedded += 1
        
        logger.info(f"Updated {papers_embedded} papers to 'embedded' status")
        
        # Update processing phase
        state["current_phase"] = "embedded"
        
        logger.info("Embedding generation worker completed successfully")
        
        return state
        
    except Exception as e:
        logger.error(f"Embedding generation worker failed: {e}")
        state["errors"].append({
            "stage": "embedding_generation",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        })
        return state
