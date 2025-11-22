#!/usr/bin/env python3
"""
Phase 5 Usage Examples: Embedding Generation and FAISS Index

This file demonstrates how to use the embedding generation module
for various use cases.

Examples include:
- Generating embeddings with OpenAI API
- Building FAISS index
- Saving and loading index
- Searching the index
- Using the LangGraph worker
- Cost estimation
"""

import sys
from pathlib import Path
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    PaperRecord,
    PaperChunk,
    StateManager,
    create_default_config,
)

from embedding_generator import (
    # Step 5.1
    EmbeddingGenerator,
    create_embedding_generator,
    estimate_embedding_cost,
    
    # Step 5.2
    embed_all_chunks,
    embed_chunks_batch,
    
    # Step 5.3
    FaissIndexBuilder,
    build_faiss_index,
    create_metadata_mapping,
    
    # Step 5.4
    save_faiss_index,
    save_metadata_mapping,
    
    # Step 5.5
    load_faiss_index,
    load_metadata_mapping,
    validate_index,
    
    # Worker
    embedding_generation_worker,
)


# =============================================================================
# Example 1: Cost Estimation
# =============================================================================

def example_cost_estimation():
    """Example: Estimate costs before generating embeddings."""
    print("\n" + "=" * 70)
    print("Example 1: Cost Estimation")
    print("=" * 70)
    
    # Scenario: 500 chunks, average 1500 characters each
    num_chunks = 500
    avg_chars = 1500
    
    print(f"\nScenario: {num_chunks} chunks, {avg_chars} chars each")
    
    # Estimate for different models
    models = [
        "text-embedding-3-small",
        "text-embedding-3-large",
        "text-embedding-ada-002",
    ]
    
    print("\nCost estimates by model:")
    for model in models:
        estimate = estimate_embedding_cost(
            num_texts=num_chunks,
            avg_chars_per_text=avg_chars,
            model=model
        )
        
        print(f"\n  {model}:")
        print(f"    Estimated tokens: {estimate['estimated_tokens']:,}")
        print(f"    Estimated cost: ${estimate['estimated_cost_usd']:.4f} USD")
    
    print("\n💡 Tip: Use smaller models for cost-sensitive applications")


# =============================================================================
# Example 2: Basic Embedding Generation
# =============================================================================

def example_basic_embedding_generation():
    """Example: Generate embeddings for texts."""
    print("\n" + "=" * 70)
    print("Example 2: Basic Embedding Generation")
    print("=" * 70)
    
    # Sample texts
    texts = [
        "This paper introduces a novel approach to machine learning.",
        "Deep neural networks have shown remarkable performance.",
        "Natural language processing enables machines to understand text.",
    ]
    
    print(f"\nTexts to embed: {len(texts)}")
    for i, text in enumerate(texts):
        print(f"  {i+1}. {text[:60]}...")
    
    # Note: Requires OpenAI API key
    print("\nTo generate embeddings (requires API key):")
    print("""
    from embedding_generator import EmbeddingGenerator
    
    generator = EmbeddingGenerator(
        api_key="your-api-key-here",
        model="text-embedding-3-large",
        batch_size=100,
    )
    
    embeddings, stats = generator.generate_embeddings(texts)
    
    print(f"Generated {len(embeddings)} embeddings")
    print(f"Shape: {embeddings.shape}")
    print(f"Cost: ${stats['estimated_cost_usd']:.4f}")
    """)


# =============================================================================
# Example 3: Batch Processing with Chunks
# =============================================================================

def example_batch_chunk_embedding():
    """Example: Embed chunks in batches."""
    print("\n" + "=" * 70)
    print("Example 3: Batch Chunk Embedding")
    print("=" * 70)
    
    # Create sample chunks
    chunks = [
        PaperChunk(
            paper_id="paper1",
            chunk_id=f"chunk{i}",
            section_label="abstract" if i == 0 else "introduction",
            page_start=1,
            page_end=1,
            text=f"This is the content of chunk {i} with important information."
        )
        for i in range(5)
    ]
    
    print(f"\nCreated {len(chunks)} chunks:")
    for chunk in chunks[:3]:
        print(f"  - {chunk.chunk_id}: {chunk.section_label} ({chunk.char_count} chars)")
    print(f"  ... and {len(chunks) - 3} more")
    
    print("\nTo embed chunks (requires API key):")
    print("""
    from embedding_generator import embed_chunks_batch
    
    embeddings, updated_chunks, stats = embed_chunks_batch(
        chunks=chunks,
        api_key="your-api-key-here",
        model="text-embedding-3-large",
        show_progress=True,
    )
    
    # Chunks now have embedding_id and embedding_model set
    for chunk in updated_chunks:
        print(f"{chunk.chunk_id}: embedding_id={chunk.embedding_id}")
    """)


# =============================================================================
# Example 4: Building FAISS Index
# =============================================================================

def example_build_faiss_index():
    """Example: Build and search FAISS index."""
    print("\n" + "=" * 70)
    print("Example 4: Building FAISS Index")
    print("=" * 70)
    
    # Create sample embeddings (in practice, these come from OpenAI)
    num_embeddings = 100
    embedding_dim = 1536  # text-embedding-3-large dimension
    
    print(f"\nCreating sample index:")
    print(f"  Vectors: {num_embeddings}")
    print(f"  Dimension: {embedding_dim}")
    
    # Simulate embeddings
    embeddings = np.random.randn(num_embeddings, embedding_dim).astype(np.float32)
    
    # Create sample metadata
    chunks = [
        PaperChunk(
            paper_id=f"paper{i % 10}",
            chunk_id=f"chunk{i}",
            section_label=["abstract", "introduction", "methods", "results"][i % 4],
            page_start=i // 10 + 1,
            page_end=i // 10 + 1,
            text=f"Chunk {i} text",
            embedding_id=i,
        )
        for i in range(num_embeddings)
    ]
    
    papers = {
        f"paper{i}": PaperRecord(
            id=f"paper{i}",
            file_path=f"/path/paper{i}.pdf",
            filename=f"paper{i}.pdf",
            title=f"Research Paper {i}",
            authors=[f"Author {i}"],
        )
        for i in range(10)
    }
    
    print("\nBuilding FAISS index...")
    
    # Build index
    try:
        index_builder = build_faiss_index(
            embeddings=embeddings,
            chunks=chunks,
            papers=papers,
            index_type="FlatIP",  # Inner product (cosine similarity)
            normalize=True,
        )
        
        print(f"\n✓ Index built successfully:")
        print(f"  Total vectors: {index_builder.index.ntotal}")
        print(f"  Dimension: {index_builder.index.d}")
        print(f"  Metadata entries: {len(index_builder.metadata_map)}")
        
        # Search example
        print("\nSearching the index:")
        query = np.random.randn(1, embedding_dim).astype(np.float32)
        distances, indices, metadata = index_builder.search(query, top_k=5)
        
        print(f"\nTop 5 results:")
        for i, (dist, idx, meta) in enumerate(zip(distances, indices, metadata)):
            print(f"  {i+1}. {meta['chunk_id']} (paper: {meta['paper_id']})")
            print(f"     Section: {meta['section_label']}, Distance: {dist:.4f}")
        
        # Validate
        validation = index_builder.validate_index()
        print(f"\nValidation: {'✓ Passed' if validation['valid'] else '✗ Failed'}")
        
    except ImportError as e:
        print(f"\n⚠️  FAISS not available: {e}")
        print("Install with: pip install faiss-cpu")


# =============================================================================
# Example 5: Saving and Loading Index
# =============================================================================

def example_save_load_index():
    """Example: Persist and reload FAISS index."""
    print("\n" + "=" * 70)
    print("Example 5: Saving and Loading Index")
    print("=" * 70)
    
    print("\nSaving FAISS index and metadata:")
    print("""
    from embedding_generator import (
        save_faiss_index,
        save_metadata_mapping,
        load_faiss_index,
        load_metadata_mapping,
        validate_index,
    )
    
    # After building index
    index_path = "./faiss_index.bin"
    metadata_path = "./faiss_metadata.json"
    
    # Save
    save_faiss_index(index_builder, index_path, version="1.0")
    save_metadata_mapping(
        index_builder.metadata_map,
        metadata_path,
        format="json"
    )
    
    print(f"Index saved to: {index_path}")
    print(f"Metadata saved to: {metadata_path}")
    
    # Later, load the index
    loaded_index = load_faiss_index(index_path, validate=True)
    loaded_metadata = load_metadata_mapping(metadata_path, format="json")
    
    # Validate consistency
    validation = validate_index(loaded_index, loaded_metadata)
    if validation['valid']:
        print("✓ Index loaded and validated successfully")
    else:
        print("✗ Validation issues:", validation['issues'])
    """)
    
    print("\n💡 Tip: Use JSON format for metadata (human-readable)")
    print("   or pickle format for faster loading of large datasets")


# =============================================================================
# Example 6: Complete Pipeline with State
# =============================================================================

def example_complete_pipeline():
    """Example: Complete embedding pipeline with GraphState."""
    print("\n" + "=" * 70)
    print("Example 6: Complete Pipeline with GraphState")
    print("=" * 70)
    
    # Create configuration
    config = create_default_config(
        embedding_model="text-embedding-3-large",
    )
    
    # Create initial state
    state = StateManager.create_initial_state(config)
    
    # Add sample papers and chunks
    print("\n1. Setting up state with papers and chunks...")
    
    paper = PaperRecord(
        id="paper1",
        file_path="/drive/papers/sample.pdf",
        filename="sample.pdf",
        title="Sample Research Paper on AI",
        authors=["Dr. Jane Smith", "Prof. John Doe"],
    )
    
    state = StateManager.add_paper(state, paper)
    
    chunks = [
        PaperChunk(
            paper_id="paper1",
            chunk_id=f"chunk{i}",
            section_label=["abstract", "introduction", "methods"][i % 3],
            page_start=i + 1,
            page_end=i + 1,
            text=f"This is the content of chunk {i} from the paper."
        )
        for i in range(10)
    ]
    
    state = StateManager.add_chunks(state, "paper1", chunks)
    
    print(f"   Added 1 paper with {len(chunks)} chunks")
    
    print("\n2. Generating embeddings (requires API key):")
    print("""
    from embedding_generator import embed_all_chunks
    
    state = embed_all_chunks(
        state=state,
        api_key="your-api-key-here",
        show_progress=True,
    )
    
    # State now contains:
    # - state["embeddings"]["chunk_embeddings"]: numpy array
    # - state["embeddings"]["stats"]: token usage and cost
    # - Updated chunks with embedding_id
    
    print(f"Generated {state['stats']['embedding_count']} embeddings")
    print(f"Cost: ${state['stats']['embedding_cost_usd']:.4f}")
    """)
    
    print("\n3. Building FAISS index:")
    print("""
    from embedding_generator import build_faiss_index
    
    embeddings = state["embeddings"]["chunk_embeddings"]
    all_chunks = []
    for paper_id, chunks in state["chunks"].items():
        all_chunks.extend(chunks)
    
    index_builder = build_faiss_index(
        embeddings=embeddings,
        chunks=all_chunks,
        papers=state["papers"],
    )
    
    print(f"Index built with {index_builder.index.ntotal} vectors")
    """)
    
    print("\n4. Saving artifacts:")
    print("""
    from embedding_generator import save_faiss_index, save_metadata_mapping
    
    save_faiss_index(index_builder, "./faiss_index.bin", version="1.0")
    save_metadata_mapping(index_builder.metadata_map, "./metadata.json")
    
    # Update state with paths
    state["faiss_index_path"] = "./faiss_index.bin"
    state["faiss_meta_path"] = "./metadata.json"
    """)


# =============================================================================
# Example 7: Using the LangGraph Worker
# =============================================================================

def example_langgraph_worker():
    """Example: Use embedding generation worker."""
    print("\n" + "=" * 70)
    print("Example 7: LangGraph Worker Integration")
    print("=" * 70)
    
    print("\nThe worker orchestrates the complete Phase 5 workflow:")
    print("  1. Generate embeddings for all chunks")
    print("  2. Build FAISS index")
    print("  3. Create metadata mapping")
    print("  4. Save index and metadata to disk")
    print("  5. Update GraphState")
    
    print("\nUsage:")
    print("""
    from embedding_generator import embedding_generation_worker
    from rag_models import StateManager, create_default_config
    
    # Create state with papers and chunks (from previous phases)
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    # ... add papers and chunks to state ...
    
    # Set output paths
    state["faiss_index_path"] = "/drive/artifacts/faiss_index.bin"
    state["faiss_meta_path"] = "/drive/artifacts/faiss_metadata.json"
    
    # Run worker
    updated_state = embedding_generation_worker(
        state=state,
        api_key="your-api-key-here",
    )
    
    # Check results
    print(f"Phase: {updated_state['current_phase']}")  # "embedded"
    print(f"Embeddings: {updated_state['stats']['embedding_count']}")
    print(f"Cost: ${updated_state['stats']['embedding_cost_usd']:.4f}")
    print(f"Index saved to: {updated_state['faiss_index_path']}")
    """)
    
    print("\n💡 Tip: The worker is designed to integrate seamlessly")
    print("   with LangGraph workflows and can be used as a node")


# =============================================================================
# Example 8: Querying the Index
# =============================================================================

def example_query_index():
    """Example: Query the FAISS index for retrieval."""
    print("\n" + "=" * 70)
    print("Example 8: Querying the Index for RAG")
    print("=" * 70)
    
    print("\nTo perform RAG queries:")
    print("""
    from embedding_generator import (
        load_faiss_index,
        load_metadata_mapping,
        EmbeddingGenerator,
    )
    
    # 1. Load index and metadata
    index = load_faiss_index("./faiss_index.bin")
    metadata_map = load_metadata_mapping("./faiss_metadata.json")
    
    # 2. Create embedding generator for queries
    generator = EmbeddingGenerator(api_key="your-api-key-here")
    
    # 3. Embed the query
    query = "What are the main contributions of this research?"
    query_embedding, _ = generator.generate_embeddings([query])
    
    # 4. Search the index
    import faiss
    faiss.normalize_L2(query_embedding)  # For cosine similarity
    
    distances, indices = index.search(query_embedding, k=5)
    
    # 5. Retrieve metadata
    print("Top 5 relevant chunks:")
    for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
        meta = metadata_map[int(idx)]
        print(f"{i+1}. {meta['paper_title']} - {meta['section_label']}")
        print(f"   Pages {meta['page_start']}-{meta['page_end']}")
        print(f"   Similarity: {dist:.4f}")
    
    # 6. Use retrieved chunks for answer generation
    # (This would be Phase 15: RAG Query Interface)
    """)
    
    print("\n💡 Tip: Normalize embeddings for cosine similarity,")
    print("   or use L2 distance depending on your index type")


# =============================================================================
# Main Example Runner
# =============================================================================

def run_all_examples():
    """Run all Phase 5 examples."""
    print("\n" + "=" * 70)
    print("PHASE 5: EMBEDDING GENERATION AND FAISS INDEX - USAGE EXAMPLES")
    print("=" * 70)
    
    examples = [
        example_cost_estimation,
        example_basic_embedding_generation,
        example_batch_chunk_embedding,
        example_build_faiss_index,
        example_save_load_index,
        example_complete_pipeline,
        example_langgraph_worker,
        example_query_index,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n⚠️  Example error: {e}")
    
    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 70)
    print("\nNote: Some examples show code snippets. To run them:")
    print("  1. Install dependencies: pip install openai faiss-cpu numpy tqdm")
    print("  2. Set your OpenAI API key")
    print("  3. Run the code snippets in your environment")
    print("\nFor more details, see embedding_generator.py")
    print("=" * 70)


if __name__ == "__main__":
    run_all_examples()
