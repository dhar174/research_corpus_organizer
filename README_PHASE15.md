# Phase 15: RAG Query Interface - README

**Phase 15** implements the RAG (Retrieval-Augmented Generation) query interface for exploring the research corpus.

---

## What Is This?

The RAG query interface allows users to ask natural language questions about the research corpus and receive answers grounded in the actual papers, with proper citations.

**Example:**
```
User: "What are the key innovations in transformer architectures?"

Answer: "The key innovations in transformer architectures include the multi-head 
attention mechanism and positional encoding, as described in 'Attention Is All You Need' 
(p1). The architecture eliminates recurrence and convolution, relying entirely on attention 
mechanisms for capturing dependencies in sequences."

Sources:
- Attention Is All You Need (2017) by Vaswani et al.
- BERT: Pre-training of Deep Bidirectional Transformers (2019) by Devlin et al.
```

---

## Quick Start

### Basic Usage

```python
from rag_query_interface import rag_query

# Ask a question
result = rag_query(
    query="What are transformers?",
    state=state,  # Your corpus state from previous phases
    top_k=5
)

# Get the answer
print(result['answer_text'])

# See sources
for paper in result['used_papers']:
    print(f"- {paper['title']} ({paper['year']})")
```

### Interactive Mode

```python
from rag_query_interface import interactive_query

# Start interactive session
# This will prompt for input and display formatted results
result = interactive_query(state, top_k=5)
```

---

## How It Works

1. **Query Embedding**: Your question is converted to a vector using OpenAI embeddings
2. **Retrieval**: FAISS index finds the most similar chunks from the corpus
3. **Reranking**: Chunks are reranked based on relevance heuristics
4. **Context Assembly**: Top chunks are formatted into context
5. **Answer Generation**: GPT generates an answer via Responses API
6. **Display**: Results are formatted and shown to user

---

## Key Features

### 1. Flexible Retrieval

```python
# Get more results
result = rag_query(query, state, top_k=10)

# Retrieval only (no answer)
chunks = retrieve_top_k_chunks(query, state, top_k=5)
```

### 2. Smart Reranking

```python
# Automatic reranking (enabled by default)
result = rag_query(query, state, rerank=True)

# Custom section boosting
from rag_query_interface import rerank_chunks
reranked = rerank_chunks(
    query=query,
    chunks=chunks,
    boost_sections={'abstract': 2.0, 'methods': 1.5}
)
```

### 3. Query History

```python
from rag_query_interface import QueryHistory, track_query

# Initialize history
history = QueryHistory()

# Track queries
track_query(query, result, history)

# Search history
matches = history.search_history("attention")

# Export
from rag_query_interface import export_query_history
export_query_history(history, "my_queries.json")
```

### 4. Search Utilities

```python
from rag_query_interface import (
    search_by_title_substring,
    search_by_author,
    list_papers_in_topic
)

# Find papers
papers = search_by_title_substring(state, "BERT")
papers = search_by_author(state, "Vaswani")
papers = list_papers_in_topic(state, "T1_NLP", tier=1)
```

---

## Files

### Main Implementation
- **`rag_query_interface.py`**: Complete RAG interface implementation
  - Query engine and retrieval
  - Reranking algorithms
  - Answer generation via Responses API
  - Interactive interface
  - Query history management
  - Search utilities

### Testing & Examples
- **`test_phase15.py`**: Comprehensive test suite (22 tests)
- **`examples_phase15.py`**: Usage examples (6 examples)

### Documentation
- **`PHASE15_COMPLETION.md`**: Full completion report
- **`PHASE15_SUMMARY.md`**: High-level summary
- **`PHASE15_INDEX.md`**: Quick reference guide
- **`README_PHASE15.md`**: This file

---

## Requirements

Phase 15 requires completion of:
- ✅ Phase 1: Data models
- ✅ Phase 5: FAISS index and embeddings
- ✅ Phase 6: Summaries (optional, enhances answers)
- ✅ Phase 8: Topic taxonomy (optional, shown in results)

---

## API Usage

Phase 15 uses the **OpenAI Responses API** (not Chat Completions):

```python
# Responses API call (what we use)
response = client.responses.create(
    model="gpt-4",
    instructions="You are a research assistant...",
    input=f"Question: {query}\n\nContext: {context}"
)
```

**Why Responses API?**
- Cleaner interface for RAG workloads
- Structured instructions + input
- Optimized for interactive, low-latency queries
- No Batch API (queries are time-sensitive)
- No flex tier (consistent latency needed)

---

## Common Use Cases

### 1. Research Questions

```python
result = rag_query(
    query="What are the limitations of BERT?",
    state=state,
    top_k=5
)
```

### 2. Method Queries

```python
result = rag_query(
    query="How do transformers use positional encoding?",
    state=state,
    top_k=5
)
```

### 3. Overview Queries

```python
result = rag_query(
    query="What are the main approaches to pre-training language models?",
    state=state,
    top_k=10  # More context for broad questions
)
```

### 4. Specific Paper Search

```python
papers = search_by_title_substring(state, "GPT-3")
for paper in papers:
    print(f"{paper.title} ({paper.year})")
    print(f"  {paper.abstract_text[:200]}...")
```

---

## Best Practices

### Writing Good Queries

✓ **Good**: "What are the key innovations in transformer architectures?"  
✗ **Bad**: "transformers" (too vague)

✓ **Good**: "How does BERT use masked language modeling?"  
✗ **Bad**: "bert mlm" (too terse)

✓ **Good**: "What are the benefits of pre-training vs training from scratch?"  
✗ **Bad**: "pretraining" (needs context)

### Optimizing Results

1. **Start with top_k=5**: Good balance of speed and context
2. **Use reranking**: Improves relevance (enabled by default)
3. **Check sources**: Verify that cited papers are relevant
4. **Refine if needed**: Use query refinement for better results
5. **Track queries**: Learn what works well in your corpus

### Handling Errors

```python
try:
    result = rag_query(query, state)
    
    if 'error' in result:
        print(f"Query error: {result['error']}")
    else:
        print(result['answer_text'])
        
except Exception as e:
    print(f"Failed to query: {e}")
    print("Check that FAISS index is built and OpenAI API key is set")
```

---

## Troubleshooting

### "FAISS index not found"

Make sure Phase 5 has completed and built the FAISS index:

```python
# Check if index exists
if state.get('faiss_index_path'):
    print(f"Index: {state['faiss_index_path']}")
else:
    print("Run Phase 5 to build FAISS index")
```

### "OpenAI API error"

Check your API key:

```python
import os
if not os.getenv('OPENAI_API_KEY'):
    print("Set OPENAI_API_KEY environment variable")
```

### Poor answer quality

- Increase `top_k` for more context
- Check that papers have good summaries
- Verify that retrieved chunks are relevant
- Try query refinement

---

## Performance

**Typical query times:**
- Small corpus (100 papers): ~2-3 seconds
- Medium corpus (1,000 papers): ~3-4 seconds  
- Large corpus (10,000 papers): ~4-5 seconds

Most time is spent in answer generation (LLM call). Retrieval is fast (<100ms).

---

## What's Next?

After Phase 15, you can:
- Add custom reranking algorithms
- Implement multi-hop retrieval
- Build query expansion
- Add analytics dashboards
- Create specialized query modes

---

## Learn More

- **Full Documentation**: See `PHASE15_COMPLETION.md`
- **Examples**: See `examples_phase15.py`
- **API Reference**: See `PHASE15_INDEX.md`
- **Tests**: See `test_phase15.py`

---

## Support

For issues or questions:
1. Check `PHASE15_COMPLETION.md` for detailed documentation
2. Run test suite: `python test_phase15.py`
3. Review examples: `python examples_phase15.py`

---

**Phase 15 Status:** ✅ COMPLETE

**Happy Querying! 🔍**
