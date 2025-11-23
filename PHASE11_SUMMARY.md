# Phase 11 Summary - Deep Analysis Pass

**Quick Reference Guide**

## What is Phase 11?

Optional detailed analysis pass that extracts comprehensive methodology, experimental setup, results, and limitations from research papers using GPT-5.1 with high reasoning effort.

## When to Use

✅ **Use deep analysis when:**
- Building comprehensive knowledge bases
- Papers will be heavily referenced or replicated
- Need detailed technical understanding
- Budget allows (~$0.001-0.002 per paper)

❌ **Skip deep analysis when:**
- Basic summaries are sufficient (Phase 6 already provides good summaries)
- Large corpora with budget constraints
- Papers are well-documented elsewhere

## Quick Start

```python
from rag_models import create_default_config
from deep_analysis_pass2 import (
    should_perform_deep_analysis,
    batch_deep_analyze_papers,
    estimate_deep_analysis_cost
)

# 1. Enable in config
config = create_default_config()
config.enable_deep_analysis_pass = True

# 2. Estimate cost
estimate = estimate_deep_analysis_cost(
    num_papers=len(papers),
    model="gpt-5.1"
)
print(f"Cost: ${estimate['estimated_cost_usd']:.2f}")

# 3. Process papers
if should_perform_deep_analysis(config):
    updated_papers, stats = batch_deep_analyze_papers(
        papers=papers,
        chunks=chunks,
        config=config,
        api_key=api_key,
        subset_criteria="high_confidence"  # Only high-confidence papers
    )
    
    print(f"Analyzed: {stats['papers_analyzed']}")
```

## Selection Criteria

Choose which papers to analyze:

```python
# All eligible papers (with summaries)
subset_criteria="all"

# Only classified papers
subset_criteria="classified"

# High confidence papers (≥0.8 confidence)
subset_criteria="high_confidence"

# Specific papers
subset_criteria=["paper_1", "paper_2", "paper_3"]
```

## Output Format

Deep analysis includes:

1. **Detailed Methodology Breakdown**: Specific algorithms, datasets, techniques
2. **Experimental Setup Details**: Parameters, configurations, baselines
3. **Key Results and Metrics**: Quantitative results, statistical significance
4. **Limitations and Constraints**: Acknowledged limitations, assumptions
5. **Future Work and Extensions**: Research directions, improvements
6. **Comprehensive Notes**: Technical implementation details

## Key Functions

| Function | Purpose |
|----------|---------|
| `should_perform_deep_analysis()` | Check if enabled |
| `estimate_deep_analysis_cost()` | Estimate API costs |
| `select_papers_for_deep_analysis()` | Select papers by criteria |
| `batch_deep_analyze_papers()` | Process papers in batch |
| `validate_paper_deep_analyses()` | Validate outputs |

## Configuration

```python
config = RunConfig(
    enable_deep_analysis_pass=True,  # Enable Phase 11
    # Recommended settings:
    # - Model: gpt-5.1 (automatically used when enabled)
    # - Reasoning effort: high (automatically set)
    # - Max tokens: 4000 (automatically set)
)
```

## Cost & Performance

| Metric | Value |
|--------|-------|
| Tokens per paper | ~4500 |
| Cost per paper (GPT-5.1) | ~$0.0015 |
| Time per paper | ~1.5-2 seconds |
| 100 papers cost | ~$0.15 |
| 100 papers time | ~2.5-3.5 minutes |

## Files

- `deep_analysis_pass2.py` - Main implementation
- `test_phase11.py` - Test suite
- `examples_phase11.py` - Usage examples
- `README_PHASE11.md` - Detailed documentation
- `PHASE11_COMPLETION.md` - Completion report

## Testing

```bash
# Run tests
python test_phase11.py

# Run examples
python examples_phase11.py
```

## Integration

### With LangGraph

```python
from deep_analysis_pass2 import deep_analysis_node

# Add to workflow
state = deep_analysis_node(
    paper_id=paper_id,
    state=current_state,
    generator=generator
)
```

### With Other Phases

- **After Phase 6**: Requires full_summary to be present
- **Before/After Phase 10**: Works with or without classification
- **Before Phase 12**: deep_summary included in exports

## Common Issues

**"Deep analysis is disabled"**
→ Set `config.enable_deep_analysis_pass = True`

**"No papers selected"**
→ Ensure papers have `full_summary` and status is "summarized" or later

**High costs**
→ Use `subset_criteria="high_confidence"` to limit papers

## Best Practices

1. ✅ Always estimate cost first
2. ✅ Use selective criteria for large corpora
3. ✅ Validate outputs after processing
4. ✅ Process in batches if budget-constrained
5. ✅ Use GPT-5.1 (not gpt-5-mini) for best results

## Example Workflow

```python
# Complete workflow
config.enable_deep_analysis_pass = True

# 1. Estimate
estimate = estimate_deep_analysis_cost(num_papers=50)
print(f"Estimated: ${estimate['estimated_cost_usd']:.2f}")

# 2. Select high-value papers
selected = select_papers_for_deep_analysis(
    papers, config, "high_confidence"
)
print(f"Selected: {len(selected)} papers")

# 3. Process
updated, stats = batch_deep_analyze_papers(
    papers, chunks, config, api_key, "high_confidence"
)

# 4. Validate
results = validate_paper_deep_analyses(updated)
print(f"Valid: {results['validation_rate']:.1%}")

# 5. Use results
for paper_id, paper in updated.items():
    if paper.deep_summary:
        print(f"{paper.title}: {len(paper.deep_summary)} chars")
```

---

**Status:** Complete ✅  
**Version:** 1.0  
**Date:** 2025-11-23
