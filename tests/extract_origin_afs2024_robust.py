#!/usr/bin/env python3
"""
Robust extraction script for AFS2024.pdf (origin document)
This is the "big boy" test - the original, unprocessed PDF
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.extractor import FinancialDataExtractor
from core.pdf_processor import PDFProcessor

def extract_and_save_robust():
    """Extract data from AFS2024.pdf using robust individual page processing"""
    
    print("🚀 Starting AFS2024.pdf (ORIGIN) extraction - Big Boy Test!")
    print("=" * 60)
    
    # Initialize components
    extractor = FinancialDataExtractor()
    pdf_processor = PDFProcessor()
    
    # File paths
    pdf_path = "tests/fixtures/origin/AFS2024.pdf"
    template_path = "tests/fixtures/templates/FS_Input_Template_Fields_AFS2024.csv"
    output_csv_path = "tests/outputs/origin_afs2024_result.csv"
    output_json_path = "tests/outputs/origin_afs2024_result.json"
    
    print(f"📄 Processing: {pdf_path}")
    print(f"📋 Template: {template_path}")
    print(f"💾 Output CSV: {output_csv_path}")
    print(f"💾 Output JSON: {output_json_path}")
    print()
    
    try:
        # Convert PDF to images
        print("🔄 Converting PDF to images...")
        with open(pdf_path, 'rb') as pdf_file:
            images, page_info = pdf_processor.convert_pdf_to_images(pdf_file)
        print(f"✅ Converted to {len(images)} images")
        
        # Process each image individually (robust approach)
        print("\n🔍 Processing each page individually...")
        all_extracted_page_data = []
        
        for i, image in enumerate(images):
            print(f"  📄 Processing page {i+1}/{len(images)}...")
            try:
                extracted_page_data = extractor.extract_comprehensive_financial_data(image)
                if extracted_page_data:
                    all_extracted_page_data.append(extracted_page_data)
                    print(f"    ✅ Page {i+1} processed successfully")
                else:
                    print(f"    ⚠️ Page {i+1} returned no data")
            except Exception as e:
                print(f"    ❌ Error processing page {i+1}: {e}")
                continue
        
        print(f"\n📊 Total pages processed: {len(all_extracted_page_data)}")
        
        # Smart consolidation - prioritize Balance Sheet data
        print("\n🧠 Smart consolidation - prioritizing Balance Sheet data...")
        final_extracted_data = None
        
        for data in all_extracted_page_data:
            if data and isinstance(data, dict) and "statement_type" in data:
                statement_type = data["statement_type"].lower()
                if "financial position" in statement_type or "balance sheet" in statement_type:
                    final_extracted_data = data
                    print(f"  ✅ Found Balance Sheet data: {data['statement_type']}")
                    break
        
        # Fallback to first available data if no Balance Sheet found
        if not final_extracted_data and all_extracted_page_data:
            final_extracted_data = all_extracted_page_data[0]
            print(f"  ⚠️ No Balance Sheet found, using first available: {final_extracted_data.get('statement_type', 'Unknown')}")
        
        if not final_extracted_data:
            raise Exception("No data extracted from any page")
        
        # Load template
        print(f"\n📋 Loading template: {template_path}")
        template_df = pd.read_csv(template_path)
        print(f"  ✅ Template loaded: {len(template_df)} fields")
        
        # Map to template
        print("\n🔄 Mapping extracted data to template...")
        mapped_df = map_to_template(final_extracted_data, template_df)
        
        # Count mapped fields
        mapped_fields = 0
        for col in ['Value_Year_1', 'Value_Year_2']:
            if col in mapped_df.columns:
                mapped_fields += mapped_df[col].notna().sum()
        
        print(f"  ✅ Mapped {mapped_fields} field values")
        
        # Save results
        print(f"\n💾 Saving results...")
        mapped_df.to_csv(output_csv_path, index=False)
        
        # Save raw JSON
        with open(output_json_path, 'w') as f:
            json.dump(final_extracted_data, f, indent=2)
        
        print(f"  ✅ CSV saved: {output_csv_path}")
        print(f"  ✅ JSON saved: {output_json_path}")
        
        # Summary
        print(f"\n📊 EXTRACTION SUMMARY:")
        print(f"  📄 Pages processed: {len(all_extracted_page_data)}")
        print(f"  🎯 Statement type: {final_extracted_data.get('statement_type', 'Unknown')}")
        print(f"  📅 Years detected: {final_extracted_data.get('years_detected', [])}")
        print(f"  🔢 Fields mapped: {mapped_fields}")
        print(f"  ⏱️ Processing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ EXTRACTION FAILED: {e}")
        return False

def map_to_template(extracted_data, template_df):
    """Map extracted data to template format"""
    mapped_df = template_df.copy()
    
    # Update years in Meta/Reference section
    years_detected = extracted_data.get("years_detected", [])
    if years_detected:
        year_1 = years_detected[0] if len(years_detected) > 0 else ""
        year_2 = years_detected[1] if len(years_detected) > 1 else ""
        
        # Update Year columns in Meta/Reference
        meta_mask = mapped_df['Category'] == 'Meta/Reference'
        if 'Value_Year_1' in mapped_df.columns:
            mapped_df.loc[meta_mask & (mapped_df['Field'] == 'Year'), 'Value_Year_1'] = year_1
        if 'Value_Year_2' in mapped_df.columns:
            mapped_df.loc[meta_mask & (mapped_df['Field'] == 'Year'), 'Value_Year_2'] = year_2
    
    # Map line items to template fields
    line_items = extracted_data.get("line_items", {})
    
    for category_key, items in line_items.items():
        for item_key, item_data in items.items():
            if not isinstance(item_data, dict):
                continue
                
            # Determine template field based on item_key
            template_field = None
            
            # Cash and cash equivalents
            if any(keyword in item_key.lower() for keyword in ['cash', 'equivalents']):
                template_field = 'Cash and cash equivalents'
            elif any(keyword in item_key.lower() for keyword in ['receivables', 'trade']):
                template_field = 'Trade and other receivables'
            elif any(keyword in item_key.lower() for keyword in ['inventory', 'stock']):
                template_field = 'Inventories'
            elif any(keyword in item_key.lower() for keyword in ['prepaid', 'advance']):
                template_field = 'Prepaid expenses and other current assets'
            elif any(keyword in item_key.lower() for keyword in ['current assets', 'total current']):
                template_field = 'Total current assets'
            elif any(keyword in item_key.lower() for keyword in ['property', 'plant', 'equipment', 'ppe']):
                template_field = 'Property, plant and equipment'
            elif any(keyword in item_key.lower() for keyword in ['intangible', 'goodwill']):
                template_field = 'Intangible assets'
            elif any(keyword in item_key.lower() for keyword in ['total assets']):
                template_field = 'Total assets'
            elif any(keyword in item_key.lower() for keyword in ['payables', 'trade payable']):
                template_field = 'Trade and other payables'
            elif any(keyword in item_key.lower() for keyword in ['borrowings', 'debt']):
                template_field = 'Borrowings'
            elif any(keyword in item_key.lower() for keyword in ['current liabilities', 'total current']):
                template_field = 'Total current liabilities'
            elif any(keyword in item_key.lower() for keyword in ['non-current', 'long-term']):
                template_field = 'Non-current liabilities'
            elif any(keyword in item_key.lower() for keyword in ['equity', 'share capital']):
                template_field = 'Share capital'
            elif any(keyword in item_key.lower() for keyword in ['retained', 'earnings']):
                template_field = 'Retained earnings'
            elif any(keyword in item_key.lower() for keyword in ['total equity']):
                template_field = 'Total equity'
            
            if template_field:
                # Find the row in template
                row_index = mapped_df[(mapped_df['Field'] == template_field)].index
                if not row_index.empty:
                    row_idx = row_index[0]
                    
                    # Update confidence
                    mapped_df.loc[row_idx, 'Confidence'] = 'High'
                    mapped_df.loc[row_idx, 'Confidence_Score'] = 0.95
                    
                    # Update values
                    values = item_data.get('values', {})
                    if 'Value_Year_1' in mapped_df.columns and 'year_1' in values:
                        mapped_df.loc[row_idx, 'Value_Year_1'] = values['year_1']
                    if 'Value_Year_2' in mapped_df.columns and 'year_2' in values:
                        mapped_df.loc[row_idx, 'Value_Year_2'] = values['year_2']
    
    return mapped_df

if __name__ == "__main__":
    success = extract_and_save_robust()
    if success:
        print("\n🎉 AFS2024.pdf (ORIGIN) extraction completed successfully!")
    else:
        print("\n💥 AFS2024.pdf (ORIGIN) extraction failed!")
        sys.exit(1)
