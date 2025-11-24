#!/usr/bin/env python3
"""
Examples for Phase 16: Utility Functions and Tools

Demonstrates how to use the corpus utilities for:
- Searching and filtering papers
- Generating statistics and reports
- Exporting data in various formats
- Updating and maintaining the corpus
- Cleaning up and optimizing data

Version: 1.0
Date: 2025-11-24
"""

from datetime import date
from pathlib import Path
import json

from rag_models import (
    RunConfig,
    PaperRecord,
    GraphState,
    TopicNode,
    TopicHierarchy,
)

from corpus_utilities import (
    # Search functions
    search_papers,
    search_by_title,
    search_by_author,
    search_by_date_range,
    search_by_topic,
    filter_by_status,
    advanced_search,
    
    # Statistics
    count_papers_by_year,
    count_papers_by_source,
    get_most_common_authors,
    get_most_common_venues,
    get_topic_distribution,
    generate_corpus_report,
    
    # Export utilities
    export_paper_subset,
    export_by_topic,
    generate_bibtex_entries,
    create_reading_list,
    export_to_markdown,
    
    # Update functions
    add_new_papers,
    update_paper_metadata,
    
    # Cleanup functions
    remove_duplicate_papers,
    clean_orphaned_chunks,
    verify_data_integrity,
    compact_corpus,
)


def create_example_corpus() -> GraphState:
    """Create an example corpus for demonstration."""
    print("Creating example corpus...")
    
    # Sample papers
    papers = {
        'p1': PaperRecord(
            id='p1',
            file_path='/papers/transformer.pdf',
            filename='transformer.pdf',
            title='Attention Is All You Need',
            authors=['Vaswani', 'Shazeer', 'Parmar', 'Uszkoreit'],
            year=2017,
            publish_date=date(2017, 6, 12),
            venue='NeurIPS 2017',
            arxiv_id='1706.03762',
            abstract_text='The dominant sequence transduction models...',
            full_summary='This paper introduces the Transformer architecture...',
            tier1_topic='T1_DL',
            tier1_topic_name='Deep Learning',
            tier2_topic='T2_ATTENTION',
            tier2_topic_name='Attention Mechanisms',
            processing_status='classified'
        ),
        'p2': PaperRecord(
            id='p2',
            file_path='/papers/bert.pdf',
            filename='bert.pdf',
            title='BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',
            authors=['Devlin', 'Chang', 'Lee', 'Toutanova'],
            year=2018,
            publish_date=date(2018, 10, 11),
            venue='NAACL 2019',
            arxiv_id='1810.04805',
            abstract_text='We introduce a new language representation model...',
            full_summary='BERT uses bidirectional transformers for pre-training...',
            tier1_topic='T1_NLP',
            tier1_topic_name='Natural Language Processing',
            tier2_topic='T2_PRETRAINING',
            tier2_topic_name='Pre-training',
            processing_status='classified'
        ),
        'p3': PaperRecord(
            id='p3',
            file_path='/papers/gpt3.pdf',
            filename='gpt3.pdf',
            title='Language Models are Few-Shot Learners',
            authors=['Brown', 'Mann', 'Ryder', 'Subbiah'],
            year=2020,
            publish_date=date(2020, 5, 28),
            venue='NeurIPS 2020',
            arxiv_id='2005.14165',
            abstract_text='Recent work has demonstrated substantial gains...',
            full_summary='GPT-3 demonstrates few-shot learning capabilities...',
            tier1_topic='T1_LLM',
            tier1_topic_name='Large Language Models',
            tier2_topic='T2_SCALING',
            tier2_topic_name='Model Scaling',
            processing_status='classified'
        ),
        'p4': PaperRecord(
            id='p4',
            file_path='/papers/resnet.pdf',
            filename='resnet.pdf',
            title='Deep Residual Learning for Image Recognition',
            authors=['He', 'Zhang', 'Ren', 'Sun'],
            year=2015,
            publish_date=date(2015, 12, 10),
            venue='CVPR 2016',
            doi='10.1109/CVPR.2016.90',
            abstract_text='Deeper neural networks are more difficult to train...',
            full_summary='ResNet introduces skip connections for training very deep networks...',
            tier1_topic='T1_CV',
            tier1_topic_name='Computer Vision',
            tier2_topic='T2_CNN',
            tier2_topic_name='Convolutional Networks',
            processing_status='classified'
        ),
    }
    
    # Topic hierarchy
    hierarchy = TopicHierarchy(
        tier1_topics={
            'T1_DL': TopicNode(id='T1_DL', label='Deep Learning', tier=1),
            'T1_NLP': TopicNode(id='T1_NLP', label='Natural Language Processing', tier=1),
            'T1_LLM': TopicNode(id='T1_LLM', label='Large Language Models', tier=1),
            'T1_CV': TopicNode(id='T1_CV', label='Computer Vision', tier=1),
        },
        tier2_topics={
            'T2_ATTENTION': TopicNode(id='T2_ATTENTION', label='Attention Mechanisms', parent_id='T1_DL', tier=2),
            'T2_PRETRAINING': TopicNode(id='T2_PRETRAINING', label='Pre-training', parent_id='T1_NLP', tier=2),
            'T2_SCALING': TopicNode(id='T2_SCALING', label='Model Scaling', parent_id='T1_LLM', tier=2),
            'T2_CNN': TopicNode(id='T2_CNN', label='Convolutional Networks', parent_id='T1_CV', tier=2),
        },
        tier3_topics={}
    )
    
    state = {
        'config': RunConfig(),
        'papers': papers,
        'chunks': {},
        'topic_hierarchy': hierarchy,
    }
    
    print(f"Created corpus with {len(papers)} papers\n")
    return state


def example_search_functions():
    """Demonstrate paper search functions."""
    print("=" * 80)
    print("EXAMPLE 1: Paper Search Functions")
    print("=" * 80)
    
    state = create_example_corpus()
    
    # Example 1.1: Search by title
    print("\n--- Search by title keyword 'Transformer' ---")
    results = search_by_title(state, 'Transformer')
    for paper in results:
        print(f"  • {paper.title} ({paper.year})")
    
    # Example 1.2: Search by author
    print("\n--- Search by author 'Vaswani' ---")
    results = search_by_author(state, 'Vaswani')
    for paper in results:
        print(f"  • {paper.title}")
        print(f"    Authors: {', '.join(paper.authors)}")
    
    # Example 1.3: Search by date range
    print("\n--- Search papers from 2017-2018 ---")
    results = search_by_date_range(state, start_year=2017, end_year=2018)
    for paper in results:
        print(f"  • {paper.title} ({paper.year})")
    
    # Example 1.4: Search by topic
    print("\n--- Search papers in 'Natural Language Processing' topic ---")
    results = search_by_topic(state, 'T1_NLP', tier=1)
    for paper in results:
        print(f"  • {paper.title}")
        print(f"    Topic: {paper.tier1_topic_name}")
    
    # Example 1.5: Advanced search
    print("\n--- Advanced search: Papers with 'Learning' in title from 2015-2020 ---")
    results = advanced_search(state, {
        'title': 'Learning',
        'year_min': 2015,
        'year_max': 2020,
    })
    for paper in results:
        print(f"  • {paper.title} ({paper.year})")
    
    print()


def example_statistics():
    """Demonstrate corpus statistics functions."""
    print("=" * 80)
    print("EXAMPLE 2: Corpus Statistics")
    print("=" * 80)
    
    state = create_example_corpus()
    
    # Example 2.1: Count papers by year
    print("\n--- Papers by Year ---")
    year_counts = count_papers_by_year(state)
    for year, count in sorted(year_counts.items()):
        print(f"  {year}: {count} papers")
    
    # Example 2.2: Count papers by source
    print("\n--- Papers by Source ---")
    source_counts = count_papers_by_source(state)
    for source, count in source_counts.items():
        print(f"  {source}: {count} papers")
    
    # Example 2.3: Most common authors
    print("\n--- Top 5 Authors ---")
    top_authors = get_most_common_authors(state, top_n=5)
    for i, (author, count) in enumerate(top_authors, 1):
        print(f"  {i}. {author}: {count} papers")
    
    # Example 2.4: Topic distribution
    print("\n--- Topic Distribution (Tier 1) ---")
    topic_dist = get_topic_distribution(state, tier=1)
    hierarchy = state['topic_hierarchy']
    for topic_id, count in sorted(topic_dist.items(), key=lambda x: x[1], reverse=True):
        topic_node = hierarchy.tier1_topics.get(topic_id)
        if topic_node:
            print(f"  {topic_node.label}: {count} papers")
    
    print()


def example_export_utilities():
    """Demonstrate export utilities."""
    print("=" * 80)
    print("EXAMPLE 3: Export Utilities")
    print("=" * 80)
    
    state = create_example_corpus()
    
    # Example 3.1: Export subset to JSON
    print("\n--- Export subset to JSON ---")
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        output = Path(tmpdir) / 'subset.json'
        export_paper_subset(state, ['p1', 'p2'], str(output))
        print(f"  ✓ Exported 2 papers to {output}")
        
        # Show content
        with open(output) as f:
            data = json.load(f)
            print(f"  Papers exported: {[p['title'][:40] + '...' for p in data]}")
    
    # Example 3.2: Generate BibTeX
    print("\n--- Generate BibTeX entries ---")
    bibtex = generate_bibtex_entries(state, ['p1', 'p3'])
    print("  First entry:")
    print("  " + "\n  ".join(bibtex.split('\n\n')[0].split('\n')[:5]))
    print("  ...")
    
    # Example 3.3: Create reading list
    print("\n--- Create reading list ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        output = Path(tmpdir) / 'reading_list.md'
        create_reading_list(
            state,
            ['p1', 'p2', 'p3'],
            str(output),
            title='Top NLP Papers',
            format='markdown'
        )
        print(f"  ✓ Created reading list: {output}")
        
        # Show preview
        with open(output) as f:
            lines = f.readlines()[:10]
            print("  Preview:")
            for line in lines:
                print("    " + line.rstrip())
    
    # Example 3.4: Export to markdown
    print("\n--- Export corpus to markdown ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        output = Path(tmpdir) / 'corpus.md'
        export_to_markdown(state, output_path=str(output))
        print(f"  ✓ Exported all papers to {output}")
    
    print()


def example_update_functions():
    """Demonstrate data update functions."""
    print("=" * 80)
    print("EXAMPLE 4: Data Update Functions")
    print("=" * 80)
    
    state = create_example_corpus()
    
    # Example 4.1: Add new paper
    print("\n--- Add new paper to corpus ---")
    new_paper = PaperRecord(
        id='p_new',
        file_path='/papers/new_paper.pdf',
        filename='new_paper.pdf',
        title='A New Breakthrough in AI',
        authors=['Smith', 'Jones'],
        year=2023,
        processing_status='pending'
    )
    
    original_count = len(state['papers'])
    state = add_new_papers(state, [new_paper])
    print(f"  Papers before: {original_count}")
    print(f"  Papers after: {len(state['papers'])}")
    print(f"  ✓ Added: {new_paper.title}")
    
    # Example 4.2: Update paper metadata
    print("\n--- Update paper metadata ---")
    print(f"  Before: {state['papers']['p1'].venue}")
    state = update_paper_metadata(state, 'p1', {
        'venue': 'NeurIPS 2017 (Updated)',
        'page_count': 11
    })
    print(f"  After: {state['papers']['p1'].venue}")
    print(f"  ✓ Metadata updated")
    
    print()


def example_cleanup_functions():
    """Demonstrate cleanup functions."""
    print("=" * 80)
    print("EXAMPLE 5: Cleanup Functions")
    print("=" * 80)
    
    state = create_example_corpus()
    
    # Example 5.1: Verify data integrity
    print("\n--- Verify data integrity ---")
    report = verify_data_integrity(state)
    print(f"  Total papers: {report['total_papers']}")
    print(f"  Total issues: {report['total_issues']}")
    print(f"  Integrity score: {report['integrity_score']:.2%}")
    
    if report['total_issues'] > 0:
        print("  Issues found:")
        for issue_type, issues in report['issues'].items():
            if issues:
                print(f"    • {issue_type}: {len(issues)}")
    
    # Example 5.2: Remove duplicates
    print("\n--- Remove duplicate papers ---")
    # Add a duplicate for demonstration
    dup = PaperRecord(
        id='p_dup',
        file_path='/papers/dup.pdf',
        filename='dup.pdf',
        title='Attention Is All You Need',  # Same as p1
        year=2023
    )
    state['papers']['p_dup'] = dup
    
    before = len(state['papers'])
    state, removed = remove_duplicate_papers(state, dedupe_by='title')
    print(f"  Papers before: {before}")
    print(f"  Papers after: {len(state['papers'])}")
    print(f"  Removed: {len(removed)} duplicates")
    
    # Example 5.3: Clean orphaned chunks
    print("\n--- Clean orphaned chunks ---")
    from rag_models import PaperChunk
    
    # Add orphaned chunk
    state['chunks']['p_orphan'] = [
        PaperChunk(
            chunk_id='c1',
            paper_id='p_orphan',
            section_label='abstract',
            page_start=1,
            page_end=1,
            text='Orphaned chunk...'
        )
    ]
    
    before_chunks = sum(len(c) for c in state['chunks'].values())
    state, removed = clean_orphaned_chunks(state)
    after_chunks = sum(len(c) for c in state['chunks'].values())
    print(f"  Chunks before: {before_chunks}")
    print(f"  Chunks after: {after_chunks}")
    print(f"  Removed: {removed} orphaned chunks")
    
    # Example 5.4: Compact corpus
    print("\n--- Compact corpus (comprehensive cleanup) ---")
    state, stats = compact_corpus(state)
    print(f"  Compaction results:")
    print(f"    • Final papers: {stats['final_papers']}")
    print(f"    • Papers saved: {stats['papers_saved']}")
    print(f"    • Chunks saved: {stats['chunks_saved']}")
    
    print()


def example_generate_report():
    """Demonstrate comprehensive report generation."""
    print("=" * 80)
    print("EXAMPLE 6: Generate Comprehensive Report")
    print("=" * 80)
    
    state = create_example_corpus()
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / 'corpus_report.md'
        
        print("\n--- Generating corpus report ---")
        generate_corpus_report(state, str(report_path), include_charts=False)
        
        print(f"  ✓ Report generated: {report_path}")
        print("\n  Report preview:")
        
        with open(report_path) as f:
            lines = f.readlines()[:30]
            for line in lines:
                print("  " + line.rstrip())
        
        if len(lines) > 30:
            print("  ...")
    
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("PHASE 16: UTILITY FUNCTIONS AND TOOLS - EXAMPLES")
    print("=" * 80)
    print()
    
    # Run examples
    example_search_functions()
    example_statistics()
    example_export_utilities()
    example_update_functions()
    example_cleanup_functions()
    example_generate_report()
    
    print("=" * 80)
    print("✓ ALL EXAMPLES COMPLETED")
    print("=" * 80)
    print()
    print("These examples demonstrate how to:")
    print("  • Search and filter papers by various criteria")
    print("  • Generate statistics and reports")
    print("  • Export data in multiple formats")
    print("  • Update and maintain the corpus")
    print("  • Clean up and optimize storage")
    print()


if __name__ == '__main__':
    main()
