# Architecture Documentation

## System Overview

The Research PDF Brain is a multi-component system that processes research papers through an intelligent pipeline using LangGraph's agentic architecture.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Google Drive                            │
│                    (Research PDFs)                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   PDF Ingestion Layer                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  PyMuPDF   │  │  PyPDF2    │  │ pdfplumber │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  LangGraph Agent Workflow                    │
│                                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐               │
│  │  Ingest  │──▶│  Chunk   │──▶│Summarize │               │
│  └──────────┘   └──────────┘   └──────────┘               │
│                                       │                      │
│  ┌──────────┐   ┌──────────┐        │                      │
│  │  Embed   │◀──│ Classify │◀────────┘                     │
│  └──────────┘   └──────────┘                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Processing Layer                          │
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │   GPT-4 Turbo    │         │  OpenAI Embeddings│         │
│  │  (Summarization  │         │  (text-emb-3-lg)  │         │
│  │ & Classification)│         │                   │         │
│  └──────────────────┘         └──────────────────┘         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                             │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Master Table │  │  Taxonomy    │  │ FAISS Index  │      │
│  │  (CSV/Excel) │  │    (JSON)    │  │  (Vectors)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAG Search Layer                          │
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │ Semantic Search  │         │ Question Answer  │         │
│  │  (FAISS Query)   │         │   (GPT-4 + RAG)  │         │
│  └──────────────────┘         └──────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. PDF Ingestion Layer

**Purpose**: Robust extraction of text and metadata from PDFs

**Components**:
- **PyMuPDF (fitz)**: Primary extraction engine
  - Fast and reliable
  - Good metadata extraction
  - Handles most academic PDFs
  
- **PyPDF2**: Fallback option
  - Alternative for problematic PDFs
  - Different parsing algorithm
  
- **pdfplumber**: Reserved for complex layouts
  - Table extraction capabilities
  - Better for structured data

**Flow**:
```
PDF File → Try PyMuPDF → Success? → Extract text + metadata
                ↓ Fail
            Try PyPDF2 → Success? → Extract text + metadata
                ↓ Fail
              Error handling → Mark for manual review
```

### 2. LangGraph Agent Workflow

**Purpose**: Orchestrate paper processing through specialized agents

**State Definition**:
```python
class PaperState(TypedDict):
    file_path: str              # Source PDF location
    file_name: str              # PDF filename
    raw_text: str               # Extracted text
    chunks: List[str]           # Text chunks
    metadata: Dict              # PDF metadata
    summary: str                # GPT-4 summary
    tier1_category: str         # Broad field
    tier2_category: str         # Sub-field
    tier3_category: str         # Specific topic
    embeddings: np.ndarray      # Vector embeddings
    error: Optional[str]        # Error messages
```

**Agent Pipeline**:

1. **Ingest Agent**
   - Extracts text from PDF
   - Parses metadata (title, author, etc.)
   - Validates extraction quality
   - Error: Skip if text < 100 chars

2. **Chunk Agent**
   - Splits text into semantic chunks
   - Uses RecursiveCharacterTextSplitter
   - Maintains context with overlap
   - Separators: `\n\n`, `\n`, `. `, ` `

3. **Summarize Agent**
   - Calls GPT-4 for summary
   - Extracts: abstract, contributions, methods, findings
   - Handles long texts (truncation if needed)
   - Retry logic for API failures

4. **Classify Agent**
   - Three-tier classification via GPT-4
   - Tier 1: From predefined categories
   - Tier 2: Discovered from content
   - Tier 3: Most specific topic
   - Structured output parsing

5. **Embed Agent**
   - Generates embeddings for chunks
   - Uses OpenAI text-embedding-3-large
   - 3072-dimensional vectors
   - Batch processing for efficiency

### 3. Processing Layer

**GPT-4 Integration**:
```
Input: Paper text + metadata
  ↓
Prompt Template
  ↓
GPT-4 Turbo API
  ↓
Structured Output (summary or classification)
  ↓
Parse and validate
  ↓
Update state
```

**Embedding Generation**:
```
Input: Text chunks
  ↓
Batch chunks (up to 100)
  ↓
OpenAI Embeddings API
  ↓
3072-dim vectors
  ↓
Store in state
```

### 4. Storage Layer

**Master Table Structure**:
```
Columns:
- file_name: PDF filename
- file_path: Full path
- title: Extracted/metadata title
- author: Author(s)
- page_count: Number of pages
- tier1_category: Broad field
- tier2_category: Sub-field
- tier3_category: Specific topic
- summary: GPT-4 generated summary
- num_chunks: Number of text chunks
- has_error: Processing error flag
- error_message: Error details

Formats: CSV (machine), Excel (human)
```

**Taxonomy Structure**:
```json
{
  "Tier1 Category": {
    "Tier2 Subcategory": {
      "Tier3 Specific Topic": [
        "paper1.pdf",
        "paper2.pdf"
      ]
    }
  }
}
```

**FAISS Index**:
- Vector database for semantic search
- Index type: Flat (exact search)
- Dimension: 3072
- Metadata: source, title, author, categories
- Enables similarity search and RAG

### 5. RAG Search Layer

**Search Architecture**:
```
User Query
  ↓
Embed query (same embedding model)
  ↓
FAISS similarity search
  ↓
Retrieve top-k documents
  ↓
[Optional] GPT-4 synthesis
  ↓
Return results
```

**Search Types**:

1. **Semantic Search**
   - Input: Natural language query
   - Output: Ranked documents with scores
   - Use case: Find similar papers

2. **Question Answering**
   - Input: Question
   - Retrieve relevant context
   - GPT-4 synthesizes answer
   - Cites sources

3. **Category Search**
   - Filter by taxonomy tier
   - Combines text search + metadata
   - Use case: Browse by topic

## Data Flow

### End-to-End Processing

```
1. User provides Google Drive folder path
   ↓
2. System scans for PDFs (recursive)
   ↓
3. For each PDF:
   ├─ Initialize PaperState
   ├─ Run through LangGraph workflow
   │  ├─ Ingest → extract text
   │  ├─ Chunk → split text
   │  ├─ Summarize → GPT-4 summary
   │  ├─ Classify → taxonomy assignment
   │  └─ Embed → generate vectors
   └─ Append to corpus
   ↓
4. Build master table (all papers)
   ↓
5. Build taxonomy (hierarchical structure)
   ↓
6. Build FAISS index (all embeddings)
   ↓
7. Save outputs to Google Drive
   ↓
8. Initialize RAG search engine
   ↓
9. Ready for queries
```

## Performance Characteristics

### Processing Time
- **Per Paper**: 1-2 minutes
  - PDF extraction: 5-10 seconds
  - Chunking: 1-2 seconds
  - Summarization: 20-40 seconds
  - Classification: 15-30 seconds
  - Embedding: 10-20 seconds

- **Corpus Size Impact**:
  - 10 papers: ~15 minutes
  - 100 papers: ~2 hours
  - 1000 papers: ~20 hours

### API Costs
- **GPT-4 Turbo** (per paper):
  - Summarization: $0.01-0.05
  - Classification: $0.005-0.02
  
- **Embeddings** (per paper, avg 20 pages):
  - ~$0.0001 per page = $0.002

- **Total per paper**: ~$0.02-0.08

### Storage Requirements
- **Master table**: ~1KB per paper
- **Taxonomy JSON**: ~10-100KB
- **FAISS index**: ~12MB per 1000 chunks
- **Corpus state**: ~500KB per 100 papers

## Scalability Considerations

### Current Limits
- **Colab RAM**: 12GB (standard), 25GB (Pro)
- **API Rate Limits**: 
  - GPT-4: 10,000 TPM (tokens per minute)
  - Embeddings: 5,000 RPM (requests per minute)

### Optimization Strategies

1. **Batch Processing**
   - Process papers in batches of 50-100
   - Save intermediate results
   - Resume on failure

2. **Caching**
   - Cache embeddings
   - Skip already processed papers
   - Incremental updates

3. **Parallel Processing**
   - Async API calls where possible
   - Concurrent embedding generation
   - Note: Respects rate limits

4. **Memory Management**
   - Stream large PDFs
   - Delete processed raw text
   - Periodic garbage collection

## Error Handling

### Strategy
```
Try primary method
  ↓ Fail
Try fallback method
  ↓ Fail
Log error + continue
  ↓
Mark paper with error flag
  ↓
Continue processing other papers
```

### Error Categories

1. **Extraction Errors**
   - Corrupted PDF
   - Encrypted/protected
   - Scanned image (no text)
   - Action: Mark and skip

2. **API Errors**
   - Rate limit exceeded
   - Timeout
   - Invalid response
   - Action: Retry with backoff

3. **Processing Errors**
   - Out of memory
   - Invalid state
   - Action: Skip paper, log error

## Security Considerations

### API Key Management
- Store in environment variables
- Never commit to repository
- Use Google Colab secrets

### Data Privacy
- PDFs stay in Google Drive
- Processing in user's Colab instance
- No data sent to third parties (except OpenAI APIs)

### Access Control
- User's Google account for Drive access
- User's OpenAI account for API
- No shared credentials

## Future Enhancements

### Planned Features
1. **Citation Extraction**: Parse and link references
2. **Figure/Table Analysis**: Multimodal understanding
3. **Incremental Updates**: Process only new papers
4. **Collaboration**: Shared taxonomies
5. **Advanced Filtering**: Complex search queries
6. **Recommendation Engine**: Suggest related papers
7. **Export Options**: BibTeX, RIS, etc.

### Technical Improvements
1. **Batch API Usage**: More efficient processing
2. **Local Embedding Models**: Reduce API costs
3. **Custom Taxonomy Training**: Learn from user feedback
4. **Distributed Processing**: Scale to larger corpora
5. **Advanced Indexing**: Approximate nearest neighbor search

---

For implementation details, see the source code in `research_pdf_brain.ipynb`.
