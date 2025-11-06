#!/usr/bin/env python3
"""
Consolidated classification tests for the four-score system
Tests classification accuracy across all test files
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.pdf_processor import PDFProcessor
from core.extractor import FinancialDataExtractor


def test_classification_single_file(pdf_path):
    """Test classification on a single PDF file"""
    
    print(f"\n{'='*80}")
    print(f"TESTING: {os.path.basename(pdf_path)}")
    print(f"{'='*80}")
    
    if not os.path.exists(pdf_path):
        print(f"[SKIP] File not found: {pdf_path}")
        return None
    
    # Initialize components
    # Note: FinancialDataExtractor defaults to Claude (Anthropic) provider
    # Set AI_PROVIDER environment variable to use a different provider
    extractor = FinancialDataExtractor()
    processor = PDFProcessor(extractor)
    
    results = {
        "pdf_path": pdf_path,
        "pdf_name": os.path.basename(pdf_path),
        "status": "started"
    }
    
    try:
        # Step 1: Convert PDF to images
        print(f"[INFO] Converting PDF to images...")
        start_time = time.time()
        
        images, page_info = processor.convert_pdf_to_images(pdf_path, enable_parallel=True)
        conversion_time = time.time() - start_time
        
        if not images:
            print(f"[ERROR] No images extracted")
            return None
            
        print(f"[OK] Converted {len(images)} pages in {conversion_time:.2f}s")
        
        # Step 2: Classify pages
        print(f"[INFO] Running four-score classification...")
        start_time = time.time()
        
        financial_pages = processor.classify_pages_with_vision(images)
        classification_time = time.time() - start_time
        
        # Analyze results
        statement_counts = {
            'balance_sheet': 0,
            'income_statement': 0,
            'cash_flow': 0,
            'equity_statement': 0
        }
        
        for page in financial_pages:
            stmt_type = page['statement_type']
            if stmt_type in statement_counts:
                statement_counts[stmt_type] += 1
        
        avg_confidence = sum(p['confidence'] for p in financial_pages) / len(financial_pages) if financial_pages else 0
        
        # Display results
        print(f"\n[RESULTS] Classification Complete:")
        print(f"  Total pages: {len(images)}")
        print(f"  Financial pages: {len(financial_pages)}")
        print(f"  Average confidence: {avg_confidence:.1f}%")
        print(f"\n  Statement breakdown:")
        print(f"    Balance Sheet: {statement_counts['balance_sheet']}")
        print(f"    Income Statement: {statement_counts['income_statement']}")
        print(f"    Cash Flow: {statement_counts['cash_flow']}")
        print(f"    Equity Statement: {statement_counts['equity_statement']}")
        
        print(f"\n  Page details:")
        for page in financial_pages:
            scores = page['scores']
            print(f"    Page {page['page_num'] + 1}: {page['statement_type']} "
                  f"(BS:{scores['balance_sheet']}, IS:{scores['income_statement']}, "
                  f"CF:{scores['cash_flow']}, ES:{scores['equity_statement']}) "
                  f"Conf: {page['confidence']:.0f}%")
        
        results["classification"] = {
            "total_pages": len(images),
            "financial_pages": len(financial_pages),
            "processing_time": classification_time,
            "average_confidence": avg_confidence,
            "statement_counts": statement_counts,
            "pages": []
        }
        
        for page in financial_pages:
            results["classification"]["pages"].append({
                "page_num": page['page_num'],
                "statement_type": page['statement_type'],
                "confidence": page['confidence'],
                "scores": page['scores']
            })
        
        results["status"] = "success"
        results["conversion_time"] = conversion_time
        
        return results
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        results["status"] = "error"
        results["error"] = str(e)
        return results


def test_classification_all_files():
    """Test classification on all LIGHT test files"""
    
    print("=" * 80)
    print("FOUR-SCORE CLASSIFICATION TEST - ALL FILES")
    print("=" * 80)
    
    test_files = [
        "tests/fixtures/light/AFS2024 - statement extracted.pdf",
        "tests/fixtures/light/AFS-2022 - statement extracted.pdf",
        "tests/fixtures/light/2021 AFS with SEC Stamp - statement extracted.pdf",
        "tests/fixtures/light/afs-2021-2023 - statement extracted.pdf"
    ]
    
    all_results = {
        "test_time": datetime.now().isoformat(),
        "test_type": "classification_comprehensive",
        "files": {}
    }
    
    for i, test_file in enumerate(test_files, 1):
        print(f"\n\nFile {i}/{len(test_files)}")
        result = test_classification_single_file(test_file)
        
        if result:
            all_results["files"][result["pdf_name"]] = result
    
    # Save results
    output_file = "tests/outputs/classification_test_results.json"
    os.makedirs("tests/outputs", exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    
    for name, result in all_results["files"].items():
        if result.get("status") == "success":
            classification = result.get("classification", {})
            print(f"{name}:")
            print(f"  Financial pages: {classification.get('financial_pages', 0)}")
            print(f"  Avg confidence: {classification.get('average_confidence', 0):.1f}%")
            
            counts = classification.get("statement_counts", {})
            print(f"  BS:{counts.get('balance_sheet', 0)}, "
                  f"IS:{counts.get('income_statement', 0)}, "
                  f"CF:{counts.get('cash_flow', 0)}, "
                  f"ES:{counts.get('equity_statement', 0)}")
    
    print(f"\n[OK] Results saved to: {output_file}")
    print(f"{'='*80}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test four-score classification system")
    parser.add_argument("pdf_path", nargs="?", help="Single PDF file to test (optional)")
    parser.add_argument("--all", action="store_true", help="Test all LIGHT files")
    
    args = parser.parse_args()
    
    if args.all:
        test_classification_all_files()
    elif args.pdf_path:
        test_classification_single_file(args.pdf_path)
    else:
        # Default: test all files
        test_classification_all_files()


if __name__ == "__main__":
    main()
