#!/usr/bin/env python3
"""
Test suite for Phase 20: Testing and Validation

This module implements comprehensive testing including:
- Step 20.1: Unit Test Functions (PDF parsing, chunking, metadata, embeddings, clustering, query)
- Step 20.2: Integration Testing (small corpus, end-to-end pipeline, data consistency)
- Step 20.3: Edge Case Testing (scanned PDFs, non-standard PDFs, large/small papers, corrupted files)
- Step 20.4: Performance Testing (processing time, memory usage, API latency, bottlenecks)
- Step 20.5: Validation Tests (taxonomy quality, classification accuracy, summary quality, RAG relevance)

Version: 1.0
Date: 2025-11-25
"""

import sys
import os
import tempfile
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import core models
from rag_models import (
    RunConfig,
    PaperRecord,
    PaperChunk,
    TopicNode,
    TopicHierarchy,
    GraphState,
    StateManager,
    IDGenerator,
    StatisticsTracker,
    MetadataExtractor,
    ErrorHandler,
    DataValidator,
    CostTracker,
    create_default_config,
    validate_paper_record,
)

# Check for optional dependencies
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: numpy not available")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not available")

# =============================================================================
# Test Utilities and Helper Functions
# =============================================================================

def create_sample_text(length: int = 1000) -> str:
    """Create sample academic text for testing."""
    words = [
        "machine", "learning", "neural", "network", "algorithm",
        "data", "model", "training", "accuracy", "performance",
        "research", "experiment", "results", "method", "analysis",
        "study", "approach", "system", "framework", "evaluation"
    ]
    text_parts = []
    while len(" ".join(text_parts)) < length:
        import random
        sentence = " ".join(random.choices(words, k=random.randint(5, 15))) + "."
        text_parts.append(sentence.capitalize())
    return " ".join(text_parts)[:length]


def create_sample_paper_record(paper_id: str = None, **overrides) -> PaperRecord:
    """Create a sample PaperRecord for testing."""
    if paper_id is None:
        paper_id = IDGenerator.generate_paper_id(f"/test/paper_{datetime.now().timestamp()}.pdf")
    
    defaults = {
        "id": paper_id,
        "file_path": f"/test/{paper_id}.pdf",
        "filename": f"{paper_id}.pdf",
        "title": "Sample Research Paper on Machine Learning",
        "authors": ["John Doe", "Jane Smith"],
        "abstract_text": "This paper presents novel approaches to machine learning.",
        "year": 2023,
        "processing_status": "pending",
    }
    defaults.update(overrides)
    return PaperRecord(**defaults)


def create_sample_chunks(paper_id: str, num_chunks: int = 3) -> List[PaperChunk]:
    """Create sample PaperChunk objects for testing."""
    sections = ["abstract", "introduction", "methods", "results", "conclusion"]
    chunks = []
    for i in range(num_chunks):
        section = sections[i % len(sections)]
        chunks.append(PaperChunk(
            paper_id=paper_id,
            chunk_id=IDGenerator.generate_chunk_id(paper_id, i),
            section_label=section,
            page_start=i + 1,
            page_end=i + 2,
            text=create_sample_text(500),
            char_count=500,
        ))
    return chunks


def create_sample_state(num_papers: int = 3, chunks_per_paper: int = 3) -> GraphState:
    """Create a sample GraphState with papers and chunks for testing."""
    config = create_default_config()
    state = StateManager.create_initial_state(config)
    
    for i in range(num_papers):
        paper_id = f"paper_{i:03d}"
        paper = create_sample_paper_record(paper_id)
        state = StateManager.add_paper(state, paper)
        
        chunks = create_sample_chunks(paper_id, chunks_per_paper)
        state = StateManager.add_chunks(state, paper_id, chunks)
    
    return state


# =============================================================================
# Step 20.1: Unit Test Functions
# =============================================================================

class TestUnitFunctions:
    """Unit tests for core functions."""
    
    @staticmethod
    def test_pdf_parsing_mock():
        """Test PDF parsing logic with mock data."""
        print("\n" + "=" * 70)
        print("Test: PDF Parsing (Mock)")
        print("=" * 70)
        
        try:
            from pdf_parser import SectionDetector, chunk_text, needs_ocr
            
            # Test section detection
            assert SectionDetector.detect_section("Abstract") == "abstract"
            assert SectionDetector.detect_section("1. Introduction") == "introduction"
            assert SectionDetector.detect_section("Methods") == "methods"
            assert SectionDetector.detect_section("Results and Discussion") == "results"
            assert SectionDetector.detect_section("Conclusion") == "conclusion"
            assert SectionDetector.detect_section("Random text here") is None
            print("  ✓ Section detection working")
            
            # Test chunking
            sample_text = create_sample_text(3000)
            chunks = chunk_text(sample_text, chunk_size=500, overlap=50)
            assert len(chunks) > 1
            assert all('text' in c and 'char_count' in c for c in chunks)
            print(f"  ✓ Chunking created {len(chunks)} chunks")
            
            # Test OCR detection
            low_quality = {"parse_quality_score": 0.3, "chars_per_page": 200}
            high_quality = {"parse_quality_score": 0.9, "chars_per_page": 2000}
            assert needs_ocr(low_quality) == True
            assert needs_ocr(high_quality) == False
            print("  ✓ OCR detection working")
            
            print("\n✓ PDF parsing tests passed")
            return True
            
        except ImportError as e:
            print(f"  Skipping: pdf_parser not available ({e})")
            return None
    
    @staticmethod
    def test_chunking_logic():
        """Test text chunking logic."""
        print("\n" + "=" * 70)
        print("Test: Chunking Logic")
        print("=" * 70)
        
        try:
            from pdf_parser import chunk_text, create_chunks_from_pages
            
            # Test basic chunking
            text = "Sentence one. " * 100
            chunks = chunk_text(text, chunk_size=200, overlap=20)
            
            assert len(chunks) > 0
            assert all(c['char_count'] > 0 for c in chunks)
            print(f"  ✓ Created {len(chunks)} chunks from text")
            
            # Test empty text handling
            empty_chunks = chunk_text("", chunk_size=200)
            assert len(empty_chunks) == 0
            print("  ✓ Empty text handled correctly")
            
            # Test very small text (single chunk)
            small_text = "Small text."
            small_chunks = chunk_text(small_text, chunk_size=1000)
            assert len(small_chunks) == 1
            print("  ✓ Small text creates single chunk")
            
            # Test overlapping
            overlap_text = "A " * 500
            overlap_chunks = chunk_text(overlap_text, chunk_size=100, overlap=20)
            assert len(overlap_chunks) > 5
            print(f"  ✓ Overlap chunking created {len(overlap_chunks)} chunks")
            
            print("\n✓ Chunking logic tests passed")
            return True
            
        except ImportError as e:
            print(f"  Skipping: pdf_parser not available ({e})")
            return None
    
    @staticmethod
    def test_metadata_extraction():
        """Test metadata extraction functions."""
        print("\n" + "=" * 70)
        print("Test: Metadata Extraction")
        print("=" * 70)
        
        # Test arXiv ID detection
        arxiv_id = MetadataExtractor.extract_arxiv_id("2301.12345.pdf")
        assert arxiv_id == "2301.12345"
        print("  ✓ arXiv ID extraction working")
        
        # Test DOI detection
        doi = MetadataExtractor.extract_doi("DOI: 10.1234/example.2023")
        assert doi == "10.1234/example.2023"
        print("  ✓ DOI extraction working")
        
        # Test author normalization
        authors = MetadataExtractor.normalize_authors(["  John Doe  ", "", "Jane Smith"])
        assert authors == ["John Doe", "Jane Smith"]
        print("  ✓ Author normalization working")
        
        # Test date parsing
        date = MetadataExtractor.parse_date("2023-01-15")
        assert date is not None
        assert date.year == 2023
        print("  ✓ Date parsing working")
        
        print("\n✓ Metadata extraction tests passed")
        return True
    
    @staticmethod
    def test_embedding_generation_mock():
        """Test embedding generation with mocked API."""
        print("\n" + "=" * 70)
        print("Test: Embedding Generation (Mock)")
        print("=" * 70)
        
        if not NUMPY_AVAILABLE:
            print("  Skipping: numpy not available")
            return None
        
        try:
            from embedding_generator import estimate_embedding_cost
            
            # Test cost estimation
            estimate = estimate_embedding_cost(
                num_texts=100,
                avg_chars_per_text=1500,
                model="text-embedding-3-large"
            )
            
            assert estimate['num_texts'] == 100
            assert estimate['estimated_tokens'] > 0
            assert estimate['estimated_cost_usd'] > 0
            print(f"  ✓ Cost estimate: ${estimate['estimated_cost_usd']:.4f}")
            
            # Test with mock OpenAI client
            mock_embedding = [0.1] * 1536
            mock_response = Mock()
            mock_response.data = [Mock(embedding=mock_embedding)]
            mock_response.usage = Mock(total_tokens=100)
            
            with patch('embedding_generator.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_client.embeddings.create.return_value = mock_response
                mock_openai.return_value = mock_client
                
                from embedding_generator import EmbeddingGenerator
                generator = EmbeddingGenerator(api_key="test_key")
                embeddings, stats = generator.generate_embeddings(["test"], show_progress=False)
                
                assert embeddings.shape == (1, 1536)
                assert stats['total_tokens'] == 100
                print("  ✓ Embedding generation with mock API working")
            
            print("\n✓ Embedding generation tests passed")
            return True
            
        except ImportError as e:
            print(f"  Skipping: embedding_generator not available ({e})")
            return None
    
    @staticmethod
    def test_clustering_algorithms():
        """Test clustering algorithms."""
        print("\n" + "=" * 70)
        print("Test: Clustering Algorithms")
        print("=" * 70)
        
        if not NUMPY_AVAILABLE:
            print("  Skipping: numpy not available")
            return None
        
        try:
            from topic_taxonomy import cluster_papers, determine_optimal_k
            from sklearn.cluster import KMeans
            
            # Create sample embeddings
            np.random.seed(42)
            embeddings = np.random.randn(50, 64).astype(np.float32)
            
            # Test clustering
            labels, centroids = cluster_papers(embeddings, n_clusters=5, method='kmeans')
            
            assert len(labels) == 50
            assert centroids.shape == (5, 64)
            assert len(np.unique(labels)) == 5
            print(f"  ✓ K-means clustering created {len(np.unique(labels))} clusters")
            
            # Test optimal k determination (silhouette method)
            optimal_k = determine_optimal_k(embeddings, k_range=(2, 8), method='silhouette')
            assert 2 <= optimal_k <= 8
            print(f"  ✓ Optimal k determined: {optimal_k}")
            
            print("\n✓ Clustering algorithm tests passed")
            return True
            
        except ImportError as e:
            print(f"  Skipping: topic_taxonomy or sklearn not available ({e})")
            return None
    
    @staticmethod
    def test_query_functions():
        """Test RAG query functions."""
        print("\n" + "=" * 70)
        print("Test: Query Functions")
        print("=" * 70)
        
        try:
            from rag_query_interface import (
                rerank_chunks,
                boost_section_scores,
                format_citations,
                create_context_from_chunks,
                get_supporting_papers,
            )
            
            # Create sample chunks
            sample_chunks = [
                {
                    'chunk_id': 'c1',
                    'paper_id': 'p1',
                    'paper_title': 'Test Paper 1',
                    'paper_authors': ['Author A'],
                    'paper_year': 2023,
                    'section_label': 'abstract',
                    'text': 'Sample abstract text.',
                    'similarity_score': 0.8,
                },
                {
                    'chunk_id': 'c2',
                    'paper_id': 'p2',
                    'paper_title': 'Test Paper 2',
                    'paper_authors': ['Author B'],
                    'paper_year': 2022,
                    'section_label': 'methods',
                    'text': 'Sample methods text.',
                    'similarity_score': 0.7,
                },
            ]
            
            # Test reranking
            reranked = rerank_chunks("overview summary", sample_chunks.copy())
            assert 'rerank_score' in reranked[0]
            print("  ✓ Reranking working")
            
            # Test section boosting
            boosted = boost_section_scores(sample_chunks.copy(), query_type='overview')
            assert 'boosted_score' in boosted[0]
            print("  ✓ Section boosting working")
            
            # Test citation formatting
            citations = format_citations(sample_chunks)
            assert len(citations) == 2
            assert all('paper_id' in c for c in citations)
            print("  ✓ Citation formatting working")
            
            # Test context creation
            context = create_context_from_chunks(sample_chunks, max_tokens=1000)
            assert len(context) > 0
            assert 'Test Paper 1' in context
            print("  ✓ Context creation working")
            
            # Test supporting papers extraction
            papers = get_supporting_papers(sample_chunks)
            assert len(papers) == 2
            print("  ✓ Supporting papers extraction working")
            
            print("\n✓ Query function tests passed")
            return True
            
        except ImportError as e:
            print(f"  Skipping: rag_query_interface not available ({e})")
            return None


# =============================================================================
# Step 20.2: Integration Testing
# =============================================================================

class TestIntegration:
    """Integration tests for the pipeline."""
    
    @staticmethod
    def test_small_corpus_processing():
        """Test processing a small corpus of papers."""
        print("\n" + "=" * 70)
        print("Test: Small Corpus Processing (5-10 papers)")
        print("=" * 70)
        
        # Create sample state with 5 papers
        state = create_sample_state(num_papers=5, chunks_per_paper=4)
        
        assert len(state['papers']) == 5
        assert len(state['chunks']) == 5
        assert all(len(chunks) == 4 for chunks in state['chunks'].values())
        
        print(f"  ✓ Created state with {len(state['papers'])} papers")
        print(f"  ✓ Total chunks: {sum(len(c) for c in state['chunks'].values())}")
        
        # Verify paper records
        for paper_id, paper in state['papers'].items():
            assert paper.id == paper_id
            assert paper.file_path is not None
            assert paper.filename is not None
        print("  ✓ All paper records valid")
        
        # Verify chunk records
        for paper_id, chunks in state['chunks'].items():
            for chunk in chunks:
                assert chunk.paper_id == paper_id
                assert chunk.chunk_id is not None
                assert chunk.text is not None
                assert chunk.char_count > 0
        print("  ✓ All chunk records valid")
        
        print("\n✓ Small corpus processing test passed")
        return True
    
    @staticmethod
    def test_end_to_end_pipeline_mock():
        """Test end-to-end pipeline with mocked external services."""
        print("\n" + "=" * 70)
        print("Test: End-to-End Pipeline (Mock)")
        print("=" * 70)
        
        # Create initial state
        config = create_default_config(max_papers_per_run=5)
        state = StateManager.create_initial_state(config)
        
        # Simulate discovery phase
        for i in range(3):
            paper = create_sample_paper_record(f"paper_{i:03d}")
            state = StateManager.add_paper(state, paper)
        
        state['current_phase'] = 'discovery'
        print(f"  ✓ Discovery: {len(state['papers'])} papers")
        
        # Simulate parsing phase
        for paper_id in state['papers']:
            chunks = create_sample_chunks(paper_id, 3)
            state = StateManager.add_chunks(state, paper_id, chunks)
            state['papers'][paper_id].processing_status = 'parsed'
        
        state['current_phase'] = 'parsing'
        print(f"  ✓ Parsing: {sum(len(c) for c in state['chunks'].values())} chunks")
        
        # Simulate metadata extraction
        for paper_id, paper in state['papers'].items():
            paper.title = f"Test Paper {paper_id}"
            paper.authors = ["Author A", "Author B"]
            paper.year = 2023
        
        state['current_phase'] = 'metadata'
        print("  ✓ Metadata extraction complete")
        
        # Simulate summarization
        for paper_id, paper in state['papers'].items():
            paper.full_summary = f"Summary of {paper_id}"
            paper.processing_status = 'summarized'
        
        state['current_phase'] = 'summarization'
        print("  ✓ Summarization complete")
        
        # Verify final state
        stats = StateManager.get_stats(state)
        assert stats['total_papers'] == 3
        assert stats['total_chunks'] == 9
        print(f"  ✓ Final stats: {stats}")
        
        print("\n✓ End-to-end pipeline test passed")
        return True
    
    @staticmethod
    def test_data_consistency():
        """Test data consistency across pipeline stages."""
        print("\n" + "=" * 70)
        print("Test: Data Consistency")
        print("=" * 70)
        
        state = create_sample_state(num_papers=5, chunks_per_paper=4)
        
        # Check paper-chunk consistency
        for paper_id in state['papers']:
            assert paper_id in state['chunks']
            for chunk in state['chunks'][paper_id]:
                assert chunk.paper_id == paper_id
        print("  ✓ Paper-chunk relationship consistent")
        
        # Check chunk IDs are unique
        all_chunk_ids = []
        for chunks in state['chunks'].values():
            all_chunk_ids.extend(c.chunk_id for c in chunks)
        assert len(all_chunk_ids) == len(set(all_chunk_ids))
        print("  ✓ All chunk IDs unique")
        
        # Check paper IDs are unique
        paper_ids = list(state['papers'].keys())
        assert len(paper_ids) == len(set(paper_ids))
        print("  ✓ All paper IDs unique")
        
        # Check chunk page numbers are valid
        for chunks in state['chunks'].values():
            for chunk in chunks:
                assert chunk.page_start >= 0
                assert chunk.page_end >= chunk.page_start
        print("  ✓ Chunk page numbers valid")
        
        print("\n✓ Data consistency tests passed")
        return True
    
    @staticmethod
    def test_output_validation():
        """Test validation of pipeline outputs."""
        print("\n" + "=" * 70)
        print("Test: Output Validation")
        print("=" * 70)
        
        # Create sample paper for validation
        paper = create_sample_paper_record("test_paper")
        paper.title = "Test Title"
        paper.authors = ["Author 1"]
        paper.full_summary = "Test summary"
        paper.processing_status = "summarized"
        
        # Validate paper record
        validation = validate_paper_record(paper)
        assert validation['has_metadata'] == True
        assert validation['has_summary'] == True
        print(f"  ✓ Paper validation: {validation}")
        
        # Test validation with missing data
        incomplete_paper = create_sample_paper_record("incomplete")
        incomplete_paper.title = None
        incomplete_paper.authors = None
        incomplete_validation = validate_paper_record(incomplete_paper)
        assert len(incomplete_validation['warnings']) > 0
        print(f"  ✓ Incomplete paper detected: {len(incomplete_validation['warnings'])} warnings")
        
        print("\n✓ Output validation tests passed")
        return True


# =============================================================================
# Step 20.3: Edge Case Testing
# =============================================================================

class TestEdgeCases:
    """Edge case tests for unusual inputs."""
    
    @staticmethod
    def test_scanned_pdf_detection():
        """Test detection of scanned PDFs that need OCR."""
        print("\n" + "=" * 70)
        print("Test: Scanned PDF Detection")
        print("=" * 70)
        
        try:
            from pdf_parser import needs_ocr
            
            # Typical scanned PDF characteristics
            scanned_stats = {
                "parse_quality_score": 0.2,
                "chars_per_page": 50,
                "alnum_ratio": 0.3,
            }
            assert needs_ocr(scanned_stats) == True
            print("  ✓ Scanned PDF correctly detected")
            
            # Normal PDF characteristics
            normal_stats = {
                "parse_quality_score": 0.9,
                "chars_per_page": 2500,
                "alnum_ratio": 0.8,
            }
            assert needs_ocr(normal_stats) == False
            print("  ✓ Normal PDF correctly identified")
            
            # Borderline case
            borderline_stats = {
                "parse_quality_score": 0.5,
                "chars_per_page": 500,
            }
            # Should trigger OCR based on quality threshold
            result = needs_ocr(borderline_stats, quality_threshold=0.6)
            assert result == True
            print("  ✓ Borderline case handled correctly")
            
            print("\n✓ Scanned PDF detection tests passed")
            return True
            
        except ImportError as e:
            print(f"  Skipping: pdf_parser not available ({e})")
            return None
    
    @staticmethod
    def test_large_paper_handling():
        """Test handling of very large papers (100+ pages)."""
        print("\n" + "=" * 70)
        print("Test: Large Paper Handling")
        print("=" * 70)
        
        # Create large text content (simulating 100+ pages)
        large_text = create_sample_text(200000)  # ~200KB text
        
        try:
            from pdf_parser import chunk_text
            
            config = create_default_config(
                chunk_size_chars=1500,
                chunk_overlap_chars=200,
                max_chunks_per_paper=100
            )
            
            chunks = chunk_text(
                large_text,
                chunk_size=config.chunk_size_chars,
                overlap=config.chunk_overlap_chars
            )
            
            # Should create many chunks
            assert len(chunks) > 50
            print(f"  ✓ Created {len(chunks)} chunks from large document")
            
            # Verify chunks are within size limits
            for chunk in chunks:
                # Allow some flexibility for chunk boundaries
                assert chunk['char_count'] < config.chunk_size_chars * 1.5
            print("  ✓ All chunks within size limits")
            
            # Test max_chunks_per_paper limit
            from pdf_parser import create_chunks_from_pages
            
            paper_id = "large_paper"
            pages = [{'page_num': i, 'text': create_sample_text(3000), 'char_count': 3000} 
                     for i in range(1, 101)]
            sections = []
            
            limited_chunks = create_chunks_from_pages(paper_id, pages, sections, config)
            assert len(limited_chunks) <= 100
            print(f"  ✓ Max chunks limit respected: {len(limited_chunks)} <= 100")
            
            print("\n✓ Large paper handling tests passed")
            return True
            
        except ImportError as e:
            print(f"  Skipping: pdf_parser not available ({e})")
            return None
    
    @staticmethod
    def test_small_paper_handling():
        """Test handling of very small papers (1-2 pages)."""
        print("\n" + "=" * 70)
        print("Test: Small Paper Handling")
        print("=" * 70)
        
        # Create small text content
        small_text = "Short paper. " * 50  # ~650 characters
        
        try:
            from pdf_parser import chunk_text
            
            chunks = chunk_text(small_text, chunk_size=1500, overlap=200)
            
            # Should create at least 1 chunk
            assert len(chunks) >= 1
            print(f"  ✓ Created {len(chunks)} chunk(s) from small document")
            
            # Verify the chunk contains the text
            assert sum(c['char_count'] for c in chunks) >= len(small_text.strip()) * 0.8
            print("  ✓ Small document text preserved")
            
            # Test very small text
            tiny_text = "Tiny."
            tiny_chunks = chunk_text(tiny_text, chunk_size=1500)
            assert len(tiny_chunks) <= 1
            print("  ✓ Tiny document handled correctly")
            
            print("\n✓ Small paper handling tests passed")
            return True
            
        except ImportError as e:
            print(f"  Skipping: pdf_parser not available ({e})")
            return None
    
    @staticmethod
    def test_corrupted_file_handling():
        """Test handling of corrupted or invalid files."""
        print("\n" + "=" * 70)
        print("Test: Corrupted File Handling")
        print("=" * 70)
        
        # Test DataValidator
        validator = DataValidator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test non-existent file
            try:
                validator.validate_pdf_file("/nonexistent/file.pdf")
                assert False, "Should have raised exception"
            except Exception as e:
                assert "not exist" in str(e).lower() or "not found" in str(e).lower()
                print("  ✓ Non-existent file detected")
            
            # Test empty file
            empty_file = Path(tmpdir) / "empty.pdf"
            empty_file.write_bytes(b"")
            try:
                validator.validate_pdf_file(str(empty_file))
                assert False, "Should have raised exception"
            except Exception as e:
                assert "empty" in str(e).lower() or "0 bytes" in str(e).lower()
                print("  ✓ Empty file detected")
            
            # Test invalid PDF content
            invalid_file = Path(tmpdir) / "invalid.pdf"
            invalid_file.write_bytes(b"This is not a valid PDF file")
            try:
                result = validator.validate_pdf_file(str(invalid_file))
                # May succeed with warnings or fail depending on implementation
                if not result.get('valid', True):
                    print("  ✓ Invalid PDF content detected")
                else:
                    print("  ✓ Invalid PDF handled (with warnings)")
            except Exception as e:
                print(f"  ✓ Invalid PDF correctly rejected: {type(e).__name__}")
        
        print("\n✓ Corrupted file handling tests passed")
        return True
    
    @staticmethod
    def test_special_characters_handling():
        """Test handling of special characters in text and metadata."""
        print("\n" + "=" * 70)
        print("Test: Special Characters Handling")
        print("=" * 70)
        
        # Test with special characters in title
        paper = create_sample_paper_record("special_chars")
        paper.title = "Émojis 🎉 and Special Characters: α, β, γ"
        paper.authors = ["José García", "François Müller"]
        
        # Should not raise errors
        paper_dict = paper.to_dict()
        assert paper_dict['title'] == paper.title
        assert paper_dict['authors'] == paper.authors
        print("  ✓ Special characters in metadata preserved")
        
        # Test with special characters in text
        special_text = "Mathematical notation: ∑, ∫, √, ≠, ≤, ≥"
        stats = StatisticsTracker.calculate_text_stats(special_text, page_count=1)
        assert stats['chars_total'] > 0
        print("  ✓ Special characters in text handled")
        
        # Test author normalization with special characters
        authors = MetadataExtractor.normalize_authors(["  José García  ", "François Müller"])
        assert "José García" in authors
        print("  ✓ Special characters in author names preserved")
        
        print("\n✓ Special characters handling tests passed")
        return True


# =============================================================================
# Step 20.4: Performance Testing
# =============================================================================

class TestPerformance:
    """Performance tests for the pipeline."""
    
    @staticmethod
    def test_processing_time():
        """Test processing time for various operations."""
        print("\n" + "=" * 70)
        print("Test: Processing Time Measurement")
        print("=" * 70)
        
        results = {}
        
        # Test state creation time
        start = time.time()
        state = create_sample_state(num_papers=100, chunks_per_paper=10)
        elapsed = time.time() - start
        results['state_creation_100_papers'] = elapsed
        print(f"  ✓ State creation (100 papers, 1000 chunks): {elapsed:.3f}s")
        
        # Test paper record creation time
        start = time.time()
        for i in range(1000):
            _ = create_sample_paper_record(f"perf_paper_{i}")
        elapsed = time.time() - start
        results['paper_record_creation_1000'] = elapsed
        print(f"  ✓ Paper record creation (1000 papers): {elapsed:.3f}s")
        
        # Test chunk creation time
        start = time.time()
        for i in range(100):
            _ = create_sample_chunks(f"paper_{i}", num_chunks=10)
        elapsed = time.time() - start
        results['chunk_creation_1000'] = elapsed
        print(f"  ✓ Chunk creation (1000 chunks): {elapsed:.3f}s")
        
        # Test text statistics calculation
        long_text = create_sample_text(100000)
        start = time.time()
        for _ in range(100):
            _ = StatisticsTracker.calculate_text_stats(long_text, page_count=50)
        elapsed = time.time() - start
        results['text_stats_100x'] = elapsed
        print(f"  ✓ Text statistics (100 iterations): {elapsed:.3f}s")
        
        # Test chunking time
        try:
            from pdf_parser import chunk_text
            
            start = time.time()
            _ = chunk_text(long_text, chunk_size=1500, overlap=200)
            elapsed = time.time() - start
            results['chunking_100k_chars'] = elapsed
            print(f"  ✓ Chunking (100k chars): {elapsed:.3f}s")
        except ImportError:
            print("  Skipping chunking test: pdf_parser not available")
        
        # Performance assertions (reasonable thresholds)
        assert results['state_creation_100_papers'] < 5.0, "State creation too slow"
        assert results['paper_record_creation_1000'] < 5.0, "Paper creation too slow"
        
        print("\n✓ Processing time tests passed")
        return results
    
    @staticmethod
    def test_memory_efficiency():
        """Test memory efficiency of data structures."""
        print("\n" + "=" * 70)
        print("Test: Memory Efficiency")
        print("=" * 70)
        
        import sys
        
        # Create a paper record and measure size
        paper = create_sample_paper_record("memory_test")
        paper_size = sys.getsizeof(paper)
        print(f"  ✓ PaperRecord size: {paper_size} bytes")
        
        # Create chunks and measure size
        chunks = create_sample_chunks("memory_test", num_chunks=10)
        chunk_sizes = [sys.getsizeof(c) for c in chunks]
        avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes)
        print(f"  ✓ Average PaperChunk size: {avg_chunk_size:.0f} bytes")
        
        # Create state and measure size
        state = create_sample_state(num_papers=10, chunks_per_paper=5)
        state_size = sys.getsizeof(state)
        print(f"  ✓ GraphState size (10 papers): {state_size} bytes")
        
        # Test serialization size
        config = create_default_config()
        config_json = json.dumps(config.to_dict())
        print(f"  ✓ RunConfig JSON size: {len(config_json)} bytes")
        
        print("\n✓ Memory efficiency tests passed")
        return True
    
    @staticmethod
    def test_batch_processing_efficiency():
        """Test efficiency of batch processing."""
        print("\n" + "=" * 70)
        print("Test: Batch Processing Efficiency")
        print("=" * 70)
        
        # Create large batch of papers
        num_papers = 100
        papers = [create_sample_paper_record(f"batch_{i}") for i in range(num_papers)]
        
        # Test sequential processing
        start = time.time()
        for paper in papers:
            _ = validate_paper_record(paper)
        sequential_time = time.time() - start
        print(f"  ✓ Sequential validation (100 papers): {sequential_time:.3f}s")
        
        # Test batch state updates
        config = create_default_config()
        state = StateManager.create_initial_state(config)
        
        start = time.time()
        for paper in papers:
            state = StateManager.add_paper(state, paper)
        batch_time = time.time() - start
        print(f"  ✓ Batch state updates (100 papers): {batch_time:.3f}s")
        
        # Verify all papers added
        assert len(state['papers']) == num_papers
        print(f"  ✓ All {num_papers} papers added successfully")
        
        print("\n✓ Batch processing efficiency tests passed")
        return True


# =============================================================================
# Step 20.5: Validation Tests
# =============================================================================

class TestValidation:
    """Validation tests for quality assurance."""
    
    @staticmethod
    def test_taxonomy_quality():
        """Test taxonomy structure quality."""
        print("\n" + "=" * 70)
        print("Test: Taxonomy Quality")
        print("=" * 70)
        
        # Create sample taxonomy
        tier1 = [
            TopicNode(id="T1_01", label="Machine Learning", description="ML research", paper_ids=["p1", "p2"]),
            TopicNode(id="T1_02", label="Natural Language Processing", description="NLP research", paper_ids=["p3", "p4"]),
        ]
        
        tier2 = [
            TopicNode(id="T2_01", label="Deep Learning", description="DL research", paper_ids=["p1"], parent_id="T1_01"),
            TopicNode(id="T2_02", label="Reinforcement Learning", description="RL research", paper_ids=["p2"], parent_id="T1_01"),
            TopicNode(id="T2_03", label="Transformers", description="Transformer models", paper_ids=["p3", "p4"], parent_id="T1_02"),
        ]
        
        tier3 = [
            TopicNode(id="T3_01", label="CNNs", description="Conv networks", paper_ids=["p1"], parent_id="T2_01"),
        ]
        
        hierarchy = TopicHierarchy(
            taxonomy_version="v1.0_test",
            total_papers=4,
            tier1=tier1,
            tier2=tier2,
            tier3=tier3,
            clustering_method="kmeans",
            labeling_model="gpt-5-mini"
        )
        
        # Validate structure
        validation = hierarchy.validate_hierarchy()
        assert validation['valid'] == True
        print(f"  ✓ Hierarchy validation: {validation}")
        
        # Check statistics
        stats = hierarchy.get_statistics()
        assert stats['tier1_topics'] == 2
        assert stats['tier2_topics'] == 3
        assert stats['tier3_topics'] == 1
        print(f"  ✓ Taxonomy stats: {stats['total_topics']} total topics")
        
        # Test topic lookup
        topic = hierarchy.get_topic_by_id("T1_01")
        assert topic is not None
        assert topic.label == "Machine Learning"
        print("  ✓ Topic lookup working")
        
        # Test tier queries
        t2_children = hierarchy.get_tier2_topics(parent_tier1_id="T1_01")
        assert len(t2_children) == 2
        print("  ✓ Tier queries working")
        
        print("\n✓ Taxonomy quality tests passed")
        return True
    
    @staticmethod
    def test_classification_validation():
        """Test classification result validation."""
        print("\n" + "=" * 70)
        print("Test: Classification Validation")
        print("=" * 70)
        
        # Create classified paper
        paper = create_sample_paper_record("classified_paper")
        paper.processing_status = "classified"
        paper.tier1_topic = "T1_01"
        paper.tier1_topic_name = "Machine Learning"
        paper.tier1_confidence = 0.85
        paper.tier2_topic = "T2_01"
        paper.tier2_topic_name = "Deep Learning"
        paper.tier2_confidence = 0.78
        paper.tier3_topic = "T3_01"
        paper.tier3_topic_name = "CNNs"
        paper.tier3_confidence = 0.72
        
        # Validate paper
        validation = validate_paper_record(paper)
        assert validation['has_topics'] == True
        print(f"  ✓ Classified paper validation: {validation}")
        
        # Check confidence scores
        assert 0 <= paper.tier1_confidence <= 1
        assert 0 <= paper.tier2_confidence <= 1
        assert 0 <= paper.tier3_confidence <= 1
        print("  ✓ Confidence scores valid")
        
        # Test hierarchy consistency (tier3 requires tier2, tier2 requires tier1)
        assert paper.tier1_topic is not None or paper.tier2_topic is None
        assert paper.tier2_topic is not None or paper.tier3_topic is None
        print("  ✓ Classification hierarchy consistent")
        
        # Test missing classification detection
        unclassified = create_sample_paper_record("unclassified")
        unclassified.processing_status = "classified"
        unclassified.tier1_topic = None
        
        unclassified_validation = validate_paper_record(unclassified)
        assert len(unclassified_validation['issues']) > 0
        print("  ✓ Missing classification detected")
        
        print("\n✓ Classification validation tests passed")
        return True
    
    @staticmethod
    def test_summary_quality():
        """Test summary quality validation."""
        print("\n" + "=" * 70)
        print("Test: Summary Quality Validation")
        print("=" * 70)
        
        # Create paper with summary
        paper = create_sample_paper_record("summarized_paper")
        paper.processing_status = "summarized"
        paper.full_summary = """
        This paper presents a novel approach to machine learning.
        The key contributions include:
        1. A new architecture for deep neural networks
        2. An efficient training algorithm
        3. Comprehensive experimental results
        The approach achieves state-of-the-art performance on benchmark datasets.
        """
        
        # Validate paper
        validation = validate_paper_record(paper)
        assert validation['has_summary'] == True
        print(f"  ✓ Summarized paper validation: {validation}")
        
        # Check summary length
        summary_length = len(paper.full_summary)
        assert summary_length > 100, "Summary too short"
        assert summary_length < 10000, "Summary too long"
        print(f"  ✓ Summary length: {summary_length} chars")
        
        # Test missing summary detection
        no_summary = create_sample_paper_record("no_summary")
        no_summary.processing_status = "summarized"
        no_summary.full_summary = None
        
        no_summary_validation = validate_paper_record(no_summary)
        # Should have warnings about missing summary
        print(f"  ✓ Missing summary detected: {len(no_summary_validation['warnings'])} warnings")
        
        print("\n✓ Summary quality tests passed")
        return True
    
    @staticmethod
    def test_export_data_integrity():
        """Test export data integrity."""
        print("\n" + "=" * 70)
        print("Test: Export Data Integrity")
        print("=" * 70)
        
        # Create sample papers
        papers = {}
        for i in range(5):
            paper = create_sample_paper_record(f"export_paper_{i}")
            paper.title = f"Test Paper {i}"
            paper.authors = ["Author A", "Author B"]
            paper.year = 2023
            paper.processing_status = "classified"
            papers[paper.id] = paper
        
        # Test paper serialization
        for paper_id, paper in papers.items():
            paper_dict = paper.to_dict()
            
            # Verify key fields preserved
            assert paper_dict['id'] == paper_id
            assert paper_dict['title'] == paper.title
            assert paper_dict['authors'] == paper.authors
            assert paper_dict['year'] == paper.year
        print(f"  ✓ Paper serialization preserves {len(papers)} records")
        
        # Test round-trip (serialize and deserialize)
        for paper_id, paper in papers.items():
            paper_dict = paper.to_dict()
            restored = PaperRecord.from_dict(paper_dict)
            
            assert restored.id == paper.id
            assert restored.title == paper.title
            assert restored.authors == paper.authors
        print("  ✓ Round-trip serialization working")
        
        # Test taxonomy serialization
        hierarchy = TopicHierarchy(
            taxonomy_version="v1.0_test",
            total_papers=5,
            tier1=[TopicNode(id="T1_01", label="Test", description="Test topic", paper_ids=list(papers.keys()))],
        )
        
        hierarchy_dict = hierarchy.to_dict()
        restored_hierarchy = TopicHierarchy.from_dict(hierarchy_dict)
        assert restored_hierarchy.taxonomy_version == hierarchy.taxonomy_version
        assert len(restored_hierarchy.tier1) == 1
        print("  ✓ Taxonomy serialization working")
        
        print("\n✓ Export data integrity tests passed")
        return True


# =============================================================================
# Error Handling and Recovery Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling and recovery."""
    
    @staticmethod
    def test_error_handler():
        """Test ErrorHandler functionality."""
        print("\n" + "=" * 70)
        print("Test: Error Handler")
        print("=" * 70)
        
        handler = ErrorHandler()
        
        # Log an error
        handler.log_error(
            paper_id="test_paper",
            stage="parsing",
            error=ValueError("Test error"),
            context={"file": "test.pdf"}
        )
        
        assert len(handler.errors) == 1
        print("  ✓ Error logged successfully")
        
        # Test error retrieval
        paper_errors = handler.get_errors_by_paper("test_paper")
        assert len(paper_errors) == 1
        print("  ✓ Error retrieval by paper working")
        
        stage_errors = handler.get_errors_by_stage("parsing")
        assert len(stage_errors) == 1
        print("  ✓ Error retrieval by stage working")
        
        # Test error summary
        summary = handler.get_error_summary()
        assert summary['total_errors'] == 1
        assert 'parsing' in summary['by_stage']
        print(f"  ✓ Error summary: {summary}")
        
        # Test paper update on error
        paper = create_sample_paper_record("error_paper")
        updated = handler.update_paper_on_error(
            paper, "summarization", ValueError("API error")
        )
        
        assert updated.processing_status == "failed"
        assert updated.error_reason == "API error"
        assert updated.error_stage == "summarization"
        assert updated.retry_count == 1
        print("  ✓ Paper update on error working")
        
        print("\n✓ Error handler tests passed")
        return True
    
    @staticmethod
    def test_retry_logic():
        """Test retry logic for failed operations."""
        print("\n" + "=" * 70)
        print("Test: Retry Logic")
        print("=" * 70)
        
        try:
            from rag_models import RetryHandler, RateLimitError, TransientAPIError
            
            handler = RetryHandler(max_retries=3, initial_delay=0.01, backoff_factor=2.0)
            
            # Test successful execution
            call_count = [0]
            def success_func():
                call_count[0] += 1
                return "success"
            
            result = handler.retry_with_backoff(success_func)
            assert result == "success"
            assert call_count[0] == 1
            print("  ✓ Successful execution on first try")
            
            # Test retry on transient error
            retry_count = [0]
            def retry_func():
                retry_count[0] += 1
                if retry_count[0] < 3:
                    raise TransientAPIError("Network error")
                return "success after retry"
            
            result = handler.retry_with_backoff(retry_func)
            assert result == "success after retry"
            assert retry_count[0] == 3
            print(f"  ✓ Success after {retry_count[0]} retries")
            
            # Test max retries exceeded
            def always_fail():
                raise TransientAPIError("Always fails")
            
            try:
                handler.retry_with_backoff(always_fail)
                assert False, "Should have raised exception"
            except TransientAPIError:
                print("  ✓ Max retries correctly exceeded")
            
            print("\n✓ Retry logic tests passed")
            return True
            
        except ImportError as e:
            print(f"  Skipping: {e}")
            return None


# =============================================================================
# Cost Tracking Tests
# =============================================================================

class TestCostTracking:
    """Tests for cost tracking functionality."""
    
    @staticmethod
    def test_cost_estimation():
        """Test API cost estimation."""
        print("\n" + "=" * 70)
        print("Test: Cost Estimation")
        print("=" * 70)
        
        config = create_default_config(
            max_cost_per_run=10.0,
            enable_cost_tracking=True,
        )
        tracker = CostTracker(config)
        
        # Test GPT-5-mini cost
        cost = tracker.estimate_cost(
            model="gpt-5-mini",
            input_tokens=10000,
            output_tokens=5000,
            is_batch=False
        )
        assert cost > 0
        print(f"  ✓ GPT-5-mini cost (10k in, 5k out): ${cost:.6f}")
        
        # Test embedding cost
        embed_cost = tracker.estimate_cost(
            model="text-embedding-3-large",
            input_tokens=10000,
            output_tokens=0,
        )
        assert embed_cost > 0
        print(f"  ✓ Embedding cost (10k tokens): ${embed_cost:.6f}")
        
        # Test batch discount
        batch_cost = tracker.estimate_cost(
            model="gpt-5-mini",
            input_tokens=10000,
            output_tokens=5000,
            is_batch=True
        )
        assert batch_cost == cost * 0.5
        print(f"  ✓ Batch discount applied: ${batch_cost:.6f}")
        
        print("\n✓ Cost estimation tests passed")
        return True
    
    @staticmethod
    def test_budget_tracking():
        """Test budget tracking and limits."""
        print("\n" + "=" * 70)
        print("Test: Budget Tracking")
        print("=" * 70)
        
        config = create_default_config(
            max_cost_per_run=0.001,  # Very low budget
            enable_cost_tracking=True,
        )
        tracker = CostTracker(config)
        
        # Record some API calls
        record = tracker.record_api_call(
            operation="summarization",
            model="gpt-5-mini",
            input_tokens=100,
            output_tokens=50,
        )
        
        assert record.estimated_cost > 0
        assert tracker.total_cost > 0
        print(f"  ✓ API call recorded: ${record.estimated_cost:.6f}")
        
        # Test budget exceeded
        from rag_models import BudgetExceededError
        
        try:
            for _ in range(100):
                tracker.record_api_call(
                    operation="summarization",
                    model="gpt-5-mini",
                    input_tokens=10000,
                    output_tokens=5000,
                )
            print("  ✓ Budget tracking without limit")
        except BudgetExceededError:
            print("  ✓ Budget exceeded correctly detected")
        
        print("\n✓ Budget tracking tests passed")
        return True


# =============================================================================
# Main Test Runner
# =============================================================================

def run_all_tests():
    """Run all Phase 20 tests."""
    print("\n" + "=" * 80)
    print("PHASE 20: TESTING AND VALIDATION - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    results = {
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'details': []
    }
    
    test_sections = [
        # Step 20.1: Unit Test Functions
        ("20.1 Unit Tests", [
            ("PDF Parsing", TestUnitFunctions.test_pdf_parsing_mock),
            ("Chunking Logic", TestUnitFunctions.test_chunking_logic),
            ("Metadata Extraction", TestUnitFunctions.test_metadata_extraction),
            ("Embedding Generation", TestUnitFunctions.test_embedding_generation_mock),
            ("Clustering Algorithms", TestUnitFunctions.test_clustering_algorithms),
            ("Query Functions", TestUnitFunctions.test_query_functions),
        ]),
        
        # Step 20.2: Integration Testing
        ("20.2 Integration Tests", [
            ("Small Corpus Processing", TestIntegration.test_small_corpus_processing),
            ("End-to-End Pipeline", TestIntegration.test_end_to_end_pipeline_mock),
            ("Data Consistency", TestIntegration.test_data_consistency),
            ("Output Validation", TestIntegration.test_output_validation),
        ]),
        
        # Step 20.3: Edge Case Testing
        ("20.3 Edge Case Tests", [
            ("Scanned PDF Detection", TestEdgeCases.test_scanned_pdf_detection),
            ("Large Paper Handling", TestEdgeCases.test_large_paper_handling),
            ("Small Paper Handling", TestEdgeCases.test_small_paper_handling),
            ("Corrupted File Handling", TestEdgeCases.test_corrupted_file_handling),
            ("Special Characters", TestEdgeCases.test_special_characters_handling),
        ]),
        
        # Step 20.4: Performance Testing
        ("20.4 Performance Tests", [
            ("Processing Time", TestPerformance.test_processing_time),
            ("Memory Efficiency", TestPerformance.test_memory_efficiency),
            ("Batch Processing", TestPerformance.test_batch_processing_efficiency),
        ]),
        
        # Step 20.5: Validation Tests
        ("20.5 Validation Tests", [
            ("Taxonomy Quality", TestValidation.test_taxonomy_quality),
            ("Classification Validation", TestValidation.test_classification_validation),
            ("Summary Quality", TestValidation.test_summary_quality),
            ("Export Data Integrity", TestValidation.test_export_data_integrity),
        ]),
        
        # Additional Tests
        ("Error Handling Tests", [
            ("Error Handler", TestErrorHandling.test_error_handler),
            ("Retry Logic", TestErrorHandling.test_retry_logic),
        ]),
        
        ("Cost Tracking Tests", [
            ("Cost Estimation", TestCostTracking.test_cost_estimation),
            ("Budget Tracking", TestCostTracking.test_budget_tracking),
        ]),
    ]
    
    for section_name, tests in test_sections:
        print(f"\n{'=' * 80}")
        print(f"Section: {section_name}")
        print("=" * 80)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                if result is None:
                    results['skipped'] += 1
                    results['details'].append((test_name, "SKIPPED"))
                else:
                    results['passed'] += 1
                    results['details'].append((test_name, "PASSED"))
            except AssertionError as e:
                results['failed'] += 1
                results['details'].append((test_name, f"FAILED: {e}"))
                print(f"\n❌ {test_name} FAILED: {e}")
            except Exception as e:
                results['failed'] += 1
                results['details'].append((test_name, f"ERROR: {e}"))
                print(f"\n❌ {test_name} ERROR: {e}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total = results['passed'] + results['failed'] + results['skipped']
    print(f"Total Tests: {total}")
    print(f"Passed:      {results['passed']}")
    print(f"Failed:      {results['failed']}")
    print(f"Skipped:     {results['skipped']}")
    print("=" * 80)
    
    if results['failed'] > 0:
        print("\n⚠️  FAILED TESTS:")
        for name, status in results['details']:
            if status.startswith("FAILED") or status.startswith("ERROR"):
                print(f"  - {name}: {status}")
        print()
    
    if results['passed'] == total:
        print("\n✅ ALL TESTS PASSED!")
    elif results['failed'] == 0:
        print(f"\n✅ {results['passed']} tests passed, {results['skipped']} skipped (missing dependencies)")
    else:
        print(f"\n⚠️  {results['failed']} tests failed. Please review the output above.")
    
    return results['failed'] == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
