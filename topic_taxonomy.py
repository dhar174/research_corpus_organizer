#!/usr/bin/env python3
"""
RAG PDF Research Corpus System - Topic Modeling and Taxonomy Construction (Phase 8)

This module implements Phase 8 of the FINAL_NOTEBOOK_ACTION_PLAN.md:
- Step 8.1: Generate Paper-Level Embeddings (aggregate chunk embeddings)
- Step 8.2: Tier 1 Clustering (broad topics using KMeans/Agglomerative)
- Step 8.3: Generate Tier 1 Labels with GPT-5
- Step 8.4: Tier 2 Clustering (mid-level topics)
- Step 8.5: Generate Tier 2 Labels
- Step 8.6: Tier 3 Clustering (fine-grained topics)
- Step 8.7: Generate Tier 3 Labels
- Step 8.8: Build Complete TopicHierarchy
- Step 8.9: Visualize Taxonomy

Version: 1.0
Date: 2025-11-22
"""

import json
import logging
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Literal
import numpy as np

# OpenAI client
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not available. Install with: pip install openai")

# Clustering
try:
    from sklearn.cluster import KMeans, AgglomerativeClustering
    from sklearn.metrics import silhouette_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available. Install with: pip install scikit-learn")

# Visualization
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logging.warning("matplotlib not available. Install with: pip install matplotlib")

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False
    sns = None  # For type checking

# Progress bar
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from rag_models import (
    PaperRecord,
    PaperChunk,
    TopicNode,
    TopicHierarchy,
    GraphState,
    RunConfig,
)

logger = logging.getLogger(__name__)

# Export list
__all__ = [
    # Step 8.1: Paper-Level Embeddings
    'generate_paper_embeddings',
    'PaperEmbeddingGenerator',
    
    # Step 8.2: Tier 1 Clustering
    'build_tier1_taxonomy',
    'cluster_papers',
    'determine_optimal_k',
    
    # Step 8.3: Tier 1 Labels
    'generate_tier1_labels',
    'sample_representative_papers',
    'TopicLabelGenerator',
    
    # Step 8.4-8.7: Hierarchical Clustering
    'build_tier2_taxonomy',
    'build_tier3_taxonomy',
    'generate_tier2_labels',
    'generate_tier3_labels',
    
    # Step 8.8: Build Complete Hierarchy
    'build_complete_taxonomy',
    'validate_taxonomy_structure',
    'TaxonomyBuilder',
    
    # Step 8.9: Visualization
    'visualize_taxonomy',
    'plot_cluster_distributions',
    'generate_taxonomy_statistics',
    'TaxonomyVisualizer',
    
    # Worker
    'taxonomy_construction_worker',
]


# =============================================================================
# Step 8.1: Generate Paper-Level Embeddings
# =============================================================================

class PaperEmbeddingGenerator:
    """
    Generates paper-level embeddings by aggregating chunk embeddings.
    
    Supports multiple aggregation strategies:
    - mean: Simple average of all chunk embeddings
    - weighted_mean: Weighted by section importance (abstract, conclusion higher)
    - abstract_only: Use only abstract chunk if available
    """
    
    SECTION_WEIGHTS = {
        'abstract': 3.0,
        'introduction': 1.5,
        'conclusion': 2.0,
        'results': 1.2,
        'methods': 1.0,
        'discussion': 1.5,
        'other': 1.0,
        'references': 0.5,
    }
    
    def __init__(
        self,
        aggregation_method: Literal['mean', 'weighted_mean', 'abstract_only'] = 'weighted_mean'
    ):
        """
        Initialize the paper embedding generator.
        
        Args:
            aggregation_method: Method to aggregate chunk embeddings
        """
        self.aggregation_method = aggregation_method
        logger.info(f"Initialized PaperEmbeddingGenerator with method: {aggregation_method}")
    
    def aggregate_chunk_embeddings(
        self,
        chunks: List[PaperChunk],
        chunk_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Aggregate chunk embeddings into a single paper embedding.
        
        Args:
            chunks: List of paper chunks
            chunk_embeddings: Array of chunk embeddings (n_chunks, embedding_dim)
            
        Returns:
            Single paper embedding (embedding_dim,)
        """
        if len(chunks) == 0 or len(chunk_embeddings) == 0:
            raise ValueError("Cannot aggregate empty chunks or embeddings")
        
        if len(chunks) != len(chunk_embeddings):
            raise ValueError(f"Mismatch: {len(chunks)} chunks but {len(chunk_embeddings)} embeddings")
        
        if self.aggregation_method == 'abstract_only':
            # Find abstract chunk
            for i, chunk in enumerate(chunks):
                if chunk.section_label.lower() == 'abstract':
                    return chunk_embeddings[i]
            # Fallback to first chunk if no abstract
            logger.warning("No abstract chunk found, using first chunk")
            return chunk_embeddings[0]
        
        elif self.aggregation_method == 'mean':
            # Simple average
            return np.mean(chunk_embeddings, axis=0)
        
        elif self.aggregation_method == 'weighted_mean':
            # Weighted average by section importance
            weights = np.array([
                self.SECTION_WEIGHTS.get(chunk.section_label.lower(), 1.0)
                for chunk in chunks
            ])
            weights = weights / weights.sum()  # Normalize
            return np.average(chunk_embeddings, axis=0, weights=weights)
        
        else:
            raise ValueError(f"Unknown aggregation method: {self.aggregation_method}")
    
    def generate_paper_embeddings(
        self,
        state: GraphState,
        embeddings_array: np.ndarray,
        embedding_id_to_chunk: Dict[int, PaperChunk]
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, int]]:
        """
        Generate paper-level embeddings for all papers in state.
        
        Args:
            state: GraphState containing papers and chunks
            embeddings_array: Full FAISS embeddings array
            embedding_id_to_chunk: Mapping from embedding ID to chunk
            
        Returns:
            Tuple of (paper_embeddings dict, paper_to_idx mapping)
        """
        paper_embeddings = {}
        paper_to_idx = {}
        
        papers = state.get('papers', {})
        chunks_by_paper = state.get('chunks', {})
        
        logger.info(f"Generating paper-level embeddings for {len(papers)} papers")
        
        iterator = tqdm(papers.items(), desc="Generating paper embeddings") if TQDM_AVAILABLE else papers.items()
        
        for idx, (paper_id, paper) in enumerate(iterator):
            chunks = chunks_by_paper.get(paper_id, [])
            
            if not chunks:
                logger.warning(f"Paper {paper_id} has no chunks, skipping")
                continue
            
            # Get embeddings for all chunks of this paper
            chunk_embeddings_list = []
            valid_chunks = []
            
            for chunk in chunks:
                if chunk.embedding_id is not None:
                    if chunk.embedding_id < len(embeddings_array):
                        chunk_embeddings_list.append(embeddings_array[chunk.embedding_id])
                        valid_chunks.append(chunk)
                    else:
                        logger.warning(f"Invalid embedding_id {chunk.embedding_id} for chunk {chunk.chunk_id}")
            
            if not chunk_embeddings_list:
                logger.warning(f"Paper {paper_id} has no valid chunk embeddings, skipping")
                continue
            
            # Aggregate embeddings
            chunk_embeddings_np = np.array(chunk_embeddings_list)
            paper_embedding = self.aggregate_chunk_embeddings(valid_chunks, chunk_embeddings_np)
            
            paper_embeddings[paper_id] = paper_embedding
            paper_to_idx[paper_id] = idx
        
        logger.info(f"Generated embeddings for {len(paper_embeddings)} papers")
        return paper_embeddings, paper_to_idx


def generate_paper_embeddings(
    state: GraphState,
    embeddings_array: np.ndarray,
    embedding_id_to_chunk: Dict[int, PaperChunk],
    aggregation_method: Literal['mean', 'weighted_mean', 'abstract_only'] = 'weighted_mean'
) -> Tuple[Dict[str, np.ndarray], Dict[str, int]]:
    """
    Convenience function to generate paper-level embeddings.
    
    Args:
        state: GraphState containing papers and chunks
        embeddings_array: Full FAISS embeddings array
        embedding_id_to_chunk: Mapping from embedding ID to chunk
        aggregation_method: Method to aggregate chunk embeddings
        
    Returns:
        Tuple of (paper_embeddings dict, paper_to_idx mapping)
    """
    generator = PaperEmbeddingGenerator(aggregation_method)
    return generator.generate_paper_embeddings(state, embeddings_array, embedding_id_to_chunk)


# =============================================================================
# Step 8.2: Tier 1 Clustering (Broad Topics)
# =============================================================================

def determine_optimal_k(
    embeddings: np.ndarray,
    k_range: Tuple[int, int] = (3, 15),
    method: Literal['elbow', 'silhouette'] = 'silhouette'
) -> int:
    """
    Determine optimal number of clusters using elbow or silhouette method.
    
    Args:
        embeddings: Paper embeddings array
        k_range: Range of k values to test (min, max)
        method: Method to use ('elbow' or 'silhouette')
        
    Returns:
        Optimal k value
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for clustering")
    
    k_min, k_max = k_range
    n_samples = len(embeddings)
    
    # Limit k_max to reasonable value
    k_max = min(k_max, n_samples // 2)
    
    if k_min >= k_max:
        logger.warning(f"k_min ({k_min}) >= k_max ({k_max}), returning k_min")
        return k_min
    
    if method == 'silhouette':
        best_k = k_min
        best_score = -1
        
        for k in range(k_min, k_max + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            score = silhouette_score(embeddings, labels)
            
            logger.info(f"k={k}: silhouette score={score:.3f}")
            
            if score > best_score:
                best_score = score
                best_k = k
        
        logger.info(f"Optimal k={best_k} with silhouette score={best_score:.3f}")
        return best_k
    
    elif method == 'elbow':
        inertias = []
        
        for k in range(k_min, k_max + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(embeddings)
            inertias.append(kmeans.inertia_)
            logger.info(f"k={k}: inertia={kmeans.inertia_:.2f}")
        
        # Simple elbow detection: find max second derivative
        if len(inertias) >= 3:
            second_derivs = []
            for i in range(1, len(inertias) - 1):
                second_deriv = inertias[i - 1] - 2 * inertias[i] + inertias[i + 1]
                second_derivs.append(second_deriv)
            
            elbow_idx = second_derivs.index(max(second_derivs)) + 1
            optimal_k = k_min + elbow_idx
        else:
            optimal_k = k_min
        
        logger.info(f"Optimal k={optimal_k} using elbow method")
        return optimal_k
    
    else:
        raise ValueError(f"Unknown method: {method}")


def cluster_papers(
    embeddings: np.ndarray,
    n_clusters: int,
    method: Literal['kmeans', 'agglomerative'] = 'kmeans'
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Cluster paper embeddings using specified method.
    
    Args:
        embeddings: Paper embeddings array (n_papers, embedding_dim)
        n_clusters: Number of clusters
        method: Clustering method ('kmeans' or 'agglomerative')
        
    Returns:
        Tuple of (cluster labels, cluster centroids)
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for clustering")
    
    logger.info(f"Clustering {len(embeddings)} papers into {n_clusters} clusters using {method}")
    
    if method == 'kmeans':
        clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = clusterer.fit_predict(embeddings)
        centroids = clusterer.cluster_centers_
    
    elif method == 'agglomerative':
        clusterer = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
        labels = clusterer.fit_predict(embeddings)
        
        # Compute centroids manually
        centroids = np.zeros((n_clusters, embeddings.shape[1]))
        for i in range(n_clusters):
            cluster_points = embeddings[labels == i]
            if len(cluster_points) > 0:
                centroids[i] = cluster_points.mean(axis=0)
    
    else:
        raise ValueError(f"Unknown clustering method: {method}")
    
    # Log cluster sizes
    unique, counts = np.unique(labels, return_counts=True)
    for label, count in zip(unique, counts):
        logger.info(f"  Cluster {label}: {count} papers")
    
    return labels, centroids


def build_tier1_taxonomy(
    paper_embeddings: Dict[str, np.ndarray],
    paper_to_idx: Dict[str, int],
    config: RunConfig
) -> Tuple[List[Dict[str, Any]], np.ndarray, np.ndarray]:
    """
    Build Tier 1 topics using clustering.
    
    Args:
        paper_embeddings: Dict mapping paper_id to embedding
        paper_to_idx: Dict mapping paper_id to index
        config: RunConfig with clustering parameters
        
    Returns:
        Tuple of (tier1_clusters list, labels array, centroids array)
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for clustering")
    
    # Convert dict to array, maintaining order
    paper_ids = sorted(paper_embeddings.keys())
    embeddings_list = [paper_embeddings[pid] for pid in paper_ids]
    embeddings_array = np.array(embeddings_list)
    
    logger.info(f"Building Tier 1 taxonomy from {len(embeddings_array)} papers")
    
    # Determine number of clusters
    if config.cluster_tier1_target_k is not None:
        n_clusters = config.cluster_tier1_target_k
        logger.info(f"Using configured Tier 1 k={n_clusters}")
    else:
        # Use silhouette method to find optimal k
        n_clusters = determine_optimal_k(embeddings_array, k_range=(3, 12), method='silhouette')
        logger.info(f"Determined optimal Tier 1 k={n_clusters}")
    
    # Cluster papers
    labels, centroids = cluster_papers(embeddings_array, n_clusters, method='kmeans')
    
    # Build cluster data structures
    tier1_clusters = []
    for cluster_id in range(n_clusters):
        cluster_paper_ids = [paper_ids[i] for i in range(len(paper_ids)) if labels[i] == cluster_id]
        
        tier1_clusters.append({
            'cluster_id': cluster_id,
            'paper_ids': cluster_paper_ids,
            'paper_count': len(cluster_paper_ids),
            'centroid': centroids[cluster_id],
        })
    
    logger.info(f"Created {len(tier1_clusters)} Tier 1 clusters")
    return tier1_clusters, labels, centroids


# =============================================================================
# Step 8.3: Generate Tier 1 Labels with GPT-5.1
# =============================================================================

class TopicLabelGenerator:
    """
    Generates topic labels and descriptions using GPT-5.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5-mini",
        reasoning_effort: Literal["none", "low", "medium", "high"] = "high"
    ):
        """
        Initialize the topic label generator.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for labeling
            reasoning_effort: Reasoning effort level
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package is required")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.reasoning_effort = reasoning_effort
        logger.info(f"Initialized TopicLabelGenerator with model {model}")
    
    def sample_representative_papers(
        self,
        cluster_paper_ids: List[str],
        papers: Dict[str, PaperRecord],
        centroids: np.ndarray,
        paper_embeddings: Dict[str, np.ndarray],
        cluster_id: int,
        n_samples: int = 5
    ) -> List[PaperRecord]:
        """
        Sample representative papers from a cluster (closest to centroid).
        
        Args:
            cluster_paper_ids: Paper IDs in this cluster
            papers: All papers dict
            centroids: Cluster centroids
            paper_embeddings: Paper embeddings dict
            cluster_id: Current cluster ID
            n_samples: Number of papers to sample
            
        Returns:
            List of representative PaperRecords
        """
        centroid = centroids[cluster_id]
        
        # Calculate distances to centroid
        distances = []
        for paper_id in cluster_paper_ids:
            if paper_id in paper_embeddings:
                embedding = paper_embeddings[paper_id]
                distance = np.linalg.norm(embedding - centroid)
                distances.append((distance, paper_id))
        
        # Sort by distance and take closest
        distances.sort()
        top_paper_ids = [pid for _, pid in distances[:n_samples]]
        
        # Get paper records
        representative_papers = [papers[pid] for pid in top_paper_ids if pid in papers]
        
        logger.info(f"Sampled {len(representative_papers)} representative papers for cluster {cluster_id}")
        return representative_papers
    
    def generate_topic_label(
        self,
        representative_papers: List[PaperRecord],
        tier: int,
        parent_label: Optional[str] = None,
        sibling_labels: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Generate topic label and description using GPT-5.
        
        Args:
            representative_papers: Sample papers from this cluster
            tier: Tier level (1, 2, or 3)
            parent_label: Label of parent topic (for Tier 2/3)
            sibling_labels: Labels of sibling topics (for Tier 2/3)
            
        Returns:
            Dict with 'label' and 'description'
        """
        # Build context from representative papers
        papers_context = []
        for i, paper in enumerate(representative_papers[:10], 1):
            title = paper.title or "Untitled"
            abstract = paper.abstract_text or paper.full_summary or "No abstract available"
            # Truncate abstract
            if len(abstract) > 500:
                abstract = abstract[:500] + "..."
            # Escape title and abstract to prevent prompt injection
            safe_title = json.dumps(title)
            safe_abstract = json.dumps(abstract)
            papers_context.append(f"{i}. Title: {safe_title}\n   Abstract: {safe_abstract}")
        
        context_text = "\n\n".join(papers_context)
        
        # Build prompt based on tier
        if tier == 1:
            prompt = f"""You are analyzing a collection of research papers to identify broad research topics.

Below are {len(representative_papers)} representative papers from a cluster:

{context_text}

Based on these papers, provide:
1. A concise topic label (2-4 words) that captures the broad research area
2. A descriptive paragraph (2-3 sentences) explaining what this topic encompasses

Format your response as JSON:
{{
  "label": "Topic Label",
  "description": "Description of the topic..."
}}"""
        
        elif tier == 2:
            sibling_context = ""
            if sibling_labels:
                sibling_context = f"\n\nSibling topics at this level: {', '.join(sibling_labels)}\nEnsure your label is distinct from these siblings."
            
            prompt = f"""You are analyzing a sub-cluster of research papers within the broader topic: "{parent_label}"

Below are {len(representative_papers)} representative papers from this sub-cluster:

{context_text}

Based on these papers, provide:
1. A concise topic label (2-5 words) that captures this mid-level research area within {parent_label}
2. A descriptive paragraph (2-3 sentences) explaining what distinguishes this sub-topic{sibling_context}

Format your response as JSON:
{{
  "label": "Topic Label",
  "description": "Description of the topic..."
}}"""
        
        else:  # tier == 3
            sibling_context = ""
            if sibling_labels:
                sibling_context = f"\n\nSibling topics at this level: {', '.join(sibling_labels)}\nEnsure your label is distinct and specific."
            
            prompt = f"""You are analyzing a fine-grained sub-cluster of research papers within the topic: "{parent_label}"

Below are {len(representative_papers)} representative papers:

{context_text}

Based on these papers, provide:
1. A specific topic label (2-6 words) that captures this focused research area
2. A detailed description (2-3 sentences) highlighting what makes this topic specific{sibling_context}

Format your response as JSON:
{{
  "label": "Topic Label",
  "description": "Description of the topic..."
}}"""
        
        # Call GPT-5 using Responses API
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions="You are an expert at analyzing research papers and identifying topic hierarchies.",
                input=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            label = result.get('label', f'Tier {tier} Topic')
            description = result.get('description', 'No description available')
            
            logger.info(f"Generated Tier {tier} label: {label}")
            return {'label': label, 'description': description}
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from GPT: {e}")
            return {
                'label': f'Tier {tier} Topic',
                'description': f'Error parsing response: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error generating topic label: {e}")
            # Re-raise critical errors like authentication failures
            if 'authentication' in str(e).lower() or 'api_key' in str(e).lower():
                raise
            return {
                'label': f'Tier {tier} Topic',
                'description': f'Error: {str(e)}'
            }


def generate_tier1_labels(
    tier1_clusters: List[Dict[str, Any]],
    papers: Dict[str, PaperRecord],
    paper_embeddings: Dict[str, np.ndarray],
    centroids: np.ndarray,
    config: RunConfig,
    api_key: str
) -> List[TopicNode]:
    """
    Generate labels for Tier 1 topics using GPT-5.
    
    Args:
        tier1_clusters: Tier 1 cluster data
        papers: All papers dict
        paper_embeddings: Paper embeddings dict
        centroids: Cluster centroids
        config: RunConfig
        api_key: OpenAI API key
        
    Returns:
        List of TopicNode objects for Tier 1
    """
    generator = TopicLabelGenerator(
        api_key=api_key,
        model=config.taxonomy_model,
        reasoning_effort=config.taxonomy_reasoning_effort
    )
    
    tier1_topics = []
    
    iterator = tqdm(tier1_clusters, desc="Generating Tier 1 labels") if TQDM_AVAILABLE else tier1_clusters
    
    for cluster_data in iterator:
        cluster_id = cluster_data['cluster_id']
        cluster_paper_ids = cluster_data['paper_ids']
        
        # Sample representative papers
        representative_papers = generator.sample_representative_papers(
            cluster_paper_ids,
            papers,
            centroids,
            paper_embeddings,
            cluster_id,
            n_samples=5
        )
        
        # Generate label and description
        label_data = generator.generate_topic_label(representative_papers, tier=1)
        
        # Create TopicNode
        topic_id = f"T1_{cluster_id:02d}"
        topic = TopicNode(
            id=topic_id,
            label=label_data['label'],
            description=label_data['description'],
            paper_ids=cluster_paper_ids,
            parent_id=None,
            centroid=cluster_data['centroid'].tolist()
        )
        
        tier1_topics.append(topic)
        
        # Small delay to respect rate limits
        time.sleep(0.5)
    
    logger.info(f"Generated labels for {len(tier1_topics)} Tier 1 topics")
    return tier1_topics


def sample_representative_papers(
    cluster_paper_ids: List[str],
    papers: Dict[str, PaperRecord],
    centroids: np.ndarray,
    paper_embeddings: Dict[str, np.ndarray],
    cluster_id: int,
    n_samples: int = 5
) -> List[PaperRecord]:
    """
    Convenience function to sample representative papers (closest to centroid).
    
    Note: This function only performs sampling logic and does not make API calls.
    It extracts the sampling method from TopicLabelGenerator for standalone use.
    
    Args:
        cluster_paper_ids: Paper IDs in this cluster
        papers: All papers dict
        centroids: Cluster centroids
        paper_embeddings: Paper embeddings dict
        cluster_id: Current cluster ID
        n_samples: Number of papers to sample
        
    Returns:
        List of representative PaperRecords
    """
    centroid = centroids[cluster_id]
    
    # Calculate distances to centroid
    distances = []
    for paper_id in cluster_paper_ids:
        if paper_id in paper_embeddings:
            embedding = paper_embeddings[paper_id]
            distance = np.linalg.norm(embedding - centroid)
            distances.append((distance, paper_id))
    
    # Sort by distance and take closest
    distances.sort()
    top_paper_ids = [pid for _, pid in distances[:n_samples]]
    
    # Get paper records
    representative_papers = [papers[pid] for pid in top_paper_ids if pid in papers]
    
    logger.info(f"Sampled {len(representative_papers)} representative papers for cluster {cluster_id}")
    return representative_papers


# =============================================================================
# Step 8.4-8.7: Hierarchical Clustering (Tier 2 and Tier 3)
# =============================================================================

def build_tier2_taxonomy(
    tier1_topics: List[TopicNode],
    paper_embeddings: Dict[str, np.ndarray],
    config: RunConfig
) -> Tuple[List[Dict[str, Any]], Dict[int, np.ndarray], Dict[int, np.ndarray]]:
    """
    Build Tier 2 topics by clustering within each Tier 1 topic.
    
    Args:
        tier1_topics: Tier 1 TopicNode objects
        paper_embeddings: Paper embeddings dict
        config: RunConfig with clustering parameters
        
    Returns:
        Tuple of (tier2_clusters, tier2_labels_dict, tier2_centroids_dict)
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for clustering")
    
    tier2_clusters = []
    tier2_labels_dict = {}
    tier2_centroids_dict = {}
    
    logger.info(f"Building Tier 2 taxonomy from {len(tier1_topics)} Tier 1 topics")
    
    for t1_idx, t1_topic in enumerate(tier1_topics):
        t1_paper_ids = t1_topic.paper_ids
        
        # Get embeddings for this Tier 1 cluster
        t1_embeddings = [paper_embeddings[pid] for pid in t1_paper_ids if pid in paper_embeddings]
        
        if len(t1_embeddings) < 2:
            logger.warning(f"Tier 1 topic {t1_topic.id} has <2 papers, skipping Tier 2 clustering")
            continue
        
        t1_embeddings_array = np.array(t1_embeddings)
        
        # Determine number of Tier 2 clusters
        target_k = config.cluster_tier2_target_k or 3
        n_papers = len(t1_embeddings_array)
        n_clusters = min(target_k, max(2, n_papers // 2))
        
        if n_clusters < 2:
            logger.warning(f"Not enough papers for Tier 2 clustering in {t1_topic.id}")
            continue
        
        # Cluster
        labels, centroids = cluster_papers(t1_embeddings_array, n_clusters, method='kmeans')
        
        tier2_labels_dict[t1_idx] = labels
        tier2_centroids_dict[t1_idx] = centroids
        
        # Build cluster data structures
        for cluster_id in range(n_clusters):
            cluster_indices = [i for i in range(len(labels)) if labels[i] == cluster_id]
            cluster_paper_ids = [t1_paper_ids[i] for i in cluster_indices if i < len(t1_paper_ids)]
            
            tier2_clusters.append({
                'parent_tier1_id': t1_topic.id,
                'parent_tier1_idx': t1_idx,
                'cluster_id': cluster_id,
                'paper_ids': cluster_paper_ids,
                'paper_count': len(cluster_paper_ids),
                'centroid': centroids[cluster_id],
            })
    
    logger.info(f"Created {len(tier2_clusters)} Tier 2 clusters")
    return tier2_clusters, tier2_labels_dict, tier2_centroids_dict


def generate_tier2_labels(
    tier2_clusters: List[Dict[str, Any]],
    tier1_topics: List[TopicNode],
    papers: Dict[str, PaperRecord],
    paper_embeddings: Dict[str, np.ndarray],
    tier2_centroids_dict: Dict[int, np.ndarray],
    config: RunConfig,
    api_key: str
) -> List[TopicNode]:
    """
    Generate labels for Tier 2 topics using GPT-5.1.
    
    Args:
        tier2_clusters: Tier 2 cluster data
        tier1_topics: Tier 1 TopicNode objects
        papers: All papers dict
        paper_embeddings: Paper embeddings dict
        tier2_centroids_dict: Centroids for each Tier 1's Tier 2 clusters
        config: RunConfig
        api_key: OpenAI API key
        
    Returns:
        List of TopicNode objects for Tier 2
    """
    generator = TopicLabelGenerator(
        api_key=api_key,
        model=config.taxonomy_model,
        reasoning_effort=config.taxonomy_reasoning_effort
    )
    
    tier2_topics = []
    tier2_counter = 0
    
    # Group by parent
    clusters_by_parent = defaultdict(list)
    for cluster_data in tier2_clusters:
        parent_idx = cluster_data['parent_tier1_idx']
        clusters_by_parent[parent_idx].append(cluster_data)
    
    iterator = tqdm(clusters_by_parent.items(), desc="Generating Tier 2 labels") if TQDM_AVAILABLE else clusters_by_parent.items()
    
    for parent_idx, clusters in iterator:
        parent_topic = tier1_topics[parent_idx]
        centroids = tier2_centroids_dict.get(parent_idx)
        
        if centroids is None:
            continue
        
        # Get sibling labels
        sibling_labels = []
        
        for cluster_data in clusters:
            cluster_id = cluster_data['cluster_id']
            cluster_paper_ids = cluster_data['paper_ids']
            
            # Sample representative papers
            representative_papers = generator.sample_representative_papers(
                cluster_paper_ids,
                papers,
                centroids,
                paper_embeddings,
                cluster_id,
                n_samples=5
            )
            
            # Generate label with parent context
            label_data = generator.generate_topic_label(
                representative_papers,
                tier=2,
                parent_label=parent_topic.label,
                sibling_labels=sibling_labels
            )
            
            sibling_labels.append(label_data['label'])
            
            # Create TopicNode
            topic_id = f"T2_{tier2_counter:02d}"
            topic = TopicNode(
                id=topic_id,
                label=label_data['label'],
                description=label_data['description'],
                paper_ids=cluster_paper_ids,
                parent_id=parent_topic.id,
                centroid=cluster_data['centroid'].tolist()
            )
            
            tier2_topics.append(topic)
            tier2_counter += 1
            
            # Small delay
            time.sleep(0.5)
    
    logger.info(f"Generated labels for {len(tier2_topics)} Tier 2 topics")
    return tier2_topics


def build_tier3_taxonomy(
    tier2_topics: List[TopicNode],
    paper_embeddings: Dict[str, np.ndarray],
    config: RunConfig
) -> Tuple[List[Dict[str, Any]], Dict[str, np.ndarray], Dict[str, np.ndarray]]:
    """
    Build Tier 3 topics by clustering within each Tier 2 topic.
    
    Args:
        tier2_topics: Tier 2 TopicNode objects
        paper_embeddings: Paper embeddings dict
        config: RunConfig with clustering parameters
        
    Returns:
        Tuple of (tier3_clusters, tier3_labels_dict, tier3_centroids_dict)
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for clustering")
    
    tier3_clusters = []
    tier3_labels_dict = {}
    tier3_centroids_dict = {}
    
    logger.info(f"Building Tier 3 taxonomy from {len(tier2_topics)} Tier 2 topics")
    
    for t2_topic in tier2_topics:
        t2_paper_ids = t2_topic.paper_ids
        
        # Get embeddings for this Tier 2 cluster
        t2_embeddings = [paper_embeddings[pid] for pid in t2_paper_ids if pid in paper_embeddings]
        
        if len(t2_embeddings) < 2:
            logger.warning(f"Tier 2 topic {t2_topic.id} has <2 papers, skipping Tier 3 clustering")
            continue
        
        t2_embeddings_array = np.array(t2_embeddings)
        
        # Determine number of Tier 3 clusters
        target_k = config.cluster_tier3_target_k or 2
        n_papers = len(t2_embeddings_array)
        n_clusters = min(target_k, max(2, n_papers // 2))
        
        if n_clusters < 2:
            logger.warning(f"Not enough papers for Tier 3 clustering in {t2_topic.id}")
            continue
        
        # Cluster
        labels, centroids = cluster_papers(t2_embeddings_array, n_clusters, method='kmeans')
        
        tier3_labels_dict[t2_topic.id] = labels
        tier3_centroids_dict[t2_topic.id] = centroids
        
        # Build cluster data structures
        for cluster_id in range(n_clusters):
            cluster_indices = [i for i in range(len(labels)) if labels[i] == cluster_id]
            cluster_paper_ids = [t2_paper_ids[i] for i in cluster_indices if i < len(t2_paper_ids)]
            
            tier3_clusters.append({
                'parent_tier2_id': t2_topic.id,
                'cluster_id': cluster_id,
                'paper_ids': cluster_paper_ids,
                'paper_count': len(cluster_paper_ids),
                'centroid': centroids[cluster_id],
            })
    
    logger.info(f"Created {len(tier3_clusters)} Tier 3 clusters")
    return tier3_clusters, tier3_labels_dict, tier3_centroids_dict


def generate_tier3_labels(
    tier3_clusters: List[Dict[str, Any]],
    tier2_topics: List[TopicNode],
    papers: Dict[str, PaperRecord],
    paper_embeddings: Dict[str, np.ndarray],
    tier3_centroids_dict: Dict[str, np.ndarray],
    config: RunConfig,
    api_key: str
) -> List[TopicNode]:
    """
    Generate labels for Tier 3 topics using GPT-5.1.
    
    Args:
        tier3_clusters: Tier 3 cluster data
        tier2_topics: Tier 2 TopicNode objects
        papers: All papers dict
        paper_embeddings: Paper embeddings dict
        tier3_centroids_dict: Centroids for each Tier 2's Tier 3 clusters
        config: RunConfig
        api_key: OpenAI API key
        
    Returns:
        List of TopicNode objects for Tier 3
    """
    generator = TopicLabelGenerator(
        api_key=api_key,
        model=config.taxonomy_model,
        reasoning_effort=config.taxonomy_reasoning_effort
    )
    
    tier3_topics = []
    tier3_counter = 0
    
    # Build tier2 lookup
    tier2_by_id = {t.id: t for t in tier2_topics}
    
    # Group by parent
    clusters_by_parent = defaultdict(list)
    for cluster_data in tier3_clusters:
        parent_id = cluster_data['parent_tier2_id']
        clusters_by_parent[parent_id].append(cluster_data)
    
    iterator = tqdm(clusters_by_parent.items(), desc="Generating Tier 3 labels") if TQDM_AVAILABLE else clusters_by_parent.items()
    
    for parent_id, clusters in iterator:
        parent_topic = tier2_by_id.get(parent_id)
        if not parent_topic:
            continue
        
        centroids = tier3_centroids_dict.get(parent_id)
        if centroids is None:
            continue
        
        # Get sibling labels
        sibling_labels = []
        
        for cluster_data in clusters:
            cluster_id = cluster_data['cluster_id']
            cluster_paper_ids = cluster_data['paper_ids']
            
            # Sample representative papers
            representative_papers = generator.sample_representative_papers(
                cluster_paper_ids,
                papers,
                centroids,
                paper_embeddings,
                cluster_id,
                n_samples=5
            )
            
            # Generate label with parent context
            label_data = generator.generate_topic_label(
                representative_papers,
                tier=3,
                parent_label=parent_topic.label,
                sibling_labels=sibling_labels
            )
            
            sibling_labels.append(label_data['label'])
            
            # Create TopicNode
            topic_id = f"T3_{tier3_counter:02d}"
            topic = TopicNode(
                id=topic_id,
                label=label_data['label'],
                description=label_data['description'],
                paper_ids=cluster_paper_ids,
                parent_id=parent_topic.id,
                centroid=cluster_data['centroid'].tolist()
            )
            
            tier3_topics.append(topic)
            tier3_counter += 1
            
            # Small delay
            time.sleep(0.5)
    
    logger.info(f"Generated labels for {len(tier3_topics)} Tier 3 topics")
    return tier3_topics


# =============================================================================
# Step 8.8: Build Complete TopicHierarchy
# =============================================================================

class TaxonomyBuilder:
    """
    Builds complete 3-tier topic taxonomy.
    """
    
    def __init__(self, config: RunConfig, api_key: str):
        """
        Initialize taxonomy builder.
        
        Args:
            config: RunConfig
            api_key: OpenAI API key
        """
        self.config = config
        self.api_key = api_key
        logger.info("Initialized TaxonomyBuilder")
    
    def build_complete_taxonomy(
        self,
        state: GraphState,
        embeddings_array: np.ndarray,
        embedding_id_to_chunk: Dict[int, PaperChunk]
    ) -> TopicHierarchy:
        """
        Build complete 3-tier taxonomy.
        
        Args:
            state: GraphState containing papers and chunks
            embeddings_array: Full FAISS embeddings array
            embedding_id_to_chunk: Mapping from embedding ID to chunk
            
        Returns:
            TopicHierarchy object
        """
        papers = state.get('papers', {})
        
        # Step 8.1: Generate paper-level embeddings
        logger.info("Step 8.1: Generating paper-level embeddings")
        paper_embeddings, paper_to_idx = generate_paper_embeddings(
            state, embeddings_array, embedding_id_to_chunk, aggregation_method='weighted_mean'
        )
        
        # Step 8.2: Tier 1 clustering
        logger.info("Step 8.2: Building Tier 1 taxonomy")
        tier1_clusters, tier1_labels, tier1_centroids = build_tier1_taxonomy(
            paper_embeddings, paper_to_idx, self.config
        )
        
        # Step 8.3: Tier 1 labels
        logger.info("Step 8.3: Generating Tier 1 labels")
        tier1_topics = generate_tier1_labels(
            tier1_clusters, papers, paper_embeddings, tier1_centroids, self.config, self.api_key
        )
        
        # Step 8.4: Tier 2 clustering
        logger.info("Step 8.4: Building Tier 2 taxonomy")
        tier2_clusters, tier2_labels_dict, tier2_centroids_dict = build_tier2_taxonomy(
            tier1_topics, paper_embeddings, self.config
        )
        
        # Step 8.5: Tier 2 labels
        logger.info("Step 8.5: Generating Tier 2 labels")
        tier2_topics = generate_tier2_labels(
            tier2_clusters, tier1_topics, papers, paper_embeddings,
            tier2_centroids_dict, self.config, self.api_key
        )
        
        # Step 8.6: Tier 3 clustering
        logger.info("Step 8.6: Building Tier 3 taxonomy")
        tier3_clusters, tier3_labels_dict, tier3_centroids_dict = build_tier3_taxonomy(
            tier2_topics, paper_embeddings, self.config
        )
        
        # Step 8.7: Tier 3 labels
        logger.info("Step 8.7: Generating Tier 3 labels")
        tier3_topics = generate_tier3_labels(
            tier3_clusters, tier2_topics, papers, paper_embeddings,
            tier3_centroids_dict, self.config, self.api_key
        )
        
        # Step 8.8: Build TopicHierarchy
        logger.info("Step 8.8: Building TopicHierarchy structure")
        taxonomy_version = f"v1.0_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        hierarchy = TopicHierarchy(
            taxonomy_version=taxonomy_version,
            created_at=datetime.now(),
            notes=f"3-tier taxonomy built from {len(papers)} papers",
            total_papers=len(papers),
            tier1=tier1_topics,
            tier2=tier2_topics,
            tier3=tier3_topics,
            clustering_method='kmeans',
            labeling_model=self.config.taxonomy_model
        )
        
        # Validate hierarchy
        validation = hierarchy.validate_hierarchy()
        if validation['valid']:
            logger.info(f"Taxonomy validated successfully: {validation}")
        else:
            logger.warning(f"Taxonomy validation issues: {validation}")
        
        return hierarchy


def build_complete_taxonomy(
    state: GraphState,
    embeddings_array: np.ndarray,
    embedding_id_to_chunk: Dict[int, PaperChunk],
    config: RunConfig,
    api_key: str
) -> TopicHierarchy:
    """
    Convenience function to build complete taxonomy.
    
    Args:
        state: GraphState containing papers and chunks
        embeddings_array: Full FAISS embeddings array
        embedding_id_to_chunk: Mapping from embedding ID to chunk
        config: RunConfig
        api_key: OpenAI API key
        
    Returns:
        TopicHierarchy object
    """
    builder = TaxonomyBuilder(config, api_key)
    return builder.build_complete_taxonomy(state, embeddings_array, embedding_id_to_chunk)


def validate_taxonomy_structure(hierarchy: TopicHierarchy) -> Dict[str, Any]:
    """
    Validate taxonomy structure and return detailed results.
    
    Args:
        hierarchy: TopicHierarchy to validate
        
    Returns:
        Dict with validation results
    """
    return hierarchy.validate_hierarchy()


# =============================================================================
# Step 8.9: Visualize Taxonomy
# =============================================================================

class TaxonomyVisualizer:
    """
    Visualizes topic taxonomy with charts and statistics.
    """
    
    def __init__(self, hierarchy: TopicHierarchy):
        """
        Initialize visualizer.
        
        Args:
            hierarchy: TopicHierarchy to visualize
        """
        self.hierarchy = hierarchy
        logger.info("Initialized TaxonomyVisualizer")
    
    def generate_statistics(self) -> Dict[str, Any]:
        """
        Generate comprehensive statistics about the taxonomy.
        
        Returns:
            Dict with statistics
        """
        stats = self.hierarchy.get_statistics()
        
        # Add more detailed stats
        tier1_sizes = [t.paper_count for t in self.hierarchy.tier1]
        tier2_sizes = [t.paper_count for t in self.hierarchy.tier2]
        tier3_sizes = [t.paper_count for t in self.hierarchy.tier3]
        
        stats.update({
            'tier1_size_min': min(tier1_sizes) if tier1_sizes else 0,
            'tier1_size_max': max(tier1_sizes) if tier1_sizes else 0,
            'tier1_size_median': np.median(tier1_sizes) if tier1_sizes else 0,
            'tier2_size_min': min(tier2_sizes) if tier2_sizes else 0,
            'tier2_size_max': max(tier2_sizes) if tier2_sizes else 0,
            'tier2_size_median': np.median(tier2_sizes) if tier2_sizes else 0,
            'tier3_size_min': min(tier3_sizes) if tier3_sizes else 0,
            'tier3_size_max': max(tier3_sizes) if tier3_sizes else 0,
            'tier3_size_median': np.median(tier3_sizes) if tier3_sizes else 0,
        })
        
        return stats
    
    def plot_cluster_distributions(self, output_path: Optional[str] = None) -> Optional[str]:
        """
        Plot cluster size distributions for each tier.
        
        Args:
            output_path: Path to save plot (optional)
            
        Returns:
            Path to saved plot or None
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("matplotlib not available, skipping visualization")
            return None
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # Tier 1 distribution
        tier1_sizes = [t.paper_count for t in self.hierarchy.tier1]
        tier1_labels = [t.label[:20] + '...' if len(t.label) > 20 else t.label for t in self.hierarchy.tier1]
        
        axes[0].bar(range(len(tier1_sizes)), tier1_sizes)
        axes[0].set_title('Tier 1: Topic Sizes')
        axes[0].set_xlabel('Topic')
        axes[0].set_ylabel('Number of Papers')
        axes[0].set_xticks(range(len(tier1_labels)))
        axes[0].set_xticklabels(tier1_labels, rotation=45, ha='right')
        
        # Tier 2 distribution
        tier2_sizes = [t.paper_count for t in self.hierarchy.tier2]
        
        axes[1].hist(tier2_sizes, bins=min(20, len(tier2_sizes)), edgecolor='black')
        axes[1].set_title('Tier 2: Size Distribution')
        axes[1].set_xlabel('Papers per Topic')
        axes[1].set_ylabel('Number of Topics')
        
        # Tier 3 distribution
        tier3_sizes = [t.paper_count for t in self.hierarchy.tier3]
        
        axes[2].hist(tier3_sizes, bins=min(20, len(tier3_sizes)), edgecolor='black')
        axes[2].set_title('Tier 3: Size Distribution')
        axes[2].set_xlabel('Papers per Topic')
        axes[2].set_ylabel('Number of Topics')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            logger.info(f"Saved cluster distribution plot to {output_path}")
            plt.close()
            return output_path
        else:
            plt.close()
            return None
    
    def display_taxonomy_summary(self) -> str:
        """
        Create a text summary of the taxonomy.
        
        Returns:
            Formatted string summary
        """
        lines = [
            "=" * 80,
            "TAXONOMY SUMMARY",
            "=" * 80,
            f"Version: {self.hierarchy.taxonomy_version}",
            f"Created: {self.hierarchy.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Papers: {self.hierarchy.total_papers}",
            f"Clustering Method: {self.hierarchy.clustering_method}",
            f"Labeling Model: {self.hierarchy.labeling_model}",
            "",
            "TIER 1 TOPICS:",
            "-" * 80,
        ]
        
        for t1 in self.hierarchy.tier1:
            lines.append(f"\n{t1.id}: {t1.label} ({t1.paper_count} papers)")
            lines.append(f"   {t1.description}")
            
            # Show Tier 2 children
            t2_children = self.hierarchy.get_tier2_topics(t1.id)
            if t2_children:
                lines.append(f"   Tier 2 sub-topics:")
                for t2 in t2_children:
                    lines.append(f"     - {t2.id}: {t2.label} ({t2.paper_count} papers)")
        
        lines.extend([
            "",
            "=" * 80,
            f"Total Topics: Tier1={len(self.hierarchy.tier1)}, Tier2={len(self.hierarchy.tier2)}, Tier3={len(self.hierarchy.tier3)}",
            "=" * 80,
        ])
        
        return "\n".join(lines)


def visualize_taxonomy(
    hierarchy: TopicHierarchy,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate visualizations and statistics for taxonomy.
    
    Args:
        hierarchy: TopicHierarchy to visualize
        output_dir: Directory to save visualizations (optional)
        
    Returns:
        Dict with statistics and file paths
    """
    visualizer = TaxonomyVisualizer(hierarchy)
    
    # Generate statistics
    stats = visualizer.generate_statistics()
    
    # Generate plots
    plot_path = None
    if output_dir:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        plot_path = str(output_dir_path / f"taxonomy_distribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        visualizer.plot_cluster_distributions(plot_path)
    
    # Generate text summary
    summary = visualizer.display_taxonomy_summary()
    
    return {
        'statistics': stats,
        'plot_path': plot_path,
        'summary': summary
    }


def plot_cluster_distributions(
    hierarchy: TopicHierarchy,
    output_path: Optional[str] = None
) -> Optional[str]:
    """
    Convenience function to plot cluster distributions.
    
    Args:
        hierarchy: TopicHierarchy to visualize
        output_path: Path to save plot
        
    Returns:
        Path to saved plot or None
    """
    visualizer = TaxonomyVisualizer(hierarchy)
    return visualizer.plot_cluster_distributions(output_path)


def generate_taxonomy_statistics(hierarchy: TopicHierarchy) -> Dict[str, Any]:
    """
    Convenience function to generate taxonomy statistics.
    
    Args:
        hierarchy: TopicHierarchy
        
    Returns:
        Dict with statistics
    """
    visualizer = TaxonomyVisualizer(hierarchy)
    return visualizer.generate_statistics()


# =============================================================================
# LangGraph Worker
# =============================================================================

def taxonomy_construction_worker(
    state: GraphState,
    embeddings_array: np.ndarray,
    embedding_id_to_chunk: Dict[int, PaperChunk],
    api_key: str,
    output_dir: Optional[str] = None
) -> GraphState:
    """
    LangGraph worker node for taxonomy construction (Phase 8).
    
    Args:
        state: Current GraphState
        embeddings_array: Full FAISS embeddings array
        embedding_id_to_chunk: Mapping from embedding ID to chunk
        api_key: OpenAI API key
        output_dir: Optional directory for saving visualizations
        
    Returns:
        Updated GraphState with taxonomy
    """
    config = state.get('config')
    if not config:
        raise ValueError("RunConfig not found in state")
    
    logger.info("Starting taxonomy construction worker (Phase 8)")
    
    # Build complete taxonomy
    builder = TaxonomyBuilder(config, api_key)
    hierarchy = builder.build_complete_taxonomy(state, embeddings_array, embedding_id_to_chunk)
    
    # Update state
    state['topic_hierarchy'] = hierarchy
    state['current_phase'] = 'taxonomy_constructed'
    
    # Generate visualizations if output_dir provided
    if output_dir:
        viz_results = visualize_taxonomy(hierarchy, output_dir)
        logger.info(f"Taxonomy visualization saved to {viz_results.get('plot_path')}")
        print(viz_results['summary'])
    
    logger.info("Taxonomy construction completed successfully")
    return state
