# GitHub Actions Workflow Setup

This document contains the GitHub Actions workflow configuration for automated PyPI publishing.

## Setup Instructions

### 1. Create the Workflow Directory

```bash
mkdir -p .github/workflows
```

### 2. Create the Publish Workflow

Create `.github/workflows/publish.yml` with the following content:

```yaml
# Publish Python Package to PyPI
# 
# This workflow builds and publishes the package to PyPI using Trusted Publishing (OIDC).
# It is triggered when a release is published on GitHub.
#
# To set up Trusted Publishing:
# 1. Go to PyPI -> Your Project -> Publishing -> Add new publisher
# 2. Select GitHub
# 3. Enter: 
#    - Owner: dhar174
#    - Repository: research_corpus_organizer
#    - Workflow name: publish.yml
#    - Environment: pypi (optional, for more control)
#
# See: https://docs.pypi.org/trusted-publishers/

name: Publish to PyPI

on:
  release:
    types: [published]
  workflow_dispatch:  # Allow manual trigger for testing

jobs:
  build:
    name: Build distribution
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install build dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install build twine

      - name: Build package
        run: python -m build

      - name: Check distribution
        run: python -m twine check dist/*

      - name: Upload distribution artifacts
        uses: actions/upload-artifact@v4
        with:
          name: python-package-distributions
          path: dist/

  publish-to-pypi:
    name: Publish to PyPI
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/project/rag-pdf-research-corpus/
    permissions:
      id-token: write  # Required for OIDC trusted publishing
    steps:
      - name: Download distribution artifacts
        uses: actions/download-artifact@v4
        with:
          name: python-package-distributions
          path: dist/

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # No need for PYPI_API_TOKEN with Trusted Publishing
        # The action uses OIDC to authenticate

  publish-to-testpypi:
    name: Publish to TestPyPI
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'workflow_dispatch'
    environment:
      name: testpypi
      url: https://test.pypi.org/project/rag-pdf-research-corpus/
    permissions:
      id-token: write
    steps:
      - name: Download distribution artifacts
        uses: actions/download-artifact@v4
        with:
          name: python-package-distributions
          path: dist/

      - name: Publish to TestPyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/
```

### 3. Create a CI Workflow (Optional)

For continuous integration testing, create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[dev]"
      
      - name: Run package verification tests
        run: python test_package_publish.py
      
      - name: Build package
        run: python -m build
      
      - name: Check package
        run: python -m twine check dist/*
```

### 4. Set Up PyPI Trusted Publishing

1. Go to [PyPI](https://pypi.org) → Your Projects → `rag-pdf-research-corpus` → Publishing
2. Under "Add a new publisher", select **GitHub**
3. Enter:
   - **PyPI Project Name:** `rag-pdf-research-corpus`
   - **Owner:** `dhar174`
   - **Repository name:** `research_corpus_organizer`
   - **Workflow name:** `publish.yml`
   - **Environment name:** `pypi` (optional, leave blank for simpler setup)
4. Click "Add"

### 5. Create a Release

1. Go to GitHub → Releases → "Create a new release"
2. Create a tag (e.g., `v1.0.0`)
3. Write release notes
4. Publish the release
5. The `publish.yml` workflow will automatically build and publish to PyPI

## Testing with TestPyPI

1. Set up Trusted Publishing on TestPyPI similarly to PyPI
2. Go to GitHub Actions → "Publish to PyPI" → "Run workflow"
3. This will publish to TestPyPI for testing

## Verifying the Package

After publishing, verify the package:

```bash
# From PyPI
pip install rag-pdf-research-corpus

# From TestPyPI
pip install -i https://test.pypi.org/simple/ rag-pdf-research-corpus
```
