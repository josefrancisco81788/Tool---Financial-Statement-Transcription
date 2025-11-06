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
from tests.core.csv_exporter import CSVExporter

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
    # Note: FinancialDataExtractor defaults to Claude (Anthropic) provider
    # Set AI_PROVIDER environment variable to use a different provider
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
        combined_template_mappings = {}
        
        # Check if batch processing should be used (8+ financial pages)
        use_batch_extraction = len(financial_pages) >= 8
        
        if use_batch_extraction:
            print(f"[INFO] Using BATCH extraction for {len(financial_pages)} financial pages")
            
            try:
                # Use integrated batch processing on pre-classified pages
                batch_results = processor.process_with_batch_extraction(financial_pages)
                
                # Debug: Check actual return format
                print(f"[DEBUG] batch_results type: {type(batch_results)}")
                if isinstance(batch_results, dict):
                    print(f"[DEBUG] batch_results keys: {list(batch_results.keys())}")
                    if 'template_mappings' in batch_results:
                        print(f"[DEBUG] batch_results template_mappings count: {len(batch_results['template_mappings'])}")
                elif isinstance(batch_results, list):
                    print(f"[DEBUG] batch_results list length: {len(batch_results)}")
                    if batch_results:
                        print(f"[DEBUG] First item type: {type(batch_results[0])}")
                        if isinstance(batch_results[0], dict):
                            print(f"[DEBUG] First item keys: {list(batch_results[0].keys())}")
                
                # Handle batch return format - check if it's new combined format (dict) or legacy format (list)
                if isinstance(batch_results, dict) and 'template_mappings' in batch_results:
                    # New batch format - already combined into single dict
                    combined_template_mappings = batch_results.get('template_mappings', {})
                    print(f"[INFO] ✅ Batch processing returned {len(combined_template_mappings)} combined template mappings")
                    
                    # Track pages processed (from metadata or use actual page numbers from financial_pages)
                    pages_processed = batch_results.get('pages_processed', len(financial_pages))
                    
                    # Create extraction records for tracking (use actual page numbers from financial_pages)
                    for i, page in enumerate(financial_pages):
                        page_num = page.get('page_num', i + 1)
                        all_extractions.append({
                            "page_num": page_num,
                            "statement_type": page.get('statement_type', 'batch_processed'),
                            "fields_extracted": len(combined_template_mappings),
                            "data": combined_template_mappings
                        })
                    
                    print(f"[INFO] ✅ Batch processing: {pages_processed} pages processed, {len(combined_template_mappings)} unique fields extracted")
                    print(f"[INFO] ✅ Created {len(all_extractions)} extraction records for CSV export")
                    
                elif isinstance(batch_results, list):
                    # Legacy format - list of per-page results
                    print(f"[INFO] Processing legacy batch format: {len(batch_results)} results")
                    for result in batch_results:
                        if result and isinstance(result, dict) and 'error' not in result:
                            # Extract data from batch result - format from convert_batch_results_to_standard_format
                            page_num = result.get('page_num')
                            if page_num is None:
                                print(f"[WARN] Page number missing from batch result: {result.keys()}")
                                continue
                            
                            extracted_data = result.get('extracted_data', {})
                            statement_type = result.get('statement_type', 'unknown')
                            
                            # Extract template_mappings from extracted_data
                            # The format should match what process_pdf_with_vector_db expects
                            if isinstance(extracted_data, dict):
                                template_mappings = extracted_data.get('template_mappings', {})
                            else:
                                # Fallback: if extracted_data is not a dict, check result directly
                                template_mappings = result.get('template_mappings', {})
                            
                            if template_mappings:
                                all_extractions.append({
                                    "page_num": page_num,
                                    "statement_type": statement_type,
                                    "fields_extracted": len(template_mappings),
                                    "data": template_mappings
                                })
                                # Combine all template mappings
                                combined_template_mappings.update(template_mappings)
                                print(f"    Page {page_num + 1}: Extracted {len(template_mappings)} fields")
                            else:
                                print(f"    Page {page_num + 1}: No template mappings found")
                else:
                    # Unexpected format
                    print(f"[ERROR] Unexpected batch_results format: {type(batch_results)}")
                    print(f"[ERROR] batch_results keys: {batch_results.keys() if isinstance(batch_results, dict) else 'N/A'}")
                    combined_template_mappings = {}
                
                # Display cost summary if available
                processor.display_cost_summary(batch_results)
                
            except Exception as e:
                print(f"[ERROR] Batch extraction failed: {e}")
                print("[INFO] Falling back to sequential processing")
                use_batch_extraction = False
        
        # Sequential processing for small docs (< 8 pages) or fallback
        if not use_batch_extraction:
            # Extract years from financial pages before processing
            print("[INFO] Extracting years from financial pages...")
            page_images = []
            max_page_num = max((page.get('page_num', 0) for page in financial_pages), default=0)
            page_images = [None] * (max_page_num + 1)
            for page in financial_pages:
                page_num = page.get('page_num', 0)
                if 'image' in page:
                    page_images[page_num] = page['image']
            
            year_data = processor._extract_years_from_financial_pages(page_images, financial_pages)
            
            for idx, page in enumerate(financial_pages, 1):
                print(f"  Processing page {idx}/{len(financial_pages)} ({page['statement_type']})...")
                
                try:
                    base64_image = extractor.encode_image(page['image'])
                    
                    extracted_data = extractor.extract_comprehensive_financial_data(
                        base64_image,
                        page['statement_type'],
                        ""
                    )
                    
                    if extracted_data and 'template_mappings' in extracted_data:
                        template_mappings = extracted_data['template_mappings']
                        all_extractions.append({
                            "page_num": page['page_num'],
                            "statement_type": page['statement_type'],
                            "fields_extracted": len(template_mappings),
                            "data": template_mappings
                        })
                        
                        # Combine all template mappings
                        combined_template_mappings.update(template_mappings)
                        print(f"    Extracted {len(template_mappings)} fields")
                    else:
                        print(f"    No fields extracted")
                        
                except Exception as e:
                    print(f"    ERROR: {str(e)}")
            
            # Add Year field to combined_template_mappings AFTER all pages are processed
            # This ensures it won't be overwritten by page-level extractions
            if not use_batch_extraction and year_data and year_data.get('years'):
                years = year_data['years']
                combined_template_mappings['Year'] = {
                    'value': years[0] if years else None,
                    'confidence': year_data.get('confidence', 0.95),
                    'Value_Year_1': years[0] if len(years) > 0 else None,
                    'Value_Year_2': years[1] if len(years) > 1 else None,
                    'Value_Year_3': years[2] if len(years) > 2 else None,
                    'Value_Year_4': years[3] if len(years) > 3 else None,
                    'source': year_data.get('source', 'vision_extraction')
                }
                print(f"[INFO] Year field populated: {years}")
                
        extraction_time = time.time() - start_time
        print(f"[OK] Extraction completed in {extraction_time:.2f}s")
        
        # Verify Year field is in combined_template_mappings
        if 'Year' in combined_template_mappings:
            year_info = combined_template_mappings['Year']
            print(f"[INFO] Year field confirmed in combined_template_mappings: value={year_info.get('value')}, years=[{year_info.get('Value_Year_1')}, {year_info.get('Value_Year_2')}]")
        else:
            print(f"[WARN] Year field NOT in combined_template_mappings. Keys: {list(combined_template_mappings.keys())[:10]}")
        
        results["extraction"] = {
            "pages_processed": len(financial_pages),
            "pages_with_data": len(all_extractions),
            "processing_time": extraction_time,
            "extractions": all_extractions,
            "combined_fields": len(combined_template_mappings),
            "combined_template_mappings": combined_template_mappings  # Include for debugging
        }
        
        # Generate CSV export
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        if combined_template_mappings:
            print(f"\n[STEP 4] Generating CSV export...")
            csv_exporter = CSVExporter()
            
            # Save CSV file using the correct method
            csv_file = os.path.join(output_dir, f"{base_name}_template_export.csv")
            
            # Convert template_mappings to the expected format
            formatted_data = {
                "template_mappings": combined_template_mappings,
                "statement_type": "combined",
                "years_detected": ["2024", "2023"]
            }
            
            success = csv_exporter.export_to_template_csv(formatted_data, csv_file)
            
            if success:
                print(f"[OK] CSV saved to: {csv_file}")
                results["csv_file"] = csv_file
            else:
                print(f"[WARNING] CSV export failed")
        else:
            print(f"\n[WARNING] No template fields extracted - skipping CSV generation")
        
        # Save JSON results
        results_file = os.path.join(output_dir, f"{base_name}_extraction_results.json")
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        print(f"\n[OK] JSON results saved to: {results_file}")
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
