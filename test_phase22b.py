#!/usr/bin/env python3
"""
Test suite for Phase 22b: Advanced Visualizations

This module tests the advanced visualization functionality including:
- Interactive topic maps
- Paper embeddings visualization (t-SNE/UMAP/PCA)
- Word clouds per topic
- Author collaboration networks
- Topic evolution charts

Version: 1.0
Date: 2025-11-25
"""

import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import core models
from rag_models import (
    RunConfig,
    PaperRecord,
    PaperChunk,
    TopicNode,
    TopicHierarchy,
    GraphState,
    StateManager,
    IDGenerator,
    create_default_config,
)

# Check for optional dependencies
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: numpy not available")

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available")

try:
    from sklearn.manifold import TSNE
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: sklearn not available")

try:
    import plotly
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Warning: plotly not available")

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    print("Warning: networkx not available")


# =============================================================================
# Test Utilities
# =============================================================================

def create_sample_paper_record(paper_id: str = None, **overrides) -> PaperRecord:
    """Create a sample PaperRecord for testing."""
    if paper_id is None:
        paper_id = IDGenerator.generate_paper_id(f"/test/paper_{datetime.now().timestamp()}.pdf")
    
    defaults = {
        "id": paper_id,
        "file_path": f"/test/{paper_id}.pdf",
        "filename": f"{paper_id}.pdf",
        "title": "Sample Research Paper on Machine Learning",
        "authors": ["John Doe", "Jane Smith"],
        "abstract_text": "This paper presents novel approaches to machine learning.",
        "year": 2023,
        "processing_status": "classified",
        "tier1_topic": "T1_01",
        "tier1_topic_name": "Machine Learning",
        "tier2_topic": "T2_01",
        "tier2_topic_name": "Deep Learning",
    }
    defaults.update(overrides)
    return PaperRecord(**defaults)


def create_sample_hierarchy() -> TopicHierarchy:
    """Create a sample topic hierarchy for testing."""
    tier1 = [
        TopicNode(
            id="T1_01",
            label="Machine Learning",
            description="Research on ML algorithms and applications",
            paper_ids=["p1", "p2", "p3", "p4"],
            paper_count=4
        ),
        TopicNode(
            id="T1_02",
            label="Natural Language Processing",
            description="Research on NLP and text analysis",
            paper_ids=["p5", "p6", "p7"],
            paper_count=3
        ),
        TopicNode(
            id="T1_03",
            label="Computer Vision",
            description="Research on image and video processing",
            paper_ids=["p8", "p9"],
            paper_count=2
        ),
    ]
    
    tier2 = [
        TopicNode(
            id="T2_01",
            label="Deep Learning",
            description="Neural network architectures",
            paper_ids=["p1", "p2"],
            parent_id="T1_01",
            paper_count=2
        ),
        TopicNode(
            id="T2_02",
            label="Reinforcement Learning",
            description="RL algorithms",
            paper_ids=["p3", "p4"],
            parent_id="T1_01",
            paper_count=2
        ),
        TopicNode(
            id="T2_03",
            label="Transformers",
            description="Transformer architectures",
            paper_ids=["p5", "p6", "p7"],
            parent_id="T1_02",
            paper_count=3
        ),
    ]
    
    tier3 = [
        TopicNode(
            id="T3_01",
            label="CNNs",
            description="Convolutional networks",
            paper_ids=["p1"],
            parent_id="T2_01",
            paper_count=1
        ),
    ]
    
    return TopicHierarchy(
        taxonomy_version="v1.0_test",
        total_papers=9,
        tier1=tier1,
        tier2=tier2,
        tier3=tier3,
        clustering_method="kmeans",
        labeling_model="gpt-5-mini"
    )


def create_sample_state(num_papers: int = 10) -> GraphState:
    """Create a sample GraphState with papers for testing."""
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    # Add sample papers with diverse authors and years
    authors_pool = [
        ["John Doe", "Jane Smith"],
        ["Alice Johnson", "Bob Wilson"],
        ["John Doe", "Alice Johnson"],
        ["Jane Smith", "Charlie Brown"],
        ["Bob Wilson", "Charlie Brown"],
        ["David Lee", "John Doe"],
        ["Emma Davis", "Alice Johnson"],
        ["Frank Miller", "Bob Wilson"],
        ["Grace Chen", "Jane Smith"],
        ["Henry Taylor", "David Lee"],
    ]
    
    years = [2019, 2020, 2020, 2021, 2021, 2022, 2022, 2023, 2023, 2023]
    
    topics = [
        ("T1_01", "Machine Learning"),
        ("T1_02", "Natural Language Processing"),
        ("T1_01", "Machine Learning"),
        ("T1_02", "Natural Language Processing"),
        ("T1_03", "Computer Vision"),
        ("T1_01", "Machine Learning"),
        ("T1_02", "Natural Language Processing"),
        ("T1_03", "Computer Vision"),
        ("T1_01", "Machine Learning"),
        ("T1_01", "Machine Learning"),
    ]
    
    for i in range(num_papers):
        paper_id = f"paper_{i:03d}"
        topic_id, topic_name = topics[i % len(topics)]
        paper = create_sample_paper_record(
            paper_id,
            title=f"Research Paper {i} on Advanced Topics",
            authors=authors_pool[i % len(authors_pool)],
            year=years[i % len(years)],
            abstract_text=f"This paper {i} discusses novel approaches to {topic_name.lower()}.",
            full_summary=f"Summary of paper {i}: Important findings in {topic_name.lower()}.",
            tier1_topic=topic_id,
            tier1_topic_name=topic_name,
        )
        state = StateManager.add_paper(state, paper)
    
    # Add topic hierarchy
    state['topic_hierarchy'] = create_sample_hierarchy()
    
    return state


# =============================================================================
# Test Classes
# =============================================================================

class TestTopicMapVisualization:
    """Tests for topic map visualization."""
    
    @staticmethod
    def test_topic_map_generator_initialization():
        """Test TopicMapGenerator initialization."""
        print("\n" + "=" * 70)
        print("Test: TopicMapGenerator Initialization")
        print("=" * 70)
        
        from advanced_visualizations import TopicMapGenerator
        
        hierarchy = create_sample_hierarchy()
        generator = TopicMapGenerator(hierarchy)
        
        assert generator.hierarchy is not None
        assert len(generator.hierarchy.tier1) == 3
        print("  ✓ TopicMapGenerator initialized successfully")
        
        print("\n✓ TopicMapGenerator initialization test passed")
        return True
    
    @staticmethod
    def test_static_topic_map():
        """Test static topic map generation."""
        print("\n" + "=" * 70)
        print("Test: Static Topic Map Generation")
        print("=" * 70)
        
        if not MATPLOTLIB_AVAILABLE or not NUMPY_AVAILABLE:
            print("  Skipping: matplotlib or numpy not available")
            return None
        
        from advanced_visualizations import create_static_topic_map
        
        hierarchy = create_sample_hierarchy()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = str(Path(tmpdir) / "topic_map.png")
            result = create_static_topic_map(hierarchy, output_path)
            
            assert result is not None
            assert Path(result).exists()
            print(f"  ✓ Static topic map saved to {result}")
        
        print("\n✓ Static topic map test passed")
        return True
    
    @staticmethod
    def test_interactive_topic_map():
        """Test interactive topic map generation."""
        print("\n" + "=" * 70)
        print("Test: Interactive Topic Map Generation")
        print("=" * 70)
        
        if not PLOTLY_AVAILABLE:
            print("  Skipping: plotly not available")
            return None
        
        from advanced_visualizations import create_interactive_topic_map
        
        hierarchy = create_sample_hierarchy()
        
        # Test treemap
        fig = create_interactive_topic_map(hierarchy, chart_type='treemap')
        assert fig is not None
        print("  ✓ Interactive treemap created")
        
        # Test sunburst
        fig = create_interactive_topic_map(hierarchy, chart_type='sunburst')
        assert fig is not None
        print("  ✓ Interactive sunburst created")
        
        print("\n✓ Interactive topic map test passed")
        return True


class TestEmbeddingVisualization:
    """Tests for embedding visualization."""
    
    @staticmethod
    def test_embedding_visualizer_initialization():
        """Test EmbeddingVisualizer initialization."""
        print("\n" + "=" * 70)
        print("Test: EmbeddingVisualizer Initialization")
        print("=" * 70)
        
        if not NUMPY_AVAILABLE:
            print("  Skipping: numpy not available")
            return None
        
        from advanced_visualizations import EmbeddingVisualizer
        
        # Create sample embeddings
        embeddings = np.random.randn(10, 128).astype(np.float32)
        metadata = [{"title": f"Paper {i}", "tier1_topic_name": "ML"} for i in range(10)]
        
        visualizer = EmbeddingVisualizer(embeddings, metadata)
        
        assert visualizer.embeddings.shape == (10, 128)
        assert len(visualizer.paper_metadata) == 10
        print("  ✓ EmbeddingVisualizer initialized successfully")
        
        print("\n✓ EmbeddingVisualizer initialization test passed")
        return True
    
    @staticmethod
    def test_dimensionality_reduction():
        """Test dimensionality reduction methods."""
        print("\n" + "=" * 70)
        print("Test: Dimensionality Reduction")
        print("=" * 70)
        
        if not NUMPY_AVAILABLE or not SKLEARN_AVAILABLE:
            print("  Skipping: numpy or sklearn not available")
            return None
        
        from advanced_visualizations import (
            reduce_embeddings_tsne,
            reduce_embeddings_pca,
        )
        
        # Create sample embeddings
        embeddings = np.random.randn(50, 128).astype(np.float32)
        
        # Test PCA
        reduced_pca = reduce_embeddings_pca(embeddings, n_components=2)
        assert reduced_pca.shape == (50, 2)
        print("  ✓ PCA reduction working")
        
        # Test t-SNE
        reduced_tsne = reduce_embeddings_tsne(embeddings, n_components=2, perplexity=10, n_iter=250)
        assert reduced_tsne.shape == (50, 2)
        print("  ✓ t-SNE reduction working")
        
        print("\n✓ Dimensionality reduction test passed")
        return True
    
    @staticmethod
    def test_static_embedding_plot():
        """Test static embedding plot generation."""
        print("\n" + "=" * 70)
        print("Test: Static Embedding Plot")
        print("=" * 70)
        
        if not MATPLOTLIB_AVAILABLE or not NUMPY_AVAILABLE or not SKLEARN_AVAILABLE:
            print("  Skipping: required dependencies not available")
            return None
        
        from advanced_visualizations import visualize_paper_embeddings
        
        # Create sample data
        embeddings = np.random.randn(30, 64).astype(np.float32)
        metadata = [
            {"title": f"Paper {i}", "tier1_topic_name": f"Topic {i % 3}", "year": 2020 + i % 4}
            for i in range(30)
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = str(Path(tmpdir) / "embeddings.png")
            result = visualize_paper_embeddings(
                embeddings, metadata,
                method='pca',
                color_by='topic',
                interactive=False,
                output_path=output_path
            )
            
            assert result is not None
            assert Path(result).exists()
            print(f"  ✓ Static embedding plot saved to {result}")
        
        print("\n✓ Static embedding plot test passed")
        return True


class TestWordCloudGeneration:
    """Tests for word cloud generation."""
    
    @staticmethod
    def test_wordcloud_generator_initialization():
        """Test WordCloudGenerator initialization."""
        print("\n" + "=" * 70)
        print("Test: WordCloudGenerator Initialization")
        print("=" * 70)
        
        from advanced_visualizations import WordCloudGenerator
        
        state = create_sample_state(10)
        generator = WordCloudGenerator(state)
        
        assert generator.state is not None
        print("  ✓ WordCloudGenerator initialized successfully")
        
        print("\n✓ WordCloudGenerator initialization test passed")
        return True
    
    @staticmethod
    def test_get_topic_text():
        """Test topic text extraction."""
        print("\n" + "=" * 70)
        print("Test: Topic Text Extraction")
        print("=" * 70)
        
        from advanced_visualizations import WordCloudGenerator
        
        state = create_sample_state(10)
        generator = WordCloudGenerator(state)
        
        text = generator.get_topic_text("T1_01", tier=1)
        
        assert len(text) > 0
        assert "machine learning" in text.lower() or "advanced topics" in text.lower()
        print(f"  ✓ Extracted {len(text)} characters of text for topic T1_01")
        
        print("\n✓ Topic text extraction test passed")
        return True
    
    @staticmethod
    def test_wordcloud_generation():
        """Test word cloud generation."""
        print("\n" + "=" * 70)
        print("Test: Word Cloud Generation")
        print("=" * 70)
        
        try:
            from wordcloud import WordCloud
            WORDCLOUD_AVAILABLE = True
        except ImportError:
            WORDCLOUD_AVAILABLE = False
        
        if not WORDCLOUD_AVAILABLE or not MATPLOTLIB_AVAILABLE:
            print("  Skipping: wordcloud or matplotlib not available")
            return None
        
        from advanced_visualizations import generate_topic_wordcloud
        
        state = create_sample_state(10)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = str(Path(tmpdir) / "wordcloud.png")
            result = generate_topic_wordcloud(
                state, "T1_01", tier=1, output_path=output_path
            )
            
            if result:
                assert Path(result).exists()
                print(f"  ✓ Word cloud saved to {result}")
            else:
                print("  ✓ Word cloud generation completed (no output)")
        
        print("\n✓ Word cloud generation test passed")
        return True


class TestAuthorNetwork:
    """Tests for author collaboration network."""
    
    @staticmethod
    def test_author_network_builder():
        """Test author network building."""
        print("\n" + "=" * 70)
        print("Test: Author Network Building")
        print("=" * 70)
        
        if not NETWORKX_AVAILABLE:
            print("  Skipping: networkx not available")
            return None
        
        from advanced_visualizations import AuthorNetworkAnalyzer
        
        state = create_sample_state(10)
        analyzer = AuthorNetworkAnalyzer(state)
        
        assert analyzer.graph is not None
        assert analyzer.graph.number_of_nodes() > 0
        print(f"  ✓ Network built with {analyzer.graph.number_of_nodes()} authors")
        print(f"  ✓ Network has {analyzer.graph.number_of_edges()} collaborations")
        
        print("\n✓ Author network building test passed")
        return True
    
    @staticmethod
    def test_author_statistics():
        """Test author statistics calculation."""
        print("\n" + "=" * 70)
        print("Test: Author Statistics")
        print("=" * 70)
        
        if not NETWORKX_AVAILABLE:
            print("  Skipping: networkx not available")
            return None
        
        from advanced_visualizations import get_author_statistics
        
        state = create_sample_state(10)
        stats = get_author_statistics(state)
        
        assert 'num_authors' in stats
        assert 'num_collaborations' in stats
        assert stats['num_authors'] > 0
        print(f"  ✓ Statistics: {stats['num_authors']} authors, {stats['num_collaborations']} collaborations")
        
        if 'top_authors' in stats:
            print(f"  ✓ Top authors: {stats['top_authors'][:3]}")
        
        print("\n✓ Author statistics test passed")
        return True
    
    @staticmethod
    def test_static_network_visualization():
        """Test static network visualization."""
        print("\n" + "=" * 70)
        print("Test: Static Network Visualization")
        print("=" * 70)
        
        if not NETWORKX_AVAILABLE or not MATPLOTLIB_AVAILABLE or not NUMPY_AVAILABLE:
            print("  Skipping: required dependencies not available")
            return None
        
        from advanced_visualizations import visualize_author_network
        
        state = create_sample_state(10)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = str(Path(tmpdir) / "network.png")
            result = visualize_author_network(
                state, interactive=False, output_path=output_path, min_papers=1
            )
            
            if result:
                assert Path(result).exists()
                print(f"  ✓ Network visualization saved to {result}")
            else:
                print("  ✓ Network visualization completed (may have insufficient data)")
        
        print("\n✓ Static network visualization test passed")
        return True


class TestTopicEvolution:
    """Tests for topic evolution analysis."""
    
    @staticmethod
    def test_topic_trends():
        """Test topic trends calculation."""
        print("\n" + "=" * 70)
        print("Test: Topic Trends Calculation")
        print("=" * 70)
        
        from advanced_visualizations import get_topic_trends_by_year
        
        state = create_sample_state(10)
        trends = get_topic_trends_by_year(state, tier=1)
        
        assert len(trends) > 0
        
        for topic_id, year_counts in trends.items():
            print(f"  Topic {topic_id}: {dict(year_counts)}")
        
        print(f"  ✓ Found trends for {len(trends)} topics")
        
        print("\n✓ Topic trends calculation test passed")
        return True
    
    @staticmethod
    def test_evolution_chart():
        """Test evolution chart generation."""
        print("\n" + "=" * 70)
        print("Test: Evolution Chart Generation")
        print("=" * 70)
        
        if not MATPLOTLIB_AVAILABLE or not NUMPY_AVAILABLE:
            print("  Skipping: matplotlib or numpy not available")
            return None
        
        from advanced_visualizations import create_topic_evolution_chart
        
        state = create_sample_state(10)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = str(Path(tmpdir) / "evolution.png")
            result = create_topic_evolution_chart(
                state, tier=1, interactive=False, output_path=output_path
            )
            
            if result:
                assert Path(result).exists()
                print(f"  ✓ Evolution chart saved to {result}")
            else:
                print("  ✓ Evolution chart completed (may have insufficient data)")
        
        print("\n✓ Evolution chart generation test passed")
        return True
    
    @staticmethod
    def test_interactive_evolution_chart():
        """Test interactive evolution chart."""
        print("\n" + "=" * 70)
        print("Test: Interactive Evolution Chart")
        print("=" * 70)
        
        if not PLOTLY_AVAILABLE:
            print("  Skipping: plotly not available")
            return None
        
        from advanced_visualizations import create_topic_evolution_chart
        
        state = create_sample_state(10)
        
        fig = create_topic_evolution_chart(state, tier=1, chart_type='line', interactive=True)
        
        if fig:
            print("  ✓ Interactive line chart created")
        
        fig = create_topic_evolution_chart(state, tier=1, chart_type='area', interactive=True)
        if fig:
            print("  ✓ Interactive area chart created")
        
        print("\n✓ Interactive evolution chart test passed")
        return True


class TestVisualizationReport:
    """Tests for comprehensive visualization report."""
    
    @staticmethod
    def test_report_generation():
        """Test visualization report generation."""
        print("\n" + "=" * 70)
        print("Test: Visualization Report Generation")
        print("=" * 70)
        
        if not MATPLOTLIB_AVAILABLE or not NUMPY_AVAILABLE:
            print("  Skipping: matplotlib or numpy not available")
            return None
        
        from advanced_visualizations import generate_visualization_report
        
        state = create_sample_state(10)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report = generate_visualization_report(
                state, tmpdir, include_interactive=False
            )
            
            assert 'generated_at' in report
            assert 'visualizations' in report
            assert 'statistics' in report
            
            print(f"  ✓ Report generated at {report['generated_at']}")
            print(f"  ✓ Visualizations: {list(report['visualizations'].keys())}")
            
            # Check that some files were created
            files_created = sum(
                1 for v in report['visualizations'].values()
                if isinstance(v, str) and Path(v).exists()
            )
            print(f"  ✓ Created {files_created} visualization files")
        
        print("\n✓ Visualization report generation test passed")
        return True


# =============================================================================
# Main Test Runner
# =============================================================================

def run_all_tests():
    """Run all Phase 22b tests."""
    print("\n" + "=" * 80)
    print("PHASE 22b: ADVANCED VISUALIZATIONS - TEST SUITE")
    print("=" * 80)
    
    results = {
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'details': []
    }
    
    test_sections = [
        ("Topic Map Visualization", [
            ("TopicMapGenerator Init", TestTopicMapVisualization.test_topic_map_generator_initialization),
            ("Static Topic Map", TestTopicMapVisualization.test_static_topic_map),
            ("Interactive Topic Map", TestTopicMapVisualization.test_interactive_topic_map),
        ]),
        
        ("Embedding Visualization", [
            ("EmbeddingVisualizer Init", TestEmbeddingVisualization.test_embedding_visualizer_initialization),
            ("Dimensionality Reduction", TestEmbeddingVisualization.test_dimensionality_reduction),
            ("Static Embedding Plot", TestEmbeddingVisualization.test_static_embedding_plot),
        ]),
        
        ("Word Cloud Generation", [
            ("WordCloudGenerator Init", TestWordCloudGeneration.test_wordcloud_generator_initialization),
            ("Topic Text Extraction", TestWordCloudGeneration.test_get_topic_text),
            ("Word Cloud Generation", TestWordCloudGeneration.test_wordcloud_generation),
        ]),
        
        ("Author Network", [
            ("Network Building", TestAuthorNetwork.test_author_network_builder),
            ("Author Statistics", TestAuthorNetwork.test_author_statistics),
            ("Static Network Viz", TestAuthorNetwork.test_static_network_visualization),
        ]),
        
        ("Topic Evolution", [
            ("Topic Trends", TestTopicEvolution.test_topic_trends),
            ("Evolution Chart", TestTopicEvolution.test_evolution_chart),
            ("Interactive Evolution", TestTopicEvolution.test_interactive_evolution_chart),
        ]),
        
        ("Visualization Report", [
            ("Report Generation", TestVisualizationReport.test_report_generation),
        ]),
    ]
    
    for section_name, tests in test_sections:
        print(f"\n{'=' * 80}")
        print(f"Section: {section_name}")
        print("=" * 80)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                if result is None:
                    results['skipped'] += 1
                    results['details'].append((test_name, "SKIPPED"))
                else:
                    results['passed'] += 1
                    results['details'].append((test_name, "PASSED"))
            except AssertionError as e:
                results['failed'] += 1
                results['details'].append((test_name, f"FAILED: {e}"))
                print(f"\n❌ {test_name} FAILED: {e}")
            except Exception as e:
                results['failed'] += 1
                results['details'].append((test_name, f"ERROR: {e}"))
                print(f"\n❌ {test_name} ERROR: {e}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total = results['passed'] + results['failed'] + results['skipped']
    print(f"Total Tests: {total}")
    print(f"Passed:      {results['passed']}")
    print(f"Failed:      {results['failed']}")
    print(f"Skipped:     {results['skipped']}")
    print("=" * 80)
    
    if results['failed'] > 0:
        print("\n⚠️  FAILED TESTS:")
        for name, status in results['details']:
            if status.startswith("FAILED") or status.startswith("ERROR"):
                print(f"  - {name}: {status}")
        print()
    
    if results['passed'] == total:
        print("\n✅ ALL TESTS PASSED!")
    elif results['failed'] == 0:
        print(f"\n✅ {results['passed']} tests passed, {results['skipped']} skipped (missing dependencies)")
    else:
        print(f"\n⚠️  {results['failed']} tests failed. Please review the output above.")
    
    return results['failed'] == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
