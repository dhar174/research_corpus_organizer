# Phase 13: LangGraph Workflow Integration - INDEX

## Quick Navigation

- [Completion Report](PHASE13_COMPLETION.md) - Full implementation details
- [Summary](PHASE13_SUMMARY.md) - Executive summary
- [Main Module](workflow_orchestrator.py) - Core implementation
- [Tests](test_phase13.py) - Test suite
- [Examples](examples_phase13.py) - Usage examples

---

## Module Overview

### workflow_orchestrator.py

**Purpose:** Complete LangGraph workflow orchestration for the RAG PDF pipeline

**Key Classes:**

1. **WorkflowBuilder** (Lines ~240-600)
   - Builds StateGraph with all nodes
   - Defines edges and transitions
   - Integrates existing worker nodes
   - Methods:
     - `create_graph()` - Build complete workflow
     - `_create_*_node()` - Node factories
     - `_route_from_supervisor()` - Routing logic

2. **SupervisorCoordinator** (Lines ~65-175)
   - Coordinates workflow execution
   - Manages paper queues
   - Tracks progress
   - Methods:
     - `decide_next_stage()` - Stage routing
     - `update_queue()` - Queue management

3. **CheckpointManager** (Lines ~610-725)
   - Manages state checkpoints
   - Save/load functionality
   - Google Drive integration
   - Methods:
     - `save()` - Save checkpoint
     - `load()` - Load checkpoint
     - `list_checkpoints()` - List available
     - `save_to_drive()` - Backup to Drive

4. **WorkflowExecutor** (Lines ~740-850)
   - Controls workflow execution
   - Entry points for users
   - Resume from checkpoint
   - Methods:
     - `run_full_pipeline()` - Complete execution
     - `run_ingestion_only()` - Partial execution
     - `resume_from_checkpoint()` - Resume

5. **QualityController** (Lines ~995-1050)
   - Data quality checks
   - Paper validation
   - Corpus-wide QC
   - Methods:
     - `check_paper_quality()` - Individual check
     - `check_corpus_quality()` - Aggregate check

6. **ErrorRecoveryManager** (Lines ~1100-1180)
   - Error handling
   - Retry logic
   - Failed paper management
   - Methods:
     - `get_failed_papers()` - List failures
     - `retry_paper()` - Retry individual

**Key Functions:**

Entry Points:
- `run_full_pipeline()` - Complete pipeline (Line ~865)
- `run_ingestion_only()` - Discovery through embeddings (Line ~905)
- `run_summarization_only()` - Summarize papers (Line ~925)
- `run_classification_only()` - Classify papers (Line ~945)
- `rebuild_taxonomy()` - Rebuild taxonomy (Line ~965)

Checkpointing:
- `save_checkpoint()` - Save state (Line ~730)
- `load_checkpoint()` - Load state (Line ~738)

Visualization:
- `visualize_workflow()` - Generate diagram (Line ~985)
- `display_workflow_state()` - Show state (Line ~1025)
- `get_workflow_progress()` - Calculate progress (Line ~1055)

Quality Control:
- `check_data_quality()` - QC report (Line ~1085)
- `validate_pipeline_prerequisites()` - Validate (Line ~1095)
- `track_costs_and_time()` - Cost tracking (Line ~1125)

Error Handling:
- `retry_failed_papers()` - Retry all (Line ~1185)
- `list_failed_papers()` - List failures (Line ~1205)

**Exports:**
```python
__all__ = [
    # Graph Structure
    'create_workflow_graph',
    'WorkflowBuilder',
    
    # Supervisor
    'supervisor_node',
    'SupervisorCoordinator',
    
    # Checkpointing
    'save_checkpoint',
    'load_checkpoint',
    'CheckpointManager',
    
    # Execution
    'run_full_pipeline',
    'run_ingestion_only',
    'run_summarization_only',
    'run_classification_only',
    'rebuild_taxonomy',
    'WorkflowExecutor',
    
    # Visualization
    'visualize_workflow',
    'display_workflow_state',
    'get_workflow_progress',
    
    # Quality Control
    'QualityController',
    'check_data_quality',
    'validate_pipeline_prerequisites',
    'track_costs_and_time',
    
    # Error Handling
    'retry_failed_papers',
    'list_failed_papers',
    'ErrorRecoveryManager',
]
```

---

## Test Coverage

### test_phase13.py

**Test Categories:**

1. **Graph Structure Tests** (Lines 85-120)
   - `test_workflow_builder()`
   - `test_create_workflow_graph()`

2. **Supervisor Logic Tests** (Lines 125-200)
   - `test_supervisor_coordinator()`
   - `test_supervisor_queue_update()`
   - `test_supervisor_node()`

3. **Checkpointing Tests** (Lines 205-290)
   - `test_checkpoint_manager()`
   - `test_save_and_load_checkpoint()`
   - `test_list_checkpoints()`

4. **Execution Controller Tests** (Lines 295-390)
   - `test_workflow_executor_init()`
   - `test_run_ingestion_only()`
   - `test_run_summarization_only()`
   - `test_run_classification_only()`
   - `test_rebuild_taxonomy()`

5. **Visualization Tests** (Lines 395-480)
   - `test_visualize_workflow_mermaid()`
   - `test_visualize_workflow_ascii()`
   - `test_display_workflow_state()`
   - `test_get_workflow_progress()`

6. **Quality Control Tests** (Lines 485-580)
   - `test_quality_controller()`
   - `test_check_data_quality()`
   - `test_validate_prerequisites()`
   - `test_track_costs()`

7. **Error Handling Tests** (Lines 585-670)
   - `test_error_recovery_manager()`
   - `test_retry_failed_papers()`
   - `test_list_failed_papers()`

**Total:** 25+ tests covering all major functionality

**Running Tests:**
```bash
cd /path/to/research_corpus_organizer
python test_phase13.py
```

---

## Usage Examples

### examples_phase13.py

**Example Categories:**

1. **Example 1: Basic Full Pipeline** (Lines 30-80)
   - Complete end-to-end execution
   - Configuration setup
   - Simple usage pattern

2. **Example 2: Selective Execution** (Lines 85-170)
   - Run individual stages
   - Stage-by-stage processing
   - Review between stages

3. **Example 3: Checkpoint Management** (Lines 175-250)
   - Save checkpoints
   - Load checkpoints
   - Resume from checkpoint

4. **Example 4: Progress Monitoring** (Lines 255-325)
   - Display workflow state
   - Calculate progress
   - Track completion

5. **Example 5: Quality Control** (Lines 330-430)
   - Data quality checks
   - Prerequisite validation
   - Cost tracking

6. **Example 6: Error Recovery** (Lines 435-510)
   - List failed papers
   - Retry failures
   - Error handling patterns

7. **Example 7: Visualization** (Lines 515-560)
   - Generate Mermaid diagrams
   - ASCII flowcharts
   - Workflow display

8. **Example 8: Advanced Control** (Lines 565-630)
   - Custom executors
   - Conditional execution
   - Advanced patterns

**Running Examples:**
```bash
cd /path/to/research_corpus_organizer
python examples_phase13.py
```

---

## Integration Points

### Dependencies on Previous Phases

| Phase | Module | Function Called | Purpose |
|-------|--------|-----------------|---------|
| 0-1 | rag_models | RunConfig, GraphState, etc. | Data models |
| 2 | drive_utils | discover_pdfs() | PDF discovery |
| 3 | pdf_parser | parse_and_chunk_worker() | Parsing |
| 4 | metadata_extractor | metadata_extraction_worker() | Metadata |
| 5 | embedding_generator | embedding_generation_worker() | Embeddings |
| 6 | summarization_pass1 | summarize_papers_worker() | Summaries |
| 8 | topic_taxonomy | build_complete_taxonomy() | Taxonomy |
| 10 | paper_classification | classification_worker() | Classification |
| 12 | export_manager | export_final_data() | Export |

### External Dependencies

```python
# LangGraph (required for workflow)
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Standard library
import json, pickle, logging, time
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Any, Literal, Callable
```

---

## Common Usage Patterns

### Pattern 1: Quick Start

```python
from rag_models import create_default_config
from workflow_orchestrator import run_full_pipeline

config = create_default_config(drive_folder_path="PDFs")
final_state = run_full_pipeline(config)
```

### Pattern 2: Staged Processing

```python
from workflow_orchestrator import (
    run_ingestion_only,
    run_summarization_only,
    save_checkpoint,
)

# Stage 1: Ingest
state = run_ingestion_only(config)
save_checkpoint(state)

# Review ingested papers...

# Stage 2: Summarize
state = run_summarization_only(state)
```

### Pattern 3: Error Recovery

```python
from workflow_orchestrator import (
    run_full_pipeline,
    list_failed_papers,
    retry_failed_papers,
)

state = run_full_pipeline(config)

if state["papers_failed"]:
    failed = list_failed_papers(state)
    print(f"Found {len(failed)} failures")
    
    state = retry_failed_papers(state)
    state = run_full_pipeline(config, initial_state=state)
```

### Pattern 4: Monitoring

```python
from workflow_orchestrator import (
    display_workflow_state,
    get_workflow_progress,
    track_costs_and_time,
)

# Show state
print(display_workflow_state(state))

# Get progress
progress = get_workflow_progress(state)
print(f"Completion: {progress['completion_percentage']:.1f}%")

# Track costs
costs = track_costs_and_time(state)
print(f"Estimated cost: ${costs['estimated_costs']['total']:.2f}")
```

---

## Troubleshooting

### Common Issues

1. **ImportError: langgraph not found**
   ```bash
   pip install langgraph
   ```

2. **Worker not found**
   - Ensure all Phase 3-12 modules are present
   - Check worker function names match

3. **Checkpoint load fails**
   - Check checkpoint directory exists
   - Verify checkpoint file not corrupted
   - Ensure same Python version

4. **State not updating**
   - Always return updated state from nodes
   - Don't modify state in-place
   - Check state propagation

5. **Pipeline stuck at taxonomy_review**
   - Set `taxonomy_approved = True` in state
   - Or set `taxonomy_approval_required = False` in config

---

## Performance Tips

1. **Batch Size**
   - Adjust based on memory available
   - Larger batches = faster but more memory

2. **Checkpointing Frequency**
   - Save after expensive stages
   - Don't save too often (I/O overhead)

3. **Parallel Processing**
   - Currently sequential
   - Future: process papers in parallel

4. **Error Handling**
   - Set reasonable max_retries
   - Review failed papers before retry

---

## API Reference

### Quick Function Reference

**Execution:**
- `run_full_pipeline(config, checkpoint_dir=None)` → GraphState
- `run_ingestion_only(config)` → GraphState
- `run_summarization_only(state)` → GraphState
- `run_classification_only(state)` → GraphState
- `rebuild_taxonomy(state)` → GraphState

**Checkpointing:**
- `save_checkpoint(state, checkpoint_dir=None)` → str (path)
- `load_checkpoint(name, checkpoint_dir=None)` → GraphState

**Monitoring:**
- `display_workflow_state(state)` → str
- `get_workflow_progress(state)` → Dict
- `track_costs_and_time(state)` → Dict

**Quality Control:**
- `check_data_quality(state)` → Dict
- `validate_pipeline_prerequisites(state, stage)` → bool

**Error Handling:**
- `list_failed_papers(state)` → List[Dict]
- `retry_failed_papers(state, max_retries=3)` → GraphState

---

## Related Documentation

- [FINAL_NOTEBOOK_ACTION_PLAN.md](FINAL_NOTEBOOK_ACTION_PLAN.md) - Original Phase 13 plan
- [PHASE13_COMPLETION.md](PHASE13_COMPLETION.md) - Complete implementation report
- [PHASE13_SUMMARY.md](PHASE13_SUMMARY.md) - Executive summary
- [README.md](README.md) - Project overview

---

**Last Updated:** 2025-11-24  
**Version:** 1.0  
**Status:** Complete
