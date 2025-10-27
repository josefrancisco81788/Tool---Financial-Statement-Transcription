"""
Test script for Phase 2: Multi-Year Data Handling Improvements

This script tests the enhanced multi-year extraction (3-4 years) to validate
improvements on the afs-2021-2023 document and ensure no regression on 2-year documents.
"""

import sys
import os
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import FinancialDataExtractor, PDFProcessor


def test_multi_year_extraction():
    """Test multi-year extraction improvements"""
    print("=" * 80)
    print("PHASE 2 TEST: Multi-Year Data Handling")
    print("=" * 80)
    print()
    
    # Test files - focus on multi-year document and verify no regression
    test_files = [
        {
            'name': 'afs-2021-2023 (FOCUS)',
            'path': 'tests/fixtures/light/afs-2021-2023 - statement extracted.pdf',
            'expected_years': 3,  # Should extract 3 years
            'description': 'Multi-year document - PRIMARY TARGET',
            'baseline_extraction': 11.8,  # Current extraction rate
            'target_extraction': 40.0  # Target improvement
        },
        {
            'name': 'AFS2024 (regression check)',
            'path': 'tests/fixtures/light/AFS2024 - statement extracted.pdf',
            'expected_years': 2,
            'description': '2-year document - ensure no regression',
            'baseline_extraction': 65.6,
            'target_extraction': 65.0  # Should maintain
        },
        {
            'name': 'AFS-2022 (regression check)',
            'path': 'tests/fixtures/light/AFS-2022 - statement extracted.pdf',
            'expected_years': 2,
            'description': '2-year document - ensure no regression',
            'baseline_extraction': 36.0,
            'target_extraction': 36.0  # Should maintain
        }
    ]
    
    # Test with both providers
    providers = ['openai', 'anthropic']
    
    overall_results = []
    
    for provider in providers:
        print(f"\n{'=' * 80}")
        print(f"Testing with provider: {provider.upper()}")
        print(f"{'=' * 80}\n")
        
        # Set provider
        os.environ['AI_PROVIDER'] = provider
        
        provider_results = []
        
        for test_file in test_files:
            print(f"\n[FILE] Testing: {test_file['name']}")
            print(f"   Description: {test_file['description']}")
            print(f"   Baseline extraction: {test_file['baseline_extraction']}%")
            print(f"   Target: {test_file['target_extraction']}%")
            
            try:
                start_time = time.time()
                
                # Create fresh processor
                extractor = FinancialDataExtractor()
                pdf_processor = PDFProcessor(extractor)
                
                # Process PDF through full pipeline
                with open(test_file['path'], 'rb') as f:
                    result = pdf_processor.process_pdf_with_vector_db(f.read(), enable_parallel=False)
                
                elapsed_time = time.time() - start_time
                
                if not result:
                    print(f"   [FAIL] No result returned")
                    provider_results.append({
                        'file': test_file['name'],
                        'success': False,
                        'error': 'No result'
                    })
                    continue
                
                # Analyze results
                template_mappings = result.get('template_mappings', {})
                total_fields = len(template_mappings)
                
                # Check Year field
                year_field = template_mappings.get('Year', {})
                years_extracted = [
                    year_field.get('Value_Year_1'),
                    year_field.get('Value_Year_2'),
                    year_field.get('Value_Year_3'),
                    year_field.get('Value_Year_4')
                ]
                years_extracted = [y for y in years_extracted if y is not None]
                year_count = len(years_extracted)
                
                # Count fields with multi-year data
                multi_year_fields = 0
                for field_name, field_data in template_mappings.items():
                    if field_name == 'Year':
                        continue
                    if field_data.get('Value_Year_2') is not None:
                        multi_year_fields += 1
                
                print(f"\n   [INFO] Results:")
                print(f"   Total fields extracted: {total_fields}")
                print(f"   Years extracted: {years_extracted} ({year_count} years)")
                print(f"   Fields with multi-year data: {multi_year_fields}/{total_fields - 1}")
                print(f"   Processing time: {elapsed_time:.2f}s")
                
                # Calculate improvement
                # Note: We don't have a fixed "expected" count, so we measure relative improvement
                if test_file['name'].startswith('afs-2021-2023'):
                    # For the multi-year document, success means:
                    # 1. Extracted 3 years (not just 2)
                    # 2. More than baseline (11.8% baseline = ~2 fields, target = ~7 fields)
                    year_success = year_count >= test_file['expected_years']
                    field_success = total_fields >= 7  # Target ~40% of 17 expected fields
                    
                    if year_success and field_success:
                        print(f"   [PASS] Multi-year extraction IMPROVED!")
                        status = True
                    elif year_success or field_success:
                        print(f"   [WARN] Partial improvement")
                        status = False
                    else:
                        print(f"   [FAIL] No significant improvement")
                        status = False
                else:
                    # For 2-year documents, success means maintaining baseline
                    year_success = year_count >= test_file['expected_years']
                    # Allow 10% degradation tolerance
                    field_threshold = test_file['baseline_extraction'] * 0.9 / 100 * 32  # Rough estimate
                    field_success = total_fields >= field_threshold
                    
                    if year_success and field_success:
                        print(f"   [PASS] No regression - baseline maintained")
                        status = True
                    else:
                        print(f"   [WARN] Possible regression")
                        status = False
                
                provider_results.append({
                    'file': test_file['name'],
                    'success': status,
                    'total_fields': total_fields,
                    'year_count': year_count,
                    'multi_year_fields': multi_year_fields,
                    'years_extracted': years_extracted,
                    'time': elapsed_time
                })
                
            except Exception as e:
                print(f"   [ERROR] {str(e)}")
                provider_results.append({
                    'file': test_file['name'],
                    'success': False,
                    'error': str(e)
                })
        
        overall_results.append({
            'provider': provider,
            'results': provider_results
        })
    
    # Print summary
    print(f"\n{'=' * 80}")
    print("PHASE 2 TEST SUMMARY: Multi-Year Data Handling")
    print(f"{'=' * 80}\n")
    
    for provider_result in overall_results:
        provider = provider_result['provider']
        results = provider_result['results']
        
        success_count = sum(1 for r in results if r.get('success', False))
        total_count = len(results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        print(f"Provider: {provider.upper()}")
        print(f"  Success Rate: {success_rate:.1f}% ({success_count}/{total_count} files)")
        
        # Focus on multi-year document
        multi_year_result = next((r for r in results if 'afs-2021-2023' in r.get('file', '')), None)
        if multi_year_result and 'total_fields' in multi_year_result:
            print(f"  Multi-year doc fields: {multi_year_result['total_fields']}")
            print(f"  Multi-year doc years: {multi_year_result.get('year_count', 0)}")
        print()
    
    # Overall assessment
    print(f"{'=' * 80}")
    print("PHASE 2 ASSESSMENT")
    print(f"{'=' * 80}\n")
    
    # Check multi-year document improvement
    all_multi_year_success = all(
        any(r.get('success', False) for r in pr['results'] if 'afs-2021-2023' in r.get('file', ''))
        for pr in overall_results
    )
    
    # Check no regression on 2-year documents
    all_regression_ok = all(
        all(r.get('success', False) for r in pr['results'] if 'afs-2021-2023' not in r.get('file', ''))
        for pr in overall_results if any(r for r in pr['results'] if 'afs-2021-2023' not in r.get('file', ''))
    )
    
    if all_multi_year_success and all_regression_ok:
        print("[PASS] PHASE 2 SUCCESS: Multi-year extraction improved, no regression")
        print("   Ready to proceed to Phase 3")
        return True
    elif all_multi_year_success:
        print("[WARN] PHASE 2 PARTIAL: Multi-year improved but possible regression")
        print("   Review 2-year document results before proceeding")
        return False
    else:
        print("[FAIL] PHASE 2 NEEDS WORK: Multi-year extraction not sufficiently improved")
        print("   Consider additional prompt enhancements")
        return False


if __name__ == "__main__":
    success = test_multi_year_extraction()
    sys.exit(0 if success else 1)








