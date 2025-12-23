#!/usr/bin/env python3
"""
RAG PDF Research Corpus System - Setup Configuration

This setup.py is a thin wrapper for backward compatibility.
The project metadata is now defined in pyproject.toml.

For modern installations, use:
    pip install .
    pip install -e .  # for development

For building distributions:
    python -m build

Version: 1.0.0
Date: 2025-11-25
"""

from setuptools import setup

# This setup.py is kept for backward compatibility with older pip versions.
# All configuration is now in pyproject.toml
if __name__ == "__main__":
    setup()
