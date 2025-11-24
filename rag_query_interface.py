#!/usr/bin/env python3
"""
RAG PDF Research Corpus System - RAG Query Interface (Phase 15)

This module implements Phase 15 of the FINAL_NOTEBOOK_ACTION_PLAN.md:
- Step 15.1: Create Query Function (RAG query with embedding and retrieval)
- Step 15.2: Implement Reranking (optional relevance boosting)
- Step 15.3: Create Answer Generation (GPT-5.1 with Responses API)
- Step 15.4: Build Interactive Query Interface (user-facing query functions)
- Step 15.5: Add Query History (tracking and refinement)

This interface provides RAG-based question answering over the research corpus,
using FAISS for retrieval and GPT-5.1 for answer generation via Responses API.

Version: 1.0
Date: 2025-11-24
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Literal

logger = logging.getLogger(__name__)

# OpenAI client
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not available. Install with: pip install openai")

# FAISS
try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS package not available. Install with: pip install faiss-cpu")

from rag_models import (
    PaperRecord,
    PaperChunk,
    GraphState,
    RunConfig,
)

# Export list
__all__ = [
    # Step 15.1: Query Function
    'RAGQueryEngine',
    'rag_query',
    'generate_query_embedding',
    'search_faiss_index',
    'retrieve_top_k_chunks',
    
    # Step 15.2: Reranking
    'rerank_chunks',
    'calculate_relevance_score',
    'boost_section_scores',
    
    # Step 15.3: Answer Generation
    'generate_answer',
    'create_context_from_chunks',
    'format_citations',
    
    # Step 15.4: Interactive Interface
    'interactive_query',
    'display_query_results',
    'format_answer_display',
    'get_supporting_papers',
    
    # Step 15.5: Query History
    'QueryHistory',
    'track_query',
    'get_query_history',
    'export_query_history',
    'refine_query',
    
    # Utility Functions (Phase 22)
    'search_by_title_substring',
    'search_by_author',
    'list_papers_in_topic',
    'get_corpus_statistics',
]


# =============================================================================
# Step 15.1: Create Query Function
# =============================================================================

class RAGQueryEngine:
    """
    Main RAG query engine for the corpus.
    
    Handles embedding generation, FAISS retrieval, reranking, and answer generation.
    """
    
    def __init__(
        self,
        state: GraphState,
        openai_client: Optional[OpenAI] = None,
        debug: bool = False
    ):
        """
        Initialize RAG query engine.
        
        Args:
            state: Current GraphState with papers, chunks, and FAISS index
            openai_client: OpenAI client instance (optional, creates new if None)
            debug: Enable debug logging
        """
        self.state = state
        self.config = state.get('config')
        self.debug = debug
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package required. Install with: pip install openai")
        
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS package required. Install with: pip install faiss-cpu")
        
        self.client = openai_client or OpenAI()
        
        # Load FAISS index
        self.index = None
        self.metadata = None
        self._load_index()
    
    def _load_index(self) -> None:
        """Load FAISS index and metadata."""
        index_path = self.state.get('faiss_index_path')
        meta_path = self.state.get('faiss_meta_path')
        
        if not index_path or not Path(index_path).exists():
            logger.warning("FAISS index not found. Index must be built before querying.")
            return
        
        try:
            self.index = faiss.read_index(index_path)
            
            if meta_path and Path(meta_path).exists():
                with open(meta_path, 'r') as f:
                    self.metadata = json.load(f)
            
            if self.debug:
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
        
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            raise
    
    def query(
        self,
        query: str,
        top_k: int = 5,
        rerank: bool = True,
        generate_answer: bool = True,
        max_context_chunks: Optional[int] = None,
        max_context_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Perform RAG query on the corpus.
        
        Args:
            query: Natural language query
            top_k: Number of chunks to retrieve
            rerank: Whether to rerank retrieved chunks
            generate_answer: Whether to generate an answer (vs just retrieval)
            max_context_chunks: Maximum chunks to include in context
            max_context_tokens: Maximum tokens in context window
        
        Returns:
            Dictionary with query results including:
            - query: Original query
            - retrieved_chunks: List of retrieved chunk metadata
            - answer_text: Generated answer (if generate_answer=True)
            - used_papers: Papers cited in answer
            - used_chunks: Chunks used for answer
            - debug_info: Additional debug information (if debug=True)
        """
        if not self.index:
            raise ValueError("FAISS index not loaded. Cannot perform query.")
        
        start_time = time.time()
        
        # Step 1: Generate query embedding
        query_embedding = self._generate_embedding(query)
        
        # Step 2: Search FAISS index
        retrieved = self._search_index(query_embedding, top_k=top_k)
        
        # Step 3: Rerank if requested
        if rerank:
            retrieved = self._rerank_results(query, retrieved)
        
        # Step 4: Generate answer if requested
        answer_result = None
        if generate_answer:
            answer_result = self._generate_answer(
                query=query,
                retrieved_chunks=retrieved,
                max_chunks=max_context_chunks or top_k,
                max_tokens=max_context_tokens
            )
        
        # Prepare result
        result = {
            'query': query,
            'retrieved_chunks': retrieved,
            'timestamp': datetime.now().isoformat(),
        }
        
        if answer_result:
            result.update(answer_result)
        
        if self.debug:
            result['debug_info'] = {
                'query_time_seconds': time.time() - start_time,
                'embedding_model': self.config.embedding_model,
                'top_k': top_k,
                'rerank_enabled': rerank,
                'num_retrieved': len(retrieved),
            }
        
        return result
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for query text."""
        try:
            response = self.client.embeddings.create(
                model=self.config.embedding_model,
                input=text
            )
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            return embedding
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def _search_index(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search FAISS index for similar chunks."""
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        distances, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < 0 or idx >= len(self.metadata.get('chunks', [])):
                continue
            
            chunk_meta = self.metadata['chunks'][idx]
            paper_id = chunk_meta.get('paper_id')
            
            # Get paper and chunk details
            paper = self.state['papers'].get(paper_id)
            chunk = self._get_chunk_by_id(paper_id, chunk_meta.get('chunk_id'))
            
            if paper and chunk:
                results.append({
                    'chunk_id': chunk.chunk_id,
                    'paper_id': paper.id,
                    'paper_title': paper.title,
                    'paper_authors': paper.authors,
                    'paper_year': paper.year,
                    'section_label': chunk.section_label,
                    'page_start': chunk.page_start,
                    'page_end': chunk.page_end,
                    'text': chunk.text,
                    'distance': float(distance),
                    'similarity_score': 1.0 / (1.0 + float(distance)),
                    'tier1_topic': paper.tier1_topic_name,
                    'tier2_topic': paper.tier2_topic_name,
                })
        
        return results
    
    def _get_chunk_by_id(self, paper_id: str, chunk_id: str) -> Optional[PaperChunk]:
        """Get chunk by IDs."""
        chunks = self.state.get('chunks', {}).get(paper_id, [])
        for chunk in chunks:
            if chunk.chunk_id == chunk_id:
                return chunk
        return None
    
    def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rerank results based on relevance heuristics."""
        for result in results:
            # Base score from similarity
            score = result['similarity_score']
            
            # Boost for section type
            section = result.get('section_label', 'other').lower()
            if 'overview' in query.lower() or 'summary' in query.lower():
                if section == 'abstract':
                    score *= 1.3
                elif section == 'conclusion':
                    score *= 1.2
            elif 'method' in query.lower() or 'approach' in query.lower():
                if section == 'methods':
                    score *= 1.3
            elif 'result' in query.lower() or 'finding' in query.lower():
                if section == 'results':
                    score *= 1.3
            
            # Boost for title/author match (simple keyword matching)
            query_lower = query.lower()
            title = result.get('paper_title', '').lower()
            if any(word in title for word in query_lower.split() if len(word) > 3):
                score *= 1.15
            
            result['rerank_score'] = score
        
        # Sort by rerank score
        results.sort(key=lambda x: x.get('rerank_score', x['similarity_score']), reverse=True)
        return results
    
    def _generate_answer(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        max_chunks: int = 5,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate answer using GPT-5.1 via Responses API."""
        # Limit chunks
        chunks_to_use = retrieved_chunks[:max_chunks]
        
        # Create context
        context = self._create_context(chunks_to_use, max_tokens)
        
        # Create input with query and context
        input_text = f"""Question: {query}

Context from research papers:
{context}

Instructions:
- Answer the question based ONLY on the provided context.
- Cite specific papers by title and ID in your answer.
- If the context doesn't contain enough information to answer, say "I don't have enough information in the corpus to answer this question."
- Be specific and include relevant details from the papers.
- Format citations as [Title (ID)].
"""
        
        # System instructions for Responses API
        instructions = """You are a research assistant that helps users explore an academic corpus. 
You provide accurate answers based on the research papers in the corpus.
You always cite your sources using paper titles and IDs.
You never make up information not present in the provided context."""
        
        try:
            # Use Responses API (not Chat Completions)
            response = self.client.responses.create(
                model=self.config.summary_model,  # Use configured model
                instructions=instructions,
                input=input_text,
            )
            
            answer_text = response.output if hasattr(response, 'output') else str(response)
            
            # Extract used papers
            used_papers = self._extract_used_papers(chunks_to_use)
            
            return {
                'answer_text': answer_text,
                'used_papers': used_papers,
                'used_chunks': [
                    {
                        'chunk_id': c['chunk_id'],
                        'paper_id': c['paper_id'],
                        'paper_title': c['paper_title'],
                        'section': c['section_label'],
                        'score': c.get('rerank_score', c['similarity_score'])
                    }
                    for c in chunks_to_use
                ],
                'context_chunk_count': len(chunks_to_use),
            }
        
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return {
                'answer_text': f"Error generating answer: {str(e)}",
                'used_papers': [],
                'used_chunks': [],
                'error': str(e),
            }
    
    def _create_context(
        self,
        chunks: List[Dict[str, Any]],
        max_tokens: Optional[int] = None
    ) -> str:
        """Create context string from chunks."""
        context_parts = []
        total_chars = 0
        max_chars = (max_tokens * 4) if max_tokens else 8000  # ~4 chars per token estimate
        
        for i, chunk in enumerate(chunks, 1):
            chunk_text = f"""
--- Paper {i}: {chunk['paper_title']} (ID: {chunk['paper_id']}) ---
Section: {chunk['section_label']}
Pages: {chunk['page_start']}-{chunk['page_end']}
{chunk['tier1_topic'] or 'Unknown Topic'}

{chunk['text']}
"""
            
            if max_tokens and (total_chars + len(chunk_text)) > max_chars:
                break
            
            context_parts.append(chunk_text)
            total_chars += len(chunk_text)
        
        return "\n".join(context_parts)
    
    def _extract_used_papers(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract unique papers from chunks."""
        papers_dict = {}
        
        for chunk in chunks:
            paper_id = chunk['paper_id']
            if paper_id not in papers_dict:
                papers_dict[paper_id] = {
                    'paper_id': paper_id,
                    'title': chunk['paper_title'],
                    'authors': chunk.get('paper_authors', []),
                    'year': chunk.get('paper_year'),
                    'tier1_topic': chunk.get('tier1_topic'),
                    'tier2_topic': chunk.get('tier2_topic'),
                }
        
        return list(papers_dict.values())


def rag_query(
    query: str,
    state: GraphState,
    config: Optional[RunConfig] = None,
    top_k: int = 5,
    generate_answer: bool = True,
    openai_client: Optional[OpenAI] = None,
) -> Dict[str, Any]:
    """
    Convenience function for RAG query.
    
    Args:
        query: Natural language query
        state: GraphState with corpus data
        config: RunConfig (optional, uses state.config if None)
        top_k: Number of chunks to retrieve
        generate_answer: Whether to generate answer
        openai_client: OpenAI client (optional)
    
    Returns:
        Query results dictionary
    """
    engine = RAGQueryEngine(state=state, openai_client=openai_client)
    return engine.query(query=query, top_k=top_k, generate_answer=generate_answer)


def generate_query_embedding(
    query: str,
    config: RunConfig,
    openai_client: Optional[OpenAI] = None
) -> np.ndarray:
    """
    Generate embedding for a query string.
    
    Args:
        query: Query text
        config: RunConfig with embedding model
        openai_client: OpenAI client (optional)
    
    Returns:
        Embedding vector as numpy array
    """
    client = openai_client or OpenAI()
    
    response = client.embeddings.create(
        model=config.embedding_model,
        input=query
    )
    
    return np.array(response.data[0].embedding, dtype=np.float32)


def search_faiss_index(
    query_embedding: np.ndarray,
    index_path: str,
    metadata_path: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Search FAISS index with query embedding.
    
    Args:
        query_embedding: Query embedding vector
        index_path: Path to FAISS index file
        metadata_path: Path to metadata JSON file
        top_k: Number of results to return
    
    Returns:
        List of search results with metadata
    """
    if not FAISS_AVAILABLE:
        raise ImportError("FAISS not available")
    
    index = faiss.read_index(index_path)
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    if len(query_embedding.shape) == 1:
        query_embedding = query_embedding.reshape(1, -1)
    
    distances, indices = index.search(query_embedding, top_k)
    
    results = []
    for idx, distance in zip(indices[0], distances[0]):
        if 0 <= idx < len(metadata.get('chunks', [])):
            chunk_meta = metadata['chunks'][idx]
            results.append({
                'chunk_id': chunk_meta.get('chunk_id'),
                'paper_id': chunk_meta.get('paper_id'),
                'distance': float(distance),
                'similarity_score': 1.0 / (1.0 + float(distance)),
            })
    
    return results


def retrieve_top_k_chunks(
    query: str,
    state: GraphState,
    top_k: int = 5,
    openai_client: Optional[OpenAI] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve top-k chunks for a query (without answer generation).
    
    Args:
        query: Natural language query
        state: GraphState
        top_k: Number of chunks
        openai_client: OpenAI client (optional)
    
    Returns:
        List of retrieved chunks with metadata
    """
    engine = RAGQueryEngine(state=state, openai_client=openai_client)
    result = engine.query(query=query, top_k=top_k, generate_answer=False)
    return result['retrieved_chunks']


# =============================================================================
# Step 15.2: Implement Reranking
# =============================================================================

def rerank_chunks(
    query: str,
    chunks: List[Dict[str, Any]],
    boost_sections: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """
    Rerank retrieved chunks based on relevance heuristics.
    
    Args:
        query: Original query
        chunks: Retrieved chunks with similarity scores
        boost_sections: Dict mapping section labels to boost multipliers
    
    Returns:
        Reranked chunks with updated scores
    """
    if boost_sections is None:
        boost_sections = {
            'abstract': 1.2,
            'conclusion': 1.15,
            'introduction': 1.1,
        }
    
    for chunk in chunks:
        score = chunk.get('similarity_score', 0.0)
        
        # Apply section boost
        section = chunk.get('section_label', '').lower()
        if section in boost_sections:
            score *= boost_sections[section]
        
        chunk['rerank_score'] = score
    
    chunks.sort(key=lambda x: x.get('rerank_score', 0.0), reverse=True)
    return chunks


def calculate_relevance_score(
    query: str,
    chunk: Dict[str, Any],
    base_score: float
) -> float:
    """
    Calculate relevance score for a chunk.
    
    Args:
        query: Query text
        chunk: Chunk metadata
        base_score: Base similarity score
    
    Returns:
        Adjusted relevance score
    """
    score = base_score
    
    # Keyword matching boost
    query_lower = query.lower()
    chunk_text = chunk.get('text', '').lower()
    
    # Count query word matches in chunk
    query_words = set(query_lower.split())
    matches = sum(1 for word in query_words if word in chunk_text and len(word) > 3)
    
    if matches > 0:
        score *= (1.0 + 0.05 * matches)
    
    return score


def boost_section_scores(
    chunks: List[Dict[str, Any]],
    query_type: Literal['overview', 'methods', 'results', 'general'] = 'general'
) -> List[Dict[str, Any]]:
    """
    Boost chunk scores based on query type and section.
    
    Args:
        chunks: List of chunks
        query_type: Type of query to optimize for
    
    Returns:
        Chunks with boosted scores
    """
    boost_map = {
        'overview': {'abstract': 1.4, 'conclusion': 1.3, 'introduction': 1.2},
        'methods': {'methods': 1.4, 'introduction': 1.1},
        'results': {'results': 1.4, 'conclusion': 1.2, 'abstract': 1.1},
        'general': {'abstract': 1.2, 'introduction': 1.1},
    }
    
    boosts = boost_map.get(query_type, {})
    
    for chunk in chunks:
        section = chunk.get('section_label', '').lower()
        if section in boosts:
            current_score = chunk.get('similarity_score', 0.0)
            chunk['boosted_score'] = current_score * boosts[section]
        else:
            chunk['boosted_score'] = chunk.get('similarity_score', 0.0)
    
    chunks.sort(key=lambda x: x.get('boosted_score', 0.0), reverse=True)
    return chunks


# =============================================================================
# Step 15.3: Create Answer Generation
# =============================================================================

def generate_answer(
    query: str,
    chunks: List[Dict[str, Any]],
    state: GraphState,
    openai_client: Optional[OpenAI] = None,
    max_chunks: int = 5,
    max_tokens: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate answer from retrieved chunks using Responses API.
    
    Args:
        query: User query
        chunks: Retrieved chunks
        state: GraphState
        openai_client: OpenAI client (optional)
        max_chunks: Maximum chunks in context
        max_tokens: Maximum context tokens
    
    Returns:
        Answer dictionary with text, citations, and metadata
    """
    client = openai_client or OpenAI()
    config = state.get('config')
    
    # Limit chunks
    chunks_to_use = chunks[:max_chunks]
    
    # Create context
    context = create_context_from_chunks(chunks_to_use, max_tokens)
    
    # Create input
    input_text = f"""Question: {query}

Context:
{context}

Provide a comprehensive answer based only on the context above. Cite papers by title and ID."""
    
    instructions = """You are a research assistant. Answer questions based on provided research papers.
Always cite sources. Never make up information."""
    
    try:
        response = client.responses.create(
            model=config.summary_model,
            instructions=instructions,
            input=input_text,
        )
        
        answer_text = response.output if hasattr(response, 'output') else str(response)
        
        return {
            'answer_text': answer_text,
            'citations': format_citations(chunks_to_use),
            'num_chunks_used': len(chunks_to_use),
        }
    
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return {
            'answer_text': f"Error: {str(e)}",
            'citations': [],
            'error': str(e),
        }


def create_context_from_chunks(
    chunks: List[Dict[str, Any]],
    max_tokens: Optional[int] = None
) -> str:
    """
    Create formatted context string from chunks.
    
    Args:
        chunks: List of chunk dictionaries
        max_tokens: Maximum tokens (optional)
    
    Returns:
        Formatted context string
    """
    parts = []
    max_chars = (max_tokens * 4) if max_tokens else 10000
    total_chars = 0
    
    for i, chunk in enumerate(chunks, 1):
        part = f"""[{i}] {chunk.get('paper_title', 'Unknown')} (ID: {chunk.get('paper_id', 'N/A')})
Section: {chunk.get('section_label', 'unknown')}
{chunk.get('text', '')}
---
"""
        
        if max_tokens and (total_chars + len(part)) > max_chars:
            break
        
        parts.append(part)
        total_chars += len(part)
    
    return "\n".join(parts)


def format_citations(chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Format citations from chunks.
    
    Args:
        chunks: List of chunks
    
    Returns:
        List of citation dictionaries
    """
    citations = []
    seen_papers = set()
    
    for chunk in chunks:
        paper_id = chunk.get('paper_id')
        if paper_id and paper_id not in seen_papers:
            citations.append({
                'paper_id': paper_id,
                'title': chunk.get('paper_title', 'Unknown'),
                'authors': ', '.join(chunk.get('paper_authors', [])),
                'year': chunk.get('paper_year'),
            })
            seen_papers.add(paper_id)
    
    return citations


# =============================================================================
# Step 15.4: Build Interactive Query Interface
# =============================================================================

def interactive_query(
    state: GraphState,
    openai_client: Optional[OpenAI] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Interactive query interface for notebook use.
    
    Prompts user for query and displays formatted results.
    
    Args:
        state: GraphState
        openai_client: OpenAI client (optional)
        top_k: Number of chunks to retrieve
    
    Returns:
        Query result dictionary
    """
    # Get user input
    query = input("Enter your query: ").strip()
    
    if not query:
        print("No query entered.")
        return {}
    
    print(f"\nSearching corpus for: '{query}'...\n")
    
    # Perform query
    result = rag_query(
        query=query,
        state=state,
        top_k=top_k,
        openai_client=openai_client
    )
    
    # Display results
    display_query_results(result)
    
    return result


def display_query_results(result: Dict[str, Any]) -> None:
    """
    Display query results in a formatted way.
    
    Args:
        result: Query result dictionary
    """
    print("=" * 80)
    print("QUERY RESULTS")
    print("=" * 80)
    
    print(f"\nQuery: {result.get('query', 'N/A')}")
    print(f"Timestamp: {result.get('timestamp', 'N/A')}")
    
    if 'answer_text' in result:
        print("\n" + "-" * 80)
        print("ANSWER:")
        print("-" * 80)
        print(result['answer_text'])
    
    if 'used_papers' in result and result['used_papers']:
        print("\n" + "-" * 80)
        print("SUPPORTING PAPERS:")
        print("-" * 80)
        for i, paper in enumerate(result['used_papers'], 1):
            print(f"\n{i}. {paper.get('title', 'Unknown')}")
            print(f"   ID: {paper.get('paper_id', 'N/A')}")
            authors = paper.get('authors', [])
            if authors:
                print(f"   Authors: {', '.join(authors[:3])}{' et al.' if len(authors) > 3 else ''}")
            if paper.get('year'):
                print(f"   Year: {paper['year']}")
            if paper.get('tier1_topic'):
                print(f"   Topic: {paper['tier1_topic']}")
    
    if 'retrieved_chunks' in result and result['retrieved_chunks']:
        print("\n" + "-" * 80)
        print(f"RETRIEVED CHUNKS ({len(result['retrieved_chunks'])}):")
        print("-" * 80)
        for i, chunk in enumerate(result['retrieved_chunks'][:5], 1):
            score = chunk.get('rerank_score', chunk.get('similarity_score', 0))
            print(f"\n{i}. Score: {score:.3f} | Section: {chunk.get('section_label', 'unknown')}")
            print(f"   {chunk.get('paper_title', 'Unknown')} (pages {chunk.get('page_start')}-{chunk.get('page_end')})")
            print(f"   {chunk.get('text', '')[:200]}...")
    
    print("\n" + "=" * 80)


def format_answer_display(
    answer_text: str,
    used_papers: List[Dict[str, Any]],
    used_chunks: List[Dict[str, Any]]
) -> str:
    """
    Format answer for display.
    
    Args:
        answer_text: Generated answer
        used_papers: Papers cited
        used_chunks: Chunks used
    
    Returns:
        Formatted display string
    """
    lines = [
        "=" * 80,
        "ANSWER:",
        "=" * 80,
        "",
        answer_text,
        "",
        "-" * 80,
        "SOURCES:",
        "-" * 80,
    ]
    
    for i, paper in enumerate(used_papers, 1):
        lines.append(f"{i}. {paper.get('title', 'Unknown')} (ID: {paper.get('paper_id')})")
    
    lines.append("")
    lines.append("=" * 80)
    
    return "\n".join(lines)


def get_supporting_papers(
    chunks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Extract unique supporting papers from chunks.
    
    Args:
        chunks: List of chunk dictionaries
    
    Returns:
        List of unique paper metadata
    """
    papers = {}
    
    for chunk in chunks:
        paper_id = chunk.get('paper_id')
        if paper_id and paper_id not in papers:
            papers[paper_id] = {
                'paper_id': paper_id,
                'title': chunk.get('paper_title'),
                'authors': chunk.get('paper_authors', []),
                'year': chunk.get('paper_year'),
                'tier1_topic': chunk.get('tier1_topic'),
            }
    
    return list(papers.values())


# =============================================================================
# Step 15.5: Add Query History
# =============================================================================

class QueryHistory:
    """Tracks query history for analysis and refinement."""
    
    def __init__(self):
        """Initialize query history."""
        self.queries: List[Dict[str, Any]] = []
    
    def add_query(
        self,
        query: str,
        result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a query to history.
        
        Args:
            query: Query text
            result: Query result
            metadata: Additional metadata
        """
        entry = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'num_results': len(result.get('retrieved_chunks', [])),
            'has_answer': 'answer_text' in result,
            'result_summary': {
                'num_chunks': len(result.get('retrieved_chunks', [])),
                'num_papers': len(result.get('used_papers', [])),
            }
        }
        
        if metadata:
            entry['metadata'] = metadata
        
        self.queries.append(entry)
    
    def get_recent(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get n most recent queries."""
        return self.queries[-n:]
    
    def search_history(self, keyword: str) -> List[Dict[str, Any]]:
        """Search history for queries containing keyword."""
        return [q for q in self.queries if keyword.lower() in q['query'].lower()]
    
    def export_to_json(self, path: str) -> None:
        """Export history to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.queries, f, indent=2)
    
    def load_from_json(self, path: str) -> None:
        """Load history from JSON file."""
        with open(path, 'r') as f:
            self.queries = json.load(f)


def track_query(
    query: str,
    result: Dict[str, Any],
    history: QueryHistory,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Track a query in history.
    
    Args:
        query: Query text
        result: Query result
        history: QueryHistory instance
        metadata: Additional metadata
    """
    history.add_query(query, result, metadata)


def get_query_history(history: QueryHistory, n: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent query history.
    
    Args:
        history: QueryHistory instance
        n: Number of recent queries
    
    Returns:
        List of recent queries
    """
    return history.get_recent(n)


def export_query_history(history: QueryHistory, output_path: str) -> str:
    """
    Export query history to file.
    
    Args:
        history: QueryHistory instance
        output_path: Output file path
    
    Returns:
        Path to exported file
    """
    history.export_to_json(output_path)
    return output_path


def refine_query(
    original_query: str,
    result: Dict[str, Any],
    refinement_type: Literal['expand', 'narrow', 'rephrase'] = 'expand'
) -> str:
    """
    Suggest query refinements based on results.
    
    Args:
        original_query: Original query
        result: Query result
        refinement_type: Type of refinement
    
    Returns:
        Refined query suggestion
    """
    if refinement_type == 'expand':
        # Add related topics from results
        topics = set()
        for paper in result.get('used_papers', []):
            if paper.get('tier1_topic'):
                topics.add(paper['tier1_topic'])
        
        if topics:
            topic_str = ', '.join(list(topics)[:2])
            return f"{original_query} in the context of {topic_str}"
    
    elif refinement_type == 'narrow':
        # Add section focus
        return f"{original_query} (focus on methods and results)"
    
    elif refinement_type == 'rephrase':
        # Add explicit question format
        if '?' not in original_query:
            return f"What are the key findings about {original_query}?"
    
    return original_query


# =============================================================================
# Utility Functions (Phase 22)
# =============================================================================

def search_by_title_substring(
    state: GraphState,
    substring: str,
    case_sensitive: bool = False
) -> List[PaperRecord]:
    """
    Search papers by title substring.
    
    Args:
        state: GraphState
        substring: Substring to search for
        case_sensitive: Whether search is case-sensitive
    
    Returns:
        List of matching papers
    """
    if not case_sensitive:
        substring = substring.lower()
    
    matches = []
    for paper in state.get('papers', {}).values():
        title = paper.title or ''
        if not case_sensitive:
            title = title.lower()
        
        if substring in title:
            matches.append(paper)
    
    return matches


def search_by_author(
    state: GraphState,
    author_name: str,
    case_sensitive: bool = False
) -> List[PaperRecord]:
    """
    Search papers by author name.
    
    Args:
        state: GraphState
        author_name: Author name to search for
        case_sensitive: Whether search is case-sensitive
    
    Returns:
        List of matching papers
    """
    if not case_sensitive:
        author_name = author_name.lower()
    
    matches = []
    for paper in state.get('papers', {}).values():
        authors = paper.authors or []
        
        for author in authors:
            author_check = author if case_sensitive else author.lower()
            if author_name in author_check:
                matches.append(paper)
                break
    
    return matches


def list_papers_in_topic(
    state: GraphState,
    topic_id: str,
    tier: Literal[1, 2, 3] = 1
) -> List[PaperRecord]:
    """
    List all papers in a specific topic.
    
    Args:
        state: GraphState
        topic_id: Topic ID
        tier: Topic tier (1, 2, or 3)
    
    Returns:
        List of papers in topic
    """
    matches = []
    
    for paper in state.get('papers', {}).values():
        if tier == 1 and paper.tier1_topic == topic_id:
            matches.append(paper)
        elif tier == 2 and paper.tier2_topic == topic_id:
            matches.append(paper)
        elif tier == 3 and paper.tier3_topic == topic_id:
            matches.append(paper)
    
    return matches


def get_corpus_statistics(state: GraphState) -> Dict[str, Any]:
    """
    Get statistics about the corpus.
    
    Args:
        state: GraphState
    
    Returns:
        Dictionary of statistics
    """
    papers = state.get('papers', {})
    chunks = state.get('chunks', {})
    hierarchy = state.get('topic_hierarchy')
    
    # Count papers by status
    status_counts = {}
    for paper in papers.values():
        status = paper.processing_status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Count papers by year
    year_counts = {}
    for paper in papers.values():
        if paper.year:
            year_counts[paper.year] = year_counts.get(paper.year, 0) + 1
    
    # Count chunks
    total_chunks = sum(len(c) for c in chunks.values())
    
    return {
        'total_papers': len(papers),
        'total_chunks': total_chunks,
        'status_distribution': status_counts,
        'year_distribution': year_counts,
        'taxonomy_stats': hierarchy.get_statistics() if hierarchy else None,
        'avg_chunks_per_paper': total_chunks / len(papers) if papers else 0,
    }
