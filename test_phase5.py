#!/usr/bin/env python3
"""
Test suite for Phase 5: Embedding Generation and FAISS Index

Tests all functionality in embedding_generator.py including:
- Embedding generation with OpenAI API
- Batch processing and rate limiting
- FAISS index creation and management
- Index persistence and loading
- Cost estimation and tracking
- LangGraph worker integration

Note: Some tests require OpenAI API key and FAISS.
Mock tests are provided for environments without these dependencies.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_models import (
    PaperRecord,
    PaperChunk,
    StateManager,
    create_default_config,
)

# Try importing the phase 5 module
try:
    from embedding_generator import (
        # Step 5.1
        EmbeddingGenerator,
        estimate_embedding_cost,
        
        # Step 5.2
        embed_all_chunks,
        embed_chunks_batch,
        
        # Step 5.3
        FaissIndexBuilder,
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
    EMBEDDING_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import embedding_generator: {e}")
    EMBEDDING_MODULE_AVAILABLE = False

# Check for dependencies
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: numpy not available")

try:
    # Only check if faiss is importable; do not keep the import
    __import__('faiss')
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not available")


# =============================================================================
# Test Step 5.1: Embedding Generator
# =============================================================================

def test_estimate_embedding_cost():
    """Test embedding cost estimation."""
    if not EMBEDDING_MODULE_AVAILABLE:
        print("Skipping test_estimate_embedding_cost: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Embedding Cost Estimation")
    print("=" * 70)
    
    # Estimate cost for 100 chunks, 1500 chars each
    estimate = estimate_embedding_cost(
        num_texts=100,
        avg_chars_per_text=1500,
        model="text-embedding-3-large"
    )
    
    print(f"\nEstimate for 100 chunks (1500 chars each):")
    print(f"  Estimated tokens: {estimate['estimated_tokens']}")
    print(f"  Estimated cost: ${estimate['estimated_cost_usd']:.4f}")
    print(f"  Model: {estimate['model']}")
    
    assert estimate['num_texts'] == 100
    assert estimate['avg_chars_per_text'] == 1500
    assert estimate['estimated_tokens'] > 0
    assert estimate['estimated_cost_usd'] > 0
    
    # Test different model
    estimate_small = estimate_embedding_cost(
        num_texts=100,
        avg_chars_per_text=1500,
        model="text-embedding-3-small"
    )
    
    # Small model should be cheaper
    assert estimate_small['estimated_cost_usd'] < estimate['estimated_cost_usd']
    
    print("\n✓ Cost estimation working correctly")


def test_embedding_generator_mock():
    """Test EmbeddingGenerator with mocked OpenAI client."""
    if not EMBEDDING_MODULE_AVAILABLE or not NUMPY_AVAILABLE:
        print("Skipping test_embedding_generator_mock: dependencies not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: EmbeddingGenerator (Mock)")
    print("=" * 70)
    
    # Mock OpenAI response
    mock_embedding = [0.1] * 1536  # text-embedding-3-large dimension
    
    mock_response = Mock()
    mock_response.data = [Mock(embedding=mock_embedding) for _ in range(3)]
    mock_response.usage = Mock(total_tokens=100)
    
    with patch('embedding_generator.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create generator
        generator = EmbeddingGenerator(
            api_key="test_key",
            model="text-embedding-3-large",
            batch_size=10,
        )
        
        print(f"\nGenerator created with model: {generator.model}")
        
        # Generate embeddings
        texts = ["text 1", "text 2", "text 3"]
        embeddings, stats = generator.generate_embeddings(texts, show_progress=False)
        
        print(f"\nGenerated embeddings:")
        print(f"  Shape: {embeddings.shape}")
        print(f"  Tokens used: {stats['total_tokens']}")
        print(f"  API calls: {stats['api_calls']}")
        print(f"  Estimated cost: ${stats['estimated_cost_usd']:.6f}")
        
        assert embeddings.shape == (3, 1536)
        assert stats['total_tokens'] == 100
        assert stats['api_calls'] == 1
        
        # Check cumulative stats
        cumulative_stats = generator.get_stats()
        print(f"\nCumulative stats:")
        print(f"  Total tokens: {cumulative_stats['total_tokens']}")
        print(f"  Total API calls: {cumulative_stats['total_api_calls']}")
        
        assert cumulative_stats['total_tokens'] == 100
        assert cumulative_stats['total_api_calls'] == 1
    
    print("\n✓ EmbeddingGenerator mock test passed")


# =============================================================================
# Test Step 5.2: Embed All Chunks
# =============================================================================

def test_embed_chunks_batch_mock():
    """Test batch chunk embedding with mocked API."""
    if not EMBEDDING_MODULE_AVAILABLE or not NUMPY_AVAILABLE:
        print("Skipping test_embed_chunks_batch_mock: dependencies not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Embed Chunks Batch (Mock)")
    print("=" * 70)
    
    # Create sample chunks
    chunks = [
        PaperChunk(
            paper_id="paper1",
            chunk_id="chunk1",
            section_label="abstract",
            page_start=1,
            page_end=1,
            text="This is chunk 1 text."
        ),
        PaperChunk(
            paper_id="paper1",
            chunk_id="chunk2",
            section_label="introduction",
            page_start=1,
            page_end=2,
            text="This is chunk 2 text."
        ),
    ]
    
    print(f"\nCreated {len(chunks)} test chunks")
    
    # Mock OpenAI response
    mock_embedding = [0.1] * 1536
    mock_response = Mock()
    mock_response.data = [Mock(embedding=mock_embedding) for _ in chunks]
    mock_response.usage = Mock(total_tokens=50)
    
    with patch('embedding_generator.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Embed chunks
        embeddings, updated_chunks, stats = embed_chunks_batch(
            chunks=chunks,
            api_key="test_key",
            model="text-embedding-3-large",
            show_progress=False,
        )
        
        print(f"\nEmbedding results:")
        print(f"  Embeddings shape: {embeddings.shape}")
        print(f"  Updated chunks: {len(updated_chunks)}")
        print(f"  Tokens: {stats['total_tokens']}")
        
        assert embeddings.shape == (2, 1536)
        assert len(updated_chunks) == 2
        
        # Check chunks were updated
        for i, chunk in enumerate(updated_chunks):
            assert chunk.embedding_id == i
            assert chunk.embedding_model == "text-embedding-3-large"
            print(f"  Chunk {i}: embedding_id={chunk.embedding_id}")
    
    print("\n✓ Batch embedding test passed")


def test_embed_all_chunks_integration():
    """Test embed_all_chunks with state integration."""
    if not EMBEDDING_MODULE_AVAILABLE or not NUMPY_AVAILABLE:
        print("Skipping test_embed_all_chunks_integration: dependencies not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Embed All Chunks (State Integration)")
    print("=" * 70)
    
    # Create config and state
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    # Add test papers and chunks
    paper = PaperRecord(
        id="paper1",
        file_path="/test/paper1.pdf",
        filename="paper1.pdf"
    )
    state = StateManager.add_paper(state, paper)
    
    chunks = [
        PaperChunk(
            paper_id="paper1",
            chunk_id="chunk1",
            section_label="abstract",
            page_start=1,
            page_end=1,
            text="Sample abstract text."
        ),
        PaperChunk(
            paper_id="paper1",
            chunk_id="chunk2",
            section_label="introduction",
            page_start=2,
            page_end=2,
            text="Sample introduction text."
        ),
    ]
    state = StateManager.add_chunks(state, "paper1", chunks)
    
    print(f"\nState prepared with {len(chunks)} chunks")
    
    # Mock OpenAI response
    mock_embedding = [0.1] * 1536
    mock_response = Mock()
    mock_response.data = [Mock(embedding=mock_embedding) for _ in chunks]
    mock_response.usage = Mock(total_tokens=60)
    
    with patch('embedding_generator.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Embed all chunks
        updated_state = embed_all_chunks(state, api_key="test_key", show_progress=False)
        
        print(f"\nState updated with embeddings")
        print(f"  Embedding count: {updated_state['stats']['embedding_count']}")
        print(f"  Tokens: {updated_state['stats']['embedding_tokens']}")
        print(f"  Cost: ${updated_state['stats']['embedding_cost_usd']:.6f}")
        
        assert "embeddings" in updated_state
        assert "chunk_embeddings" in updated_state["embeddings"]
        assert updated_state["stats"]["embedding_count"] == 2
        
        # Check chunks were updated
        for chunk in updated_state["chunks"]["paper1"]:
            assert chunk.embedding_id is not None
            assert chunk.embedding_model == config.embedding_model
    
    print("\n✓ Embed all chunks integration test passed")


# =============================================================================
# Test Step 5.3: Build FAISS Index
# =============================================================================

def test_faiss_index_builder():
    """Test FaissIndexBuilder."""
    if not EMBEDDING_MODULE_AVAILABLE or not NUMPY_AVAILABLE or not FAISS_AVAILABLE:
        print("Skipping test_faiss_index_builder: dependencies not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: FAISS Index Builder")
    print("=" * 70)
    
    # Create sample embeddings
    embedding_dim = 128
    num_embeddings = 10
    embeddings = np.random.randn(num_embeddings, embedding_dim).astype(np.float32)
    
    # Create metadata
    metadata = [
        {
            "chunk_id": f"chunk{i}",
            "paper_id": f"paper{i % 3}",
            "section_label": "abstract" if i % 2 == 0 else "introduction",
        }
        for i in range(num_embeddings)
    ]
    
    print(f"\nCreated {num_embeddings} test embeddings (dim={embedding_dim})")
    
    # Build index
    builder = FaissIndexBuilder(embedding_dim=embedding_dim, index_type="FlatIP")
    builder.build_index(embeddings, metadata, normalize=True)
    
    print(f"\nIndex built:")
    print(f"  Total vectors: {builder.index.ntotal}")
    print(f"  Dimension: {builder.index.d}")
    print(f"  Metadata entries: {len(builder.metadata_map)}")
    
    assert builder.index.ntotal == num_embeddings
    assert builder.index.d == embedding_dim
    assert len(builder.metadata_map) == num_embeddings
    
    # Test search
    query = np.random.randn(1, embedding_dim).astype(np.float32)
    distances, indices, meta_list = builder.search(query, top_k=3, normalize=True)
    
    print(f"\nSearch test:")
    print(f"  Retrieved: {len(meta_list)} results")
    print(f"  Top result: chunk_id={meta_list[0]['chunk_id']}, distance={distances[0]:.4f}")
    
    assert len(meta_list) == 3
    assert len(distances) == 3
    
    # Test validation
    validation = builder.validate_index()
    print(f"\nValidation:")
    print(f"  Valid: {validation['valid']}")
    print(f"  Issues: {validation.get('issues', [])}")
    
    assert validation['valid']
    
    print("\n✓ FAISS index builder test passed")


def test_create_metadata_mapping():
    """Test metadata mapping creation."""
    if not EMBEDDING_MODULE_AVAILABLE:
        print("Skipping test_create_metadata_mapping: module not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Create Metadata Mapping")
    print("=" * 70)
    
    # Create sample chunks and papers
    paper = PaperRecord(
        id="paper1",
        file_path="/test/paper1.pdf",
        filename="paper1.pdf",
        title="Test Paper",
        authors=["Author 1"],
        year=2023,
    )
    
    chunks = [
        PaperChunk(
            paper_id="paper1",
            chunk_id="chunk1",
            section_label="abstract",
            page_start=1,
            page_end=1,
            text="Abstract text."
        ),
        PaperChunk(
            paper_id="paper1",
            chunk_id="chunk2",
            section_label="introduction",
            page_start=2,
            page_end=2,
            text="Introduction text."
        ),
    ]
    
    papers = {"paper1": paper}
    
    # Create mapping
    metadata_map = create_metadata_mapping(chunks, papers)
    
    print(f"\nMetadata mapping created:")
    print(f"  Entries: {len(metadata_map)}")
    
    assert len(metadata_map) == 2
    
    # Check first entry
    meta0 = metadata_map[0]
    print(f"\nEntry 0:")
    print(f"  chunk_id: {meta0['chunk_id']}")
    print(f"  paper_id: {meta0['paper_id']}")
    print(f"  paper_title: {meta0['paper_title']}")
    print(f"  section_label: {meta0['section_label']}")
    
    assert meta0['chunk_id'] == "chunk1"
    assert meta0['paper_id'] == "paper1"
    assert meta0['paper_title'] == "Test Paper"
    assert meta0['paper_year'] == 2023
    
    print("\n✓ Metadata mapping test passed")


# =============================================================================
# Test Step 5.4 & 5.5: Save and Load Index
# =============================================================================

def test_save_and_load_index():
    """Test saving and loading FAISS index."""
    if not EMBEDDING_MODULE_AVAILABLE or not NUMPY_AVAILABLE or not FAISS_AVAILABLE:
        print("Skipping test_save_and_load_index: dependencies not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Save and Load FAISS Index")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create and build index
        embedding_dim = 64
        num_embeddings = 5
        embeddings = np.random.randn(num_embeddings, embedding_dim).astype(np.float32)
        metadata = [{"chunk_id": f"chunk{i}"} for i in range(num_embeddings)]
        
        builder = FaissIndexBuilder(embedding_dim=embedding_dim)
        builder.build_index(embeddings, metadata)
        
        print(f"\nBuilt index with {num_embeddings} vectors")
        
        # Save index
        index_path = Path(tmpdir) / "test_index.bin"
        save_faiss_index(builder, str(index_path), version="1.0")
        
        print(f"\nSaved index to: {index_path}")
        assert index_path.exists()
        
        # Check version file
        version_path = index_path.with_suffix('.version.json')
        assert version_path.exists()
        
        with open(version_path, 'r') as f:
            version_info = json.load(f)
            print(f"Version info: {version_info['version']}")
            assert version_info['version'] == "1.0"
            assert version_info['ntotal'] == num_embeddings
        
        # Save metadata
        metadata_path = Path(tmpdir) / "test_metadata.json"
        save_metadata_mapping(builder.metadata_map, str(metadata_path), format="json")
        
        print(f"Saved metadata to: {metadata_path}")
        assert metadata_path.exists()
        
        # Load index
        loaded_index = load_faiss_index(str(index_path), validate=True)
        
        print(f"\nLoaded index:")
        print(f"  Vectors: {loaded_index.ntotal}")
        print(f"  Dimension: {loaded_index.d}")
        
        assert loaded_index.ntotal == num_embeddings
        assert loaded_index.d == embedding_dim
        
        # Load metadata
        loaded_metadata = load_metadata_mapping(str(metadata_path), format="json")
        
        print(f"Loaded metadata:")
        print(f"  Entries: {len(loaded_metadata)}")
        
        assert len(loaded_metadata) == num_embeddings
        assert loaded_metadata[0]['chunk_id'] == "chunk0"
        
        # Validate
        validation = validate_index(loaded_index, loaded_metadata)
        print(f"\nValidation:")
        print(f"  Valid: {validation['valid']}")
        
        assert validation['valid']
    
    print("\n✓ Save and load test passed")


# =============================================================================
# Test LangGraph Worker
# =============================================================================

def test_embedding_generation_worker():
    """Test the complete embedding generation worker."""
    if not EMBEDDING_MODULE_AVAILABLE or not NUMPY_AVAILABLE or not FAISS_AVAILABLE:
        print("Skipping test_embedding_generation_worker: dependencies not available")
        return
    
    print("\n" + "=" * 70)
    print("Test: Embedding Generation Worker")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create config and state
        config = create_default_config()
        state = StateManager.create_initial_state(config)
        
        # Set output paths
        state["faiss_index_path"] = str(Path(tmpdir) / "index.bin")
        state["faiss_meta_path"] = str(Path(tmpdir) / "metadata.json")
        
        # Add test paper and chunks
        paper = PaperRecord(
            id="paper1",
            file_path="/test/paper1.pdf",
            filename="paper1.pdf",
            title="Test Paper"
        )
        state = StateManager.add_paper(state, paper)
        
        chunks = [
            PaperChunk(
                paper_id="paper1",
                chunk_id=f"chunk{i}",
                section_label="abstract",
                page_start=1,
                page_end=1,
                text=f"Sample text {i}."
            )
            for i in range(3)
        ]
        state = StateManager.add_chunks(state, "paper1", chunks)
        
        print(f"\nState prepared with {len(chunks)} chunks")
        
        # Mock OpenAI response
        mock_embedding = [0.1] * 1536
        mock_response = Mock()
        mock_response.data = [Mock(embedding=mock_embedding) for _ in chunks]
        mock_response.usage = Mock(total_tokens=75)
        
        with patch('embedding_generator.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Run worker
            updated_state = embedding_generation_worker(state, api_key="test_key")
            
            print(f"\nWorker completed:")
            print(f"  Phase: {updated_state['current_phase']}")
            print(f"  Embeddings: {updated_state['stats']['embedding_count']}")
            print(f"  Index path: {updated_state['faiss_index_path']}")
            
            assert updated_state['current_phase'] == "embedded"
            assert updated_state['stats']['embedding_count'] == 3
            
            # Check files were created
            index_path = Path(updated_state['faiss_index_path'])
            metadata_path = Path(updated_state['faiss_meta_path'])
            
            assert index_path.exists()
            assert metadata_path.exists()
            
            print(f"\nFiles created:")
            print(f"  Index: {index_path}")
            print(f"  Metadata: {metadata_path}")
    
    print("\n✓ Worker integration test passed")


def test_embedding_worker_updates_paper_status():
    """Test that embedding worker updates paper statuses to 'embedded'."""
    if not EMBEDDING_MODULE_AVAILABLE or not NUMPY_AVAILABLE or not FAISS_AVAILABLE:
        import pytest
        pytest.skip("dependencies not available: EMBEDDING_MODULE, NUMPY, or FAISS")
    
    print("\n" + "=" * 70)
    print("Test: Embedding Worker Updates Paper Status (STRUCTURAL_REVIEW fix)")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create config and state
        config = create_default_config()
        state = StateManager.create_initial_state(config)
        
        # Set output paths
        state["faiss_index_path"] = str(Path(tmpdir) / "index.bin")
        state["faiss_meta_path"] = str(Path(tmpdir) / "metadata.json")
        
        # Add multiple test papers with "parsed" status
        papers = []
        for i in range(3):
            paper = PaperRecord(
                id=f"paper{i}",
                file_path=f"/test/paper{i}.pdf",
                filename=f"paper{i}.pdf",
                title=f"Test Paper {i}",
                processing_status="parsed"  # Papers should be parsed before embedding
            )
            state = StateManager.add_paper(state, paper)
            papers.append(paper)
            
            # Add chunks for each paper
            chunks = [
                PaperChunk(
                    paper_id=f"paper{i}",
                    chunk_id=f"paper{i}_chunk{j}",
                    section_label="body",
                    page_start=1,
                    page_end=1,
                    text=f"Sample text from paper {i} chunk {j}."
                )
                for j in range(2)
            ]
            state = StateManager.add_chunks(state, f"paper{i}", chunks)
        
        print(f"\nState prepared with {len(papers)} papers, each with 2 chunks")
        
        # Verify initial status is "parsed"
        for paper_id in ["paper0", "paper1", "paper2"]:
            assert state["papers"][paper_id].processing_status == "parsed", \
                f"Paper {paper_id} should have 'parsed' status initially"
        
        # Mock OpenAI response
        mock_embedding = [0.1] * 1536
        total_chunks = sum(len(chunks) for chunks in state["chunks"].values())
        mock_response = Mock()
        mock_response.data = [Mock(embedding=mock_embedding) for _ in range(total_chunks)]
        mock_response.usage = Mock(total_tokens=150)
        
        with patch('embedding_generator.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Run worker
            updated_state = embedding_generation_worker(state, api_key="test_key")
            
            print(f"\nWorker completed:")
            print(f"  Phase: {updated_state['current_phase']}")
            
            # Verify ALL papers have "embedded" status
            for paper_id in ["paper0", "paper1", "paper2"]:
                paper = updated_state["papers"][paper_id]
                assert paper.processing_status == "embedded", \
                    f"Paper {paper_id} should have 'embedded' status, got '{paper.processing_status}'"
                print(f"  Paper {paper_id} status: {paper.processing_status}")
            
            print("\n✓ All paper statuses correctly updated to 'embedded'")
    
    print("\n✓ Paper status update test passed")


# =============================================================================
# Main Test Runner
# =============================================================================

def run_all_tests():
    """Run all Phase 5 tests."""
    print("\n" + "=" * 70)
    print("PHASE 5: EMBEDDING GENERATION AND FAISS INDEX - TEST SUITE")
    print("=" * 70)
    
    if not EMBEDDING_MODULE_AVAILABLE:
        print("\nERROR: embedding_generator module not available")
        print("Cannot run tests without the module")
        return
    
    tests = [
        # Step 5.1
        ("Cost Estimation", test_estimate_embedding_cost),
        ("Embedding Generator (Mock)", test_embedding_generator_mock),
        
        # Step 5.2
        ("Embed Chunks Batch (Mock)", test_embed_chunks_batch_mock),
        ("Embed All Chunks (Integration)", test_embed_all_chunks_integration),
        
        # Step 5.3
        ("FAISS Index Builder", test_faiss_index_builder),
        ("Create Metadata Mapping", test_create_metadata_mapping),
        
        # Step 5.4 & 5.5
        ("Save and Load Index", test_save_and_load_index),
        
        # Worker
        ("Embedding Generation Worker", test_embedding_generation_worker),
        ("Embedding Worker Updates Paper Status", test_embedding_worker_updates_paper_status),
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ {test_name} FAILED: {e}")
            failed += 1
        except Exception as e:
            if "Skipping" in str(e) or "dependencies not available" in str(e):
                skipped += 1
            else:
                print(f"\n✗ {test_name} ERROR: {e}")
                failed += 1
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Skipped: {skipped}")
    print(f"Total:   {len(tests)}")
    print("=" * 70)
    
    if failed > 0:
        print("\n⚠️  Some tests failed. Please review the output above.")
    elif passed == len(tests):
        print("\n✓ All tests passed!")
    else:
        print(f"\n✓ {passed} tests passed, {skipped} skipped (missing dependencies)")


if __name__ == "__main__":
    run_all_tests()
