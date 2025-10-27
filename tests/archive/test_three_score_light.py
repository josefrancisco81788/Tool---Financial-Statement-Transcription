#!/usr/bin/env python3
"""
Test script for three-score vision-based classification system
Tests on LIGHT files first (smaller, faster)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.pdf_processor import PDFProcessor
from core.extractor import FinancialDataExtractor
from core.config import Config

def test_three_score_classification_light():
    """Test the three-score classification on LIGHT files first"""
    
    print("=" * 80)
    print("TESTING THREE-SCORE VISION CLASSIFICATION - LIGHT FILES")
    print("=" * 80)
    
    # Initialize components
    extractor = FinancialDataExtractor()
    processor = PDFProcessor(extractor)
    
    # Test files (LIGHT files - smaller, faster)
    test_files = [
        "tests/fixtures/light/AFS2024 - statement extracted.pdf",
        "tests/fixtures/light/AFS-2022 - statement extracted.pdf"
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
            
            # Test the new three-score classification on just first page
            print(f"[INFO] Running three-score classification on first page only...")
            first_page = [images[0]]  # Test just first page
            financial_pages = processor.classify_pages_with_vision(first_page)
            
            # Display results
            print(f"\n[RESULTS] Classification Results:")
            print(f"  Total pages tested: {len(first_page)}")
            print(f"  Financial pages identified: {len(financial_pages)}")
            
            if financial_pages:
                page = financial_pages[0]
                scores = page['scores']
                print(f"  Page 1: {page['statement_type']} (BS:{scores['balance_sheet']}, IS:{scores['income_statement']}, CF:{scores['cash_flow']})")
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
    test_three_score_classification_light()


