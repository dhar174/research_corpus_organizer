# RAG PDF Research Corpus System - Examples

**Version:** 1.0  
**Date:** 2025-11-25

This document provides comprehensive examples for using the RAG PDF Research Corpus System.

---

## Table of Contents

1. [Configuration Examples](#configuration-examples)
2. [Query Examples](#query-examples)
3. [Output Examples](#output-examples)
4. [Common Use Cases](#common-use-cases)
5. [Best Practices Examples](#best-practices-examples)

---

## Configuration Examples

### Example 1: Minimal Configuration

The simplest configuration to get started:

```python
from rag_models import create_default_config

config = create_default_config(
    drive_folder_path="PDFs"  # Your folder in Google Drive
)
```

### Example 2: Research Corpus Configuration

Configuration for processing a research paper corpus:

```python
from rag_models import RunConfig

config = RunConfig(
    # File location
    drive_folder_path="Research_Papers",
    
    # Processing limits
    max_papers_per_run=100,
    max_chunks_per_paper=80,
    
    # Models - using efficient models
    summary_model="gpt-5-mini",
    taxonomy_model="gpt-5-mini",
    classification_model="gpt-5-mini",
    embedding_model="text-embedding-3-large",
    
    # Reasoning effort
    summary_reasoning_effort="medium",
    taxonomy_reasoning_effort="high",
    
    # Taxonomy settings - 8 broad topics with subtopics
    cluster_tier1_target_k=8,
    cluster_tier2_target_k=3,
    cluster_tier3_target_k=2,
    
    # Cost controls
    max_cost_per_run=10.0,
    enable_cost_tracking=True,
    batch_api_calls=True,
)

# Display configuration
print(config.display_config())
```

**Output:**
```
============================================================
RAG PDF System Configuration
============================================================
Drive folder: Research_Papers
Max papers per run: 100
Max pages per paper: unlimited
Max chunks per paper: 80

Models:
  Summary: gpt-5-mini
  Taxonomy: gpt-5-mini
  Classification: gpt-5-mini
  Embedding: text-embedding-3-large

Reasoning Effort:
  Summary: medium
  Taxonomy: high
  Classification: medium

Clustering:
  Tier 1 target k: 8
  Tier 2 target k: 3
  Tier 3 target k: 2

Features:
  OCR fallback: False
  Deep analysis: False
  Taxonomy approval: True

Budget & Cost Controls:
  Max cost per run: $10.0
  Cost warning threshold: 80.0%
  Cost tracking: True
  Result caching: True
  Batch API calls: True
============================================================
```

### Example 3: High-Quality Analysis Configuration

For the best possible analysis quality:

```python
from rag_models import RunConfig

config = RunConfig(
    drive_folder_path="Important_Papers",
    
    # Use full GPT-5 for best quality
    summary_model="gpt-5",
    taxonomy_model="gpt-5",
    classification_model="gpt-5-mini",  # Classification can use mini
    
    # High reasoning effort
    summary_reasoning_effort="high",
    taxonomy_reasoning_effort="high",
    classification_reasoning_effort="medium",
    
    # Enable deep analysis
    enable_deep_analysis_pass=True,
    
    # Larger token limits for detailed summaries
    max_tokens_per_summary=3000,
    
    # Higher budget for quality
    max_cost_per_run=50.0,
)
```

### Example 4: Budget-Conscious Configuration

Minimize costs while maintaining functionality:

```python
from rag_models import RunConfig

config = RunConfig(
    drive_folder_path="PDFs",
    
    # Use cost-effective models
    summary_model="gpt-5-mini",
    taxonomy_model="gpt-5-mini",
    classification_model="gpt-5-mini",
    embedding_model="text-embedding-3-small",  # Smaller embedding model
    
    # Lower reasoning effort
    summary_reasoning_effort="low",
    taxonomy_reasoning_effort="medium",
    
    # Smaller token limits
    max_tokens_per_summary=1000,
    max_tokens_per_classification=500,
    
    # Strict budget
    max_cost_per_run=2.0,
    
    # Enable cost-saving features
    batch_api_calls=True,
    enable_result_caching=True,
)
```

### Example 5: OCR-Enabled Configuration

For corpora with scanned PDFs:

```python
from rag_models import RunConfig

config = RunConfig(
    drive_folder_path="Scanned_Papers",
    
    # Enable OCR fallback
    enable_ocr_fallback=True,
    
    # Larger chunks for OCR text (may be noisier)
    chunk_size_chars=2000,
    chunk_overlap_chars=300,
    
    # Standard models
    summary_model="gpt-5-mini",
    embedding_model="text-embedding-3-large",
)
```

---

## Query Examples

### Example 1: Basic RAG Query

```python
from rag_query_interface import RAGQueryEngine

# Initialize engine with state
engine = RAGQueryEngine(state)

# Simple query
result = engine.query("What are the main challenges in training large language models?")

# Display answer
print("Answer:")
print(result['answer'])
print("\nSources:")
for source in result['sources'][:3]:
    print(f"  - {source['title']} (confidence: {source['score']:.2f})")
```

**Example Output:**
```
Answer:
Based on the research corpus, the main challenges in training large language models include:

1. **Computational Cost**: Training LLMs requires massive computational resources, 
   with recent models requiring thousands of GPU-hours [1].

2. **Data Quality and Scale**: Acquiring high-quality training data at scale while 
   avoiding harmful or biased content remains challenging [2].

3. **Memory Constraints**: Storing model parameters and activations during training 
   often exceeds available GPU memory [3].

4. **Optimization Stability**: Large models are prone to training instabilities, 
   requiring careful learning rate scheduling and gradient clipping [1,2].

Sources:
  - Scaling Laws for Neural Language Models (confidence: 0.92)
  - Training Compute-Optimal Large Language Models (confidence: 0.89)
  - FlashAttention: Fast and Memory-Efficient Attention (confidence: 0.85)
```

### Example 2: Topic-Specific Query

```python
# Query within a specific topic
result = engine.query(
    "How do vision transformers differ from CNNs?",
    top_k=5,
    filter_topics=["T1_ComputerVision"]  # Only search CV papers
)
```

### Example 3: Section-Boosted Query

```python
# Boost results from methods and conclusions
result = engine.query(
    "What evaluation metrics are commonly used?",
    top_k=10,
    boost_sections=['methods', 'results', 'conclusion']
)
```

### Example 4: Interactive Query Session

```python
from rag_query_interface import interactive_query

# Run interactive query with full display
result = interactive_query(
    state,
    query="Explain the attention mechanism in transformers",
    top_k=5,
    rerank=True,
    display_chunks=True  # Show retrieved chunks
)
```

**Example Output:**
```
================================================================================
QUERY: Explain the attention mechanism in transformers
================================================================================

RETRIEVED CHUNKS (5):
--------------------------------------------------------------------------------
1. [Score: 0.94] "Attention Is All You Need" - Abstract
   The dominant sequence transduction models are based on complex recurrent or 
   convolutional neural networks... We propose a new simple network architecture, 
   the Transformer, based solely on attention mechanisms...

2. [Score: 0.91] "BERT: Pre-training of Deep Bidirectional Transformers" - Methods
   The attention mechanism allows the model to focus on relevant parts of the 
   input when producing an output, computing a weighted sum of values based on 
   query-key compatibility...

[... more chunks ...]

GENERATED ANSWER:
--------------------------------------------------------------------------------
The attention mechanism in transformers is a core innovation that enables the 
model to dynamically focus on relevant parts of the input sequence when 
producing each output. Here's how it works:

**Self-Attention (Scaled Dot-Product Attention)**
Given an input sequence, each position computes three vectors: Query (Q), 
Key (K), and Value (V). The attention weights are computed as:

Attention(Q, K, V) = softmax(QK^T / √d_k) * V

This allows each token to "attend" to all other tokens, with the softmax 
determining how much weight to give each relationship.

**Multi-Head Attention**
Instead of single attention, transformers use multiple attention "heads" in 
parallel, each learning different relationships:

MultiHead(Q, K, V) = Concat(head_1, ..., head_h) * W^O

This enables the model to jointly attend to information from different 
representation subspaces.

**Benefits over RNNs/CNNs**
1. Parallel computation (no sequential dependencies)
2. Direct connections between distant positions
3. More interpretable attention patterns

SOURCES:
- Vaswani et al. "Attention Is All You Need" (2017)
- Devlin et al. "BERT: Pre-training of Deep Bidirectional Transformers" (2019)
- Dosovitskiy et al. "An Image is Worth 16x16 Words" (2020)
================================================================================
```

### Example 5: Corpus Search Examples

```python
from corpus_utilities import (
    search_by_title,
    search_by_author,
    search_by_date_range,
    search_by_topic
)

# Search by title keyword
transformer_papers = search_by_title(state, "transformer")
print(f"Found {len(transformer_papers)} papers about transformers")

# Search by author
vaswani_papers = search_by_author(state, "Vaswani")
for paper in vaswani_papers:
    print(f"  - {paper.title}")

# Search by date range
from datetime import date
recent_papers = search_by_date_range(
    state,
    start_date=date(2023, 1, 1),
    end_date=date(2024, 1, 1)
)
print(f"Found {len(recent_papers)} papers from 2023")

# Search by topic
llm_papers = search_by_topic(state, "T1_LLMs")
print(f"Found {len(llm_papers)} papers in LLMs topic")
```

---

## Output Examples

### Example 1: Paper Record

```python
from rag_models import PaperRecord

# Example paper record (as stored in state)
paper = state['papers']['abc123def456']

print(paper.to_dict())
```

**Example Output:**
```json
{
    "id": "abc123def456",
    "file_path": "/content/drive/MyDrive/PDFs/2301.12345.pdf",
    "filename": "2301.12345.pdf",
    "source": "arxiv",
    "arxiv_id": "2301.12345",
    "doi": null,
    "title": "Scaling Laws for Neural Language Models",
    "authors": ["Jared Kaplan", "Sam McCandlish", "Tom Brown", "..."],
    "venue": "arXiv preprint",
    "publish_date": "2020-01-23",
    "year": 2020,
    "abstract_text": "We study empirical scaling laws for language model performance...",
    "full_summary": "This paper presents a comprehensive study of scaling laws governing the performance of language models. The key findings include: 1) Performance scales as a power-law with model size, dataset size, and compute. 2) Larger models are more sample-efficient. 3) Optimal compute allocation follows predictable ratios. The authors propose equations predicting loss as a function of N (parameters), D (data), and C (compute).",
    "tier1_topic": "T1_LLMs",
    "tier1_topic_name": "Large Language Models",
    "tier1_confidence": 0.95,
    "tier2_topic": "T2_Scaling",
    "tier2_topic_name": "Scaling and Efficiency",
    "tier2_confidence": 0.91,
    "tier3_topic": "T3_ScalingLaws",
    "tier3_topic_name": "Scaling Laws and Predictions",
    "tier3_confidence": 0.88,
    "processing_status": "classified",
    "created_at": "2024-01-15T10:30:00",
    "last_updated": "2024-01-15T11:45:00"
}
```

### Example 2: Topic Hierarchy

```python
# Display taxonomy
hierarchy = state['topic_hierarchy']

print(f"Taxonomy Version: {hierarchy.taxonomy_version}")
print(f"Total Papers: {hierarchy.total_papers}")
print(f"\nTier 1 Topics ({len(hierarchy.tier1)}):")

for t1 in hierarchy.tier1:
    print(f"\n  {t1.id}: {t1.label} ({t1.paper_count} papers)")
    print(f"    {t1.description}")
    
    for t2 in hierarchy.get_tier2_topics(t1.id):
        print(f"      └─ {t2.label} ({t2.paper_count})")
        
        for t3 in hierarchy.get_tier3_topics(t2.id):
            print(f"          └─ {t3.label} ({t3.paper_count})")
```

**Example Output:**
```
Taxonomy Version: v1.0_20240115
Total Papers: 150

Tier 1 Topics (8):

  T1_LLMs: Large Language Models (45 papers)
    Research on large-scale language models, training, and applications
      └─ Scaling and Efficiency (18)
          └─ Scaling Laws (8)
          └─ Efficient Training (10)
      └─ Alignment and Safety (15)
          └─ RLHF Methods (9)
          └─ Safety Evaluation (6)
      └─ Applications (12)
          └─ Code Generation (7)
          └─ Reasoning Tasks (5)

  T1_Vision: Computer Vision (32 papers)
    Visual recognition, generation, and understanding
      └─ Vision Transformers (14)
          └─ ViT Architectures (8)
          └─ Efficient ViTs (6)
      └─ Image Generation (10)
          └─ Diffusion Models (6)
          └─ GANs (4)
      └─ Object Detection (8)
          └─ DETR-based (5)
          └─ Real-time Detection (3)

  [... more topics ...]
```

### Example 3: Cost Report

```python
from workflow_orchestrator import print_cost_summary

print_cost_summary(state)
```

**Example Output:**
```
======================================================================
COST REPORT
======================================================================
Period: 2024-01-15 10:30:00 - 2024-01-15 11:45:00

TOTAL COST:
  $3.4521 USD

BUDGET:
  Limit: $10.00
  Remaining: $6.55
  Utilization: 34.5%

COST BREAKDOWN BY OPERATION:
  Embeddings:      $1.2340
  Summarization:   $1.5678
  Taxonomy:        $0.3456
  Classification:  $0.2789
  Other:           $0.0258

TOKEN USAGE:
  Input tokens:    245,678
  Output tokens:   34,567
  Total tokens:    280,245

API CALLS:
  Total calls:     178
    embedding: 150
    summarization: 20
    taxonomy: 5
    classification: 3

RECOMMENDATIONS:
  💡 Consider using text-embedding-3-small for embeddings (6.5x cheaper)
======================================================================
```

### Example 4: QC Report

```python
from quality_control import generate_qc_report

report = generate_qc_report(state, "./qc_report.md")
print(report.get_summary())
```

**Example Output:**
```
================================================================================
QUALITY CONTROL SUMMARY
================================================================================

CORPUS OVERVIEW:
  Total Papers: 150
  Successfully Processed: 145 (96.7%)
  Failed: 5 (3.3%)

PROCESSING STATUS:
  ✓ Classified: 142
  ✓ Summarized: 145
  ⚠ Pending: 0
  ✗ Failed: 5

DATA QUALITY:
  Papers with title: 148 (98.7%)
  Papers with authors: 145 (96.7%)
  Papers with abstract: 140 (93.3%)
  Papers with DOI: 89 (59.3%)
  Papers with arXiv ID: 112 (74.7%)

CHUNK STATISTICS:
  Total chunks: 7,523
  Avg chunks per paper: 50.2
  Sections detected:
    abstract: 145
    introduction: 142
    methods: 138
    results: 135
    conclusion: 140

TAXONOMY CONSISTENCY:
  ✓ All Tier 2 topics have valid Tier 1 parents
  ✓ All Tier 3 topics have valid Tier 2 parents
  ✓ No orphaned papers detected

ISSUES:
  ⚠ 5 papers failed processing
  ⚠ 2 papers missing publish_date
  ⚠ 5 papers missing venue

RECOMMENDATIONS:
  1. Review failed papers: 2301.99999, 2302.00001, ...
  2. Consider enabling OCR for scanned PDFs
  3. Manually add missing metadata where possible
================================================================================
```

### Example 5: Export Formats

**CSV Export:**
```csv
id,title,authors,year,tier1_topic,tier2_topic,full_summary,processing_status
abc123,"Attention Is All You Need","[""Vaswani"", ""Shazeer"", ...]",2017,T1_LLMs,T2_Architectures,"This seminal paper introduces...",classified
def456,"BERT: Pre-training of Deep...","[""Devlin"", ""Chang"", ...]",2019,T1_LLMs,T2_Pretraining,"BERT represents a breakthrough...",classified
```

**JSON Export:**
```json
{
    "metadata": {
        "export_date": "2024-01-15T12:00:00",
        "total_papers": 150,
        "taxonomy_version": "v1.0"
    },
    "papers": {
        "abc123": {
            "title": "Attention Is All You Need",
            "authors": ["Vaswani", "Shazeer", "..."],
            "summary": "...",
            "topics": {
                "tier1": "T1_LLMs",
                "tier2": "T2_Architectures"
            }
        }
    },
    "taxonomy": {
        "tier1": [...],
        "tier2": [...],
        "tier3": [...]
    }
}
```

**BibTeX Export:**
```bibtex
@article{vaswani2017attention,
    title={Attention Is All You Need},
    author={Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and ...},
    journal={Advances in Neural Information Processing Systems},
    year={2017},
    note={arXiv:1706.03762}
}

@article{devlin2019bert,
    title={BERT: Pre-training of Deep Bidirectional Transformers},
    author={Devlin, Jacob and Chang, Ming-Wei and Lee, Kenton and ...},
    journal={NAACL},
    year={2019},
    note={arXiv:1810.04805}
}
```

---

## Common Use Cases

### Use Case 1: Literature Review Preparation

```python
# Step 1: Process papers
config = create_default_config(
    drive_folder_path="LitReview_2024",
    enable_deep_analysis_pass=True,  # Detailed analysis
)
state = run_full_pipeline(config)

# Step 2: Generate organized reading list
from corpus_utilities import create_reading_list

reading_list = create_reading_list(
    state,
    paper_ids=list(state['papers'].keys()),
    output_path="reading_list.md",
    title="Literature Review Reading List"
)

# Step 3: Query for specific themes
engine = RAGQueryEngine(state)
themes = [
    "recent advances in efficiency",
    "main limitations and challenges",
    "future research directions"
]

for theme in themes:
    result = engine.query(f"What do papers say about {theme}?")
    print(f"\n## {theme.title()}")
    print(result['answer'])

# Step 4: Export bibliography
from corpus_utilities import generate_bibtex_entries
bibtex = generate_bibtex_entries(state)
with open("references.bib", "w") as f:
    f.write(bibtex)
```

### Use Case 2: Research Gap Analysis

```python
# Query to identify gaps
gap_queries = [
    "What problems remain unsolved?",
    "What are the limitations mentioned across papers?",
    "What future work is suggested?",
    "What approaches have been under-explored?"
]

engine = RAGQueryEngine(state)

print("# Research Gap Analysis\n")
for query in gap_queries:
    result = engine.query(query, top_k=10)
    print(f"## {query}")
    print(result['answer'])
    print()
```

### Use Case 3: Comparative Analysis

```python
# Compare approaches within a topic
from corpus_utilities import search_by_topic

# Get papers from two different subtopics
vit_papers = search_by_topic(state, "T2_VisionTransformers")
cnn_papers = search_by_topic(state, "T2_CNNs")

# Query for comparison
engine = RAGQueryEngine(state)
comparison = engine.query(
    "Compare the performance and efficiency of Vision Transformers vs CNNs",
    top_k=10
)
print(comparison['answer'])
```

---

## Best Practices Examples

### Example 1: Incremental Processing

```python
# Process in batches to avoid issues
from workflow_orchestrator import save_checkpoint, load_checkpoint

config = create_default_config(
    drive_folder_path="Large_Corpus",
    max_papers_per_run=50,  # Process 50 at a time
)

state = StateManager.create_initial_state(config)

# Process in batches
from drive_utils import discover_pdfs
all_papers = discover_pdfs(config.drive_folder_path, config)
paper_ids = list(all_papers.keys())

batch_size = 50
for i in range(0, len(paper_ids), batch_size):
    batch = paper_ids[i:i+batch_size]
    print(f"Processing batch {i//batch_size + 1}: {len(batch)} papers")
    
    # Process batch
    for paper_id in batch:
        state = StateManager.add_paper(state, all_papers[paper_id])
    
    # Run pipeline for this batch
    # ... processing code ...
    
    # Save checkpoint after each batch
    save_checkpoint(state, f"batch_{i//batch_size}")
    print(f"Checkpoint saved: batch_{i//batch_size}")
```

### Example 2: Error Recovery

```python
from workflow_orchestrator import (
    list_failed_papers,
    retry_failed_papers,
    get_recovery_options
)

# Check what failed
failed = list_failed_papers(state)
print(f"Failed papers: {len(failed)}")

for f in failed[:5]:
    print(f"  - {f['filename']}: {f['error_reason']}")

# Get recovery options
options = get_recovery_options(state)
print("\nRecovery options:")
for rec in options['recommended_actions']:
    print(f"  - {rec}")

# Retry specific types of failures
state = retry_failed_papers(
    state,
    filter_stage="parsing",  # Only retry parsing failures
    max_papers=10
)
```

### Example 3: Cost Monitoring

```python
from workflow_orchestrator import (
    check_budget_before_operation,
    print_cost_summary,
    get_cost_recommendations
)

# Check before expensive operation
can_proceed = check_budget_before_operation(
    state,
    operation="summarization",
    estimated_tokens=50000
)

if can_proceed:
    # Proceed with summarization
    state = summarize_papers_worker(state, api_key)
else:
    print("Insufficient budget! Options:")
    print("1. Increase max_cost_per_run in config")
    print("2. Use a cheaper model")
    print("3. Process fewer papers")

# After processing, review costs
print_cost_summary(state)

# Get recommendations
recommendations = get_cost_recommendations(state)
for rec in recommendations:
    print(f"💡 {rec}")
```

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-25 | Initial examples documentation |

---

**End of Examples**
