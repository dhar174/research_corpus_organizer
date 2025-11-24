#!/usr/bin/env python3
"""
RAG PDF Research Corpus System - Phase 14: Quality Control and Validation

This module implements comprehensive quality control, validation, and error analysis
for the RAG PDF pipeline according to FINAL_NOTEBOOK_ACTION_PLAN.md Phase 14:
- Step 14.1: Create QC Dashboard
- Step 14.2: Data Quality Checks
- Step 14.3: Error Analysis
- Step 14.4: Consistency Validation
- Step 14.5: Create QC Report

Version: 1.0
Date: 2025-11-24
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
import json

from rag_models import (
    RunConfig,
    PaperRecord,
    PaperChunk,
    TopicHierarchy,
    GraphState,
    StateManager,
)

logger = logging.getLogger(__name__)

# Export list
__all__ = [
    # Step 14.1: QC Dashboard
    'QCDashboard',
    'create_qc_dashboard',
    'display_qc_statistics',
    
    # Step 14.2: Data Quality Checks
    'DataQualityChecker',
    'verify_pdfs_processed',
    'check_missing_metadata',
    'validate_embedding_integrity',
    'check_summary_completeness',
    'verify_topic_assignments',
    
    # Step 14.3: Error Analysis
    'ErrorAnalyzer',
    'list_failed_papers',
    'categorize_error_types',
    'suggest_remediation',
    'export_error_log',
    
    # Step 14.4: Consistency Validation
    'ConsistencyValidator',
    'check_taxonomy_consistency',
    'validate_hierarchical_relationships',
    'verify_paper_counts',
    'check_orphaned_records',
    'validate_timestamp_sequences',
    
    # Step 14.5: QC Report Generation
    'QCReportGenerator',
    'generate_qc_report',
    'export_report_markdown',
    'export_report_html',
    'save_report_to_drive',
]


# =============================================================================
# Step 14.1: QC Dashboard
# =============================================================================

class QCDashboard:
    """
    Quality Control Dashboard for visualizing corpus statistics and status.
    
    Provides methods to:
    - Display overall statistics
    - Show processing status distribution
    - Identify failed papers
    - Show quality scores distribution
    - Display topic distribution
    """
    
    def __init__(self, state: GraphState):
        """
        Initialize QC Dashboard with current state.
        
        Args:
            state: Current GraphState
        """
        self.state = state
        self.papers = state.get("papers", {})
        self.chunks = state.get("chunks", {})
        self.taxonomy = state.get("topic_hierarchy")
        self.logger = logging.getLogger(f"{__name__}.QCDashboard")
    
    def get_overall_statistics(self) -> Dict[str, Any]:
        """
        Get overall corpus statistics.
        
        Returns:
            Dictionary with comprehensive statistics
        """
        total_papers = len(self.papers)
        total_chunks = sum(len(chunks) for chunks in self.chunks.values())
        
        # Status counts
        status_counts = defaultdict(int)
        for paper in self.papers.values():
            status_counts[paper.processing_status] += 1
        
        # Metadata completeness
        papers_with_title = sum(1 for p in self.papers.values() if p.title)
        papers_with_authors = sum(1 for p in self.papers.values() if p.authors)
        papers_with_date = sum(1 for p in self.papers.values() if p.publish_date)
        papers_with_abstract = sum(1 for p in self.papers.values() if p.abstract_text)
        
        # Summary completeness
        papers_with_summary = sum(1 for p in self.papers.values() if p.full_summary)
        papers_with_deep_summary = sum(1 for p in self.papers.values() if p.deep_summary)
        
        # Topic assignments
        papers_with_tier1 = sum(1 for p in self.papers.values() if p.tier1_topic)
        papers_with_tier2 = sum(1 for p in self.papers.values() if p.tier2_topic)
        papers_with_tier3 = sum(1 for p in self.papers.values() if p.tier3_topic)
        
        return {
            "total_papers": total_papers,
            "total_chunks": total_chunks,
            "status_counts": dict(status_counts),
            "metadata_completeness": {
                "with_title": papers_with_title,
                "with_authors": papers_with_authors,
                "with_date": papers_with_date,
                "with_abstract": papers_with_abstract,
            },
            "summary_completeness": {
                "with_summary": papers_with_summary,
                "with_deep_summary": papers_with_deep_summary,
            },
            "topic_assignments": {
                "with_tier1": papers_with_tier1,
                "with_tier2": papers_with_tier2,
                "with_tier3": papers_with_tier3,
            },
            "taxonomy_info": {
                "has_taxonomy": self.taxonomy is not None,
                "taxonomy_approved": self.state.get("taxonomy_approved", False),
            } if self.taxonomy else None,
        }
    
    def get_status_distribution(self) -> Dict[str, int]:
        """
        Get distribution of processing statuses.
        
        Returns:
            Dictionary mapping status to count
        """
        status_dist = defaultdict(int)
        for paper in self.papers.values():
            status_dist[paper.processing_status] += 1
        return dict(status_dist)
    
    def get_failed_papers(self) -> List[Dict[str, Any]]:
        """
        Get list of failed papers with details.
        
        Returns:
            List of dictionaries with failed paper information
        """
        failed = []
        for paper in self.papers.values():
            if paper.processing_status == "failed":
                failed.append({
                    "id": paper.id,
                    "filename": paper.filename,
                    "error_stage": paper.error_stage,
                    "error_reason": paper.error_reason,
                    "retry_count": paper.retry_count,
                })
        return failed
    
    def get_quality_score_distribution(self) -> Dict[str, Any]:
        """
        Get distribution of quality scores.
        
        Returns:
            Dictionary with quality score buckets
        """
        quality_scores = []
        
        for paper in self.papers.values():
            # Calculate quality score (0-1)
            score = 1.0
            
            # Deduct for missing metadata
            if not paper.title:
                score -= 0.15
            if not paper.authors:
                score -= 0.10
            if not paper.publish_date:
                score -= 0.10
            
            # Deduct for missing summaries (if should have them)
            if paper.processing_status in ["summarized", "classified", "deep_analyzed"]:
                if not paper.full_summary:
                    score -= 0.25
            
            # Deduct for missing classifications (if should have them)
            if paper.processing_status == "classified":
                if not paper.tier1_topic:
                    score -= 0.20
            
            # Failed papers get 0
            if paper.processing_status == "failed":
                score = 0.0
            
            quality_scores.append(max(0.0, score))
        
        # Bucket into categories
        distribution = {
            "excellent (0.9-1.0)": sum(1 for s in quality_scores if s >= 0.9),
            "good (0.7-0.9)": sum(1 for s in quality_scores if 0.7 <= s < 0.9),
            "fair (0.5-0.7)": sum(1 for s in quality_scores if 0.5 <= s < 0.7),
            "poor (<0.5)": sum(1 for s in quality_scores if s < 0.5),
        }
        
        avg_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            "distribution": distribution,
            "average_score": avg_score,
            "min_score": min(quality_scores) if quality_scores else 0,
            "max_score": max(quality_scores) if quality_scores else 0,
        }
    
    def get_topic_distribution(self) -> Dict[str, Any]:
        """
        Get distribution of papers across topics.
        
        Returns:
            Dictionary with topic distribution at each tier
        """
        if not self.taxonomy:
            return {"error": "No taxonomy available"}
        
        tier1_dist = defaultdict(int)
        tier2_dist = defaultdict(int)
        tier3_dist = defaultdict(int)
        
        for paper in self.papers.values():
            if paper.tier1_topic:
                tier1_dist[paper.tier1_topic_name or paper.tier1_topic] += 1
            if paper.tier2_topic:
                tier2_dist[paper.tier2_topic_name or paper.tier2_topic] += 1
            if paper.tier3_topic:
                tier3_dist[paper.tier3_topic_name or paper.tier3_topic] += 1
        
        return {
            "tier1": dict(tier1_dist),
            "tier2": dict(tier2_dist),
            "tier3": dict(tier3_dist),
            "unclassified": sum(1 for p in self.papers.values() if not p.tier1_topic),
        }


def create_qc_dashboard(state: GraphState) -> QCDashboard:
    """
    Create a QC Dashboard instance.
    
    Args:
        state: Current GraphState
        
    Returns:
        QCDashboard instance
    """
    return QCDashboard(state)


def display_qc_statistics(state: GraphState) -> str:
    """
    Display QC statistics in a formatted string.
    
    Args:
        state: Current GraphState
        
    Returns:
        Formatted statistics string
    """
    dashboard = QCDashboard(state)
    stats = dashboard.get_overall_statistics()
    status_dist = dashboard.get_status_distribution()
    quality_dist = dashboard.get_quality_score_distribution()
    topic_dist = dashboard.get_topic_distribution()
    
    lines = [
        "=" * 70,
        "QUALITY CONTROL DASHBOARD",
        "=" * 70,
        "",
        "OVERALL STATISTICS:",
        f"  Total Papers: {stats['total_papers']}",
        f"  Total Chunks: {stats['total_chunks']}",
        "",
        "PROCESSING STATUS:",
    ]
    
    for status, count in status_dist.items():
        pct = (count / stats['total_papers'] * 100) if stats['total_papers'] > 0 else 0
        lines.append(f"  {status:15s}: {count:4d} ({pct:5.1f}%)")
    
    lines.extend([
        "",
        "METADATA COMPLETENESS:",
        f"  With Title:    {stats['metadata_completeness']['with_title']:4d} / {stats['total_papers']:4d}",
        f"  With Authors:  {stats['metadata_completeness']['with_authors']:4d} / {stats['total_papers']:4d}",
        f"  With Date:     {stats['metadata_completeness']['with_date']:4d} / {stats['total_papers']:4d}",
        f"  With Abstract: {stats['metadata_completeness']['with_abstract']:4d} / {stats['total_papers']:4d}",
        "",
        "SUMMARY COMPLETENESS:",
        f"  With Summary:      {stats['summary_completeness']['with_summary']:4d} / {stats['total_papers']:4d}",
        f"  With Deep Summary: {stats['summary_completeness']['with_deep_summary']:4d} / {stats['total_papers']:4d}",
        "",
        "TOPIC ASSIGNMENTS:",
        f"  Tier 1: {stats['topic_assignments']['with_tier1']:4d} / {stats['total_papers']:4d}",
        f"  Tier 2: {stats['topic_assignments']['with_tier2']:4d} / {stats['total_papers']:4d}",
        f"  Tier 3: {stats['topic_assignments']['with_tier3']:4d} / {stats['total_papers']:4d}",
        "",
        "QUALITY SCORES:",
        f"  Average Score: {quality_dist['average_score']:.2f}",
    ])
    
    for category, count in quality_dist['distribution'].items():
        pct = (count / stats['total_papers'] * 100) if stats['total_papers'] > 0 else 0
        lines.append(f"  {category:20s}: {count:4d} ({pct:5.1f}%)")
    
    if not isinstance(topic_dist, dict) or "error" in topic_dist:
        lines.extend([
            "",
            "TOPIC DISTRIBUTION: Not available",
        ])
    else:
        lines.extend([
            "",
            f"TOPIC DISTRIBUTION:",
            f"  Unclassified: {topic_dist['unclassified']}",
            f"  Tier 1 topics: {len(topic_dist['tier1'])}",
            f"  Tier 2 topics: {len(topic_dist['tier2'])}",
            f"  Tier 3 topics: {len(topic_dist['tier3'])}",
        ])
    
    lines.append("=" * 70)
    
    return "\n".join(lines)


# =============================================================================
# Step 14.2: Data Quality Checks
# =============================================================================

class DataQualityChecker:
    """
    Performs comprehensive data quality checks on the corpus.
    """
    
    def __init__(self, state: GraphState):
        """
        Initialize data quality checker.
        
        Args:
            state: Current GraphState
        """
        self.state = state
        self.papers = state.get("papers", {})
        self.chunks = state.get("chunks", {})
        self.logger = logging.getLogger(f"{__name__}.DataQualityChecker")
    
    def verify_all_pdfs_processed(self) -> Dict[str, Any]:
        """
        Verify that all discovered PDFs have been processed.
        
        Returns:
            Dictionary with verification results
        """
        total_papers = len(self.papers)
        pending = sum(1 for p in self.papers.values() if p.processing_status == "pending")
        failed = sum(1 for p in self.papers.values() if p.processing_status == "failed")
        processed = total_papers - pending
        
        return {
            "total_papers": total_papers,
            "processed": processed,
            "pending": pending,
            "failed": failed,
            "all_processed": pending == 0,
            "success_rate": (processed / total_papers * 100) if total_papers > 0 else 0,
        }
    
    def check_missing_metadata(self) -> Dict[str, Any]:
        """
        Check for papers with missing metadata fields.
        
        Returns:
            Dictionary with missing metadata analysis
        """
        missing_fields = defaultdict(list)
        
        for paper in self.papers.values():
            if not paper.title:
                missing_fields["title"].append(paper.id)
            if not paper.authors:
                missing_fields["authors"].append(paper.id)
            if not paper.publish_date:
                missing_fields["publish_date"].append(paper.id)
            if not paper.venue:
                missing_fields["venue"].append(paper.id)
            if not paper.doi and not paper.arxiv_id:
                missing_fields["external_id"].append(paper.id)
        
        return {
            "missing_counts": {field: len(ids) for field, ids in missing_fields.items()},
            "missing_details": {field: ids for field, ids in missing_fields.items()},
            "papers_with_complete_metadata": len(self.papers) - len(set(
                paper_id for ids in missing_fields.values() for paper_id in ids
            )),
        }
    
    def validate_embedding_integrity(self) -> Dict[str, Any]:
        """
        Validate that embeddings exist and are consistent.
        
        Returns:
            Dictionary with embedding validation results
        """
        faiss_index_path = self.state.get("faiss_index_path")
        faiss_meta_path = self.state.get("faiss_meta_path")
        
        # Check if index files exist
        index_exists = faiss_index_path and Path(faiss_index_path).exists() if faiss_index_path else False
        meta_exists = faiss_meta_path and Path(faiss_meta_path).exists() if faiss_meta_path else False
        
        # Count chunks
        total_chunks = sum(len(chunks) for chunks in self.chunks.values())
        papers_with_chunks = len([p for p in self.papers.keys() if p in self.chunks])
        
        return {
            "index_file_exists": index_exists,
            "metadata_file_exists": meta_exists,
            "total_chunks": total_chunks,
            "papers_with_chunks": papers_with_chunks,
            "papers_without_chunks": len(self.papers) - papers_with_chunks,
            "avg_chunks_per_paper": total_chunks / len(self.papers) if self.papers else 0,
            "integrity_status": "OK" if (index_exists and meta_exists and total_chunks > 0) else "ISSUES",
        }
    
    def check_summary_completeness(self) -> Dict[str, Any]:
        """
        Check completeness of summaries for papers.
        
        Returns:
            Dictionary with summary completeness analysis
        """
        papers_needing_summary = [
            p for p in self.papers.values()
            if p.processing_status in ["summarized", "classified", "deep_analyzed"]
        ]
        
        with_summary = sum(1 for p in papers_needing_summary if p.full_summary)
        with_deep_summary = sum(1 for p in papers_needing_summary if p.deep_summary)
        
        missing_summary = [
            p.id for p in papers_needing_summary if not p.full_summary
        ]
        
        return {
            "papers_needing_summary": len(papers_needing_summary),
            "with_summary": with_summary,
            "with_deep_summary": with_deep_summary,
            "missing_summary": len(missing_summary),
            "missing_summary_ids": missing_summary,
            "completeness_rate": (with_summary / len(papers_needing_summary) * 100) 
                if papers_needing_summary else 100,
        }
    
    def verify_topic_assignments(self) -> Dict[str, Any]:
        """
        Verify that papers have appropriate topic assignments.
        
        Returns:
            Dictionary with topic assignment verification
        """
        papers_needing_classification = [
            p for p in self.papers.values()
            if p.processing_status == "classified"
        ]
        
        with_tier1 = sum(1 for p in papers_needing_classification if p.tier1_topic)
        with_tier2 = sum(1 for p in papers_needing_classification if p.tier2_topic)
        with_tier3 = sum(1 for p in papers_needing_classification if p.tier3_topic)
        
        missing_tier1 = [
            p.id for p in papers_needing_classification if not p.tier1_topic
        ]
        
        # Check confidence scores
        low_confidence_tier1 = [
            p.id for p in papers_needing_classification
            if p.tier1_confidence is not None and p.tier1_confidence < 0.5
        ]
        
        return {
            "papers_needing_classification": len(papers_needing_classification),
            "with_tier1": with_tier1,
            "with_tier2": with_tier2,
            "with_tier3": with_tier3,
            "missing_tier1": len(missing_tier1),
            "missing_tier1_ids": missing_tier1,
            "low_confidence_tier1": len(low_confidence_tier1),
            "low_confidence_tier1_ids": low_confidence_tier1,
            "classification_rate": (with_tier1 / len(papers_needing_classification) * 100)
                if papers_needing_classification else 100,
        }


def verify_pdfs_processed(state: GraphState) -> Dict[str, Any]:
    """Verify all PDFs processed."""
    checker = DataQualityChecker(state)
    return checker.verify_all_pdfs_processed()


def check_missing_metadata(state: GraphState) -> Dict[str, Any]:
    """Check for missing metadata."""
    checker = DataQualityChecker(state)
    return checker.check_missing_metadata()


def validate_embedding_integrity(state: GraphState) -> Dict[str, Any]:
    """Validate embedding integrity."""
    checker = DataQualityChecker(state)
    return checker.validate_embedding_integrity()


def check_summary_completeness(state: GraphState) -> Dict[str, Any]:
    """Check summary completeness."""
    checker = DataQualityChecker(state)
    return checker.check_summary_completeness()


def verify_topic_assignments(state: GraphState) -> Dict[str, Any]:
    """Verify topic assignments."""
    checker = DataQualityChecker(state)
    return checker.verify_topic_assignments()


# =============================================================================
# Step 14.3: Error Analysis
# =============================================================================

class ErrorAnalyzer:
    """
    Analyzes errors across the pipeline and suggests remediation.
    """
    
    def __init__(self, state: GraphState):
        """
        Initialize error analyzer.
        
        Args:
            state: Current GraphState
        """
        self.state = state
        self.papers = state.get("papers", {})
        self.errors = state.get("errors", [])
        self.logger = logging.getLogger(f"{__name__}.ErrorAnalyzer")
    
    def list_all_failed_papers(self) -> List[Dict[str, Any]]:
        """
        List all failed papers with error details.
        
        Returns:
            List of failed paper information
        """
        failed = []
        for paper in self.papers.values():
            if paper.processing_status == "failed":
                failed.append({
                    "id": paper.id,
                    "filename": paper.filename,
                    "file_path": paper.file_path,
                    "error_stage": paper.error_stage,
                    "error_reason": paper.error_reason,
                    "retry_count": paper.retry_count,
                    "last_updated": paper.last_updated.isoformat(),
                })
        return failed
    
    def categorize_errors(self) -> Dict[str, Any]:
        """
        Categorize errors by type and stage.
        
        Returns:
            Dictionary with error categorization
        """
        error_by_stage = defaultdict(list)
        error_by_type = defaultdict(list)
        
        for paper in self.papers.values():
            if paper.processing_status == "failed":
                # Categorize by stage
                stage = paper.error_stage or "unknown"
                error_by_stage[stage].append(paper.id)
                
                # Categorize by error type (basic heuristic)
                reason = paper.error_reason or "unknown"
                if "PDF" in reason or "parse" in reason.lower():
                    error_type = "pdf_parsing"
                elif "metadata" in reason.lower():
                    error_type = "metadata_extraction"
                elif "embedding" in reason.lower():
                    error_type = "embedding_generation"
                elif "summary" in reason.lower() or "summarize" in reason.lower():
                    error_type = "summarization"
                elif "classify" in reason.lower() or "topic" in reason.lower():
                    error_type = "classification"
                elif "API" in reason or "rate limit" in reason.lower():
                    error_type = "api_error"
                elif "timeout" in reason.lower():
                    error_type = "timeout"
                else:
                    error_type = "other"
                
                error_by_type[error_type].append(paper.id)
        
        return {
            "by_stage": {stage: len(ids) for stage, ids in error_by_stage.items()},
            "by_type": {etype: len(ids) for etype, ids in error_by_type.items()},
            "stage_details": dict(error_by_stage),
            "type_details": dict(error_by_type),
            "total_failures": sum(len(ids) for ids in error_by_stage.values()),
        }
    
    def get_error_reasons(self) -> List[Tuple[str, str, int]]:
        """
        Get all unique error reasons with counts.
        
        Returns:
            List of (error_reason, error_stage, count) tuples
        """
        error_counts = defaultdict(int)
        error_stages = {}
        
        for paper in self.papers.values():
            if paper.processing_status == "failed" and paper.error_reason:
                key = paper.error_reason
                error_counts[key] += 1
                if key not in error_stages:
                    error_stages[key] = paper.error_stage or "unknown"
        
        # Sort by count descending
        sorted_errors = sorted(
            [(reason, error_stages[reason], count) for reason, count in error_counts.items()],
            key=lambda x: x[2],
            reverse=True
        )
        
        return sorted_errors
    
    def suggest_remediation(self) -> Dict[str, List[str]]:
        """
        Suggest remediation steps for common error types.
        
        Returns:
            Dictionary mapping error types to remediation suggestions
        """
        error_categories = self.categorize_errors()
        suggestions = {}
        
        for error_type, paper_ids in error_categories["type_details"].items():
            if error_type == "pdf_parsing":
                suggestions[error_type] = [
                    "Check if PDFs are corrupted or password-protected",
                    "Enable OCR fallback for scanned PDFs",
                    "Verify PDF files are accessible and readable",
                    "Try re-downloading problematic PDFs",
                ]
            elif error_type == "metadata_extraction":
                suggestions[error_type] = [
                    "Verify arXiv/DOI APIs are accessible",
                    "Check for rate limiting on external APIs",
                    "Manually add metadata for papers with extraction failures",
                    "Verify paper filenames contain valid identifiers",
                ]
            elif error_type == "embedding_generation":
                suggestions[error_type] = [
                    "Check OpenAI API key and quota",
                    "Verify embedding model is available",
                    "Reduce batch size if memory issues",
                    "Check for empty or malformed text chunks",
                ]
            elif error_type == "summarization":
                suggestions[error_type] = [
                    "Check OpenAI API key and quota",
                    "Verify GPT model availability",
                    "Reduce input length if hitting token limits",
                    "Retry with exponential backoff for transient errors",
                ]
            elif error_type == "classification":
                suggestions[error_type] = [
                    "Verify taxonomy is built and approved",
                    "Check taxonomy structure for consistency",
                    "Ensure papers have summaries before classification",
                    "Retry classification with updated taxonomy",
                ]
            elif error_type == "api_error":
                suggestions[error_type] = [
                    "Wait and retry after rate limit cooldown",
                    "Check API credentials and quotas",
                    "Implement exponential backoff strategy",
                    "Consider using batch API for large-scale processing",
                ]
            elif error_type == "timeout":
                suggestions[error_type] = [
                    "Increase timeout limits in configuration",
                    "Split large papers into smaller chunks",
                    "Check network connectivity",
                    "Retry failed papers during off-peak hours",
                ]
            else:
                suggestions[error_type] = [
                    "Review error logs for specific details",
                    "Check system resources (memory, disk space)",
                    "Verify all dependencies are installed",
                    "Manually retry failed papers",
                ]
        
        return suggestions
    
    def create_error_log(self) -> str:
        """
        Create a formatted error log.
        
        Returns:
            Formatted error log string
        """
        failed_papers = self.list_all_failed_papers()
        error_categories = self.categorize_errors()
        error_reasons = self.get_error_reasons()
        
        lines = [
            "=" * 70,
            "ERROR LOG",
            "=" * 70,
            f"Generated: {datetime.now().isoformat()}",
            f"Total Failed Papers: {len(failed_papers)}",
            "",
            "ERROR SUMMARY BY STAGE:",
        ]
        
        for stage, count in error_categories["by_stage"].items():
            lines.append(f"  {stage:20s}: {count:4d}")
        
        lines.extend([
            "",
            "ERROR SUMMARY BY TYPE:",
        ])
        
        for etype, count in error_categories["by_type"].items():
            lines.append(f"  {etype:25s}: {count:4d}")
        
        lines.extend([
            "",
            "TOP ERROR REASONS:",
        ])
        
        for reason, stage, count in error_reasons[:10]:  # Top 10
            lines.append(f"  [{stage}] {reason[:50]} ... ({count})")
        
        lines.extend([
            "",
            "FAILED PAPERS DETAILS:",
            "-" * 70,
        ])
        
        for paper_info in failed_papers:
            lines.extend([
                f"ID: {paper_info['id']}",
                f"File: {paper_info['filename']}",
                f"Stage: {paper_info['error_stage']}",
                f"Reason: {paper_info['error_reason']}",
                f"Retries: {paper_info['retry_count']}",
                "-" * 70,
            ])
        
        return "\n".join(lines)


def list_failed_papers(state: GraphState) -> List[Dict[str, Any]]:
    """List all failed papers."""
    analyzer = ErrorAnalyzer(state)
    return analyzer.list_all_failed_papers()


def categorize_error_types(state: GraphState) -> Dict[str, Any]:
    """Categorize error types."""
    analyzer = ErrorAnalyzer(state)
    return analyzer.categorize_errors()


def suggest_remediation(state: GraphState) -> Dict[str, List[str]]:
    """Suggest remediation steps."""
    analyzer = ErrorAnalyzer(state)
    return analyzer.suggest_remediation()


def export_error_log(state: GraphState, output_path: Optional[str] = None) -> str:
    """
    Export error log to file.
    
    Args:
        state: Current GraphState
        output_path: Optional path for error log file
        
    Returns:
        Path to saved error log
    """
    analyzer = ErrorAnalyzer(state)
    error_log = analyzer.create_error_log()
    
    if output_path is None:
        output_path = f"error_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(output_path, 'w') as f:
        f.write(error_log)
    
    logger.info(f"Error log exported to: {output_path}")
    return output_path


# =============================================================================
# Step 14.4: Consistency Validation
# =============================================================================

class ConsistencyValidator:
    """
    Validates consistency across the entire corpus and data structures.
    """
    
    def __init__(self, state: GraphState):
        """
        Initialize consistency validator.
        
        Args:
            state: Current GraphState
        """
        self.state = state
        self.papers = state.get("papers", {})
        self.chunks = state.get("chunks", {})
        self.taxonomy = state.get("topic_hierarchy")
        self.logger = logging.getLogger(f"{__name__}.ConsistencyValidator")
    
    def check_taxonomy_consistency(self) -> Dict[str, Any]:
        """
        Check taxonomy consistency and structure.
        
        Returns:
            Dictionary with consistency check results
        """
        if not self.taxonomy:
            return {
                "status": "NO_TAXONOMY",
                "message": "No taxonomy found",
                "issues": [],
            }
        
        # Use built-in validation
        validation_result = self.taxonomy.validate_hierarchy()
        
        # Additional checks
        issues = list(validation_result.get("issues", []))
        
        # Check for empty topics
        empty_topics = []
        for tier_num, tier_topics in [(1, self.taxonomy.tier1), 
                                       (2, self.taxonomy.tier2), 
                                       (3, self.taxonomy.tier3)]:
            for topic in tier_topics:
                if topic.paper_count == 0:
                    empty_topics.append(f"Tier {tier_num} topic '{topic.name}' has 0 papers")
        
        if empty_topics:
            issues.extend(empty_topics)
        
        return {
            "status": "VALID" if validation_result["valid"] else "INVALID",
            "validation_result": validation_result,
            "additional_issues": empty_topics,
            "all_issues": issues,
        }
    
    def validate_hierarchical_relationships(self) -> Dict[str, Any]:
        """
        Validate hierarchical relationships in taxonomy and paper classifications.
        
        Returns:
            Dictionary with validation results
        """
        if not self.taxonomy:
            return {
                "status": "NO_TAXONOMY",
                "issues": [],
            }
        
        issues = []
        
        # Check paper classifications match taxonomy
        for paper in self.papers.values():
            if paper.processing_status == "classified":
                # Verify tier1 exists
                if paper.tier1_topic:
                    topic = self.taxonomy.get_topic_by_id(paper.tier1_topic)
                    if not topic:
                        issues.append(f"Paper {paper.id} has invalid tier1_topic: {paper.tier1_topic}")
                
                # Verify tier2 exists and has correct parent
                if paper.tier2_topic:
                    topic = self.taxonomy.get_topic_by_id(paper.tier2_topic)
                    if not topic:
                        issues.append(f"Paper {paper.id} has invalid tier2_topic: {paper.tier2_topic}")
                    elif topic.parent_id != paper.tier1_topic:
                        issues.append(f"Paper {paper.id} tier2 parent mismatch")
                
                # Verify tier3 exists and has correct parent
                if paper.tier3_topic:
                    topic = self.taxonomy.get_topic_by_id(paper.tier3_topic)
                    if not topic:
                        issues.append(f"Paper {paper.id} has invalid tier3_topic: {paper.tier3_topic}")
                    elif topic.parent_id != paper.tier2_topic:
                        issues.append(f"Paper {paper.id} tier3 parent mismatch")
        
        return {
            "status": "VALID" if len(issues) == 0 else "ISSUES_FOUND",
            "issues": issues,
            "issues_count": len(issues),
        }
    
    def verify_paper_counts(self) -> Dict[str, Any]:
        """
        Verify paper counts are consistent across data structures.
        
        Returns:
            Dictionary with count verification results
        """
        # Count papers in different structures
        papers_dict_count = len(self.papers)
        papers_pending_count = len(self.state.get("papers_pending", []))
        papers_completed_count = len(self.state.get("papers_completed", []))
        papers_failed_count = len(self.state.get("papers_failed", []))
        
        queue_total = papers_pending_count + papers_completed_count + papers_failed_count
        
        # Count papers in chunks
        papers_with_chunks = len(self.chunks)
        
        # Count papers in taxonomy
        if self.taxonomy:
            taxonomy_total = sum(t.paper_count for t in self.taxonomy.tier1)
        else:
            taxonomy_total = None
        
        # Check for discrepancies
        issues = []
        
        if queue_total != papers_dict_count:
            issues.append(f"Queue count ({queue_total}) != papers dict count ({papers_dict_count})")
        
        if papers_with_chunks > papers_dict_count:
            issues.append(f"More chunks ({papers_with_chunks}) than papers ({papers_dict_count})")
        
        if taxonomy_total is not None:
            classified_count = sum(1 for p in self.papers.values() if p.tier1_topic)
            if taxonomy_total != classified_count:
                issues.append(f"Taxonomy count ({taxonomy_total}) != classified papers ({classified_count})")
        
        return {
            "papers_dict": papers_dict_count,
            "papers_pending": papers_pending_count,
            "papers_completed": papers_completed_count,
            "papers_failed": papers_failed_count,
            "queue_total": queue_total,
            "papers_with_chunks": papers_with_chunks,
            "taxonomy_total": taxonomy_total,
            "consistent": len(issues) == 0,
            "issues": issues,
        }
    
    def check_orphaned_records(self) -> Dict[str, Any]:
        """
        Check for orphaned chunks or papers.
        
        Returns:
            Dictionary with orphaned records information
        """
        # Find chunks without corresponding papers
        orphaned_chunks = []
        for paper_id in self.chunks.keys():
            if paper_id not in self.papers:
                orphaned_chunks.append(paper_id)
        
        # Find papers in queue lists that don't exist
        orphaned_in_pending = [
            pid for pid in self.state.get("papers_pending", [])
            if pid not in self.papers
        ]
        orphaned_in_completed = [
            pid for pid in self.state.get("papers_completed", [])
            if pid not in self.papers
        ]
        orphaned_in_failed = [
            pid for pid in self.state.get("papers_failed", [])
            if pid not in self.papers
        ]
        
        total_orphaned = (
            len(orphaned_chunks) + 
            len(orphaned_in_pending) + 
            len(orphaned_in_completed) + 
            len(orphaned_in_failed)
        )
        
        return {
            "has_orphaned_records": total_orphaned > 0,
            "orphaned_chunks": orphaned_chunks,
            "orphaned_in_pending": orphaned_in_pending,
            "orphaned_in_completed": orphaned_in_completed,
            "orphaned_in_failed": orphaned_in_failed,
            "total_orphaned": total_orphaned,
        }
    
    def validate_timestamps(self) -> Dict[str, Any]:
        """
        Validate timestamp sequences are logical.
        
        Returns:
            Dictionary with timestamp validation results
        """
        issues = []
        
        for paper in self.papers.values():
            # Check that last_updated >= created_at
            if paper.last_updated < paper.created_at:
                issues.append(f"Paper {paper.id}: last_updated before created_at")
            
            # Check that timestamps are not in the future
            now = datetime.now()
            if paper.created_at > now:
                issues.append(f"Paper {paper.id}: created_at in the future")
            if paper.last_updated > now:
                issues.append(f"Paper {paper.id}: last_updated in the future")
        
        # Check taxonomy timestamp
        if self.taxonomy:
            if self.taxonomy.created_at > datetime.now():
                issues.append("Taxonomy: created_at in the future")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "issues_count": len(issues),
        }


def check_taxonomy_consistency(state: GraphState) -> Dict[str, Any]:
    """Check taxonomy consistency."""
    validator = ConsistencyValidator(state)
    return validator.check_taxonomy_consistency()


def validate_hierarchical_relationships(state: GraphState) -> Dict[str, Any]:
    """Validate hierarchical relationships."""
    validator = ConsistencyValidator(state)
    return validator.validate_hierarchical_relationships()


def verify_paper_counts(state: GraphState) -> Dict[str, Any]:
    """Verify paper counts."""
    validator = ConsistencyValidator(state)
    return validator.verify_paper_counts()


def check_orphaned_records(state: GraphState) -> Dict[str, Any]:
    """Check for orphaned records."""
    validator = ConsistencyValidator(state)
    return validator.check_orphaned_records()


def validate_timestamp_sequences(state: GraphState) -> Dict[str, Any]:
    """Validate timestamp sequences."""
    validator = ConsistencyValidator(state)
    return validator.validate_timestamps()


# =============================================================================
# Step 14.5: QC Report Generation
# =============================================================================

class QCReportGenerator:
    """
    Generates comprehensive QC reports in multiple formats.
    """
    
    def __init__(self, state: GraphState):
        """
        Initialize QC report generator.
        
        Args:
            state: Current GraphState
        """
        self.state = state
        self.logger = logging.getLogger(f"{__name__}.QCReportGenerator")
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive QC report with all validation results.
        
        Returns:
            Dictionary containing all QC results
        """
        # Run all checks
        dashboard = QCDashboard(self.state)
        data_checker = DataQualityChecker(self.state)
        error_analyzer = ErrorAnalyzer(self.state)
        consistency_validator = ConsistencyValidator(self.state)
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "corpus_info": {
                "total_papers": len(self.state.get("papers", {})),
                "total_chunks": sum(len(c) for c in self.state.get("chunks", {}).values()),
                "current_phase": self.state.get("current_phase", "unknown"),
            },
            "dashboard": {
                "overall_statistics": dashboard.get_overall_statistics(),
                "status_distribution": dashboard.get_status_distribution(),
                "quality_scores": dashboard.get_quality_score_distribution(),
                "topic_distribution": dashboard.get_topic_distribution(),
            },
            "data_quality": {
                "pdfs_processed": data_checker.verify_all_pdfs_processed(),
                "missing_metadata": data_checker.check_missing_metadata(),
                "embedding_integrity": data_checker.validate_embedding_integrity(),
                "summary_completeness": data_checker.check_summary_completeness(),
                "topic_assignments": data_checker.verify_topic_assignments(),
            },
            "error_analysis": {
                "failed_papers": error_analyzer.list_all_failed_papers(),
                "error_categorization": error_analyzer.categorize_errors(),
                "error_reasons": error_analyzer.get_error_reasons(),
                "remediation_suggestions": error_analyzer.suggest_remediation(),
            },
            "consistency_validation": {
                "taxonomy_consistency": consistency_validator.check_taxonomy_consistency(),
                "hierarchical_relationships": consistency_validator.validate_hierarchical_relationships(),
                "paper_counts": consistency_validator.verify_paper_counts(),
                "orphaned_records": consistency_validator.check_orphaned_records(),
                "timestamp_validation": consistency_validator.validate_timestamps(),
            },
            "recommendations": self._generate_recommendations(),
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """
        Generate recommendations based on QC results.
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Check data quality
        data_checker = DataQualityChecker(self.state)
        
        pdf_status = data_checker.verify_all_pdfs_processed()
        if pdf_status["pending"] > 0:
            recommendations.append(f"Complete processing of {pdf_status['pending']} pending papers")
        
        metadata_status = data_checker.check_missing_metadata()
        for field, count in metadata_status["missing_counts"].items():
            if count > 0:
                recommendations.append(f"Extract missing {field} for {count} papers")
        
        summary_status = data_checker.check_summary_completeness()
        if summary_status["missing_summary"]:
            recommendations.append(f"Generate summaries for {summary_status['missing_summary']} papers")
        
        # Check errors
        error_analyzer = ErrorAnalyzer(self.state)
        failed = error_analyzer.list_all_failed_papers()
        if failed:
            recommendations.append(f"Review and retry {len(failed)} failed papers")
        
        # Check consistency
        consistency_validator = ConsistencyValidator(self.state)
        
        orphaned = consistency_validator.check_orphaned_records()
        if orphaned["has_orphaned_records"]:
            recommendations.append(f"Clean up {orphaned['total_orphaned']} orphaned records")
        
        counts = consistency_validator.verify_paper_counts()
        if not counts["consistent"]:
            recommendations.append("Resolve paper count inconsistencies")
        
        if not recommendations:
            recommendations.append("All quality checks passed! Corpus is in good shape.")
        
        return recommendations
    
    def format_as_markdown(self, report: Dict[str, Any]) -> str:
        """
        Format QC report as Markdown.
        
        Args:
            report: QC report dictionary
            
        Returns:
            Markdown formatted report
        """
        lines = [
            "# Quality Control Report",
            "",
            f"**Generated:** {report['generated_at']}",
            "",
            "## Corpus Overview",
            "",
            f"- **Total Papers:** {report['corpus_info']['total_papers']}",
            f"- **Total Chunks:** {report['corpus_info']['total_chunks']}",
            f"- **Current Phase:** {report['corpus_info']['current_phase']}",
            "",
            "## Processing Status Distribution",
            "",
        ]
        
        for status, count in report['dashboard']['status_distribution'].items():
            pct = (count / report['corpus_info']['total_papers'] * 100) if report['corpus_info']['total_papers'] > 0 else 0
            lines.append(f"- **{status}:** {count} ({pct:.1f}%)")
        
        lines.extend([
            "",
            "## Quality Scores",
            "",
            f"- **Average Score:** {report['dashboard']['quality_scores']['average_score']:.2f}",
            "",
        ])
        
        for category, count in report['dashboard']['quality_scores']['distribution'].items():
            lines.append(f"- **{category}:** {count}")
        
        lines.extend([
            "",
            "## Data Quality Summary",
            "",
            "### PDF Processing",
            "",
            f"- Processed: {report['data_quality']['pdfs_processed']['processed']} / {report['data_quality']['pdfs_processed']['total_papers']}",
            f"- Success Rate: {report['data_quality']['pdfs_processed']['success_rate']:.1f}%",
            f"- Failed: {report['data_quality']['pdfs_processed']['failed']}",
            "",
            "### Metadata Completeness",
            "",
        ])
        
        for field, count in report['data_quality']['missing_metadata']['missing_counts'].items():
            lines.append(f"- Missing {field}: {count}")
        
        lines.extend([
            "",
            "### Embedding Integrity",
            "",
            f"- Status: {report['data_quality']['embedding_integrity']['integrity_status']}",
            f"- Total Chunks: {report['data_quality']['embedding_integrity']['total_chunks']}",
            f"- Papers with Chunks: {report['data_quality']['embedding_integrity']['papers_with_chunks']}",
            "",
            "## Error Analysis",
            "",
            f"**Total Failed Papers:** {len(report['error_analysis']['failed_papers'])}",
            "",
            "### Errors by Type",
            "",
        ])
        
        for error_type, count in report['error_analysis']['error_categorization']['by_type'].items():
            lines.append(f"- **{error_type}:** {count}")
        
        lines.extend([
            "",
            "## Consistency Validation",
            "",
            f"- **Taxonomy Status:** {report['consistency_validation']['taxonomy_consistency']['status']}",
            f"- **Paper Counts Consistent:** {report['consistency_validation']['paper_counts']['consistent']}",
            f"- **Has Orphaned Records:** {report['consistency_validation']['orphaned_records']['has_orphaned_records']}",
            f"- **Timestamps Valid:** {report['consistency_validation']['timestamp_validation']['valid']}",
            "",
            "## Recommendations",
            "",
        ])
        
        for i, rec in enumerate(report['recommendations'], 1):
            lines.append(f"{i}. {rec}")
        
        lines.extend([
            "",
            "---",
            "",
            "*End of Quality Control Report*",
        ])
        
        return "\n".join(lines)
    
    def format_as_html(self, report: Dict[str, Any]) -> str:
        """
        Format QC report as HTML.
        
        Args:
            report: QC report dictionary
            
        Returns:
            HTML formatted report
        """
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Quality Control Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #ccc; padding-bottom: 5px; }}
        .metric {{ margin: 10px 0; }}
        .good {{ color: green; }}
        .warning {{ color: orange; }}
        .error {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .recommendation {{ background-color: #ffffcc; padding: 10px; margin: 5px 0; border-left: 4px solid #ffeb3b; }}
    </style>
</head>
<body>
    <h1>Quality Control Report</h1>
    <p><strong>Generated:</strong> {report['generated_at']}</p>
    
    <h2>Corpus Overview</h2>
    <div class="metric">Total Papers: {report['corpus_info']['total_papers']}</div>
    <div class="metric">Total Chunks: {report['corpus_info']['total_chunks']}</div>
    <div class="metric">Current Phase: {report['corpus_info']['current_phase']}</div>
    
    <h2>Processing Status Distribution</h2>
    <table>
        <tr><th>Status</th><th>Count</th><th>Percentage</th></tr>
"""
        
        for status, count in report['dashboard']['status_distribution'].items():
            pct = (count / report['corpus_info']['total_papers'] * 100) if report['corpus_info']['total_papers'] > 0 else 0
            html += f"        <tr><td>{status}</td><td>{count}</td><td>{pct:.1f}%</td></tr>\n"
        
        html += """
    </table>
    
    <h2>Quality Scores</h2>
"""
        
        avg_score = report['dashboard']['quality_scores']['average_score']
        score_class = "good" if avg_score >= 0.8 else "warning" if avg_score >= 0.6 else "error"
        
        html += f'    <div class="metric {score_class}">Average Quality Score: {avg_score:.2f}</div>\n'
        html += '    <table>\n        <tr><th>Category</th><th>Count</th></tr>\n'
        
        for category, count in report['dashboard']['quality_scores']['distribution'].items():
            html += f"        <tr><td>{category}</td><td>{count}</td></tr>\n"
        
        html += """
    </table>
    
    <h2>Recommendations</h2>
"""
        
        for i, rec in enumerate(report['recommendations'], 1):
            html += f'    <div class="recommendation">{i}. {rec}</div>\n'
        
        html += """
    <hr>
    <p><em>End of Quality Control Report</em></p>
</body>
</html>
"""
        
        return html


def generate_qc_report(state: GraphState) -> Dict[str, Any]:
    """
    Generate comprehensive QC report.
    
    Args:
        state: Current GraphState
        
    Returns:
        QC report dictionary
    """
    generator = QCReportGenerator(state)
    return generator.generate_comprehensive_report()


def export_report_markdown(
    state: GraphState,
    output_path: Optional[str] = None
) -> str:
    """
    Export QC report as Markdown.
    
    Args:
        state: Current GraphState
        output_path: Optional path for report file
        
    Returns:
        Path to saved report
    """
    generator = QCReportGenerator(state)
    report = generator.generate_comprehensive_report()
    markdown = generator.format_as_markdown(report)
    
    if output_path is None:
        output_path = f"qc_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(output_path, 'w') as f:
        f.write(markdown)
    
    logger.info(f"QC report exported to: {output_path}")
    return output_path


def export_report_html(
    state: GraphState,
    output_path: Optional[str] = None
) -> str:
    """
    Export QC report as HTML.
    
    Args:
        state: Current GraphState
        output_path: Optional path for report file
        
    Returns:
        Path to saved report
    """
    generator = QCReportGenerator(state)
    report = generator.generate_comprehensive_report()
    html = generator.format_as_html(report)
    
    if output_path is None:
        output_path = f"qc_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    logger.info(f"QC report exported to: {output_path}")
    return output_path


def save_report_to_drive(
    state: GraphState,
    drive_path: str,
    format: str = "markdown"
) -> str:
    """
    Save QC report to Google Drive.
    
    Args:
        state: Current GraphState
        drive_path: Google Drive path for report
        format: Report format ('markdown' or 'html')
        
    Returns:
        Path to saved report
    """
    import shutil
    
    # Generate report locally
    if format == "markdown":
        local_path = export_report_markdown(state)
    elif format == "html":
        local_path = export_report_html(state)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    # Copy to Drive
    drive_report_path = Path(drive_path) / Path(local_path).name
    
    try:
        shutil.copy(local_path, drive_report_path)
        logger.info(f"QC report saved to Drive: {drive_report_path}")
        return str(drive_report_path)
    except Exception as e:
        logger.error(f"Failed to save report to Drive: {e}")
        raise
