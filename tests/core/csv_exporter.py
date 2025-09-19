"""
Core CSV Export Functionality for Financial Data

This module provides centralized CSV export functionality for all test scenarios
and API functionality. It handles template-compliant CSV generation, multiple
output formats, and comprehensive field mapping.
"""

import os
import csv
import json
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSVExporter:
    """Centralized CSV export functionality for financial data"""
    
    def __init__(self, template_path: str = "tests/fixtures/templates/FS_Input_Template_Fields.csv"):
        """Initialize with template path"""
        self.template_path = template_path
        self.template_data = self._load_template()
        self.field_mappings = self._create_field_mappings()
        
        # Template header structure
        self.template_header = [
            'Category', 'Subcategory', 'Field', 'Confidence', 'Confidence_Score',
            'Value_Year_1', 'Value_Year_2', 'Value_Year_3', 'Value_Year_4'
        ]
    
    def _load_template(self) -> List[Dict[str, str]]:
        """Load the template CSV structure"""
        try:
            template_path = Path(self.template_path)
            if not template_path.exists():
                logger.warning(f"Template file not found: {template_path}")
                return []
            
            template_data = []
            with open(template_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    template_data.append(row)
            
            logger.info(f"Loaded {len(template_data)} template fields")
            return template_data
            
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            return []
    
    def _create_field_mappings(self) -> Dict[str, str]:
        """Create field mappings from extracted data to template fields"""
        mappings = {
            # Meta fields
            'company_name': 'Company',
            'period': 'Period',
            'currency': 'Currency',
            'years_detected': 'Years',
            
            # Balance Sheet - Current Assets
            'cash': 'Cash and Cash Equivalents',
            'cash_and_equivalents': 'Cash and Cash Equivalents',
            'receivables': 'Trade and Other Current Receivables',
            'trade_receivables': 'Trade and Other Current Receivables',
            'inventories': 'Inventories',
            'prepaid_expenses': 'Prepaid Expenses',
            'other_current_assets': 'Other Current Assets',
            
            # Balance Sheet - Non-Current Assets
            'property_plant_equipment': 'Property, Plant and Equipment',
            'ppe': 'Property, Plant and Equipment',
            'intangible_assets': 'Intangible Assets',
            'goodwill': 'Goodwill',
            'other_non_current_assets': 'Other Non-Current Assets',
            
            # Balance Sheet - Current Liabilities
            'trade_payables': 'Trade and Other Current Payables',
            'accounts_payable': 'Trade and Other Current Payables',
            'short_term_debt': 'Short-term Debt',
            'current_portion_long_term_debt': 'Current Portion of Long-term Debt',
            'other_current_liabilities': 'Other Current Liabilities',
            
            # Balance Sheet - Non-Current Liabilities
            'long_term_debt': 'Long-term Debt',
            'other_non_current_liabilities': 'Other Non-Current Liabilities',
            
            # Balance Sheet - Equity
            'share_capital': 'Share Capital',
            'retained_earnings': 'Retained Earnings',
            'other_equity': 'Other Equity',
            
            # Income Statement
            'revenue': 'Revenue',
            'sales': 'Revenue',
            'cost_of_sales': 'Cost of Sales',
            'gross_profit': 'Gross Profit',
            'operating_expenses': 'Operating Expenses',
            'operating_profit': 'Operating Profit',
            'finance_costs': 'Finance Costs',
            'profit_before_tax': 'Profit Before Tax',
            'income_tax': 'Income Tax',
            'profit_after_tax': 'Profit After Tax',
            
            # Cash Flow
            'operating_cash_flow': 'Operating Cash Flow',
            'investing_cash_flow': 'Investing Cash Flow',
            'financing_cash_flow': 'Financing Cash Flow',
            'net_cash_flow': 'Net Cash Flow'
        }
        
        return mappings
    
    def _map_extracted_data_to_template(self, extracted_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Map extracted financial data to template structure"""
        mapped_data = []
        
        # Get years from extracted data
        years = extracted_data.get('years_detected', [])
        if not years:
            years = ['2024', '2023']  # Default fallback
        
        # Sort years (most recent first)
        years = sorted(years, reverse=True)
        
        # Add meta information
        meta_fields = [
            {
                'Category': 'Meta',
                'Subcategory': 'Reference',
                'Field': 'Company',
                'Confidence': 'High',
                'Confidence_Score': '0.95',
                'Value_Year_1': extracted_data.get('company_name', ''),
                'Value_Year_2': '',
                'Value_Year_3': '',
                'Value_Year_4': ''
            },
            {
                'Category': 'Meta',
                'Subcategory': 'Reference',
                'Field': 'Period',
                'Confidence': 'High',
                'Confidence_Score': '0.95',
                'Value_Year_1': extracted_data.get('period', ''),
                'Value_Year_2': '',
                'Value_Year_3': '',
                'Value_Year_4': ''
            },
            {
                'Category': 'Meta',
                'Subcategory': 'Reference',
                'Field': 'Currency',
                'Confidence': 'High',
                'Confidence_Score': '0.95',
                'Value_Year_1': extracted_data.get('currency', ''),
                'Value_Year_2': '',
                'Value_Year_3': '',
                'Value_Year_4': ''
            }
        ]
        mapped_data.extend(meta_fields)
        
        # Map line items
        line_items = extracted_data.get('line_items', {})
        for category, items in line_items.items():
            if isinstance(items, dict):
                for item_name, item_data in items.items():
                    if isinstance(item_data, dict) and 'value' in item_data:
                        # Map to template field name
                        template_field = self.field_mappings.get(item_name, item_name.title())
                        
                        # Determine category and subcategory
                        if 'current_assets' in category.lower():
                            cat = 'Balance Sheet'
                            subcat = 'Current Assets'
                        elif 'non_current_assets' in category.lower() or 'fixed_assets' in category.lower():
                            cat = 'Balance Sheet'
                            subcat = 'Non-Current Assets'
                        elif 'current_liabilities' in category.lower():
                            cat = 'Balance Sheet'
                            subcat = 'Current Liabilities'
                        elif 'non_current_liabilities' in category.lower():
                            cat = 'Balance Sheet'
                            subcat = 'Non-Current Liabilities'
                        elif 'equity' in category.lower():
                            cat = 'Balance Sheet'
                            subcat = 'Equity'
                        elif 'revenue' in category.lower() or 'income' in category.lower():
                            cat = 'Income Statement'
                            subcat = 'Revenue'
                        elif 'expense' in category.lower() or 'cost' in category.lower():
                            cat = 'Income Statement'
                            subcat = 'Expenses'
                        elif 'cash_flow' in category.lower():
                            cat = 'Cash Flow Statement'
                            subcat = 'Operating Activities'
                        else:
                            cat = 'Balance Sheet'
                            subcat = 'Other'
                        
                        # Extract values for each year
                        values = ['', '', '', '']
                        confidence = item_data.get('confidence', 0.95)
                        confidence_score = f"{confidence:.2f}"
                        
                        # Map year values
                        if 'base_year' in item_data:
                            values[0] = str(item_data['base_year'])
                        if 'year_1' in item_data:
                            values[1] = str(item_data['year_1'])
                        if 'year_2' in item_data:
                            values[2] = str(item_data['year_2'])
                        if 'year_3' in item_data:
                            values[3] = str(item_data['year_3'])
                        
                        # Also check for year-specific keys
                        for i, year in enumerate(years[:4]):
                            if f'year_{year}' in item_data:
                                values[i] = str(item_data[f'year_{year}'])
                            elif year in item_data:
                                values[i] = str(item_data[year])
                        
                        mapped_data.append({
                            'Category': cat,
                            'Subcategory': subcat,
                            'Field': template_field,
                            'Confidence': 'High' if confidence >= 0.8 else 'Medium',
                            'Confidence_Score': confidence_score,
                            'Value_Year_1': values[0],
                            'Value_Year_2': values[1],
                            'Value_Year_3': values[2],
                            'Value_Year_4': values[3]
                        })
        
        return mapped_data
    
    def export_to_template_csv(self, extracted_data: Dict[str, Any], output_path: str) -> bool:
        """
        Export extracted financial data to template CSV format
        
        Args:
            extracted_data: Financial data extracted from API
            output_path: Path to save the CSV file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Map data to template structure
            mapped_data = self._map_extracted_data_to_template(extracted_data)
            
            # Write to CSV
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.template_header)
                writer.writeheader()
                writer.writerows(mapped_data)
            
            logger.info(f"Template CSV exported to: {output_path}")
            logger.info(f"Exported {len(mapped_data)} fields")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting template CSV: {e}")
            return False
    
    def export_to_summary_csv(self, test_results: List[Dict[str, Any]], output_path: str) -> bool:
        """
        Export test results to summary CSV format
        
        Args:
            test_results: List of test result dictionaries
            output_path: Path to save the summary CSV
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Summary CSV header
            summary_header = [
                'File', 'Company', 'Statement Type', 'Years', 'Processing Time (s)',
                'Pages Processed', 'Line Items Count', 'Total Assets', 'Total Liabilities',
                'Total Equity', 'Success', 'Status Code', 'Error Message'
            ]
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(summary_header)
                
                for result in test_results:
                    response_data = result.get('response_data', {}) or {}
                    data_content = response_data.get('data', {}) or {}
                    
                    # Extract key information
                    filename = result.get('filename', 'Unknown')
                    company = data_content.get('company_name', 'N/A')
                    statement_type = data_content.get('statement_type', 'N/A')
                    years = ', '.join(data_content.get('years_detected', []))
                    processing_time = result.get('processing_time', 0)
                    pages_processed = response_data.get('pages_processed', 'N/A')
                    line_items_count = data_content.get('document_structure', {}).get('line_item_count', 'N/A')
                    
                    # Extract summary metrics
                    summary = data_content.get('summary_metrics', {})
                    total_assets = summary.get('total_assets', {}).get('value', 'N/A')
                    total_liabilities = summary.get('total_liabilities', {}).get('value', 'N/A')
                    total_equity = summary.get('total_equity', {}).get('value', 'N/A')
                    
                    success = result.get('success', False)
                    status_code = result.get('status_code', 'N/A')
                    error_message = result.get('error', 'N/A')
                    
                    writer.writerow([
                        filename, company, statement_type, years, f"{processing_time:.1f}",
                        pages_processed, line_items_count, total_assets, total_liabilities,
                        total_equity, success, status_code, error_message
                    ])
            
            logger.info(f"Summary CSV exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting summary CSV: {e}")
            return False
    
    def validate_template_compliance(self, csv_path: str) -> Dict[str, Any]:
        """
        Validate CSV against template format
        
        Args:
            csv_path: Path to CSV file to validate
            
        Returns:
            Dict with validation results
        """
        try:
            csv_path = Path(csv_path)
            if not csv_path.exists():
                return {'valid': False, 'error': 'File not found'}
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Check header compliance
            expected_header = set(self.template_header)
            actual_header = set(reader.fieldnames) if reader.fieldnames else set()
            
            header_compliance = expected_header == actual_header
            
            # Count non-empty fields
            non_empty_fields = 0
            for row in rows:
                for field in ['Value_Year_1', 'Value_Year_2', 'Value_Year_3', 'Value_Year_4']:
                    if row.get(field, '').strip():
                        non_empty_fields += 1
            
            return {
                'valid': header_compliance,
                'header_compliance': header_compliance,
                'total_rows': len(rows),
                'non_empty_fields': non_empty_fields,
                'expected_header': list(expected_header),
                'actual_header': list(actual_header)
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}


def main():
    """Test the CSV exporter functionality"""
    print("🧪 Testing CSV Exporter...")
    
    # Initialize exporter
    exporter = CSVExporter()
    
    # Test with sample data
    sample_data = {
        'company_name': 'Test Company',
        'period': 'December 31, 2024',
        'currency': 'USD',
        'years_detected': ['2024', '2023'],
        'line_items': {
            'current_assets': {
                'cash': {
                    'value': 1000000,
                    'confidence': 0.95,
                    'base_year': 1000000,
                    'year_1': 950000
                }
            }
        }
    }
    
    # Test template CSV export
    test_output = "tests/results/test_template_export.csv"
    success = exporter.export_to_template_csv(sample_data, test_output)
    
    if success:
        print(f"✅ Template CSV export successful: {test_output}")
        
        # Validate the output
        validation = exporter.validate_template_compliance(test_output)
        print(f"📊 Validation results: {validation}")
    else:
        print("❌ Template CSV export failed")
    
    print("🎉 CSV Exporter test completed!")


if __name__ == "__main__":
    main()
