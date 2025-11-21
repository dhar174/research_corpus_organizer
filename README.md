# Research PDF Brain 🧠

A Colab-based "research PDF brain" for Google Drive that intelligently organizes, analyzes, and searches through research papers using advanced AI and RAG (Retrieval-Augmented Generation) techniques.

## Overview

This system provides a comprehensive solution for managing and searching through research PDF collections stored in Google Drive. It leverages LangGraph's agentic architecture to orchestrate a sophisticated pipeline that:

- 📥 **Ingests PDFs** from Google Drive folders
- 📄 **Parses and chunks** documents intelligently
- 🤖 **Extracts metadata** and generates GPT-powered summaries
- 🏷️ **Builds a three-tier topic taxonomy** for classification
- 🔍 **Creates vector embeddings** and FAISS index for semantic search
- 📊 **Outputs a master table** with all paper information
- 💬 **Provides RAG-powered tools** for fast, structured literature search

## Features

### 🤖 LangGraph Agentic Architecture
- Utilizes LangGraph's state-based workflow for robust processing
- Each paper flows through a series of intelligent agents:
  1. **Ingestion Agent** - Extracts text and metadata from PDFs
  2. **Chunking Agent** - Intelligently splits content into semantic chunks
  3. **Summarization Agent** - Generates comprehensive GPT-4 summaries
  4. **Classification Agent** - Categorizes papers into three-tier taxonomy
  5. **Embedding Agent** - Creates vector embeddings for semantic search

### 🏷️ Three-Tier Topic Taxonomy
Automatically classifies papers into a hierarchical structure:
- **Tier 1**: Broad field (Computer Science, Physics, Mathematics, etc.)
- **Tier 2**: Sub-field (Machine Learning, Quantum Physics, etc.)
- **Tier 3**: Specific topic (Transformer Models, Quantum Entanglement, etc.)

### 🔍 Advanced Search Capabilities
- **Semantic Search**: Find papers by meaning, not just keywords
- **Question Answering**: Ask questions and get answers from your corpus
- **Similar Paper Discovery**: Find related papers automatically
- **Category Filtering**: Search within specific taxonomy categories

### 📊 Comprehensive Output
- **Master Table**: CSV and Excel files with all paper metadata
- **FAISS Index**: Vector database for lightning-fast semantic search
- **Taxonomy JSON**: Complete hierarchical classification structure
- **Corpus State**: Serialized processing results for quick reloading

## Installation & Setup

### 1. Open in Google Colab
Upload `research_pdf_brain.ipynb` to Google Colab or open it directly.

### 2. Configure Settings
Edit the `Config` class in the notebook:

```python
class Config:
    # Google Drive folder containing your PDFs
    DRIVE_FOLDER_PATH = '/content/drive/MyDrive/Research_PDFs'
    
    # Output folder for results
    OUTPUT_FOLDER = '/content/drive/MyDrive/Research_Brain_Output'
    
    # Your OpenAI API key (required)
    OPENAI_API_KEY = 'sk-...'
    
    # Model settings (using GPT-4; update to GPT-5.1 when available)
    MODEL_NAME = 'gpt-4-turbo-preview'
    EMBEDDING_MODEL = 'text-embedding-3-large'
```

### 3. Prepare Your PDFs
Place your research PDFs in the specified Google Drive folder.

### 4. Run the Pipeline
Execute the cells in sequence. The main pipeline runs with:

```python
corpus_state, rag_engine = run_research_brain()
```

## Usage

### Basic Search
```python
# Search for papers on a topic
search_papers("machine learning optimization", num_results=5)
```

### Ask Questions
```python
# Ask questions about your research corpus
ask_question("What are the main approaches to neural network optimization?")
```

### View Statistics
```python
# Display taxonomy distribution
show_taxonomy_stats()
```

### Access Master Table
```python
# View the complete paper database
corpus_state['master_table'].head()
```

### Find Similar Papers
```python
# Find papers similar to a given title
similar = rag_engine.find_similar_papers("Attention Is All You Need", k=5)
for doc in similar:
    print(doc.metadata['title'])
```

### Load Previously Processed Data
```python
# Reload without reprocessing
corpus_state, rag_engine = load_existing_corpus()
```

## Architecture

### LangGraph Workflow
```
┌─────────────┐
│   Ingest    │  Extract text and metadata from PDF
└──────┬──────┘
       │
┌──────▼──────┐
│    Chunk    │  Split into semantic chunks
└──────┬──────┘
       │
┌──────▼──────┐
│  Summarize  │  Generate GPT-4 summary
└──────┬──────┘
       │
┌──────▼──────┐
│  Classify   │  Categorize into taxonomy
└──────┬──────┘
       │
┌──────▼──────┐
│    Embed    │  Create vector embeddings
└──────┬──────┘
       │
       ▼
     [END]
```

### Components

1. **PDF Processing**: Multi-library approach (PyMuPDF, PyPDF2, pdfplumber) for robust extraction
2. **Text Chunking**: RecursiveCharacterTextSplitter with semantic-aware splitting
3. **AI Analysis**: GPT-4 for summaries and classification
4. **Embeddings**: OpenAI text-embedding-3-large (3072 dimensions)
5. **Vector Store**: FAISS for efficient similarity search
6. **RAG Engine**: LangChain-based retrieval augmented generation

## Output Files

After processing, the following files are created in `OUTPUT_FOLDER`:

- `master_table.csv` - Complete paper database (CSV format)
- `master_table.xlsx` - Complete paper database (Excel format)
- `taxonomy.json` - Hierarchical topic taxonomy
- `faiss_index/` - Vector database directory
- `corpus_state.pkl` - Serialized processing state

## Requirements

See `requirements.txt` for complete dependencies. Key packages:
- langchain & langgraph (agentic workflow)
- openai (GPT-4 and embeddings)
- faiss-cpu (vector search)
- PyMuPDF, PyPDF2, pdfplumber (PDF processing)
- google-api-python-client (Google Drive integration)
- pandas, numpy (data processing)

## Performance Considerations

- **Processing Time**: ~1-2 minutes per paper (including GPT-4 calls)
- **API Costs**: Uses GPT-4 for summaries and classification
- **Storage**: FAISS index size depends on corpus (typically 10-50 MB per 100 papers)
- **Memory**: Recommended 8GB+ RAM for large corpora (500+ papers)

## Future Enhancements

- [ ] Update to GPT-5.1 when available
- [ ] Batch processing for faster ingestion
- [ ] Citation extraction and linking
- [ ] Figure and table extraction
- [ ] Multi-modal analysis (images, equations)
- [ ] Collaboration features (shared taxonomies)
- [ ] Advanced filtering and faceted search
- [ ] Paper recommendation engine

## Troubleshooting

### Common Issues

**"No PDF files found"**
- Check the `DRIVE_FOLDER_PATH` configuration
- Ensure Google Drive is mounted correctly
- Verify PDFs are in the specified folder

**"OpenAI API key not set"**
- Set `config.OPENAI_API_KEY` in the configuration cell
- Ensure you have API credits available

**PDF extraction errors**
- Some PDFs may be scanned images (no text layer)
- Try re-saving PDFs with a text layer
- Check PDF permissions/encryption

**Memory errors**
- Process smaller batches
- Reduce `CHUNK_SIZE` in configuration
- Use a Colab instance with more RAM

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

Built with:
- [LangChain](https://langchain.com/) - LLM application framework
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent workflow orchestration
- [OpenAI](https://openai.com/) - GPT-4 and embeddings
- [FAISS](https://faiss.ai/) - Vector similarity search
- [Google Colab](https://colab.research.google.com/) - Cloud notebook platform
