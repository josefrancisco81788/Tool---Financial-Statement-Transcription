#!/usr/bin/env python3
"""
Test script for four-score vision-based classification system
Tests the new classify_pages_with_vision() method with equity statement detection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.pdf_processor import PDFProcessor
from core.extractor import FinancialDataExtractor

def test_four_score_classification():
    """Test the four-score classification on LIGHT files to validate equity statement detection"""
    
    print("=" * 80)
    print("TESTING FOUR-SCORE VISION CLASSIFICATION")
    print("=" * 80)
    
    # Initialize components
    extractor = FinancialDataExtractor()
    processor = PDFProcessor(extractor)
    
    # Test file with known equity statement (from our analysis)
    test_file = "tests/fixtures/light/afs-2021-2023 - statement extracted.pdf"
    
    if not os.path.exists(test_file):
        print(f"[ERROR] File not found: {test_file}")
        return
        
    print(f"TESTING: {os.path.basename(test_file)}")
    print("=" * 60)
    
    try:
        # Convert PDF to images
        print(f"[INFO] Converting PDF to images...")
        images, page_info = processor.convert_pdf_to_images(test_file, enable_parallel=True)
        
        if not images:
            print(f"[ERROR] No images extracted")
            return
            
        print(f"[INFO] PDF converted to {len(images)} pages")
        
        # Test classification on all pages
        print(f"[INFO] Running four-score classification on all pages...")
        financial_pages = processor.classify_pages_with_vision(images)
        
        # Display results
        print(f"\n[RESULTS] Classification Results:")
        print(f"  Total pages: {len(images)}")
        print(f"  Financial pages identified: {len(financial_pages)}")
        
        if financial_pages:
            print(f"\n  Financial pages breakdown:")
            bs_count = sum(1 for p in financial_pages if p['statement_type'] == 'balance_sheet')
            is_count = sum(1 for p in financial_pages if p['statement_type'] == 'income_statement')
            cf_count = sum(1 for p in financial_pages if p['statement_type'] == 'cash_flow')
            es_count = sum(1 for p in financial_pages if p['statement_type'] == 'equity_statement')
            
            print(f"    Balance Sheet pages: {bs_count}")
            print(f"    Income Statement pages: {is_count}")
            print(f"    Cash Flow pages: {cf_count}")
            print(f"    Equity Statement pages: {es_count}")
            
            print(f"\n  Page details:")
            for page in financial_pages:
                scores = page['scores']
                print(f"    Page {page['page_num'] + 1}: {page['statement_type']} "
                      f"(BS:{scores['balance_sheet']}, IS:{scores['income_statement']}, CF:{scores['cash_flow']}, ES:{scores['equity_statement']}) "
                      f"Confidence: {page['confidence']:.2f}")
        else:
            print(f"  [WARNING] No financial pages identified!")
            
        # Check if we captured the equity statement (should be page 3 based on our analysis)
        equity_pages = [p for p in financial_pages if p['statement_type'] == 'equity_statement']
        if equity_pages:
            print(f"\n[SUCCESS] ✅ Equity statements detected: {len(equity_pages)} pages")
            for page in equity_pages:
                print(f"    Page {page['page_num'] + 1}: Equity Statement (ES score: {page['scores']['equity_statement']})")
        else:
            print(f"\n[WARNING] ❌ No equity statements detected - may need prompt refinement")
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_four_score_classification()


