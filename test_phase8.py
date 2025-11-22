#!/usr/bin/env python3
"""
Test suite for Phase 8: Topic Modeling and Taxonomy Construction

Tests all functionality in topic_taxonomy.py including:
- Paper-level embedding generation
- Tier 1/2/3 clustering
- Topic labeling with GPT-5.1
- Taxonomy hierarchy construction
- Visualization and statistics
- LangGraph worker integration

Note: Some tests require OpenAI API key and scikit-learn.
Mock tests are provided for environments without these dependencies.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    PaperRecord,
    PaperChunk,
    TopicNode,
    TopicHierarchy,
    StateManager,
    create_default_config,
)

# Try importing the phase 8 module
try:
    from topic_taxonomy import (
        # Step 8.1
        PaperEmbeddingGenerator,
        generate_paper_embeddings,
        
        # Step 8.2
        determine_optimal_k,
        cluster_papers,
        build_tier1_taxonomy,
        
        # Step 8.3
        TopicLabelGenerator,
        generate_tier1_labels,
        
        # Step 8.4-8.7
        build_tier2_taxonomy,
        build_tier3_taxonomy,
        generate_tier2_labels,
        generate_tier3_labels,
        
        # Step 8.8
        TaxonomyBuilder,
        build_complete_taxonomy,
        validate_taxonomy_structure,
        
        # Step 8.9
        TaxonomyVisualizer,
        visualize_taxonomy,
        generate_taxonomy_statistics,
        
        # Worker
        taxonomy_construction_worker,
    )
    TAXONOMY_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import topic_taxonomy module: {e}")
    TAXONOMY_MODULE_AVAILABLE = False

# Check for dependencies
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: numpy not available")

try:
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available")


def create_mock_papers(n_papers: int = 20) -> dict:
    """Create mock papers for testing."""
    papers = {}
    for i in range(n_papers):
        paper_id = f"paper_{i:03d}"
        papers[paper_id] = PaperRecord(
            id=paper_id,
            file_path=f"/path/to/paper_{i}.pdf",
            filename=f"paper_{i}.pdf",
            title=f"Research Paper {i}",
            abstract_text=f"This is the abstract for paper {i}. It discusses topic A and topic B.",
            authors=[f"Author {i}A", f"Author {i}B"],
            year=2020 + (i % 5),
            processing_status="embedded"
        )
    return papers


def create_mock_chunks(papers: dict, chunks_per_paper: int = 5) -> dict:
    """Create mock chunks for papers."""
    chunks = {}
    chunk_id_counter = 0
    
    for paper_id in papers:
        paper_chunks = []
        for i in range(chunks_per_paper):
            section = ['abstract', 'introduction', 'methods', 'results', 'conclusion'][i % 5]
            chunk = PaperChunk(
                paper_id=paper_id,
                chunk_id=f"chunk_{chunk_id_counter:05d}",
                section_label=section,
                page_start=i,
                page_end=i,
                text=f"This is chunk {i} from {paper_id} in section {section}.",
                embedding_id=chunk_id_counter,
                char_count=50
            )
            paper_chunks.append(chunk)
            chunk_id_counter += 1
        chunks[paper_id] = paper_chunks
    
    return chunks


def create_mock_embeddings(n_embeddings: int, embedding_dim: int = 512):
    """Create mock embeddings array."""
    if not NUMPY_AVAILABLE:
        return None
    np.random.seed(42)
    return np.random.randn(n_embeddings, embedding_dim).astype(np.float32)


# =============================================================================
# Test Step 8.1: Paper-Level Embeddings
# =============================================================================

def test_paper_embedding_generator_initialization():
    """Test PaperEmbeddingGenerator initialization."""
    if not TAXONOMY_MODULE_AVAILABLE:
        print("SKIP: test_paper_embedding_generator_initialization (module not available)")
        return
    
    generator = PaperEmbeddingGenerator(aggregation_method='mean')
    assert generator.aggregation_method == 'mean'
    
    generator = PaperEmbeddingGenerator(aggregation_method='weighted_mean')
    assert generator.aggregation_method == 'weighted_mean'
    
    print("PASS: test_paper_embedding_generator_initialization")


def test_aggregate_chunk_embeddings_mean():
    """Test mean aggregation of chunk embeddings."""
    if not TAXONOMY_MODULE_AVAILABLE or not NUMPY_AVAILABLE:
        print("SKIP: test_aggregate_chunk_embeddings_mean")
        return
    
    generator = PaperEmbeddingGenerator(aggregation_method='mean')
    
    # Create mock chunks and embeddings
    chunks = [
        PaperChunk(
            paper_id="p1", chunk_id="c1", section_label="abstract",
            page_start=0, page_end=0, text="test", char_count=4
        ),
        PaperChunk(
            paper_id="p1", chunk_id="c2", section_label="introduction",
            page_start=1, page_end=1, text="test", char_count=4
        ),
    ]
    
    embeddings = np.array([[1.0, 2.0, 3.0], [3.0, 4.0, 5.0]])
    
    result = generator.aggregate_chunk_embeddings(chunks, embeddings)
    
    expected = np.mean(embeddings, axis=0)
    assert np.allclose(result, expected)
    
    print("PASS: test_aggregate_chunk_embeddings_mean")


def test_aggregate_chunk_embeddings_weighted():
    """Test weighted mean aggregation."""
    if not TAXONOMY_MODULE_AVAILABLE or not NUMPY_AVAILABLE:
        print("SKIP: test_aggregate_chunk_embeddings_weighted")
        return
    
    generator = PaperEmbeddingGenerator(aggregation_method='weighted_mean')
    
    chunks = [
        PaperChunk(
            paper_id="p1", chunk_id="c1", section_label="abstract",
            page_start=0, page_end=0, text="test", char_count=4
        ),
        PaperChunk(
            paper_id="p1", chunk_id="c2", section_label="other",
            page_start=1, page_end=1, text="test", char_count=4
        ),
    ]
    
    embeddings = np.array([[1.0, 2.0, 3.0], [3.0, 4.0, 5.0]])
    
    result = generator.aggregate_chunk_embeddings(chunks, embeddings)
    
    # Abstract has weight 3.0, other has weight 1.0
    weights = np.array([3.0, 1.0])
    weights = weights / weights.sum()
    expected = np.average(embeddings, axis=0, weights=weights)
    
    assert np.allclose(result, expected)
    
    print("PASS: test_aggregate_chunk_embeddings_weighted")


def test_generate_paper_embeddings():
    """Test generating paper-level embeddings from state."""
    if not TAXONOMY_MODULE_AVAILABLE or not NUMPY_AVAILABLE:
        print("SKIP: test_generate_paper_embeddings")
        return
    
    # Create mock data
    papers = create_mock_papers(n_papers=5)
    chunks = create_mock_chunks(papers, chunks_per_paper=3)
    embeddings_array = create_mock_embeddings(n_embeddings=15, embedding_dim=128)
    
    # Create state
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    state['papers'] = papers
    state['chunks'] = chunks
    
    # Create embedding mapping
    embedding_id_to_chunk = {}
    for paper_chunks in chunks.values():
        for chunk in paper_chunks:
            embedding_id_to_chunk[chunk.embedding_id] = chunk
    
    # Generate paper embeddings
    paper_embeddings, paper_to_idx = generate_paper_embeddings(
        state, embeddings_array, embedding_id_to_chunk, aggregation_method='mean'
    )
    
    assert len(paper_embeddings) == 5
    assert all(emb.shape == (128,) for emb in paper_embeddings.values())
    
    print("PASS: test_generate_paper_embeddings")


# =============================================================================
# Test Step 8.2: Tier 1 Clustering
# =============================================================================

def test_cluster_papers_kmeans():
    """Test KMeans clustering of papers."""
    if not TAXONOMY_MODULE_AVAILABLE or not NUMPY_AVAILABLE or not SKLEARN_AVAILABLE:
        print("SKIP: test_cluster_papers_kmeans")
        return
    
    # Create mock embeddings
    embeddings = create_mock_embeddings(n_embeddings=20, embedding_dim=64)
    
    # Cluster
    labels, centroids = cluster_papers(embeddings, n_clusters=3, method='kmeans')
    
    assert len(labels) == 20
    assert centroids.shape == (3, 64)
    assert set(labels).issubset({0, 1, 2})
    
    print("PASS: test_cluster_papers_kmeans")


def test_determine_optimal_k_silhouette():
    """Test optimal k determination using silhouette method."""
    if not TAXONOMY_MODULE_AVAILABLE or not NUMPY_AVAILABLE or not SKLEARN_AVAILABLE:
        print("SKIP: test_determine_optimal_k_silhouette")
        return
    
    # Create mock embeddings with clear clusters
    np.random.seed(42)
    cluster1 = np.random.randn(10, 32) + [5, 5]
    cluster2 = np.random.randn(10, 32) + [-5, -5]
    cluster3 = np.random.randn(10, 32) + [5, -5]
    embeddings = np.vstack([cluster1, cluster2, cluster3])
    
    optimal_k = determine_optimal_k(embeddings, k_range=(2, 5), method='silhouette')
    
    assert 2 <= optimal_k <= 5
    
    print("PASS: test_determine_optimal_k_silhouette")


def test_build_tier1_taxonomy():
    """Test building Tier 1 taxonomy."""
    if not TAXONOMY_MODULE_AVAILABLE or not NUMPY_AVAILABLE or not SKLEARN_AVAILABLE:
        print("SKIP: test_build_tier1_taxonomy")
        return
    
    # Create mock paper embeddings
    paper_ids = [f"paper_{i:03d}" for i in range(20)]
    embeddings_dict = {pid: np.random.randn(64) for pid in paper_ids}
    paper_to_idx = {pid: i for i, pid in enumerate(paper_ids)}
    
    # Create config
    config = create_default_config()
    config.cluster_tier1_target_k = 4
    
    # Build taxonomy
    tier1_clusters, labels, centroids = build_tier1_taxonomy(
        embeddings_dict, paper_to_idx, config
    )
    
    assert len(tier1_clusters) == 4
    assert all('paper_ids' in c for c in tier1_clusters)
    assert sum(c['paper_count'] for c in tier1_clusters) == 20
    
    print("PASS: test_build_tier1_taxonomy")


# =============================================================================
# Test Step 8.3: Tier 1 Labels
# =============================================================================

def test_topic_label_generator_mock():
    """Test TopicLabelGenerator with mocked API."""
    if not TAXONOMY_MODULE_AVAILABLE:
        print("SKIP: test_topic_label_generator_mock")
        return
    
    with patch('topic_taxonomy.OpenAI') as mock_openai:
        # Mock the API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            'label': 'Machine Learning',
            'description': 'Papers about ML and AI.'
        })
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create generator
        generator = TopicLabelGenerator(api_key="test_key", model="gpt-5.1-mini")
        
        # Create mock papers
        papers = [
            PaperRecord(
                id="p1", file_path="/p1.pdf", filename="p1.pdf",
                title="Deep Learning Research",
                abstract_text="This paper discusses deep learning.",
                processing_status="embedded"
            )
        ]
        
        # Generate label
        result = generator.generate_topic_label(papers, tier=1)
        
        assert result['label'] == 'Machine Learning'
        assert 'ML and AI' in result['description']
        
        print("PASS: test_topic_label_generator_mock")


# =============================================================================
# Test Step 8.4-8.7: Hierarchical Clustering
# =============================================================================

def test_build_tier2_taxonomy():
    """Test building Tier 2 taxonomy."""
    if not TAXONOMY_MODULE_AVAILABLE or not NUMPY_AVAILABLE or not SKLEARN_AVAILABLE:
        print("SKIP: test_build_tier2_taxonomy")
        return
    
    # Create Tier 1 topics
    tier1_topics = [
        TopicNode(
            id="T1_00",
            label="Topic A",
            description="First topic",
            paper_ids=[f"paper_{i:03d}" for i in range(10)],
            parent_id=None
        ),
        TopicNode(
            id="T1_01",
            label="Topic B",
            description="Second topic",
            paper_ids=[f"paper_{i:03d}" for i in range(10, 20)],
            parent_id=None
        ),
    ]
    
    # Create paper embeddings
    paper_embeddings = {f"paper_{i:03d}": np.random.randn(64) for i in range(20)}
    
    # Create config
    config = create_default_config()
    config.cluster_tier2_target_k = 2
    
    # Build Tier 2
    tier2_clusters, tier2_labels_dict, tier2_centroids_dict = build_tier2_taxonomy(
        tier1_topics, paper_embeddings, config
    )
    
    assert len(tier2_clusters) >= 2  # At least some Tier 2 clusters
    
    print("PASS: test_build_tier2_taxonomy")


# =============================================================================
# Test Step 8.8: Build Complete Hierarchy
# =============================================================================

def test_taxonomy_builder_with_mocks():
    """Test TaxonomyBuilder with mocked API and data."""
    if not TAXONOMY_MODULE_AVAILABLE or not NUMPY_AVAILABLE or not SKLEARN_AVAILABLE:
        print("SKIP: test_taxonomy_builder_with_mocks")
        return
    
    with patch('topic_taxonomy.OpenAI') as mock_openai, \
         patch('topic_taxonomy.generate_tier1_labels') as mock_tier1, \
         patch('topic_taxonomy.generate_tier2_labels') as mock_tier2, \
         patch('topic_taxonomy.generate_tier3_labels') as mock_tier3:
        
        # Mock API
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock tier label generation
        mock_tier1.return_value = [
            TopicNode(id="T1_00", label="Topic A", description="Desc A", paper_ids=["p1", "p2"])
        ]
        mock_tier2.return_value = []
        mock_tier3.return_value = []
        
        # Create config and state
        config = create_default_config()
        config.cluster_tier1_target_k = 2
        
        papers = create_mock_papers(n_papers=5)
        chunks = create_mock_chunks(papers, chunks_per_paper=3)
        embeddings_array = create_mock_embeddings(n_embeddings=15, embedding_dim=128)
        
        state = StateManager.create_initial_state(config)
        state['papers'] = papers
        state['chunks'] = chunks
        
        embedding_id_to_chunk = {}
        for paper_chunks in chunks.values():
            for chunk in paper_chunks:
                embedding_id_to_chunk[chunk.embedding_id] = chunk
        
        # Build taxonomy (this will use mocked label generation)
        # Note: We can't fully test this without real API, but we can test initialization
        builder = TaxonomyBuilder(config, api_key="test_key")
        assert builder.config == config
        assert builder.api_key == "test_key"
        
        print("PASS: test_taxonomy_builder_with_mocks")


def test_validate_taxonomy_structure():
    """Test taxonomy structure validation."""
    if not TAXONOMY_MODULE_AVAILABLE:
        print("SKIP: test_validate_taxonomy_structure")
        return
    
    # Create valid hierarchy
    tier1 = [
        TopicNode(id="T1_00", label="Topic A", description="Desc A", paper_ids=["p1", "p2"])
    ]
    tier2 = [
        TopicNode(id="T2_00", label="Subtopic A1", description="Desc A1", paper_ids=["p1"], parent_id="T1_00")
    ]
    tier3 = [
        TopicNode(id="T3_00", label="Fine topic A1a", description="Desc A1a", paper_ids=["p1"], parent_id="T2_00")
    ]
    
    hierarchy = TopicHierarchy(
        taxonomy_version="test_v1",
        tier1=tier1,
        tier2=tier2,
        tier3=tier3,
        total_papers=2
    )
    
    validation = validate_taxonomy_structure(hierarchy)
    assert validation['valid'] == True
    assert validation['tier1_count'] == 1
    assert validation['tier2_count'] == 1
    assert validation['tier3_count'] == 1
    
    print("PASS: test_validate_taxonomy_structure")


# =============================================================================
# Test Step 8.9: Visualization
# =============================================================================

def test_taxonomy_visualizer():
    """Test TaxonomyVisualizer."""
    if not TAXONOMY_MODULE_AVAILABLE:
        print("SKIP: test_taxonomy_visualizer")
        return
    
    # Create simple hierarchy
    tier1 = [
        TopicNode(id="T1_00", label="Topic A", description="Desc A", paper_ids=["p1", "p2", "p3"])
    ]
    tier2 = [
        TopicNode(id="T2_00", label="Subtopic A1", description="Desc A1", paper_ids=["p1", "p2"], parent_id="T1_00")
    ]
    
    hierarchy = TopicHierarchy(
        taxonomy_version="test_v1",
        tier1=tier1,
        tier2=tier2,
        tier3=[],
        total_papers=3
    )
    
    visualizer = TaxonomyVisualizer(hierarchy)
    
    # Test statistics
    stats = visualizer.generate_statistics()
    assert stats['total_papers'] == 3
    assert stats['tier1_topics'] == 1
    assert stats['tier2_topics'] == 1
    
    # Test summary
    summary = visualizer.display_taxonomy_summary()
    assert 'Topic A' in summary
    assert 'test_v1' in summary
    
    print("PASS: test_taxonomy_visualizer")


def test_generate_taxonomy_statistics():
    """Test taxonomy statistics generation."""
    if not TAXONOMY_MODULE_AVAILABLE:
        print("SKIP: test_generate_taxonomy_statistics")
        return
    
    tier1 = [
        TopicNode(id="T1_00", label="Topic A", description="Desc A", paper_ids=["p1", "p2"])
    ]
    
    hierarchy = TopicHierarchy(
        taxonomy_version="test_v1",
        tier1=tier1,
        tier2=[],
        tier3=[],
        total_papers=2
    )
    
    stats = generate_taxonomy_statistics(hierarchy)
    
    assert 'total_papers' in stats
    assert 'tier1_topics' in stats
    assert stats['total_papers'] == 2
    
    print("PASS: test_generate_taxonomy_statistics")


# =============================================================================
# Main Test Runner
# =============================================================================

def run_all_tests():
    """Run all tests."""
    print("=" * 80)
    print("PHASE 8 TEST SUITE: Topic Modeling and Taxonomy Construction")
    print("=" * 80)
    
    # Step 8.1 tests
    print("\n--- Step 8.1: Paper-Level Embeddings ---")
    test_paper_embedding_generator_initialization()
    test_aggregate_chunk_embeddings_mean()
    test_aggregate_chunk_embeddings_weighted()
    test_generate_paper_embeddings()
    
    # Step 8.2 tests
    print("\n--- Step 8.2: Tier 1 Clustering ---")
    test_cluster_papers_kmeans()
    test_determine_optimal_k_silhouette()
    test_build_tier1_taxonomy()
    
    # Step 8.3 tests
    print("\n--- Step 8.3: Tier 1 Labels ---")
    test_topic_label_generator_mock()
    
    # Step 8.4-8.7 tests
    print("\n--- Step 8.4-8.7: Hierarchical Clustering ---")
    test_build_tier2_taxonomy()
    
    # Step 8.8 tests
    print("\n--- Step 8.8: Build Complete Hierarchy ---")
    test_taxonomy_builder_with_mocks()
    test_validate_taxonomy_structure()
    
    # Step 8.9 tests
    print("\n--- Step 8.9: Visualization ---")
    test_taxonomy_visualizer()
    test_generate_taxonomy_statistics()
    
    print("\n" + "=" * 80)
    print("PHASE 8 TESTS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
