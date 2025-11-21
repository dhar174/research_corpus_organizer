# Testing and Validation Guide

This document describes how to test and validate the Research PDF Brain system.

## Quick Validation Checklist

Use this checklist to verify the system is working correctly:

### ✅ Pre-Flight Checks

- [ ] Google Colab is accessible
- [ ] OpenAI API key is valid and has credits
- [ ] Google Drive folder with PDFs exists
- [ ] All required packages install successfully

### ✅ Core Functionality

- [ ] Google Drive authentication works
- [ ] PDFs are detected in the folder
- [ ] PDF text extraction succeeds
- [ ] Text chunking produces reasonable chunks
- [ ] GPT-4 summarization generates summaries
- [ ] Classification produces three-tier categories
- [ ] Embeddings are generated
- [ ] FAISS index is created

### ✅ Output Validation

- [ ] master_table.csv is created
- [ ] master_table.xlsx is created
- [ ] taxonomy.json is created
- [ ] faiss_index/ directory exists
- [ ] corpus_state.pkl is saved

### ✅ Search Functionality

- [ ] Semantic search returns relevant results
- [ ] Question answering provides coherent responses
- [ ] Category filtering works
- [ ] Similar paper discovery functions

## Test Scenarios

### Scenario 1: Small Corpus (5-10 Papers)

**Purpose**: Validate basic functionality with minimal API costs

**Setup**:
1. Create a test folder with 5-10 research PDFs
2. Update configuration to point to test folder
3. Run the pipeline

**Expected Results**:
- Processing time: ~10-15 minutes
- All papers successfully processed (or marked with errors if PDFs are problematic)
- Master table contains all papers
- Taxonomy has at least 2-3 Tier 1 categories
- FAISS index is created
- Search returns relevant results

**Validation**:
```python
# Check master table
df = pd.read_csv('master_table.csv')
assert len(df) >= 5, "Should have at least 5 papers"
assert df['summary'].notna().all(), "All papers should have summaries"

# Check taxonomy
with open('taxonomy.json') as f:
    taxonomy = json.load(f)
assert len(taxonomy) > 0, "Taxonomy should not be empty"

# Check search
results = rag_engine.search("machine learning", k=3)
assert len(results) > 0, "Search should return results"
```

### Scenario 2: Diverse Topics

**Purpose**: Test taxonomy classification across different fields

**Setup**:
Papers from different domains:
- Computer Science (ML/AI)
- Physics (Quantum)
- Mathematics (Statistics)
- Biology (Genomics)

**Expected Results**:
- Each field appears as Tier 1 category
- Sub-fields are correctly identified
- Related papers are grouped together

**Validation**:
```python
# Check tier 1 diversity
tier1_counts = df['tier1_category'].value_counts()
assert len(tier1_counts) >= 3, "Should have multiple Tier 1 categories"
```

### Scenario 3: Large Corpus (100+ Papers)

**Purpose**: Test scalability and performance

**Setup**:
1. Large collection of papers (100+)
2. Monitor memory usage
3. Track processing time
4. Watch API costs

**Expected Results**:
- Processing completes without memory errors
- Time: ~2-3 hours
- Cost: ~$20-40 in API calls
- FAISS index builds successfully

**Monitoring**:
```python
import time
start_time = time.time()
corpus_state, rag_engine = run_research_brain()
elapsed = time.time() - start_time

print(f"Processing time: {elapsed/60:.1f} minutes")
print(f"Papers processed: {corpus_state['processed_papers']}")
print(f"Errors: {len(corpus_state['errors'])}")
```

### Scenario 4: Edge Cases

**Purpose**: Test error handling and robustness

**Test PDFs**:
- Empty PDF
- Scanned image (no text layer)
- Very large PDF (100+ pages)
- Corrupted PDF
- Password-protected PDF
- Non-English PDF

**Expected Results**:
- System continues processing other papers
- Errors are logged appropriately
- Error messages are informative
- No crashes or hangs

**Validation**:
```python
# Check error handling
errors_df = df[df['has_error'] == True]
print(f"Papers with errors: {len(errors_df)}")
for idx, row in errors_df.iterrows():
    print(f"  {row['file_name']}: {row['error_message']}")
```

### Scenario 5: Search Quality

**Purpose**: Validate search relevance and quality

**Test Queries**:
1. "transformer neural networks" → Should find transformer papers
2. "quantum entanglement" → Should find quantum physics papers
3. "deep learning optimization" → Should find ML optimization papers

**Expected Results**:
- Relevant papers are ranked higher
- Different queries return different results
- Similar queries return overlapping results

**Validation**:
```python
def test_search_relevance(query, expected_keyword):
    results = rag_engine.search(query, k=5)
    # Check if top results contain expected keyword
    found = any(expected_keyword.lower() in str(doc.page_content).lower() 
               for doc in results[:3])
    assert found, f"Search for '{query}' should find papers about '{expected_keyword}'"

test_search_relevance("transformer", "transformer")
test_search_relevance("quantum", "quantum")
```

### Scenario 6: RAG Question Answering

**Purpose**: Test question answering quality

**Test Questions**:
1. "What are the main approaches to attention mechanisms?"
2. "How do convolutional neural networks work?"
3. "What are the latest advances in quantum computing?"

**Expected Results**:
- Coherent answers based on corpus
- Citations to source papers
- Relevant context extracted

**Validation**:
```python
answer = rag_engine.answer_question("What are transformers in machine learning?")
assert len(answer) > 100, "Answer should be substantial"
assert "Source:" in answer or "paper" in answer.lower(), "Should cite sources"
```

## Performance Benchmarks

### Expected Performance Metrics

| Metric | Small (10) | Medium (50) | Large (200) |
|--------|-----------|------------|-------------|
| Processing Time | 15-20 min | 1-2 hours | 4-6 hours |
| API Cost | $0.50-1 | $3-5 | $15-30 |
| Memory Usage | <2 GB | <4 GB | <8 GB |
| FAISS Index Size | <5 MB | ~20 MB | ~80 MB |
| Search Speed | <1 sec | <1 sec | <2 sec |

### Optimization Tips

1. **Reduce Chunk Size**: Lower CHUNK_SIZE if memory is tight
2. **Batch Processing**: Process papers in batches of 50
3. **Resume Capability**: Save state periodically to resume on failure
4. **API Optimization**: Cache embeddings, reuse summaries

## Common Issues and Solutions

### Issue: PDF Extraction Fails

**Symptoms**:
- Empty text extracted
- "Failed to extract meaningful text" error

**Solutions**:
1. Check if PDF is scanned image (needs OCR)
2. Try different PDF library
3. Re-save PDF with text layer
4. Verify PDF is not corrupted

**Test**:
```python
text, metadata = extract_text_from_pdf("test.pdf")
print(f"Extracted {len(text)} characters")
print(f"Pages: {metadata.get('page_count', 0)}")
```

### Issue: API Rate Limits

**Symptoms**:
- "Rate limit exceeded" errors
- Slow processing

**Solutions**:
1. Add delays between API calls
2. Use batch processing
3. Upgrade OpenAI tier
4. Process during off-peak hours

**Test**:
```python
import time
for paper in papers[:5]:
    process_paper(paper)
    time.sleep(5)  # Add delay
```

### Issue: Out of Memory

**Symptoms**:
- Colab crashes
- Memory error messages

**Solutions**:
1. Use Colab Pro (more RAM)
2. Reduce CHUNK_SIZE
3. Process fewer papers at once
4. Clear variables after processing

**Test**:
```python
import psutil
print(f"Memory usage: {psutil.virtual_memory().percent}%")
```

### Issue: Poor Search Results

**Symptoms**:
- Irrelevant papers returned
- Empty search results

**Solutions**:
1. Verify FAISS index was built
2. Check embeddings are generated
3. Reload vectorstore
4. Try different query phrasing

**Test**:
```python
# Test embedding generation
test_text = "machine learning"
embedding = embedding_generator.generate_embedding(test_text)
print(f"Embedding shape: {embedding.shape}")
assert embedding.shape[0] == 3072, "Embedding dimension should be 3072"
```

## Automated Testing

### Unit Test Examples

```python
import unittest

class TestPDFBrain(unittest.TestCase):
    
    def test_pdf_extraction(self):
        """Test PDF text extraction"""
        text, metadata = extract_text_from_pdf("sample.pdf")
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)
        self.assertIn('page_count', metadata)
    
    def test_chunking(self):
        """Test text chunking"""
        text = "This is a test. " * 1000
        chunks = chunk_text(text, chunk_size=500, chunk_overlap=100)
        self.assertGreater(len(chunks), 0)
        self.assertLess(len(chunks[0]), 600)
    
    def test_taxonomy_classification(self):
        """Test taxonomy classification"""
        tier1, tier2, tier3 = ("Computer Science", "Machine Learning", "Neural Networks")
        self.assertIn(tier1, config.TIER_1_CATEGORIES + ["Computer Science", "Other"])
        self.assertIsInstance(tier2, str)
        self.assertIsInstance(tier3, str)
    
    def test_search(self):
        """Test search functionality"""
        results = rag_engine.search("test query", k=3)
        self.assertLessEqual(len(results), 3)
    
    def test_master_table_format(self):
        """Test master table has required columns"""
        required_cols = ['file_name', 'title', 'tier1_category', 'summary']
        for col in required_cols:
            self.assertIn(col, df.columns)

if __name__ == '__main__':
    unittest.main()
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Test Research PDF Brain

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Validate notebook
      run: |
        python -c "import json; json.load(open('research_pdf_brain.ipynb'))"
    - name: Check code style
      run: |
        pip install black
        black --check *.py
```

## Manual Testing Checklist

Before releasing or merging changes:

- [ ] Test with fresh Colab instance
- [ ] Test with small corpus (5 papers)
- [ ] Verify all outputs are generated
- [ ] Test search functionality
- [ ] Test question answering
- [ ] Check error handling with bad PDFs
- [ ] Verify API costs are reasonable
- [ ] Test documentation examples work
- [ ] Ensure notebook cells run in order
- [ ] Clear all cell outputs before committing

## Reporting Issues

When reporting bugs, include:

1. **Environment**: Colab or local, Python version
2. **Steps to Reproduce**: Exact sequence of actions
3. **Expected vs Actual**: What should happen vs what happened
4. **Logs/Errors**: Complete error messages
5. **Sample Data**: Example PDF if relevant (or description)
6. **Configuration**: Settings used

Example bug report:
```
**Environment**: Google Colab, Python 3.10
**Issue**: PDF extraction fails for scanned documents
**Steps**:
1. Upload scanned PDF to Drive
2. Run pipeline
3. See error "Failed to extract meaningful text"
**Expected**: Should extract text or provide OCR option
**Actual**: Error and skip paper
**Logs**: [paste error]
```

---

For questions or help with testing, see CONTRIBUTING.md or open a GitHub issue.
