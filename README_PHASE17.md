# Phase 17: Cost Tracking and Optimization

**Version:** 1.0  
**Date:** 2025-11-24  
**Status:** ✅ Complete

---

## Overview

Phase 17 implements comprehensive cost tracking, budget controls, and cost optimization strategies for the RAG PDF Research Corpus System. This phase adds the ability to monitor API costs in real-time, enforce budget limits, and provide recommendations for cost savings.

---

## Features Implemented

### ✅ Step 17.1: Cost Tracking

- **CostTracker Class**: Core tracking system that monitors all API calls
- **API Call Recording**: Tracks every OpenAI API call with full details
- **Token Usage Calculation**: Accurately calculates input and output tokens
- **Cost Estimation**: Uses current OpenAI pricing to estimate costs
- **Running Total Display**: Shows cumulative costs during pipeline execution
- **Budget Warnings**: Alerts when approaching budget limits (configurable threshold)

### ✅ Step 17.2: Cost Optimization

- **Tiered Model Selection**: Configure cheaper models for bulk tasks via `use_tiered_models`
- **Batch API Calls**: 50% discount when using OpenAI Batch API (`batch_api_calls=True`)
- **Result Caching**: Cache API results to avoid duplicate calls (`enable_result_caching=True`)
- **Rate Limiting**: Implicit via budget controls - operations pause when budget exceeded
- **Cost-Saving Recommendations**: Automated suggestions based on usage patterns

### ✅ Step 17.3: Budget Controls

- **Maximum Cost Per Run**: Set `max_cost_per_run` in RunConfig
- **Budget Exceeded Exception**: Raises `BudgetExceededError` when limit reached
- **Cost Approval**: Budget limits act as automatic approval gates
- **Expenditure Logging**: All API calls logged with timestamps and costs
- **Comprehensive Reports**: Generate detailed cost reports in JSON format

---

## Configuration

### RunConfig Parameters

Add these fields to your `RunConfig`:

```python
from rag_models import RunConfig

config = RunConfig(
    # ... other config ...
    
    # Budget and cost control
    max_cost_per_run=10.0,              # Maximum cost in USD (None = unlimited)
    cost_warning_threshold=0.8,          # Warn at 80% of budget
    enable_cost_tracking=True,           # Enable/disable tracking
    enable_result_caching=True,          # Cache results to avoid duplicates
    batch_api_calls=True,                # Use batch API for 50% savings
)
```

---

## Usage Examples

### Basic Cost Tracking

```python
from rag_models import RunConfig, CostTracker

# Create config with cost tracking
config = RunConfig(
    drive_folder_path="PDFs",
    enable_cost_tracking=True,
)

# Create cost tracker
tracker = CostTracker(config)

# Record an API call
tracker.record_api_call(
    operation="summarization",
    model="gpt-5-mini",
    input_tokens=5000,
    output_tokens=2000,
    paper_id="paper_001",
)

# View current cost
print(f"Total cost: ${tracker.total_cost:.4f}")

# Print detailed report
tracker.print_summary()
```

### Budget Controls

```python
from rag_models import RunConfig, CostTracker, BudgetExceededError

config = RunConfig(
    max_cost_per_run=5.0,  # $5 budget
    cost_warning_threshold=0.75,  # Warn at 75%
    enable_cost_tracking=True,
)

tracker = CostTracker(config)

try:
    # Process papers
    for paper in papers:
        tracker.record_api_call(
            operation="summarization",
            model="gpt-5-mini",
            input_tokens=5000,
            output_tokens=2000,
            paper_id=paper.id,
        )
except BudgetExceededError as e:
    print(f"Budget exceeded: {e}")
    tracker.print_summary()
```

### Integration with Workflow

```python
from rag_models import RunConfig, StateManager
from workflow_orchestrator import (
    initialize_cost_tracking,
    update_cost_tracking,
    check_budget_before_operation,
    print_cost_summary,
)

# Create state with cost tracking
config = RunConfig(
    enable_cost_tracking=True,
    max_cost_per_run=20.0,
)

state = StateManager.create_initial_state(config)
state = initialize_cost_tracking(state)

# Check budget before expensive operation
if check_budget_before_operation(state, "summarization", estimated_tokens=50000):
    # Proceed with operation
    state = update_cost_tracking(
        state,
        operation="summarization",
        model="gpt-5-mini",
        input_tokens=5000,
        output_tokens=2000,
    )

# Print summary at end
print_cost_summary(state)
```

---

## API Pricing

Current OpenAI pricing (as of 2025-11):

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| gpt-5-mini | $0.10 | $0.40 |
| gpt-5 | $3.00 | $15.00 |
| o4-mini | $0.15 | $0.60 |
| o4 | $5.00 | $20.00 |
| text-embedding-3-small | $0.02 | - |
| text-embedding-3-large | $0.13 | - |

**Batch API Discount:** 50% off all models when using batch endpoints

---

## Cost Report Format

The `CostReport` includes:

```json
{
  "start_time": "2025-11-24T10:00:00",
  "end_time": "2025-11-24T10:30:00",
  "total_cost": 0.1234,
  "embedding_cost": 0.0100,
  "summarization_cost": 0.0800,
  "taxonomy_cost": 0.0200,
  "classification_cost": 0.0134,
  "other_cost": 0.0000,
  "total_input_tokens": 125000,
  "total_output_tokens": 45000,
  "total_tokens": 170000,
  "total_api_calls": 156,
  "api_calls_by_operation": {
    "embedding": 100,
    "summarization": 50,
    "classification": 5,
    "taxonomy": 1
  },
  "budget_limit": 10.0,
  "budget_remaining": 9.8766,
  "budget_utilization": 0.0123,
  "warnings": [
    "High total cost detected"
  ],
  "recommendations": [
    "Enable batch_api_calls in config for 50% cost savings",
    "Consider using gpt-5-mini for summarization (10-30x cheaper)"
  ]
}
```

---

## Cost Optimization Strategies

### 1. Use Batch API

Enable `batch_api_calls=True` for 50% discount:

```python
config = RunConfig(
    batch_api_calls=True,  # Save 50%!
)
```

### 2. Enable Caching

Avoid duplicate API calls:

```python
config = RunConfig(
    enable_result_caching=True,
)
```

### 3. Use Cheaper Models

For bulk operations, use `gpt-5-mini` instead of `gpt-5`:

```python
config = RunConfig(
    summary_model="gpt-5-mini",        # 30x cheaper than gpt-5
    classification_model="gpt-5-mini",  # 30x cheaper than gpt-5
    embedding_model="text-embedding-3-small",  # 6.5x cheaper than large
)
```

### 4. Set Token Limits

Limit output tokens to control costs:

```python
config = RunConfig(
    max_tokens_per_summary=1500,       # Reduce from default 2000
    max_tokens_per_classification=500,  # Reduce from default 1000
)
```

### 5. Process in Batches

Process papers in smaller batches with budget limits:

```python
config = RunConfig(
    max_cost_per_run=1.0,     # Process $1 worth at a time
    max_papers_per_run=10,     # Limit papers per batch
)
```

---

## Testing

Run the Phase 17 test suite:

```bash
python test_phase17.py
```

Test coverage includes:
- ✅ Cost estimation for all models
- ✅ Batch API discount (50%)
- ✅ Budget controls and warnings
- ✅ Result caching
- ✅ Cost report generation
- ✅ GraphState integration
- ✅ Serialization/deserialization

---

## Examples

Run the examples to see cost tracking in action:

```bash
python examples_phase17.py
```

Examples demonstrate:
1. Basic cost tracking
2. Budget controls and warnings
3. Cost optimization with caching
4. Batch API savings
5. Cost report generation
6. Integration with GraphState

---

## Files Modified/Created

### Created
- `test_phase17.py` - Comprehensive test suite (500+ lines)
- `examples_phase17.py` - Usage examples (400+ lines)
- `README_PHASE17.md` - This documentation

### Modified
- `rag_models.py`:
  - Added `CostTracker` class (600+ lines)
  - Added `APICallRecord` model
  - Added `CostReport` model
  - Added `BudgetExceededError` exception
  - Added budget fields to `RunConfig`
  - Added cost fields to `GraphState`

- `workflow_orchestrator.py`:
  - Added `initialize_cost_tracking()`
  - Added `update_cost_tracking()`
  - Added `check_budget_before_operation()`
  - Added `print_cost_summary()`
  - Added `get_cost_recommendations()`
  - Added `save_cost_report()`
  - Updated `supervisor_node()` to initialize tracking

---

## Best Practices

### 1. Always Set a Budget

Prevent runaway costs:

```python
config = RunConfig(
    max_cost_per_run=20.0,  # Never spend more than $20
)
```

### 2. Monitor Costs Regularly

Check costs after each phase:

```python
from workflow_orchestrator import print_cost_summary

# After each phase
print_cost_summary(state)
```

### 3. Use Batch API for Production

For processing many papers:

```python
config = RunConfig(
    batch_api_calls=True,  # 50% savings
)
```

### 4. Cache Results

Especially useful during development/testing:

```python
config = RunConfig(
    enable_result_caching=True,
)
```

### 5. Review Recommendations

After each run, check recommendations:

```python
from workflow_orchestrator import get_cost_recommendations

recommendations = get_cost_recommendations(state)
for rec in recommendations:
    print(f"💡 {rec}")
```

---

## Troubleshooting

### Cost Tracking Not Working

**Problem:** `total_cost` is always 0.0

**Solution:** Ensure `enable_cost_tracking=True` in config:

```python
config = RunConfig(
    enable_cost_tracking=True,  # Must be True!
)
```

### Budget Exceeded Immediately

**Problem:** `BudgetExceededError` raised on first API call

**Solution:** Increase budget limit:

```python
config = RunConfig(
    max_cost_per_run=10.0,  # Increase from 1.0
)
```

### Inaccurate Cost Estimates

**Problem:** Costs don't match actual OpenAI billing

**Solution:** Pricing in `CostTracker.PRICING` may be outdated. Update to current OpenAI pricing:

```python
# In rag_models.py, CostTracker class
PRICING = {
    "gpt-5-mini": {
        "input": 0.10 / 1_000_000,   # Update with current pricing
        "output": 0.40 / 1_000_000,
    },
    # ... etc
}
```

---

## Future Enhancements

Potential improvements for future phases:

1. **Real-time Cost Dashboard**: Web-based dashboard showing costs in real-time
2. **Cost Alerts**: Email/Slack notifications when approaching budget
3. **Historical Cost Analysis**: Track costs over time, identify trends
4. **Per-Paper Cost Breakdown**: Show which papers are most expensive
5. **Cost-Based Prioritization**: Process cheaper papers first
6. **Multi-Account Support**: Distribute work across multiple API keys
7. **Automatic Model Selection**: Choose model based on budget constraints

---

## Summary

Phase 17 provides comprehensive cost tracking and optimization for the RAG PDF pipeline:

✅ **Track all API costs** with token-level precision  
✅ **Enforce budget limits** to prevent overspending  
✅ **Optimize costs** with caching and batch API  
✅ **Generate reports** for cost analysis  
✅ **Get recommendations** for cost savings  

With Phase 17, you can confidently run the pipeline while staying within budget and optimizing for cost efficiency.

---

## Support

For questions or issues with Phase 17:

1. Check the examples in `examples_phase17.py`
2. Run the tests in `test_phase17.py`
3. Review the cost recommendations in the cost report
4. Check the OpenAI pricing page for updated rates

---

**Phase 17 Status:** ✅ Complete  
**Next Phase:** Phase 18 (Error Handling and Resilience)
