#!/usr/bin/env python3
"""
RAG PDF Research Corpus System - Advanced Visualizations (Phase 22b)

This module implements Phase 22b (Step 22.5) of the FINAL_NOTEBOOK_ACTION_PLAN.md:
- Interactive topic map
- Paper embeddings visualization (t-SNE/UMAP)
- Word clouds per topic
- Author collaboration networks
- Topic evolution charts

Version: 1.0
Date: 2025-11-25
"""

import logging
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Literal
import io
import base64

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy not available. Install with: pip install numpy")

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib not available. Install with: pip install matplotlib")

try:
    from sklearn.manifold import TSNE
    from sklearn.decomposition import PCA
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Install with: pip install scikit-learn")

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    logger.info("UMAP not available. Install with: pip install umap-learn")

try:
    from wordcloud import WordCloud
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False
    logger.info("WordCloud not available. Install with: pip install wordcloud")

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.info("NetworkX not available. Install with: pip install networkx")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.info("Plotly not available. Install with: pip install plotly")

from rag_models import (
    PaperRecord,
    PaperChunk,
    TopicHierarchy,
    TopicNode,
    GraphState,
)

# Export list
__all__ = [
    # Interactive Topic Map
    'create_interactive_topic_map',
    'create_static_topic_map',
    'TopicMapGenerator',
    
    # Paper Embeddings Visualization
    'visualize_paper_embeddings',
    'reduce_embeddings_tsne',
    'reduce_embeddings_umap',
    'reduce_embeddings_pca',
    'EmbeddingVisualizer',
    
    # Word Clouds
    'generate_topic_wordcloud',
    'generate_all_topic_wordclouds',
    'WordCloudGenerator',
    
    # Author Collaboration Networks
    'build_author_collaboration_network',
    'visualize_author_network',
    'get_author_statistics',
    'AuthorNetworkAnalyzer',
    
    # Topic Evolution Charts
    'create_topic_evolution_chart',
    'get_topic_trends_by_year',
    'TopicEvolutionAnalyzer',
    
    # Utility Functions
    'save_figure_to_base64',
    'generate_visualization_report',
]


# =============================================================================
# Interactive Topic Map
# =============================================================================

class TopicMapGenerator:
    """
    Generates interactive and static topic maps for the taxonomy.
    
    Visualizes the hierarchical topic structure with paper counts
    and interactive exploration capabilities.
    """
    
    def __init__(self, hierarchy: TopicHierarchy):
        """
        Initialize topic map generator.
        
        Args:
            hierarchy: TopicHierarchy with tier1, tier2, tier3 topics
        """
        self.hierarchy = hierarchy
        logger.info(f"TopicMapGenerator initialized with {len(hierarchy.tier1)} tier1 topics")
    
    def create_interactive_map(self) -> Optional[Any]:
        """
        Create an interactive topic map using Plotly.
        
        Returns:
            Plotly figure object or None if Plotly not available
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available for interactive map")
            return None
        
        # Build tree structure for treemap
        labels = []
        parents = []
        values = []
        text = []
        
        # Root node
        labels.append("Research Corpus")
        parents.append("")
        values.append(self.hierarchy.total_papers)
        text.append(f"Total: {self.hierarchy.total_papers} papers")
        
        # Tier 1 topics
        for t1 in self.hierarchy.tier1:
            labels.append(t1.label)
            parents.append("Research Corpus")
            values.append(t1.paper_count)
            text.append(f"{t1.paper_count} papers<br>{t1.description[:100]}...")
        
        # Tier 2 topics
        for t2 in self.hierarchy.tier2:
            parent_topic = self.hierarchy.get_topic_by_id(t2.parent_id)
            parent_label = parent_topic.label if parent_topic else "Research Corpus"
            
            labels.append(f"{t2.label}")
            parents.append(parent_label)
            values.append(t2.paper_count)
            text.append(f"{t2.paper_count} papers<br>{t2.description[:100]}...")
        
        # Create treemap
        fig = go.Figure(go.Treemap(
            labels=labels,
            parents=parents,
            values=values,
            text=text,
            hovertemplate='<b>%{label}</b><br>%{text}<extra></extra>',
            marker=dict(
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='Papers')
            ),
            textinfo='label+value',
            pathbar=dict(visible=True),
        ))
        
        fig.update_layout(
            title=dict(
                text="Interactive Topic Map",
                font=dict(size=20)
            ),
            margin=dict(t=50, l=25, r=25, b=25),
        )
        
        logger.info("Created interactive topic map")
        return fig
    
    def create_sunburst(self) -> Optional[Any]:
        """
        Create a sunburst chart of the topic hierarchy.
        
        Returns:
            Plotly figure object or None if Plotly not available
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available for sunburst chart")
            return None
        
        # Build data for sunburst
        ids = ["corpus"]
        labels = ["Research Corpus"]
        parents = [""]
        values = [self.hierarchy.total_papers]
        
        # Tier 1
        for t1 in self.hierarchy.tier1:
            ids.append(t1.id)
            labels.append(t1.label)
            parents.append("corpus")
            values.append(t1.paper_count)
        
        # Tier 2
        for t2 in self.hierarchy.tier2:
            ids.append(t2.id)
            labels.append(t2.label)
            parents.append(t2.parent_id if t2.parent_id else "corpus")
            values.append(t2.paper_count)
        
        # Tier 3
        for t3 in self.hierarchy.tier3:
            ids.append(t3.id)
            labels.append(t3.label)
            parents.append(t3.parent_id if t3.parent_id else "corpus")
            values.append(t3.paper_count)
        
        fig = go.Figure(go.Sunburst(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            hovertemplate='<b>%{label}</b><br>Papers: %{value}<extra></extra>',
            maxdepth=3,
        ))
        
        fig.update_layout(
            title="Topic Hierarchy Sunburst",
            margin=dict(t=50, l=0, r=0, b=0),
        )
        
        logger.info("Created sunburst chart")
        return fig
    
    def create_static_map(self, output_path: Optional[str] = None) -> Optional[str]:
        """
        Create a static topic map using matplotlib.
        
        Args:
            output_path: Path to save the figure
            
        Returns:
            Path to saved figure or None
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib not available for static map")
            return None
        
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # Create horizontal bar chart for tier 1 topics
        tier1_labels = [t.label for t in self.hierarchy.tier1]
        tier1_counts = [t.paper_count for t in self.hierarchy.tier1]
        
        # Sort by count
        sorted_data = sorted(zip(tier1_counts, tier1_labels), reverse=True)
        tier1_counts, tier1_labels = zip(*sorted_data) if sorted_data else ([], [])
        
        y_pos = range(len(tier1_labels))
        colors = plt.cm.viridis(np.linspace(0, 0.8, len(tier1_labels)))
        
        bars = ax.barh(y_pos, tier1_counts, color=colors)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(tier1_labels)
        ax.invert_yaxis()  # Largest at top
        ax.set_xlabel('Number of Papers')
        ax.set_title('Topic Distribution (Tier 1)', fontsize=14, fontweight='bold')
        
        # Add value labels on bars
        for bar, count in zip(bars, tier1_counts):
            width = bar.get_width()
            ax.text(width + 0.5, bar.get_y() + bar.get_height()/2,
                   str(count), ha='left', va='center', fontsize=9)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            logger.info(f"Saved static topic map to {output_path}")
            plt.close()
            return output_path
        else:
            plt.close()
            return None


def create_interactive_topic_map(
    hierarchy: TopicHierarchy,
    chart_type: Literal['treemap', 'sunburst'] = 'treemap'
) -> Optional[Any]:
    """
    Create an interactive topic map.
    
    Args:
        hierarchy: TopicHierarchy object
        chart_type: Type of chart ('treemap' or 'sunburst')
        
    Returns:
        Plotly figure or None
    """
    generator = TopicMapGenerator(hierarchy)
    
    if chart_type == 'sunburst':
        return generator.create_sunburst()
    else:
        return generator.create_interactive_map()


def create_static_topic_map(
    hierarchy: TopicHierarchy,
    output_path: Optional[str] = None
) -> Optional[str]:
    """
    Create a static topic map.
    
    Args:
        hierarchy: TopicHierarchy object
        output_path: Path to save the figure
        
    Returns:
        Path to saved figure or None
    """
    generator = TopicMapGenerator(hierarchy)
    return generator.create_static_map(output_path)


# =============================================================================
# Paper Embeddings Visualization (t-SNE/UMAP)
# =============================================================================

class EmbeddingVisualizer:
    """
    Visualizes paper embeddings in 2D using dimensionality reduction.
    
    Supports t-SNE, UMAP, and PCA for dimensionality reduction.
    """
    
    def __init__(
        self,
        embeddings: np.ndarray,
        paper_metadata: List[Dict[str, Any]],
    ):
        """
        Initialize embedding visualizer.
        
        Args:
            embeddings: Paper embeddings array (n_papers, embedding_dim)
            paper_metadata: List of dicts with paper info (title, topic, year, etc.)
        """
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy required for embedding visualization")
        
        self.embeddings = embeddings
        self.paper_metadata = paper_metadata
        self.reduced_embeddings = None
        self.reduction_method = None
        
        logger.info(f"EmbeddingVisualizer initialized with {len(embeddings)} embeddings")
    
    def reduce_dimensions(
        self,
        method: Literal['tsne', 'umap', 'pca'] = 'tsne',
        n_components: int = 2,
        **kwargs
    ) -> np.ndarray:
        """
        Reduce embedding dimensions for visualization.
        
        Args:
            method: Reduction method ('tsne', 'umap', or 'pca')
            n_components: Target dimensions (usually 2)
            **kwargs: Additional parameters for the reduction method
            
        Returns:
            Reduced embeddings array
        """
        if method == 'tsne':
            if not SKLEARN_AVAILABLE:
                raise ImportError("scikit-learn required for t-SNE")
            
            perplexity = kwargs.get('perplexity', min(30, len(self.embeddings) - 1))
            n_iter = kwargs.get('n_iter', 1000)
            
            tsne = TSNE(
                n_components=n_components,
                perplexity=perplexity,
                n_iter=n_iter,
                random_state=42,
            )
            self.reduced_embeddings = tsne.fit_transform(self.embeddings)
            self.reduction_method = 'tsne'
            
        elif method == 'umap':
            if not UMAP_AVAILABLE:
                raise ImportError("umap-learn required for UMAP")
            
            n_neighbors = kwargs.get('n_neighbors', min(15, len(self.embeddings) - 1))
            min_dist = kwargs.get('min_dist', 0.1)
            
            reducer = umap.UMAP(
                n_components=n_components,
                n_neighbors=n_neighbors,
                min_dist=min_dist,
                random_state=42,
            )
            self.reduced_embeddings = reducer.fit_transform(self.embeddings)
            self.reduction_method = 'umap'
            
        elif method == 'pca':
            if not SKLEARN_AVAILABLE:
                raise ImportError("scikit-learn required for PCA")
            
            pca = PCA(n_components=n_components, random_state=42)
            self.reduced_embeddings = pca.fit_transform(self.embeddings)
            self.reduction_method = 'pca'
            
        else:
            raise ValueError(f"Unknown reduction method: {method}")
        
        logger.info(f"Reduced embeddings to {n_components}D using {method}")
        return self.reduced_embeddings
    
    def create_interactive_plot(
        self,
        color_by: str = 'topic',
    ) -> Optional[Any]:
        """
        Create an interactive scatter plot of embeddings.
        
        Args:
            color_by: Field to color points by ('topic', 'year', etc.)
            
        Returns:
            Plotly figure or None
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available for interactive plot")
            return None
        
        if self.reduced_embeddings is None:
            self.reduce_dimensions()
        
        # Prepare data for plotly
        x = self.reduced_embeddings[:, 0]
        y = self.reduced_embeddings[:, 1]
        
        # Get color values
        colors = []
        hover_texts = []
        for meta in self.paper_metadata:
            if color_by == 'topic':
                colors.append(meta.get('tier1_topic_name', 'Unknown'))
            elif color_by == 'year':
                colors.append(str(meta.get('year', 'Unknown')))
            else:
                colors.append(str(meta.get(color_by, 'Unknown')))
            
            # Build hover text
            title = meta.get('title', 'Unknown')[:50]
            topic = meta.get('tier1_topic_name', 'Unknown')
            year = meta.get('year', 'Unknown')
            hover_texts.append(f"<b>{title}...</b><br>Topic: {topic}<br>Year: {year}")
        
        fig = px.scatter(
            x=x, y=y,
            color=colors,
            hover_name=hover_texts,
            title=f'Paper Embeddings ({self.reduction_method.upper()})',
            labels={'x': 'Dimension 1', 'y': 'Dimension 2', 'color': color_by.title()},
        )
        
        fig.update_traces(
            marker=dict(size=8, opacity=0.7),
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=hover_texts,
        )
        
        fig.update_layout(
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="right",
                x=1.3
            ),
            margin=dict(r=200),
        )
        
        logger.info("Created interactive embedding plot")
        return fig
    
    def create_static_plot(
        self,
        color_by: str = 'topic',
        output_path: Optional[str] = None,
        figsize: Tuple[int, int] = (12, 10),
    ) -> Optional[str]:
        """
        Create a static scatter plot of embeddings.
        
        Args:
            color_by: Field to color points by
            output_path: Path to save the figure
            figsize: Figure size
            
        Returns:
            Path to saved figure or None
        """
        if not MATPLOTLIB_AVAILABLE or not NUMPY_AVAILABLE:
            logger.warning("Matplotlib/NumPy not available for static plot")
            return None
        
        if self.reduced_embeddings is None:
            self.reduce_dimensions()
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Get unique categories for coloring
        categories = []
        for meta in self.paper_metadata:
            if color_by == 'topic':
                categories.append(meta.get('tier1_topic_name', 'Unknown'))
            elif color_by == 'year':
                categories.append(str(meta.get('year', 'Unknown')))
            else:
                categories.append(str(meta.get(color_by, 'Unknown')))
        
        unique_cats = list(set(categories))
        colors = plt.cm.tab20(np.linspace(0, 1, len(unique_cats)))
        color_map = dict(zip(unique_cats, colors))
        
        # Plot each category
        for cat in unique_cats:
            mask = [c == cat for c in categories]
            indices = np.where(mask)[0]
            ax.scatter(
                self.reduced_embeddings[indices, 0],
                self.reduced_embeddings[indices, 1],
                c=[color_map[cat]],
                label=cat[:30] + '...' if len(cat) > 30 else cat,
                alpha=0.7,
                s=50,
            )
        
        ax.set_xlabel('Dimension 1')
        ax.set_ylabel('Dimension 2')
        ax.set_title(f'Paper Embeddings ({self.reduction_method.upper() if self.reduction_method else ""})')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            logger.info(f"Saved embedding plot to {output_path}")
            plt.close()
            return output_path
        else:
            plt.close()
            return None


def reduce_embeddings_tsne(
    embeddings: np.ndarray,
    n_components: int = 2,
    perplexity: int = 30,
    n_iter: int = 1000,
) -> np.ndarray:
    """
    Reduce embeddings using t-SNE.
    
    Args:
        embeddings: High-dimensional embeddings
        n_components: Target dimensions
        perplexity: t-SNE perplexity parameter
        n_iter: Number of iterations
        
    Returns:
        Reduced embeddings
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn required for t-SNE")
    
    perplexity = min(perplexity, len(embeddings) - 1)
    tsne = TSNE(n_components=n_components, perplexity=perplexity, n_iter=n_iter, random_state=42)
    return tsne.fit_transform(embeddings)


def reduce_embeddings_umap(
    embeddings: np.ndarray,
    n_components: int = 2,
    n_neighbors: int = 15,
    min_dist: float = 0.1,
) -> np.ndarray:
    """
    Reduce embeddings using UMAP.
    
    Args:
        embeddings: High-dimensional embeddings
        n_components: Target dimensions
        n_neighbors: UMAP n_neighbors parameter
        min_dist: UMAP min_dist parameter
        
    Returns:
        Reduced embeddings
    """
    if not UMAP_AVAILABLE:
        raise ImportError("umap-learn required for UMAP")
    
    n_neighbors = min(n_neighbors, len(embeddings) - 1)
    reducer = umap.UMAP(n_components=n_components, n_neighbors=n_neighbors, min_dist=min_dist, random_state=42)
    return reducer.fit_transform(embeddings)


def reduce_embeddings_pca(
    embeddings: np.ndarray,
    n_components: int = 2,
) -> np.ndarray:
    """
    Reduce embeddings using PCA.
    
    Args:
        embeddings: High-dimensional embeddings
        n_components: Target dimensions
        
    Returns:
        Reduced embeddings
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn required for PCA")
    
    pca = PCA(n_components=n_components, random_state=42)
    return pca.fit_transform(embeddings)


def visualize_paper_embeddings(
    embeddings: np.ndarray,
    paper_metadata: List[Dict[str, Any]],
    method: Literal['tsne', 'umap', 'pca'] = 'tsne',
    color_by: str = 'topic',
    interactive: bool = True,
    output_path: Optional[str] = None,
) -> Optional[Any]:
    """
    Visualize paper embeddings in 2D.
    
    Args:
        embeddings: Paper embeddings array
        paper_metadata: List of paper metadata dicts
        method: Dimensionality reduction method
        color_by: Field to color points by
        interactive: Whether to create interactive plot
        output_path: Path to save static plot
        
    Returns:
        Plotly figure (if interactive) or path to saved figure
    """
    visualizer = EmbeddingVisualizer(embeddings, paper_metadata)
    visualizer.reduce_dimensions(method=method)
    
    if interactive:
        return visualizer.create_interactive_plot(color_by=color_by)
    else:
        return visualizer.create_static_plot(color_by=color_by, output_path=output_path)


# =============================================================================
# Word Clouds per Topic
# =============================================================================

class WordCloudGenerator:
    """
    Generates word clouds for topics based on paper content.
    """
    
    # Common academic stop words to filter out
    STOP_WORDS = {
        'the', 'and', 'for', 'that', 'this', 'with', 'are', 'from', 'our',
        'can', 'has', 'have', 'been', 'were', 'was', 'will', 'also', 'more',
        'than', 'which', 'such', 'these', 'they', 'their', 'use', 'used',
        'using', 'based', 'show', 'shows', 'shown', 'paper', 'approach',
        'method', 'methods', 'model', 'models', 'results', 'propose', 'proposed',
        'work', 'works', 'study', 'studies', 'data', 'first', 'new', 'one',
        'two', 'three', 'however', 'present', 'presents', 'performance',
    }
    
    def __init__(
        self,
        state: GraphState,
        min_word_length: int = 3,
        max_words: int = 100,
    ):
        """
        Initialize word cloud generator.
        
        Args:
            state: GraphState with papers and topic hierarchy
            min_word_length: Minimum word length to include
            max_words: Maximum words in word cloud
        """
        self.state = state
        self.min_word_length = min_word_length
        self.max_words = max_words
        
        papers = state.get('papers', {})
        logger.info(f"WordCloudGenerator initialized with {len(papers)} papers")
    
    def get_topic_text(self, topic_id: str, tier: int = 1) -> str:
        """
        Get combined text from all papers in a topic.
        
        Args:
            topic_id: Topic ID
            tier: Topic tier (1, 2, or 3)
            
        Returns:
            Combined text from topic papers
        """
        papers = self.state.get('papers', {})
        text_parts = []
        
        for paper in papers.values():
            # Check if paper is in this topic
            if tier == 1 and paper.tier1_topic == topic_id:
                pass  # Include this paper
            elif tier == 2 and paper.tier2_topic == topic_id:
                pass
            elif tier == 3 and paper.tier3_topic == topic_id:
                pass
            else:
                continue
            
            # Add title and abstract
            if paper.title:
                text_parts.append(paper.title)
            if paper.abstract_text:
                text_parts.append(paper.abstract_text)
            if paper.full_summary:
                text_parts.append(paper.full_summary)
        
        return ' '.join(text_parts)
    
    def generate_wordcloud(
        self,
        topic_id: str,
        tier: int = 1,
        width: int = 800,
        height: int = 400,
        background_color: str = 'white',
    ) -> Optional[Any]:
        """
        Generate a word cloud for a topic.
        
        Args:
            topic_id: Topic ID
            tier: Topic tier
            width: Image width
            height: Image height
            background_color: Background color
            
        Returns:
            WordCloud object or None
        """
        if not WORDCLOUD_AVAILABLE:
            logger.warning("WordCloud library not available")
            return None
        
        text = self.get_topic_text(topic_id, tier)
        
        if not text:
            logger.warning(f"No text found for topic {topic_id}")
            return None
        
        # Generate word cloud
        wordcloud = WordCloud(
            width=width,
            height=height,
            background_color=background_color,
            max_words=self.max_words,
            min_word_length=self.min_word_length,
            stopwords=self.STOP_WORDS,
            colormap='viridis',
            prefer_horizontal=0.7,
        ).generate(text)
        
        logger.info(f"Generated word cloud for topic {topic_id}")
        return wordcloud
    
    def save_wordcloud(
        self,
        topic_id: str,
        output_path: str,
        tier: int = 1,
        **kwargs
    ) -> Optional[str]:
        """
        Generate and save a word cloud.
        
        Args:
            topic_id: Topic ID
            output_path: Path to save image
            tier: Topic tier
            **kwargs: Additional arguments for generate_wordcloud
            
        Returns:
            Path to saved image or None
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib not available for saving word cloud")
            return None
        
        wordcloud = self.generate_wordcloud(topic_id, tier, **kwargs)
        
        if wordcloud is None:
            return None
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        
        # Get topic label
        hierarchy = self.state.get('topic_hierarchy')
        topic = hierarchy.get_topic_by_id(topic_id) if hierarchy else None
        title = topic.label if topic else topic_id
        ax.set_title(f'Word Cloud: {title}', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved word cloud to {output_path}")
        return output_path


def generate_topic_wordcloud(
    state: GraphState,
    topic_id: str,
    tier: int = 1,
    output_path: Optional[str] = None,
    **kwargs
) -> Optional[Any]:
    """
    Generate a word cloud for a specific topic.
    
    Args:
        state: GraphState with papers
        topic_id: Topic ID
        tier: Topic tier (1, 2, or 3)
        output_path: Path to save image (optional)
        **kwargs: Additional arguments for word cloud generation
        
    Returns:
        WordCloud object or path to saved image
    """
    generator = WordCloudGenerator(state)
    
    if output_path:
        return generator.save_wordcloud(topic_id, output_path, tier, **kwargs)
    else:
        return generator.generate_wordcloud(topic_id, tier, **kwargs)


def generate_all_topic_wordclouds(
    state: GraphState,
    output_dir: str,
    tier: int = 1,
) -> Dict[str, str]:
    """
    Generate word clouds for all topics in a tier.
    
    Args:
        state: GraphState with papers
        output_dir: Directory to save word clouds
        tier: Topic tier (1, 2, or 3)
        
    Returns:
        Dict mapping topic_id to file path
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    hierarchy = state.get('topic_hierarchy')
    if not hierarchy:
        logger.warning("No topic hierarchy in state")
        return {}
    
    generator = WordCloudGenerator(state)
    results = {}
    
    # Get topics for the specified tier
    if tier == 1:
        topics = hierarchy.tier1
    elif tier == 2:
        topics = hierarchy.tier2
    else:
        topics = hierarchy.tier3
    
    for topic in topics:
        filename = f"wordcloud_{topic.id}.png"
        filepath = str(output_path / filename)
        
        result = generator.save_wordcloud(topic.id, filepath, tier)
        if result:
            results[topic.id] = result
    
    logger.info(f"Generated {len(results)} word clouds in {output_dir}")
    return results


# =============================================================================
# Author Collaboration Networks
# =============================================================================

class AuthorNetworkAnalyzer:
    """
    Analyzes and visualizes author collaboration networks.
    """
    
    def __init__(self, state: GraphState):
        """
        Initialize author network analyzer.
        
        Args:
            state: GraphState with papers
        """
        self.state = state
        self.graph = None
        self._build_network()
    
    def _build_network(self) -> None:
        """Build the collaboration network graph."""
        if not NETWORKX_AVAILABLE:
            logger.warning("NetworkX not available for network analysis")
            return
        
        self.graph = nx.Graph()
        papers = self.state.get('papers', {})
        
        # Add edges between co-authors
        for paper in papers.values():
            authors = paper.authors or []
            if len(authors) < 2:
                continue
            
            # Add nodes for each author
            for author in authors:
                if author not in self.graph:
                    self.graph.add_node(author, papers=0)
                self.graph.nodes[author]['papers'] += 1
            
            # Add edges between all co-author pairs
            for i in range(len(authors)):
                for j in range(i + 1, len(authors)):
                    author1, author2 = authors[i], authors[j]
                    
                    if self.graph.has_edge(author1, author2):
                        self.graph[author1][author2]['weight'] += 1
                    else:
                        self.graph.add_edge(author1, author2, weight=1)
        
        logger.info(f"Built collaboration network with {self.graph.number_of_nodes()} authors "
                   f"and {self.graph.number_of_edges()} collaborations")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get network statistics.
        
        Returns:
            Dict with network statistics
        """
        if self.graph is None:
            return {}
        
        stats = {
            'num_authors': self.graph.number_of_nodes(),
            'num_collaborations': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
        }
        
        if self.graph.number_of_nodes() > 0:
            # Get most prolific authors
            author_papers = [(n, d.get('papers', 0)) for n, d in self.graph.nodes(data=True)]
            author_papers.sort(key=lambda x: x[1], reverse=True)
            stats['top_authors'] = author_papers[:10]
            
            # Get most collaborative pairs
            edges = [(u, v, d['weight']) for u, v, d in self.graph.edges(data=True)]
            edges.sort(key=lambda x: x[2], reverse=True)
            stats['top_collaborations'] = edges[:10]
            
            # Degree statistics
            degrees = [d for _, d in self.graph.degree()]
            if degrees:
                stats['avg_collaborators'] = sum(degrees) / len(degrees)
                stats['max_collaborators'] = max(degrees)
        
        return stats
    
    def get_top_authors(self, n: int = 20) -> List[Tuple[str, int]]:
        """
        Get top n authors by paper count.
        
        Args:
            n: Number of authors to return
            
        Returns:
            List of (author_name, paper_count) tuples
        """
        if self.graph is None:
            return []
        
        author_papers = [(node, data.get('papers', 0)) 
                        for node, data in self.graph.nodes(data=True)]
        author_papers.sort(key=lambda x: x[1], reverse=True)
        return author_papers[:n]
    
    def create_interactive_network(
        self,
        min_papers: int = 2,
        min_collaborations: int = 1,
    ) -> Optional[Any]:
        """
        Create an interactive network visualization.
        
        Args:
            min_papers: Minimum papers to include an author
            min_collaborations: Minimum collaborations to include an edge
            
        Returns:
            Plotly figure or None
        """
        if not PLOTLY_AVAILABLE or self.graph is None:
            logger.warning("Plotly or NetworkX not available for network visualization")
            return None
        
        # Filter graph
        filtered_nodes = [n for n, d in self.graph.nodes(data=True) 
                         if d.get('papers', 0) >= min_papers]
        subgraph = self.graph.subgraph(filtered_nodes).copy()
        
        # Remove edges with low weight
        edges_to_remove = [(u, v) for u, v, d in subgraph.edges(data=True) 
                          if d.get('weight', 0) < min_collaborations]
        subgraph.remove_edges_from(edges_to_remove)
        
        if subgraph.number_of_nodes() == 0:
            logger.warning("No nodes in filtered network")
            return None
        
        # Get layout
        pos = nx.spring_layout(subgraph, k=1/np.sqrt(subgraph.number_of_nodes()), seed=42)
        
        # Create edge traces
        edge_x = []
        edge_y = []
        for edge in subgraph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Create node traces
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        
        for node in subgraph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            papers = subgraph.nodes[node].get('papers', 0)
            degree = subgraph.degree(node)
            node_text.append(f"{node}<br>Papers: {papers}<br>Collaborators: {degree}")
            node_size.append(10 + papers * 3)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[n[:15] + '...' if len(n) > 15 else n for n in subgraph.nodes()],
            textposition="top center",
            textfont=dict(size=8),
            hovertext=node_text,
            marker=dict(
                size=node_size,
                color=[subgraph.degree(n) for n in subgraph.nodes()],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='Collaborators'),
                line=dict(width=1, color='white')
            )
        )
        
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='Author Collaboration Network',
                           showlegend=False,
                           hovermode='closest',
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           margin=dict(l=20, r=20, t=50, b=20),
                       ))
        
        logger.info("Created interactive collaboration network")
        return fig
    
    def create_static_network(
        self,
        output_path: Optional[str] = None,
        min_papers: int = 2,
        figsize: Tuple[int, int] = (14, 10),
    ) -> Optional[str]:
        """
        Create a static network visualization.
        
        Args:
            output_path: Path to save the figure
            min_papers: Minimum papers to include an author
            figsize: Figure size
            
        Returns:
            Path to saved figure or None
        """
        if not MATPLOTLIB_AVAILABLE or not NETWORKX_AVAILABLE or self.graph is None:
            logger.warning("Dependencies not available for static network plot")
            return None
        
        # Filter graph
        filtered_nodes = [n for n, d in self.graph.nodes(data=True) 
                         if d.get('papers', 0) >= min_papers]
        subgraph = self.graph.subgraph(filtered_nodes).copy()
        
        if subgraph.number_of_nodes() == 0:
            logger.warning("No nodes in filtered network")
            return None
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Get layout
        pos = nx.spring_layout(subgraph, k=2/np.sqrt(subgraph.number_of_nodes()), seed=42)
        
        # Node sizes based on paper count
        node_sizes = [100 + subgraph.nodes[n].get('papers', 0) * 50 for n in subgraph.nodes()]
        
        # Edge widths based on collaboration count
        edge_widths = [0.5 + subgraph[u][v].get('weight', 1) * 0.5 for u, v in subgraph.edges()]
        
        # Draw network
        nx.draw_networkx_edges(subgraph, pos, ax=ax, alpha=0.3, width=edge_widths)
        nx.draw_networkx_nodes(subgraph, pos, ax=ax, node_size=node_sizes, 
                              node_color='steelblue', alpha=0.7)
        
        # Add labels for top authors
        top_nodes = sorted(subgraph.nodes(), key=lambda n: subgraph.nodes[n].get('papers', 0), reverse=True)[:15]
        labels = {n: n[:20] for n in top_nodes}
        nx.draw_networkx_labels(subgraph, pos, labels, ax=ax, font_size=8)
        
        ax.set_title('Author Collaboration Network', fontsize=14, fontweight='bold')
        ax.axis('off')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            logger.info(f"Saved collaboration network to {output_path}")
            plt.close()
            return output_path
        else:
            plt.close()
            return None


def build_author_collaboration_network(state: GraphState) -> Optional[Any]:
    """
    Build an author collaboration network from papers.
    
    Args:
        state: GraphState with papers
        
    Returns:
        NetworkX graph or None
    """
    analyzer = AuthorNetworkAnalyzer(state)
    return analyzer.graph


def visualize_author_network(
    state: GraphState,
    interactive: bool = True,
    output_path: Optional[str] = None,
    min_papers: int = 2,
) -> Optional[Any]:
    """
    Visualize the author collaboration network.
    
    Args:
        state: GraphState with papers
        interactive: Whether to create interactive plot
        output_path: Path to save static plot
        min_papers: Minimum papers to include an author
        
    Returns:
        Plotly figure (if interactive) or path to saved figure
    """
    analyzer = AuthorNetworkAnalyzer(state)
    
    if interactive:
        return analyzer.create_interactive_network(min_papers=min_papers)
    else:
        return analyzer.create_static_network(output_path=output_path, min_papers=min_papers)


def get_author_statistics(state: GraphState) -> Dict[str, Any]:
    """
    Get author collaboration statistics.
    
    Args:
        state: GraphState with papers
        
    Returns:
        Dict with network statistics
    """
    analyzer = AuthorNetworkAnalyzer(state)
    return analyzer.get_statistics()


# =============================================================================
# Topic Evolution Charts
# =============================================================================

class TopicEvolutionAnalyzer:
    """
    Analyzes and visualizes topic evolution over time.
    """
    
    def __init__(self, state: GraphState):
        """
        Initialize topic evolution analyzer.
        
        Args:
            state: GraphState with papers and topic hierarchy
        """
        self.state = state
        self.hierarchy = state.get('topic_hierarchy')
        logger.info("TopicEvolutionAnalyzer initialized")
    
    def get_topic_trends_by_year(
        self,
        tier: int = 1,
    ) -> Dict[str, Dict[int, int]]:
        """
        Get paper counts per topic per year.
        
        Args:
            tier: Topic tier to analyze (1, 2, or 3)
            
        Returns:
            Dict mapping topic_id to dict of year -> count
        """
        papers = self.state.get('papers', {})
        trends = defaultdict(lambda: defaultdict(int))
        
        for paper in papers.values():
            year = paper.year
            if not year:
                continue
            
            if tier == 1 and paper.tier1_topic:
                topic_id = paper.tier1_topic
            elif tier == 2 and paper.tier2_topic:
                topic_id = paper.tier2_topic
            elif tier == 3 and paper.tier3_topic:
                topic_id = paper.tier3_topic
            else:
                continue
            
            trends[topic_id][year] += 1
        
        return dict(trends)
    
    def create_evolution_chart(
        self,
        tier: int = 1,
        chart_type: Literal['line', 'area', 'bar'] = 'line',
        normalize: bool = False,
    ) -> Optional[Any]:
        """
        Create an interactive evolution chart.
        
        Args:
            tier: Topic tier to visualize
            chart_type: Type of chart ('line', 'area', or 'bar')
            normalize: Whether to normalize counts to percentages
            
        Returns:
            Plotly figure or None
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available for evolution chart")
            return None
        
        trends = self.get_topic_trends_by_year(tier)
        
        if not trends:
            logger.warning("No trend data available")
            return None
        
        # Get all years
        all_years = set()
        for topic_data in trends.values():
            all_years.update(topic_data.keys())
        years = sorted(all_years)
        
        if not years:
            return None
        
        # Build data for plotting
        topic_labels = {}
        if self.hierarchy:
            if tier == 1:
                for t in self.hierarchy.tier1:
                    topic_labels[t.id] = t.label
            elif tier == 2:
                for t in self.hierarchy.tier2:
                    topic_labels[t.id] = t.label
            else:
                for t in self.hierarchy.tier3:
                    topic_labels[t.id] = t.label
        
        # Create figure
        fig = go.Figure()
        
        for topic_id, year_counts in trends.items():
            counts = [year_counts.get(year, 0) for year in years]
            
            if normalize:
                total_per_year = [sum(trends[tid].get(y, 0) for tid in trends) for y in years]
                counts = [c / t * 100 if t > 0 else 0 for c, t in zip(counts, total_per_year)]
            
            label = topic_labels.get(topic_id, topic_id)
            
            if chart_type == 'area':
                fig.add_trace(go.Scatter(
                    x=years, y=counts,
                    mode='lines',
                    name=label,
                    stackgroup='one',
                    hovertemplate=f'{label}<br>Year: %{{x}}<br>{"%" if normalize else "Count"}: %{{y:.1f}}<extra></extra>',
                ))
            elif chart_type == 'bar':
                fig.add_trace(go.Bar(
                    x=years, y=counts,
                    name=label,
                ))
            else:  # line
                fig.add_trace(go.Scatter(
                    x=years, y=counts,
                    mode='lines+markers',
                    name=label,
                    hovertemplate=f'{label}<br>Year: %{{x}}<br>{"%" if normalize else "Count"}: %{{y:.1f}}<extra></extra>',
                ))
        
        fig.update_layout(
            title=f'Topic Evolution Over Time (Tier {tier})',
            xaxis_title='Year',
            yaxis_title='Percentage of Papers' if normalize else 'Number of Papers',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            ),
            margin=dict(b=100),
        )
        
        if chart_type == 'bar':
            fig.update_layout(barmode='stack')
        
        logger.info(f"Created topic evolution chart for tier {tier}")
        return fig
    
    def create_static_evolution_chart(
        self,
        tier: int = 1,
        output_path: Optional[str] = None,
        figsize: Tuple[int, int] = (14, 8),
    ) -> Optional[str]:
        """
        Create a static evolution chart.
        
        Args:
            tier: Topic tier to visualize
            output_path: Path to save the figure
            figsize: Figure size
            
        Returns:
            Path to saved figure or None
        """
        if not MATPLOTLIB_AVAILABLE or not NUMPY_AVAILABLE:
            logger.warning("Matplotlib/NumPy not available for static chart")
            return None
        
        trends = self.get_topic_trends_by_year(tier)
        
        if not trends:
            logger.warning("No trend data available")
            return None
        
        # Get all years
        all_years = set()
        for topic_data in trends.values():
            all_years.update(topic_data.keys())
        years = sorted(all_years)
        
        if not years:
            return None
        
        # Get topic labels
        topic_labels = {}
        if self.hierarchy:
            if tier == 1:
                for t in self.hierarchy.tier1:
                    topic_labels[t.id] = t.label
            elif tier == 2:
                for t in self.hierarchy.tier2:
                    topic_labels[t.id] = t.label
            else:
                for t in self.hierarchy.tier3:
                    topic_labels[t.id] = t.label
        
        fig, ax = plt.subplots(figsize=figsize)
        
        colors = plt.cm.tab20(np.linspace(0, 1, len(trends)))
        
        for (topic_id, year_counts), color in zip(trends.items(), colors):
            counts = [year_counts.get(year, 0) for year in years]
            label = topic_labels.get(topic_id, topic_id)
            ax.plot(years, counts, marker='o', label=label[:30], color=color, linewidth=2)
        
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('Number of Papers', fontsize=12)
        ax.set_title(f'Topic Evolution Over Time (Tier {tier})', fontsize=14, fontweight='bold')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            logger.info(f"Saved evolution chart to {output_path}")
            plt.close()
            return output_path
        else:
            plt.close()
            return None


def create_topic_evolution_chart(
    state: GraphState,
    tier: int = 1,
    chart_type: Literal['line', 'area', 'bar'] = 'line',
    interactive: bool = True,
    output_path: Optional[str] = None,
    normalize: bool = False,
) -> Optional[Any]:
    """
    Create a topic evolution chart.
    
    Args:
        state: GraphState with papers and topic hierarchy
        tier: Topic tier to visualize
        chart_type: Type of chart ('line', 'area', or 'bar')
        interactive: Whether to create interactive plot
        output_path: Path to save static plot
        normalize: Whether to normalize to percentages
        
    Returns:
        Plotly figure (if interactive) or path to saved figure
    """
    analyzer = TopicEvolutionAnalyzer(state)
    
    if interactive:
        return analyzer.create_evolution_chart(tier=tier, chart_type=chart_type, normalize=normalize)
    else:
        return analyzer.create_static_evolution_chart(tier=tier, output_path=output_path)


def get_topic_trends_by_year(
    state: GraphState,
    tier: int = 1,
) -> Dict[str, Dict[int, int]]:
    """
    Get topic trends by year.
    
    Args:
        state: GraphState with papers
        tier: Topic tier to analyze
        
    Returns:
        Dict mapping topic_id to dict of year -> count
    """
    analyzer = TopicEvolutionAnalyzer(state)
    return analyzer.get_topic_trends_by_year(tier)


# =============================================================================
# Utility Functions
# =============================================================================

def save_figure_to_base64(fig: Any) -> Optional[str]:
    """
    Save a matplotlib figure to base64 encoded string.
    
    Args:
        fig: Matplotlib figure
        
    Returns:
        Base64 encoded PNG string or None
    """
    if not MATPLOTLIB_AVAILABLE:
        return None
    
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    buffer.close()
    return img_str


def generate_visualization_report(
    state: GraphState,
    output_dir: str,
    include_interactive: bool = True,
) -> Dict[str, Any]:
    """
    Generate a comprehensive visualization report.
    
    Args:
        state: GraphState with papers and topic hierarchy
        output_dir: Directory to save visualizations
        include_interactive: Whether to include interactive plots
        
    Returns:
        Dict with paths to generated visualizations and statistics
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'visualizations': {},
        'statistics': {},
    }
    
    hierarchy = state.get('topic_hierarchy')
    
    # 1. Topic Map
    if hierarchy:
        try:
            topic_map_path = str(output_path / 'topic_map.png')
            result = create_static_topic_map(hierarchy, topic_map_path)
            if result:
                report['visualizations']['topic_map'] = result
        except Exception as e:
            logger.error(f"Error creating topic map: {e}")
    
    # 2. Word Clouds (for top 5 tier1 topics)
    if hierarchy and hierarchy.tier1:
        wordcloud_paths = {}
        for topic in hierarchy.tier1[:5]:
            try:
                wc_path = str(output_path / f'wordcloud_{topic.id}.png')
                result = generate_topic_wordcloud(state, topic.id, tier=1, output_path=wc_path)
                if result:
                    wordcloud_paths[topic.id] = result
            except Exception as e:
                logger.error(f"Error creating word cloud for {topic.id}: {e}")
        report['visualizations']['wordclouds'] = wordcloud_paths
    
    # 3. Author Network
    try:
        network_path = str(output_path / 'author_network.png')
        result = visualize_author_network(state, interactive=False, output_path=network_path)
        if result:
            report['visualizations']['author_network'] = result
        
        # Add author statistics
        author_stats = get_author_statistics(state)
        report['statistics']['author_network'] = author_stats
    except Exception as e:
        logger.error(f"Error creating author network: {e}")
    
    # 4. Topic Evolution
    if hierarchy:
        try:
            evolution_path = str(output_path / 'topic_evolution.png')
            result = create_topic_evolution_chart(
                state, tier=1, interactive=False, output_path=evolution_path
            )
            if result:
                report['visualizations']['topic_evolution'] = result
        except Exception as e:
            logger.error(f"Error creating evolution chart: {e}")
    
    # 5. Save interactive plots if requested
    if include_interactive and PLOTLY_AVAILABLE:
        interactive_plots = {}
        
        if hierarchy:
            try:
                fig = create_interactive_topic_map(hierarchy, chart_type='treemap')
                if fig:
                    html_path = str(output_path / 'topic_map_interactive.html')
                    fig.write_html(html_path)
                    interactive_plots['topic_map'] = html_path
            except Exception as e:
                logger.error(f"Error creating interactive topic map: {e}")
            
            try:
                fig = create_topic_evolution_chart(state, tier=1, interactive=True)
                if fig:
                    html_path = str(output_path / 'topic_evolution_interactive.html')
                    fig.write_html(html_path)
                    interactive_plots['topic_evolution'] = html_path
            except Exception as e:
                logger.error(f"Error creating interactive evolution chart: {e}")
        
        try:
            fig = visualize_author_network(state, interactive=True)
            if fig:
                html_path = str(output_path / 'author_network_interactive.html')
                fig.write_html(html_path)
                interactive_plots['author_network'] = html_path
        except Exception as e:
            logger.error(f"Error creating interactive author network: {e}")
        
        report['visualizations']['interactive'] = interactive_plots
    
    logger.info(f"Generated visualization report in {output_dir}")
    return report
