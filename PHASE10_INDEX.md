# Phase 10: Final Topic Classification - Quick Reference

**Module:** `paper_classification.py`  
**Tests:** `test_phase10.py`  
**Examples:** `examples_phase10.py`

---

## Quick Start

```python
from paper_classification import classification_worker

# Classify all papers
state = classification_worker(state, api_key, validate=True)

# Check results
validation = state['classification_validation']
print(f"Valid: {validation['valid_count']}/{validation['classified_count']}")
```

---

## Main Functions

### Classification

```python
# Initialize classifier
classifier = PaperClassifier(api_key, model, reasoning_effort)

# Classify paper
classification = classifier.classify_paper(paper, hierarchy)

# LangGraph node
state = classify_paper_node(paper_id, state, api_key)
```

### Batch Processing

```python
# With rate limiting
classifications = classify_papers_with_rate_limit(
    papers, hierarchy, api_key, config,
    rate_limit_delay=0.5, max_retries=3
)

# From state
state = batch_classify_papers(state, api_key)
```

### Validation

```python
# Check consistency
is_valid, issues = check_tier_consistency(t1, t2, t3, hierarchy)

# Validate paper
validation = validate_paper_classification(paper, hierarchy)

# Validate all
results = validate_all_classifications(papers, hierarchy)
```

### Updates

```python
# Update single
updated_paper = update_paper_with_classification(
    paper, classification, taxonomy_version
)

# Update batch
updated_papers = update_papers_batch(
    papers, classifications, taxonomy_version
)
```

---

## Classification Result Format

```json
{
  "tier1": {
    "topic_id": "T1_00",
    "confidence": 0.92,
    "reasoning": "Paper focuses on machine learning..."
  },
  "tier2": {
    "topic_id": "T2_00",
    "confidence": 0.88,
    "reasoning": "Specifically about deep learning..."
  },
  "tier3": {
    "topic_id": "T3_00",
    "confidence": 0.85,
    "reasoning": "Uses convolutional networks..."
  },
  "overall_notes": "Strong fit for ML/DL/CNN path"
}
```

---

## Validation Result Format

```python
{
    "valid": True/False,
    "issues": ["list of issues"],
    "paper_id": "paper_001",
    "title": "Paper title"
}
```

---

## Common Patterns

### Classify and Validate

```python
# Classify
state = batch_classify_papers(state, api_key)

# Validate
validation = validate_all_classifications(
    state['papers'], 
    state['topic_hierarchy']
)

# Check anomalies
for anomaly in validation['anomalies']:
    if anomaly['confidence'] < 0.5:
        print(f"Low confidence: {anomaly['paper_id']}")
```

### Handle Low Confidence

```python
validation = validate_all_classifications(papers, hierarchy)

# Filter low confidence
low_conf = [
    a for a in validation['anomalies'] 
    if a['confidence'] < 0.6
]

# Flag for review
for paper in low_conf:
    flag_for_manual_review(paper['paper_id'])
```

### Custom Rate Limiting

```python
# For high API tier
classifications = classify_papers_with_rate_limit(
    papers, hierarchy, api_key, config,
    rate_limit_delay=0.2,  # Faster
    max_retries=2
)

# For low API tier
classifications = classify_papers_with_rate_limit(
    papers, hierarchy, api_key, config,
    rate_limit_delay=2.0,  # Slower
    max_retries=5
)
```

---

## Configuration

```python
config = create_default_config()

# Classification model
config.classification_model = "gpt-5.1-mini"  # or "gpt-5.1"

# Reasoning effort
config.classification_reasoning_effort = "medium"  # none, low, medium, high
```

---

## Error Handling

```python
# Classification errors
classification = classifier.classify_paper(paper, hierarchy)
if "error" in classification:
    print(f"Failed: {classification['error']}")

# Validation errors
validation = validate_paper_classification(paper, hierarchy)
if not validation['valid']:
    print(f"Issues: {validation['issues']}")
```

---

## Testing

```bash
# Run all tests
python test_phase10.py

# Run examples
python examples_phase10.py
```

---

## See Also

- `PHASE10_COMPLETION.md` - Full documentation
- `PHASE10_SUMMARY.md` - Overview
- `FINAL_NOTEBOOK_ACTION_PLAN.md` - Phase 10 requirements
