#!/usr/bin/env python3
"""
RAG PDF Research Corpus System - Corpus Utilities (Phase 16)

This module implements Phase 16 of the FINAL_NOTEBOOK_ACTION_PLAN.md:
- Step 16.1: Paper Search Functions
- Step 16.2: Corpus Statistics
- Step 16.3: Export Utilities
- Step 16.4: Data Update Functions
- Step 16.5: Cleanup Functions

Provides comprehensive utilities for searching, analyzing, managing, and maintaining
the research corpus.

Version: 1.0
Date: 2025-11-24
"""

import json
import logging
import shutil
from collections import Counter, defaultdict
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Literal, Set
import hashlib

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("Pandas not available. Some export features may be limited.")

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    logger.warning("Matplotlib/Seaborn not available. Chart generation disabled.")

try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available. Index operations disabled.")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Some update functions may be limited.")

from rag_models import (
    PaperRecord,
    PaperChunk,
    GraphState,
    RunConfig,
    TopicHierarchy,
)

# Export list
__all__ = [
    # Step 16.1: Paper Search Functions
    'search_papers',
    'search_by_title',
    'search_by_author',
    'search_by_date_range',
    'search_by_topic',
    'filter_by_status',
    'advanced_search',
    
    # Step 16.2: Corpus Statistics
    'count_papers_by_year',
    'count_papers_by_source',
    'get_most_common_authors',
    'get_most_common_venues',
    'get_topic_distribution',
    'generate_statistics_charts',
    'generate_corpus_report',
    
    # Step 16.3: Export Utilities
    'export_paper_subset',
    'export_by_topic',
    'export_by_date_range',
    'generate_bibtex_entries',
    'create_reading_list',
    'export_to_markdown',
    
    # Step 16.4: Data Update Functions
    'add_new_papers',
    'reprocess_failed_papers',
    'update_paper_metadata',
    'reclassify_papers',
    'rebuild_faiss_index',
    'merge_corpus_states',
    
    # Step 16.5: Cleanup Functions
    'remove_duplicate_papers',
    'clean_orphaned_chunks',
    'verify_data_integrity',
    'optimize_storage',
    'archive_old_versions',
    'compact_corpus',
]


# =============================================================================
# Step 16.1: Paper Search Functions
# =============================================================================

def search_papers(
    state: GraphState,
    query: Optional[str] = None,
    author: Optional[str] = None,
    year_range: Optional[Tuple[int, int]] = None,
    topic_id: Optional[str] = None,
    status: Optional[str] = None,
    has_doi: Optional[bool] = None,
    has_arxiv: Optional[bool] = None,
) -> List[PaperRecord]:
    """
    Generic search function with multiple filters.
    
    Args:
        state: GraphState
        query: Search query for title/abstract
        author: Author name to search for
        year_range: Tuple of (min_year, max_year)
        topic_id: Topic ID to filter by
        status: Processing status to filter by
        has_doi: Filter papers with/without DOI
        has_arxiv: Filter papers with/without arXiv ID
    
    Returns:
        List of matching papers
    """
    papers = state.get('papers', {}).values()
    results = []
    
    for paper in papers:
        # Apply all filters
        if query:
            query_lower = query.lower()
            title_match = query_lower in (paper.title or '').lower()
            abstract_match = query_lower in (paper.abstract_text or '').lower()
            if not (title_match or abstract_match):
                continue
        
        if author:
            author_lower = author.lower()
            if not any(author_lower in a.lower() for a in (paper.authors or [])):
                continue
        
        if year_range:
            min_year, max_year = year_range
            if not paper.year or not (min_year <= paper.year <= max_year):
                continue
        
        if topic_id:
            if not (paper.tier1_topic == topic_id or 
                    paper.tier2_topic == topic_id or 
                    paper.tier3_topic == topic_id):
                continue
        
        if status and paper.processing_status != status:
            continue
        
        if has_doi is not None:
            if has_doi and not paper.doi:
                continue
            if not has_doi and paper.doi:
                continue
        
        if has_arxiv is not None:
            if has_arxiv and not paper.arxiv_id:
                continue
            if not has_arxiv and paper.arxiv_id:
                continue
        
        results.append(paper)
    
    return results


def search_by_title(
    state: GraphState,
    keyword: str,
    case_sensitive: bool = False,
    exact_match: bool = False
) -> List[PaperRecord]:
    """
    Search papers by title keyword.
    
    Args:
        state: GraphState
        keyword: Keyword to search for
        case_sensitive: Whether search is case-sensitive
        exact_match: Whether to match exact title only
    
    Returns:
        List of matching papers
    """
    if not case_sensitive:
        keyword = keyword.lower()
    
    matches = []
    for paper in state.get('papers', {}).values():
        title = paper.title or ''
        if not case_sensitive:
            title = title.lower()
        
        if exact_match:
            if title == keyword:
                matches.append(paper)
        else:
            if keyword in title:
                matches.append(paper)
    
    return matches


def search_by_author(
    state: GraphState,
    author_name: str,
    case_sensitive: bool = False,
    exact_match: bool = False
) -> List[PaperRecord]:
    """
    Search papers by author name.
    
    Args:
        state: GraphState
        author_name: Author name to search for
        case_sensitive: Whether search is case-sensitive
        exact_match: Whether to match exact author name only
    
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
            
            if exact_match:
                if author_check == author_name:
                    matches.append(paper)
                    break
            else:
                if author_name in author_check:
                    matches.append(paper)
                    break
    
    return matches


def search_by_date_range(
    state: GraphState,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None
) -> List[PaperRecord]:
    """
    Search papers by date range.
    
    Args:
        state: GraphState
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        start_year: Start year (inclusive)
        end_year: End year (inclusive)
    
    Returns:
        List of matching papers
    """
    matches = []
    
    for paper in state.get('papers', {}).values():
        # Check by date
        if start_date or end_date:
            if not paper.publish_date:
                continue
            
            if start_date and paper.publish_date < start_date:
                continue
            if end_date and paper.publish_date > end_date:
                continue
        
        # Check by year
        if start_year or end_year:
            if not paper.year:
                continue
            
            if start_year and paper.year < start_year:
                continue
            if end_year and paper.year > end_year:
                continue
        
        matches.append(paper)
    
    return matches


def search_by_topic(
    state: GraphState,
    topic_id: str,
    tier: Literal[1, 2, 3] = 1,
    include_children: bool = False
) -> List[PaperRecord]:
    """
    Search papers by topic.
    
    Args:
        state: GraphState
        topic_id: Topic ID
        tier: Topic tier (1, 2, or 3)
        include_children: Include papers in child topics
    
    Returns:
        List of matching papers
    """
    matches = []
    hierarchy = state.get('topic_hierarchy')
    
    # Get topic IDs to search
    topic_ids = {topic_id}
    
    if include_children and hierarchy:
        # Add child topics
        if tier == 1:
            for t2_id, t2_node in hierarchy.tier2_topics.items():
                if t2_node.parent_id == topic_id:
                    topic_ids.add(t2_id)
                    # Add tier 3 children
                    for t3_id, t3_node in hierarchy.tier3_topics.items():
                        if t3_node.parent_id == t2_id:
                            topic_ids.add(t3_id)
        elif tier == 2:
            for t3_id, t3_node in hierarchy.tier3_topics.items():
                if t3_node.parent_id == topic_id:
                    topic_ids.add(t3_id)
    
    # Find matching papers
    for paper in state.get('papers', {}).values():
        if tier == 1 and paper.tier1_topic in topic_ids:
            matches.append(paper)
        elif tier == 2 and paper.tier2_topic in topic_ids:
            matches.append(paper)
        elif tier == 3 and paper.tier3_topic in topic_ids:
            matches.append(paper)
    
    return matches


def filter_by_status(
    state: GraphState,
    status: str
) -> List[PaperRecord]:
    """
    Filter papers by processing status.
    
    Args:
        state: GraphState
        status: Processing status (e.g., 'classified', 'failed', 'pending')
    
    Returns:
        List of papers with matching status
    """
    matches = []
    for paper in state.get('papers', {}).values():
        if paper.processing_status == status:
            matches.append(paper)
    
    return matches


def advanced_search(
    state: GraphState,
    filters: Dict[str, Any]
) -> List[PaperRecord]:
    """
    Advanced search with complex filter combinations.
    
    Args:
        state: GraphState
        filters: Dictionary of filter criteria
            - 'title': str
            - 'authors': List[str]
            - 'year_min': int
            - 'year_max': int
            - 'topics': List[str]
            - 'status': str
            - 'has_summary': bool
            - 'min_pages': int
            - 'max_pages': int
    
    Returns:
        List of matching papers
    """
    papers = list(state.get('papers', {}).values())
    
    # Apply title filter
    if 'title' in filters:
        keyword = filters['title'].lower()
        papers = [p for p in papers if keyword in (p.title or '').lower()]
    
    # Apply authors filter (any author matches)
    if 'authors' in filters:
        author_filters = [a.lower() for a in filters['authors']]
        papers = [
            p for p in papers
            if any(
                af in author.lower()
                for af in author_filters
                for author in (p.authors or [])
            )
        ]
    
    # Apply year range
    if 'year_min' in filters:
        papers = [p for p in papers if p.year and p.year >= filters['year_min']]
    if 'year_max' in filters:
        papers = [p for p in papers if p.year and p.year <= filters['year_max']]
    
    # Apply topic filter (any topic matches)
    if 'topics' in filters:
        topic_ids = set(filters['topics'])
        papers = [
            p for p in papers
            if (p.tier1_topic in topic_ids or 
                p.tier2_topic in topic_ids or 
                p.tier3_topic in topic_ids)
        ]
    
    # Apply status filter
    if 'status' in filters:
        papers = [p for p in papers if p.processing_status == filters['status']]
    
    # Apply summary filter
    if 'has_summary' in filters:
        if filters['has_summary']:
            papers = [p for p in papers if p.full_summary]
        else:
            papers = [p for p in papers if not p.full_summary]
    
    # Apply page count filters
    if 'min_pages' in filters:
        papers = [p for p in papers if p.page_count and p.page_count >= filters['min_pages']]
    if 'max_pages' in filters:
        papers = [p for p in papers if p.page_count and p.page_count <= filters['max_pages']]
    
    return papers


# =============================================================================
# Step 16.2: Corpus Statistics
# =============================================================================

def count_papers_by_year(state: GraphState) -> Dict[int, int]:
    """
    Count papers by publication year.
    
    Args:
        state: GraphState
    
    Returns:
        Dictionary mapping year to count
    """
    year_counts = Counter()
    
    for paper in state.get('papers', {}).values():
        if paper.year:
            year_counts[paper.year] += 1
    
    return dict(sorted(year_counts.items()))


def count_papers_by_source(state: GraphState) -> Dict[str, int]:
    """
    Count papers by source (arXiv, journal, unknown).
    
    Args:
        state: GraphState
    
    Returns:
        Dictionary mapping source type to count
    """
    source_counts = Counter()
    
    for paper in state.get('papers', {}).values():
        if paper.arxiv_id:
            source_counts['arXiv'] += 1
        elif paper.doi:
            source_counts['Journal/Conference'] += 1
        else:
            source_counts['Unknown'] += 1
    
    return dict(source_counts)


def get_most_common_authors(
    state: GraphState,
    top_n: int = 10
) -> List[Tuple[str, int]]:
    """
    Get most common authors in the corpus.
    
    Args:
        state: GraphState
        top_n: Number of top authors to return
    
    Returns:
        List of (author, count) tuples
    """
    author_counts = Counter()
    
    for paper in state.get('papers', {}).values():
        for author in (paper.authors or []):
            author_counts[author] += 1
    
    return author_counts.most_common(top_n)


def get_most_common_venues(
    state: GraphState,
    top_n: int = 10
) -> List[Tuple[str, int]]:
    """
    Get most common publication venues in the corpus.
    
    Args:
        state: GraphState
        top_n: Number of top venues to return
    
    Returns:
        List of (venue, count) tuples
    """
    venue_counts = Counter()
    
    for paper in state.get('papers', {}).values():
        if paper.venue:
            venue_counts[paper.venue] += 1
    
    return venue_counts.most_common(top_n)


def get_topic_distribution(
    state: GraphState,
    tier: Literal[1, 2, 3] = 1
) -> Dict[str, int]:
    """
    Get distribution of papers across topics.
    
    Args:
        state: GraphState
        tier: Topic tier to analyze
    
    Returns:
        Dictionary mapping topic ID to paper count
    """
    topic_counts = Counter()
    
    for paper in state.get('papers', {}).values():
        if tier == 1 and paper.tier1_topic:
            topic_counts[paper.tier1_topic] += 1
        elif tier == 2 and paper.tier2_topic:
            topic_counts[paper.tier2_topic] += 1
        elif tier == 3 and paper.tier3_topic:
            topic_counts[paper.tier3_topic] += 1
    
    return dict(topic_counts)


def generate_statistics_charts(
    state: GraphState,
    output_dir: str,
    chart_types: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Generate various statistics charts.
    
    Args:
        state: GraphState
        output_dir: Directory to save charts
        chart_types: List of chart types to generate (None = all)
            Options: 'year', 'source', 'authors', 'venues', 'topics'
    
    Returns:
        Dictionary mapping chart type to file path
    """
    if not PLOTTING_AVAILABLE:
        logger.warning("Plotting libraries not available. Charts not generated.")
        return {}
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if chart_types is None:
        chart_types = ['year', 'source', 'authors', 'venues', 'topics']
    
    chart_paths = {}
    
    # Papers by year chart
    if 'year' in chart_types:
        year_counts = count_papers_by_year(state)
        if year_counts:
            plt.figure(figsize=(12, 6))
            plt.bar(year_counts.keys(), year_counts.values())
            plt.xlabel('Year')
            plt.ylabel('Number of Papers')
            plt.title('Papers by Publication Year')
            plt.xticks(rotation=45)
            plt.tight_layout()
            path = output_path / 'papers_by_year.png'
            plt.savefig(path)
            plt.close()
            chart_paths['year'] = str(path)
    
    # Papers by source chart
    if 'source' in chart_types:
        source_counts = count_papers_by_source(state)
        if source_counts:
            plt.figure(figsize=(10, 6))
            plt.bar(source_counts.keys(), source_counts.values())
            plt.xlabel('Source Type')
            plt.ylabel('Number of Papers')
            plt.title('Papers by Source Type')
            plt.tight_layout()
            path = output_path / 'papers_by_source.png'
            plt.savefig(path)
            plt.close()
            chart_paths['source'] = str(path)
    
    # Top authors chart
    if 'authors' in chart_types:
        top_authors = get_most_common_authors(state, top_n=15)
        if top_authors:
            authors, counts = zip(*top_authors)
            plt.figure(figsize=(12, 8))
            plt.barh(range(len(authors)), counts)
            plt.yticks(range(len(authors)), authors)
            plt.xlabel('Number of Papers')
            plt.title('Top 15 Most Prolific Authors')
            plt.tight_layout()
            path = output_path / 'top_authors.png'
            plt.savefig(path)
            plt.close()
            chart_paths['authors'] = str(path)
    
    # Top venues chart
    if 'venues' in chart_types:
        top_venues = get_most_common_venues(state, top_n=15)
        if top_venues:
            venues, counts = zip(*top_venues)
            plt.figure(figsize=(12, 8))
            plt.barh(range(len(venues)), counts)
            plt.yticks(range(len(venues)), venues)
            plt.xlabel('Number of Papers')
            plt.title('Top 15 Most Common Venues')
            plt.tight_layout()
            path = output_path / 'top_venues.png'
            plt.savefig(path)
            plt.close()
            chart_paths['venues'] = str(path)
    
    # Topic distribution chart
    if 'topics' in chart_types:
        topic_dist = get_topic_distribution(state, tier=1)
        if topic_dist:
            # Get topic names
            hierarchy = state.get('topic_hierarchy')
            if hierarchy:
                labels = []
                counts = []
                for topic_id, count in sorted(topic_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
                    topic_node = hierarchy.tier1_topics.get(topic_id)
                    if topic_node:
                        labels.append(topic_node.label)
                        counts.append(count)
                
                if labels:
                    plt.figure(figsize=(12, 8))
                    plt.barh(range(len(labels)), counts)
                    plt.yticks(range(len(labels)), labels)
                    plt.xlabel('Number of Papers')
                    plt.title('Top 10 Topics (Tier 1)')
                    plt.tight_layout()
                    path = output_path / 'topic_distribution.png'
                    plt.savefig(path)
                    plt.close()
                    chart_paths['topics'] = str(path)
    
    logger.info(f"Generated {len(chart_paths)} charts in {output_dir}")
    return chart_paths


def generate_corpus_report(
    state: GraphState,
    output_path: str,
    include_charts: bool = True
) -> str:
    """
    Generate comprehensive corpus statistics report.
    
    Args:
        state: GraphState
        output_path: Path to save report
        include_charts: Whether to generate and include charts
    
    Returns:
        Path to generated report
    """
    papers = state.get('papers', {})
    chunks = state.get('chunks', {})
    
    # Generate statistics
    total_papers = len(papers)
    total_chunks = sum(len(c) for c in chunks.values())
    year_dist = count_papers_by_year(state)
    source_dist = count_papers_by_source(state)
    top_authors = get_most_common_authors(state, top_n=10)
    top_venues = get_most_common_venues(state, top_n=10)
    topic_dist = get_topic_distribution(state, tier=1)
    
    # Count by status
    status_counts = Counter()
    for paper in papers.values():
        status_counts[paper.processing_status] += 1
    
    # Build report
    lines = [
        "# Research Corpus Statistics Report",
        f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "\n## Overview",
        f"- **Total Papers:** {total_papers}",
        f"- **Total Chunks:** {total_chunks}",
        f"- **Average Chunks per Paper:** {total_chunks / total_papers if total_papers else 0:.1f}",
        "\n## Processing Status",
    ]
    
    for status, count in sorted(status_counts.items()):
        lines.append(f"- {status}: {count} ({count/total_papers*100:.1f}%)")
    
    lines.extend([
        "\n## Papers by Year",
    ])
    for year, count in sorted(year_dist.items(), reverse=True)[:10]:
        lines.append(f"- {year}: {count}")
    
    lines.extend([
        "\n## Papers by Source",
    ])
    for source, count in source_dist.items():
        lines.append(f"- {source}: {count} ({count/total_papers*100:.1f}%)")
    
    lines.extend([
        "\n## Top 10 Authors",
    ])
    for i, (author, count) in enumerate(top_authors, 1):
        lines.append(f"{i}. {author}: {count} papers")
    
    lines.extend([
        "\n## Top 10 Venues",
    ])
    for i, (venue, count) in enumerate(top_venues, 1):
        lines.append(f"{i}. {venue}: {count} papers")
    
    # Topic distribution
    hierarchy = state.get('topic_hierarchy')
    if hierarchy and topic_dist:
        lines.extend([
            "\n## Topic Distribution (Tier 1)",
        ])
        sorted_topics = sorted(topic_dist.items(), key=lambda x: x[1], reverse=True)
        for topic_id, count in sorted_topics:
            topic_node = hierarchy.tier1_topics.get(topic_id)
            if topic_node:
                lines.append(f"- {topic_node.label}: {count} ({count/total_papers*100:.1f}%)")
    
    # Generate charts if requested
    if include_charts and PLOTTING_AVAILABLE:
        chart_dir = Path(output_path).parent / 'corpus_charts'
        chart_paths = generate_statistics_charts(state, str(chart_dir))
        
        if chart_paths:
            lines.extend([
                "\n## Charts",
            ])
            for chart_type, path in chart_paths.items():
                lines.append(f"- {chart_type.title()}: `{path}`")
    
    # Write report
    report_text = "\n".join(lines)
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    logger.info(f"Generated corpus report: {output_path}")
    return output_path


# =============================================================================
# Step 16.3: Export Utilities
# =============================================================================

def export_paper_subset(
    state: GraphState,
    paper_ids: List[str],
    output_path: str,
    format: Literal['json', 'csv'] = 'json'
) -> str:
    """
    Export a subset of papers.
    
    Args:
        state: GraphState
        paper_ids: List of paper IDs to export
        output_path: Output file path
        format: Export format ('json' or 'csv')
    
    Returns:
        Path to exported file
    """
    papers = state.get('papers', {})
    subset = [papers[pid] for pid in paper_ids if pid in papers]
    
    if format == 'json':
        data = [p.model_dump() if hasattr(p, 'model_dump') else p.dict() for p in subset]
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    elif format == 'csv' and PANDAS_AVAILABLE:
        data = [p.model_dump() if hasattr(p, 'model_dump') else p.dict() for p in subset]
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
    
    logger.info(f"Exported {len(subset)} papers to {output_path}")
    return output_path


def export_by_topic(
    state: GraphState,
    topic_id: str,
    output_path: str,
    tier: Literal[1, 2, 3] = 1,
    format: Literal['json', 'csv'] = 'json'
) -> str:
    """
    Export papers in a specific topic.
    
    Args:
        state: GraphState
        topic_id: Topic ID
        output_path: Output file path
        tier: Topic tier
        format: Export format
    
    Returns:
        Path to exported file
    """
    papers = search_by_topic(state, topic_id, tier)
    paper_ids = [p.id for p in papers]
    return export_paper_subset(state, paper_ids, output_path, format)


def export_by_date_range(
    state: GraphState,
    start_year: int,
    end_year: int,
    output_path: str,
    format: Literal['json', 'csv'] = 'json'
) -> str:
    """
    Export papers in a date range.
    
    Args:
        state: GraphState
        start_year: Start year (inclusive)
        end_year: End year (inclusive)
        output_path: Output file path
        format: Export format
    
    Returns:
        Path to exported file
    """
    papers = search_by_date_range(state, start_year=start_year, end_year=end_year)
    paper_ids = [p.id for p in papers]
    return export_paper_subset(state, paper_ids, output_path, format)


def generate_bibtex_entries(
    state: GraphState,
    paper_ids: Optional[List[str]] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Generate BibTeX entries for papers.
    
    Args:
        state: GraphState
        paper_ids: List of paper IDs (None = all papers)
        output_path: Output file path (None = return string only)
    
    Returns:
        BibTeX string
    """
    papers_dict = state.get('papers', {})
    
    if paper_ids is None:
        papers = list(papers_dict.values())
    else:
        papers = [papers_dict[pid] for pid in paper_ids if pid in papers_dict]
    
    bibtex_entries = []
    
    for paper in papers:
        # Generate citation key
        first_author = paper.authors[0].split()[-1] if paper.authors else 'Unknown'
        year = paper.year or 'XXXX'
        title_word = paper.title.split()[0] if paper.title else 'Paper'
        cite_key = f"{first_author}{year}{title_word}"
        
        # Determine entry type
        if paper.arxiv_id:
            entry_type = 'article'
        elif paper.venue:
            entry_type = 'inproceedings' if 'conference' in paper.venue.lower() else 'article'
        else:
            entry_type = 'misc'
        
        # Build entry
        entry = [f"@{entry_type}{{{cite_key},"]
        
        if paper.title:
            entry.append(f'  title = {{{paper.title}}},')
        
        if paper.authors:
            authors_str = ' and '.join(paper.authors)
            entry.append(f'  author = {{{authors_str}}},')
        
        if paper.year:
            entry.append(f'  year = {{{paper.year}}},')
        
        if paper.venue:
            if entry_type == 'inproceedings':
                entry.append(f'  booktitle = {{{paper.venue}}},')
            else:
                entry.append(f'  journal = {{{paper.venue}}},')
        
        if paper.doi:
            entry.append(f'  doi = {{{paper.doi}}},')
        
        if paper.arxiv_id:
            entry.append(f'  eprint = {{{paper.arxiv_id}}},')
            entry.append(f'  archivePrefix = {{arXiv}},')
        
        if paper.abstract_text:
            # Sanitize abstract for BibTeX
            abstract = paper.abstract_text.replace('{', '').replace('}', '')
            entry.append(f'  abstract = {{{abstract}}},')
        
        entry.append('}')
        bibtex_entries.append('\n'.join(entry))
    
    bibtex_text = '\n\n'.join(bibtex_entries)
    
    if output_path:
        with open(output_path, 'w') as f:
            f.write(bibtex_text)
        logger.info(f"Generated BibTeX for {len(papers)} papers: {output_path}")
    
    return bibtex_text


def create_reading_list(
    state: GraphState,
    paper_ids: List[str],
    output_path: str,
    title: str = "Reading List",
    format: Literal['markdown', 'html', 'txt'] = 'markdown'
) -> str:
    """
    Create a reading list from papers.
    
    Args:
        state: GraphState
        paper_ids: List of paper IDs
        output_path: Output file path
        title: Reading list title
        format: Output format
    
    Returns:
        Path to generated reading list
    """
    papers_dict = state.get('papers', {})
    papers = [papers_dict[pid] for pid in paper_ids if pid in papers_dict]
    
    if format == 'markdown':
        lines = [
            f"# {title}",
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d')}",
            f"\nTotal Papers: {len(papers)}",
            "\n---\n",
        ]
        
        for i, paper in enumerate(papers, 1):
            lines.append(f"## {i}. {paper.title or 'Unknown Title'}")
            
            if paper.authors:
                authors_str = ', '.join(paper.authors[:3])
                if len(paper.authors) > 3:
                    authors_str += ' et al.'
                lines.append(f"\n**Authors:** {authors_str}")
            
            if paper.year:
                lines.append(f"**Year:** {paper.year}")
            
            if paper.venue:
                lines.append(f"**Venue:** {paper.venue}")
            
            if paper.arxiv_id:
                lines.append(f"**arXiv:** [{paper.arxiv_id}](https://arxiv.org/abs/{paper.arxiv_id})")
            
            if paper.doi:
                lines.append(f"**DOI:** [{paper.doi}](https://doi.org/{paper.doi})")
            
            if paper.abstract_text:
                lines.append(f"\n**Abstract:** {paper.abstract_text[:300]}...")
            
            if paper.tier1_topic_name:
                lines.append(f"\n**Topic:** {paper.tier1_topic_name}")
            
            lines.append("\n---\n")
        
        content = '\n'.join(lines)
    
    elif format == 'html':
        lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"  <title>{title}</title>",
            "  <style>",
            "    body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }",
            "    h1 { color: #333; }",
            "    h2 { color: #666; margin-top: 30px; }",
            "    .meta { color: #888; }",
            "    .abstract { margin-top: 10px; font-style: italic; }",
            "  </style>",
            "</head>",
            "<body>",
            f"  <h1>{title}</h1>",
            f"  <p class='meta'>Generated: {datetime.now().strftime('%Y-%m-%d')} | Total Papers: {len(papers)}</p>",
            "  <hr>",
        ]
        
        for i, paper in enumerate(papers, 1):
            lines.append(f"  <h2>{i}. {paper.title or 'Unknown Title'}</h2>")
            
            if paper.authors:
                authors_str = ', '.join(paper.authors[:3])
                if len(paper.authors) > 3:
                    authors_str += ' et al.'
                lines.append(f"  <p class='meta'><strong>Authors:</strong> {authors_str}</p>")
            
            if paper.year:
                lines.append(f"  <p class='meta'><strong>Year:</strong> {paper.year}</p>")
            
            if paper.venue:
                lines.append(f"  <p class='meta'><strong>Venue:</strong> {paper.venue}</p>")
            
            if paper.arxiv_id:
                lines.append(f"  <p class='meta'><strong>arXiv:</strong> <a href='https://arxiv.org/abs/{paper.arxiv_id}'>{paper.arxiv_id}</a></p>")
            
            if paper.abstract_text:
                lines.append(f"  <p class='abstract'>{paper.abstract_text[:300]}...</p>")
            
            lines.append("  <hr>")
        
        lines.extend([
            "</body>",
            "</html>",
        ])
        
        content = '\n'.join(lines)
    
    else:  # txt format
        lines = [
            title,
            "=" * len(title),
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d')}",
            f"Total Papers: {len(papers)}",
            "\n" + "-" * 80 + "\n",
        ]
        
        for i, paper in enumerate(papers, 1):
            lines.append(f"{i}. {paper.title or 'Unknown Title'}")
            
            if paper.authors:
                authors_str = ', '.join(paper.authors[:3])
                if len(paper.authors) > 3:
                    authors_str += ' et al.'
                lines.append(f"   Authors: {authors_str}")
            
            if paper.year:
                lines.append(f"   Year: {paper.year}")
            
            if paper.venue:
                lines.append(f"   Venue: {paper.venue}")
            
            if paper.arxiv_id:
                lines.append(f"   arXiv: {paper.arxiv_id}")
            
            if paper.abstract_text:
                lines.append(f"\n   {paper.abstract_text[:200]}...")
            
            lines.append("\n" + "-" * 80 + "\n")
        
        content = '\n'.join(lines)
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Created reading list with {len(papers)} papers: {output_path}")
    return output_path


def export_to_markdown(
    state: GraphState,
    paper_ids: Optional[List[str]] = None,
    output_path: str = 'corpus_export.md'
) -> str:
    """
    Export papers to a markdown document.
    
    Args:
        state: GraphState
        paper_ids: List of paper IDs (None = all papers)
        output_path: Output file path
    
    Returns:
        Path to exported file
    """
    papers_dict = state.get('papers', {})
    
    if paper_ids is None:
        papers = list(papers_dict.values())
    else:
        papers = [papers_dict[pid] for pid in paper_ids if pid in papers_dict]
    
    # Sort by year (descending) and title
    papers = sorted(papers, key=lambda p: (-(p.year or 0), p.title or ''))
    
    lines = [
        "# Research Corpus Export",
        f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total Papers: {len(papers)}",
        "\n---\n",
    ]
    
    # Group by year
    papers_by_year = defaultdict(list)
    for paper in papers:
        year = paper.year or 'Unknown'
        papers_by_year[year].append(paper)
    
    for year in sorted(papers_by_year.keys(), reverse=True):
        year_papers = papers_by_year[year]
        lines.append(f"## {year} ({len(year_papers)} papers)\n")
        
        for paper in year_papers:
            lines.append(f"### {paper.title or 'Unknown Title'}")
            
            if paper.authors:
                lines.append(f"\n**Authors:** {', '.join(paper.authors)}")
            
            if paper.venue:
                lines.append(f"**Venue:** {paper.venue}")
            
            if paper.arxiv_id:
                lines.append(f"**arXiv:** [{paper.arxiv_id}](https://arxiv.org/abs/{paper.arxiv_id})")
            
            if paper.doi:
                lines.append(f"**DOI:** [{paper.doi}](https://doi.org/{paper.doi})")
            
            if paper.tier1_topic_name:
                topics = [paper.tier1_topic_name]
                if paper.tier2_topic_name:
                    topics.append(paper.tier2_topic_name)
                if paper.tier3_topic_name:
                    topics.append(paper.tier3_topic_name)
                lines.append(f"**Topics:** {' → '.join(topics)}")
            
            if paper.abstract_text:
                lines.append(f"\n{paper.abstract_text}")
            
            if paper.full_summary:
                lines.append(f"\n**Summary:** {paper.full_summary[:500]}...")
            
            lines.append("\n---\n")
    
    content = '\n'.join(lines)
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Exported {len(papers)} papers to markdown: {output_path}")
    return output_path


# =============================================================================
# Step 16.4: Data Update Functions
# =============================================================================

def add_new_papers(
    state: GraphState,
    new_papers: List[PaperRecord],
    merge_strategy: Literal['skip', 'replace', 'update'] = 'skip'
) -> GraphState:
    """
    Add new papers to existing corpus.
    
    Args:
        state: GraphState
        new_papers: List of new PaperRecord objects
        merge_strategy: How to handle duplicates
            - 'skip': Skip papers with existing IDs
            - 'replace': Replace existing papers
            - 'update': Update existing papers with new data
    
    Returns:
        Updated GraphState
    """
    papers = state.get('papers', {})
    added = 0
    updated = 0
    skipped = 0
    
    for paper in new_papers:
        if paper.id in papers:
            if merge_strategy == 'skip':
                skipped += 1
                continue
            elif merge_strategy == 'replace':
                papers[paper.id] = paper
                updated += 1
            elif merge_strategy == 'update':
                # Update only non-empty fields
                existing = papers[paper.id]
                updated_paper = existing.model_copy() if hasattr(existing, 'model_copy') else existing.copy()
                
                for field, value in (paper.model_dump() if hasattr(paper, 'model_dump') else paper.dict()).items():
                    if value is not None and value != '':
                        setattr(updated_paper, field, value)
                
                papers[paper.id] = updated_paper
                updated += 1
        else:
            papers[paper.id] = paper
            added += 1
    
    state['papers'] = papers
    logger.info(f"Added {added} new papers, updated {updated}, skipped {skipped}")
    
    return state


def reprocess_failed_papers(
    state: GraphState,
    reprocess_fn: Any,
    max_papers: Optional[int] = None
) -> GraphState:
    """
    Reprocess papers that failed processing.
    
    Args:
        state: GraphState
        reprocess_fn: Function to reprocess papers
        max_papers: Maximum number of papers to reprocess
    
    Returns:
        Updated GraphState
    """
    failed_papers = filter_by_status(state, 'failed')
    
    if max_papers:
        failed_papers = failed_papers[:max_papers]
    
    logger.info(f"Reprocessing {len(failed_papers)} failed papers")
    
    # Call reprocess function
    if callable(reprocess_fn):
        state = reprocess_fn(state, failed_papers)
    
    return state


def update_paper_metadata(
    state: GraphState,
    paper_id: str,
    metadata_updates: Dict[str, Any]
) -> GraphState:
    """
    Update metadata for a specific paper.
    
    Args:
        state: GraphState
        paper_id: Paper ID
        metadata_updates: Dictionary of field updates
    
    Returns:
        Updated GraphState
    """
    papers = state.get('papers', {})
    
    if paper_id not in papers:
        logger.warning(f"Paper {paper_id} not found")
        return state
    
    paper = papers[paper_id]
    updated_paper = paper.model_copy() if hasattr(paper, 'model_copy') else paper.copy()
    
    for field, value in metadata_updates.items():
        if hasattr(updated_paper, field):
            setattr(updated_paper, field, value)
    
    papers[paper_id] = updated_paper
    state['papers'] = papers
    
    logger.info(f"Updated metadata for paper {paper_id}")
    return state


def reclassify_papers(
    state: GraphState,
    paper_ids: Optional[List[str]] = None,
    classifier_fn: Optional[Any] = None
) -> GraphState:
    """
    Reclassify papers with new taxonomy.
    
    Args:
        state: GraphState
        paper_ids: List of paper IDs to reclassify (None = all)
        classifier_fn: Classification function
    
    Returns:
        Updated GraphState
    """
    papers_dict = state.get('papers', {})
    
    if paper_ids is None:
        papers_to_classify = list(papers_dict.values())
    else:
        papers_to_classify = [papers_dict[pid] for pid in paper_ids if pid in papers_dict]
    
    logger.info(f"Reclassifying {len(papers_to_classify)} papers")
    
    if classifier_fn and callable(classifier_fn):
        state = classifier_fn(state, papers_to_classify)
    
    return state


def rebuild_faiss_index(
    state: GraphState,
    openai_client: Optional[OpenAI] = None,
    force: bool = False
) -> GraphState:
    """
    Rebuild FAISS index from chunks.
    
    Args:
        state: GraphState
        openai_client: OpenAI client for embeddings
        force: Force rebuild even if index exists
    
    Returns:
        Updated GraphState with new index
    """
    if not FAISS_AVAILABLE:
        logger.error("FAISS not available")
        return state
    
    chunks = state.get('chunks', {})
    config = state.get('config', RunConfig())
    
    # Collect all chunks
    all_chunks = []
    for paper_chunks in chunks.values():
        all_chunks.extend(paper_chunks)
    
    if not all_chunks:
        logger.warning("No chunks to index")
        return state
    
    logger.info(f"Rebuilding FAISS index with {len(all_chunks)} chunks")
    
    # Check if embeddings exist
    has_embeddings = all(chunk.embedding is not None for chunk in all_chunks)
    
    if not has_embeddings:
        logger.warning("Some chunks missing embeddings. Generate embeddings first.")
        if not openai_client or not OPENAI_AVAILABLE:
            logger.error("Cannot generate embeddings without OpenAI client")
            return state
        
        # Generate embeddings (this would need to be implemented)
        logger.info("Generating embeddings for chunks...")
        # This would call embedding generation logic
    
    # Build FAISS index
    try:
        embeddings = []
        chunk_metadata = []
        
        for chunk in all_chunks:
            if chunk.embedding:
                embeddings.append(chunk.embedding)
                chunk_metadata.append({
                    'chunk_id': chunk.chunk_id,
                    'paper_id': chunk.paper_id,
                })
        
        if embeddings:
            embeddings_array = np.array(embeddings, dtype=np.float32)
            dimension = embeddings_array.shape[1]
            
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings_array)
            
            state['faiss_index'] = index
            state['chunk_metadata'] = chunk_metadata
            
            logger.info(f"Successfully built FAISS index with {len(embeddings)} vectors")
        else:
            logger.error("No valid embeddings found")
    
    except Exception as e:
        logger.error(f"Error building FAISS index: {e}")
    
    return state


def merge_corpus_states(
    state1: GraphState,
    state2: GraphState,
    merge_strategy: Literal['skip', 'replace', 'update'] = 'skip'
) -> GraphState:
    """
    Merge two corpus states.
    
    Args:
        state1: First GraphState
        state2: Second GraphState
        merge_strategy: How to handle conflicts
    
    Returns:
        Merged GraphState
    """
    merged = state1.copy()
    
    # Merge papers
    papers2 = state2.get('papers', {})
    if papers2:
        new_papers = list(papers2.values())
        merged = add_new_papers(merged, new_papers, merge_strategy)
    
    # Merge chunks
    chunks1 = merged.get('chunks', {})
    chunks2 = state2.get('chunks', {})
    
    for paper_id, paper_chunks in chunks2.items():
        if paper_id not in chunks1:
            chunks1[paper_id] = paper_chunks
        elif merge_strategy == 'replace':
            chunks1[paper_id] = paper_chunks
    
    merged['chunks'] = chunks1
    
    logger.info("Merged corpus states")
    return merged


# =============================================================================
# Step 16.5: Cleanup Functions
# =============================================================================

def remove_duplicate_papers(
    state: GraphState,
    dedupe_by: Literal['id', 'title', 'doi', 'arxiv'] = 'id'
) -> Tuple[GraphState, List[str]]:
    """
    Remove duplicate papers from corpus.
    
    Args:
        state: GraphState
        dedupe_by: Field to use for deduplication
    
    Returns:
        Tuple of (updated GraphState, list of removed paper IDs)
    """
    papers = state.get('papers', {})
    seen = set()
    to_remove = []
    
    for paper_id, paper in papers.items():
        # Determine deduplication key
        if dedupe_by == 'id':
            key = paper.id
        elif dedupe_by == 'title':
            key = (paper.title or '').lower().strip()
        elif dedupe_by == 'doi':
            key = paper.doi
        elif dedupe_by == 'arxiv':
            key = paper.arxiv_id
        else:
            key = paper.id
        
        if not key:
            continue
        
        if key in seen:
            to_remove.append(paper_id)
        else:
            seen.add(key)
    
    # Remove duplicates
    for paper_id in to_remove:
        del papers[paper_id]
    
    state['papers'] = papers
    logger.info(f"Removed {len(to_remove)} duplicate papers")
    
    return state, to_remove


def clean_orphaned_chunks(
    state: GraphState
) -> Tuple[GraphState, int]:
    """
    Remove chunks for papers that no longer exist.
    
    Args:
        state: GraphState
    
    Returns:
        Tuple of (updated GraphState, count of removed chunks)
    """
    papers = set(state.get('papers', {}).keys())
    chunks = state.get('chunks', {})
    
    orphaned = []
    for paper_id in list(chunks.keys()):
        if paper_id not in papers:
            orphaned.append(paper_id)
    
    # Remove orphaned chunks
    chunks_removed = 0
    for paper_id in orphaned:
        chunks_removed += len(chunks[paper_id])
        del chunks[paper_id]
    
    state['chunks'] = chunks
    logger.info(f"Removed {chunks_removed} orphaned chunks from {len(orphaned)} papers")
    
    return state, chunks_removed


def verify_data_integrity(
    state: GraphState
) -> Dict[str, Any]:
    """
    Verify data integrity and report issues.
    
    Args:
        state: GraphState
    
    Returns:
        Dictionary of integrity check results
    """
    papers = state.get('papers', {})
    chunks = state.get('chunks', {})
    hierarchy = state.get('topic_hierarchy')
    
    issues = {
        'missing_titles': [],
        'missing_authors': [],
        'missing_summaries': [],
        'missing_topics': [],
        'missing_chunks': [],
        'invalid_years': [],
        'orphaned_chunks': [],
    }
    
    # Check papers
    for paper_id, paper in papers.items():
        if not paper.title:
            issues['missing_titles'].append(paper_id)
        
        if not paper.authors:
            issues['missing_authors'].append(paper_id)
        
        if not paper.full_summary:
            issues['missing_summaries'].append(paper_id)
        
        if not paper.tier1_topic:
            issues['missing_topics'].append(paper_id)
        
        if paper_id not in chunks or not chunks[paper_id]:
            issues['missing_chunks'].append(paper_id)
        
        if paper.year and (paper.year < 1900 or paper.year > datetime.now().year + 1):
            issues['invalid_years'].append(paper_id)
    
    # Check for orphaned chunks
    for paper_id in chunks:
        if paper_id not in papers:
            issues['orphaned_chunks'].append(paper_id)
    
    # Calculate statistics
    total_issues = sum(len(v) for v in issues.values())
    
    report = {
        'total_papers': len(papers),
        'total_chunks': sum(len(c) for c in chunks.values()),
        'total_issues': total_issues,
        'issues': issues,
        'integrity_score': 1.0 - (total_issues / (len(papers) * 6)) if papers else 0.0,
    }
    
    logger.info(f"Integrity check: {total_issues} issues found (score: {report['integrity_score']:.2f})")
    
    return report


def optimize_storage(
    state: GraphState,
    remove_embeddings: bool = False,
    compress_summaries: bool = False
) -> Tuple[GraphState, Dict[str, Any]]:
    """
    Optimize storage by removing redundant data.
    
    Args:
        state: GraphState
        remove_embeddings: Remove embeddings from chunks (keep in FAISS only)
        compress_summaries: Compress long summaries
    
    Returns:
        Tuple of (optimized GraphState, optimization stats)
    """
    stats = {
        'embeddings_removed': 0,
        'summaries_compressed': 0,
        'original_size': 0,
        'optimized_size': 0,
    }
    
    # Estimate original size (rough approximation)
    papers = state.get('papers', {})
    chunks = state.get('chunks', {})
    
    # Remove embeddings from chunks if requested
    if remove_embeddings:
        for paper_chunks in chunks.values():
            for chunk in paper_chunks:
                if chunk.embedding:
                    chunk.embedding = None
                    stats['embeddings_removed'] += 1
    
    # Compress summaries if requested
    if compress_summaries:
        for paper in papers.values():
            if paper.full_summary and len(paper.full_summary) > 2000:
                paper.full_summary = paper.full_summary[:2000] + '...'
                stats['summaries_compressed'] += 1
    
    state['papers'] = papers
    state['chunks'] = chunks
    
    logger.info(f"Optimized storage: removed {stats['embeddings_removed']} embeddings, compressed {stats['summaries_compressed']} summaries")
    
    return state, stats


def archive_old_versions(
    state_path: str,
    archive_dir: str,
    max_versions: int = 5
) -> List[str]:
    """
    Archive old versions of state files.
    
    Args:
        state_path: Path to current state file
        archive_dir: Directory to store archives
        max_versions: Maximum number of versions to keep
    
    Returns:
        List of archived file paths
    """
    archive_path = Path(archive_dir)
    archive_path.mkdir(parents=True, exist_ok=True)
    
    state_file = Path(state_path)
    if not state_file.exists():
        logger.warning(f"State file not found: {state_path}")
        return []
    
    # Create archive with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_name = f"{state_file.stem}_{timestamp}{state_file.suffix}"
    archive_file = archive_path / archive_name
    
    # Copy to archive
    shutil.copy2(state_path, archive_file)
    logger.info(f"Archived state to: {archive_file}")
    
    # Clean up old versions
    archives = sorted(archive_path.glob(f"{state_file.stem}_*{state_file.suffix}"))
    
    if len(archives) > max_versions:
        to_remove = archives[:-max_versions]
        for old_archive in to_remove:
            old_archive.unlink()
            logger.info(f"Removed old archive: {old_archive}")
    
    return [str(a) for a in archives[-max_versions:]]


def compact_corpus(
    state: GraphState,
    remove_failed: bool = True,
    deduplicate: bool = True,
    clean_orphans: bool = True,
    optimize: bool = True
) -> Tuple[GraphState, Dict[str, Any]]:
    """
    Comprehensive corpus cleanup and optimization.
    
    Args:
        state: GraphState
        remove_failed: Remove failed papers
        deduplicate: Remove duplicate papers
        clean_orphans: Remove orphaned chunks
        optimize: Optimize storage
    
    Returns:
        Tuple of (compacted GraphState, compaction stats)
    """
    stats = {
        'original_papers': len(state.get('papers', {})),
        'original_chunks': sum(len(c) for c in state.get('chunks', {}).values()),
        'failed_removed': 0,
        'duplicates_removed': 0,
        'orphans_removed': 0,
    }
    
    # Remove failed papers
    if remove_failed:
        papers = state.get('papers', {})
        failed = [pid for pid, p in papers.items() if p.processing_status == 'failed']
        for pid in failed:
            del papers[pid]
        state['papers'] = papers
        stats['failed_removed'] = len(failed)
    
    # Deduplicate
    if deduplicate:
        state, removed = remove_duplicate_papers(state)
        stats['duplicates_removed'] = len(removed)
    
    # Clean orphans
    if clean_orphans:
        state, orphans_count = clean_orphaned_chunks(state)
        stats['orphans_removed'] = orphans_count
    
    # Optimize
    if optimize:
        state, opt_stats = optimize_storage(state, remove_embeddings=False)
    
    stats['final_papers'] = len(state.get('papers', {}))
    stats['final_chunks'] = sum(len(c) for c in state.get('chunks', {}).values())
    stats['papers_saved'] = stats['original_papers'] - stats['final_papers']
    stats['chunks_saved'] = stats['original_chunks'] - stats['final_chunks']
    
    logger.info(f"Compacted corpus: {stats['papers_saved']} papers, {stats['chunks_saved']} chunks removed")
    
    return state, stats
