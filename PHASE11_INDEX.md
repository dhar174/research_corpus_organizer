# Phase 11 Index - Deep Analysis Pass

**Navigation and Reference Guide**

## Core Files

### Implementation
- **[deep_analysis_pass2.py](deep_analysis_pass2.py)** - Main implementation module
  - All Phase 11 functionality
  - ~800 lines of code
  - OpenAI Responses API integration

### Testing
- **[test_phase11.py](test_phase11.py)** - Comprehensive test suite
  - 9 test functions
  - 100% coverage of core functionality
  - Mock API tests included

### Examples
- **[examples_phase11.py](examples_phase11.py)** - Usage examples
  - 6 complete examples
  - Cost estimation workflows
  - Paper selection strategies

### Documentation
- **[README_PHASE11.md](README_PHASE11.md)** - Detailed user guide
  - Complete feature documentation
  - Usage examples
  - Best practices
  - Troubleshooting

- **[PHASE11_COMPLETION.md](PHASE11_COMPLETION.md)** - Completion report
  - Implementation details
  - Testing results
  - Performance metrics
  - Comparison with Phase 6

- **[PHASE11_SUMMARY.md](PHASE11_SUMMARY.md)** - Quick reference
  - Quick start guide
  - Common patterns
  - Key functions
  - Cost & performance metrics

- **[PHASE11_INDEX.md](PHASE11_INDEX.md)** - This file

## Module Structure

### deep_analysis_pass2.py

```
deep_analysis_pass2.py
├── Step 11.1: Check Deep Analysis Flag
│   ├── should_perform_deep_analysis()
│   └── check_deep_analysis_flag()
│
├── Step 11.2: Deep Analysis Node
│   ├── DeepAnalysisGenerator (class)
│   │   ├── __init__()
│   │   ├── generate_deep_analysis()
│   │   ├── analyze_paper()
│   │   ├── get_stats()
│   │   └── _estimate_call_cost()
│   ├── deep_analysis_node()
│   └── create_deep_analysis_generator()
│
├── Step 11.3: Deep Analysis Prompts
│   ├── DeepAnalysisPromptFactory (class)
│   │   ├── create_system_prompt()
│   │   ├── create_user_prompt()
│   │   └── _truncate_text()
│   └── create_deep_analysis_prompt()
│
├── Step 11.4: Process Selected Papers
│   ├── select_papers_for_deep_analysis()
│   ├── batch_deep_analyze_papers()
│   └── deep_analyze_papers_worker()
│
├── Validation
│   ├── validate_deep_analysis()
│   └── validate_paper_deep_analyses()
│
└── Cost Estimation
    └── estimate_deep_analysis_cost()
```

## Function Reference

### Flag Checking
```python
should_perform_deep_analysis(config: RunConfig) -> bool
check_deep_analysis_flag(state: GraphState) -> bool
```

### Generator
```python
DeepAnalysisGenerator(api_key, model, reasoning_effort, max_tokens, ...)
create_deep_analysis_generator(config: RunConfig, api_key: str) -> DeepAnalysisGenerator
deep_analysis_node(paper_id, state, generator) -> GraphState
```

### Prompts
```python
DeepAnalysisPromptFactory.create_system_prompt() -> str
DeepAnalysisPromptFactory.create_user_prompt(...) -> str
create_deep_analysis_prompt(paper, chunks, config) -> Tuple[str, str]
```

### Paper Selection & Processing
```python
select_papers_for_deep_analysis(papers, config, subset_criteria) -> List[str]
batch_deep_analyze_papers(papers, chunks, config, api_key, ...) -> Tuple[Dict, Dict]
deep_analyze_papers_worker(state, api_key, ...) -> GraphState
```

### Validation
```python
validate_deep_analysis(deep_analysis: str) -> Tuple[bool, Optional[str]]
validate_paper_deep_analyses(papers: Dict) -> Dict[str, Any]
```

### Cost Estimation
```python
estimate_deep_analysis_cost(num_papers, avg_paper_length_chars, model) -> Dict
```

## Test Reference

### test_phase11.py

```
test_phase11.py
├── Test Step 11.1: Check Deep Analysis Flag
│   ├── test_should_perform_deep_analysis()
│   └── test_check_deep_analysis_flag()
│
├── Test Step 11.3: Deep Analysis Prompts
│   ├── test_deep_analysis_prompt_creation()
│   └── test_deep_analysis_prompt_factory()
│
├── Test Step 11.4: Paper Selection
│   └── test_select_papers_for_deep_analysis()
│
├── Test Validation
│   ├── test_validate_deep_analysis()
│   └── test_validate_paper_deep_analyses()
│
├── Test Cost Estimation
│   └── test_estimate_deep_analysis_cost()
│
└── Test Mock API
    └── test_deep_analysis_generator_mock()
```

## Example Reference

### examples_phase11.py

```
examples_phase11.py
├── Example 1: Cost Estimation
│   └── example_cost_estimation()
│
├── Example 2: Checking Deep Analysis Flag
│   └── example_check_flag()
│
├── Example 3: Creating Deep Analysis Prompts
│   └── example_create_prompts()
│
├── Example 4: Paper Selection
│   └── example_select_papers()
│
├── Example 5: Validation
│   └── example_validation()
│
└── Example 6: Complete Workflow
    └── example_complete_workflow()
```

## Quick Access

### Getting Started
1. Read [PHASE11_SUMMARY.md](PHASE11_SUMMARY.md) for quick start
2. Check [examples_phase11.py](examples_phase11.py) for usage patterns
3. Run [test_phase11.py](test_phase11.py) to validate setup

### Development
1. Review [deep_analysis_pass2.py](deep_analysis_pass2.py) for implementation
2. Study [PHASE11_COMPLETION.md](PHASE11_COMPLETION.md) for details
3. Use [README_PHASE11.md](README_PHASE11.md) as reference

### Integration
1. Check [README_PHASE11.md](README_PHASE11.md) integration section
2. See [examples_phase11.py](examples_phase11.py) example 6 for workflow
3. Review [PHASE11_COMPLETION.md](PHASE11_COMPLETION.md) integration points

## Related Files

### Dependencies
- `rag_models.py` - PaperRecord, PaperChunk, RunConfig, GraphState
- `summarization_pass1.py` - Pattern reference for implementation

### Referenced By
- Phase 12 (Export) - Includes deep_summary in exports
- Phase 13 (LangGraph) - Uses deep_analysis_node
- Phase 15 (RAG) - Enhanced context from deep summaries

## Key Concepts

### Deep Analysis vs. Basic Summary

| Aspect | Basic Summary (Phase 6) | Deep Analysis (Phase 11) |
|--------|------------------------|--------------------------|
| Scope | Overview | Technical details |
| Length | 300-500 words | 800-1500 words |
| Tokens | ~1500 | ~4500 |
| Cost | ~$0.0002/paper | ~$0.0015/paper |
| Model | gpt-5-mini | gpt-5.1 |
| When | All papers | Selected papers |

### Selection Criteria

1. **"all"** - All papers with full_summary
2. **"classified"** - Papers with topic classification
3. **"high_confidence"** - Classification confidence ≥ 0.8
4. **List[str]** - Specific paper IDs

### Output Structure

1. Detailed Methodology Breakdown
2. Experimental Setup Details
3. Key Results and Metrics
4. Limitations and Constraints
5. Future Work and Extensions
6. Comprehensive Notes

## Version History

### Version 1.0 (2025-11-23)
- Initial implementation
- All steps from FINAL_NOTEBOOK_ACTION_PLAN.md completed
- Comprehensive testing and documentation

## Navigation Map

```
Start Here
│
├── Quick Start? → PHASE11_SUMMARY.md
├── Examples? → examples_phase11.py
├── Testing? → test_phase11.py
├── Full Guide? → README_PHASE11.md
├── Details? → PHASE11_COMPLETION.md
└── Navigation? → PHASE11_INDEX.md (this file)
```

## Search Tags

#phase11 #deep-analysis #methodology #results #gpt-5.1 #reasoning-effort #detailed-analysis #technical-analysis #experimental-setup #cost-estimation #paper-selection #validation #batch-processing

---

**Phase:** 11 - Deep Analysis Pass (Optional - Pass 2)  
**Status:** Complete ✅  
**Version:** 1.0  
**Date:** 2025-11-23
