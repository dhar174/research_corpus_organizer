#!/usr/bin/env python3
"""
Quick validation script for Phase 12 implementation.

Tests:
- Module imports
- Basic functionality
- Integration with existing models
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all Phase 12 functions can be imported."""
    print("\n" + "=" * 70)
    print("Testing Phase 12 Imports")
    print("=" * 70)
    
    try:
        from export_manager import (
            # Step 12.1
            export_final_data,
            create_final_export_config,
            
            # Step 12.2
            export_full_csv,
            export_summary_csv,
            export_to_json,
            export_taxonomy_to_json,
            
            # Step 12.3
            generate_statistics_report,
            count_papers_by_status,
            count_papers_by_topic,
            generate_quality_report,
            display_export_summary,
            
            # Step 12.4
            save_all_artifacts,
            save_error_logs,
            save_processing_logs,
            update_state_with_paths,
        )
        
        print("\n✅ All Phase 12 functions imported successfully!")
        print("\nImported functions:")
        print("  Step 12.1: export_final_data, create_final_export_config")
        print("  Step 12.2: export_full_csv, export_summary_csv, export_to_json, export_taxonomy_to_json")
        print("  Step 12.3: generate_statistics_report, count_papers_by_status, count_papers_by_topic, generate_quality_report, display_export_summary")
        print("  Step 12.4: save_all_artifacts, save_error_logs, save_processing_logs, update_state_with_paths")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_models():
    """Test that required models are available."""
    print("\n" + "=" * 70)
    print("Testing Data Models")
    print("=" * 70)
    
    try:
        from rag_models import (
            PaperRecord,
            TopicNode,
            TopicHierarchy,
            StateManager,
            create_default_config,
        )
        
        print("\n✅ All data models imported successfully!")
        print("\nImported models:")
        print("  - PaperRecord")
        print("  - TopicNode")
        print("  - TopicHierarchy")
        print("  - StateManager")
        print("  - create_default_config")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ Model import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_basic_functionality():
    """Test basic Phase 12 functionality."""
    print("\n" + "=" * 70)
    print("Testing Basic Functionality")
    print("=" * 70)
    
    try:
        from rag_models import PaperRecord, create_default_config, StateManager
        from export_manager import (
            create_final_export_config,
            count_papers_by_status,
        )
        
        # Test 1: Create export config
        print("\n1. Testing create_final_export_config()...")
        config = create_final_export_config()
        assert config.include_fields is None
        assert len(config.exclude_fields) == 0
        print("   ✅ Export config created successfully")
        
        # Test 2: Count papers by status
        print("\n2. Testing count_papers_by_status()...")
        papers = {
            "p1": PaperRecord(
                id="p1",
                file_path="/test/p1.pdf",
                filename="p1.pdf",
                processing_status="classified"
            ),
            "p2": PaperRecord(
                id="p2",
                file_path="/test/p2.pdf",
                filename="p2.pdf",
                processing_status="summarized"
            ),
            "p3": PaperRecord(
                id="p3",
                file_path="/test/p3.pdf",
                filename="p3.pdf",
                processing_status="failed"
            ),
        }
        
        counts = count_papers_by_status(papers)
        assert counts["classified"] == 1
        assert counts["summarized"] == 1
        assert counts["failed"] == 1
        print(f"   ✅ Status counts: {counts}")
        
        print("\n✅ Basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("\n" + "=" * 70)
    print("PHASE 12 VALIDATION")
    print("=" * 70)
    
    results = []
    
    # Test imports
    results.append(("Imports", test_imports()))
    
    # Test models
    results.append(("Models", test_models()))
    
    # Test basic functionality
    results.append(("Functionality", test_basic_functionality()))
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10} {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n✅ All validation tests passed!")
        print("\nPhase 12 is ready to use.")
        return 0
    else:
        print("\n❌ Some validation tests failed.")
        print("\nPlease check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
