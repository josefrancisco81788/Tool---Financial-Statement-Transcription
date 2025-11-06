"""
Test script for Phase 1: Year Field Extraction

This script tests the new year extraction functionality independently
to validate that it achieves 90%+ accuracy before proceeding to Phase 2.
"""

import sys
import os
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import FinancialDataExtractor, PDFProcessor


def test_year_extraction_only():
    """Test year extraction method independently on all test files"""
    print("=" * 80)
    print("PHASE 1 TEST: Year Field Extraction")
    print("=" * 80)
    print()
    
    # Test files
    test_files = [
        {
            'name': 'AFS2024',
            'path': 'tests/fixtures/light/AFS2024 - statement extracted.pdf',
            'expected_years': [2024, 2023],
            'description': 'Wireless Services Asia Inc. - 2024/2023'
        },
        {
            'name': 'AFS-2022',
            'path': 'tests/fixtures/light/AFS-2022 - statement extracted.pdf',
            'expected_years': [2022, 2021],
            'description': 'Ideal Marketing - 2022/2021'
        },
        {
            'name': '2021 AFS with SEC Stamp',
            'path': 'tests/fixtures/light/2021 AFS with SEC Stamp - statement extracted.pdf',
            'expected_years': [2021, 2020],
            'description': 'Metechs Industrial - 2021/2020'
        },
        {
            'name': 'afs-2021-2023',
            'path': 'tests/fixtures/light/afs-2021-2023 - statement extracted.pdf',
            'expected_years': [2022, 2021, 2020],  # Multi-year document
            'description': 'GBS Concept Advertising - Multi-year'
        }
    ]
    
    # Test with both providers
    # Note: Claude (Anthropic) is the default provider, but this test explicitly compares both
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
            print(f"   Expected years: {test_file['expected_years']}")
            
            try:
                start_time = time.time()
                
                # Create fresh extractor and processor
                extractor = FinancialDataExtractor()
                pdf_processor = PDFProcessor(extractor)
                
                # Convert PDF to images
                with open(test_file['path'], 'rb') as f:
                    pdf_bytes = f.read()
                
                images, page_info = pdf_processor.convert_pdf_to_images(pdf_bytes, enable_parallel=False)
                
                if not images or len(images) == 0:
                    print(f"   [FAIL] Failed to convert PDF to images")
                    provider_results.append({
                        'file': test_file['name'],
                        'success': False,
                        'error': 'PDF conversion failed'
                    })
                    continue
                
                # Test year extraction on first page
                first_page_image = extractor.encode_image(images[0])
                year_data = extractor.extract_years_from_image(first_page_image)
                
                elapsed_time = time.time() - start_time
                
                # Evaluate results
                extracted_years = year_data.get('years', [])
                confidence = year_data.get('confidence', 0.0)
                expected_years = test_file['expected_years']
                
                # Check if extraction was successful
                if len(extracted_years) >= 2:
                    # Check if extracted years match expected (allowing for some flexibility)
                    matches = sum(1 for year in expected_years if year in extracted_years)
                    accuracy = matches / len(expected_years) if expected_years else 0
                    
                    if accuracy >= 0.8:  # At least 80% of expected years found
                        print(f"   [PASS] SUCCESS: Extracted {extracted_years}")
                        print(f"   Confidence: {confidence:.2f}")
                        print(f"   Accuracy: {accuracy*100:.1f}% ({matches}/{len(expected_years)} years correct)")
                        print(f"   Time: {elapsed_time:.2f}s")
                        
                        provider_results.append({
                            'file': test_file['name'],
                            'success': True,
                            'extracted_years': extracted_years,
                            'expected_years': expected_years,
                            'confidence': confidence,
                            'accuracy': accuracy,
                            'time': elapsed_time
                        })
                    else:
                        print(f"   [WARN] PARTIAL: Extracted {extracted_years}")
                        print(f"   Expected: {expected_years}")
                        print(f"   Confidence: {confidence:.2f}")
                        print(f"   Accuracy: {accuracy*100:.1f}% ({matches}/{len(expected_years)} years correct)")
                        print(f"   Time: {elapsed_time:.2f}s")
                        
                        provider_results.append({
                            'file': test_file['name'],
                            'success': False,
                            'extracted_years': extracted_years,
                            'expected_years': expected_years,
                            'confidence': confidence,
                            'accuracy': accuracy,
                            'time': elapsed_time,
                            'error': 'Partial match'
                        })
                else:
                    print(f"   [FAIL] FAILED: Extracted {extracted_years}")
                    print(f"   Expected: {expected_years}")
                    print(f"   Confidence: {confidence:.2f}")
                    print(f"   Time: {elapsed_time:.2f}s")
                    
                    provider_results.append({
                        'file': test_file['name'],
                        'success': False,
                        'extracted_years': extracted_years,
                        'expected_years': expected_years,
                        'confidence': confidence,
                        'accuracy': 0.0,
                        'time': elapsed_time,
                        'error': 'Insufficient years extracted'
                    })
                
            except Exception as e:
                print(f"   [ERROR] ERROR: {str(e)}")
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
    print("PHASE 1 TEST SUMMARY: Year Field Extraction")
    print(f"{'=' * 80}\n")
    
    for provider_result in overall_results:
        provider = provider_result['provider']
        results = provider_result['results']
        
        success_count = sum(1 for r in results if r.get('success', False))
        total_count = len(results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        avg_accuracy = sum(r.get('accuracy', 0) for r in results if 'accuracy' in r) / len(results) if results else 0
        avg_confidence = sum(r.get('confidence', 0) for r in results if 'confidence' in r) / len(results) if results else 0
        avg_time = sum(r.get('time', 0) for r in results if 'time' in r) / len(results) if results else 0
        
        print(f"Provider: {provider.upper()}")
        print(f"  Success Rate: {success_rate:.1f}% ({success_count}/{total_count} files)")
        print(f"  Average Accuracy: {avg_accuracy*100:.1f}%")
        print(f"  Average Confidence: {avg_confidence:.2f}")
        print(f"  Average Time: {avg_time:.2f}s")
        print()
    
    # Overall assessment
    print(f"{'=' * 80}")
    print("PHASE 1 ASSESSMENT")
    print(f"{'=' * 80}\n")
    
    total_successes = sum(
        sum(1 for r in pr['results'] if r.get('success', False))
        for pr in overall_results
    )
    total_tests = sum(len(pr['results']) for pr in overall_results)
    overall_success_rate = (total_successes / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Overall Success Rate: {overall_success_rate:.1f}% ({total_successes}/{total_tests} tests passed)")
    print()
    
    if overall_success_rate >= 90:
        print("[PASS] PHASE 1 SUCCESS: Year extraction achieves 90%+ accuracy")
        print("   Ready to proceed to Phase 2")
        return True
    elif overall_success_rate >= 75:
        print("[WARN] PHASE 1 PARTIAL: Year extraction achieves 75-90% accuracy")
        print("   Consider improvements before proceeding to Phase 2")
        return False
    else:
        print("[FAIL] PHASE 1 FAILED: Year extraction below 75% accuracy")
        print("   Must fix before proceeding to Phase 2")
        return False


if __name__ == "__main__":
    success = test_year_extraction_only()
    sys.exit(0 if success else 1)

