# Phase 17 Index

Quick reference for Phase 17: Cost Tracking and Optimization

---

## Core Components

### Models (`rag_models.py`)

| Class/Model | Purpose | Key Methods |
|-------------|---------|-------------|
| `CostTracker` | Main cost tracking system | `record_api_call()`, `generate_report()`, `print_summary()` |
| `APICallRecord` | Individual API call record | `to_dict()` |
| `CostReport` | Comprehensive cost report | `to_formatted_string()`, `to_dict()` |
| `BudgetExceededError` | Budget limit exception | - |

### Configuration (`RunConfig`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_cost_per_run` | float? | None | Maximum cost in USD |
| `cost_warning_threshold` | float | 0.8 | Warn at this fraction of budget |
| `enable_cost_tracking` | bool | True | Enable/disable tracking |
| `enable_result_caching` | bool | True | Cache API results |
| `batch_api_calls` | bool | True | Use batch API discount |

### GraphState Fields

| Field | Type | Description |
|-------|------|-------------|
| `cost_tracker` | CostTracker? | Cost tracking instance |
| `total_cost` | float | Current total cost |
| `cost_breakdown` | Dict[str, float] | Cost by operation type |

---

## API Reference

### CostTracker Methods

```python
# Initialize
tracker = CostTracker(config)

# Record API call
record = tracker.record_api_call(
    operation="summarization",
    model="gpt-5-mini",
    input_tokens=5000,
    output_tokens=2000,
    paper_id="paper_001",
    batch_size=1,
    is_batch=False
)

# Estimate cost before call
cost = tracker.estimate_cost(
    model="gpt-5-mini",
    input_tokens=5000,
    output_tokens=2000,
    is_batch=False
)

# Generate report
report = tracker.generate_report()

# Print summary
tracker.print_summary()

# Save report
tracker.save_report("cost_report.json")

# Caching
cache_key = tracker.get_cache_key(operation="test", param1="value")
result = tracker.get_cached_result(cache_key)
tracker.cache_result(cache_key, result)
```

### Workflow Functions

```python
from workflow_orchestrator import (
    initialize_cost_tracking,
    update_cost_tracking,
    check_budget_before_operation,
    print_cost_summary,
    get_cost_recommendations,
    save_cost_report,
)

# Initialize tracking
state = initialize_cost_tracking(state)

# Update costs
state = update_cost_tracking(
    state,
    operation="summarization",
    model="gpt-5-mini",
    input_tokens=5000,
    output_tokens=2000,
    paper_id="paper_001"
)

# Check budget
can_proceed = check_budget_before_operation(
    state,
    operation="summarization",
    estimated_tokens=50000
)

# Print summary
print_cost_summary(state)

# Get recommendations
recommendations = get_cost_recommendations(state)

# Save report
path = save_cost_report(state, "cost_report.json")
```

---

## Pricing (November 2025)

### Completions

- **gpt-5-mini**: $0.10 / $0.40 per 1M input/output tokens
- **gpt-5**: $3.00 / $15.00 per 1M input/output tokens
- **o4-mini**: $0.15 / $0.60 per 1M input/output tokens
- **o4**: $5.00 / $20.00 per 1M input/output tokens

### Embeddings

- **text-embedding-3-small**: $0.02 per 1M tokens
- **text-embedding-3-large**: $0.13 per 1M tokens

### Batch Discount

- **50% off** all models when using Batch API

---

## Quick Start

### Basic Setup

```python
from rag_models import RunConfig, CostTracker

config = RunConfig(
    enable_cost_tracking=True,
    max_cost_per_run=10.0,  # $10 budget
    cost_warning_threshold=0.8,  # Warn at 80%
)

tracker = CostTracker(config)
```

### With Workflow

```python
from rag_models import RunConfig, StateManager
from workflow_orchestrator import initialize_cost_tracking, print_cost_summary

config = RunConfig(
    enable_cost_tracking=True,
    max_cost_per_run=20.0,
    batch_api_calls=True,  # 50% savings!
)

state = StateManager.create_initial_state(config)
state = initialize_cost_tracking(state)

# ... run pipeline ...

print_cost_summary(state)
```

---

## Cost Optimization Checklist

- [ ] Set `batch_api_calls=True` (50% savings)
- [ ] Enable `enable_result_caching=True`
- [ ] Use `gpt-5-mini` instead of `gpt-5` (30x cheaper)
- [ ] Use `text-embedding-3-small` instead of `large` (6.5x cheaper)
- [ ] Set `max_cost_per_run` to prevent overspending
- [ ] Review cost recommendations after each run
- [ ] Reduce `max_tokens_per_summary` if needed
- [ ] Process in batches with budget limits

---

## Common Patterns

### Budget-Controlled Processing

```python
config = RunConfig(
    max_cost_per_run=5.0,
    enable_cost_tracking=True,
)

tracker = CostTracker(config)

try:
    for paper in papers:
        tracker.record_api_call(...)
except BudgetExceededError as e:
    print(f"Budget exceeded: {e}")
    tracker.print_summary()
```

### Pre-Check Before Expensive Operation

```python
from workflow_orchestrator import check_budget_before_operation

if check_budget_before_operation(state, "summarization", 100000):
    # Proceed
    state = process_papers(state)
else:
    print("Insufficient budget remaining")
```

### Generate Cost Report

```python
from workflow_orchestrator import save_cost_report

# After pipeline run
report_path = save_cost_report(state, "reports/cost_report.json")
print(f"Cost report saved to {report_path}")
```

---

## Files

### Implementation
- `rag_models.py` - Core cost tracking (+653 lines)
- `workflow_orchestrator.py` - Integration (+235 lines)

### Testing
- `test_phase17.py` - Test suite (21 tests)
- `examples_phase17.py` - Usage examples (6 examples)

### Documentation
- `README_PHASE17.md` - Complete guide
- `PHASE17_COMPLETION.md` - Implementation summary
- `PHASE17_INDEX.md` - This quick reference

---

## Error Handling

### BudgetExceededError

```python
from rag_models import BudgetExceededError

try:
    tracker.record_api_call(...)
except BudgetExceededError as e:
    # Budget exceeded
    print(f"Budget exceeded: {e}")
    # Option 1: Stop processing
    return
    # Option 2: Increase budget
    # Option 3: Continue with approval
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Cost tracking not working | Set `enable_cost_tracking=True` |
| Budget exceeded immediately | Increase `max_cost_per_run` |
| Inaccurate costs | Update `CostTracker.PRICING` with current rates |
| Cache not working | Set `enable_result_caching=True` |
| No recommendations | Process more API calls first |

---

## Testing

Run tests:
```bash
python test_phase17.py
```

Run examples:
```bash
python examples_phase17.py
```

---

## Next Steps

After Phase 17:
1. Review cost reports
2. Apply optimization recommendations
3. Set appropriate budget limits
4. Enable batch API for production
5. Proceed to Phase 18 (Error Handling)

---

**Phase 17 Status:** ✅ Complete  
**Documentation:** Complete  
**Testing:** All tests passing
