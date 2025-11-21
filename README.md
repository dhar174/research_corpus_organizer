# Research Corpus Organizer

A RAG (Retrieval-Augmented Generation) PDF Research Corpus System for organizing and analyzing saved research PDFs from arxiv.org and other sources.

## Project Documentation

- **[FINAL_NOTEBOOK_ACTION_PLAN.md](FINAL_NOTEBOOK_ACTION_PLAN.md)** - Comprehensive implementation plan with 22 phases
- **[rag_pdf_system_spec_v_2.md](rag_pdf_system_spec_v_2.md)** - Technical specification v2.1
- **[RAG_PDF_System_Spec_v2_1.pdf](RAG_PDF_System_Spec_v2_1.pdf)** - PDF version of specification

## GitHub Issues

To track implementation progress, create GitHub issues from the action plan:

- **[QUICK_START.md](QUICK_START.md)** - Quick reference for creating issues
- **[ISSUES_README.md](ISSUES_README.md)** - Full documentation for issue creation
- **[issues_definition.yaml](issues_definition.yaml)** - Issue definitions (22 phases)
- **[create_issues.py](create_issues.py)** - Automated issue creation script

### Quick Start

```bash
# Install prerequisites
gh auth login
pip install pyyaml

# Create all 22 GitHub issues
python create_issues.py
```

See [QUICK_START.md](QUICK_START.md) for more details.

## Overview

This system uses LangGraph workflows with GPT-5.1 to:

1. Process academic PDFs from Google Drive
2. Extract metadata and generate summaries
3. Build a hierarchical topic taxonomy (3-tier)
4. Enable RAG-based querying of the corpus

The implementation is designed for Google Colab notebooks with comprehensive error handling, cost tracking, and quality control.
