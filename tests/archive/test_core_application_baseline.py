#!/usr/bin/env python3
"""
Test the core application on each LIGHT file individually to establish baseline performance
Shows detailed results for each file to understand current system capabilities
"""

import sys
import os
import time
import json
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from core.pdf_processor import PDFProcessor
from core.extractor import FinancialDataExtractor

def test_core_application_baseline():
    """Test core application on each LIGHT file individually"""
    
    print("=" * 80)
    print("CORE APPLICATION BASELINE TEST - LIGHT FILES")
    print("=" * 80)
    
    # Initialize components
    extractor = FinancialDataExtractor()
    processor = PDFProcessor(extractor)
    
    # Test files (LIGHT files - one at a time)
    test_files = [
        "tests/fixtures/light/AFS2024 - statement extracted.pdf",
        "tests/fixtures/light/AFS-2022 - statement extracted.pdf", 
        "tests/fixtures/light/2021 AFS with SEC Stamp - statement extracted.pdf",
        "tests/fixtures/light/afs-2021-2023 - statement extracted.pdf"
    ]
    
    results = {
        "test_time": datetime.now().isoformat(),
        "test_type": "core_application_baseline",
        "files": {}
    }
    
    for i, test_file in enumerate(test_files, 1):
        if not os.path.exists(test_file):
            print(f"[SKIP] File not found: {test_file}")
            continue
            
        print(f"\n{'='*80}")
        print(f"TEST {i}/4: {os.path.basename(test_file)}")
        print(f"{'='*80}")
        
        file_results = {
            "file_path": test_file,
            "file_name": os.path.basename(test_file),
            "processing": {},
            "classification": {},
            "extraction": {},
            "template_analysis": {}
        }
        
        try:
            # Step 1: PDF Processing
            print(f"[STEP 1] PDF Processing...")
            start_time = time.time()
            
            images, page_info = processor.convert_pdf_to_images(test_file, enable_parallel=True)
            processing_time = time.time() - start_time
            
            if not images:
                print(f"[ERROR] No images extracted from {test_file}")
                file_results["error"] = "No images extracted"
                continue
                
            print(f"[SUCCESS] PDF converted to {len(images)} pages in {processing_time:.2f}s")
            
            file_results["processing"] = {
                "total_pages": len(images),
                "processing_time_seconds": processing_time,
                "page_info": page_info
            }
            
            # Step 2: Four-Score Classification
            print(f"[STEP 2] Four-Score Classification...")
            start_time = time.time()
            
            financial_pages = processor.classify_pages_with_vision(images)
            classification_time = time.time() - start_time
            
            print(f"[SUCCESS] Classification completed in {classification_time:.2f}s")
            
            # Analyze classification results
            statement_breakdown = {
                'balance_sheet': len([p for p in financial_pages if p['statement_type'] == 'balance_sheet']),
                'income_statement': len([p for p in financial_pages if p['statement_type'] == 'income_statement']),
                'cash_flow': len([p for p in financial_pages if p['statement_type'] == 'cash_flow']),
                'equity_statement': len([p for p in financial_pages if p['statement_type'] == 'equity_statement'])
            }
            
            avg_confidence = sum(p['confidence'] for p in financial_pages) / len(financial_pages) if financial_pages else 0
            
            file_results["classification"] = {
                "total_financial_pages": len(financial_pages),
                "statement_breakdown": statement_breakdown,
                "average_confidence": avg_confidence,
                "classification_time_seconds": classification_time,
                "page_details": [
                    {
                        "page_number": p['page_num'] + 1,
                        "statement_type": p['statement_type'],
                        "confidence": p['confidence'],
                        "scores": p['scores']
                    } for p in financial_pages
                ]
            }
            
            # Step 3: Financial Data Extraction
            print(f"[STEP 3] Financial Data Extraction...")
            start_time = time.time()
            
            extraction_results = []
            total_template_fields = 0
            successful_extractions = 0
            
            for page in financial_pages:
                try:
                    base64_image = processor.extractor.encode_image(page['image'])
                    statement_type = page['statement_type']
                    
                    print(f"  Processing page {page['page_num'] + 1} ({statement_type})...")
                    
                    extracted_data = processor.extractor.extract_comprehensive_financial_data(
                        base64_image, 
                        statement_type, 
                        ""
                    )
                    
                    if extracted_data and 'error' not in extracted_data:
                        template_mappings = extracted_data.get('template_mappings', {})
                        total_template_fields += len(template_mappings)
                        successful_extractions += 1
                        
                        extraction_results.append({
                            'page_num': page['page_num'],
                            'statement_type': statement_type,
                            'template_fields_count': len(template_mappings),
                            'confidence': page['confidence'],
                            'sample_fields': list(template_mappings.keys())[:5] if template_mappings else []
                        })
                        
                        print(f"    [SUCCESS] Extracted {len(template_mappings)} template fields")
                    else:
                        print(f"    [FAILED] Extraction failed")
                        extraction_results.append({
                            'page_num': page['page_num'],
                            'statement_type': statement_type,
                            'template_fields_count': 0,
                            'confidence': page['confidence'],
                            'error': extracted_data.get('error', 'Unknown error') if extracted_data else 'No data returned'
                        })
                        
                except Exception as e:
                    print(f"    [ERROR] Extraction error: {e}")
                    extraction_results.append({
                        'page_num': page['page_num'],
                        'statement_type': statement_type,
                        'template_fields_count': 0,
                        'confidence': page['confidence'],
                        'error': str(e)
                    })
                    continue
            
            extraction_time = time.time() - start_time
            
            file_results["extraction"] = {
                "pages_processed": len(extraction_results),
                "successful_extractions": successful_extractions,
                "total_template_fields": total_template_fields,
                "extraction_time_seconds": extraction_time,
                "page_details": extraction_results
            }
            
            # Step 4: Template Analysis
            print(f"[STEP 4] Template Analysis...")
            
            # Analyze template field distribution
            all_template_fields = []
            for result in extraction_results:
                if 'sample_fields' in result:
                    all_template_fields.extend(result['sample_fields'])
            
            # Count unique template fields
            unique_template_fields = list(set(all_template_fields))
            
            file_results["template_analysis"] = {
                "total_template_fields_extracted": total_template_fields,
                "unique_template_fields": len(unique_template_fields),
                "sample_template_fields": unique_template_fields[:10],
                "average_fields_per_page": total_template_fields / len(financial_pages) if financial_pages else 0
            }
            
            # Display comprehensive results
            print(f"\n[RESULTS] Core Application Performance:")
            print(f"  📄 File: {os.path.basename(test_file)}")
            print(f"  📊 Total pages: {len(images)}")
            print(f"  🎯 Financial pages identified: {len(financial_pages)}")
            print(f"  📈 Statement breakdown: {statement_breakdown}")
            print(f"  🎯 Average confidence: {avg_confidence:.2f}")
            print(f"  📋 Template fields extracted: {total_template_fields}")
            print(f"  ✅ Successful extractions: {successful_extractions}/{len(financial_pages)}")
            print(f"  ⏱️  Total processing time: {processing_time + classification_time + extraction_time:.2f}s")
            
            # Show page-by-page breakdown
            print(f"\n  📋 Page-by-page breakdown:")
            for result in extraction_results:
                page_num = result['page_num'] + 1
                statement_type = result['statement_type']
                fields_count = result['template_fields_count']
                confidence = result['confidence']
                
                if fields_count > 0:
                    print(f"    Page {page_num}: {statement_type} - {fields_count} fields (confidence: {confidence:.2f})")
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"    Page {page_num}: {statement_type} - FAILED ({error})")
            
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
    results_file = f"core_application_baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*80}")
    print("CORE APPLICATION BASELINE TEST COMPLETE")
    print(f"Results saved to: {results_file}")
    print(f"{'='*80}")
    
    # Overall summary
    total_files = len([f for f in test_files if os.path.exists(f)])
    successful_files = len([f for f in results["files"].values() if "error" not in f])
    
    if successful_files > 0:
        # Calculate overall statistics
        all_financial_pages = sum(f["classification"]["total_financial_pages"] for f in results["files"].values() if "error" not in f)
        all_template_fields = sum(f["extraction"]["total_template_fields"] for f in results["files"].values() if "error" not in f)
        all_equity_pages = sum(f["classification"]["statement_breakdown"]["equity_statement"] for f in results["files"].values() if "error" not in f)
        all_processing_time = sum(f["processing"]["processing_time_seconds"] + f["classification"]["classification_time_seconds"] + f["extraction"]["extraction_time_seconds"] for f in results["files"].values() if "error" not in f)
        
        print(f"\n[OVERALL SUMMARY]")
        print(f"  📁 Files tested: {total_files}")
        print(f"  ✅ Successful: {successful_files}")
        print(f"  ❌ Failed: {total_files - successful_files}")
        print(f"  📊 Total financial pages identified: {all_financial_pages}")
        print(f"  📋 Total template fields extracted: {all_template_fields}")
        print(f"  🏛️  Total equity statement pages: {all_equity_pages}")
        print(f"  ⏱️  Total processing time: {all_processing_time:.2f}s")
        print(f"  📈 Average template fields per page: {all_template_fields / all_financial_pages if all_financial_pages > 0 else 0:.1f}")
        print(f"  🎯 Average processing time per page: {all_processing_time / all_financial_pages if all_financial_pages > 0 else 0:.2f}s")

if __name__ == "__main__":
    test_core_application_baseline()
