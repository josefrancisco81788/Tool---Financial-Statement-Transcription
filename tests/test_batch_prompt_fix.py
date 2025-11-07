#!/usr/bin/env python3
"""
Test batch prompt fix - verify template fields are included
No tokens needed - just verify prompt structure
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.batch_processor import DocumentStructureAnalyzer
from core.extractor import FinancialDataExtractor


def test_batch_prompt_includes_template_fields():
    """Test that batch prompt now includes template fields"""
    print("=" * 70)
    print("TEST: Batch Prompt Includes Template Fields")
    print("=" * 70)
    
    # Load template fields
    extractor = FinancialDataExtractor()
    template_fields = extractor._load_template_fields()
    
    print(f"\n[TEST] Loaded {len(template_fields)} template fields")
    print(f"[TEST] Sample fields: {template_fields[:5]}")
    
    # Create analyzer
    analyzer = DocumentStructureAnalyzer()
    
    # Test each statement type
    statement_types = ['balance_sheet', 'income_statement', 'cash_flow', 'other']
    
    for statement_type in statement_types:
        print(f"\n{'='*70}")
        print(f"[TEST] Testing {statement_type} prompt")
        print(f"{'='*70}")
        
        prompt = analyzer.get_context_prompt(statement_type, template_fields)
        
        # Check for key elements
        checks = {
            'Template fields included': 'AVAILABLE TEMPLATE FIELDS' in prompt,
            'Exact template names instruction': 'Use EXACT template field names' in prompt,
            'Case-sensitive instruction': 'case-sensitive' in prompt,
            'Template field list': any(field in prompt for field in template_fields[:10]),
            'Return format specified': 'template_mappings' in prompt,
        }
        
        print(f"\n[TEST] Prompt checks:")
        all_passed = True
        for check_name, passed in checks.items():
            status = "[OK]" if passed else "[FAIL]"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False
        
        if not all_passed:
            print(f"\n[TEST] Prompt preview (first 500 chars):")
            print(prompt[:500])
        
        assert all_passed, f"Prompt for {statement_type} missing required elements"
    
    print(f"\n{'='*70}")
    print("[TEST] All prompt checks passed!")
    print(f"{'='*70}")


def test_normalizer_removed():
    """Test that normalizer is no longer used in batch processing"""
    print("\n" + "=" * 70)
    print("TEST: Normalizer Removed from Batch Processing")
    print("=" * 70)
    
    # Read pdf_processor.py to check for normalizer usage
    pdf_processor_path = project_root / "core" / "pdf_processor.py"
    
    with open(pdf_processor_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that normalizer is not initialized
    normalizer_init = "field_normalizer = FieldNameNormalizer()" in content
    normalize_call = "field_normalizer.normalize(" in content
    
    print(f"\n[TEST] Checking for normalizer usage:")
    print(f"  Normalizer initialization: {'FOUND' if normalizer_init else 'NOT FOUND'} [{'OK' if not normalizer_init else 'FAIL'}]")
    print(f"  Normalizer call: {'FOUND' if normalize_call else 'NOT FOUND'} [{'OK' if not normalize_call else 'FAIL'}]")
    
    # Check that template fields are loaded
    template_fields_load = "template_fields = self.extractor._load_template_fields()" in content
    print(f"  Template fields loaded: {'FOUND' if template_fields_load else 'NOT FOUND'} [{'OK' if template_fields_load else 'FAIL'}]")
    
    # Check that template fields passed to create_processing_batches
    template_fields_passed = "create_processing_batches(statement_groups, template_fields=" in content
    print(f"  Template fields passed to batches: {'FOUND' if template_fields_passed else 'NOT FOUND'} [{'OK' if template_fields_passed else 'FAIL'}]")
    
    assert not normalizer_init, "Normalizer should not be initialized"
    assert not normalize_call, "Normalizer should not be called"
    assert template_fields_load, "Template fields should be loaded"
    assert template_fields_passed, "Template fields should be passed to batch creation"
    
    print(f"\n{'='*70}")
    print("[TEST] Normalizer removal verified!")
    print(f"{'='*70}")


def main():
    """Run all tests"""
    try:
        test_batch_prompt_includes_template_fields()
        test_normalizer_removed()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\nSummary:")
        print("  ✅ Batch prompt now includes template fields")
        print("  ✅ Batch prompt includes 'Use EXACT template field names' instruction")
        print("  ✅ Normalizer removed from batch processing")
        print("  ✅ Template fields loaded and passed to batch creation")
        print("\nNext: Test with actual extraction (requires tokens)")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()






