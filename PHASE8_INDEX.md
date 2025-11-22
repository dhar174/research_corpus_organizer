# Phase 8: Topic Modeling and Taxonomy Construction - Quick Reference

**Version:** 1.0  
**Date:** 2025-11-22  
**Module:** `topic_taxonomy.py`

---

## Function Index

### Step 8.1: Paper-Level Embeddings

#### `PaperEmbeddingGenerator`
```python
generator = PaperEmbeddingGenerator(aggregation_method='weighted_mean')
paper_embeddings, paper_to_idx = generator.generate_paper_embeddings(
    state, embeddings_array, embedding_id_to_chunk
)
```

#### `generate_paper_embeddings()`
```python
paper_embeddings, paper_to_idx = generate_paper_embeddings(
    state, embeddings_array, embedding_id_to_chunk,
    aggregation_method='weighted_mean'
)
```

---

### Step 8.2: Tier 1 Clustering

#### `determine_optimal_k()`
```python
optimal_k = determine_optimal_k(
    embeddings, k_range=(3, 15), method='silhouette'
)
```

#### `cluster_papers()`
```python
labels, centroids = cluster_papers(
    embeddings, n_clusters=8, method='kmeans'
)
```

#### `build_tier1_taxonomy()`
```python
tier1_clusters, labels, centroids = build_tier1_taxonomy(
    paper_embeddings, paper_to_idx, config
)
```

---

### Step 8.3: Tier 1 Labels

#### `TopicLabelGenerator`
```python
generator = TopicLabelGenerator(
    api_key=openai_api_key,
    model='gpt-5.1-mini',
    reasoning_effort='high'
)

label_data = generator.generate_topic_label(
    representative_papers, tier=1
)
```

#### `generate_tier1_labels()`
```python
tier1_topics = generate_tier1_labels(
    tier1_clusters, papers, paper_embeddings,
    centroids, config, api_key
)
```

---

### Step 8.4-8.7: Hierarchical Clustering

#### `build_tier2_taxonomy()`
```python
tier2_clusters, tier2_labels_dict, tier2_centroids_dict = build_tier2_taxonomy(
    tier1_topics, paper_embeddings, config
)
```

#### `generate_tier2_labels()`
```python
tier2_topics = generate_tier2_labels(
    tier2_clusters, tier1_topics, papers, paper_embeddings,
    tier2_centroids_dict, config, api_key
)
```

#### `build_tier3_taxonomy()`
```python
tier3_clusters, tier3_labels_dict, tier3_centroids_dict = build_tier3_taxonomy(
    tier2_topics, paper_embeddings, config
)
```

#### `generate_tier3_labels()`
```python
tier3_topics = generate_tier3_labels(
    tier3_clusters, tier2_topics, papers, paper_embeddings,
    tier3_centroids_dict, config, api_key
)
```

---

### Step 8.8: Build Complete Hierarchy

#### `TaxonomyBuilder`
```python
builder = TaxonomyBuilder(config, api_key)
hierarchy = builder.build_complete_taxonomy(
    state, embeddings_array, embedding_id_to_chunk
)
```

#### `build_complete_taxonomy()`
```python
hierarchy = build_complete_taxonomy(
    state, embeddings_array, embedding_id_to_chunk,
    config, api_key
)
```

#### `validate_taxonomy_structure()`
```python
validation = validate_taxonomy_structure(hierarchy)
if validation['valid']:
    print(f"✅ Valid taxonomy with {validation['total_topics']} topics")
```

---

### Step 8.9: Visualization

#### `TaxonomyVisualizer`
```python
visualizer = TaxonomyVisualizer(hierarchy)
stats = visualizer.generate_statistics()
summary = visualizer.display_taxonomy_summary()
plot_path = visualizer.plot_cluster_distributions('/path/to/output.png')
```

#### `visualize_taxonomy()`
```python
viz_results = visualize_taxonomy(
    hierarchy, output_dir='/drive/taxonomy_viz'
)
print(viz_results['summary'])
```

#### `generate_taxonomy_statistics()`
```python
stats = generate_taxonomy_statistics(hierarchy)
print(f"Total topics: {stats['total_topics']}")
```

---

### LangGraph Worker

#### `taxonomy_construction_worker()`
```python
state = taxonomy_construction_worker(
    state, embeddings_array, embedding_id_to_chunk,
    api_key, output_dir='/drive/output'
)
```

---

## Common Patterns

### Pattern 1: Basic Taxonomy Construction

```python
from topic_taxonomy import build_complete_taxonomy
from rag_models import create_default_config

config = create_default_config()
config.cluster_tier1_target_k = 8
config.cluster_tier2_target_k = 3
config.cluster_tier3_target_k = 2

hierarchy = build_complete_taxonomy(
    state, embeddings_array, embedding_id_to_chunk,
    config, api_key
)
```

### Pattern 2: Step-by-Step Control

```python
from topic_taxonomy import (
    generate_paper_embeddings,
    build_tier1_taxonomy,
    generate_tier1_labels,
    build_tier2_taxonomy,
    generate_tier2_labels
)

# Step 8.1
paper_embeddings, paper_to_idx = generate_paper_embeddings(
    state, embeddings_array, embedding_id_to_chunk
)

# Step 8.2
tier1_clusters, labels, centroids = build_tier1_taxonomy(
    paper_embeddings, paper_to_idx, config
)

# Step 8.3
tier1_topics = generate_tier1_labels(
    tier1_clusters, papers, paper_embeddings,
    centroids, config, api_key
)

# Step 8.4-8.5
tier2_clusters, tier2_labels, tier2_centroids = build_tier2_taxonomy(
    tier1_topics, paper_embeddings, config
)
tier2_topics = generate_tier2_labels(
    tier2_clusters, tier1_topics, papers, paper_embeddings,
    tier2_centroids, config, api_key
)
```

### Pattern 3: Automatic k Selection

```python
from topic_taxonomy import determine_optimal_k

# Let silhouette method choose k
embeddings_array = np.array(list(paper_embeddings.values()))
optimal_k = determine_optimal_k(
    embeddings_array,
    k_range=(5, 15),
    method='silhouette'
)

config.cluster_tier1_target_k = optimal_k
```

### Pattern 4: Save and Load Taxonomy

```python
import json

# Save
with open('taxonomy.json', 'w') as f:
    json.dump(hierarchy.to_dict(), f, indent=2, default=str)

# Load
with open('taxonomy.json', 'r') as f:
    data = json.load(f)
hierarchy = TopicHierarchy.from_dict(data)
```

### Pattern 5: Visualize and Review

```python
from topic_taxonomy import (
    visualize_taxonomy,
    generate_taxonomy_statistics
)

# Generate statistics
stats = generate_taxonomy_statistics(hierarchy)
print(f"Tier 1: {stats['tier1_topics']} topics")
print(f"Tier 2: {stats['tier2_topics']} topics")
print(f"Tier 3: {stats['tier3_topics']} topics")

# Create visualizations
viz_results = visualize_taxonomy(
    hierarchy,
    output_dir='/content/drive/MyDrive/taxonomy_viz'
)

print(viz_results['summary'])
print(f"Saved plot to: {viz_results['plot_path']}")
```

---

## Configuration Parameters

### RunConfig Settings for Phase 8

```python
config = create_default_config()

# Clustering parameters
config.cluster_tier1_target_k = 8      # Tier 1 topics (None = auto)
config.cluster_tier2_target_k = 3      # Tier 2 per Tier 1
config.cluster_tier3_target_k = 2      # Tier 3 per Tier 2

# Model selection
config.taxonomy_model = 'gpt-5.1-mini'  # For topic labeling
config.taxonomy_reasoning_effort = 'high'  # Reasoning level

# Embedding model (used in Phase 5)
config.embedding_model = 'text-embedding-3-large'
```

### Recommended k Values by Corpus Size

**Small corpus (50-100 papers):**
- Tier 1: 4-6 topics
- Tier 2: 2-3 per Tier 1
- Tier 3: 2 per Tier 2

**Medium corpus (100-500 papers):**
- Tier 1: 6-10 topics
- Tier 2: 3-4 per Tier 1
- Tier 3: 2-3 per Tier 2

**Large corpus (500+ papers):**
- Tier 1: 10-15 topics
- Tier 2: 4-5 per Tier 1
- Tier 3: 2-4 per Tier 2

---

## Data Structures

### TopicNode

```python
topic = TopicNode(
    id="T1_00",
    label="Machine Learning",
    description="Research on ML algorithms and applications",
    paper_ids=["paper_001", "paper_002", ...],
    parent_id=None,  # None for Tier 1, parent ID for Tier 2/3
    centroid=[0.1, 0.2, ...]  # Embedding centroid
)
```

### TopicHierarchy

```python
hierarchy = TopicHierarchy(
    taxonomy_version="v1.0_20251122",
    created_at=datetime.now(),
    notes="3-tier taxonomy for research corpus",
    total_papers=100,
    tier1=[...],  # List of Tier 1 TopicNode objects
    tier2=[...],  # List of Tier 2 TopicNode objects
    tier3=[...],  # List of Tier 3 TopicNode objects
    clustering_method='kmeans',
    labeling_model='gpt-5.1-mini'
)
```

---

## Error Handling

### Common Issues

**Issue: "scikit-learn not available"**
```bash
pip install scikit-learn
```

**Issue: "OpenAI API key invalid"**
```python
# Verify API key
import openai
openai.api_key = "your-key-here"
```

**Issue: "Not enough papers for clustering"**
```python
# Ensure minimum papers per cluster
if len(tier1_cluster['paper_ids']) < 2:
    # Skip Tier 2 clustering for this cluster
    continue
```

**Issue: "Validation failed - invalid parent reference"**
```python
# Check parent-child links
validation = hierarchy.validate_hierarchy()
for issue in validation['issues']:
    print(issue)
```

---

## API Costs

### Estimated GPT-5.1 Costs

**For 100 papers:**
- Tier 1 (8 topics): ~$0.20
- Tier 2 (24 topics): ~$0.50
- Tier 3 (48 topics): ~$1.00
- **Total: ~$1.70**

**For 1000 papers:**
- Tier 1 (12 topics): ~$0.30
- Tier 2 (48 topics): ~$1.20
- Tier 3 (96 topics): ~$2.40
- **Total: ~$3.90**

*Costs based on GPT-4 Turbo pricing as of January 2025. Update with actual model pricing when using gpt-5.1 or other models.*

---

## Performance Tips

### 1. Use Weighted Mean Aggregation
Best balance of quality and computational cost.

### 2. Limit Tier 3 Clustering
Only create Tier 3 for larger Tier 2 clusters (>10 papers).

### 3. Cache Embeddings
Save paper embeddings to avoid regeneration.

### 4. Batch API Calls
Use rate limiting but batch prepare contexts.

### 5. Validate Early
Check structure after each tier to catch issues.

---

## Quick Start

```python
# Complete workflow in 5 lines
from topic_taxonomy import build_complete_taxonomy, visualize_taxonomy
from rag_models import create_default_config

config = create_default_config()
hierarchy = build_complete_taxonomy(state, embeddings, chunk_map, config, api_key)
viz = visualize_taxonomy(hierarchy, output_dir='/drive/output')
```

---

## Related Files

- **Implementation:** `topic_taxonomy.py`
- **Tests:** `test_phase8.py`
- **Examples:** `examples_phase8.py`
- **Documentation:** `PHASE8_COMPLETION.md`
- **Summary:** `PHASE8_SUMMARY.md`

---

## Version History

- **v1.0** (2025-11-22): Initial implementation with all 9 steps
