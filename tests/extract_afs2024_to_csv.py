"""
Extract AFS2024 document to CSV format

This script will process the AFS2024 document and generate a CSV file
with the extracted financial data.
"""

import os
import sys
import json
import csv
import time
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.extractor import FinancialDataExtractor
from core.pdf_processor import PDFProcessor


def extract_financial_data_to_csv(pdf_path: str, output_csv_path: str):
    """Extract financial data from PDF and save to CSV"""
    print(f"🔍 Processing: {pdf_path}")
    print(f"📄 Output: {output_csv_path}")
    print("=" * 60)
    
    try:
        # Initialize components
        print("🔧 Initializing components...")
        extractor = FinancialDataExtractor()
        processor = PDFProcessor(extractor)
        print("✅ Components initialized")
        
        # Load PDF
        print(f"📄 Loading PDF: {Path(pdf_path).name}")
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        print(f"✅ PDF loaded: {len(pdf_data)} bytes")
        
        # Process PDF
        print("🔄 Processing PDF...")
        start_time = time.time()
        
        extracted_data = processor.process_pdf_with_vector_db(pdf_data)
        
        processing_time = time.time() - start_time
        print(f"✅ Processing completed: {processing_time:.2f}s")
        
        if not extracted_data:
            print("❌ No data extracted")
            return False
        
        # Convert to CSV format
        print("📊 Converting to CSV format...")
        csv_data = convert_to_csv_format(extracted_data)
        
        # Save CSV
        print(f"💾 Saving CSV: {output_csv_path}")
        save_csv(csv_data, output_csv_path)
        
        print("🎉 Successfully generated CSV!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def convert_to_csv_format(extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert extracted data to CSV format"""
    csv_rows = []
    
    # Extract basic info
    statement_type = extracted_data.get('statement_type', 'Unknown')
    company_name = extracted_data.get('company_name', 'Unknown')
    period = extracted_data.get('period', 'Unknown')
    currency = extracted_data.get('currency', 'Unknown')
    years_detected = extracted_data.get('years_detected', [])
    
    # Add header row
    csv_rows.append({
        'Field': 'Document Information',
        'Value': '',
        'Year': '',
        'Category': 'Header'
    })
    csv_rows.append({
        'Field': 'Statement Type',
        'Value': statement_type,
        'Year': '',
        'Category': 'Header'
    })
    csv_rows.append({
        'Field': 'Company Name',
        'Value': company_name,
        'Year': '',
        'Category': 'Header'
    })
    csv_rows.append({
        'Field': 'Period',
        'Value': period,
        'Year': '',
        'Category': 'Header'
    })
    csv_rows.append({
        'Field': 'Currency',
        'Value': currency,
        'Year': '',
        'Category': 'Header'
    })
    csv_rows.append({
        'Field': 'Years Detected',
        'Value': ', '.join(years_detected),
        'Year': '',
        'Category': 'Header'
    })
    
    # Add separator
    csv_rows.append({
        'Field': '',
        'Value': '',
        'Year': '',
        'Category': 'Separator'
    })
    
    # Extract line items
    line_items = extracted_data.get('line_items', {})
    
    for category, items in line_items.items():
        if not isinstance(items, dict):
            continue
            
        # Add category header
        csv_rows.append({
            'Field': category.replace('_', ' ').title(),
            'Value': '',
            'Year': '',
            'Category': 'Category'
        })
        
        # Add items in this category
        for item_name, item_data in items.items():
            if not isinstance(item_data, dict):
                continue
                
            field_name = item_name.replace('_', ' ').title()
            
            # Get values for each year
            base_year_value = item_data.get('base_year', '')
            year_1_value = item_data.get('year_1', '')
            confidence = item_data.get('confidence', '')
            
            # Add base year row
            if base_year_value != '':
                csv_rows.append({
                    'Field': field_name,
                    'Value': base_year_value,
                    'Year': years_detected[0] if len(years_detected) > 0 else 'Base Year',
                    'Category': category
                })
            
            # Add year 1 row if different from base year
            if year_1_value != '' and year_1_value != base_year_value:
                csv_rows.append({
                    'Field': field_name,
                    'Value': year_1_value,
                    'Year': years_detected[1] if len(years_detected) > 1 else 'Year 1',
                    'Category': category
                })
    
    return csv_rows


def save_csv(csv_data: List[Dict[str, Any]], output_path: str):
    """Save CSV data to file"""
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Field', 'Value', 'Year', 'Category']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in csv_data:
            writer.writerow(row)


def main():
    """Main function"""
    # Input and output paths
    pdf_path = "tests/fixtures/light/AFS2024 - statement extracted.pdf"
    output_csv_path = "tests/outputs/AFS2024_extracted_data.csv"
    
    # Create output directory if it doesn't exist
    Path(output_csv_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Extract data
    success = extract_financial_data_to_csv(pdf_path, output_csv_path)
    
    if success:
        print(f"\n🎉 CSV file generated successfully!")
        print(f"📁 Location: {output_csv_path}")
        
        # Show file size
        file_size = Path(output_csv_path).stat().st_size
        print(f"📊 File size: {file_size} bytes")
        
        # Show first few rows
        print(f"\n📋 Preview of CSV content:")
        print("-" * 60)
        with open(output_csv_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i < 10:  # Show first 10 lines
                    print(line.strip())
                else:
                    print("...")
                    break
    else:
        print("\n❌ Failed to generate CSV file")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
