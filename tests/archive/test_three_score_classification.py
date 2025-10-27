#!/usr/bin/env python3
"""
Test script for three-score vision-based classification system
Tests the new classify_pages_with_vision() method on ORIGIN files
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.pdf_processor import PDFProcessor
from core.extractor import FinancialDataExtractor
from core.config import Config

def test_three_score_classification():
    """Test the three-score classification on ORIGIN files"""
    
    print("=" * 80)
    print("TESTING THREE-SCORE VISION CLASSIFICATION")
    print("=" * 80)
    
    # Initialize components
    extractor = FinancialDataExtractor()
    processor = PDFProcessor(extractor)
    
    # Test files (ORIGIN files - full 30-80 page documents)
    test_files = [
        "tests/fixtures/origin/AFS2024.pdf",
        "tests/fixtures/origin/AFS-2022.pdf", 
        "tests/fixtures/origin/2021 AFS with SEC Stamp.pdf",
        "tests/fixtures/origin/afs-2021-2023.pdf"
    ]
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"[SKIP] File not found: {test_file}")
            continue
            
        print(f"\n{'='*60}")
        print(f"TESTING: {os.path.basename(test_file)}")
        print(f"{'='*60}")
        
        try:
            # Test just the classification part (not full extraction)
            print(f"[INFO] Converting PDF to images...")
            images, page_info = processor.convert_pdf_to_images(test_file, enable_parallel=True)
            
            if not images:
                print(f"[ERROR] No images extracted from {test_file}")
                continue
                
            print(f"[INFO] PDF converted to {len(images)} pages")
            
            # Test the new three-score classification
            print(f"[INFO] Running three-score classification...")
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
                
                print(f"    Balance Sheet pages: {bs_count}")
                print(f"    Income Statement pages: {is_count}")
                print(f"    Cash Flow pages: {cf_count}")
                
                print(f"\n  Page details:")
                for page in financial_pages[:5]:  # Show first 5 pages
                    scores = page['scores']
                    print(f"    Page {page['page_num'] + 1}: {page['statement_type']} "
                          f"(BS:{scores['balance_sheet']}, IS:{scores['income_statement']}, CF:{scores['cash_flow']})")
                
                if len(financial_pages) > 5:
                    print(f"    ... and {len(financial_pages) - 5} more pages")
            else:
                print(f"  [WARNING] No financial pages identified!")
                
        except Exception as e:
            print(f"[ERROR] Test failed for {test_file}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n{'='*80}")
    print("THREE-SCORE CLASSIFICATION TEST COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    test_three_score_classification()


