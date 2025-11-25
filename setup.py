#!/usr/bin/env python3
"""
RAG PDF Research Corpus System - Setup Configuration

This setup.py enables installation of the RAG PDF Research Corpus System
as a Python package for easy deployment and distribution.

Usage:
    # Install in development mode
    pip install -e .
    
    # Install from PyPI (when published)
    pip install rag-pdf-research-corpus
    
    # Build distribution packages
    python setup.py sdist bdist_wheel

Version: 1.0.0
Date: 2025-11-25
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README for the long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Core dependencies required for basic functionality
CORE_DEPENDENCIES = [
    "pydantic>=2.0.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "tqdm>=4.65.0",
    "requests>=2.31.0",
    "python-dateutil>=2.8.2",
]

# PDF processing dependencies
PDF_DEPENDENCIES = [
    "pymupdf>=1.23.0",
]

# AI/ML dependencies
AI_DEPENDENCIES = [
    "openai>=1.3.0",
    "langgraph>=0.0.30",
    "langchain>=0.1.0",
    "faiss-cpu>=1.7.4",
    "scikit-learn>=1.3.0",
]

# Optional dependencies for enhanced functionality
OPTIONAL_DEPENDENCIES = {
    "ocr": [
        "pytesseract>=0.3.10",
        "Pillow>=10.0.0",
    ],
    "clustering": [
        "hdbscan>=0.8.33",
    ],
    "visualization": [
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
    ],
    "dev": [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "black>=23.0.0",
        "isort>=5.12.0",
        "flake8>=6.0.0",
        "mypy>=1.0.0",
    ],
}

# All optional dependencies combined
OPTIONAL_DEPENDENCIES["all"] = (
    OPTIONAL_DEPENDENCIES["ocr"] +
    OPTIONAL_DEPENDENCIES["clustering"] +
    OPTIONAL_DEPENDENCIES["visualization"]
)

# Full development setup
OPTIONAL_DEPENDENCIES["full"] = (
    OPTIONAL_DEPENDENCIES["all"] +
    OPTIONAL_DEPENDENCIES["dev"]
)

setup(
    name="rag-pdf-research-corpus",
    version="1.0.0",
    author="Research Corpus Organizer",
    author_email="",
    description="A comprehensive system for processing and organizing academic PDF research papers using LangGraph, GPT-5, and RAG",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dhar174/research_corpus_organizer",
    project_urls={
        "Bug Tracker": "https://github.com/dhar174/research_corpus_organizer/issues",
        "Documentation": "https://github.com/dhar174/research_corpus_organizer/blob/main/USER_GUIDE.md",
        "Source": "https://github.com/dhar174/research_corpus_organizer",
    },
    
    # Package discovery
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    py_modules=[
        "rag_models",
        "drive_utils",
        "pdf_parser",
        "metadata_extractor",
        "embedding_generator",
        "summarization_pass1",
        "topic_taxonomy",
        "paper_classification",
        "export_manager",
        "workflow_orchestrator",
        "quality_control",
        "rag_query_interface",
        "corpus_utilities",
        "taxonomy_review",
        "deep_analysis_pass2",
        "advanced_visualizations",
    ],
    
    # Dependencies
    install_requires=CORE_DEPENDENCIES + PDF_DEPENDENCIES + AI_DEPENDENCIES,
    extras_require=OPTIONAL_DEPENDENCIES,
    
    # Python version requirement
    python_requires=">=3.10",
    
    # Package classifiers for PyPI
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Text Processing :: General",
        "Topic :: Text Processing :: Indexing",
    ],
    
    # Keywords for PyPI search
    keywords=[
        "research",
        "pdf",
        "rag",
        "retrieval-augmented-generation",
        "langgraph",
        "gpt",
        "openai",
        "academic",
        "papers",
        "corpus",
        "taxonomy",
        "classification",
        "summarization",
        "faiss",
        "embeddings",
        "nlp",
    ],
    
    # Entry points for command-line tools (optional future feature)
    entry_points={
        "console_scripts": [
            # Future: Add CLI tools
            # "rag-corpus=rag_models:main",
        ],
    },
    
    # Include additional files
    include_package_data=True,
    package_data={
        "": [
            "*.md",
            "*.json",
            "*.yaml",
        ],
    },
    
    # Zip-safe flag
    zip_safe=False,
)
