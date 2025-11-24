# Phase 18: Error Handling and Resilience - Index

## Quick Reference

| Component | File | Purpose |
|-----------|------|---------|
| ErrorHandler | rag_models.py | Global error logging and paper status updates |
| RetryHandler | rag_models.py | API retry with exponential backoff |
| DataValidator | rag_models.py | Pre-processing validation (PDFs, records) |
| ErrorRecoveryManager | workflow_orchestrator.py | Recovery mechanisms and checkpoints |
| Tests | test_phase18.py | Comprehensive test suite |
| Examples | examples_phase18.py | Usage examples and patterns |
| Documentation | PHASE18_COMPLETION.md | Complete documentation |

## Key Classes

### ErrorHandler
```python
from rag_models import ErrorHandler

error_handler = ErrorHandler()
paper = error_handler.update_paper_on_error(paper, stage, error, context)
summary = error_handler.get_error_summary()
```

### RetryHandler
```python
from rag_models import RetryHandler

retry_handler = RetryHandler(max_retries=5)
result = retry_handler.retry_with_backoff(function, *args, **kwargs)
```

### DataValidator
```python
from rag_models import DataValidator

validator = DataValidator()
result = validator.validate_pdf_file(file_path)
result = validator.validate_paper_record(paper)
```

### ErrorRecoveryManager
```python
from workflow_orchestrator import (
    retry_failed_papers,
    get_recovery_options,
    create_recovery_checkpoint
)

options = get_recovery_options(state)
checkpoint = create_recovery_checkpoint(state)
state = retry_failed_papers(state, filter_stage="parsing")
```

## Exception Hierarchy

```
Exception
├── APIError (base for API errors)
│   ├── RateLimitError (429 errors)
│   ├── QuotaExceededError (quota exhausted)
│   └── TransientAPIError (network/timeout)
└── ValidationError (base for validation)
    └── PDFValidationError (PDF-specific)
```

## Implementation Checklist

- [x] Step 18.1: Global Error Handler
  - [x] Try-except blocks wrapper
  - [x] Error logging with context
  - [x] Paper status updates
  - [x] Error categorization
  
- [x] Step 18.2: API Error Handling
  - [x] Rate limit handling (429)
  - [x] Exponential backoff
  - [x] Retry transient failures
  - [x] Quota exceeded handling
  - [x] Graceful degradation
  
- [x] Step 18.3: Data Validation Error Handling
  - [x] Invalid PDF handling
  - [x] Corrupt file detection
  - [x] Format validation
  - [x] Pre-processing validation
  - [x] Clear error messages
  
- [x] Step 18.4: Recovery Mechanisms
  - [x] Regular checkpointing
  - [x] Resume from checkpoint
  - [x] Retry failed papers
  - [x] Manual intervention options
  - [x] Rollback capabilities

## Test Coverage

| Test Class | Coverage |
|------------|----------|
| TestErrorHandler | Error logging, paper updates, summaries |
| TestRetryHandler | Exponential backoff, rate limits, retries |
| TestDataValidator | PDF validation, record validation |
| TestErrorRecoveryManager | Selective retry, checkpoints, recovery |
| TestIntegration | End-to-end workflows |

Run tests:
```bash
python test_phase18.py
```

## Examples

Run all examples:
```bash
python examples_phase18.py
```

Individual examples:
1. ErrorHandler for error logging
2. RetryHandler for API calls
3. DataValidator for validation
4. ErrorRecoveryManager for recovery
5. Complete integrated workflow

## Integration Points

### Phase 13 (Workflow Orchestration)
- Error handling in worker nodes
- Integration with LangGraph
- Checkpoint compatibility

### Phase 14 (Quality Control)
- Error metrics in QC dashboard
- Failed paper tracking
- Quality validation

### Phase 17 (Cost Tracking)
- Budget-aware retry logic
- Cost implications of retries
- Recovery cost tracking

## Common Patterns

### Pattern 1: Worker with Error Handling
```python
def worker_node(state: GraphState) -> GraphState:
    error_handler = ErrorHandler()
    retry_handler = RetryHandler()
    
    for paper in state["papers"].values():
        try:
            result = retry_handler.retry_with_backoff(process, paper)
        except Exception as e:
            paper = error_handler.update_paper_on_error(paper, "stage", e)
    
    return state
```

### Pattern 2: Validation Before Processing
```python
validator = DataValidator()

try:
    validator.validate_pdf_file(file_path)
    # Proceed with processing
except PDFValidationError as e:
    # Handle invalid PDF
    paper = error_handler.update_paper_on_error(paper, "validation", e)
```

### Pattern 3: Recovery Workflow
```python
# Analyze failures
options = get_recovery_options(state)

# Create checkpoint
checkpoint = create_recovery_checkpoint(state)

# Attempt selective retry
state = retry_failed_papers(state, filter_stage="parsing")

# If unsuccessful, rollback
if still_failing:
    state = rollback_to_checkpoint(checkpoint)
```

## API Reference

### ErrorHandler Methods
- `log_error(paper_id, stage, error, context)`: Log error
- `update_paper_on_error(paper, stage, error, context)`: Update paper status
- `get_error_summary()`: Get error statistics
- `get_errors_by_paper(paper_id)`: Get errors for paper
- `get_errors_by_stage(stage)`: Get errors for stage
- `export_errors(filepath)`: Export to JSON

### RetryHandler Methods
- `retry_with_backoff(func, *args, **kwargs)`: Execute with retry
- `calculate_delay(attempt)`: Calculate backoff delay

### DataValidator Methods
- `validate_pdf_file(file_path)`: Validate PDF
- `validate_paper_record(paper, required_fields)`: Validate record

### Recovery Functions
- `retry_failed_papers(state, max_retries, filter_stage, filter_error_type, max_papers)`: Retry papers
- `list_failed_papers(state)`: List failures
- `get_recovery_options(state, max_retries)`: Get options
- `create_recovery_checkpoint(state, checkpoint_dir)`: Create checkpoint
- `rollback_to_checkpoint(checkpoint_name, checkpoint_dir)`: Rollback

## Configuration

### RetryHandler Configuration
```python
RetryHandler(
    max_retries=5,        # Maximum retry attempts
    initial_delay=1.0,    # Initial delay in seconds
    max_delay=60.0,       # Maximum delay in seconds
    backoff_factor=2.0    # Exponential backoff multiplier
)
```

### ErrorRecoveryManager Configuration
```python
ErrorRecoveryManager(
    max_retries=3  # Maximum retry attempts per paper
)
```

## Troubleshooting

### High Rate Limit Errors
```python
# Increase initial delay and max delay
retry_handler = RetryHandler(
    initial_delay=2.0,
    max_delay=120.0
)
```

### Many Parsing Failures
```python
# Enable OCR and retry parsing errors
config.enable_ocr_fallback = True
state = retry_failed_papers(state, filter_stage="parsing")
```

### Budget Concerns with Retries
```python
# Check recovery options first
options = get_recovery_options(state)
# Selective retry to minimize cost
state = retry_failed_papers(state, max_papers=10)
```

## Resources

- **Documentation**: PHASE18_COMPLETION.md
- **Tests**: test_phase18.py
- **Examples**: examples_phase18.py
- **Implementation**: rag_models.py, workflow_orchestrator.py
- **Specification**: FINAL_NOTEBOOK_ACTION_PLAN.md (Phase 18)

---

**Version:** 1.0  
**Date:** 2025-11-24  
**Status:** Complete ✓
