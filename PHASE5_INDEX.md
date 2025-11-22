# Phase 5: Embedding Generation and FAISS Index - Quick Reference

**Status:** ✅ Complete  
**Module:** `embedding_generator.py`  
**Tests:** `test_phase5.py`  
**Examples:** `examples_phase5.py`

---

## Quick Start

```python
from embedding_generator import (
    embed_all_chunks,
    embedding_generation_worker,
)

# Option 1: Direct function call
state = embed_all_chunks(state, api_key="your-key", show_progress=True)

# Option 2: LangGraph worker
state = embedding_generation_worker(state, api_key="your-key")
```

---

## Core Functions

### Step 5.1: Embedding Generation
- `EmbeddingGenerator(api_key, model, batch_size, rate_limit_delay, max_retries)`
- `create_embedding_generator(api_key, config)`
- `estimate_embedding_cost(num_texts, avg_chars_per_text, model)`

### Step 5.2: Embed Chunks
- `embed_all_chunks(state, api_key, show_progress)`
- `embed_chunks_batch(chunks, api_key, model, show_progress)`

### Step 5.3: Build FAISS Index
- `FaissIndexBuilder(embedding_dim, index_type)`
- `build_faiss_index(embeddings, chunks, papers, index_type, normalize)`
- `create_metadata_mapping(chunks, papers)`

### Step 5.4: Save Index
- `save_faiss_index(index_builder, index_path, version)`
- `save_metadata_mapping(metadata_map, metadata_path, format)`

### Step 5.5: Load Index
- `load_faiss_index(index_path, validate)`
- `load_metadata_mapping(metadata_path, format)`
- `validate_index(index, metadata_map)`

---

## Key Classes

### EmbeddingGenerator
```python
generator = EmbeddingGenerator(
    api_key="your-key",
    model="text-embedding-3-large",
    batch_size=100,
    rate_limit_delay=1.0,
    max_retries=3,
)

embeddings, stats = generator.generate_embeddings(texts, show_progress=True)
```

### FaissIndexBuilder
```python
builder = FaissIndexBuilder(
    embedding_dim=1536,
    index_type="FlatIP",
)

builder.build_index(embeddings, metadata, normalize=True)
distances, indices, metadata = builder.search(query, top_k=5)
validation = builder.validate_index()
```

---

## Cost Estimation

```python
from embedding_generator import estimate_embedding_cost

# Estimate before processing
estimate = estimate_embedding_cost(
    num_texts=500,
    avg_chars_per_text=1500,
    model="text-embedding-3-large"
)

print(f"Estimated cost: ${estimate['estimated_cost_usd']:.4f}")
```

**Pricing (as of Nov 2025):**
- text-embedding-3-small: $0.02 per 1M tokens
- text-embedding-3-large: $0.13 per 1M tokens
- text-embedding-ada-002: $0.10 per 1M tokens

---

## Error Handling

All functions include comprehensive error handling:
- OpenAI API errors with exponential backoff
- Rate limiting with automatic delays
- FAISS import errors with helpful messages
- File not found errors with clear paths
- Validation errors with detailed reports

---

## Integration Points

### From Phase 1 (Models)
- Uses `PaperChunk` for text data
- Updates `GraphState` via `StateManager`
- Uses `RunConfig` for configuration

### From Phase 3 (Parsing)
- Works with chunks created by `parse_and_chunk_worker`
- Uses `cleaned_text` or `text` from chunks

### To Phase 15 (RAG Queries)
- Provides FAISS index for similarity search
- Metadata mapping for retrieval results
- Search functionality for top-k retrieval

---

## Files

- **embedding_generator.py** - Main implementation (~1000 lines)
- **test_phase5.py** - Test suite (8 tests, ~650 lines)
- **examples_phase5.py** - Usage examples (8 examples, ~550 lines)
- **PHASE5_COMPLETION.md** - Detailed completion report

---

## Dependencies

**Required:**
- openai (`pip install openai`)
- faiss-cpu (`pip install faiss-cpu`)
- numpy (`pip install numpy`)

**Optional:**
- tqdm (`pip install tqdm`) - for progress bars

---

## Common Use Cases

### 1. Generate embeddings for all chunks
```python
state = embed_all_chunks(state, api_key="your-key")
print(f"Generated {state['stats']['embedding_count']} embeddings")
print(f"Cost: ${state['stats']['embedding_cost_usd']:.4f}")
```

### 2. Build and save index
```python
embeddings = state["embeddings"]["chunk_embeddings"]
chunks = [c for chunks in state["chunks"].values() for c in chunks]

builder = build_faiss_index(embeddings, chunks, state["papers"])
save_faiss_index(builder, "./index.bin")
save_metadata_mapping(builder.metadata_map, "./metadata.json")
```

### 3. Load and search index
```python
index = load_faiss_index("./index.bin")
metadata = load_metadata_mapping("./metadata.json")

# Generate query embedding
query_emb, _ = generator.generate_embeddings(["your query"])

# Search
distances, indices = index.search(query_emb, k=5)
for idx in indices[0]:
    print(metadata[int(idx)])
```

---

## Performance

- **Embedding Generation:** ~100 texts/second (network dependent)
- **Index Creation:** <1 second for 10K vectors
- **Index Search:** <10ms for 100K vectors (CPU)
- **Index Save/Load:** <1 second for 100K vectors

---

## Next Steps

With Phase 5 complete, proceed to:
- **Phase 6:** Summarization (Pass 1) - Generate paper summaries
- **Phase 7:** Initial CSV Export - Export processed papers
- **Phase 8:** Topic Taxonomy - Build 3-tier topic hierarchy

---

For detailed documentation, see [PHASE5_COMPLETION.md](PHASE5_COMPLETION.md)
