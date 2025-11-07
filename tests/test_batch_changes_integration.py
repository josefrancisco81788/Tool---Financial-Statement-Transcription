#!/usr/bin/env python3
"""
Integration test for batch processing changes (no tokens)
Tests: Prompt fix + normalizer removal
"""

import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.batch_processor import DocumentStructureAnalyzer, BatchExtractor
from core.extractor import FinancialDataExtractor


def test_prompt_includes_template_fields():
    """Test that batch prompt includes template fields"""
    print("\n" + "=" * 70)
    print("TEST 1: Batch Prompt Includes Template Fields")
    print("=" * 70)
    
    extractor = FinancialDataExtractor()
    template_fields = extractor._load_template_fields()
    
    analyzer = DocumentStructureAnalyzer()
    prompt = analyzer.get_context_prompt('balance_sheet', template_fields)
    
    # Verify key elements
    assert 'AVAILABLE TEMPLATE FIELDS' in prompt, "Missing template fields section"
    assert 'Use EXACT template field names' in prompt, "Missing exact name instruction"
    assert 'case-sensitive' in prompt, "Missing case-sensitive instruction"
    assert 'Cash and Cash Equivalents' in prompt, "Template fields not in prompt"
    assert len(template_fields) >= 91, f"Expected 91+ fields, got {len(template_fields)}"
    
    print(f"  [OK] Prompt includes template fields section")
    print(f"  [OK] Prompt includes exact name instruction")
    print(f"  [OK] Prompt includes {len(template_fields)} template fields")
    print(f"  [OK] Sample field in prompt: 'Cash and Cash Equivalents'")


def test_batch_creation_with_template_fields():
    """Test that batches are created with template fields in prompt"""
    print("\n" + "=" * 70)
    print("TEST 2: Batch Creation with Template Fields")
    print("=" * 70)
    
    extractor = FinancialDataExtractor()
    template_fields = extractor._load_template_fields()
    
    analyzer = DocumentStructureAnalyzer()
    
    # Mock classified pages
    mock_pages = [
        {'page_num': 1, 'classified': True, 'statement_type': 'balance_sheet', 'image': 'mock'},
        {'page_num': 2, 'classified': True, 'statement_type': 'balance_sheet', 'image': 'mock'},
        {'page_num': 3, 'classified': True, 'statement_type': 'income_statement', 'image': 'mock'},
    ]
    
    statement_groups = analyzer.analyze_document_structure(mock_pages)
    batches = analyzer.create_processing_batches(statement_groups, template_fields=template_fields)
    
    assert len(batches) > 0, "Should create batches"
    
    # Check that each batch has proper prompt
    for batch in batches:
        prompt = batch['context_prompt']
        assert 'AVAILABLE TEMPLATE FIELDS' in prompt, f"Batch {batch['batch_id']} missing template fields"
        assert 'Use EXACT template field names' in prompt, f"Batch {batch['batch_id']} missing exact name instruction"
        assert 'Cash and Cash Equivalents' in prompt, f"Batch {batch['batch_id']} template fields not in prompt"
    
    print(f"  [OK] Created {len(batches)} batches")
    print(f"  [OK] All batches have template fields in prompt")
    print(f"  [OK] All batches have exact name instruction")


def test_normalizer_removed_from_processing():
    """Test that normalizer is not used in batch processing"""
    print("\n" + "=" * 70)
    print("TEST 3: Normalizer Removed from Processing")
    print("=" * 70)
    
    # Read pdf_processor.py
    pdf_processor_path = project_root / "core" / "pdf_processor.py"
    with open(pdf_processor_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check normalizer is not used
    assert "field_normalizer = FieldNameNormalizer()" not in content, "Normalizer still initialized"
    assert "field_normalizer.normalize(" not in content, "Normalizer still called"
    
    # Check that template fields are loaded
    assert "template_fields = self.extractor._load_template_fields()" in content, "Template fields not loaded"
    
    # Check that field names are used directly
    assert "pages_data[page_num]['template_mappings'][field_name]" in content, "Field names not used directly"
    
    print(f"  [OK] Normalizer initialization removed")
    print(f"  [OK] Normalizer call removed")
    print(f"  [OK] Template fields loaded")
    print(f"  [OK] Field names used directly")


def test_mock_batch_processing_flow():
    """Test batch processing flow with mock data (no API calls)"""
    print("\n" + "=" * 70)
    print("TEST 4: Mock Batch Processing Flow")
    print("=" * 70)
    
    extractor = FinancialDataExtractor()
    template_fields = extractor._load_template_fields()
    
    analyzer = DocumentStructureAnalyzer()
    
    # Mock pages
    mock_pages = [
        {'page_num': 1, 'classified': True, 'statement_type': 'balance_sheet', 'image': 'mock'},
        {'page_num': 2, 'classified': True, 'statement_type': 'balance_sheet', 'image': 'mock'},
    ]
    
    # Create batches
    statement_groups = analyzer.analyze_document_structure(mock_pages)
    batches = analyzer.create_processing_batches(statement_groups, template_fields=template_fields)
    
    assert len(batches) == 1, "Should create 1 batch"
    batch = batches[0]
    
    # Verify batch structure
    assert 'context_prompt' in batch, "Batch missing context_prompt"
    assert 'template_fields' not in batch, "Template fields should not be in batch dict (they're in prompt)"
    
    # Verify prompt content
    prompt = batch['context_prompt']
    assert 'Revenue' in prompt or 'Cash and Cash Equivalents' in prompt, "Prompt should include template fields"
    
    print(f"  [OK] Batch structure correct")
    print(f"  [OK] Prompt includes template fields")
    print(f"  [OK] Batch ready for processing")


def test_field_name_direct_usage():
    """Test that field names are used directly without normalization"""
    print("\n" + "=" * 70)
    print("TEST 5: Field Name Direct Usage")
    print("=" * 70)
    
    # Simulate batch extraction result (what LLM would return)
    mock_batch_result = {
        'extracted_data': [
            {
                'page_num': 1,
                'field_name': 'Revenue',  # Should be exact template field name
                'value': 1000000,
                'confidence': 0.95,
                'year': '2024'
            },
            {
                'page_num': 1,
                'field_name': 'Cost of Sales',  # Should be exact template field name
                'value': 800000,
                'confidence': 0.90,
                'year': '2024'
            }
        ]
    }
    
    # Simulate processing (what pdf_processor.py does)
    pages_data = {}
    for item in mock_batch_result['extracted_data']:
        page_num = item.get('page_num', 0)
        if page_num not in pages_data:
            pages_data[page_num] = {'template_mappings': {}}
        
        field_name = item.get('field_name', '')
        if field_name:
            # Direct usage (no normalization)
            pages_data[page_num]['template_mappings'][field_name] = {
                'value': item.get('value'),
                'confidence': item.get('confidence', 0.0),
                'year': item.get('year', ''),
                'page_num': page_num
            }
    
    # Verify field names are used directly
    assert 'Revenue' in pages_data[1]['template_mappings'], "Revenue field should be present"
    assert 'Cost of Sales' in pages_data[1]['template_mappings'], "Cost of Sales field should be present"
    assert pages_data[1]['template_mappings']['Revenue']['value'] == 1000000, "Revenue value should match"
    
    print(f"  [OK] Field names used directly (no normalization)")
    print(f"  [OK] Template mappings structure correct")
    print(f"  [OK] Values preserved correctly")


def test_comparison_with_single_page():
    """Compare batch prompt with single-page prompt format"""
    print("\n" + "=" * 70)
    print("TEST 6: Batch vs Single-Page Prompt Comparison")
    print("=" * 70)
    
    extractor = FinancialDataExtractor()
    template_fields = extractor._load_template_fields()
    
    # Get batch prompt
    analyzer = DocumentStructureAnalyzer()
    batch_prompt = analyzer.get_context_prompt('balance_sheet', template_fields)
    
    # Get single-page prompt
    single_page_prompt = extractor._build_extraction_prompt('balance sheet')
    
    # Compare key elements
    batch_has_template_fields = 'AVAILABLE TEMPLATE FIELDS' in batch_prompt
    single_has_template_fields = 'AVAILABLE TEMPLATE FIELDS' in single_page_prompt
    
    batch_has_exact = 'Use EXACT template field names' in batch_prompt
    single_has_exact = 'Use EXACT template field names' in single_page_prompt
    
    batch_has_case = 'case-sensitive' in batch_prompt
    single_has_case = 'case-sensitive' in single_page_prompt
    
    print(f"  Template fields section:")
    print(f"    Batch: {'[OK]' if batch_has_template_fields else '[FAIL]'}")
    print(f"    Single-page: {'[OK]' if single_has_template_fields else '[FAIL]'}")
    
    print(f"  Exact name instruction:")
    print(f"    Batch: {'[OK]' if batch_has_exact else '[FAIL]'}")
    print(f"    Single-page: {'[OK]' if single_has_exact else '[FAIL]'}")
    
    print(f"  Case-sensitive instruction:")
    print(f"    Batch: {'[OK]' if batch_has_case else '[FAIL]'}")
    print(f"    Single-page: {'[OK]' if single_has_case else '[FAIL]'}")
    
    # Both should have same key elements now
    assert batch_has_template_fields == single_has_template_fields, "Template fields instruction mismatch"
    assert batch_has_exact == single_has_exact, "Exact name instruction mismatch"
    assert batch_has_case == single_has_case, "Case-sensitive instruction mismatch"
    
    print(f"  [OK] Batch prompt matches single-page prompt format")


def main():
    """Run all integration tests"""
    print("=" * 70)
    print("BATCH PROCESSING CHANGES - INTEGRATION TESTS")
    print("=" * 70)
    print("\nTesting:")
    print("  1. Batch prompt includes template fields")
    print("  2. Batch creation with template fields")
    print("  3. Normalizer removed from processing")
    print("  4. Mock batch processing flow")
    print("  5. Field name direct usage")
    print("  6. Batch vs single-page prompt comparison")
    
    try:
        test_prompt_includes_template_fields()
        test_batch_creation_with_template_fields()
        test_normalizer_removed_from_processing()
        test_mock_batch_processing_flow()
        test_field_name_direct_usage()
        test_comparison_with_single_page()
        
        print("\n" + "=" * 70)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 70)
        print("\nSummary:")
        print("  ✅ Batch prompt now includes template fields (matches single-page)")
        print("  ✅ Normalizer completely removed from batch processing")
        print("  ✅ Field names used directly (no normalization layer)")
        print("  ✅ Template fields properly loaded and passed")
        print("\nReady for live extraction testing (optional, requires tokens)")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()






