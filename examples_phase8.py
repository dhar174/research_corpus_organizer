#!/usr/bin/env python3
"""
Phase 8 Usage Examples: Topic Modeling and Taxonomy Construction

This file demonstrates how to use the topic_taxonomy module for various use cases.

Examples include:
- Generating paper-level embeddings
- Building Tier 1 taxonomy (broad topics)
- Building Tier 2 and Tier 3 taxonomies (hierarchical)
- Generating topic labels with GPT-5.1
- Validating taxonomy structure
- Visualizing taxonomy
- Complete taxonomy construction pipeline
- Saving and loading taxonomy
- Manual taxonomy editing

All examples use mock data for demonstration purposes.
"""

import sys
from pathlib import Path
import tempfile
from datetime import datetime
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
    print(f"Warning: topic_taxonomy module not available: {e}")
    TAXONOMY_MODULE_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


# =============================================================================
# Helper Functions
# =============================================================================

def create_sample_papers(n_papers=30):
    """Create sample papers for examples."""
    papers = {}
    
    topics = [
        ("Machine Learning", "deep learning, neural networks, optimization"),
        ("Natural Language Processing", "text analysis, language models, transformers"),
        ("Computer Vision", "image recognition, object detection, segmentation"),
        ("Robotics", "autonomous systems, control, navigation"),
        ("Reinforcement Learning", "agents, rewards, policy learning"),
    ]
    
    for i in range(n_papers):
        topic_idx = i % len(topics)
        topic_name, keywords = topics[topic_idx]
        
        paper_id = f"paper_{i:03d}"
        papers[paper_id] = PaperRecord(
            id=paper_id,
            file_path=f"/papers/paper_{i}.pdf",
            filename=f"paper_{i}.pdf",
            title=f"{topic_name} Research Paper {i}",
            abstract_text=f"This paper explores {topic_name.lower()} focusing on {keywords}. "
                         f"We present novel approaches and experimental results.",
            authors=[f"Author {i}A", f"Author {i}B"],
            year=2020 + (i % 5),
            processing_status="embedded"
        )
    
    return papers


def create_sample_chunks(papers, chunks_per_paper=5):
    """Create sample chunks for papers."""
    chunks = {}
    chunk_id_counter = 0
    
    for paper_id, paper in papers.items():
        paper_chunks = []
        sections = ['abstract', 'introduction', 'methods', 'results', 'conclusion']
        
        for i in range(chunks_per_paper):
            section = sections[i % len(sections)]
            chunk = PaperChunk(
                paper_id=paper_id,
                chunk_id=f"chunk_{chunk_id_counter:05d}",
                section_label=section,
                page_start=i,
                page_end=i,
                text=f"Content from {paper.title} - {section} section.",
                embedding_id=chunk_id_counter,
                embedding_model="text-embedding-3-large",
                char_count=50
            )
            paper_chunks.append(chunk)
            chunk_id_counter += 1
        
        chunks[paper_id] = paper_chunks
    
    return chunks


def create_sample_embeddings(n_embeddings, embedding_dim=512):
    """Create sample embeddings with topic structure."""
    if not NUMPY_AVAILABLE:
        return None
    
    np.random.seed(42)
    
    # Create embeddings with 5 distinct clusters
    n_per_cluster = n_embeddings // 5
    embeddings_list = []
    
    cluster_centers = [
        np.array([5.0, 5.0]),
        np.array([-5.0, 5.0]),
        np.array([5.0, -5.0]),
        np.array([-5.0, -5.0]),
        np.array([0.0, 0.0]),
    ]
    
    for i in range(n_embeddings):
        cluster_idx = i % 5
        center = cluster_centers[cluster_idx]
        
        # Create embedding around cluster center
        embedding = np.random.randn(embedding_dim) * 0.5
        embedding[:2] += center  # Use first 2 dims for structure
        embeddings_list.append(embedding)
    
    return np.array(embeddings_list, dtype=np.float32)


# =============================================================================
# Example 1: Generate Paper-Level Embeddings
# =============================================================================

def example_1_paper_embeddings():
    """Example: Generate paper-level embeddings from chunk embeddings."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Generate Paper-Level Embeddings")
    print("=" * 80)
    
    if not TAXONOMY_MODULE_AVAILABLE or not NUMPY_AVAILABLE:
        print("SKIP: Required modules not available")
        return
    
    # Create sample data
    papers = create_sample_papers(n_papers=10)
    chunks = create_sample_chunks(papers, chunks_per_paper=5)
    embeddings_array = create_sample_embeddings(n_embeddings=50, embedding_dim=512)
    
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
    
    print("\nGenerating paper embeddings using weighted mean aggregation...")
    
    # Generate paper embeddings
    paper_embeddings, paper_to_idx = generate_paper_embeddings(
        state,
        embeddings_array,
        embedding_id_to_chunk,
        aggregation_method='weighted_mean'
    )
    
    print(f"✓ Generated embeddings for {len(paper_embeddings)} papers")
    print(f"  Embedding dimension: {next(iter(paper_embeddings.values())).shape[0]}")
    
    # Show sample
    sample_paper_id = list(paper_embeddings.keys())[0]
    sample_embedding = paper_embeddings[sample_paper_id]
    print(f"\nSample paper: {sample_paper_id}")
    print(f"  Embedding shape: {sample_embedding.shape}")
    print(f"  First 5 values: {sample_embedding[:5]}")


# =============================================================================
# Example 2: Build Tier 1 Taxonomy
# =============================================================================

def example_2_tier1_taxonomy():
    """Example: Build Tier 1 taxonomy with clustering."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Build Tier 1 Taxonomy")
    print("=" * 80)
    
    if not TAXONOMY_MODULE_AVAILABLE or not NUMPY_AVAILABLE:
        print("SKIP: Required modules not available")
        return
    
    try:
        from sklearn.cluster import KMeans
    except ImportError:
        print("SKIP: scikit-learn not available")
        return
    
    # Create sample paper embeddings
    n_papers = 30
    paper_ids = [f"paper_{i:03d}" for i in range(n_papers)]
    
    # Create structured embeddings (5 clusters)
    np.random.seed(42)
    embeddings_dict = {}
    for i, pid in enumerate(paper_ids):
        cluster_id = i % 5
        center = np.array([cluster_id * 3.0, cluster_id * 2.0])
        embedding = np.random.randn(64) * 0.5
        embedding[:2] += center
        embeddings_dict[pid] = embedding
    
    paper_to_idx = {pid: i for i, pid in enumerate(paper_ids)}
    
    # Create config
    config = create_default_config()
    config.cluster_tier1_target_k = 5
    
    print(f"\nClustering {n_papers} papers into {config.cluster_tier1_target_k} Tier 1 topics...")
    
    # Build Tier 1 taxonomy
    tier1_clusters, labels, centroids = build_tier1_taxonomy(
        embeddings_dict,
        paper_to_idx,
        config
    )
    
    print(f"✓ Created {len(tier1_clusters)} Tier 1 clusters")
    
    for i, cluster in enumerate(tier1_clusters):
        print(f"\nCluster {i}:")
        print(f"  Papers: {cluster['paper_count']}")
        print(f"  Paper IDs: {cluster['paper_ids'][:5]}...")


# =============================================================================
# Example 3: Generate Topic Labels with GPT-5.1 (Mocked)
# =============================================================================

def example_3_topic_labels():
    """Example: Generate topic labels (with mocked API)."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Generate Topic Labels (Mocked)")
    print("=" * 80)
    
    if not TAXONOMY_MODULE_AVAILABLE:
        print("SKIP: Required modules not available")
        return
    
    # Create sample papers
    papers = create_sample_papers(n_papers=5)
    
    print("\nNote: This example would normally call GPT-5.1 API.")
    print("In production, provide a valid OpenAI API key.")
    print("\nSample papers for labeling:")
    
    for i, (pid, paper) in enumerate(list(papers.items())[:3], 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Abstract: {paper.abstract_text[:80]}...")
    
    print("\n✓ In production, TopicLabelGenerator would analyze these papers")
    print("  and generate labels like:")
    print("  - Label: 'Machine Learning & Deep Learning'")
    print("  - Description: 'Research on neural networks, optimization, and learning algorithms.'")


# =============================================================================
# Example 4: Build Complete 3-Tier Taxonomy
# =============================================================================

def example_4_complete_taxonomy():
    """Example: Build complete 3-tier taxonomy."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Build Complete 3-Tier Taxonomy")
    print("=" * 80)
    
    if not TAXONOMY_MODULE_AVAILABLE or not NUMPY_AVAILABLE:
        print("SKIP: Required modules not available")
        return
    
    # Create sample hierarchy manually (simulating full pipeline)
    tier1_topics = [
        TopicNode(
            id="T1_00",
            label="Machine Learning",
            description="Research on machine learning algorithms and applications",
            paper_ids=[f"paper_{i:03d}" for i in range(0, 10)],
            parent_id=None
        ),
        TopicNode(
            id="T1_01",
            label="Natural Language Processing",
            description="Research on language understanding and generation",
            paper_ids=[f"paper_{i:03d}" for i in range(10, 20)],
            parent_id=None
        ),
        TopicNode(
            id="T1_02",
            label="Computer Vision",
            description="Research on visual recognition and understanding",
            paper_ids=[f"paper_{i:03d}" for i in range(20, 30)],
            parent_id=None
        ),
    ]
    
    tier2_topics = [
        TopicNode(
            id="T2_00",
            label="Deep Learning",
            description="Neural networks and deep architectures",
            paper_ids=[f"paper_{i:03d}" for i in range(0, 5)],
            parent_id="T1_00"
        ),
        TopicNode(
            id="T2_01",
            label="Reinforcement Learning",
            description="Learning from interaction and rewards",
            paper_ids=[f"paper_{i:03d}" for i in range(5, 10)],
            parent_id="T1_00"
        ),
    ]
    
    tier3_topics = [
        TopicNode(
            id="T3_00",
            label="Convolutional Networks",
            description="CNNs for image and spatial data",
            paper_ids=[f"paper_{i:03d}" for i in range(0, 3)],
            parent_id="T2_00"
        ),
    ]
    
    # Create hierarchy
    hierarchy = TopicHierarchy(
        taxonomy_version="v1.0_example",
        created_at=datetime.now(),
        notes="Example taxonomy for demonstration",
        total_papers=30,
        tier1=tier1_topics,
        tier2=tier2_topics,
        tier3=tier3_topics,
        clustering_method='kmeans',
        labeling_model='gpt-5.1-mini'
    )
    
    print("\n✓ Created 3-tier taxonomy:")
    print(f"  Tier 1 topics: {len(hierarchy.tier1)}")
    print(f"  Tier 2 topics: {len(hierarchy.tier2)}")
    print(f"  Tier 3 topics: {len(hierarchy.tier3)}")
    print(f"  Total papers: {hierarchy.total_papers}")
    
    # Validate
    validation = validate_taxonomy_structure(hierarchy)
    print(f"\n✓ Validation: {'PASSED' if validation['valid'] else 'FAILED'}")
    if not validation['valid']:
        print(f"  Issues: {validation['issues']}")
    
    return hierarchy


# =============================================================================
# Example 5: Visualize Taxonomy
# =============================================================================

def example_5_visualize_taxonomy():
    """Example: Visualize taxonomy with statistics."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Visualize Taxonomy")
    print("=" * 80)
    
    if not TAXONOMY_MODULE_AVAILABLE:
        print("SKIP: Required modules not available")
        return
    
    # Create sample hierarchy
    hierarchy = example_4_complete_taxonomy()
    
    print("\n--- Generating Statistics ---")
    
    # Generate statistics
    stats = generate_taxonomy_statistics(hierarchy)
    
    print(f"\nTaxonomy Statistics:")
    print(f"  Version: {stats['taxonomy_version']}")
    print(f"  Total Papers: {stats['total_papers']}")
    print(f"  Total Topics: {stats['total_topics']}")
    print(f"  Tier 1 Topics: {stats['tier1_topics']}")
    print(f"  Tier 2 Topics: {stats['tier2_topics']}")
    print(f"  Tier 3 Topics: {stats['tier3_topics']}")
    print(f"  Avg Papers per Tier 1: {stats['avg_papers_per_tier1']:.1f}")
    
    print("\n--- Displaying Taxonomy Summary ---")
    
    # Create visualizer
    visualizer = TaxonomyVisualizer(hierarchy)
    summary = visualizer.display_taxonomy_summary()
    print(summary)
    
    print("\n✓ Visualization complete")
    print("  In production, plots would be saved to output directory")


# =============================================================================
# Example 6: Save and Load Taxonomy
# =============================================================================

def example_6_save_load_taxonomy():
    """Example: Save and load taxonomy to/from JSON."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Save and Load Taxonomy")
    print("=" * 80)
    
    if not TAXONOMY_MODULE_AVAILABLE:
        print("SKIP: Required modules not available")
        return
    
    # Create sample hierarchy
    hierarchy = TopicHierarchy(
        taxonomy_version="v1.0_test",
        created_at=datetime.now(),
        notes="Test taxonomy",
        total_papers=10,
        tier1=[
            TopicNode(
                id="T1_00",
                label="Test Topic",
                description="A test topic",
                paper_ids=["p1", "p2"],
                parent_id=None
            )
        ],
        tier2=[],
        tier3=[],
        clustering_method='kmeans',
        labeling_model='gpt-5.1-mini'
    )
    
    print("\n--- Saving Taxonomy ---")
    
    # Save to JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json_path = f.name
        json.dump(hierarchy.to_dict(), f, indent=2, default=str)
    
    print(f"✓ Saved taxonomy to: {json_path}")
    print(f"  File size: {Path(json_path).stat().st_size} bytes")
    
    print("\n--- Loading Taxonomy ---")
    
    # Load from JSON
    with open(json_path, 'r') as f:
        loaded_data = json.load(f)
    
    loaded_hierarchy = TopicHierarchy.from_dict(loaded_data)
    
    print(f"✓ Loaded taxonomy:")
    print(f"  Version: {loaded_hierarchy.taxonomy_version}")
    print(f"  Tier 1 topics: {len(loaded_hierarchy.tier1)}")
    print(f"  Total papers: {loaded_hierarchy.total_papers}")
    
    # Clean up
    Path(json_path).unlink()


# =============================================================================
# Example 7: Manual Taxonomy Editing
# =============================================================================

def example_7_manual_editing():
    """Example: Manually edit taxonomy structure."""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Manual Taxonomy Editing")
    print("=" * 80)
    
    if not TAXONOMY_MODULE_AVAILABLE:
        print("SKIP: Required modules not available")
        return
    
    # Create initial hierarchy
    hierarchy = TopicHierarchy(
        taxonomy_version="v1.0",
        total_papers=10,
        tier1=[
            TopicNode(
                id="T1_00",
                label="Original Topic",
                description="Original description",
                paper_ids=["p1", "p2", "p3"],
                parent_id=None
            )
        ],
        tier2=[],
        tier3=[]
    )
    
    print(f"\nOriginal taxonomy:")
    print(f"  Tier 1 label: {hierarchy.tier1[0].label}")
    print(f"  Description: {hierarchy.tier1[0].description}")
    print(f"  Papers: {hierarchy.tier1[0].paper_ids}")
    
    print("\n--- Editing Taxonomy ---")
    
    # Edit topic label
    hierarchy.tier1[0].label = "Edited Topic Label"
    hierarchy.tier1[0].description = "Updated description with more detail"
    
    # Add a paper
    hierarchy.tier1[0].add_paper("p4")
    
    # Add a new Tier 2 topic
    new_tier2 = TopicNode(
        id="T2_00",
        label="New Subtopic",
        description="Manually added subtopic",
        paper_ids=["p1", "p2"],
        parent_id="T1_00"
    )
    hierarchy.add_topic(2, new_tier2)
    
    print(f"\nEdited taxonomy:")
    print(f"  Tier 1 label: {hierarchy.tier1[0].label}")
    print(f"  Description: {hierarchy.tier1[0].description}")
    print(f"  Papers: {hierarchy.tier1[0].paper_ids}")
    print(f"  Tier 2 topics: {len(hierarchy.tier2)}")
    
    # Validate
    validation = hierarchy.validate_hierarchy()
    print(f"\n✓ Validation: {'PASSED' if validation['valid'] else 'FAILED'}")


# =============================================================================
# Example 8: Complete Pipeline
# =============================================================================

def example_8_complete_pipeline():
    """Example: Complete taxonomy construction pipeline."""
    print("\n" + "=" * 80)
    print("EXAMPLE 8: Complete Taxonomy Construction Pipeline")
    print("=" * 80)
    
    if not TAXONOMY_MODULE_AVAILABLE or not NUMPY_AVAILABLE:
        print("SKIP: Required modules not available")
        return
    
    print("\nThis example demonstrates the complete workflow:")
    print("1. Generate paper-level embeddings")
    print("2. Build Tier 1 taxonomy")
    print("3. Generate Tier 1 labels (would use GPT-5.1)")
    print("4. Build Tier 2 taxonomy")
    print("5. Generate Tier 2 labels")
    print("6. Build Tier 3 taxonomy")
    print("7. Generate Tier 3 labels")
    print("8. Validate complete hierarchy")
    print("9. Generate visualizations")
    print("10. Save taxonomy")
    
    print("\n✓ In production, use TaxonomyBuilder.build_complete_taxonomy()")
    print("  which orchestrates all these steps automatically.")
    
    print("\nExample usage:")
    print("""
    from topic_taxonomy import TaxonomyBuilder
    
    # Initialize builder
    builder = TaxonomyBuilder(config, api_key)
    
    # Build complete taxonomy
    hierarchy = builder.build_complete_taxonomy(
        state,
        embeddings_array,
        embedding_id_to_chunk
    )
    
    # Validate
    validation = validate_taxonomy_structure(hierarchy)
    
    # Visualize
    viz_results = visualize_taxonomy(hierarchy, output_dir="/path/to/output")
    
    # Save
    taxonomy_path = "/path/to/taxonomy.json"
    with open(taxonomy_path, 'w') as f:
        json.dump(hierarchy.to_dict(), f, indent=2, default=str)
    """)


# =============================================================================
# Main
# =============================================================================

def run_all_examples():
    """Run all examples."""
    print("=" * 80)
    print("PHASE 8 EXAMPLES: Topic Modeling and Taxonomy Construction")
    print("=" * 80)
    
    example_1_paper_embeddings()
    example_2_tier1_taxonomy()
    example_3_topic_labels()
    example_4_complete_taxonomy()
    example_5_visualize_taxonomy()
    example_6_save_load_taxonomy()
    example_7_manual_editing()
    example_8_complete_pipeline()
    
    print("\n" + "=" * 80)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    run_all_examples()
