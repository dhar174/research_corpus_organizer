# Phase 8: Topic Modeling and Taxonomy Construction

> **Status:** ✅ Complete | **Version:** 1.0 | **Date:** 2025-11-22

Build a 3-tier hierarchical topic taxonomy for your research paper corpus using clustering and GPT-5.1 labeling.

---

## 🚀 Quick Start

```python
from topic_taxonomy import build_complete_taxonomy, visualize_taxonomy
from rag_models import create_default_config

# Configure
config = create_default_config()
config.cluster_tier1_target_k = 8
config.cluster_tier2_target_k = 3
config.cluster_tier3_target_k = 2
config.taxonomy_model = 'gpt-5.1-mini'

# Build complete 3-tier taxonomy
hierarchy = build_complete_taxonomy(
    state=state,
    embeddings_array=faiss_embeddings,
    embedding_id_to_chunk=chunk_mapping,
    config=config,
    api_key=openai_api_key
)

# Visualize and save
viz = visualize_taxonomy(hierarchy, output_dir='/drive/taxonomy')
print(f"Created {len(hierarchy.tier1)} Tier 1 topics")

# Save taxonomy
import json
with open('/drive/taxonomy.json', 'w') as f:
    json.dump(hierarchy.to_dict(), f, indent=2, default=str)
```

---

## 📋 What's Included

### Implementation (`topic_taxonomy.py`)
- ✅ Paper-level embedding generation (3 aggregation methods)
- ✅ 3-tier hierarchical clustering (KMeans, Agglomerative)
- ✅ Automatic k selection (silhouette, elbow)
- ✅ GPT-5.1 topic labeling with context awareness
- ✅ Complete taxonomy construction pipeline
- ✅ Validation and visualization tools
- ✅ LangGraph worker integration

### Testing (`test_phase8.py`)
- ✅ 15+ comprehensive tests
- ✅ Mock tests for API calls
- ✅ Unit and integration coverage

### Examples (`examples_phase8.py`)
1. Generate paper-level embeddings
2. Build Tier 1 taxonomy
3. Generate topic labels
4. Build complete 3-tier taxonomy
5. Visualize taxonomy
6. Save and load taxonomy
7. Manual taxonomy editing
8. Complete pipeline

### Documentation
- **PHASE8_COMPLETION.md** - Full API reference and usage guide
- **PHASE8_INDEX.md** - Quick function reference
- **PHASE8_SUMMARY.md** - Executive summary
- **README_PHASE8.md** - This file

---

## 🎯 Key Features

### Paper-Level Embeddings
Aggregate chunk embeddings into single paper representation:
- **mean**: Simple average
- **weighted_mean**: Section-aware (abstract 3x, conclusion 2x) ⭐ Recommended
- **abstract_only**: Use abstract chunk only

### 3-Tier Clustering
- **Tier 1**: Broad research areas (5-15 topics)
- **Tier 2**: Mid-level topics (2-5 per Tier 1)
- **Tier 3**: Fine-grained topics (2-4 per Tier 2)

### GPT-5.1 Topic Labeling
- Context from representative papers
- Parent-aware for Tier 2/3
- Sibling-aware for distinctiveness
- Structured JSON output

### Validation & Visualization
- Parent-child relationship validation
- Cluster distribution plots
- Comprehensive statistics
- Text summaries

---

## 📚 Core Functions

### Complete Taxonomy
```python
hierarchy = build_complete_taxonomy(
    state, embeddings_array, embedding_id_to_chunk, config, api_key
)
```

### Step-by-Step

```python
# Step 8.1: Paper embeddings
paper_embeddings, paper_to_idx = generate_paper_embeddings(
    state, embeddings_array, embedding_id_to_chunk
)

# Step 8.2: Tier 1 clustering
tier1_clusters, labels, centroids = build_tier1_taxonomy(
    paper_embeddings, paper_to_idx, config
)

# Step 8.3: Tier 1 labels
tier1_topics = generate_tier1_labels(
    tier1_clusters, papers, paper_embeddings, centroids, config, api_key
)

# Steps 8.4-8.5: Tier 2
tier2_clusters, _, tier2_centroids = build_tier2_taxonomy(
    tier1_topics, paper_embeddings, config
)
tier2_topics = generate_tier2_labels(
    tier2_clusters, tier1_topics, papers, paper_embeddings,
    tier2_centroids, config, api_key
)

# Steps 8.6-8.7: Tier 3 (similar pattern)
```

### Visualization
```python
# Generate statistics
stats = generate_taxonomy_statistics(hierarchy)

# Create visualizations
viz_results = visualize_taxonomy(hierarchy, output_dir='/drive/output')

# Display summary
visualizer = TaxonomyVisualizer(hierarchy)
print(visualizer.display_taxonomy_summary())
```

---

## ⚙️ Configuration

### Recommended k Values

**Small corpus (50-100 papers):**
```python
config.cluster_tier1_target_k = 5
config.cluster_tier2_target_k = 2
config.cluster_tier3_target_k = 2
```

**Medium corpus (100-500 papers):**
```python
config.cluster_tier1_target_k = 8
config.cluster_tier2_target_k = 3
config.cluster_tier3_target_k = 2
```

**Large corpus (500+ papers):**
```python
config.cluster_tier1_target_k = 12
config.cluster_tier2_target_k = 4
config.cluster_tier3_target_k = 3
```

### Automatic k Selection
```python
# Let silhouette method choose
config.cluster_tier1_target_k = None  # Will auto-select

# Or manually determine
optimal_k = determine_optimal_k(embeddings, k_range=(5, 15))
config.cluster_tier1_target_k = optimal_k
```

---

## 📊 Data Structures

### TopicNode
```python
topic = TopicNode(
    id="T1_00",                    # T1_*, T2_*, or T3_*
    label="Machine Learning",      # 2-6 words
    description="Research on...",  # 2-3 sentences
    paper_ids=["p1", "p2", ...],  # Papers in this topic
    parent_id=None,                # Parent topic (None for Tier 1)
    centroid=[...],                # Embedding centroid
    paper_count=25                 # Auto-calculated
)
```

### TopicHierarchy
```python
hierarchy = TopicHierarchy(
    taxonomy_version="v1.0_20251122",
    created_at=datetime.now(),
    notes="3-tier taxonomy",
    total_papers=100,
    tier1=[...],  # TopicNode list
    tier2=[...],  # TopicNode list  
    tier3=[...],  # TopicNode list
    clustering_method='kmeans',
    labeling_model='gpt-5.1-mini'
)
```

---

## 💰 Cost & Performance

### API Costs (GPT-5.1-mini)
- **100 papers**: ~$1.70
- **1000 papers**: ~$3.90

### Computation Time
- **100 papers**: ~2-3 minutes
- **1000 papers**: ~20-30 minutes

### Memory Usage
- Paper embeddings: ~2 MB per 1000 papers
- Taxonomy structure: ~100 KB

---

## 🔧 Dependencies

```bash
pip install numpy scikit-learn openai matplotlib seaborn tqdm
```

**Required:**
- numpy
- scikit-learn
- openai

**Optional (for visualization):**
- matplotlib
- seaborn
- tqdm

---

## 🧪 Testing

```bash
# Run all tests
python test_phase8.py

# Run examples
python examples_phase8.py
```

---

## 📖 Documentation

- **[PHASE8_COMPLETION.md](PHASE8_COMPLETION.md)** - Complete API reference and usage guide
- **[PHASE8_INDEX.md](PHASE8_INDEX.md)** - Quick function reference
- **[PHASE8_SUMMARY.md](PHASE8_SUMMARY.md)** - Executive summary

---

## 🔗 Integration

### LangGraph Worker
```python
from topic_taxonomy import taxonomy_construction_worker

state = taxonomy_construction_worker(
    state, embeddings_array, embedding_id_to_chunk,
    api_key, output_dir='/drive/output'
)
```

### Pipeline Position
- **After**: Phase 5 (Embedding Generation)
- **Before**: Phase 9 (Taxonomy Review)

---

## ✅ Best Practices

1. **Use weighted mean aggregation** for best results
2. **Validate after construction** to catch issues early
3. **Choose appropriate k values** for your corpus size
4. **Save intermediate results** for debugging
5. **Review before approval** using visualization tools

---

## 🚦 Next Steps

After Phase 8, proceed to:
- **Phase 9**: Taxonomy Review and Approval
- **Phase 10**: Final Topic Classification (Pass 3)
- **Phase 11**: Classification Review and Correction

---

## 📝 Example Output

```
================================================================================
TAXONOMY SUMMARY
================================================================================
Version: v1.0_20251122_150000
Created: 2025-11-22 15:00:00
Total Papers: 100
Clustering Method: kmeans
Labeling Model: gpt-5.1-mini

TIER 1 TOPICS:
--------------------------------------------------------------------------------

T1_00: Machine Learning & Deep Learning (35 papers)
   Research on neural networks, optimization algorithms, and learning methods
   for various AI applications.
   Tier 2 sub-topics:
     - T2_00: Convolutional Neural Networks (15 papers)
     - T2_01: Recurrent Neural Networks (12 papers)
     - T2_02: Optimization Methods (8 papers)

T1_01: Natural Language Processing (28 papers)
   Studies on language understanding, generation, and transformer architectures
   for text processing tasks.
   Tier 2 sub-topics:
     - T2_03: Language Models (18 papers)
     - T2_04: Text Classification (10 papers)

T1_02: Computer Vision (22 papers)
   Research on image recognition, object detection, and visual understanding
   using deep learning approaches.
   ...

================================================================================
Total Topics: Tier1=8, Tier2=24, Tier3=48
================================================================================
```

---

## 📄 License

Part of the RAG PDF Research Corpus System project.

---

**For detailed documentation, see [PHASE8_COMPLETION.md](PHASE8_COMPLETION.md)**
