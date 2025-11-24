#!/usr/bin/env python3
"""
Test Suite for Phase 15: RAG Query Interface

Tests all components of the RAG query interface:
- Query function and embedding generation
- FAISS index search and retrieval
- Reranking functionality
- Answer generation using Responses API
- Interactive query interface
- Query history tracking

Version: 1.0
Date: 2025-11-24
"""

import json
import tempfile
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock

# Import modules to test
from rag_models import (
    RunConfig,
    PaperRecord,
    PaperChunk,
    TopicNode,
    TopicHierarchy,
    GraphState,
    StateManager,
    IDGenerator,
)

from rag_query_interface import (
    # Step 15.1
    RAGQueryEngine,
    rag_query,
    generate_query_embedding,
    retrieve_top_k_chunks,
    
    # Step 15.2
    rerank_chunks,
    calculate_relevance_score,
    boost_section_scores,
    
    # Step 15.3
    generate_answer,
    create_context_from_chunks,
    format_citations,
    
    # Step 15.4
    display_query_results,
    format_answer_display,
    get_supporting_papers,
    
    # Step 15.5
    QueryHistory,
    track_query,
    get_query_history,
    export_query_history,
    refine_query,
    
    # Utilities
    search_by_title_substring,
    search_by_author,
    list_papers_in_topic,
    get_corpus_statistics,
)


def create_sample_state() -> GraphState:
    """Create a sample GraphState for testing."""
    config = RunConfig(
        drive_folder_path="test_pdfs",
        summary_model="gpt-4",
        embedding_model="text-embedding-3-large",
    )
    
    # Create sample papers
    paper1 = PaperRecord(
        id="p1",
        file_path="/test/paper1.pdf",
        filename="paper1.pdf",
        title="Attention Is All You Need",
        authors=["Vaswani", "Shazeer", "Parmar"],
        year=2017,
        publish_date=date(2017, 6, 12),
        abstract_text="We propose the Transformer...",
        full_summary="This paper introduces transformers.",
        tier1_topic="T1_NLP",
        tier1_topic_name="Natural Language Processing",
        tier1_confidence=0.95,
        processing_status="classified"
    )
    
    paper2 = PaperRecord(
        id="p2",
        file_path="/test/paper2.pdf",
        filename="paper2.pdf",
        title="BERT: Pre-training of Deep Bidirectional Transformers",
        authors=["Devlin", "Chang", "Lee"],
        year=2019,
        publish_date=date(2019, 10, 11),
        abstract_text="We introduce BERT...",
        full_summary="This paper presents BERT.",
        tier1_topic="T1_NLP",
        tier1_topic_name="Natural Language Processing",
        tier1_confidence=0.92,
        processing_status="classified"
    )
    
    # Create sample chunks
    chunk1 = PaperChunk(
        paper_id="p1",
        chunk_id="p1_c0",
        section_label="abstract",
        page_start=1,
        page_end=1,
        text="We propose a new attention mechanism called the Transformer.",
        embedding_id=0,
        embedding_model="text-embedding-3-large"
    )
    
    chunk2 = PaperChunk(
        paper_id="p1",
        chunk_id="p1_c1",
        section_label="methods",
        page_start=3,
        page_end=4,
        text="The Transformer uses multi-head attention.",
        embedding_id=1,
        embedding_model="text-embedding-3-large"
    )
    
    chunk3 = PaperChunk(
        paper_id="p2",
        chunk_id="p2_c0",
        section_label="abstract",
        page_start=1,
        page_end=1,
        text="BERT is a bidirectional transformer for language understanding.",
        embedding_id=2,
        embedding_model="text-embedding-3-large"
    )
    
    # Create topology
    topic1 = TopicNode(
        id="T1_NLP",
        label="Natural Language Processing",
        description="NLP research",
        paper_ids=["p1", "p2"]
    )
    
    hierarchy = TopicHierarchy(
        taxonomy_version="v1.0",
        total_papers=2,
        tier1=[topic1],
        tier2=[],
        tier3=[]
    )
    
    # Create state
    state = StateManager.create_initial_state(config)
    state = StateManager.add_paper(state, paper1)
    state = StateManager.add_paper(state, paper2)
    state = StateManager.add_chunks(state, "p1", [chunk1, chunk2])
    state = StateManager.add_chunks(state, "p2", [chunk3])
    state['topic_hierarchy'] = hierarchy
    
    return state


def create_mock_faiss_index():
    """Create mock FAISS index and metadata."""
    import numpy as np
    
    # Create mock index
    mock_index = Mock()
    mock_index.ntotal = 3
    
    # Mock search results
    distances = np.array([[0.1, 0.2, 0.3]])
    indices = np.array([[0, 1, 2]])
    mock_index.search = Mock(return_value=(distances, indices))
    
    # Create metadata
    metadata = {
        'chunks': [
            {'chunk_id': 'p1_c0', 'paper_id': 'p1'},
            {'chunk_id': 'p1_c1', 'paper_id': 'p1'},
            {'chunk_id': 'p2_c0', 'paper_id': 'p2'},
        ]
    }
    
    return mock_index, metadata


# =============================================================================
# Step 15.1: Query Function Tests
# =============================================================================

def test_generate_query_embedding():
    """Test query embedding generation."""
    print("\n=== Test: Generate Query Embedding ===")
    
    config = RunConfig(embedding_model="text-embedding-3-large")
    
    with patch('rag_query_interface.OpenAI') as mock_openai:
        # Mock embedding response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_client.embeddings.create = Mock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        # Generate embedding
        embedding = generate_query_embedding(
            query="What is attention mechanism?",
            config=config,
            openai_client=mock_client
        )
        
        assert embedding is not None
        assert len(embedding) == 1536
        print("✓ Query embedding generated successfully")


def test_retrieve_top_k_chunks():
    """Test chunk retrieval."""
    print("\n=== Test: Retrieve Top-K Chunks ===")
    
    state = create_sample_state()
    mock_index, metadata = create_mock_faiss_index()
    
    # Create temp files
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = Path(tmpdir) / "test.index"
        meta_path = Path(tmpdir) / "test_meta.json"
        
        # Create dummy index file so the existence check passes
        index_path.touch()
        
        # Save metadata
        with open(meta_path, 'w') as f:
            json.dump(metadata, f)
        
        state['faiss_index_path'] = str(index_path)
        state['faiss_meta_path'] = str(meta_path)
        
        with patch('rag_query_interface.faiss.read_index', return_value=mock_index):
            with patch('rag_query_interface.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_response = Mock()
                mock_response.data = [Mock(embedding=[0.1] * 1536)]
                mock_client.embeddings.create = Mock(return_value=mock_response)
                mock_openai.return_value = mock_client
                
                chunks = retrieve_top_k_chunks(
                    query="attention mechanism",
                    state=state,
                    top_k=3,
                    openai_client=mock_client
                )
                
                assert len(chunks) > 0
                assert all('chunk_id' in c for c in chunks)
                assert all('paper_id' in c for c in chunks)
                print(f"✓ Retrieved {len(chunks)} chunks")


def test_rag_query_engine_init():
    """Test RAGQueryEngine initialization."""
    print("\n=== Test: RAG Query Engine Initialization ===")
    
    state = create_sample_state()
    
    with patch('rag_query_interface.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Should not raise without FAISS index
        engine = RAGQueryEngine(state=state, openai_client=mock_client, debug=True)
        
        assert engine is not None
        assert engine.state == state
        assert engine.client == mock_client
        assert engine.debug == True
        print("✓ RAGQueryEngine initialized successfully")


# =============================================================================
# Step 15.2: Reranking Tests
# =============================================================================

def test_rerank_chunks():
    """Test chunk reranking."""
    print("\n=== Test: Rerank Chunks ===")
    
    chunks = [
        {
            'chunk_id': 'c1',
            'section_label': 'methods',
            'similarity_score': 0.8,
            'text': 'Methods section text'
        },
        {
            'chunk_id': 'c2',
            'section_label': 'abstract',
            'similarity_score': 0.7,
            'text': 'Abstract text'
        },
        {
            'chunk_id': 'c3',
            'section_label': 'results',
            'similarity_score': 0.75,
            'text': 'Results text'
        },
    ]
    
    reranked = rerank_chunks(
        query="test query",
        chunks=chunks,
        boost_sections={'abstract': 1.5, 'methods': 1.2}
    )
    
    assert len(reranked) == 3
    assert all('rerank_score' in c for c in reranked)
    
    # Abstract should be boosted most
    abstract_chunk = [c for c in reranked if c['section_label'] == 'abstract'][0]
    assert abstract_chunk['rerank_score'] > 0.7
    
    print("✓ Chunks reranked successfully")


def test_calculate_relevance_score():
    """Test relevance score calculation."""
    print("\n=== Test: Calculate Relevance Score ===")
    
    chunk = {
        'text': 'This discusses attention mechanism in transformers',
        'section_label': 'methods'
    }
    
    score = calculate_relevance_score(
        query="attention mechanism",
        chunk=chunk,
        base_score=0.8
    )
    
    assert score >= 0.8  # Should be boosted
    print(f"✓ Relevance score calculated: {score:.3f}")


def test_boost_section_scores():
    """Test section-based score boosting."""
    print("\n=== Test: Boost Section Scores ===")
    
    chunks = [
        {'chunk_id': 'c1', 'section_label': 'abstract', 'similarity_score': 0.7},
        {'chunk_id': 'c2', 'section_label': 'methods', 'similarity_score': 0.8},
        {'chunk_id': 'c3', 'section_label': 'results', 'similarity_score': 0.75},
    ]
    
    # Test overview query type
    boosted = boost_section_scores(chunks, query_type='overview')
    
    assert len(boosted) == 3
    assert all('boosted_score' in c for c in boosted)
    
    # Abstract should be boosted for overview
    abstract_chunk = [c for c in boosted if c['section_label'] == 'abstract'][0]
    assert abstract_chunk['boosted_score'] > 0.7
    
    print("✓ Section scores boosted successfully")


# =============================================================================
# Step 15.3: Answer Generation Tests
# =============================================================================

def test_create_context_from_chunks():
    """Test context creation from chunks."""
    print("\n=== Test: Create Context from Chunks ===")
    
    chunks = [
        {
            'paper_id': 'p1',
            'paper_title': 'Test Paper',
            'section_label': 'abstract',
            'page_start': 1,
            'page_end': 1,
            'text': 'This is test abstract text.',
            'tier1_topic': 'Machine Learning'
        },
        {
            'paper_id': 'p2',
            'paper_title': 'Another Paper',
            'section_label': 'methods',
            'page_start': 3,
            'page_end': 4,
            'text': 'This describes the methods used.',
            'tier1_topic': 'Deep Learning'
        },
    ]
    
    context = create_context_from_chunks(chunks, max_tokens=500)
    
    assert context is not None
    assert 'Test Paper' in context
    assert 'Another Paper' in context
    assert len(context) > 0
    print(f"✓ Context created ({len(context)} chars)")


def test_format_citations():
    """Test citation formatting."""
    print("\n=== Test: Format Citations ===")
    
    chunks = [
        {
            'paper_id': 'p1',
            'paper_title': 'Paper One',
            'paper_authors': ['Author A', 'Author B'],
            'paper_year': 2020
        },
        {
            'paper_id': 'p1',  # Duplicate paper
            'paper_title': 'Paper One',
            'paper_authors': ['Author A', 'Author B'],
            'paper_year': 2020
        },
        {
            'paper_id': 'p2',
            'paper_title': 'Paper Two',
            'paper_authors': ['Author C'],
            'paper_year': 2021
        },
    ]
    
    citations = format_citations(chunks)
    
    assert len(citations) == 2  # Duplicates removed
    assert all('paper_id' in c for c in citations)
    assert all('title' in c for c in citations)
    print(f"✓ Citations formatted ({len(citations)} unique papers)")


def test_generate_answer_with_mock():
    """Test answer generation with mocked API."""
    print("\n=== Test: Generate Answer (Mocked) ===")
    
    state = create_sample_state()
    chunks = [
        {
            'paper_id': 'p1',
            'paper_title': 'Test Paper',
            'paper_authors': ['Author A'],
            'paper_year': 2020,
            'section_label': 'abstract',
            'page_start': 1,
            'page_end': 1,
            'text': 'This paper discusses transformers.',
            'tier1_topic': 'NLP',
            'similarity_score': 0.9
        }
    ]
    
    with patch('rag_query_interface.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.output = "Transformers are neural network architectures."
        mock_client.responses.create = Mock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        result = generate_answer(
            query="What are transformers?",
            chunks=chunks,
            state=state,
            openai_client=mock_client
        )
        
        assert 'answer_text' in result
        assert 'citations' in result
        assert result['answer_text'] is not None
        print(f"✓ Answer generated: {result['answer_text'][:50]}...")


# =============================================================================
# Step 15.4: Interactive Interface Tests
# =============================================================================

def test_display_query_results():
    """Test query results display."""
    print("\n=== Test: Display Query Results ===")
    
    result = {
        'query': 'What is attention?',
        'timestamp': datetime.now().isoformat(),
        'answer_text': 'Attention is a mechanism...',
        'used_papers': [
            {
                'paper_id': 'p1',
                'title': 'Attention Is All You Need',
                'authors': ['Vaswani'],
                'year': 2017,
                'tier1_topic': 'NLP'
            }
        ],
        'retrieved_chunks': [
            {
                'chunk_id': 'c1',
                'paper_title': 'Attention Is All You Need',
                'section_label': 'abstract',
                'page_start': 1,
                'page_end': 1,
                'text': 'We propose attention...',
                'similarity_score': 0.9
            }
        ]
    }
    
    # Should not raise
    display_query_results(result)
    print("✓ Query results displayed successfully")


def test_format_answer_display():
    """Test answer display formatting."""
    print("\n=== Test: Format Answer Display ===")
    
    answer_text = "This is the answer."
    used_papers = [
        {'paper_id': 'p1', 'title': 'Paper One'},
        {'paper_id': 'p2', 'title': 'Paper Two'},
    ]
    used_chunks = [
        {'chunk_id': 'c1', 'paper_id': 'p1'},
        {'chunk_id': 'c2', 'paper_id': 'p2'},
    ]
    
    display = format_answer_display(answer_text, used_papers, used_chunks)
    
    assert display is not None
    assert 'ANSWER:' in display
    assert 'SOURCES:' in display
    assert 'Paper One' in display
    print("✓ Answer display formatted")


def test_get_supporting_papers():
    """Test extracting supporting papers from chunks."""
    print("\n=== Test: Get Supporting Papers ===")
    
    chunks = [
        {
            'paper_id': 'p1',
            'paper_title': 'Paper One',
            'paper_authors': ['A', 'B'],
            'paper_year': 2020,
            'tier1_topic': 'NLP'
        },
        {
            'paper_id': 'p1',  # Duplicate
            'paper_title': 'Paper One',
            'paper_authors': ['A', 'B'],
            'paper_year': 2020,
            'tier1_topic': 'NLP'
        },
        {
            'paper_id': 'p2',
            'paper_title': 'Paper Two',
            'paper_authors': ['C'],
            'paper_year': 2021,
            'tier1_topic': 'CV'
        },
    ]
    
    papers = get_supporting_papers(chunks)
    
    assert len(papers) == 2  # Duplicates removed
    assert all('paper_id' in p for p in papers)
    print(f"✓ Extracted {len(papers)} supporting papers")


# =============================================================================
# Step 15.5: Query History Tests
# =============================================================================

def test_query_history_add():
    """Test adding queries to history."""
    print("\n=== Test: Query History Add ===")
    
    history = QueryHistory()
    
    result = {
        'retrieved_chunks': [{'chunk_id': 'c1'}],
        'answer_text': 'Answer',
        'used_papers': [{'paper_id': 'p1'}]
    }
    
    history.add_query("Test query", result)
    
    assert len(history.queries) == 1
    assert history.queries[0]['query'] == "Test query"
    assert history.queries[0]['has_answer'] == True
    print("✓ Query added to history")


def test_query_history_search():
    """Test searching query history."""
    print("\n=== Test: Query History Search ===")
    
    history = QueryHistory()
    
    history.add_query("attention mechanism", {})
    history.add_query("transformer architecture", {})
    history.add_query("bert model", {})
    
    results = history.search_history("attention")
    
    assert len(results) == 1
    assert results[0]['query'] == "attention mechanism"
    print(f"✓ Found {len(results)} matching queries")


def test_query_history_export_import():
    """Test exporting and importing query history."""
    print("\n=== Test: Query History Export/Import ===")
    
    history = QueryHistory()
    history.add_query("test query 1", {})
    history.add_query("test query 2", {})
    
    with tempfile.TemporaryDirectory() as tmpdir:
        export_path = Path(tmpdir) / "history.json"
        
        # Export
        export_query_history(history, str(export_path))
        
        assert export_path.exists()
        
        # Import
        new_history = QueryHistory()
        new_history.load_from_json(str(export_path))
        
        assert len(new_history.queries) == 2
        print("✓ Query history exported and imported")


def test_track_query():
    """Test tracking queries."""
    print("\n=== Test: Track Query ===")
    
    history = QueryHistory()
    
    query = "What is attention?"
    result = {
        'retrieved_chunks': [{'chunk_id': 'c1'}],
        'used_papers': [{'paper_id': 'p1'}]
    }
    metadata = {'source': 'test'}
    
    track_query(query, result, history, metadata)
    
    assert len(history.queries) == 1
    assert 'metadata' in history.queries[0]
    print("✓ Query tracked successfully")


def test_refine_query():
    """Test query refinement."""
    print("\n=== Test: Refine Query ===")
    
    result = {
        'used_papers': [
            {'tier1_topic': 'NLP'},
            {'tier1_topic': 'Deep Learning'}
        ]
    }
    
    # Test expand
    refined = refine_query("transformers", result, refinement_type='expand')
    assert "transformers" in refined
    assert len(refined) > len("transformers")
    
    # Test narrow
    refined = refine_query("transformers", result, refinement_type='narrow')
    assert "transformers" in refined
    
    # Test rephrase
    refined = refine_query("transformers", result, refinement_type='rephrase')
    assert "transformers" in refined
    
    print("✓ Query refined successfully")


# =============================================================================
# Utility Function Tests
# =============================================================================

def test_search_by_title_substring():
    """Test title substring search."""
    print("\n=== Test: Search by Title Substring ===")
    
    state = create_sample_state()
    
    results = search_by_title_substring(state, "Attention")
    
    assert len(results) == 1
    assert results[0].title == "Attention Is All You Need"
    print(f"✓ Found {len(results)} papers with 'Attention' in title")


def test_search_by_author():
    """Test author search."""
    print("\n=== Test: Search by Author ===")
    
    state = create_sample_state()
    
    results = search_by_author(state, "Vaswani")
    
    assert len(results) == 1
    assert "Vaswani" in results[0].authors
    print(f"✓ Found {len(results)} papers by Vaswani")


def test_list_papers_in_topic():
    """Test listing papers in topic."""
    print("\n=== Test: List Papers in Topic ===")
    
    state = create_sample_state()
    
    results = list_papers_in_topic(state, "T1_NLP", tier=1)
    
    assert len(results) == 2
    assert all(p.tier1_topic == "T1_NLP" for p in results)
    print(f"✓ Found {len(results)} papers in topic T1_NLP")


def test_get_corpus_statistics():
    """Test corpus statistics."""
    print("\n=== Test: Get Corpus Statistics ===")
    
    state = create_sample_state()
    
    stats = get_corpus_statistics(state)
    
    assert stats['total_papers'] == 2
    assert stats['total_chunks'] == 3
    assert 'status_distribution' in stats
    assert 'year_distribution' in stats
    print(f"✓ Corpus statistics: {stats['total_papers']} papers, {stats['total_chunks']} chunks")


# =============================================================================
# Integration Tests
# =============================================================================

def test_end_to_end_query_flow():
    """Test complete query flow (with mocking)."""
    print("\n=== Test: End-to-End Query Flow ===")
    
    state = create_sample_state()
    mock_index, metadata = create_mock_faiss_index()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = Path(tmpdir) / "test.index"
        meta_path = Path(tmpdir) / "test_meta.json"
        
        # Create dummy index file so the existence check passes
        index_path.touch()
        
        with open(meta_path, 'w') as f:
            json.dump(metadata, f)
        
        state['faiss_index_path'] = str(index_path)
        state['faiss_meta_path'] = str(meta_path)
        
        with patch('rag_query_interface.faiss.read_index', return_value=mock_index):
            with patch('rag_query_interface.OpenAI') as mock_openai:
                mock_client = Mock()
                
                # Mock embedding
                mock_emb_response = Mock()
                mock_emb_response.data = [Mock(embedding=[0.1] * 1536)]
                mock_client.embeddings.create = Mock(return_value=mock_emb_response)
                
                # Mock answer generation
                mock_ans_response = Mock()
                mock_ans_response.output = "Transformers are models that use attention."
                mock_client.responses.create = Mock(return_value=mock_ans_response)
                
                mock_openai.return_value = mock_client
                
                # Perform query
                result = rag_query(
                    query="What are transformers?",
                    state=state,
                    top_k=3,
                    openai_client=mock_client
                )
                
                assert 'query' in result
                assert 'retrieved_chunks' in result
                assert 'answer_text' in result
                assert result['query'] == "What are transformers?"
                print("✓ End-to-end query flow completed successfully")


# =============================================================================
# Test Runner
# =============================================================================

def run_all_tests():
    """Run all tests."""
    print("=" * 80)
    print("PHASE 15 TEST SUITE: RAG Query Interface")
    print("=" * 80)
    
    test_count = 0
    passed_count = 0
    
    tests = [
        # Step 15.1: Query Function
        test_generate_query_embedding,
        test_retrieve_top_k_chunks,
        test_rag_query_engine_init,
        
        # Step 15.2: Reranking
        test_rerank_chunks,
        test_calculate_relevance_score,
        test_boost_section_scores,
        
        # Step 15.3: Answer Generation
        test_create_context_from_chunks,
        test_format_citations,
        test_generate_answer_with_mock,
        
        # Step 15.4: Interactive Interface
        test_display_query_results,
        test_format_answer_display,
        test_get_supporting_papers,
        
        # Step 15.5: Query History
        test_query_history_add,
        test_query_history_search,
        test_query_history_export_import,
        test_track_query,
        test_refine_query,
        
        # Utilities
        test_search_by_title_substring,
        test_search_by_author,
        test_list_papers_in_topic,
        test_get_corpus_statistics,
        
        # Integration
        test_end_to_end_query_flow,
    ]
    
    for test_func in tests:
        test_count += 1
        try:
            test_func()
            passed_count += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} FAILED: {e}")
    
    print("\n" + "=" * 80)
    print(f"TEST RESULTS: {passed_count}/{test_count} tests passed")
    print("=" * 80)
    
    if passed_count == test_count:
        print("\n✓ ALL TESTS PASSED!")
        return True
    else:
        print(f"\n✗ {test_count - passed_count} TEST(S) FAILED")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
