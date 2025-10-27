#!/usr/bin/env python3
"""
Comprehensive test of three-score classification on ORIGIN files
Logs detailed results for analysis and future ACE implementation
"""

import sys
import os
import json
import time
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.pdf_processor import PDFProcessor
from core.extractor import FinancialDataExtractor

def test_origin_file_comprehensive():
    """Test the three-score classification on ORIGIN files with detailed logging"""
    
    print("=" * 80)
    print("COMPREHENSIVE ORIGIN FILE TEST - THREE-SCORE CLASSIFICATION")
    print("=" * 80)
    
    # Initialize components
    extractor = FinancialDataExtractor()
    processor = PDFProcessor(extractor)
    
    # Test file (ORIGIN file - full 30-80 page document)
    test_file = "tests/fixtures/origin/AFS-2022.pdf"
    
    if not os.path.exists(test_file):
        print(f"[ERROR] File not found: {test_file}")
        return
        
    print(f"TESTING: {os.path.basename(test_file)}")
    print(f"FILE PATH: {test_file}")
    print(f"TEST TIME: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Create detailed log structure
    test_log = {
        "test_file": test_file,
        "test_time": datetime.now().isoformat(),
        "test_type": "three_score_classification_origin",
        "results": {}
    }
    
    try:
        # Step 1: PDF Conversion
        print(f"[STEP 1] Converting PDF to images...")
        start_time = time.time()
        
        images, page_info = processor.convert_pdf_to_images(test_file, enable_parallel=True)
        conversion_time = time.time() - start_time
        
        if not images:
            print(f"[ERROR] No images extracted")
            test_log["results"]["error"] = "No images extracted from PDF"
            return
            
        print(f"[SUCCESS] PDF converted to {len(images)} pages in {conversion_time:.2f}s")
        
        test_log["results"]["pdf_conversion"] = {
            "total_pages": len(images),
            "conversion_time_seconds": conversion_time,
            "page_info": page_info
        }
        
        # Step 2: Three-Score Classification
        print(f"[STEP 2] Running three-score classification...")
        start_time = time.time()
        
        financial_pages = processor.classify_pages_with_vision(images)
        classification_time = time.time() - start_time
        
        print(f"[SUCCESS] Classification completed in {classification_time:.2f}s")
        
        # Step 3: Detailed Analysis
        print(f"[STEP 3] Analyzing results...")
        
        # Count by statement type
        bs_pages = [p for p in financial_pages if p['statement_type'] == 'balance_sheet']
        is_pages = [p for p in financial_pages if p['statement_type'] == 'income_statement']
        cf_pages = [p for p in financial_pages if p['statement_type'] == 'cash_flow']
        
        # Calculate confidence statistics
        all_confidences = [p['confidence'] for p in financial_pages]
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        min_confidence = min(all_confidences) if all_confidences else 0
        max_confidence = max(all_confidences) if all_confidences else 0
        
        # Score analysis
        bs_scores = [p['scores']['balance_sheet'] for p in financial_pages]
        is_scores = [p['scores']['income_statement'] for p in financial_pages]
        cf_scores = [p['scores']['cash_flow'] for p in financial_pages]
        
        test_log["results"]["classification"] = {
            "total_financial_pages": len(financial_pages),
            "classification_time_seconds": classification_time,
            "statement_type_breakdown": {
                "balance_sheet_pages": len(bs_pages),
                "income_statement_pages": len(is_pages),
                "cash_flow_pages": len(cf_pages)
            },
            "confidence_statistics": {
                "average_confidence": avg_confidence,
                "min_confidence": min_confidence,
                "max_confidence": max_confidence
            },
            "score_statistics": {
                "balance_sheet_scores": {
                    "min": min(bs_scores) if bs_scores else 0,
                    "max": max(bs_scores) if bs_scores else 0,
                    "avg": sum(bs_scores) / len(bs_scores) if bs_scores else 0
                },
                "income_statement_scores": {
                    "min": min(is_scores) if is_scores else 0,
                    "max": max(is_scores) if is_scores else 0,
                    "avg": sum(is_scores) / len(is_scores) if is_scores else 0
                },
                "cash_flow_scores": {
                    "min": min(cf_scores) if cf_scores else 0,
                    "max": max(cf_scores) if cf_scores else 0,
                    "avg": sum(cf_scores) / len(cf_scores) if cf_scores else 0
                }
            },
            "detailed_pages": []
        }
        
        # Add detailed page information (without PIL image objects)
        for page in financial_pages:
            page_detail = {
                "page_number": page['page_num'] + 1,
                "statement_type": page['statement_type'],
                "confidence": page['confidence'],
                "scores": page['scores']
                # Note: 'image' field excluded to avoid JSON serialization issues
            }
            test_log["results"]["classification"]["detailed_pages"].append(page_detail)
        
        # Step 4: Display Results
        print(f"\n[RESULTS] Classification Results:")
        print(f"  Total pages: {len(images)}")
        print(f"  Financial pages identified: {len(financial_pages)}")
        print(f"  Classification time: {classification_time:.2f}s")
        
        if financial_pages:
            print(f"\n  Statement type breakdown:")
            print(f"    Balance Sheet pages: {len(bs_pages)}")
            print(f"    Income Statement pages: {len(is_pages)}")
            print(f"    Cash Flow pages: {len(cf_pages)}")
            
            print(f"\n  Confidence statistics:")
            print(f"    Average confidence: {avg_confidence:.2f}")
            print(f"    Min confidence: {min_confidence:.2f}")
            print(f"    Max confidence: {max_confidence:.2f}")
            
            print(f"\n  Page details (first 10 pages):")
            for i, page in enumerate(financial_pages[:10]):
                scores = page['scores']
                print(f"    Page {page['page_num'] + 1}: {page['statement_type']} "
                      f"(BS:{scores['balance_sheet']}, IS:{scores['income_statement']}, CF:{scores['cash_flow']}) "
                      f"Confidence: {page['confidence']:.2f}")
            
            if len(financial_pages) > 10:
                print(f"    ... and {len(financial_pages) - 10} more pages")
        else:
            print(f"  [WARNING] No financial pages identified!")
            test_log["results"]["classification"]["warning"] = "No financial pages identified"
        
        # Step 5: Year Extraction Test
        print(f"\n[STEP 4] Testing year extraction from financial pages...")
        start_time = time.time()
        
        year_data = processor._extract_years_from_financial_pages(images, financial_pages)
        year_extraction_time = time.time() - start_time
        
        test_log["results"]["year_extraction"] = {
            "years_found": year_data.get('years', []),
            "confidence": year_data.get('confidence', 0),
            "source": year_data.get('source', 'unknown'),
            "extraction_time_seconds": year_extraction_time
        }
        
        print(f"  Years found: {year_data.get('years', [])}")
        print(f"  Confidence: {year_data.get('confidence', 0)}")
        print(f"  Source: {year_data.get('source', 'unknown')}")
        print(f"  Extraction time: {year_extraction_time:.2f}s")
        
        # Step 6: Save detailed log
        log_filename = f"test_log_origin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_filename, 'w') as f:
            json.dump(test_log, f, indent=2)
        
        print(f"\n[SUCCESS] Detailed test log saved to: {log_filename}")
        
        # Step 7: Summary for ACE Analysis
        print(f"\n[ACE ANALYSIS SUMMARY]")
        print(f"  Classification Success: {'✅ YES' if financial_pages else '❌ NO'}")
        print(f"  Statement Types Identified: {len(set(p['statement_type'] for p in financial_pages))}")
        print(f"  Average Confidence: {avg_confidence:.2f}")
        print(f"  Years Extracted: {len(year_data.get('years', []))}")
        print(f"  Ready for Phase 1.2 (Reflector): {'✅ YES' if financial_pages else '❌ NO'}")
        
        test_log["results"]["ace_analysis"] = {
            "classification_success": bool(financial_pages),
            "statement_types_identified": len(set(p['statement_type'] for p in financial_pages)),
            "average_confidence": avg_confidence,
            "years_extracted": len(year_data.get('years', [])),
            "ready_for_phase_1_2": bool(financial_pages)
        }
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        
        test_log["results"]["error"] = {
            "message": str(e),
            "traceback": traceback.format_exc()
        }
    
    finally:
        # Save final log even if there was an error
        log_filename = f"test_log_origin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_filename, 'w') as f:
            json.dump(test_log, f, indent=2)
        
        print(f"\n[FINAL] Test log saved to: {log_filename}")
    
    print(f"\n{'='*80}")
    print("COMPREHENSIVE ORIGIN FILE TEST COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    test_origin_file_comprehensive()
