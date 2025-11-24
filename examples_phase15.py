#!/usr/bin/env python3
"""
Example Usage for Phase 15: RAG Query Interface

Demonstrates how to use the RAG query interface for exploring the corpus.

Version: 1.0
Date: 2025-11-24
"""

from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any

from rag_models import (
    RunConfig,
    PaperRecord,
    PaperChunk,
    TopicNode,
    TopicHierarchy,
    GraphState,
    StateManager,
)

from rag_query_interface import (
    RAGQueryEngine,
    rag_query,
    retrieve_top_k_chunks,
    rerank_chunks,
    generate_answer,
    interactive_query,
    QueryHistory,
    track_query,
    search_by_title_substring,
    search_by_author,
    list_papers_in_topic,
    get_corpus_statistics,
    refine_query,
)


def create_example_state() -> GraphState:
    """Create example state with sample papers."""
    config = RunConfig(
        drive_folder_path="example_pdfs",
        summary_model="gpt-4",
        embedding_model="text-embedding-3-large",
    )
    
    # Create papers
    papers = [
        PaperRecord(
            id="p1",
            file_path="/papers/attention.pdf",
            filename="attention_is_all_you_need.pdf",
            title="Attention Is All You Need",
            authors=["Vaswani", "Shazeer", "Parmar", "Uszkoreit", "Jones"],
            year=2017,
            publish_date=date(2017, 6, 12),
            abstract_text="We propose a new simple network architecture, the Transformer...",
            full_summary="This paper introduces the Transformer architecture based entirely on attention mechanisms.",
            tier1_topic="T1_NLP",
            tier1_topic_name="Natural Language Processing",
            tier1_confidence=0.95,
            tier2_topic="T2_NLP_Arch",
            tier2_topic_name="NLP Architectures",
            processing_status="classified"
        ),
        PaperRecord(
            id="p2",
            file_path="/papers/bert.pdf",
            filename="bert_pretraining.pdf",
            title="BERT: Pre-training of Deep Bidirectional Transformers",
            authors=["Devlin", "Chang", "Lee", "Toutanova"],
            year=2019,
            publish_date=date(2019, 10, 11),
            abstract_text="We introduce BERT, a new language representation model...",
            full_summary="BERT applies bidirectional training of Transformer to language modeling.",
            tier1_topic="T1_NLP",
            tier1_topic_name="Natural Language Processing",
            tier1_confidence=0.92,
            tier2_topic="T2_NLP_Pretrain",
            tier2_topic_name="Pre-training Methods",
            processing_status="classified"
        ),
        PaperRecord(
            id="p3",
            file_path="/papers/gpt3.pdf",
            filename="language_models_are_few_shot_learners.pdf",
            title="Language Models are Few-Shot Learners",
            authors=["Brown", "Mann", "Ryder", "Subbiah"],
            year=2020,
            publish_date=date(2020, 5, 28),
            abstract_text="We show that scaling up language models greatly improves task-agnostic, few-shot performance...",
            full_summary="GPT-3 demonstrates that large language models can perform tasks with minimal examples.",
            tier1_topic="T1_NLP",
            tier1_topic_name="Natural Language Processing",
            tier1_confidence=0.94,
            tier2_topic="T2_NLP_LLM",
            tier2_topic_name="Large Language Models",
            processing_status="classified"
        ),
    ]
    
    # Create chunks
    chunks_dict = {
        "p1": [
            PaperChunk(
                paper_id="p1",
                chunk_id="p1_c0",
                section_label="abstract",
                page_start=1,
                page_end=1,
                text="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
                embedding_id=0
            ),
            PaperChunk(
                paper_id="p1",
                chunk_id="p1_c1",
                section_label="methods",
                page_start=3,
                page_end=4,
                text="The Transformer uses multi-head attention to allow the model to jointly attend to information from different representation subspaces. Scaled dot-product attention computes the attention function on a set of queries simultaneously.",
                embedding_id=1
            ),
        ],
        "p2": [
            PaperChunk(
                paper_id="p2",
                chunk_id="p2_c0",
                section_label="abstract",
                page_start=1,
                page_end=1,
                text="BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers. The pre-trained BERT model can be fine-tuned with just one additional output layer.",
                embedding_id=2
            ),
        ],
        "p3": [
            PaperChunk(
                paper_id="p3",
                chunk_id="p3_c0",
                section_label="abstract",
                page_start=1,
                page_end=1,
                text="Recent work has demonstrated substantial gains on many NLP tasks through pre-training on a large corpus followed by fine-tuning. We show that scaling up language models greatly improves task-agnostic, few-shot performance, achieving strong performance on many tasks without any gradient updates or fine-tuning.",
                embedding_id=3
            ),
        ],
    }
    
    # Create taxonomy
    topics = [
        TopicNode(
            id="T1_NLP",
            label="Natural Language Processing",
            description="Research on natural language understanding and generation",
            paper_ids=["p1", "p2", "p3"]
        ),
        TopicNode(
            id="T2_NLP_Arch",
            label="NLP Architectures",
            description="Neural network architectures for NLP",
            parent_id="T1_NLP",
            paper_ids=["p1"]
        ),
        TopicNode(
            id="T2_NLP_Pretrain",
            label="Pre-training Methods",
            description="Methods for pre-training language models",
            parent_id="T1_NLP",
            paper_ids=["p2"]
        ),
        TopicNode(
            id="T2_NLP_LLM",
            label="Large Language Models",
            description="Large-scale language models and their applications",
            parent_id="T1_NLP",
            paper_ids=["p3"]
        ),
    ]
    
    hierarchy = TopicHierarchy(
        taxonomy_version="v1.0",
        total_papers=3,
        tier1=[topics[0]],
        tier2=topics[1:],
        tier3=[]
    )
    
    # Build state
    state = StateManager.create_initial_state(config)
    for paper in papers:
        state = StateManager.add_paper(state, paper)
    for paper_id, chunks in chunks_dict.items():
        state = StateManager.add_chunks(state, paper_id, chunks)
    state['topic_hierarchy'] = hierarchy
    
    return state


# =============================================================================
# Example 1: Basic RAG Query
# =============================================================================

def example_1_basic_query():
    """Example 1: Perform a basic RAG query."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic RAG Query")
    print("=" * 80)
    
    state = create_example_state()
    
    # Note: In real usage, you would have a FAISS index built
    # For this example, we'll demonstrate the API without actual retrieval
    
    print("\nQuery: 'What is the Transformer architecture?'")
    print("\nIn a real scenario with FAISS index:")
    print("- Query would be embedded using text-embedding-3-large")
    print("- FAISS would retrieve top-5 most similar chunks")
    print("- Chunks would be reranked based on relevance")
    print("- GPT-4 would generate answer from context")
    
    # Show what the API call would look like
    print("\nAPI Usage:")
    print("""
    result = rag_query(
        query="What is the Transformer architecture?",
        state=state,
        top_k=5,
        generate_answer=True
    )
    
    # Result would contain:
    # - answer_text: Generated answer
    # - used_papers: Papers cited in answer
    # - used_chunks: Chunks used for context
    # - retrieved_chunks: All retrieved chunks with scores
    """)
    
    print("✓ Example 1 complete")


# =============================================================================
# Example 2: Reranking Retrieved Chunks
# =============================================================================

def example_2_reranking():
    """Example 2: Demonstrate chunk reranking."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Chunk Reranking")
    print("=" * 80)
    
    # Simulate retrieved chunks
    chunks = [
        {
            'chunk_id': 'p1_c0',
            'paper_id': 'p1',
            'paper_title': 'Attention Is All You Need',
            'section_label': 'methods',
            'similarity_score': 0.75,
            'text': 'Multi-head attention allows...'
        },
        {
            'chunk_id': 'p1_c1',
            'paper_id': 'p1',
            'paper_title': 'Attention Is All You Need',
            'section_label': 'abstract',
            'similarity_score': 0.70,
            'text': 'We propose the Transformer...'
        },
        {
            'chunk_id': 'p2_c0',
            'paper_id': 'p2',
            'paper_title': 'BERT',
            'section_label': 'results',
            'similarity_score': 0.68,
            'text': 'BERT achieves state-of-the-art...'
        },
    ]
    
    print("\nOriginal ranking (by similarity):")
    for i, chunk in enumerate(chunks, 1):
        print(f"{i}. {chunk['paper_title']} - {chunk['section_label']}: {chunk['similarity_score']:.2f}")
    
    # Rerank with section boosting
    reranked = rerank_chunks(
        query="transformer overview",
        chunks=chunks,
        boost_sections={'abstract': 1.5, 'introduction': 1.2}
    )
    
    print("\nAfter reranking (abstract sections boosted):")
    for i, chunk in enumerate(reranked, 1):
        rerank_score = chunk.get('rerank_score', chunk['similarity_score'])
        print(f"{i}. {chunk['paper_title']} - {chunk['section_label']}: {rerank_score:.2f}")
    
    print("\n✓ Example 2 complete")


# =============================================================================
# Example 3: Search Utilities
# =============================================================================

def example_3_search_utilities():
    """Example 3: Use search utility functions."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Search Utilities")
    print("=" * 80)
    
    state = create_example_state()
    
    # Search by title
    print("\n1. Search by title substring 'Transformer':")
    results = search_by_title_substring(state, "Transformer")
    for paper in results:
        print(f"   - {paper.title} ({paper.year})")
    
    # Search by author
    print("\n2. Search by author 'Devlin':")
    results = search_by_author(state, "Devlin")
    for paper in results:
        print(f"   - {paper.title}")
        print(f"     Authors: {', '.join(paper.authors[:3])}")
    
    # List papers in topic
    print("\n3. Papers in topic 'Natural Language Processing':")
    results = list_papers_in_topic(state, "T1_NLP", tier=1)
    for paper in results:
        print(f"   - {paper.title} ({paper.tier1_topic_name})")
    
    # Get corpus statistics
    print("\n4. Corpus statistics:")
    stats = get_corpus_statistics(state)
    print(f"   Total papers: {stats['total_papers']}")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Avg chunks per paper: {stats['avg_chunks_per_paper']:.1f}")
    print(f"   Year distribution: {stats['year_distribution']}")
    
    print("\n✓ Example 3 complete")


# =============================================================================
# Example 4: Query History
# =============================================================================

def example_4_query_history():
    """Example 4: Track and manage query history."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Query History")
    print("=" * 80)
    
    # Create query history
    history = QueryHistory()
    
    # Simulate some queries
    queries_and_results = [
        ("What is attention mechanism?", {
            'retrieved_chunks': [{'chunk_id': 'c1'}, {'chunk_id': 'c2'}],
            'answer_text': 'Attention is...',
            'used_papers': [{'paper_id': 'p1', 'title': 'Attention Is All You Need'}]
        }),
        ("How does BERT work?", {
            'retrieved_chunks': [{'chunk_id': 'c3'}],
            'answer_text': 'BERT uses...',
            'used_papers': [{'paper_id': 'p2', 'title': 'BERT'}]
        }),
        ("What are transformers?", {
            'retrieved_chunks': [{'chunk_id': 'c1'}, {'chunk_id': 'c4'}],
            'answer_text': 'Transformers are...',
            'used_papers': [{'paper_id': 'p1', 'title': 'Attention Is All You Need'}]
        }),
    ]
    
    # Track queries
    for query, result in queries_and_results:
        track_query(query, result, history)
    
    print(f"\nTracked {len(history.queries)} queries")
    
    # Get recent queries
    print("\nRecent queries:")
    recent = history.get_recent(n=3)
    for i, q in enumerate(recent, 1):
        print(f"{i}. '{q['query']}' - {q['result_summary']['num_papers']} papers cited")
    
    # Search history
    print("\nSearching history for 'attention':")
    matches = history.search_history("attention")
    for q in matches:
        print(f"   - '{q['query']}'")
    
    # Query refinement
    print("\nRefining query:")
    original = "transformers"
    result = queries_and_results[0][1]
    
    refined_expand = refine_query(original, result, refinement_type='expand')
    print(f"   Original: '{original}'")
    print(f"   Expanded: '{refined_expand}'")
    
    refined_narrow = refine_query(original, result, refinement_type='narrow')
    print(f"   Narrowed: '{refined_narrow}'")
    
    print("\n✓ Example 4 complete")


# =============================================================================
# Example 5: Answer Generation Context
# =============================================================================

def example_5_answer_context():
    """Example 5: Create context for answer generation."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Answer Generation Context")
    print("=" * 80)
    
    from rag_query_interface import create_context_from_chunks, format_citations
    
    # Sample chunks
    chunks = [
        {
            'paper_id': 'p1',
            'paper_title': 'Attention Is All You Need',
            'paper_authors': ['Vaswani', 'Shazeer'],
            'paper_year': 2017,
            'section_label': 'abstract',
            'page_start': 1,
            'page_end': 1,
            'text': 'We propose the Transformer architecture...',
            'tier1_topic': 'NLP'
        },
        {
            'paper_id': 'p2',
            'paper_title': 'BERT',
            'paper_authors': ['Devlin', 'Chang'],
            'paper_year': 2019,
            'section_label': 'methods',
            'page_start': 3,
            'page_end': 4,
            'text': 'BERT uses masked language modeling...',
            'tier1_topic': 'NLP'
        },
    ]
    
    # Create context
    context = create_context_from_chunks(chunks, max_tokens=500)
    
    print("\nGenerated context for GPT:")
    print("-" * 80)
    print(context)
    print("-" * 80)
    
    # Format citations
    citations = format_citations(chunks)
    
    print("\nFormatted citations:")
    for i, citation in enumerate(citations, 1):
        print(f"{i}. {citation['title']} ({citation['year']})")
        print(f"   Authors: {citation['authors']}")
    
    print("\n✓ Example 5 complete")


# =============================================================================
# Example 6: Complete Workflow
# =============================================================================

def example_6_complete_workflow():
    """Example 6: Demonstrate complete RAG workflow."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Complete RAG Workflow")
    print("=" * 80)
    
    state = create_example_state()
    history = QueryHistory()
    
    print("\nWorkflow Steps:")
    print("1. User enters query")
    print("2. Query is embedded")
    print("3. FAISS retrieves relevant chunks")
    print("4. Chunks are reranked")
    print("5. Context is assembled")
    print("6. GPT generates answer via Responses API")
    print("7. Results are displayed")
    print("8. Query is saved to history")
    
    # Simulate the workflow
    query = "How do transformers use attention?"
    
    print(f"\nQuery: '{query}'")
    
    # Step 1-3: Retrieve (simulated)
    print("\n[Simulated] Retrieving from FAISS...")
    simulated_chunks = [
        {
            'chunk_id': 'p1_c1',
            'paper_id': 'p1',
            'paper_title': 'Attention Is All You Need',
            'paper_authors': ['Vaswani'],
            'paper_year': 2017,
            'section_label': 'methods',
            'page_start': 3,
            'page_end': 4,
            'text': 'Multi-head attention allows the model to attend to different positions.',
            'similarity_score': 0.85,
            'tier1_topic': 'NLP'
        }
    ]
    
    # Step 4: Rerank
    print("[Simulated] Reranking chunks...")
    reranked = rerank_chunks(query, simulated_chunks)
    
    # Step 5-6: Generate answer (simulated)
    print("[Simulated] Generating answer with GPT via Responses API...")
    simulated_answer = {
        'answer_text': "Transformers use multi-head attention mechanisms to process input sequences. The attention mechanism allows the model to focus on different positions and representation subspaces simultaneously, as described in 'Attention Is All You Need' (p1).",
        'used_papers': [
            {
                'paper_id': 'p1',
                'title': 'Attention Is All You Need',
                'authors': ['Vaswani'],
                'year': 2017,
                'tier1_topic': 'NLP'
            }
        ],
        'used_chunks': reranked
    }
    
    # Step 7: Display
    print("\nAnswer:")
    print("-" * 80)
    print(simulated_answer['answer_text'])
    print("-" * 80)
    
    print("\nSources:")
    for paper in simulated_answer['used_papers']:
        print(f"- {paper['title']} ({paper['year']})")
    
    # Step 8: Save to history
    track_query(query, simulated_answer, history)
    print(f"\nQuery saved to history (total: {len(history.queries)})")
    
    print("\n✓ Example 6 complete")


# =============================================================================
# Main Runner
# =============================================================================

def run_all_examples():
    """Run all examples."""
    print("=" * 80)
    print("PHASE 15 EXAMPLES: RAG Query Interface")
    print("=" * 80)
    
    examples = [
        example_1_basic_query,
        example_2_reranking,
        example_3_search_utilities,
        example_4_query_history,
        example_5_answer_context,
        example_6_complete_workflow,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n✗ Error in {example.__name__}: {e}")
    
    print("\n" + "=" * 80)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("- Use rag_query() for complete Q&A workflow")
    print("- Use retrieve_top_k_chunks() for retrieval only")
    print("- Use rerank_chunks() to improve relevance")
    print("- Use QueryHistory to track and refine queries")
    print("- Use search utilities for direct corpus exploration")
    print("- All answer generation uses Responses API (not Chat Completions)")


if __name__ == "__main__":
    run_all_examples()
