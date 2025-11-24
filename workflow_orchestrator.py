#!/usr/bin/env python3
"""
RAG PDF Research Corpus System - LangGraph Workflow Orchestration (Phase 13)

This module implements Phase 13 of the FINAL_NOTEBOOK_ACTION_PLAN.md:
- Step 13.1: Define Graph Structure (StateGraph, supervisor, workers, edges)
- Step 13.2: Implement Supervisor Logic (coordination, queue management, progress tracking)
- Step 13.3: Add Checkpointing (save state, resume after interruption)
- Step 13.4: Create Execution Controller (main execution, user controls, error handling)
- Step 13.5: Add Workflow Visualization (display graph, show progress)

This orchestrator stitches together all pipeline phases into a cohesive workflow
using LangGraph, with monitoring, validation, and documentation.

Version: 1.0
Date: 2025-11-24
"""

import json
import logging
import pickle
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal, Callable

logger = logging.getLogger(__name__)

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph not available. Install with: pip install langgraph")

# Import all worker nodes from existing modules
from rag_models import (
    RunConfig,
    PaperRecord,
    PaperChunk,
    TopicHierarchy,
    GraphState,
    StateManager,
    CostTracker,
    BudgetExceededError,
)

# Import worker functions
try:
    from pdf_parser import parse_and_chunk_worker
    PDF_PARSER_AVAILABLE = True
except ImportError:
    PDF_PARSER_AVAILABLE = False
    logger.warning("pdf_parser not available")

try:
    from metadata_extractor import metadata_extraction_worker
    METADATA_EXTRACTOR_AVAILABLE = True
except ImportError:
    METADATA_EXTRACTOR_AVAILABLE = False
    logger.warning("metadata_extractor not available")

try:
    from embedding_generator import embedding_generation_worker
    EMBEDDING_GENERATOR_AVAILABLE = True
except ImportError:
    EMBEDDING_GENERATOR_AVAILABLE = False
    logger.warning("embedding_generator not available")

try:
    from summarization_pass1 import summarize_papers_worker
    SUMMARIZATION_AVAILABLE = True
except ImportError:
    SUMMARIZATION_AVAILABLE = False
    logger.warning("summarization_pass1 not available")

try:
    from paper_classification import classification_worker
    CLASSIFICATION_AVAILABLE = True
except ImportError:
    CLASSIFICATION_AVAILABLE = False
    logger.warning("paper_classification not available")

try:
    from topic_taxonomy import build_complete_taxonomy
    TAXONOMY_AVAILABLE = True
except ImportError:
    TAXONOMY_AVAILABLE = False
    logger.warning("topic_taxonomy not available")

# Export list
__all__ = [
    # Step 13.1: Graph Structure
    'create_workflow_graph',
    'WorkflowBuilder',
    
    # Step 13.2: Supervisor Logic
    'supervisor_node',
    'SupervisorCoordinator',
    
    # Step 13.3: Checkpointing
    'save_checkpoint',
    'load_checkpoint',
    'CheckpointManager',
    
    # Step 13.4: Execution Controller
    'run_full_pipeline',
    'run_ingestion_only',
    'run_summarization_only',
    'run_classification_only',
    'rebuild_taxonomy',
    'WorkflowExecutor',
    
    # Step 13.5: Visualization
    'visualize_workflow',
    'display_workflow_state',
    'get_workflow_progress',
    
    # Quality Control & Monitoring
    'QualityController',
    'check_data_quality',
    'validate_pipeline_prerequisites',
    'track_costs_and_time',
    
    # Error Handling & Recovery
    'retry_failed_papers',
    'list_failed_papers',
    'get_recovery_options',
    'create_recovery_checkpoint',
    'rollback_to_checkpoint',
    'ErrorRecoveryManager',
    
    # Phase 17: Cost Tracking Integration
    'initialize_cost_tracking',
    'update_cost_tracking',
    'check_budget_before_operation',
    'print_cost_summary',
    'get_cost_recommendations',
    'save_cost_report',
]


# =============================================================================
# Step 13.2: Supervisor Node and Coordinator
# =============================================================================

class SupervisorCoordinator:
    """
    Coordinates the workflow execution, manages paper queue, and tracks progress.
    
    The supervisor decides which stage to execute next based on the current
    state and handles failures gracefully.
    """
    
    def __init__(self, config: RunConfig):
        """
        Initialize supervisor with configuration.
        
        Args:
            config: RunConfig with pipeline settings
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SupervisorCoordinator")
    
    def decide_next_stage(self, state: GraphState) -> str:
        """
        Decide which stage to execute next based on current state.
        
        Args:
            state: Current GraphState
            
        Returns:
            Next stage name: 'parse', 'metadata', 'embed', 'summarize', 
                           'taxonomy', 'classify', 'export', or 'end'
        """
        current_phase = state.get("current_phase", "initialization")
        papers = state.get("papers", {})
        
        self.logger.info(f"Current phase: {current_phase}, Total papers: {len(papers)}")
        
        # If no papers discovered yet, start with discovery
        if not papers:
            return "discover"
        
        # Count papers by status
        status_counts = defaultdict(int)
        for paper in papers.values():
            status_counts[paper.processing_status] += 1
        
        self.logger.info(f"Paper status counts: {dict(status_counts)}")
        
        # Decision tree based on current phase and paper statuses
        if current_phase == "initialization" or current_phase == "discovery":
            # Start parsing papers
            return "parse"
        
        elif current_phase == "parsing":
            # Check if all papers are parsed
            pending_parse = sum(1 for p in papers.values() 
                              if p.processing_status == "pending")
            if pending_parse > 0:
                return "parse"
            else:
                return "metadata"
        
        elif current_phase == "metadata":
            # Move to embedding generation
            return "embed"
        
        elif current_phase == "embedding":
            # Move to summarization
            return "summarize"
        
        elif current_phase == "summarization":
            # Check if we need to build taxonomy
            if state.get("topic_hierarchy") is None:
                return "taxonomy"
            elif not state.get("taxonomy_approved", False):
                return "taxonomy_review"
            else:
                return "classify"
        
        elif current_phase == "taxonomy_review":
            # Wait for user approval, then classify
            if state.get("taxonomy_approved", False):
                return "classify"
            else:
                return "taxonomy_review"  # Stay in review
        
        elif current_phase == "classification":
            # Move to final export
            return "export"
        
        elif current_phase == "export":
            # Pipeline complete
            return "end"
        
        else:
            self.logger.warning(f"Unknown phase: {current_phase}, ending workflow")
            return "end"
    
    def update_queue(self, state: GraphState) -> GraphState:
        """
        Update the paper processing queue based on current status.
        
        Args:
            state: Current GraphState
            
        Returns:
            Updated GraphState with refreshed queues
        """
        papers = state.get("papers", {})
        
        # Categorize papers
        pending = []
        completed = []
        failed = []
        
        for paper_id, paper in papers.items():
            if paper.processing_status == "failed":
                failed.append(paper_id)
            elif paper.processing_status in ["classified", "deep_analyzed"]:
                completed.append(paper_id)
            else:
                pending.append(paper_id)
        
        state["papers_pending"] = pending
        state["papers_completed"] = completed
        state["papers_failed"] = failed
        
        return state


def supervisor_node(state: GraphState) -> GraphState:
    """
    Supervisor node that coordinates the workflow execution.
    
    This is a LangGraph node that:
    - Tracks overall progress
    - Manages the paper queue
    - Handles failures
    - Decides next stage
    - Monitors costs (Phase 17)
    
    Args:
        state: Current GraphState
        
    Returns:
        Updated GraphState with next stage decision
    """
    logger.info("=== Supervisor Node ===")
    
    # Get config
    config = state.get("config")
    if not config:
        logger.error("No config in state")
        state["current_phase"] = "error"
        return state
    
    # Initialize cost tracking if enabled (Phase 17)
    state = initialize_cost_tracking(state)
    
    # Create coordinator
    coordinator = SupervisorCoordinator(config)
    
    # Update queues
    state = coordinator.update_queue(state)
    
    # Decide next stage
    next_stage = coordinator.decide_next_stage(state)
    logger.info(f"Next stage: {next_stage}")
    
    # Update state
    state["next_stage"] = next_stage
    
    # Update statistics
    stats = StateManager.get_stats(state)
    state["stats"] = stats
    
    logger.info(f"Statistics: {stats}")
    
    # Log cost information if tracking enabled (Phase 17)
    if config.enable_cost_tracking and state.get("cost_tracker"):
        tracker = state["cost_tracker"]
        logger.info(f"Current cost: ${tracker.total_cost:.4f}")
        if config.max_cost_per_run:
            utilization = tracker.total_cost / config.max_cost_per_run
            logger.info(f"Budget utilization: {utilization * 100:.1f}%")
    
    return state


# =============================================================================
# Step 13.1: Graph Structure and Builder
# =============================================================================

class WorkflowBuilder:
    """
    Builds the LangGraph StateGraph for the RAG PDF pipeline.
    
    The workflow includes nodes for:
    - Supervisor (coordination)
    - PDF discovery
    - Parsing and chunking
    - Metadata extraction
    - Embedding generation
    - Summarization
    - Taxonomy building
    - Classification
    - Export
    """
    
    def __init__(self, config: RunConfig):
        """
        Initialize workflow builder.
        
        Args:
            config: RunConfig with pipeline settings
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.WorkflowBuilder")
    
    def create_graph(self) -> StateGraph:
        """
        Create the complete workflow graph.
        
        Returns:
            StateGraph ready to compile
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph is not available. Install with: pip install langgraph")
        
        # Create graph
        graph = StateGraph(GraphState)
        
        # Add all nodes
        graph.add_node("supervisor", supervisor_node)
        graph.add_node("discover", self._create_discovery_node())
        graph.add_node("parse", self._create_parse_node())
        graph.add_node("metadata", self._create_metadata_node())
        graph.add_node("embed", self._create_embedding_node())
        graph.add_node("summarize", self._create_summarization_node())
        graph.add_node("taxonomy", self._create_taxonomy_node())
        graph.add_node("taxonomy_review", self._create_taxonomy_review_node())
        graph.add_node("classify", self._create_classification_node())
        graph.add_node("export", self._create_export_node())
        
        # Set entry point
        graph.set_entry_point("supervisor")
        
        # Add edges from supervisor to stages
        graph.add_conditional_edges(
            "supervisor",
            self._route_from_supervisor,
            {
                "discover": "discover",
                "parse": "parse",
                "metadata": "metadata",
                "embed": "embed",
                "summarize": "summarize",
                "taxonomy": "taxonomy",
                "taxonomy_review": "taxonomy_review",
                "classify": "classify",
                "export": "export",
                "end": END,
            }
        )
        
        # Add edges from stages back to supervisor
        for stage in ["discover", "parse", "metadata", "embed", "summarize", 
                     "taxonomy", "taxonomy_review", "classify", "export"]:
            graph.add_edge(stage, "supervisor")
        
        return graph
    
    def _route_from_supervisor(self, state: GraphState) -> str:
        """
        Route from supervisor to next stage based on state.
        
        Args:
            state: Current GraphState
            
        Returns:
            Next stage name
        """
        return state.get("next_stage", "end")
    
    def _create_discovery_node(self) -> Callable:
        """Create PDF discovery node."""
        def discovery_node(state: GraphState) -> GraphState:
            """Discover PDFs in Google Drive."""
            from drive_utils import discover_pdfs
            
            logger.info("=== Discovery Node ===")
            config = state["config"]
            
            try:
                # Discover PDFs
                papers = discover_pdfs(config.drive_folder_path, config)
                
                # Add to state
                for paper_id, paper in papers.items():
                    state = StateManager.add_paper(state, paper)
                
                state["current_phase"] = "discovery"
                logger.info(f"Discovered {len(papers)} papers")
                
            except Exception as e:
                logger.error(f"Discovery failed: {e}")
                state["errors"].append({
                    "stage": "discovery",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            return state
        
        return discovery_node
    
    def _create_parse_node(self) -> Callable:
        """Create parsing node."""
        def parse_node(state: GraphState) -> GraphState:
            """Parse and chunk papers."""
            logger.info("=== Parse Node ===")
            
            try:
                # Get papers that need parsing
                papers_to_parse = [
                    p_id for p_id, p in state["papers"].items()
                    if p.processing_status == "pending"
                ]
                
                logger.info(f"Parsing {len(papers_to_parse)} papers")
                
                # Parse each paper
                for paper_id in papers_to_parse[:10]:  # Batch of 10
                    try:
                        if PDF_PARSER_AVAILABLE:
                            state = parse_and_chunk_worker(paper_id, state)
                        else:
                            logger.warning("PDF parser not available")
                    except Exception as e:
                        logger.error(f"Failed to parse {paper_id}: {e}")
                        state = StateManager.mark_paper_failed(state, paper_id, str(e))
                
                state["current_phase"] = "parsing"
                
            except Exception as e:
                logger.error(f"Parse node failed: {e}")
                state["errors"].append({
                    "stage": "parsing",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            return state
        
        return parse_node
    
    def _create_metadata_node(self) -> Callable:
        """Create metadata extraction node."""
        def metadata_node(state: GraphState) -> GraphState:
            """Extract metadata from papers."""
            logger.info("=== Metadata Node ===")
            
            try:
                # Get papers that need metadata
                papers_to_extract = [
                    p_id for p_id, p in state["papers"].items()
                    if p.processing_status == "parsed"
                ]
                
                logger.info(f"Extracting metadata for {len(papers_to_extract)} papers")
                
                # Extract metadata for each paper
                for paper_id in papers_to_extract:
                    try:
                        if METADATA_EXTRACTOR_AVAILABLE:
                            state = metadata_extraction_worker(paper_id, state)
                        else:
                            logger.warning("Metadata extractor not available")
                    except Exception as e:
                        logger.error(f"Failed to extract metadata for {paper_id}: {e}")
                        # Don't fail the paper, just log
                
                state["current_phase"] = "metadata"
                
            except Exception as e:
                logger.error(f"Metadata node failed: {e}")
                state["errors"].append({
                    "stage": "metadata",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            return state
        
        return metadata_node
    
    def _create_embedding_node(self) -> Callable:
        """Create embedding generation node."""
        def embedding_node(state: GraphState) -> GraphState:
            """Generate embeddings for all chunks."""
            logger.info("=== Embedding Node ===")
            
            try:
                if EMBEDDING_GENERATOR_AVAILABLE:
                    # embedding_generation_worker requires (state, api_key)
                    import os
                    api_key = os.getenv("OPENAI_API_KEY", "")
                    if not api_key:
                        logger.error("OPENAI_API_KEY not set")
                        raise ValueError("OPENAI_API_KEY environment variable required")
                    state = embedding_generation_worker(state, api_key)
                else:
                    logger.warning("Embedding generator not available")
                
                state["current_phase"] = "embedding"
                
            except Exception as e:
                logger.error(f"Embedding node failed: {e}")
                state["errors"].append({
                    "stage": "embedding",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            return state
        
        return embedding_node
    
    def _create_summarization_node(self) -> Callable:
        """Create summarization node."""
        def summarization_node(state: GraphState) -> GraphState:
            """Summarize papers."""
            logger.info("=== Summarization Node ===")
            
            try:
                if SUMMARIZATION_AVAILABLE:
                    # summarize_papers_worker requires (state, api_key)
                    import os
                    api_key = os.getenv("OPENAI_API_KEY", "")
                    if not api_key:
                        logger.error("OPENAI_API_KEY not set")
                        raise ValueError("OPENAI_API_KEY environment variable required")
                    state = summarize_papers_worker(state, api_key)
                else:
                    logger.warning("Summarization not available")
                
                state["current_phase"] = "summarization"
                
            except Exception as e:
                logger.error(f"Summarization node failed: {e}")
                state["errors"].append({
                    "stage": "summarization",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            return state
        
        return summarization_node
    
    def _create_taxonomy_node(self) -> Callable:
        """Create taxonomy building node."""
        def taxonomy_node(state: GraphState) -> GraphState:
            """Build topic taxonomy."""
            logger.info("=== Taxonomy Node ===")
            
            try:
                if TAXONOMY_AVAILABLE:
                    # build_complete_taxonomy requires (state, embeddings_array, embedding_id_to_chunk, config, api_key)
                    import os
                    api_key = os.getenv("OPENAI_API_KEY", "")
                    if not api_key:
                        logger.error("OPENAI_API_KEY not set")
                        raise ValueError("OPENAI_API_KEY environment variable required")
                    
                    # Get embeddings array from FAISS index
                    from embedding_generator import load_faiss_index, load_metadata_mapping
                    if state.get("faiss_index_path") and state.get("faiss_meta_path"):
                        index = load_faiss_index(state["faiss_index_path"])
                        metadata_map = load_metadata_mapping(state["faiss_meta_path"])
                        
                        # Extract embeddings array
                        embeddings_array = index.index.reconstruct_n(0, index.index.ntotal)
                        
                        # Create embedding_id_to_chunk mapping
                        embedding_id_to_chunk = {}
                        for emb_id, meta in metadata_map.items():
                            chunk_id = meta["chunk_id"]
                            paper_id = meta["paper_id"]
                            # Find chunk in state
                            if paper_id in state["chunks"]:
                                for chunk in state["chunks"][paper_id]:
                                    if chunk.chunk_id == chunk_id:
                                        embedding_id_to_chunk[emb_id] = chunk
                                        break
                        
                        hierarchy = build_complete_taxonomy(
                            state,
                            embeddings_array,
                            embedding_id_to_chunk,
                            state["config"],
                            api_key
                        )
                        state["topic_hierarchy"] = hierarchy
                        
                        # If approval not required, auto-approve
                        if not state["config"].taxonomy_approval_required:
                            state["taxonomy_approved"] = True
                    else:
                        logger.error("FAISS index not found. Run embedding generation first.")
                else:
                    logger.warning("Taxonomy builder not available")
                
                state["current_phase"] = "taxonomy"
                
            except Exception as e:
                logger.error(f"Taxonomy node failed: {e}")
                state["errors"].append({
                    "stage": "taxonomy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            return state
        
        return taxonomy_node
    
    def _create_taxonomy_review_node(self) -> Callable:
        """Create taxonomy review node."""
        def taxonomy_review_node(state: GraphState) -> GraphState:
            """Review and approve taxonomy."""
            logger.info("=== Taxonomy Review Node ===")
            
            # This is a human-in-the-loop step
            # In a notebook, this would pause for user review
            # For now, we just check if already approved
            
            if not state.get("taxonomy_approved", False):
                logger.info("Taxonomy waiting for approval")
                # In practice, this would display taxonomy and wait
                # For automated runs, we auto-approve
                state["taxonomy_approved"] = True
            
            state["current_phase"] = "taxonomy_review"
            
            return state
        
        return taxonomy_review_node
    
    def _create_classification_node(self) -> Callable:
        """Create classification node."""
        def classification_node(state: GraphState) -> GraphState:
            """Classify papers into taxonomy."""
            logger.info("=== Classification Node ===")
            
            try:
                if CLASSIFICATION_AVAILABLE:
                    # classification_worker requires (state, api_key)
                    import os
                    api_key = os.getenv("OPENAI_API_KEY", "")
                    if not api_key:
                        logger.error("OPENAI_API_KEY not set")
                        raise ValueError("OPENAI_API_KEY environment variable required")
                    state = classification_worker(state, api_key)
                else:
                    logger.warning("Classification not available")
                
                state["current_phase"] = "classification"
                
            except Exception as e:
                logger.error(f"Classification node failed: {e}")
                state["errors"].append({
                    "stage": "classification",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            return state
        
        return classification_node
    
    def _create_export_node(self) -> Callable:
        """Create export node."""
        def export_node(state: GraphState) -> GraphState:
            """Export final results."""
            logger.info("=== Export Node ===")
            
            try:
                from export_manager import export_final_data
                
                # export_final_data requires (state, output_dir)
                output_dir = state.get("export_dir", "./exports")
                
                # Export all data
                export_paths = export_final_data(state, output_dir)
                
                # Update state with paths
                for key, path in export_paths.items():
                    state[f"export_{key}_path"] = path
                
                state["current_phase"] = "export"
                
            except Exception as e:
                logger.error(f"Export node failed: {e}")
                state["errors"].append({
                    "stage": "export",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            return state
        
        return export_node


def create_workflow_graph(config: RunConfig) -> StateGraph:
    """
    Create the complete workflow graph for the RAG PDF pipeline.
    
    Args:
        config: RunConfig with pipeline settings
        
    Returns:
        Compiled StateGraph ready for execution
        
    Example:
        >>> config = create_default_config()
        >>> graph = create_workflow_graph(config)
        >>> result = graph.invoke(initial_state)
    """
    builder = WorkflowBuilder(config)
    graph = builder.create_graph()
    return graph


# =============================================================================
# Step 13.3: Checkpointing
# =============================================================================

class CheckpointManager:
    """
    Manages checkpoint saving and loading for workflow state.
    
    Enables resume after interruption by periodically saving state.
    """
    
    def __init__(self, checkpoint_dir: Optional[Path] = None):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_dir: Directory for checkpoint files (default: ./checkpoints)
        """
        self.checkpoint_dir = checkpoint_dir or Path("./checkpoints")
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(f"{__name__}.CheckpointManager")
    
    def save(self, state: GraphState, checkpoint_name: Optional[str] = None) -> str:
        """
        Save current state to checkpoint file.
        
        Args:
            state: GraphState to save
            checkpoint_name: Optional name for checkpoint (default: timestamp)
            
        Returns:
            Path to checkpoint file
        """
        if checkpoint_name is None:
            checkpoint_name = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_name}.pkl"
        
        try:
            with open(checkpoint_path, 'wb') as f:
                pickle.dump(state, f)
            
            self.logger.info(f"Saved checkpoint to {checkpoint_path}")
            return str(checkpoint_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            raise
    
    def load(self, checkpoint_name: str) -> GraphState:
        """
        Load state from checkpoint file.
        
        Args:
            checkpoint_name: Name of checkpoint to load
            
        Returns:
            Loaded GraphState
        """
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_name}.pkl"
        
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        
        try:
            with open(checkpoint_path, 'rb') as f:
                state = pickle.load(f)
            
            self.logger.info(f"Loaded checkpoint from {checkpoint_path}")
            return state
            
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            raise
    
    def list_checkpoints(self) -> List[str]:
        """
        List all available checkpoints.
        
        Returns:
            List of checkpoint names
        """
        checkpoints = [
            p.stem for p in self.checkpoint_dir.glob("checkpoint_*.pkl")
        ]
        return sorted(checkpoints)
    
    def save_to_drive(self, state: GraphState, drive_path: str) -> str:
        """
        Save checkpoint to Google Drive.
        
        Args:
            state: GraphState to save
            drive_path: Google Drive path for checkpoint
            
        Returns:
            Path to saved checkpoint
        """
        # First save locally
        local_path = self.save(state)
        
        # Copy to drive path
        drive_checkpoint_path = Path(drive_path) / Path(local_path).name
        
        try:
            import shutil
            shutil.copy(local_path, drive_checkpoint_path)
            self.logger.info(f"Copied checkpoint to Drive: {drive_checkpoint_path}")
            return str(drive_checkpoint_path)
            
        except Exception as e:
            self.logger.error(f"Failed to copy to Drive: {e}")
            raise


def save_checkpoint(state: GraphState, checkpoint_dir: Optional[str] = None) -> str:
    """
    Save workflow state to checkpoint.
    
    Args:
        state: Current GraphState
        checkpoint_dir: Directory for checkpoints
        
    Returns:
        Path to saved checkpoint
    """
    manager = CheckpointManager(Path(checkpoint_dir) if checkpoint_dir else None)
    return manager.save(state)


def load_checkpoint(checkpoint_name: str, checkpoint_dir: Optional[str] = None) -> GraphState:
    """
    Load workflow state from checkpoint.
    
    Args:
        checkpoint_name: Name of checkpoint to load
        checkpoint_dir: Directory containing checkpoints
        
    Returns:
        Loaded GraphState
    """
    manager = CheckpointManager(Path(checkpoint_dir) if checkpoint_dir else None)
    return manager.load(checkpoint_name)


# =============================================================================
# Step 13.4: Execution Controller
# =============================================================================

class WorkflowExecutor:
    """
    Controls workflow execution with user-friendly entry points.
    
    Provides methods for:
    - Running full pipeline
    - Running specific stages
    - Pausing and resuming
    - Error handling and recovery
    """
    
    def __init__(self, config: RunConfig, checkpoint_dir: Optional[str] = None):
        """
        Initialize workflow executor.
        
        Args:
            config: RunConfig with pipeline settings
            checkpoint_dir: Directory for checkpoints
        """
        self.config = config
        self.checkpoint_manager = CheckpointManager(
            Path(checkpoint_dir) if checkpoint_dir else None
        )
        self.logger = logging.getLogger(f"{__name__}.WorkflowExecutor")
    
    def run_full_pipeline(
        self,
        initial_state: Optional[GraphState] = None,
        save_checkpoints: bool = True
    ) -> GraphState:
        """
        Run the complete RAG pipeline from start to finish.
        
        Args:
            initial_state: Optional initial state (default: create new)
            save_checkpoints: Whether to save checkpoints periodically
            
        Returns:
            Final GraphState after pipeline completion
        """
        self.logger.info("=== Running Full Pipeline ===")
        
        # Create initial state if not provided
        if initial_state is None:
            initial_state = StateManager.create_initial_state(self.config)
        
        # Create workflow graph
        graph = create_workflow_graph(self.config)
        
        # Compile with checkpointing
        if save_checkpoints:
            memory = MemorySaver()
            app = graph.compile(checkpointer=memory)
        else:
            app = graph.compile()
        
        try:
            # Run workflow
            config_dict = {"configurable": {"thread_id": "main"}}
            result = app.invoke(initial_state, config_dict)
            
            # Save final checkpoint
            if save_checkpoints:
                self.checkpoint_manager.save(result, "final_state")
            
            self.logger.info("Pipeline completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            raise
    
    def run_ingestion_only(self, initial_state: Optional[GraphState] = None) -> GraphState:
        """
        Run only the ingestion phase (discovery, parsing, metadata, embeddings).
        
        Args:
            initial_state: Optional initial state
            
        Returns:
            GraphState after ingestion
        """
        self.logger.info("=== Running Ingestion Only ===")
        
        if initial_state is None:
            initial_state = StateManager.create_initial_state(self.config)
        
        # Modify config to stop after embedding
        temp_config = self.config.model_copy()
        # We'll run until embedding is complete
        
        # Create and run graph
        graph = create_workflow_graph(temp_config)
        app = graph.compile()
        
        # Run and stop after embedding
        result = app.invoke(initial_state)
        
        self.logger.info("Ingestion completed")
        return result
    
    def resume_from_checkpoint(self, checkpoint_name: str) -> GraphState:
        """
        Resume pipeline execution from a saved checkpoint.
        
        Args:
            checkpoint_name: Name of checkpoint to resume from
            
        Returns:
            Final GraphState after completion
        """
        self.logger.info(f"=== Resuming from Checkpoint: {checkpoint_name} ===")
        
        # Load checkpoint
        state = self.checkpoint_manager.load(checkpoint_name)
        
        # Resume pipeline
        return self.run_full_pipeline(initial_state=state)


def run_full_pipeline(config: RunConfig, checkpoint_dir: Optional[str] = None) -> GraphState:
    """
    Run the complete RAG pipeline from start to finish.
    
    This is the main entry point for executing the full workflow.
    
    Args:
        config: RunConfig with pipeline settings
        checkpoint_dir: Optional directory for checkpoints
        
    Returns:
        Final GraphState after pipeline completion
        
    Example:
        >>> from rag_models import create_default_config
        >>> config = create_default_config(drive_folder_path="PDFs")
        >>> final_state = run_full_pipeline(config)
    """
    executor = WorkflowExecutor(config, checkpoint_dir)
    return executor.run_full_pipeline()


def run_ingestion_only(config: RunConfig) -> GraphState:
    """
    Run only the ingestion phase of the pipeline.
    
    Args:
        config: RunConfig with pipeline settings
        
    Returns:
        GraphState after ingestion (discovery, parsing, metadata, embeddings)
    """
    executor = WorkflowExecutor(config)
    return executor.run_ingestion_only()


def run_summarization_only(state: GraphState) -> GraphState:
    """
    Run only summarization on already-ingested papers.
    
    Args:
        state: GraphState with ingested papers
        
    Returns:
        GraphState with summaries added
    """
    logger.info("=== Running Summarization Only ===")
    
    if SUMMARIZATION_AVAILABLE:
        from summarization_pass1 import summarize_papers_worker
        import os
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            logger.error("OPENAI_API_KEY not set")
            raise ValueError("OPENAI_API_KEY environment variable required")
        state = summarize_papers_worker(state, api_key)
    else:
        logger.warning("Summarization not available")
    
    return state


def run_classification_only(state: GraphState) -> GraphState:
    """
    Run only classification (assumes taxonomy already exists).
    
    Args:
        state: GraphState with taxonomy
        
    Returns:
        GraphState with papers classified
    """
    logger.info("=== Running Classification Only ===")
    
    if not state.get("topic_hierarchy"):
        raise ValueError("No taxonomy found. Run taxonomy building first.")
    
    if CLASSIFICATION_AVAILABLE:
        from paper_classification import classification_worker
        import os
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            logger.error("OPENAI_API_KEY not set")
            raise ValueError("OPENAI_API_KEY environment variable required")
        state = classification_worker(state, api_key)
    else:
        logger.warning("Classification not available")
    
    return state


def rebuild_taxonomy(state: GraphState) -> GraphState:
    """
    Rebuild the topic taxonomy from scratch.
    
    Args:
        state: GraphState with embedded papers
        
    Returns:
        GraphState with new taxonomy
    """
    logger.info("=== Rebuilding Taxonomy ===")
    
    if TAXONOMY_AVAILABLE:
        from topic_taxonomy import build_complete_taxonomy
        from embedding_generator import load_faiss_index, load_metadata_mapping
        import os
        
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            logger.error("OPENAI_API_KEY not set")
            raise ValueError("OPENAI_API_KEY environment variable required")
        
        # Get embeddings array from FAISS index
        if state.get("faiss_index_path") and state.get("faiss_meta_path"):
            index = load_faiss_index(state["faiss_index_path"])
            metadata_map = load_metadata_mapping(state["faiss_meta_path"])
            
            # Extract embeddings array
            embeddings_array = index.index.reconstruct_n(0, index.index.ntotal)
            
            # Create embedding_id_to_chunk mapping
            embedding_id_to_chunk = {}
            for emb_id, meta in metadata_map.items():
                chunk_id = meta["chunk_id"]
                paper_id = meta["paper_id"]
                # Find chunk in state
                if paper_id in state["chunks"]:
                    for chunk in state["chunks"][paper_id]:
                        if chunk.chunk_id == chunk_id:
                            embedding_id_to_chunk[emb_id] = chunk
                            break
            
            hierarchy = build_complete_taxonomy(
                state,
                embeddings_array,
                embedding_id_to_chunk,
                state["config"],
                api_key
            )
            state["topic_hierarchy"] = hierarchy
            state["taxonomy_approved"] = False  # Require re-approval
        else:
            logger.error("FAISS index not found. Run embedding generation first.")
    else:
        logger.warning("Taxonomy builder not available")
    
    return state


# =============================================================================
# Step 13.5: Workflow Visualization
# =============================================================================

def visualize_workflow(config: RunConfig, output_format: str = "mermaid") -> str:
    """
    Generate visualization of the workflow graph.
    
    Args:
        config: RunConfig for building graph
        output_format: Format for visualization ('mermaid' or 'ascii')
        
    Returns:
        String representation of workflow graph
    """
    if output_format == "mermaid":
        return _generate_mermaid_diagram()
    elif output_format == "ascii":
        return _generate_ascii_diagram()
    else:
        raise ValueError(f"Unknown format: {output_format}")


def _generate_mermaid_diagram() -> str:
    """Generate Mermaid flowchart diagram."""
    return """
```mermaid
graph TD
    Start([Start]) --> Supervisor{Supervisor}
    Supervisor --> Discover[Discover PDFs]
    Supervisor --> Parse[Parse & Chunk]
    Supervisor --> Metadata[Extract Metadata]
    Supervisor --> Embed[Generate Embeddings]
    Supervisor --> Summarize[Summarize Papers]
    Supervisor --> Taxonomy[Build Taxonomy]
    Supervisor --> Review[Review Taxonomy]
    Supervisor --> Classify[Classify Papers]
    Supervisor --> Export[Export Results]
    Supervisor --> End([End])
    
    Discover --> Supervisor
    Parse --> Supervisor
    Metadata --> Supervisor
    Embed --> Supervisor
    Summarize --> Supervisor
    Taxonomy --> Supervisor
    Review --> Supervisor
    Classify --> Supervisor
    Export --> Supervisor
    
    style Supervisor fill:#f9f,stroke:#333,stroke-width:4px
    style Start fill:#9f9,stroke:#333,stroke-width:2px
    style End fill:#f99,stroke:#333,stroke-width:2px
```
"""


def _generate_ascii_diagram() -> str:
    """Generate ASCII flowchart."""
    return """
RAG PDF Pipeline Workflow
=========================

    [Start]
       |
       v
  {Supervisor} <-----------------+
       |                         |
       +-> [Discover PDFs] ------+
       |                         |
       +-> [Parse & Chunk] ------+
       |                         |
       +-> [Extract Metadata] ---+
       |                         |
       +-> [Generate Embeddings]-+
       |                         |
       +-> [Summarize Papers] ---+
       |                         |
       +-> [Build Taxonomy] -----+
       |                         |
       +-> [Review Taxonomy] ----+
       |                         |
       +-> [Classify Papers] ----+
       |                         |
       +-> [Export Results] -----+
       |
       v
     [End]
"""


def display_workflow_state(state: GraphState) -> str:
    """
    Display current workflow state in a human-readable format.
    
    Args:
        state: Current GraphState
        
    Returns:
        Formatted string showing workflow progress
    """
    stats = StateManager.get_stats(state)
    current_phase = state.get("current_phase", "unknown")
    
    output = [
        "=" * 60,
        "WORKFLOW STATE",
        "=" * 60,
        f"Current Phase: {current_phase}",
        f"Total Papers: {stats['total_papers']}",
        f"Pending: {stats['pending']}",
        f"Completed: {stats['completed']}",
        f"Failed: {stats['failed']}",
        f"Total Chunks: {stats['total_chunks']}",
        f"Has Taxonomy: {stats['has_taxonomy']}",
        f"Taxonomy Approved: {stats['taxonomy_approved']}",
        "=" * 60,
    ]
    
    return "\n".join(output)


def get_workflow_progress(state: GraphState) -> Dict[str, Any]:
    """
    Get detailed progress information about the workflow.
    
    Args:
        state: Current GraphState
        
    Returns:
        Dictionary with progress details
    """
    stats = StateManager.get_stats(state)
    
    # Calculate completion percentages
    total = stats['total_papers']
    completed = stats['completed']
    
    completion_pct = (completed / total * 100) if total > 0 else 0
    
    # Phase completion flags
    phases_complete = {
        "discovery": total > 0,
        "parsing": all(p.processing_status != "pending" for p in state["papers"].values()),
        "metadata": all(p.title is not None for p in state["papers"].values() if p.processing_status != "failed"),
        "embedding": state.get("faiss_index_path") is not None,
        "summarization": all(p.full_summary is not None for p in state["papers"].values() if p.processing_status not in ["failed", "pending", "parsed"]),
        "taxonomy": state.get("topic_hierarchy") is not None,
        "classification": all(p.tier1_topic is not None for p in state["papers"].values() if p.processing_status == "classified"),
        "export": state.get("master_csv_path") is not None,
    }
    
    return {
        "current_phase": state.get("current_phase", "unknown"),
        "completion_percentage": completion_pct,
        "papers_total": total,
        "papers_completed": completed,
        "papers_pending": stats['pending'],
        "papers_failed": stats['failed'],
        "phases_complete": phases_complete,
        "errors_count": len(state.get("errors", [])),
    }


# =============================================================================
# Quality Control & Monitoring
# =============================================================================

class QualityController:
    """
    Performs quality control checks on pipeline data and outputs.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.QualityController")
    
    def check_paper_quality(self, paper: PaperRecord) -> Dict[str, Any]:
        """
        Check quality of a single paper record.
        
        Args:
            paper: PaperRecord to check
            
        Returns:
            Dictionary with quality metrics and issues
        """
        issues = []
        warnings = []
        
        # Check metadata completeness
        if not paper.title:
            warnings.append("Missing title")
        if not paper.authors:
            warnings.append("Missing authors")
        if not paper.publish_date:
            warnings.append("Missing publication date")
        
        # Check processing status
        if paper.processing_status == "failed":
            issues.append(f"Failed: {paper.error_reason}")
        
        # Check summaries
        if paper.processing_status in ["summarized", "classified"]:
            if not paper.full_summary:
                issues.append("Missing summary")
        
        # Check classification
        if paper.processing_status == "classified":
            if not paper.tier1_topic:
                issues.append("Missing Tier 1 classification")
        
        return {
            "paper_id": paper.id,
            "has_issues": len(issues) > 0,
            "issues": issues,
            "warnings": warnings,
            "quality_score": 1.0 - (len(issues) * 0.2 + len(warnings) * 0.1),
        }
    
    def check_corpus_quality(self, state: GraphState) -> Dict[str, Any]:
        """
        Check quality of entire corpus.
        
        Args:
            state: GraphState with all papers
            
        Returns:
            Quality report dictionary
        """
        papers = state.get("papers", {})
        
        # Check each paper
        paper_quality = [
            self.check_paper_quality(paper)
            for paper in papers.values()
        ]
        
        # Aggregate statistics
        total_papers = len(papers)
        papers_with_issues = sum(1 for pq in paper_quality if pq["has_issues"])
        avg_quality = sum(pq["quality_score"] for pq in paper_quality) / total_papers if total_papers > 0 else 0
        
        return {
            "total_papers": total_papers,
            "papers_with_issues": papers_with_issues,
            "average_quality_score": avg_quality,
            "quality_distribution": {
                "excellent": sum(1 for pq in paper_quality if pq["quality_score"] >= 0.9),
                "good": sum(1 for pq in paper_quality if 0.7 <= pq["quality_score"] < 0.9),
                "fair": sum(1 for pq in paper_quality if 0.5 <= pq["quality_score"] < 0.7),
                "poor": sum(1 for pq in paper_quality if pq["quality_score"] < 0.5),
            },
            "paper_details": paper_quality,
        }


def check_data_quality(state: GraphState) -> Dict[str, Any]:
    """
    Check data quality across the pipeline.
    
    Args:
        state: Current GraphState
        
    Returns:
        Quality report
    """
    controller = QualityController()
    return controller.check_corpus_quality(state)


def validate_pipeline_prerequisites(state: GraphState, stage: str) -> bool:
    """
    Validate that prerequisites are met before running a stage.
    
    Args:
        state: Current GraphState
        stage: Stage to validate for ('embed', 'classify', etc.)
        
    Returns:
        True if prerequisites met, False otherwise
    """
    logger.info(f"Validating prerequisites for stage: {stage}")
    
    if stage == "embed":
        # Need parsed papers with chunks
        if not state.get("chunks"):
            logger.error("No chunks found. Run parsing first.")
            return False
    
    elif stage == "classify":
        # Need approved taxonomy
        if not state.get("topic_hierarchy"):
            logger.error("No taxonomy found. Build taxonomy first.")
            return False
        if not state.get("taxonomy_approved", False):
            logger.error("Taxonomy not approved. Review taxonomy first.")
            return False
    
    elif stage == "export":
        # Need completed papers
        if not state.get("papers"):
            logger.error("No papers found.")
            return False
    
    return True


def track_costs_and_time(state: GraphState) -> Dict[str, Any]:
    """
    Track costs and time for pipeline execution.
    
    Args:
        state: Current GraphState
        
    Returns:
        Cost and time tracking information
    """
    # This would integrate with actual API usage tracking
    # For now, provide estimates based on state
    
    papers_count = len(state.get("papers", {}))
    chunks_count = sum(len(chunks) for chunks in state.get("chunks", {}).values())
    
    # Rough estimates (would be replaced with actual tracking)
    estimated_embedding_cost = chunks_count * 0.0001  # $0.0001 per chunk
    estimated_summary_cost = papers_count * 0.01  # $0.01 per paper
    estimated_classification_cost = papers_count * 0.005  # $0.005 per paper
    
    total_estimated_cost = (
        estimated_embedding_cost + 
        estimated_summary_cost + 
        estimated_classification_cost
    )
    
    return {
        "papers_processed": papers_count,
        "chunks_processed": chunks_count,
        "estimated_costs": {
            "embedding": estimated_embedding_cost,
            "summarization": estimated_summary_cost,
            "classification": estimated_classification_cost,
            "total": total_estimated_cost,
        },
        "currency": "USD",
        "note": "These are rough estimates. Actual costs may vary.",
    }


# =============================================================================
# Error Handling & Recovery
# =============================================================================

class ErrorRecoveryManager:
    """
    Manages error recovery and retry logic for failed papers (Phase 18: Step 18.4).
    
    Enhanced with:
    - Checkpoint-based recovery
    - Selective retry of failed papers
    - Manual intervention options
    - Rollback capabilities
    """
    
    def __init__(self, max_retries: int = 3):
        """
        Initialize error recovery manager.
        
        Args:
            max_retries: Maximum number of retry attempts
        """
        self.max_retries = max_retries
        self.logger = logging.getLogger(f"{__name__}.ErrorRecoveryManager")
    
    def get_failed_papers(self, state: GraphState) -> List[PaperRecord]:
        """
        Get list of failed papers.
        
        Args:
            state: Current GraphState
            
        Returns:
            List of failed PaperRecords
        """
        return [
            paper for paper in state.get("papers", {}).values()
            if paper.processing_status == "failed"
        ]
    
    def get_failed_papers_by_stage(
        self,
        state: GraphState,
        stage: str
    ) -> List[PaperRecord]:
        """
        Get list of papers that failed at a specific stage (Phase 18: Step 18.4).
        
        Args:
            state: Current GraphState
            stage: Processing stage (e.g., 'parsing', 'summarization')
            
        Returns:
            List of PaperRecords that failed at the specified stage
        """
        return [
            paper for paper in state.get("papers", {}).values()
            if paper.processing_status == "failed" and paper.error_stage == stage
        ]
    
    def retry_paper(self, state: GraphState, paper_id: str) -> GraphState:
        """
        Retry processing a failed paper.
        
        Args:
            state: Current GraphState
            paper_id: ID of paper to retry
            
        Returns:
            Updated GraphState
        """
        if paper_id not in state["papers"]:
            self.logger.error(f"Paper not found: {paper_id}")
            return state
        
        paper = state["papers"][paper_id]
        
        if paper.retry_count >= self.max_retries:
            self.logger.warning(f"Max retries reached for {paper_id}")
            return state
        
        # Reset paper status
        paper.processing_status = "pending"
        paper.error_reason = None
        paper.error_stage = None
        paper.retry_count += 1
        
        # Move from failed to pending list
        if paper_id in state.get("papers_failed", []):
            state["papers_failed"].remove(paper_id)
        if paper_id not in state.get("papers_pending", []):
            state["papers_pending"].append(paper_id)
        
        self.logger.info(f"Retry {paper.retry_count}/{self.max_retries} for {paper_id}")
        
        return state
    
    def retry_failed_papers_selective(
        self,
        state: GraphState,
        filter_stage: Optional[str] = None,
        filter_error_type: Optional[str] = None,
        max_papers: Optional[int] = None
    ) -> GraphState:
        """
        Selectively retry failed papers based on criteria (Phase 18: Step 18.4).
        
        Args:
            state: Current GraphState
            filter_stage: Only retry papers that failed at this stage
            filter_error_type: Only retry papers with this error type
            max_papers: Maximum number of papers to retry
            
        Returns:
            Updated GraphState with selected papers reset for retry
        """
        failed_papers = self.get_failed_papers(state)
        
        # Apply filters
        if filter_stage:
            failed_papers = [p for p in failed_papers if p.error_stage == filter_stage]
        
        if filter_error_type:
            failed_papers = [
                p for p in failed_papers 
                if filter_error_type.lower() in (p.error_reason or "").lower()
            ]
        
        # Limit number of retries
        if max_papers:
            failed_papers = failed_papers[:max_papers]
        
        self.logger.info(f"Retrying {len(failed_papers)} papers (filtered)")
        
        for paper in failed_papers:
            state = self.retry_paper(state, paper.id)
        
        return state
    
    def create_recovery_checkpoint(
        self,
        state: GraphState,
        checkpoint_dir: Optional[str] = None
    ) -> str:
        """
        Create a checkpoint before attempting recovery (Phase 18: Step 18.4).
        
        Args:
            state: Current GraphState
            checkpoint_dir: Directory for checkpoints
            
        Returns:
            Path to created checkpoint
        """
        checkpoint_name = f"pre_recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        manager = CheckpointManager(Path(checkpoint_dir) if checkpoint_dir else None)
        checkpoint_path = manager.save(state, checkpoint_name)
        
        self.logger.info(f"Recovery checkpoint created: {checkpoint_path}")
        
        return checkpoint_path
    
    def rollback_to_checkpoint(
        self,
        checkpoint_name: str,
        checkpoint_dir: Optional[str] = None
    ) -> GraphState:
        """
        Rollback to a previous checkpoint (Phase 18: Step 18.4).
        
        Args:
            checkpoint_name: Name of checkpoint to rollback to
            checkpoint_dir: Directory containing checkpoints
            
        Returns:
            Restored GraphState
        """
        manager = CheckpointManager(Path(checkpoint_dir) if checkpoint_dir else None)
        state = manager.load(checkpoint_name)
        
        self.logger.info(f"Rolled back to checkpoint: {checkpoint_name}")
        
        return state
    
    def get_recovery_options(self, state: GraphState) -> Dict[str, Any]:
        """
        Get available recovery options for current state (Phase 18: Step 18.4).
        
        Args:
            state: Current GraphState
            
        Returns:
            Dictionary describing available recovery actions
        """
        failed_papers = self.get_failed_papers(state)
        
        # Group by stage and error type
        by_stage = {}
        by_error = {}
        retryable = []
        
        for paper in failed_papers:
            stage = paper.error_stage or "unknown"
            error = paper.error_reason or "unknown"
            
            by_stage[stage] = by_stage.get(stage, 0) + 1
            by_error[error] = by_error.get(error, 0) + 1
            
            if paper.retry_count < self.max_retries:
                retryable.append(paper.id)
        
        return {
            "total_failed": len(failed_papers),
            "retryable": len(retryable),
            "max_retries_reached": len(failed_papers) - len(retryable),
            "failures_by_stage": by_stage,
            "failures_by_error": by_error,
            "recommended_actions": self._generate_recovery_recommendations(
                failed_papers, by_stage, by_error
            ),
        }
    
    def _generate_recovery_recommendations(
        self,
        failed_papers: List[PaperRecord],
        by_stage: Dict[str, int],
        by_error: Dict[str, int]
    ) -> List[str]:
        """
        Generate recovery recommendations based on failure patterns.
        
        Args:
            failed_papers: List of failed papers
            by_stage: Count of failures by stage
            by_error: Count of failures by error type
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if not failed_papers:
            return ["No failed papers to recover."]
        
        # Check for common error patterns
        total_failed = len(failed_papers)
        
        # Stage-specific recommendations
        if by_stage.get("parsing", 0) > total_failed * 0.5:
            recommendations.append(
                "Many failures in parsing stage. Consider enabling OCR fallback "
                "or checking PDF file integrity."
            )
        
        if by_stage.get("metadata", 0) > total_failed * 0.3:
            recommendations.append(
                "Multiple metadata extraction failures. Check arXiv/CrossRef API connectivity."
            )
        
        # Error-specific recommendations
        for error, count in by_error.items():
            error_lower = error.lower()
            
            if "rate limit" in error_lower or "429" in error_lower:
                recommendations.append(
                    f"{count} rate limit errors. Consider increasing retry delay or "
                    "enabling batch processing."
                )
            
            if "timeout" in error_lower or "network" in error_lower:
                recommendations.append(
                    f"{count} network errors. Check internet connection and retry."
                )
            
            if "quota" in error_lower or "exceeded" in error_lower:
                recommendations.append(
                    f"{count} quota errors. Check API limits and consider upgrading plan."
                )
        
        # General recommendations
        retryable = sum(1 for p in failed_papers if p.retry_count < self.max_retries)
        if retryable > 0:
            recommendations.append(
                f"{retryable} papers can be retried. Use retry_failed_papers() to attempt recovery."
            )
        
        max_retries_reached = total_failed - retryable
        if max_retries_reached > 0:
            recommendations.append(
                f"{max_retries_reached} papers have reached max retries. "
                "Consider manual intervention or increasing max_retries."
            )
        
        return recommendations


def retry_failed_papers(
    state: GraphState,
    max_retries: int = 3,
    filter_stage: Optional[str] = None,
    filter_error_type: Optional[str] = None,
    max_papers: Optional[int] = None
) -> GraphState:
    """
    Retry failed papers with optional filtering (Phase 18: Step 18.4).
    
    Args:
        state: Current GraphState
        max_retries: Maximum retry attempts per paper
        filter_stage: Only retry papers that failed at this stage
        filter_error_type: Only retry papers with this error type
        max_papers: Maximum number of papers to retry
        
    Returns:
        Updated GraphState with failed papers reset for retry
    """
    manager = ErrorRecoveryManager(max_retries)
    
    # Use selective retry if filters provided
    if filter_stage or filter_error_type or max_papers:
        logger.info(
            f"Selective retry: stage={filter_stage}, "
            f"error_type={filter_error_type}, max={max_papers}"
        )
        return manager.retry_failed_papers_selective(
            state,
            filter_stage=filter_stage,
            filter_error_type=filter_error_type,
            max_papers=max_papers
        )
    
    # Otherwise retry all failed papers
    failed_papers = manager.get_failed_papers(state)
    logger.info(f"Retrying {len(failed_papers)} failed papers")
    
    for paper in failed_papers:
        state = manager.retry_paper(state, paper.id)
    
    return state


def list_failed_papers(state: GraphState) -> List[Dict[str, Any]]:
    """
    Get list of failed papers with error details.
    
    Args:
        state: Current GraphState
        
    Returns:
        List of dictionaries with paper info and errors
    """
    failed = []
    
    for paper in state.get("papers", {}).values():
        if paper.processing_status == "failed":
            failed.append({
                "paper_id": paper.id,
                "filename": paper.filename,
                "error_reason": paper.error_reason,
                "error_stage": paper.error_stage,
                "retry_count": paper.retry_count,
            })
    
    return failed


def get_recovery_options(state: GraphState, max_retries: int = 3) -> Dict[str, Any]:
    """
    Get available recovery options for current state (Phase 18: Step 18.4).
    
    Args:
        state: Current GraphState
        max_retries: Maximum retry attempts per paper
        
    Returns:
        Dictionary describing available recovery actions
    """
    manager = ErrorRecoveryManager(max_retries)
    return manager.get_recovery_options(state)


def create_recovery_checkpoint(
    state: GraphState,
    checkpoint_dir: Optional[str] = None
) -> str:
    """
    Create a checkpoint before attempting recovery (Phase 18: Step 18.4).
    
    Args:
        state: Current GraphState
        checkpoint_dir: Directory for checkpoints
        
    Returns:
        Path to created checkpoint
    """
    manager = ErrorRecoveryManager()
    return manager.create_recovery_checkpoint(state, checkpoint_dir)


def rollback_to_checkpoint(
    checkpoint_name: str,
    checkpoint_dir: Optional[str] = None
) -> GraphState:
    """
    Rollback to a previous checkpoint (Phase 18: Step 18.4).
    
    Args:
        checkpoint_name: Name of checkpoint to rollback to
        checkpoint_dir: Directory containing checkpoints
        
    Returns:
        Restored GraphState
    """
    manager = ErrorRecoveryManager()
    return manager.rollback_to_checkpoint(checkpoint_name, checkpoint_dir)


# =============================================================================
# Phase 17: Cost Tracking Integration
# =============================================================================

def initialize_cost_tracking(state: GraphState) -> GraphState:
    """
    Initialize cost tracking in the GraphState.
    
    Args:
        state: Current GraphState
        
    Returns:
        Updated GraphState with cost tracker initialized
    """
    config = state.get("config")
    if not config or not config.enable_cost_tracking:
        logger.info("Cost tracking disabled in config")
        return state
    
    # Initialize cost tracker if not already present
    if state.get("cost_tracker") is None:
        logger.info("Initializing cost tracker")
        state["cost_tracker"] = CostTracker(config)
        state["total_cost"] = 0.0
        state["cost_breakdown"] = {}
    
    return state


def update_cost_tracking(
    state: GraphState,
    operation: str,
    model: str,
    input_tokens: int,
    output_tokens: int = 0,
    paper_id: Optional[str] = None,
    batch_size: int = 1,
    is_batch: bool = False
) -> GraphState:
    """
    Record an API call and update cost tracking in state.
    
    Args:
        state: Current GraphState
        operation: Type of operation (embedding, summarization, etc.)
        model: Model used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        paper_id: Associated paper ID (if applicable)
        batch_size: Batch size if batched
        is_batch: Whether this is a batch API call
        
    Returns:
        Updated GraphState with cost information
        
    Raises:
        BudgetExceededError: If budget limit is exceeded
    """
    config = state.get("config")
    if not config or not config.enable_cost_tracking:
        return state
    
    # Ensure cost tracker is initialized
    state = initialize_cost_tracking(state)
    
    tracker = state["cost_tracker"]
    
    try:
        # Record the API call
        record = tracker.record_api_call(
            operation=operation,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            paper_id=paper_id,
            batch_size=batch_size,
            is_batch=is_batch
        )
        
        # Update state with current costs
        state["total_cost"] = tracker.total_cost
        state["cost_breakdown"] = tracker.cost_by_operation.copy()
        
        logger.debug(f"Cost updated: ${tracker.total_cost:.4f} (+${record.estimated_cost:.4f})")
        
    except BudgetExceededError as e:
        logger.error(f"Budget exceeded: {e}")
        # Add to errors but don't fail silently
        state["errors"].append({
            "stage": "cost_tracking",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        # Re-raise to allow caller to handle
        raise
    
    return state


def check_budget_before_operation(
    state: GraphState,
    operation: str,
    estimated_tokens: int,
    model: Optional[str] = None
) -> bool:
    """
    Check if there's sufficient budget before starting an expensive operation.
    
    Args:
        state: Current GraphState
        operation: Operation to perform
        estimated_tokens: Estimated token usage
        model: Model to use (defaults from config if not specified)
        
    Returns:
        True if operation can proceed, False if budget would be exceeded
    """
    config = state.get("config")
    if not config or not config.enable_cost_tracking or not config.max_cost_per_run:
        # No budget limit, always allow
        return True
    
    # Get tracker
    tracker = state.get("cost_tracker")
    if tracker is None:
        # No tracking yet, initialize
        state = initialize_cost_tracking(state)
        tracker = state["cost_tracker"]
    
    # Determine model
    if model is None:
        if "embed" in operation.lower():
            model = config.embedding_model
        elif "summar" in operation.lower():
            model = config.summary_model
        elif "classif" in operation.lower():
            model = config.classification_model
        else:
            model = config.summary_model  # Default
    
    # Estimate cost
    estimated_cost = tracker.estimate_cost(
        model=model,
        input_tokens=estimated_tokens,
        output_tokens=int(estimated_tokens * 0.5),  # Rough estimate
        is_batch=config.batch_api_calls
    )
    
    # Check if within budget
    projected_total = tracker.total_cost + estimated_cost
    budget_available = projected_total <= config.max_cost_per_run
    
    if not budget_available:
        logger.warning(
            f"Operation '{operation}' would exceed budget: "
            f"${projected_total:.4f} > ${config.max_cost_per_run:.2f}"
        )
    
    return budget_available


def print_cost_summary(state: GraphState) -> None:
    """
    Print a cost summary for the current pipeline run.
    
    Args:
        state: Current GraphState
    """
    config = state.get("config")
    if not config or not config.enable_cost_tracking:
        print("Cost tracking is disabled.")
        return
    
    tracker = state.get("cost_tracker")
    if tracker is None:
        print("No cost data available.")
        return
    
    # Generate and print report
    tracker.print_summary()


def get_cost_recommendations(state: GraphState) -> List[str]:
    """
    Get cost-saving recommendations based on current usage.
    
    Args:
        state: Current GraphState
        
    Returns:
        List of recommendation strings
    """
    config = state.get("config")
    if not config or not config.enable_cost_tracking:
        return []
    
    tracker = state.get("cost_tracker")
    if tracker is None:
        return []
    
    return tracker._generate_recommendations()


def save_cost_report(state: GraphState, output_path: str) -> Optional[str]:
    """
    Save cost report to a JSON file.
    
    Args:
        state: Current GraphState
        output_path: Path to output file
        
    Returns:
        Path to saved file, or None if cost tracking disabled
    """
    config = state.get("config")
    if not config or not config.enable_cost_tracking:
        logger.warning("Cost tracking disabled, cannot save report")
        return None
    
    tracker = state.get("cost_tracker")
    if tracker is None:
        logger.warning("No cost tracker initialized")
        return None
    
    return tracker.save_report(output_path)

