# Phase 15: RAG Query Interface - Quick Reference

Quick reference for using the RAG query interface.

---

## Quick Import

```python
from rag_query_interface import (
    # Core Query
    RAGQueryEngine,
    rag_query,
    retrieve_top_k_chunks,
    
    # Reranking
    rerank_chunks,
    boost_section_scores,
    
    # Answer Generation
    generate_answer,
    create_context_from_chunks,
    
    # Interactive
    interactive_query,
    display_query_results,
    
    # History
    QueryHistory,
    track_query,
    export_query_history,
    
    # Utilities
    search_by_title_substring,
    search_by_author,
    list_papers_in_topic,
    get_corpus_statistics,
)
```

---

## Common Tasks

### 1. Simple Query

```python
# Perform RAG query
result = rag_query(
    query="What are transformers?",
    state=state,
    top_k=5
)

# Get answer
print(result['answer_text'])

# Get sources
for paper in result['used_papers']:
    print(f"- {paper['title']}")
```

### 2. Interactive Session

```python
# Start interactive query
result = interactive_query(state, top_k=5)

# Results are automatically displayed
```

### 3. Custom Retrieval

```python
# Retrieve chunks only (no answer)
chunks = retrieve_top_k_chunks(
    query="attention mechanism",
    state=state,
    top_k=10
)

# Rerank manually
reranked = rerank_chunks(
    query="attention mechanism",
    chunks=chunks,
    boost_sections={'abstract': 2.0}
)

# Generate answer from top 5
answer = generate_answer(
    query="attention mechanism",
    chunks=reranked[:5],
    state=state
)
```

### 4. Track Query History

```python
# Initialize history
history = QueryHistory()

# Perform query
result = rag_query(query, state)

# Track it
track_query(query, result, history)

# Export history
export_query_history(history, "history.json")
```

### 5. Search Corpus

```python
# Search by title
papers = search_by_title_substring(state, "transformer")

# Search by author
papers = search_by_author(state, "Vaswani")

# List papers in topic
papers = list_papers_in_topic(state, "T1_NLP", tier=1)

# Get statistics
stats = get_corpus_statistics(state)
print(f"Total: {stats['total_papers']} papers")
```

### 6. Query Engine

```python
# Initialize engine
engine = RAGQueryEngine(
    state=state,
    debug=True  # Enable debug mode
)

# Perform query
result = engine.query(
    query="What are transformers?",
    top_k=5,
    rerank=True,
    generate_answer=True,
    max_context_chunks=5,
    max_context_tokens=4000
)
```

---

## Result Structure

### Query Result

```python
{
    'query': 'What are transformers?',
    'timestamp': '2025-11-24T03:32:28',
    'retrieved_chunks': [
        {
            'chunk_id': 'p1_c0',
            'paper_id': 'p1',
            'paper_title': 'Attention Is All You Need',
            'section_label': 'abstract',
            'text': '...',
            'similarity_score': 0.85,
            'rerank_score': 1.02
        },
        ...
    ],
    'answer_text': 'Transformers are...',
    'used_papers': [
        {
            'paper_id': 'p1',
            'title': 'Attention Is All You Need',
            'authors': ['Vaswani', ...],
            'year': 2017,
            'tier1_topic': 'NLP'
        },
        ...
    ],
    'used_chunks': [
        {
            'chunk_id': 'p1_c0',
            'paper_id': 'p1',
            'paper_title': 'Attention Is All You Need',
            'section': 'abstract',
            'score': 1.02
        },
        ...
    ]
}
```

---

## Configuration

### Query Parameters

- `query`: Natural language query string
- `top_k`: Number of chunks to retrieve (default: 5)
- `rerank`: Enable reranking (default: True)
- `generate_answer`: Generate answer vs retrieval only (default: True)
- `max_context_chunks`: Max chunks in context (default: same as top_k)
- `max_context_tokens`: Max tokens in context (default: ~2000)

### Reranking Options

```python
# Section boost multipliers
boost_sections = {
    'abstract': 1.5,      # Boost abstracts
    'methods': 1.2,       # Boost methods
    'conclusion': 1.3     # Boost conclusions
}

# Query type optimization
query_type = 'overview'   # 'overview', 'methods', 'results', 'general'
```

---

## Best Practices

### Good Queries

✓ "What are the key innovations in transformer architectures?"  
✓ "How does BERT improve upon previous language models?"  
✓ "What methods are used for pre-training large language models?"

### Poor Queries

✗ "transformers" (too vague)  
✗ "Tell me everything about NLP" (too broad)  
✗ "Is BERT better?" (comparative, may lack context)

### Workflow Recommendations

1. **Start broad**: Get overview with general query
2. **Refine**: Use query refinement for better results
3. **Track**: Always track queries in history
4. **Explore**: Use search utilities for specific papers
5. **Validate**: Check supporting papers for relevance

---

## Troubleshooting

### No Results

```python
# Check if FAISS index exists
if not state.get('faiss_index_path'):
    print("FAISS index not built. Run Phase 5 first.")

# Check corpus size
stats = get_corpus_statistics(state)
print(f"Corpus has {stats['total_papers']} papers")
```

### Poor Answer Quality

```python
# Increase top_k for more context
result = rag_query(query, state, top_k=10)

# Enable reranking
result = rag_query(query, state, rerank=True)

# Check retrieved chunks
for chunk in result['retrieved_chunks'][:3]:
    print(f"{chunk['paper_title']}: {chunk['similarity_score']:.3f}")
```

### API Errors

```python
# Check OpenAI credentials
import os
if not os.getenv('OPENAI_API_KEY'):
    print("Set OPENAI_API_KEY environment variable")

# Use custom client
from openai import OpenAI
client = OpenAI(api_key='your-key')
result = rag_query(query, state, openai_client=client)
```

---

## Responses API Details

Phase 15 uses OpenAI Responses API (NOT Chat Completions):

```python
# CORRECT: Responses API
response = client.responses.create(
    model="gpt-4",
    instructions="You are a research assistant...",
    input=f"Question: {query}\n\nContext: {context}"
)
answer = response.output

# WRONG: Don't use Chat Completions
# response = client.chat.completions.create(...)  # ✗
```

**Why Responses API?**
- Cleaner interface for RAG
- Structured input/output
- Optimized for low-latency interactive use
- No Batch API (interactive, not batch)
- No flex tier (consistent latency needed)

---

## Performance

**Typical Query Times:**
- Embedding: ~100ms
- FAISS search: <100ms
- Reranking: <50ms
- Answer generation: 2-5 seconds (LLM dependent)

**Total**: ~2-5 seconds for complete query

**Optimization:**
- Reuse `RAGQueryEngine` instance
- Use lower `top_k` for faster retrieval
- Skip reranking if not needed
- Use `generate_answer=False` for retrieval only

---

## For More Details

- **Full Documentation**: `PHASE15_COMPLETION.md`
- **Usage Examples**: `examples_phase15.py`
- **Test Suite**: `test_phase15.py`
- **Implementation**: `rag_query_interface.py`

---

**Quick Start:**

```python
from rag_query_interface import interactive_query

# Start querying!
result = interactive_query(state)
```
