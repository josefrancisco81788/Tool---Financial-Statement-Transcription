#!/usr/bin/env python3
"""
Test the core application and output detailed CSV results for manual review
Creates CSV files with all extracted template fields for each file
"""

import sys
import os
import time
import csv
import pandas as pd
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.pdf_processor import PDFProcessor
from core.extractor import FinancialDataExtractor

def test_core_application_csv_output():
    """Test core application and output detailed CSV results"""
    
    print("=" * 80)
    print("CORE APPLICATION CSV OUTPUT TEST")
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
    
    # Create output directory
    output_dir = f"csv_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)
    
    summary_data = []
    
    for i, test_file in enumerate(test_files, 1):
        if not os.path.exists(test_file):
            print(f"[SKIP] File not found: {test_file}")
            continue
            
        print(f"\n{'='*80}")
        print(f"TEST {i}/4: {os.path.basename(test_file)}")
        print(f"{'='*80}")
        
        file_name = os.path.basename(test_file).replace('.pdf', '')
        
        try:
            # Step 1: PDF Processing
            print(f"[STEP 1] PDF Processing...")
            start_time = time.time()
            
            images, page_info = processor.convert_pdf_to_images(test_file, enable_parallel=True)
            processing_time = time.time() - start_time
            
            if not images:
                print(f"[ERROR] No images extracted from {test_file}")
                continue
                
            print(f"[SUCCESS] PDF converted to {len(images)} pages in {processing_time:.2f}s")
            
            # Step 2: Four-Score Classification
            print(f"[STEP 2] Four-Score Classification...")
            start_time = time.time()
            
            financial_pages = processor.classify_pages_with_vision(images)
            classification_time = time.time() - start_time
            
            print(f"[SUCCESS] Classification completed in {classification_time:.2f}s")
            
            # Step 3: Financial Data Extraction with CSV Output
            print(f"[STEP 3] Financial Data Extraction...")
            start_time = time.time()
            
            all_extracted_data = []
            page_summary = []
            
            for page in financial_pages:
                try:
                    base64_image = processor.extractor.encode_image(page['image'])
                    statement_type = page['statement_type']
                    page_num = page['page_num'] + 1
                    
                    print(f"  Processing page {page_num} ({statement_type})...")
                    
                    extracted_data = processor.extractor.extract_comprehensive_financial_data(
                        base64_image, 
                        statement_type, 
                        ""
                    )
                    
                    if extracted_data and 'error' not in extracted_data:
                        template_mappings = extracted_data.get('template_mappings', {})
                        
                        # Add each template field to the detailed CSV
                        for field_name, field_data in template_mappings.items():
                            row = {
                                'file_name': file_name,
                                'page_number': page_num,
                                'statement_type': statement_type,
                                'confidence': page['confidence'],
                                'template_field': field_name,
                                'value': field_data.get('value', ''),
                                'field_confidence': field_data.get('confidence', ''),
                                'value_year_1': field_data.get('Value_Year_1', ''),
                                'value_year_2': field_data.get('Value_Year_2', ''),
                                'value_year_3': field_data.get('Value_Year_3', ''),
                                'value_year_4': field_data.get('Value_Year_4', ''),
                                'raw_field_data': str(field_data)
                            }
                            all_extracted_data.append(row)
                        
                        page_summary.append({
                            'file_name': file_name,
                            'page_number': page_num,
                            'statement_type': statement_type,
                            'confidence': page['confidence'],
                            'template_fields_count': len(template_mappings),
                            'sample_fields': ', '.join(list(template_mappings.keys())[:5])
                        })
                        
                        print(f"    ✅ Extracted {len(template_mappings)} template fields")
                    else:
                        error_msg = extracted_data.get('error', 'Unknown error') if extracted_data else 'No data returned'
                        page_summary.append({
                            'file_name': file_name,
                            'page_number': page_num,
                            'statement_type': statement_type,
                            'confidence': page['confidence'],
                            'template_fields_count': 0,
                            'sample_fields': f"ERROR: {error_msg}"
                        })
                        print(f"    ❌ Extraction failed: {error_msg}")
                        
                except Exception as e:
                    page_summary.append({
                        'file_name': file_name,
                        'page_number': page_num,
                        'statement_type': statement_type,
                        'confidence': page['confidence'],
                        'template_fields_count': 0,
                        'sample_fields': f"ERROR: {str(e)}"
                    })
                    print(f"    ❌ Extraction error: {e}")
                    continue
            
            extraction_time = time.time() - start_time
            
            # Step 4: Create CSV files
            print(f"[STEP 4] Creating CSV files...")
            
            # Create detailed CSV with all template fields
            if all_extracted_data:
                detailed_csv_path = os.path.join(output_dir, f"{file_name}_detailed_extraction.csv")
                df_detailed = pd.DataFrame(all_extracted_data)
                df_detailed.to_csv(detailed_csv_path, index=False)
                print(f"  ✅ Detailed CSV created: {detailed_csv_path}")
            
            # Create summary CSV
            summary_csv_path = os.path.join(output_dir, f"{file_name}_summary.csv")
            df_summary = pd.DataFrame(page_summary)
            df_summary.to_csv(summary_csv_path, index=False)
            print(f"  ✅ Summary CSV created: {summary_csv_path}")
            
            # Add to overall summary
            total_fields = sum(p['template_fields_count'] for p in page_summary)
            summary_data.append({
                'file_name': file_name,
                'total_pages': len(images),
                'financial_pages': len(financial_pages),
                'total_template_fields': total_fields,
                'processing_time_seconds': processing_time + classification_time + extraction_time,
                'success_rate': f"{len([p for p in page_summary if p['template_fields_count'] > 0])}/{len(page_summary)}"
            })
            
            # Display results
            print(f"\n[RESULTS] {file_name}:")
            print(f"  📊 Total pages: {len(images)}")
            print(f"  🎯 Financial pages: {len(financial_pages)}")
            print(f"  📋 Template fields: {total_fields}")
            print(f"  ⏱️  Processing time: {processing_time + classification_time + extraction_time:.2f}s")
            print(f"  📁 CSV files created in: {output_dir}/")
                
        except Exception as e:
            print(f"[ERROR] Test failed for {test_file}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Create overall summary CSV
    if summary_data:
        overall_summary_path = os.path.join(output_dir, "overall_summary.csv")
        df_overall = pd.DataFrame(summary_data)
        df_overall.to_csv(overall_summary_path, index=False)
        print(f"\n✅ Overall summary CSV created: {overall_summary_path}")
    
    print(f"\n{'='*80}")
    print("CSV OUTPUT TEST COMPLETE")
    print(f"All CSV files saved in: {output_dir}/")
    print(f"{'='*80}")
    
    # List all created files
    print(f"\n📁 Created CSV files:")
    for file in os.listdir(output_dir):
        if file.endswith('.csv'):
            file_path = os.path.join(output_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"  📄 {file} ({file_size:,} bytes)")
    
    # Overall summary
    if summary_data:
        total_pages = sum(s['total_pages'] for s in summary_data)
        total_financial_pages = sum(s['financial_pages'] for s in summary_data)
        total_template_fields = sum(s['total_template_fields'] for s in summary_data)
        total_processing_time = sum(s['processing_time_seconds'] for s in summary_data)
        
        print(f"\n[OVERALL SUMMARY]")
        print(f"  📁 Files processed: {len(summary_data)}")
        print(f"  📊 Total pages: {total_pages}")
        print(f"  🎯 Financial pages: {total_financial_pages}")
        print(f"  📋 Template fields: {total_template_fields}")
        print(f"  ⏱️  Total processing time: {total_processing_time:.2f}s")
        print(f"  📈 Average fields per page: {total_template_fields / total_financial_pages if total_financial_pages > 0 else 0:.1f}")

if __name__ == "__main__":
    test_core_application_csv_output()


