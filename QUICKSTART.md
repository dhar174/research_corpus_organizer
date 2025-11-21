# Quick Start Guide - Research PDF Brain

## For Google Colab Users (Recommended)

### Step 1: Upload to Colab
1. Go to [Google Colab](https://colab.research.google.com/)
2. Upload `research_pdf_brain.ipynb`
3. Or use File → Open Notebook → GitHub and paste the repository URL

### Step 2: Prepare Your PDFs
1. Create a folder in Google Drive (e.g., `Research_PDFs`)
2. Upload your research PDFs to this folder
3. You can organize them in subfolders - the system will recursively scan all PDFs

### Step 3: Configure
In the notebook, find the configuration cell and update:

```python
config.DRIVE_FOLDER_PATH = '/content/drive/MyDrive/Research_PDFs'  # Your PDF folder
config.OUTPUT_FOLDER = '/content/drive/MyDrive/Research_Brain_Output'  # Output location
config.OPENAI_API_KEY = 'sk-...'  # Your OpenAI API key
```

### Step 4: Run
Execute all cells in order. The main execution cell will:
1. Authenticate with Google Drive
2. Scan for PDFs
3. Process each paper through the LangGraph pipeline
4. Generate outputs (master table, taxonomy, FAISS index)

### Step 5: Search and Analyze
Use the provided search functions:

```python
# Search for papers
search_papers("transformer neural networks", num_results=5)

# Ask questions
ask_question("What are the latest advances in attention mechanisms?")

# View statistics
show_taxonomy_stats()
```

## Expected Processing Time

- Small corpus (10-50 papers): 15-30 minutes
- Medium corpus (50-200 papers): 1-3 hours  
- Large corpus (200+ papers): 3+ hours

*Time varies based on paper length and API response times*

## Cost Estimation

Using GPT-4 Turbo:
- ~$0.01-0.05 per paper for summarization
- ~$0.005-0.02 per paper for classification
- Embeddings: ~$0.0001 per page

Example: 100 papers × 20 pages = **~$20-40** total

## Output Files

After processing, check your `OUTPUT_FOLDER` for:

1. **master_table.csv / .xlsx** - Spreadsheet with all papers
   - File names, titles, authors
   - Three-tier classification
   - Summaries
   - Metadata

2. **taxonomy.json** - Hierarchical topic structure
   ```json
   {
     "Computer Science": {
       "Machine Learning": {
         "Neural Networks": ["paper1.pdf", "paper2.pdf"],
         "Transformers": ["paper3.pdf"]
       }
     }
   }
   ```

3. **faiss_index/** - Vector database for search
   - Enables semantic search
   - Powers the RAG engine

4. **corpus_state.pkl** - Complete processing results
   - Reload without reprocessing
   - Contains all extracted data

## Tips for Best Results

### PDF Quality
- ✅ Text-based PDFs (most academic papers)
- ❌ Scanned images without OCR
- ⚠️ Password-protected PDFs won't process

### API Key
- Get from [OpenAI Platform](https://platform.openai.com/)
- Ensure you have credits available
- Monitor usage in OpenAI dashboard

### Google Drive
- Keep PDFs organized in folders
- Consistent naming helps (author_year_title.pdf)
- Remove duplicates beforehand

### Search Quality
- Use descriptive queries
- Combine topic keywords
- Try different phrasings

## Troubleshooting

### "No PDF files found"
```python
# Check your path
import os
os.listdir(config.DRIVE_FOLDER_PATH)
```

### "API Rate Limit"
- Wait a few minutes
- Process in smaller batches
- Upgrade OpenAI tier

### "Out of Memory"
- Reduce `CHUNK_SIZE` in config
- Process fewer papers at once
- Use Colab Pro for more RAM

### "PDF extraction failed"
- Try different PDF reader settings
- Re-save PDF with text layer
- Check PDF isn't corrupted

## Loading Previous Results

Don't want to reprocess? Load existing data:

```python
corpus_state, rag_engine = load_existing_corpus()
```

This instantly restores:
- Master table
- Taxonomy
- FAISS index
- RAG search engine

## Advanced Usage

### Filter by Category
```python
# Get all Computer Science papers
cs_papers = corpus_state['master_table'][
    corpus_state['master_table']['tier1_category'] == 'Computer Science'
]
```

### Export Summaries
```python
# Save all summaries to text file
summaries = corpus_state['master_table'][['title', 'summary']]
summaries.to_csv('all_summaries.csv', index=False)
```

### Custom Taxonomy
Edit Tier 1 categories in the config before running:
```python
config.TIER_1_CATEGORIES = [
    'Deep Learning',
    'NLP',
    'Computer Vision',
    'Robotics'
]
```

### Batch Processing
For very large corpora, process in batches:
```python
# Process 50 at a time
all_pdfs = get_pdf_files(config.DRIVE_FOLDER_PATH)
for batch in chunks(all_pdfs, 50):
    # Process batch
    pass
```

## Next Steps

After initial processing:

1. **Explore your taxonomy** - See how papers are organized
2. **Test searches** - Find papers on specific topics  
3. **Ask questions** - Query your research corpus
4. **Refine categories** - Adjust taxonomy if needed
5. **Add more papers** - Incrementally update

## Support

- Issues: [GitHub Issues](https://github.com/dhar174/research_corpus_organizer/issues)
- Docs: See README.md
- Updates: Check for new releases

## Security Notes

⚠️ **Important:**
- Keep your OpenAI API key private
- Don't share notebooks with API keys
- Use environment variables for keys
- Monitor API usage regularly

---

**Ready to get started?** Open the notebook and run the first cell! 🚀
