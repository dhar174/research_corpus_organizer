# Phase 13: LangGraph Workflow Integration

Complete workflow orchestration system for the RAG PDF Research Corpus pipeline.

## Quick Start

### Installation

```bash
# Install LangGraph (required)
pip install langgraph

# Verify installation
python -c "from langgraph.graph import StateGraph; print('✓ LangGraph installed')"
```

### Basic Usage

```python
from rag_models import create_default_config
from workflow_orchestrator import run_full_pipeline

# Configure pipeline
config = create_default_config(
    drive_folder_path="/content/drive/MyDrive/PDFs",
    max_papers_per_run=100,
    summary_model="gpt-5-mini",
    taxonomy_model="gpt-5-mini",
    classification_model="gpt-5-mini",
)

# Run complete pipeline
final_state = run_full_pipeline(config, checkpoint_dir="./checkpoints")

# Access results
print(f"Processed: {len(final_state['papers'])} papers")
print(f"Taxonomy: {final_state['taxonomy_json_path']}")
print(f"Export: {final_state['master_csv_path']}")
```

## Features

### ✅ Workflow Orchestration
- **StateGraph** with supervisor pattern
- **10 integrated stages** (discovery → export)
- **Conditional routing** based on state
- **Modular design** for easy extension

### ✅ Checkpointing
- **Save/resume** at any pipeline stage
- **Google Drive backup** for persistence
- **Timestamp-based versioning**
- **Complete state serialization**

### ✅ Execution Modes
- **Full pipeline** - Complete end-to-end
- **Ingestion only** - Discovery through embeddings
- **Summarization only** - Summarize existing papers
- **Classification only** - Classify into taxonomy
- **Taxonomy rebuild** - Regenerate hierarchy

### ✅ Quality Control
- **Paper-level QC** checks
- **Corpus-wide** quality reports
- **Prerequisite validation** before stages
- **Quality scoring** (0-1 scale)

### ✅ Cost & Performance
- **Token usage** estimation
- **Cost calculation** by component
- **Time tracking** per stage
- **Budget monitoring**

### ✅ Error Handling
- **Isolated failures** (one paper doesn't stop pipeline)
- **Retry logic** with configurable attempts
- **Error details** preserved for debugging
- **Batch retry** functionality

### ✅ Monitoring
- **Real-time progress** tracking
- **Completion percentage** calculation
- **Phase completion** flags
- **Visual progress** indicators

### ✅ Visualization
- **Mermaid diagrams** (interactive)
- **ASCII diagrams** (terminal)
- **State displays** (formatted)

## Entry Points

### run_full_pipeline()
Run the complete RAG pipeline from start to finish.

```python
from workflow_orchestrator import run_full_pipeline

final_state = run_full_pipeline(
    config,
    checkpoint_dir="./checkpoints"
)
```

### run_ingestion_only()
Run only ingestion (discovery, parsing, metadata, embeddings).

```python
from workflow_orchestrator import run_ingestion_only

ingested_state = run_ingestion_only(config)
# Save checkpoint
save_checkpoint(ingested_state)
```

### run_summarization_only()
Summarize papers that have already been ingested.

```python
from workflow_orchestrator import run_summarization_only

summarized_state = run_summarization_only(ingested_state)
```

### run_classification_only()
Classify papers into an existing taxonomy.

```python
from workflow_orchestrator import run_classification_only

# Ensure taxonomy is approved
state["taxonomy_approved"] = True
classified_state = run_classification_only(state)
```

### rebuild_taxonomy()
Rebuild the topic taxonomy from scratch.

```python
from workflow_orchestrator import rebuild_taxonomy

# Adjust clustering parameters
config.cluster_tier1_target_k = 10
new_taxonomy_state = rebuild_taxonomy(state)
```

## Checkpointing

### Save Checkpoint
```python
from workflow_orchestrator import save_checkpoint

checkpoint_path = save_checkpoint(
    state,
    checkpoint_dir="./checkpoints"
)
print(f"Saved to: {checkpoint_path}")
```

### Load Checkpoint
```python
from workflow_orchestrator import load_checkpoint

state = load_checkpoint(
    "checkpoint_20251124_120000",
    checkpoint_dir="./checkpoints"
)
```

### Resume from Checkpoint
```python
from workflow_orchestrator import WorkflowExecutor

executor = WorkflowExecutor(config)
final_state = executor.resume_from_checkpoint("checkpoint_20251124_120000")
```

### Backup to Google Drive
```python
from workflow_orchestrator import CheckpointManager

manager = CheckpointManager()
drive_path = manager.save_to_drive(
    state,
    "/content/drive/MyDrive/checkpoints"
)
```

## Monitoring & Progress

### Display Current State
```python
from workflow_orchestrator import display_workflow_state

print(display_workflow_state(state))
```

Output:
```
==============================================================
WORKFLOW STATE
==============================================================
Current Phase: summarization
Total Papers: 50
Pending: 10
Completed: 38
Failed: 2
Total Chunks: 2500
Has Taxonomy: False
Taxonomy Approved: False
==============================================================
```

### Get Progress Details
```python
from workflow_orchestrator import get_workflow_progress

progress = get_workflow_progress(state)

print(f"Completion: {progress['completion_percentage']:.1f}%")
print(f"Current phase: {progress['current_phase']}")

for phase, complete in progress['phases_complete'].items():
    status = "✓" if complete else "✗"
    print(f"  {status} {phase}")
```

### Track Costs
```python
from workflow_orchestrator import track_costs_and_time

costs = track_costs_and_time(state)

print(f"Papers processed: {costs['papers_processed']}")
print(f"Chunks processed: {costs['chunks_processed']}")
print(f"\nEstimated costs:")
for component, cost in costs['estimated_costs'].items():
    print(f"  {component}: ${cost:.4f}")
print(f"Total: ${costs['estimated_costs']['total']:.2f}")
```

## Quality Control

### Check Data Quality
```python
from workflow_orchestrator import check_data_quality

quality_report = check_data_quality(state)

print(f"Total papers: {quality_report['total_papers']}")
print(f"Papers with issues: {quality_report['papers_with_issues']}")
print(f"Average quality: {quality_report['average_quality_score']:.2f}")
print(f"\nDistribution: {quality_report['quality_distribution']}")
```

### Validate Prerequisites
```python
from workflow_orchestrator import validate_pipeline_prerequisites

# Check before running expensive stage
if validate_pipeline_prerequisites(state, "classify"):
    state = run_classification_only(state)
else:
    print("Prerequisites not met for classification")
```

## Error Handling

### List Failed Papers
```python
from workflow_orchestrator import list_failed_papers

failed = list_failed_papers(state)

for paper_info in failed:
    print(f"File: {paper_info['filename']}")
    print(f"Error: {paper_info['error_reason']}")
    print(f"Stage: {paper_info['error_stage']}")
    print(f"Retries: {paper_info['retry_count']}")
    print()
```

### Retry Failed Papers
```python
from workflow_orchestrator import retry_failed_papers

# Retry all failed papers
updated_state = retry_failed_papers(state, max_retries=3)

# Continue pipeline with retried papers
final_state = run_full_pipeline(config, initial_state=updated_state)
```

### Manual Retry
```python
from workflow_orchestrator import ErrorRecoveryManager

manager = ErrorRecoveryManager(max_retries=3)

# Retry specific paper
updated_state = manager.retry_paper(state, "paper_123")
```

## Visualization

### Mermaid Diagram
```python
from workflow_orchestrator import visualize_workflow

# Generate Mermaid diagram
mermaid = visualize_workflow(config, output_format="mermaid")
print(mermaid)

# In Jupyter/Colab, display in Markdown cell:
# ```mermaid
# [paste diagram here]
# ```
```

### ASCII Diagram
```python
# Generate ASCII diagram
ascii_diagram = visualize_workflow(config, output_format="ascii")
print(ascii_diagram)
```

## Advanced Usage

### Custom Workflow Executor
```python
from workflow_orchestrator import WorkflowExecutor

# Create executor with custom settings
executor = WorkflowExecutor(
    config,
    checkpoint_dir="/content/drive/MyDrive/checkpoints"
)

# Run with automatic checkpointing
final_state = executor.run_full_pipeline(save_checkpoints=True)
```

### Staged Processing with Review
```python
# Stage 1: Ingest
state = run_ingestion_only(config)
save_checkpoint(state, "post_ingestion")

# Review ingested papers...
quality = check_data_quality(state)
if quality['average_quality_score'] < 0.7:
    print("Quality issues detected")
    # Fix issues...

# Stage 2: Continue if quality is good
state = run_full_pipeline(config, initial_state=state)
```

### Conditional Execution
```python
# Build taxonomy
state = rebuild_taxonomy(state)

# Review and approve
hierarchy = state["topic_hierarchy"]
validation = hierarchy.validate_hierarchy()

if validation["valid"]:
    state["taxonomy_approved"] = True
    state = run_classification_only(state)
else:
    print(f"Taxonomy issues: {validation['issues']}")
    # Rebuild with different parameters...
```

## Architecture

### Supervisor Pattern
```
           ┌─────────────┐
           │ Supervisor  │
           │   Node      │
           └──────┬──────┘
                  │
     ┌────────────┼────────────┐
     │            │            │
     ▼            ▼            ▼
 ┌───────┐   ┌───────┐   ┌───────┐
 │Worker │   │Worker │   │Worker │
 │Node 1 │   │Node 2 │   │Node 3 │
 └───┬───┘   └───┬───┘   └───┬───┘
     │            │            │
     └────────────┴────────────┘
                  │
                  ▼
           ┌─────────────┐
           │ Supervisor  │
           │   (loop)    │
           └─────────────┘
```

### Workflow Stages
```
1. initialization
2. discover        → drive_utils.discover_pdfs()
3. parse           → pdf_parser.parse_and_chunk_worker()
4. metadata        → metadata_extractor.metadata_extraction_worker()
5. embed           → embedding_generator.embedding_generation_worker()
6. summarize       → summarization_pass1.summarize_papers_worker()
7. taxonomy        → topic_taxonomy.build_complete_taxonomy()
8. taxonomy_review → (human approval)
9. classify        → paper_classification.classification_worker()
10. export         → export_manager.export_final_data()
11. end
```

## Testing

### Run Tests
```bash
cd /path/to/research_corpus_organizer
python test_phase13.py
```

Expected output:
```
======================================================================
PHASE 13: LANGGRAPH WORKFLOW INTEGRATION - TEST SUITE
======================================================================

=== Test: WorkflowBuilder ===
✓ WorkflowBuilder initialized correctly

... (25 tests)

======================================================================
TEST RESULTS: 25 passed, 0 failed
======================================================================
```

### Run Examples
```bash
python examples_phase13.py
```

## Troubleshooting

### LangGraph not found
```bash
pip install langgraph
```

### Worker not found
Ensure all Phase 3-12 modules are present.

### Checkpoint load fails
- Check file exists and path is correct
- Verify same Python version
- Try loading an earlier checkpoint

### Pipeline stuck at taxonomy_review
```python
# Option 1: Approve taxonomy
state["taxonomy_approved"] = True

# Option 2: Disable approval requirement
config.taxonomy_approval_required = False
```

### High memory usage
```python
# Reduce batch size
config.max_papers_per_run = 20

# Clear old checkpoints
checkpoint_manager.cleanup_old_checkpoints(keep=5)
```

## Performance Tips

1. **Batch Size**: Adjust based on available memory
2. **Checkpointing**: Save after expensive stages only
3. **Error Handling**: Set reasonable max_retries
4. **Quality Control**: Run QC before expensive stages

## Documentation

- **[PHASE13_COMPLETION.md](PHASE13_COMPLETION.md)** - Full implementation details
- **[PHASE13_INDEX.md](PHASE13_INDEX.md)** - Quick navigation and API reference
- **[PHASE13_SUMMARY.md](PHASE13_SUMMARY.md)** - Executive summary
- **[workflow_orchestrator.py](workflow_orchestrator.py)** - Source code with docstrings
- **[test_phase13.py](test_phase13.py)** - Test suite
- **[examples_phase13.py](examples_phase13.py)** - Usage examples

## API Reference

### Classes
- **WorkflowBuilder** - Build StateGraph
- **SupervisorCoordinator** - Coordinate execution
- **CheckpointManager** - Manage checkpoints
- **WorkflowExecutor** - User-friendly controller
- **QualityController** - Data quality checks
- **ErrorRecoveryManager** - Error handling

### Functions
- **run_full_pipeline()** - Complete workflow
- **run_ingestion_only()** - Partial execution
- **run_summarization_only()** - Summarize stage
- **run_classification_only()** - Classify stage
- **rebuild_taxonomy()** - Rebuild taxonomy
- **save_checkpoint()** - Save state
- **load_checkpoint()** - Load state
- **visualize_workflow()** - Generate diagrams
- **display_workflow_state()** - Show state
- **get_workflow_progress()** - Calculate progress
- **check_data_quality()** - QC report
- **validate_pipeline_prerequisites()** - Validate
- **track_costs_and_time()** - Cost tracking
- **list_failed_papers()** - List failures
- **retry_failed_papers()** - Retry failures

## Dependencies

### Required
- `langgraph` - Workflow orchestration
- `rag_models` - Data models (Phase 1)
- `drive_utils` - PDF discovery (Phase 2)
- `pdf_parser` - Parsing (Phase 3)
- `metadata_extractor` - Metadata (Phase 4)
- `embedding_generator` - Embeddings (Phase 5)
- `summarization_pass1` - Summaries (Phase 6)
- `topic_taxonomy` - Taxonomy (Phase 8)
- `paper_classification` - Classification (Phase 10)
- `export_manager` - Export (Phase 12)

### Standard Library
- `json`, `pickle`, `logging`, `time`
- `pathlib`, `datetime`, `collections`
- `typing`

## License

Same as parent project.

## Contributing

Follow the parent project's contribution guidelines.

## Support

See parent project README for support information.

---

**Version:** 1.0  
**Status:** ✅ Production Ready  
**Last Updated:** 2025-11-24
