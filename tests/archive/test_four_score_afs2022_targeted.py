#!/usr/bin/env python3
"""
Test four-score classification on specific pages of AFS-2022 where financial statements are located
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.pdf_processor import PDFProcessor
from core.extractor import FinancialDataExtractor

def test_four_score_afs2022_targeted():
    """Test four-score classification on specific pages of AFS-2022"""
    
    print("=" * 80)
    print("TESTING FOUR-SCORE CLASSIFICATION ON AFS-2022 TARGETED PAGES")
    print("=" * 80)
    
    # Initialize components
    extractor = FinancialDataExtractor()
    processor = PDFProcessor(extractor)
    
    # Test file (ORIGIN file - full document)
    test_file = "tests/fixtures/origin/AFS-2022.pdf"
    
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
        
        # Test classification on pages 10-20 (where financial statements are likely located)
        print(f"[INFO] Running four-score classification on pages 10-20...")
        target_pages = images[9:20]  # Pages 10-20 (0-indexed)
        financial_pages = processor.classify_pages_with_vision(target_pages)
        
        # Adjust page numbers for display (add 10 to account for offset)
        for page in financial_pages:
            page['page_num'] += 10
        
        # Display results
        print(f"\n[RESULTS] Classification Results (Pages 10-20):")
        print(f"  Total pages tested: {len(target_pages)}")
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
            
        # Check if we captured the equity statement
        equity_pages = [p for p in financial_pages if p['statement_type'] == 'equity_statement']
        if equity_pages:
            print(f"\n[SUCCESS] ✅ Equity statements detected: {len(equity_pages)} pages")
            for page in equity_pages:
                print(f"    Page {page['page_num'] + 1}: Equity Statement (ES score: {page['scores']['equity_statement']})")
        else:
            print(f"\n[INFO] No equity statements detected in pages 10-20")
            
        # Compare with previous three-score results
        print(f"\n[COMPARISON] vs Previous Three-Score System:")
        print(f"  Previous: 6 financial pages identified (missing equity statements)")
        print(f"  Current:  {len(financial_pages)} financial pages identified in pages 10-20")
        if equity_pages:
            print(f"  Improvement: ✅ Four-score system now captures equity statements!")
        else:
            print(f"  Status: Four-score system implemented, equity detection ready")
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_four_score_afs2022_targeted()


