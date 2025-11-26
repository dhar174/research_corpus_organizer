#!/usr/bin/env python3
"""
Package verification tests for PyPI publishing.

These tests verify that the package is correctly configured for distribution:
- Package metadata is complete and valid
- All required modules can be imported
- Version information is consistent
- Dependencies are properly specified

Run with: python test_package_publish.py
"""

import sys
from pathlib import Path


def test_pyproject_toml_exists():
    """Verify pyproject.toml exists and has required fields."""
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    content = pyproject_path.read_text()
    
    # Check for required sections
    assert "[project]" in content, "Missing [project] section"
    assert "[build-system]" in content, "Missing [build-system] section"
    
    # Check for required fields
    assert 'name = "rag-pdf-research-corpus"' in content, "Missing package name"
    assert 'version = "1.0.0"' in content, "Missing version"
    assert 'requires-python = ">=3.10"' in content, "Missing Python version requirement"
    
    print("✓ pyproject.toml is valid")


def test_readme_exists():
    """Verify README.md exists for PyPI description."""
    readme_path = Path(__file__).parent / "README.md"
    assert readme_path.exists(), "README.md not found"
    
    content = readme_path.read_text()
    assert len(content) > 1000, "README.md seems too short"
    assert "# RAG PDF Research Corpus" in content, "Missing title in README"
    assert "## Installation" in content, "Missing installation section"
    
    print("✓ README.md is valid")


def test_license_exists():
    """Verify LICENSE file exists."""
    license_path = Path(__file__).parent / "LICENSE"
    assert license_path.exists(), "LICENSE not found"
    
    content = license_path.read_text()
    assert "MIT License" in content, "Not MIT License"
    
    print("✓ LICENSE is valid")


def test_version_consistency():
    """Verify version is consistent across files."""
    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent))
    
    from rag_models import __version__
    
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    pyproject_content = pyproject_path.read_text()
    
    assert f'version = "{__version__}"' in pyproject_content, \
        f"Version mismatch: rag_models has {__version__}"
    
    print(f"✓ Version {__version__} is consistent")


def test_core_imports():
    """Verify core modules can be imported."""
    sys.path.insert(0, str(Path(__file__).parent))
    
    # Test core model imports
    from rag_models import (
        RunConfig,
        PaperRecord,
        PaperChunk,
        TopicHierarchy,
        GraphState,
        create_default_config,
    )
    
    # Verify classes are available
    assert RunConfig is not None
    assert PaperRecord is not None
    assert PaperChunk is not None
    
    print("✓ Core imports successful")


def test_module_imports():
    """Verify all documented modules can be imported."""
    sys.path.insert(0, str(Path(__file__).parent))
    
    modules = [
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
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            # Allow failures for modules with optional dependencies
            failed.append((module, str(e)))
            print(f"  ⚠ {module}: {e}")
    
    # Only fail for core modules
    core_modules = ["rag_models"]
    core_failed = [m for m, _ in failed if m in core_modules]
    
    assert not core_failed, f"Core module imports failed: {core_failed}"
    
    print("✓ Module imports checked")


def test_create_config():
    """Verify RunConfig can be instantiated with defaults."""
    sys.path.insert(0, str(Path(__file__).parent))
    
    from rag_models import RunConfig, create_default_config
    
    # Test with defaults
    config = create_default_config()
    assert config is not None
    assert config.drive_folder_path == "PDFs"
    
    # Test with custom values
    config = create_default_config(
        drive_folder_path="CustomFolder",
        max_papers_per_run=10,
    )
    assert config.drive_folder_path == "CustomFolder"
    assert config.max_papers_per_run == 10
    
    print("✓ RunConfig creation works")


def test_manifest_in_exists():
    """Verify MANIFEST.in exists for source distribution."""
    manifest_path = Path(__file__).parent / "MANIFEST.in"
    assert manifest_path.exists(), "MANIFEST.in not found"
    
    content = manifest_path.read_text()
    assert "include LICENSE" in content, "LICENSE not included in MANIFEST.in"
    assert "include README.md" in content, "README.md not included in MANIFEST.in"
    
    print("✓ MANIFEST.in is valid")


def run_all_tests():
    """Run all package verification tests."""
    print("\n" + "=" * 60)
    print("Package Verification Tests")
    print("=" * 60 + "\n")
    
    tests = [
        test_pyproject_toml_exists,
        test_readme_exists,
        test_license_exists,
        test_version_consistency,
        test_core_imports,
        test_module_imports,
        test_create_config,
        test_manifest_in_exists,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
