#!/usr/bin/env python3
"""
Regression test to compare three-score vs four-score system performance
Ensures the four-score system doesn't break existing functionality
"""

import sys
import os
import time
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.pdf_processor import PDFProcessor
from core.extractor import FinancialDataExtractor

def test_four_score_regression():
    """Test four-score system against known good LIGHT files"""
    
    print("=" * 80)
    print("FOUR-SCORE SYSTEM REGRESSION TEST")
    print("=" * 80)
    
    # Initialize components
    extractor = FinancialDataExtractor()
    processor = PDFProcessor(extractor)
    
    # Test files (LIGHT files - known good data)
    test_files = [
        "tests/fixtures/light/AFS2024 - statement extracted.pdf",
        "tests/fixtures/light/AFS-2022 - statement extracted.pdf",
        "tests/fixtures/light/afs-2021-2023 - statement extracted.pdf"
    ]
    
    results = {
        "test_time": datetime.now().isoformat(),
        "test_type": "four_score_regression",
        "files": {}
    }
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"[SKIP] File not found: {test_file}")
            continue
            
        print(f"\n{'='*60}")
        print(f"TESTING: {os.path.basename(test_file)}")
        print(f"{'='*60}")
        
        file_results = {
            "file_path": test_file,
            "classification": {},
            "extraction": {},
            "performance": {}
        }
        
        try:
            # Step 1: PDF Conversion
            start_time = time.time()
            images, page_info = processor.convert_pdf_to_images(test_file, enable_parallel=True)
            conversion_time = time.time() - start_time
            
            if not images:
                print(f"[ERROR] No images extracted from {test_file}")
                continue
                
            print(f"[INFO] PDF converted to {len(images)} pages in {conversion_time:.2f}s")
            
            # Step 2: Four-Score Classification
            start_time = time.time()
            financial_pages = processor.classify_pages_with_vision(images)
            classification_time = time.time() - start_time
            
            # Step 3: Extract data from identified pages
            start_time = time.time()
            extraction_results = []
            total_template_fields = 0
            
            for page in financial_pages:
                try:
                    base64_image = processor.extractor.encode_image(page['image'])
                    statement_type = page['statement_type']
                    
                    extracted_data = processor.extractor.extract_comprehensive_financial_data(
                        base64_image, 
                        statement_type, 
                        ""
                    )
                    
                    if extracted_data and 'error' not in extracted_data:
                        template_mappings = extracted_data.get('template_mappings', {})
                        total_template_fields += len(template_mappings)
                        
                        extraction_results.append({
                            'page_num': page['page_num'],
                            'statement_type': statement_type,
                            'template_fields_count': len(template_mappings),
                            'confidence': page['confidence']
                        })
                        
                except Exception as e:
                    print(f"[WARN] Extraction failed for page {page['page_num'] + 1}: {e}")
                    continue
            
            extraction_time = time.time() - start_time
            
            # Step 4: Analyze Results
            statement_breakdown = {
                'balance_sheet': len([p for p in financial_pages if p['statement_type'] == 'balance_sheet']),
                'income_statement': len([p for p in financial_pages if p['statement_type'] == 'income_statement']),
                'cash_flow': len([p for p in financial_pages if p['statement_type'] == 'cash_flow']),
                'equity_statement': len([p for p in financial_pages if p['statement_type'] == 'equity_statement'])
            }
            
            avg_confidence = sum(p['confidence'] for p in financial_pages) / len(financial_pages) if financial_pages else 0
            
            # Store results
            file_results["classification"] = {
                "total_pages": len(images),
                "financial_pages_identified": len(financial_pages),
                "statement_breakdown": statement_breakdown,
                "average_confidence": avg_confidence,
                "classification_time_seconds": classification_time
            }
            
            file_results["extraction"] = {
                "pages_processed": len(extraction_results),
                "total_template_fields": total_template_fields,
                "extraction_time_seconds": extraction_time,
                "page_details": extraction_results
            }
            
            file_results["performance"] = {
                "total_time_seconds": conversion_time + classification_time + extraction_time,
                "conversion_time_seconds": conversion_time,
                "classification_time_seconds": classification_time,
                "extraction_time_seconds": extraction_time
            }
            
            # Display results
            print(f"\n[RESULTS] Four-Score System Performance:")
            print(f"  Total pages: {len(images)}")
            print(f"  Financial pages identified: {len(financial_pages)}")
            print(f"  Statement breakdown: {statement_breakdown}")
            print(f"  Average confidence: {avg_confidence:.2f}")
            print(f"  Template fields extracted: {total_template_fields}")
            print(f"  Total processing time: {conversion_time + classification_time + extraction_time:.2f}s")
            
            # Check for equity statements
            if statement_breakdown['equity_statement'] > 0:
                print(f"  ✅ Equity statements detected: {statement_breakdown['equity_statement']} pages")
            else:
                print(f"  ℹ️  No equity statements in this file")
                
        except Exception as e:
            print(f"[ERROR] Test failed for {test_file}: {e}")
            import traceback
            traceback.print_exc()
            file_results["error"] = str(e)
            continue
        
        results["files"][os.path.basename(test_file)] = file_results
    
    # Save results
    results_file = f"four_score_regression_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*80}")
    print("REGRESSION TEST COMPLETE")
    print(f"Results saved to: {results_file}")
    print(f"{'='*80}")
    
    # Summary
    total_files = len([f for f in test_files if os.path.exists(f)])
    successful_files = len([f for f in results["files"].values() if "error" not in f])
    
    print(f"\n[SUMMARY]")
    print(f"  Files tested: {total_files}")
    print(f"  Successful: {successful_files}")
    print(f"  Failed: {total_files - successful_files}")
    
    if successful_files > 0:
        # Calculate averages
        all_financial_pages = sum(f["classification"]["financial_pages_identified"] for f in results["files"].values() if "error" not in f)
        all_template_fields = sum(f["extraction"]["total_template_fields"] for f in results["files"].values() if "error" not in f)
        all_equity_pages = sum(f["classification"]["statement_breakdown"]["equity_statement"] for f in results["files"].values() if "error" not in f)
        
        print(f"  Total financial pages identified: {all_financial_pages}")
        print(f"  Total template fields extracted: {all_template_fields}")
        print(f"  Total equity statement pages: {all_equity_pages}")
        print(f"  Average template fields per page: {all_template_fields / all_financial_pages if all_financial_pages > 0 else 0:.1f}")

if __name__ == "__main__":
    test_four_score_regression()


