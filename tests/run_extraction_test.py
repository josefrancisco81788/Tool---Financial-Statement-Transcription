#!/usr/bin/env python3
"""
Lightweight test runner for financial statement extraction
Simple, focused test runner without complex abstractions
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

def run_extraction_test(pdf_path: str, output_dir: str = None):
    """
    Run extraction test on a single PDF file
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save results (optional)
        
    Returns:
        dict: Test results
    """
    print("=" * 80)
    print(f"EXTRACTION TEST: {os.path.basename(pdf_path)}")
    print("=" * 80)
    
    # Default output to tests/outputs
    if output_dir is None:
        output_dir = "tests/outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize components
    extractor = FinancialDataExtractor()
    processor = PDFProcessor(extractor)
    
    results = {
        "test_time": datetime.now().isoformat(),
        "pdf_path": pdf_path,
        "pdf_name": os.path.basename(pdf_path),
        "status": "started"
    }
    
    try:
        # Step 1: PDF to Images
        print("\n[STEP 1] Converting PDF to images...")
        start_time = time.time()
        
        images, page_info = processor.convert_pdf_to_images(pdf_path, enable_parallel=True)
        conversion_time = time.time() - start_time
        
        if not images:
            raise Exception("No images extracted from PDF")
            
        print(f"[OK] Converted {len(images)} pages in {conversion_time:.2f}s")
        
        results["pdf_info"] = {
            "total_pages": len(images),
            "conversion_time": conversion_time
        }
        
        # Step 2: Four-Score Classification
        print("\n[STEP 2] Classifying financial statement pages...")
        start_time = time.time()
        
        financial_pages = processor.classify_pages_with_vision(images)
        classification_time = time.time() - start_time
        
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
                
        print(f"[OK] Found {len(financial_pages)} financial pages in {classification_time:.2f}s")
        print(f"     BS: {statement_counts['balance_sheet']}, "
              f"IS: {statement_counts['income_statement']}, "
              f"CF: {statement_counts['cash_flow']}, "
              f"ES: {statement_counts['equity_statement']}")
        
        results["classification"] = {
            "financial_pages": len(financial_pages),
            "processing_time": classification_time,
            "statement_counts": statement_counts
        }
        
        # Step 3: Extract Financial Data
        print("\n[STEP 3] Extracting financial data...")
        start_time = time.time()
        
        all_extractions = []
        for idx, page in enumerate(financial_pages, 1):
            print(f"  Processing page {idx}/{len(financial_pages)} ({page['statement_type']})...")
            
            try:
                template_mappings = extractor.extract_template_fields_from_image(
                    page['image_base64'],
                    page['statement_type']
                )
                
                if template_mappings:
                    all_extractions.append({
                        "page_num": page['page_num'],
                        "statement_type": page['statement_type'],
                        "fields_extracted": len(template_mappings),
                        "data": template_mappings
                    })
                    print(f"    Extracted {len(template_mappings)} fields")
                else:
                    print(f"    No fields extracted")
                    
            except Exception as e:
                print(f"    ERROR: {str(e)}")
                
        extraction_time = time.time() - start_time
        print(f"[OK] Extraction completed in {extraction_time:.2f}s")
        
        results["extraction"] = {
            "pages_processed": len(financial_pages),
            "pages_with_data": len(all_extractions),
            "processing_time": extraction_time,
            "extractions": all_extractions
        }
        
        # Save results
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        results_file = os.path.join(output_dir, f"{base_name}_extraction_results.json")
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        print(f"\n[OK] Results saved to: {results_file}")
        results["results_file"] = results_file
        results["status"] = "success"
        
        return results
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        results["status"] = "error"
        results["error"] = str(e)
        return results


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run financial statement extraction test")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("-o", "--output", help="Output directory", default="tests/outputs")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        print(f"ERROR: File not found: {args.pdf_path}")
        sys.exit(1)
        
    results = run_extraction_test(args.pdf_path, args.output)
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Status: {results['status'].upper()}")
    if 'classification' in results:
        print(f"Financial Pages: {results['classification']['financial_pages']}")
    if 'extraction' in results:
        print(f"Pages with Data: {results['extraction']['pages_with_data']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
