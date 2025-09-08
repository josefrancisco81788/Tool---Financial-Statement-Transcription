"""
Extract AFS2024 document to standardized template CSV format

This script will process the AFS2024 document and generate a CSV file
that matches the exact format of FS_Input_Template_Fields.csv
"""

import os
import sys
import json
import csv
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.extractor import FinancialDataExtractor
from core.pdf_processor import PDFProcessor


def extract_financial_data_to_template_csv(pdf_path: str, output_csv_path: str):
    """Extract financial data from PDF and save to template CSV format"""
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
        
        # Load template
        print("📋 Loading template format...")
        template_path = "tests/fixtures/templates/FS_Input_Template_Fields.csv"
        template_data = load_template(template_path)
        print(f"✅ Template loaded: {len(template_data)} fields")
        
        # Map extracted data to template
        print("🔄 Mapping data to template format...")
        mapped_data = map_data_to_template(extracted_data, template_data)
        
        # Save CSV
        print(f"💾 Saving template CSV: {output_csv_path}")
        save_template_csv(mapped_data, output_csv_path)
        
        print("🎉 Successfully generated template CSV!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_template(template_path: str) -> List[Dict[str, str]]:
    """Load the template CSV format"""
    template_data = []
    with open(template_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            template_data.append(row)
    return template_data


def map_data_to_template(extracted_data: Dict[str, Any], template_data: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Map extracted data to template format"""
    mapped_data = []
    
    # Get years from extracted data
    years_detected = extracted_data.get('years_detected', [])
    year_1 = years_detected[0] if len(years_detected) > 0 else ""
    year_2 = years_detected[1] if len(years_detected) > 1 else ""
    
    # Create field mapping
    field_mapping = create_field_mapping(extracted_data)
    
    for template_row in template_data:
        # Create a copy of the template row
        mapped_row = template_row.copy()
        
        # Set the year in the first row (Meta/Reference/Year)
        if template_row['Category'] == 'Meta' and template_row['Field'] == 'Year':
            mapped_row['Value_Year_1'] = year_1
            mapped_row['Value_Year_2'] = year_2
            mapped_row['Confidence'] = 'High'
            mapped_row['Confidence_Score'] = '0.95'
        else:
            # Try to find matching data
            field_key = f"{template_row['Category']}|{template_row['Subcategory']}|{template_row['Field']}"
            
            if field_key in field_mapping:
                field_data = field_mapping[field_key]
                mapped_row['Value_Year_1'] = str(field_data.get('year_1', ''))
                mapped_row['Value_Year_2'] = str(field_data.get('year_2', ''))
                mapped_row['Confidence'] = 'High' if field_data.get('confidence', 0) > 0.8 else 'Medium'
                mapped_row['Confidence_Score'] = str(field_data.get('confidence', 0))
            else:
                # No data found, keep empty
                mapped_row['Value_Year_1'] = ''
                mapped_row['Value_Year_2'] = ''
                mapped_row['Confidence'] = ''
                mapped_row['Confidence_Score'] = ''
        
        mapped_data.append(mapped_row)
    
    return mapped_data


def create_field_mapping(extracted_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Create mapping from template fields to extracted data"""
    mapping = {}
    
    line_items = extracted_data.get('line_items', {})
    years_detected = extracted_data.get('years_detected', [])
    
    # Define field mappings
    field_mappings = {
        # Current Assets
        'Balance Sheet|Current Assets|Cash and Cash Equivalents': 'cash',
        'Balance Sheet|Current Assets|Trade and Other Current Receivables': 'receivables',
        'Balance Sheet|Current Assets|Other current non-financial assets': 'other_current_assets',
        'Balance Sheet|Current Assets|Total Current Assets': 'total_current_assets',
        
        # Non-Current Assets
        'Balance Sheet|Non Current Assets|Property, Plant and Equipment': 'property_equipment',
        'Balance Sheet|Non Current Assets|Investments in subsidiaries, joint ventures and associates': 'investment_in_non_proprietary_shares',
        'Balance Sheet|Non Current Assets|Other non-current non-financial assets': 'other_non_current_assets',
        'Balance Sheet|Non Current Assets|Total Non Current Assets': 'total_non_current_assets',
        
        # Totals
        'Balance Sheet|Totals|Total Assets': 'total_assets',
        'Balance Sheet|Totals|Total Liabilities And Equity': 'total_liabilities_and_equity_deficit',
        
        # Current Liabilities
        'Balance Sheet|Current Liabilities|Trade and other current payables': 'trade_payables',
        'Balance Sheet|Current Liabilities|Current tax liabilities, current': 'income_tax_payable',
        'Balance Sheet|Current Liabilities|Other current financial liabilities': 'loans_payable_current_portion',
        'Balance Sheet|Current Liabilities|Other current non-financial liabilities': 'other_current_liabilities',
        'Balance Sheet|Current Liabilities|Total Current Liabilities': 'total_current_liabilities',
        
        # Non-Current Liabilities
        'Balance Sheet|Non Current Liabilities|Other long-term financial liabilities': 'advances_from_stockholder',
        'Balance Sheet|Non Current Liabilities|Other non-current non-financial liabilities': 'other_long_term_liabilities',
        'Balance Sheet|Non Current Liabilities|Total Non Current Liabilities': 'total_non_current_liabilities',
        
        # Equity
        'Balance Sheet|Equity|Issued (share) capital': 'share_capital',
        'Balance Sheet|Equity|Share premium': 'additional_paid_in_capital',
        'Balance Sheet|Equity|Treasury shares': 'treasury_shares',
        'Balance Sheet|Equity|Retained earnings': 'cumulative_earnings_appropriated',
        'Balance Sheet|Equity|Other reserves': 'cumulative_earnings_deficit',
        'Balance Sheet|Equity|Total Equity': 'total_equity_deficit',
    }
    
    # Map the data
    for template_key, extracted_key in field_mappings.items():
        # Find the data in line_items
        for category, items in line_items.items():
            if extracted_key in items:
                item_data = items[extracted_key]
                if isinstance(item_data, dict):
                    mapping[template_key] = {
                        'year_1': item_data.get('base_year', ''),
                        'year_2': item_data.get('year_1', ''),
                        'confidence': item_data.get('confidence', 0)
                    }
                break
    
    return mapping


def save_template_csv(mapped_data: List[Dict[str, str]], output_path: str):
    """Save mapped data to CSV in template format"""
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Category', 'Subcategory', 'Field', 'Confidence', 'Confidence_Score', 
                     'Value_Year_1', 'Value_Year_2', 'Value_Year_3', 'Value_Year_4']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in mapped_data:
            writer.writerow(row)


def main():
    """Main function"""
    # Input and output paths
    pdf_path = "tests/fixtures/light/AFS2024 - statement extracted.pdf"
    output_csv_path = "tests/outputs/AFS2024_template_format.csv"
    
    # Create output directory if it doesn't exist
    Path(output_csv_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Extract data
    success = extract_financial_data_to_template_csv(pdf_path, output_csv_path)
    
    if success:
        print(f"\n🎉 Template CSV file generated successfully!")
        print(f"📁 Location: {output_csv_path}")
        
        # Show file size
        file_size = Path(output_csv_path).stat().st_size
        print(f"📊 File size: {file_size} bytes")
        
        # Show first few rows
        print(f"\n📋 Preview of template CSV content:")
        print("-" * 80)
        with open(output_csv_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i < 15:  # Show first 15 lines
                    print(line.strip())
                else:
                    print("...")
                    break
    else:
        print("\n❌ Failed to generate template CSV file")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
