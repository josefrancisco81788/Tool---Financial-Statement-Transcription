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
from difflib import SequenceMatcher
import re

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
        self.comprehensive_mappings = self._create_comprehensive_mappings()
        
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
    
    def _create_comprehensive_mappings(self) -> Dict[str, List[str]]:
        """Create comprehensive field mappings with extensive variations"""
        return {
            # Balance Sheet - Current Assets
            "Cash and Cash Equivalents": [
                "cash", "cash equivalents", "cash and equivalents", "liquid assets",
                "cash at bank", "cash in hand", "available funds", "short term deposits",
                "cash & short-term investments", "cash and near cash", "cash at bank and in hand",
                "cash and cash equivalents", "cash & cash equivalents", "liquid funds",
                "cash and short-term deposits", "cash and bank balances", "cash and equivalents"
            ],
            "Trade and Other Current Receivables": [
                "receivables", "accounts receivable", "trade receivables", "trade and other receivables",
                "current receivables", "other receivables", "trade debtors", "accounts receivable net",
                "trade and other current receivables", "receivables net", "trade receivables net",
                "other current receivables", "trade and other receivables net"
            ],
            "Current Inventories": [
                "inventory", "inventories", "stock", "current inventories", "inventory at cost",
                "inventories at cost", "stock in trade", "merchandise inventory", "raw materials",
                "work in progress", "finished goods", "inventory net", "inventories net"
            ],
            "Property, Plant and Equipment": [
                "ppe", "property plant and equipment", "property plant equipment", "fixed assets",
                "plant and equipment", "property and equipment", "tangible fixed assets",
                "property plant & equipment", "fixed assets net", "ppe net", "property equipment",
                "plant equipment", "tangible assets", "fixed assets at cost"
            ],
            "Total Current Assets": [
                "total current assets", "current assets total", "total current assets net",
                "current assets", "total current assets at cost", "current assets sum"
            ],
            "Total Assets": [
                "total assets", "assets total", "total assets net", "total assets at cost",
                "assets", "total assets sum", "total assets before depreciation"
            ],
            
            # Balance Sheet - Liabilities
            "Trade and Other Current Payables": [
                "payables", "accounts payable", "trade payables", "trade and other payables",
                "current payables", "other payables", "trade creditors", "accounts payable net",
                "trade and other current payables", "payables net", "trade payables net",
                "other current payables", "trade and other payables net"
            ],
            "Total Current Liabilities": [
                "total current liabilities", "current liabilities total", "total current liabilities net",
                "current liabilities", "total current liabilities at cost", "current liabilities sum"
            ],
            "Total Liabilities": [
                "total liabilities", "liabilities total", "total liabilities net", "total liabilities at cost",
                "liabilities", "total liabilities sum", "total liabilities before depreciation"
            ],
            
            # Balance Sheet - Equity
            "Share Capital": [
                "share capital", "capital", "equity capital", "shareholders capital", "issued capital",
                "authorized capital", "paid up capital", "share capital issued", "equity share capital",
                "ordinary share capital", "common share capital", "share capital at par"
            ],
            "Retained Earnings": [
                "retained earnings", "retained profits", "accumulated profits", "retained income",
                "retained earnings brought forward", "retained earnings carried forward",
                "accumulated retained earnings", "retained earnings net", "retained profits net"
            ],
            "Total Equity": [
                "total equity", "equity total", "total shareholders equity", "total equity net",
                "shareholders equity", "total equity at cost", "equity sum", "total equity before depreciation"
            ],
            
            # Income Statement
            "Total Revenue": [
                "revenue", "total revenue", "net sales", "gross sales", "turnover", "income",
                "sales", "total sales", "operating revenue", "total income", "revenue from operations",
                "net revenue", "gross revenue", "sales revenue", "operating income", "revenue net"
            ],
            "Net Income": [
                "net income", "profit", "net profit", "profit for the period", "net earnings",
                "profit after tax", "net profit after tax", "earnings", "net income after tax",
                "profit for the year", "net profit for the year", "net income net"
            ],
            "Cost of Sales": [
                "cost of sales", "cogs", "cost of goods sold", "cost of revenue", "cost of sales net",
                "direct costs", "cost of products sold", "cost of services", "cost of sales at cost"
            ],
            "Gross Profit": [
                "gross profit", "gross income", "gross margin", "gross profit margin",
                "gross profit net", "gross income net", "gross profit before expenses"
            ],
            "Operating Expenses": [
                "operating expenses", "opex", "operating costs", "administrative expenses",
                "selling expenses", "general expenses", "operating costs net", "total operating expenses",
                "operating expenses net", "operating costs at cost"
            ],
            
            # Cash Flow Statement
            "Net Cashflow from Operations (per FS)": [
                "operating cash flow", "cash from operations", "net cash operations", "cash flow from operations",
                "operating cashflow", "net operating cash flow", "cash generated from operations",
                "operating activities cash flow", "net cash from operating activities", "net_cash_from_operating_activities",
                "net_cash_applied_operating_activities", "total_cash_applied_to_operating_activities"
            ],
            "Depreciation": [
                "depreciation", "depreciation expense", "depreciation and amortization", "depreciation net",
                "accumulated depreciation", "depreciation charge", "depreciation for the year",
                "amortization_depreciation_of_fixed_assets"
            ],
            "Amortization": [
                "amortization", "amortization expense", "amortization net", "amortization charge",
                "amortization for the year", "intangible asset amortization", "amortization_depreciation_of_fixed_assets"
            ],
            "Interest Expense": [
                "interest expense", "interest paid", "interest cost", "interest charges",
                "cash_paid_for_income_taxes", "interest payments"
            ],
            "Principal Payments": [
                "principal payments", "principal repayments", "debt payments", "loan payments",
                "proceeds_from_additional_issuance_of_paid_up_capital"
            ],
            "Interest Payments": [
                "interest payments", "interest paid", "interest expense", "interest cost",
                "cash_paid_for_income_taxes"
            ],
            "Non-Cash Expenses": [
                "non-cash expenses", "non cash expenses", "noncash expenses", "non-cash items",
                "amortization_depreciation_of_fixed_assets", "depreciation and amortization"
            ],
            "Lease Payments": [
                "lease payments", "rental payments", "lease expenses", "rent expenses",
                "operating lease payments", "finance lease payments"
            ]
        }
    
    def fuzzy_match_score(self, a: str, b: str) -> float:
        """Calculate similarity between two strings using multiple algorithms"""
        a_clean = re.sub(r'[^\w\s]', '', a.lower().strip())
        b_clean = re.sub(r'[^\w\s]', '', b.lower().strip())
        
        # Sequence matcher
        sequence_score = SequenceMatcher(None, a_clean, b_clean).ratio()
        
        # Word overlap score
        a_words = set(a_clean.split())
        b_words = set(b_clean.split())
        if a_words and b_words:
            word_overlap = len(a_words.intersection(b_words)) / len(a_words.union(b_words))
        else:
            word_overlap = 0
        
        # Combined score (weighted average)
        combined_score = (sequence_score * 0.7) + (word_overlap * 0.3)
        return combined_score
    
    def find_best_template_match(self, extracted_field: str, threshold: float = 0.6) -> Optional[Dict[str, str]]:
        """Find best matching template field using fuzzy matching"""
        best_match = None
        best_score = 0
        
        for template_row in self.template_data:
            template_field = template_row['Field']
            
            # Check comprehensive mappings first
            if template_field in self.comprehensive_mappings:
                for variant in self.comprehensive_mappings[template_field]:
                    score = self.fuzzy_match_score(extracted_field, variant)
                    if score > best_score and score > threshold:
                        best_score = score
                        best_match = template_row
            
            # Also check direct fuzzy matching
            score = self.fuzzy_match_score(extracted_field, template_field)
            if score > best_score and score > threshold:
                best_score = score
                best_match = template_row
        
        if best_match:
            logger.debug(f"Matched '{extracted_field}' to '{best_match['Field']}' (score: {best_score:.3f})")
        
        return best_match
    
    def adapt_ai_extraction(self, raw_ai_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert AI extraction format to expected structure for template mapping"""
        adapted_data = {
            'company_name': raw_ai_data.get('company_name', ''),
            'period': raw_ai_data.get('period', ''),
            'currency': raw_ai_data.get('currency', ''),
            'years_detected': raw_ai_data.get('years_detected', []),
            'line_items': {},
            'summary_metrics': {}
        }
        
        # Handle nested line_items structure (already in expected format)
        if 'line_items' in raw_ai_data:
            adapted_data['line_items'] = raw_ai_data['line_items']
        
        # Handle summary_metrics structure (already in expected format)
        if 'summary_metrics' in raw_ai_data:
            adapted_data['summary_metrics'] = raw_ai_data['summary_metrics']
        
        # Handle flat extraction format (convert to nested structure)
        flat_fields = {}
        for key, value in raw_ai_data.items():
            if key not in ['company_name', 'period', 'currency', 'years_detected', 'line_items', 'summary_metrics']:
                if isinstance(value, (int, float)) and value != 0:
                    flat_fields[key] = value
        
        # Convert flat fields to nested structure using fuzzy matching
        for field_name, field_value in flat_fields.items():
            # Find best template match
            template_match = self.find_best_template_match(field_name)
            if template_match:
                category = template_match['Category'].lower()
                subcategory = template_match['Subcategory'].lower()
                
                # Determine category key for line_items
                category_key = self._determine_category_key(category, subcategory)
                
                if category_key not in adapted_data['line_items']:
                    adapted_data['line_items'][category_key] = {}
                
                adapted_data['line_items'][category_key][field_name] = {
                    'value': field_value,
                    'confidence': 0.8,  # Default confidence for flat extraction
                    'base_year': field_value
                }
                
                logger.debug(f"Adapted flat field '{field_name}' to category '{category_key}'")
        
        return adapted_data
    
    def _determine_category_key(self, category: str, subcategory: str) -> str:
        """Determine the category key for line_items based on template category/subcategory"""
        category = category.lower()
        subcategory = subcategory.lower()
        
        if category == 'balance sheet':
            if 'current assets' in subcategory:
                return 'current_assets'
            elif 'non-current assets' in subcategory or 'non current assets' in subcategory:
                return 'non_current_assets'
            elif 'current liabilities' in subcategory:
                return 'current_liabilities'
            elif 'non-current liabilities' in subcategory or 'non current liabilities' in subcategory:
                return 'non_current_liabilities'
            elif 'equity' in subcategory:
                return 'equity'
        elif category == 'income statement':
            if 'revenue' in subcategory:
                return 'revenues'
            elif 'expenses' in subcategory:
                return 'operating_expenses'
            elif 'cost' in subcategory:
                return 'cost_of_sales'
        elif category == 'cash flow statement':
            if 'operating' in subcategory:
                return 'operating_activities'
            elif 'investing' in subcategory:
                return 'investing_activities'
            elif 'financing' in subcategory:
                return 'financing_activities'
        
        # Default fallback
        return 'other'
    
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
    
    def _populate_template_field(self, template_row: Dict[str, str], extracted_data: Dict[str, Any]) -> bool:
        """
        Populate a single template field with extracted data
        
        Args:
            template_row: Single row from the template
            extracted_data: Financial data extracted from API
            
        Returns:
            bool: True if field was populated, False otherwise
        """
        field_name = template_row.get('Field', '').lower()
        category = template_row.get('Category', '').lower()
        subcategory = template_row.get('Subcategory', '').lower()
        
        # Handle meta fields
        if category == 'meta':
            if 'company' in field_name:
                template_row['Value_Year_1'] = extracted_data.get('company_name', '')
                template_row['Confidence'] = 'High'
                template_row['Confidence_Score'] = '0.95'
                return True
            elif 'period' in field_name:
                template_row['Value_Year_1'] = extracted_data.get('period', '')
                template_row['Confidence'] = 'High'
                template_row['Confidence_Score'] = '0.95'
                return True
            elif 'currency' in field_name:
                template_row['Value_Year_1'] = extracted_data.get('currency', '')
                template_row['Confidence'] = 'High'
                template_row['Confidence_Score'] = '0.95'
                return True
            elif 'year' in field_name:
                years = extracted_data.get('years_detected', [])
                if years:
                    template_row['Value_Year_1'] = years[0]
                    template_row['Confidence'] = 'High'
                    template_row['Confidence_Score'] = '0.95'
                    return True
            return False
        
        # Handle financial line items
        line_items = extracted_data.get('line_items', {})
        years = extracted_data.get('years_detected', [])
        
        # Try to find matching field in extracted data
        for category_key, items in line_items.items():
            if not isinstance(items, dict):
                continue
                
            for item_name, item_data in items.items():
                if not isinstance(item_data, dict) or 'value' not in item_data:
                    continue
                
                # Check if this extracted field matches the template field
                if self._field_matches(field_name, item_name, category, subcategory, category_key):
                    # Populate the field with extracted data
                    self._populate_field_values(template_row, item_data, years)
                    return True
        
        # Try summary metrics
        summary_metrics = extracted_data.get('summary_metrics', {})
        for metric_name, metric_data in summary_metrics.items():
            if self._field_matches(field_name, metric_name, category, subcategory, ''):
                if isinstance(metric_data, dict) and 'value' in metric_data:
                    self._populate_field_values(template_row, metric_data, years)
                    return True
        
        return False
    
    def _field_matches(self, template_field: str, extracted_field: str, template_category: str, template_subcategory: str, extracted_category: str) -> bool:
        """Check if an extracted field matches a template field"""
        template_field = template_field.lower()
        extracted_field = extracted_field.lower()
        template_category = template_category.lower()
        template_subcategory = template_subcategory.lower()
        extracted_category = extracted_category.lower()
        
        # Direct name matching
        if template_field in extracted_field or extracted_field in template_field:
            return True
        
        # Category-based matching
        if template_category == 'balance sheet':
            if 'current_assets' in extracted_category and 'current assets' in template_subcategory:
                return self._balance_sheet_field_match(template_field, extracted_field, 'current_assets')
            elif 'non_current_assets' in extracted_category and 'non-current assets' in template_subcategory:
                return self._balance_sheet_field_match(template_field, extracted_field, 'non_current_assets')
            elif 'current_liabilities' in extracted_category and 'current liabilities' in template_subcategory:
                return self._balance_sheet_field_match(template_field, extracted_field, 'current_liabilities')
            elif 'equity' in extracted_category and 'equity' in template_subcategory:
                return self._balance_sheet_field_match(template_field, extracted_field, 'equity')
        
        elif template_category == 'income statement':
            if 'revenue' in extracted_category and 'revenue' in template_subcategory:
                return self._income_statement_field_match(template_field, extracted_field, 'revenue')
            elif 'expense' in extracted_category and 'expenses' in template_subcategory:
                return self._income_statement_field_match(template_field, extracted_field, 'expense')
        
        elif template_category == 'cash flow statement':
            if 'operating' in extracted_category and 'operating activities' in template_subcategory:
                return self._cash_flow_field_match(template_field, extracted_field, 'operating')
        
        return False
    
    def _balance_sheet_field_match(self, template_field: str, extracted_field: str, category: str) -> bool:
        """Match balance sheet fields"""
        field_mappings = {
            'cash and cash equivalents': ['cash', 'cash_equivalents', 'cash_and_equivalents'],
            'trade and other current receivables': ['receivables', 'accounts_receivable', 'trade_receivables'],
            'current inventories': ['inventory', 'inventories', 'stock'],
            'property, plant and equipment': ['ppe', 'property_plant_equipment', 'fixed_assets'],
            'total current assets': ['total_current_assets', 'current_assets_total'],
            'total assets': ['total_assets', 'assets_total'],
            'total current liabilities': ['total_current_liabilities', 'current_liabilities_total'],
            'total liabilities': ['total_liabilities', 'liabilities_total'],
            'share capital': ['share_capital', 'capital', 'equity_capital'],
            'retained earnings': ['retained_earnings', 'retained_earnings']
        }
        
        for template_key, extracted_variants in field_mappings.items():
            if template_key in template_field:
                return any(variant in extracted_field for variant in extracted_variants)
        
        return False
    
    def _income_statement_field_match(self, template_field: str, extracted_field: str, category: str) -> bool:
        """Match income statement fields"""
        field_mappings = {
            'total revenue': ['revenue', 'total_revenue', 'net_sales', 'sales'],
            'net income': ['net_income', 'profit', 'net_profit'],
            'cost of sales': ['cost_of_sales', 'cogs', 'cost_of_goods_sold'],
            'gross profit': ['gross_profit', 'gross_income'],
            'operating expenses': ['operating_expenses', 'opex', 'operating_costs']
        }
        
        for template_key, extracted_variants in field_mappings.items():
            if template_key in template_field:
                return any(variant in extracted_field for variant in extracted_variants)
        
        return False
    
    def _cash_flow_field_match(self, template_field: str, extracted_field: str, category: str) -> bool:
        """Match cash flow statement fields"""
        field_mappings = {
            'net cashflow from operations': ['operating_cash_flow', 'cash_from_operations', 'net_cash_operations'],
            'depreciation': ['depreciation', 'depreciation_expense'],
            'amortization': ['amortization', 'amortization_expense']
        }
        
        for template_key, extracted_variants in field_mappings.items():
            if template_key in template_field:
                return any(variant in extracted_field for variant in extracted_variants)
        
        return False
    
    def _populate_field_values(self, template_row: Dict[str, str], item_data: Dict[str, Any], years: List[str]) -> None:
        """Populate template row with extracted values"""
        confidence = item_data.get('confidence', 0.95)
        
        # Set confidence
        if confidence >= 0.9:
            template_row['Confidence'] = 'High'
        elif confidence >= 0.7:
            template_row['Confidence'] = 'Medium'
        else:
            template_row['Confidence'] = 'Low'
        
        template_row['Confidence_Score'] = f"{confidence:.2f}"
        
        # Populate year values
        if 'base_year' in item_data:
            template_row['Value_Year_1'] = str(item_data['base_year'])
        if 'year_1' in item_data:
            template_row['Value_Year_2'] = str(item_data['year_1'])
        if 'year_2' in item_data:
            template_row['Value_Year_3'] = str(item_data['year_2'])
        if 'year_3' in item_data:
            template_row['Value_Year_4'] = str(item_data['year_3'])
    
    def export_to_template_csv(self, extracted_data: Dict[str, Any], output_path: str) -> bool:
        """
        Export extracted financial data to template CSV format using LLM-first direct mapping
        
        Args:
            extracted_data: Financial data with template_mappings from LLM
            output_path: Path to save the CSV file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get direct mappings from LLM
            template_mappings = extracted_data.get('template_mappings', {})
            
            # Create a copy of the template structure
            filled_template = []
            for template_row in self.template_data:
                filled_row = template_row.copy()
                field_name = template_row['Field']
                
                # Direct lookup - no complex mapping needed
                if field_name in template_mappings:
                    mapping = template_mappings[field_name]
                    filled_row['Value_Year_1'] = mapping.get('value')
                    filled_row['Confidence'] = self._convert_confidence(mapping.get('confidence', 0.8))
                    filled_row['Confidence_Score'] = mapping.get('confidence', 0.8)
                    
                    # Handle multi-year data if available
                    if 'Value_Year_1' in mapping:
                        filled_row['Value_Year_1'] = mapping.get('Value_Year_1')
                    if 'Value_Year_2' in mapping:
                        filled_row['Value_Year_2'] = mapping.get('Value_Year_2')
                    if 'Value_Year_3' in mapping:
                        filled_row['Value_Year_3'] = mapping.get('Value_Year_3')
                    if 'Value_Year_4' in mapping:
                        filled_row['Value_Year_4'] = mapping.get('Value_Year_4')
                    
                    # Also handle old format for backward compatibility
                    if 'base_year' in mapping:
                        filled_row['Value_Year_1'] = mapping.get('base_year')
                    if 'year_1' in mapping:
                        filled_row['Value_Year_2'] = mapping.get('year_1')
                    if 'year_2' in mapping:
                        filled_row['Value_Year_3'] = mapping.get('year_2')
                    if 'year_3' in mapping:
                        filled_row['Value_Year_4'] = mapping.get('year_3')
                
                filled_template.append(filled_row)
            
            # Write to CSV
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.template_header)
                writer.writeheader()
                writer.writerows(filled_template)
            
            # Count populated fields
            populated_count = sum(1 for row in filled_template if row.get('Value_Year_1') or row.get('Value_Year_2') or row.get('Value_Year_3') or row.get('Value_Year_4'))
            
            logger.info(f"LLM-First Template CSV exported to: {output_path}")
            logger.info(f"Template structure: {len(filled_template)} rows")
            logger.info(f"Populated fields: {populated_count} out of {len(filled_template)}")
            logger.info(f"Coverage: {populated_count / len(filled_template) * 100:.1f}%")
            logger.info(f"Direct mappings used: {len(template_mappings)}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting template CSV: {e}")
            return False
    
    def _convert_confidence(self, confidence: float) -> str:
        """Convert numeric confidence to string format"""
        if confidence >= 0.9:
            return "High"
        elif confidence >= 0.7:
            return "Medium"
        else:
            return "Low"
    
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
