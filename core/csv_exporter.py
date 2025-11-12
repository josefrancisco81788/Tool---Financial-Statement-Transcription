"""
Core CSV export functionality used by the Financial Statement Transcription API.

This module was promoted from the test harness so runtime environments (e.g. Cloud Run)
can generate standardized template-compliant CSV outputs without depending on
`tests.*` packages that may be excluded from deployment artifacts.
"""

from __future__ import annotations

import csv
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)


class CSVExporter:
    """Centralized CSV export functionality for financial data."""

    _DEFAULT_TEMPLATE = Path(__file__).parent / "templates" / "FS_Input_Template_Fields.csv"

    def __init__(self, template_path: Optional[str | Path] = None):
        """Initialize the exporter with a template path."""
        self.template_path = Path(template_path) if template_path else self._DEFAULT_TEMPLATE
        self.template_data = self._load_template()
        self.field_mappings = self._create_field_mappings()
        self.comprehensive_mappings = self._create_comprehensive_mappings()
        self.template_header = [
            "Category",
            "Subcategory",
            "Field",
            "Confidence",
            "Confidence_Score",
            "Value_Year_1",
            "Value_Year_2",
            "Value_Year_3",
            "Value_Year_4",
        ]

    # --------------------------------------------------------------------- #
    # Template helpers
    # --------------------------------------------------------------------- #
    def _load_template(self) -> List[Dict[str, str]]:
        """Load the template CSV structure from disk."""
        try:
            if not self.template_path.exists():
                logger.warning("Template file not found: %s", self.template_path)
                return []

            with self.template_path.open("r", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                template_data = list(reader)

            logger.info("Loaded %d template fields from %s", len(template_data), self.template_path)
            return template_data

        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Error loading template '%s': %s", self.template_path, exc)
            return []

    def _create_field_mappings(self) -> Dict[str, str]:
        """Create basic field mappings from extracted data to template fields."""
        return {
            # Meta fields
            "company_name": "Company",
            "period": "Period",
            "currency": "Currency",
            "years_detected": "Years",
            # Balance Sheet - Current Assets
            "cash": "Cash and Cash Equivalents",
            "cash_and_equivalents": "Cash and Cash Equivalents",
            "receivables": "Trade and Other Current Receivables",
            "trade_receivables": "Trade and Other Current Receivables",
            "inventories": "Inventories",
            "prepaid_expenses": "Prepaid Expenses",
            "other_current_assets": "Other Current Assets",
            # Balance Sheet - Non-Current Assets
            "property_plant_equipment": "Property, Plant and Equipment",
            "ppe": "Property, Plant and Equipment",
            "intangible_assets": "Intangible Assets",
            "goodwill": "Goodwill",
            "other_non_current_assets": "Other Non-Current Assets",
            # Balance Sheet - Current Liabilities
            "trade_payables": "Trade and Other Current Payables",
            "accounts_payable": "Trade and Other Current Payables",
            "short_term_debt": "Short-term Debt",
            "current_portion_long_term_debt": "Current Portion of Long-term Debt",
            "other_current_liabilities": "Other Current Liabilities",
            # Balance Sheet - Non-Current Liabilities
            "long_term_debt": "Long-term Debt",
            "other_non_current_liabilities": "Other Non-Current Liabilities",
            # Balance Sheet - Equity
            "share_capital": "Share Capital",
            "retained_earnings": "Retained Earnings",
            "other_equity": "Other Equity",
            # Income Statement
            "revenue": "Revenue",
            "sales": "Revenue",
            "cost_of_sales": "Cost of Sales",
            "gross_profit": "Gross Profit",
            "operating_expenses": "Operating Expenses",
            "operating_profit": "Operating Profit",
            "finance_costs": "Finance Costs",
            "profit_before_tax": "Profit Before Tax",
            "income_tax": "Income Tax",
            "profit_after_tax": "Profit After Tax",
            # Cash Flow
            "operating_cash_flow": "Operating Cash Flow",
            "investing_cash_flow": "Investing Cash Flow",
            "financing_cash_flow": "Financing Cash Flow",
            "net_cash_flow": "Net Cash Flow",
        }

    def _create_comprehensive_mappings(self) -> Dict[str, List[str]]:
        """Create comprehensive field mappings with extensive naming variations."""
        return {
            "Cash and Cash Equivalents": [
                "cash",
                "cash equivalents",
                "cash and equivalents",
                "liquid assets",
                "cash at bank",
                "cash in hand",
                "available funds",
                "short term deposits",
                "cash & short-term investments",
                "cash and near cash",
                "cash at bank and in hand",
                "cash and cash equivalents",
                "cash & cash equivalents",
                "liquid funds",
                "cash and short-term deposits",
                "cash and bank balances",
            ],
            "Trade and Other Current Receivables": [
                "receivables",
                "accounts receivable",
                "trade receivables",
                "trade and other receivables",
                "current receivables",
                "other receivables",
                "trade debtors",
                "accounts receivable net",
            ],
            "Current Inventories": [
                "inventory",
                "inventories",
                "stock",
                "current inventories",
                "inventory at cost",
                "inventories at cost",
                "stock in trade",
                "merchandise inventory",
                "raw materials",
                "work in progress",
                "finished goods",
            ],
            "Property, Plant and Equipment": [
                "ppe",
                "property plant and equipment",
                "property plant equipment",
                "fixed assets",
                "plant and equipment",
                "property and equipment",
                "tangible fixed assets",
                "property plant & equipment",
                "fixed assets net",
                "ppe net",
            ],
            "Total Current Assets": [
                "total current assets",
                "current assets total",
                "current assets sum",
            ],
            "Total Assets": [
                "total assets",
                "assets total",
                "total assets net",
            ],
            "Trade and Other Current Payables": [
                "payables",
                "accounts payable",
                "trade payables",
                "trade and other payables",
                "current payables",
                "other payables",
                "trade creditors",
                "accounts payable net",
            ],
            "Total Current Liabilities": [
                "total current liabilities",
                "current liabilities total",
                "current liabilities sum",
            ],
            "Total Liabilities": [
                "total liabilities",
                "liabilities total",
                "total liabilities net",
            ],
            "Share Capital": [
                "share capital",
                "capital",
                "equity capital",
                "shareholders capital",
                "issued capital",
                "authorized capital",
                "paid up capital",
                "share capital issued",
                "equity share capital",
                "ordinary share capital",
                "common share capital",
            ],
            "Retained Earnings": [
                "retained earnings",
                "retained profits",
                "accumulated profits",
                "retained income",
                "accumulated retained earnings",
            ],
            "Total Equity": [
                "total equity",
                "equity total",
                "total shareholders equity",
            ],
            "Total Revenue": [
                "revenue",
                "total revenue",
                "net sales",
                "gross sales",
                "turnover",
                "income",
                "sales",
                "total sales",
                "operating revenue",
                "total income",
                "revenue from operations",
                "net revenue",
            ],
            "Net Income": [
                "net income",
                "profit",
                "net profit",
                "profit for the period",
                "net earnings",
                "profit after tax",
                "net profit after tax",
            ],
            "Cost of Sales": [
                "cost of sales",
                "cogs",
                "cost of goods sold",
                "cost of revenue",
            ],
            "Gross Profit": [
                "gross profit",
                "gross income",
                "gross margin",
            ],
            "Operating Expenses": [
                "operating expenses",
                "opex",
                "operating costs",
                "administrative expenses",
                "selling expenses",
                "general expenses",
            ],
            "Net Cashflow from Operations (per FS)": [
                "operating cash flow",
                "cash from operations",
                "net cash operations",
                "cash flow from operations",
                "operating cashflow",
                "net operating cash flow",
                "cash generated from operations",
            ],
            "Depreciation": [
                "depreciation",
                "depreciation expense",
                "depreciation and amortization",
            ],
            "Amortization": [
                "amortization",
                "amortization expense",
                "amortization net",
            ],
            "Interest Expense": [
                "interest expense",
                "interest paid",
                "interest cost",
            ],
            "Principal Payments": [
                "principal payments",
                "principal repayments",
                "debt payments",
                "loan payments",
            ],
            "Interest Payments": [
                "interest payments",
                "interest paid",
                "interest expense",
            ],
            "Non-Cash Expenses": [
                "non-cash expenses",
                "non cash expenses",
                "noncash expenses",
                "non-cash items",
                "depreciation and amortization",
            ],
            "Lease Payments": [
                "lease payments",
                "rental payments",
                "lease expenses",
                "rent expenses",
            ],
        }

    # --------------------------------------------------------------------- #
    # Matching helpers
    # --------------------------------------------------------------------- #
    @staticmethod
    def _clean_field_name(value: str) -> str:
        return re.sub(r"[^\w\s]", "", value.lower().strip())

    def fuzzy_match_score(self, a: str, b: str) -> float:
        """Calculate similarity between two strings using multiple algorithms."""
        a_clean = self._clean_field_name(a)
        b_clean = self._clean_field_name(b)

        sequence_score = SequenceMatcher(None, a_clean, b_clean).ratio()
        a_words = set(a_clean.split())
        b_words = set(b_clean.split())
        word_overlap = len(a_words & b_words) / len(a_words | b_words) if a_words and b_words else 0
        return (sequence_score * 0.7) + (word_overlap * 0.3)

    def find_best_template_match(self, extracted_field: str, threshold: float = 0.6) -> Optional[Dict[str, str]]:
        """Find best matching template field using fuzzy matching."""
        best_match: Optional[Dict[str, str]] = None
        best_score = 0.0

        for template_row in self.template_data:
            template_field = template_row["Field"]

            if template_field in self.comprehensive_mappings:
                for variant in self.comprehensive_mappings[template_field]:
                    score = self.fuzzy_match_score(extracted_field, variant)
                    if score > best_score and score > threshold:
                        best_score = score
                        best_match = template_row

            score = self.fuzzy_match_score(extracted_field, template_field)
            if score > best_score and score > threshold:
                best_score = score
                best_match = template_row

        if best_match:
            logger.debug(
                "Matched '%s' to '%s' (score=%.3f)",
                extracted_field,
                best_match["Field"],
                best_score,
            )
        return best_match

    # --------------------------------------------------------------------- #
    # Adaptation helpers
    # --------------------------------------------------------------------- #
    def adapt_ai_extraction(self, raw_ai_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert AI extraction format to expected structure for template mapping."""
        adapted_data: Dict[str, Any] = {
            "company_name": raw_ai_data.get("company_name", ""),
            "period": raw_ai_data.get("period", ""),
            "currency": raw_ai_data.get("currency", ""),
            "years_detected": raw_ai_data.get("years_detected", []),
            "line_items": raw_ai_data.get("line_items", {}),
            "summary_metrics": raw_ai_data.get("summary_metrics", {}),
        }

        flat_fields = {}
        for key, value in raw_ai_data.items():
            if key in adapted_data:
                continue
            if isinstance(value, (int, float)) and value != 0:
                flat_fields[key] = value

        for field_name, field_value in flat_fields.items():
            template_match = self.find_best_template_match(field_name)
            if not template_match:
                continue

            category = template_match["Category"].lower()
            subcategory = template_match["Subcategory"].lower()
            category_key = self._determine_category_key(category, subcategory)

            adapted_data.setdefault("line_items", {})
            adapted_data["line_items"].setdefault(category_key, {})
            adapted_data["line_items"][category_key][field_name] = {
                "value": field_value,
                "confidence": 0.8,
                "base_year": field_value,
            }

        return adapted_data

    @staticmethod
    def _determine_category_key(category: str, subcategory: str) -> str:
        """Determine the category key for line_items based on template metadata."""
        category = category.lower()
        subcategory = subcategory.lower()

        if category == "balance sheet":
            if "current assets" in subcategory:
                return "current_assets"
            if "non-current assets" in subcategory or "non current assets" in subcategory:
                return "non_current_assets"
            if "current liabilities" in subcategory:
                return "current_liabilities"
            if "non-current liabilities" in subcategory or "non current liabilities" in subcategory:
                return "non_current_liabilities"
            if "equity" in subcategory:
                return "equity"
        if category == "income statement":
            if "revenue" in subcategory:
                return "revenues"
            if "expenses" in subcategory:
                return "operating_expenses"
            if "cost" in subcategory:
                return "cost_of_sales"
        if category == "cash flow statement":
            if "operating" in subcategory:
                return "operating_activities"
            if "investing" in subcategory:
                return "investing_activities"
            if "financing" in subcategory:
                return "financing_activities"
        return "other"

    # --------------------------------------------------------------------- #
    # Mapping helpers
    # --------------------------------------------------------------------- #
    def _populate_field_values(self, template_row: Dict[str, str], item_data: Dict[str, Any], years: List[str]) -> None:
        """Populate template row with extracted values."""
        confidence = item_data.get("confidence", 0.95)
        if confidence >= 0.9:
            template_row["Confidence"] = "High"
        elif confidence >= 0.7:
            template_row["Confidence"] = "Medium"
        else:
            template_row["Confidence"] = "Low"
        template_row["Confidence_Score"] = f"{confidence:.2f}"

        if "base_year" in item_data:
            template_row["Value_Year_1"] = str(item_data["base_year"])
        if "year_1" in item_data:
            template_row["Value_Year_2"] = str(item_data["year_1"])
        if "year_2" in item_data:
            template_row["Value_Year_3"] = str(item_data["year_2"])
        if "year_3" in item_data:
            template_row["Value_Year_4"] = str(item_data["year_3"])

        for index, year in enumerate(years[:4]):
            key = f"year_{year}"
            if key in item_data:
                template_row[f"Value_Year_{index + 1}"] = str(item_data[key])
            elif year in item_data:
                template_row[f"Value_Year_{index + 1}"] = str(item_data[year])

    def _field_matches(
        self,
        template_field: str,
        extracted_field: str,
        template_category: str,
        template_subcategory: str,
        extracted_category: str,
    ) -> bool:
        """Check if an extracted field matches a template field."""
        template_field = template_field.lower()
        extracted_field = extracted_field.lower()
        template_category = template_category.lower()
        template_subcategory = template_subcategory.lower()
        extracted_category = extracted_category.lower()

        if template_field in extracted_field or extracted_field in template_field:
            return True

        if template_category == "balance sheet":
            if "current_assets" in extracted_category and "current assets" in template_subcategory:
                return self._balance_sheet_field_match(template_field, extracted_field)
            if "non_current_assets" in extracted_category and "non-current assets" in template_subcategory:
                return self._balance_sheet_field_match(template_field, extracted_field)
            if "current_liabilities" in extracted_category and "current liabilities" in template_subcategory:
                return self._balance_sheet_field_match(template_field, extracted_field)
            if "equity" in extracted_category and "equity" in template_subcategory:
                return self._balance_sheet_field_match(template_field, extracted_field)

        if template_category == "income statement":
            if "revenue" in extracted_category and "revenue" in template_subcategory:
                return self._income_statement_field_match(template_field, extracted_field)
            if "expense" in extracted_category and "expenses" in template_subcategory:
                return self._income_statement_field_match(template_field, extracted_field)

        if template_category == "cash flow statement":
            if "operating" in extracted_category and "operating activities" in template_subcategory:
                return self._cash_flow_field_match(template_field, extracted_field)

        return False

    @staticmethod
    def _balance_sheet_field_match(template_field: str, extracted_field: str) -> bool:
        mappings = {
            "cash and cash equivalents": ["cash", "cash_equivalents", "cash_and_equivalents"],
            "trade and other current receivables": ["receivables", "accounts_receivable", "trade_receivables"],
            "current inventories": ["inventory", "inventories", "stock"],
            "property, plant and equipment": ["ppe", "property_plant_equipment", "fixed_assets"],
            "total current assets": ["total_current_assets", "current_assets_total"],
            "total assets": ["total_assets", "assets_total"],
            "total current liabilities": ["total_current_liabilities", "current_liabilities_total"],
            "total liabilities": ["total_liabilities", "liabilities_total"],
            "share capital": ["share_capital", "capital", "equity_capital"],
            "retained earnings": ["retained_earnings"],
        }
        for template_key, variants in mappings.items():
            if template_key in template_field:
                return any(variant in extracted_field for variant in variants)
        return False

    @staticmethod
    def _income_statement_field_match(template_field: str, extracted_field: str) -> bool:
        mappings = {
            "total revenue": ["revenue", "total_revenue", "net_sales", "sales"],
            "net income": ["net_income", "profit", "net_profit"],
            "cost of sales": ["cost_of_sales", "cogs", "cost_of_goods_sold"],
            "gross profit": ["gross_profit", "gross_income"],
            "operating expenses": ["operating_expenses", "opex", "operating_costs"],
        }
        for template_key, variants in mappings.items():
            if template_key in template_field:
                return any(variant in extracted_field for variant in variants)
        return False

    @staticmethod
    def _cash_flow_field_match(template_field: str, extracted_field: str) -> bool:
        mappings = {
            "net cashflow from operations": [
                "operating_cash_flow",
                "cash_from_operations",
                "net_cash_operations",
            ],
            "depreciation": ["depreciation", "depreciation_expense"],
            "amortization": ["amortization", "amortization_expense"],
        }
        for template_key, variants in mappings.items():
            if template_key in template_field:
                return any(variant in extracted_field for variant in variants)
        return False

    # --------------------------------------------------------------------- #
    # Export helpers
    # --------------------------------------------------------------------- #
    def export_to_template_csv(self, extracted_data: Dict[str, Any], output_path: str | Path) -> bool:
        """Export extracted financial data to template CSV format."""
        try:
            template_mappings = extracted_data.get("template_mappings", {})
            years_detected = extracted_data.get("years_detected", [])

            if not years_detected and "Year" in template_mappings:
                year_data = template_mappings["Year"]
                years_detected = [
                    str(year_data.get(f"Value_Year_{idx}", ""))
                    for idx in range(1, 5)
                    if year_data.get(f"Value_Year_{idx}")
                ]

            if years_detected:
                years_detected = sorted(
                    (str(year) for year in years_detected),
                    key=lambda value: int(value) if str(value).isdigit() else 0,
                    reverse=True,
                )

            filled_template: List[Dict[str, Any]] = []
            for template_row in self.template_data:
                filled_row = template_row.copy()
                field_name = template_row["Field"]

                if field_name in template_mappings:
                    mapping = template_mappings[field_name]
                    confidence = mapping.get("confidence", 0.8)

                    filled_row["Confidence"] = self._convert_confidence(confidence)
                    filled_row["Confidence_Score"] = confidence

                    for index in range(1, 5):
                        key = f"Value_Year_{index}"
                        if key in mapping:
                            filled_row[key] = mapping.get(key)

                    if "year" in mapping and years_detected and not any(
                        filled_row.get(f"Value_Year_{i}") for i in range(1, 5)
                    ):
                        year_value = str(mapping.get("year", ""))
                        field_value = mapping.get("value", "")
                        if year_value in years_detected:
                            year_index = years_detected.index(year_value)
                            filled_row[f"Value_Year_{year_index + 1}"] = field_value
                        elif not filled_row.get("Value_Year_1"):
                            filled_row["Value_Year_1"] = field_value

                    if not any(filled_row.get(f"Value_Year_{i}") for i in range(1, 5)):
                        if "base_year" in mapping:
                            filled_row["Value_Year_1"] = mapping.get("base_year")
                            filled_row["Value_Year_2"] = mapping.get("year_1", "")
                            filled_row["Value_Year_3"] = mapping.get("year_2", "")
                            filled_row["Value_Year_4"] = mapping.get("year_3", "")
                        elif "value" in mapping:
                            filled_row["Value_Year_1"] = mapping["value"]

                filled_template.append(filled_row)

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with output_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=self.template_header)
                writer.writeheader()
                writer.writerows(filled_template)

            populated_count = sum(
                1
                for row in filled_template
                if row.get("Value_Year_1")
                or row.get("Value_Year_2")
                or row.get("Value_Year_3")
                or row.get("Value_Year_4")
            )
            logger.info(
                "Template CSV exported to %s (%d/%d populated fields)",
                output_path,
                populated_count,
                len(filled_template),
            )
            return True

        except Exception as exc:  # pragma: no cover - defenses for IO issues
            logger.error("Error exporting template CSV to %s: %s", output_path, exc)
            return False

    def export_to_summary_csv(self, test_results: List[Dict[str, Any]], output_path: str | Path) -> bool:
        """Export test results to summary CSV format."""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            summary_header = [
                "File",
                "Company",
                "Statement Type",
                "Years",
                "Processing Time (s)",
                "Pages Processed",
                "Line Items Count",
                "Total Assets",
                "Total Liabilities",
                "Total Equity",
                "Success",
                "Status Code",
                "Error Message",
            ]

            with output_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(summary_header)

                for result in test_results:
                    response_data = result.get("response_data") or {}
                    data_content = response_data.get("data") or {}

                    filename = result.get("filename", "Unknown")
                    company = data_content.get("company_name", "N/A")
                    statement_type = data_content.get("statement_type", "N/A")
                    years = ", ".join(data_content.get("years_detected", []))
                    processing_time = result.get("processing_time", 0)
                    pages_processed = response_data.get("pages_processed", "N/A")
                    line_items_count = (
                        data_content.get("document_structure", {}).get("line_item_count", "N/A")
                    )

                    summary = data_content.get("summary_metrics", {})
                    total_assets = summary.get("total_assets", {}).get("value", "N/A")
                    total_liabilities = summary.get("total_liabilities", {}).get("value", "N/A")
                    total_equity = summary.get("total_equity", {}).get("value", "N/A")

                    success = result.get("success", False)
                    status_code = result.get("status_code", "N/A")
                    error_message = result.get("error", "N/A")

                    writer.writerow(
                        [
                            filename,
                            company,
                            statement_type,
                            years,
                            f"{processing_time:.1f}",
                            pages_processed,
                            line_items_count,
                            total_assets,
                            total_liabilities,
                            total_equity,
                            success,
                            status_code,
                            error_message,
                        ]
                    )

            logger.info("Summary CSV exported to %s", output_path)
            return True

        except Exception as exc:  # pragma: no cover
            logger.error("Error exporting summary CSV to %s: %s", output_path, exc)
            return False

    def validate_template_compliance(self, csv_path: str | Path) -> Dict[str, Any]:
        """Validate CSV against template format."""
        try:
            csv_path = Path(csv_path)
            if not csv_path.exists():
                return {"valid": False, "error": "File not found"}

            with csv_path.open("r", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)

            expected_header = set(self.template_header)
            actual_header = set(reader.fieldnames) if reader.fieldnames else set()
            header_compliance = expected_header == actual_header

            non_empty_fields = 0
            for row in rows:
                for field in ("Value_Year_1", "Value_Year_2", "Value_Year_3", "Value_Year_4"):
                    if row.get(field, "").strip():
                        non_empty_fields += 1

            return {
                "valid": header_compliance,
                "header_compliance": header_compliance,
                "total_rows": len(rows),
                "non_empty_fields": non_empty_fields,
                "expected_header": list(expected_header),
                "actual_header": list(actual_header),
            }

        except Exception as exc:  # pragma: no cover
            return {"valid": False, "error": str(exc)}

    @staticmethod
    def _convert_confidence(confidence: float) -> str:
        """Convert numeric confidence to qualitative label."""
        if confidence >= 0.9:
            return "High"
        if confidence >= 0.7:
            return "Medium"
        return "Low"


__all__ = ["CSVExporter"]

