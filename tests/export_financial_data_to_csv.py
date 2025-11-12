"""
Export detailed financial data from API JSON responses to template CSV format.
This creates the actual financial data CSV that matches the template structure.
"""

import json
import csv
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.csv_exporter import CSVExporter


def convert_json_to_template_csv_core(json_file_path: str, output_csv_path: str = None) -> str:
    """
    Convert API JSON response to template CSV format using core CSV exporter.
    
    Args:
        json_file_path: Path to the JSON test report file
        output_csv_path: Optional output CSV path (defaults to same directory as JSON)
    
    Returns:
        Path to the created CSV file
    """
    # Load the JSON data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Determine output path
    if output_csv_path is None:
        json_path = Path(json_file_path)
        output_csv_path = json_path.parent / f"{json_path.stem}_template_format.csv"
    
    # Extract the financial data from the API response
    extracted_data = data.get('data', {})
    
    if not extracted_data:
        print("❌ No financial data found in JSON response")
        return None
    
    # Use core CSV exporter
    csv_exporter = CSVExporter()
    success = csv_exporter.export_to_template_csv(extracted_data, str(output_csv_path))
    
    if success:
        print(f"✅ Template CSV created: {output_csv_path}")
        return str(output_csv_path)
    else:
        print("❌ Failed to create template CSV")
        return None


def convert_json_to_template_csv(json_file_path: str, output_csv_path: str = None) -> str:
    """
    Convert API JSON response to template CSV format.
    
    Args:
        json_file_path: Path to the JSON test report file
        output_csv_path: Optional output CSV path (defaults to same directory as JSON)
    
    Returns:
        Path to the created CSV file
    """
    # Load the JSON data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Determine output path
    if output_csv_path is None:
        json_path = Path(json_file_path)
        output_csv_path = json_path.parent / f"{json_path.stem}_financial_data.csv"
    
    # Process each test result
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header (template format)
        writer.writerow([
            'Category', 'Subcategory', 'Field', 'Confidence', 'Confidence_Score',
            'Value_Year_1', 'Value_Year_2', 'Value_Year_3', 'Value_Year_4'
        ])
        
        for result in data.get('results', []):
            if not result.get('success', False):
                continue
                
            response_data = result.get('response_data', {})
            if not response_data:
                continue
                
            financial_data = response_data.get('data', {})
            if not financial_data:
                continue
            
            # Extract metadata
            company_name = financial_data.get('company_name', 'Unknown')
            statement_type = financial_data.get('statement_type', 'Unknown')
            years_detected = financial_data.get('years_detected', [])
            base_year = financial_data.get('base_year', '')
            
            # Write metadata row
            writer.writerow([
                'Meta', 'Reference', 'Year', '', '',
                years_detected[0] if len(years_detected) > 0 else '',
                years_detected[1] if len(years_detected) > 1 else '',
                years_detected[2] if len(years_detected) > 2 else '',
                years_detected[3] if len(years_detected) > 3 else ''
            ])
            
            # Process line items
            line_items = financial_data.get('line_items', {})
            print(f"DEBUG: Found {len(line_items)} line item categories")
            
            # Process each category
            for category_name, category_data in line_items.items():
                if not isinstance(category_data, dict):
                    continue
                
                # Process each field (the structure is category -> field, not category -> subcategory -> field)
                for field_name, field_data in category_data.items():
                    if not isinstance(field_data, dict):
                        continue
                    
                    # Extract values
                    confidence = field_data.get('confidence', 0)
                    confidence_score = confidence
                    confidence_pct = f"{confidence * 100:.2f}%" if confidence > 0 else ""
                    
                    # Extract year values
                    value_year_1 = field_data.get('base_year', '')
                    value_year_2 = field_data.get('year_1', '')
                    value_year_3 = field_data.get('year_2', '')
                    value_year_4 = field_data.get('year_3', '')
                    
                    # Convert category names to match template
                    category_mapped = map_category_name(category_name)
                    subcategory_mapped = map_subcategory_name(category_name)  # Use category as subcategory
                    field_mapped = map_field_name(field_name)
                    
                    # Write row
                    writer.writerow([
                        category_mapped,
                        subcategory_mapped,
                        field_mapped,
                        confidence_pct,
                        confidence_score,
                        value_year_1,
                        value_year_2,
                        value_year_3,
                        value_year_4
                    ])
    
    return str(output_csv_path)


def map_category_name(category: str) -> str:
    """Map API category names to template category names"""
    mapping = {
        'current_assets': 'Balance Sheet',
        'non_current_assets': 'Balance Sheet',
        'total_assets': 'Balance Sheet',
        'current_liabilities': 'Balance Sheet',
        'non_current_liabilities': 'Balance Sheet',
        'total_liabilities': 'Balance Sheet',
        'equity': 'Balance Sheet',
        'total_liabilities_and_equity_deficit': 'Balance Sheet',
        'revenues': 'Income Statement',
        'cost_of_sales': 'Income Statement',
        'operating_expenses': 'Income Statement',
        'operating_activities': 'Cash Flow Statement',
        'investing_activities': 'Cash Flow Statement',
        'financing_activities': 'Cash Flow Statement'
    }
    return mapping.get(category, 'Balance Sheet')


def map_subcategory_name(subcategory: str) -> str:
    """Map API subcategory names to template subcategory names"""
    mapping = {
        'current_assets': 'Current Assets',
        'non_current_assets': 'Non Current Assets',
        'totals': 'Totals',
        'current_liabilities': 'Current Liabilities',
        'non_current_liabilities': 'Non Current Liabilities',
        'equity': 'Equity',
        'revenues': 'Revenue',
        'cost_of_sales': 'Revenue',
        'operating_expenses': 'Revenue',
        'operating_activities': 'Operating Activities',
        'investing_activities': 'Investing Activities',
        'financing_activities': 'Financing Activities'
    }
    return mapping.get(subcategory, 'Current Assets')


def map_field_name(field: str) -> str:
    """Map API field names to template field names"""
    mapping = {
        'cash': 'Cash and Cash Equivalents',
        'receivables': 'Trade and Other Current Receivables',
        'other_current_assets': 'Other current non-financial assets',
        'total_current_assets': 'Total Current Assets',
        'investment_in_non_proprietary_shares': 'Other non-current financial assets',
        'property_and_equipment': 'Property, Plant and Equipment',
        'other_non_current_assets': 'Other non-current non-financial assets',
        'total_non_current_assets': 'Total Non Current Assets',
        'total_assets': 'Total Assets',
        'trade_payables': 'Trade and other current payables',
        'income_tax_payable': 'Current tax liabilities, current',
        'loans_payable_current_portion': 'Other current financial liabilities',
        'other_current_liabilities': 'Other current non-financial liabilities',
        'total_current_liabilities': 'Total Current Liabilities',
        'advances_from_stockholder': 'Trade and other non-current payables',
        'long_term_liabilities': 'Other long-term financial liabilities',
        'other_long_term_liabilities': 'Other non-current non-financial liabilities',
        'total_non_current_liabilities': 'Total Non Current Liabilities',
        'total_liabilities': 'Total Liabilities And Equity',
        'share_capital': 'Issued (share) capital',
        'additional_paid_in_capital': 'Share premium',
        'cumulative_earnings_appropriated': 'Other reserves',
        'cumulative_earnings_deficit': 'Retained earnings',
        'gain_loss_on_fair_value_of_asset_held_for_sale': 'Other equity interest',
        'treasury_shares': 'Treasury shares',
        'total_equity_deficit': 'Total Equity',
        'total_liabilities_and_equity_deficit': 'Total Liabilities And Equity'
    }
    return mapping.get(field, field.replace('_', ' ').title())


def main():
    """Command line interface"""
    if len(sys.argv) < 2:
        print("Usage: python export_financial_data_to_csv.py <json_file> [output_csv]")
        print("Example: python export_financial_data_to_csv.py tests/results/enhanced_test_report_1757432682.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        csv_path = convert_json_to_template_csv(json_file, output_csv)
        print(f"✅ Financial data exported to: {csv_path}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
