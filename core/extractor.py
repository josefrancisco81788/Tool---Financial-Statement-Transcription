"""
Core financial data extraction logic extracted from the proven alpha-testing-v1 Streamlit app.
"""

import json
import base64
import time
import random
from typing import Dict, Any, Optional, List, Union
from openai import OpenAI
import anthropic
from .config import Config


class FinancialDataExtractor:
    """Core financial data extraction class with dual provider support"""
    
    def __init__(self, openai_client: Optional[OpenAI] = None, anthropic_client: Optional[anthropic.Anthropic] = None):
        """Initialize the extractor with AI provider clients"""
        self.config = Config()
        self.provider = self.config.AI_PROVIDER.lower()
        
        # Initialize clients based on provider
        if self.provider == "openai":
            self.openai_client = openai_client or OpenAI(api_key=self.config.OPENAI_API_KEY)
            self.anthropic_client = None
        elif self.provider == "anthropic":
            self.openai_client = None
            self.anthropic_client = anthropic_client or anthropic.Anthropic(api_key=self.config.ANTHROPIC_API_KEY)
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}. Must be 'openai' or 'anthropic'")
    
    def exponential_backoff_retry(self, func, max_retries: int = 3, base_delay: float = 1, max_delay: int = 60):
        """Implement exponential backoff for API calls with rate limiting"""
        for attempt in range(max_retries):
            try:
                result = func()
                if result is None:
                    raise Exception("API returned None response")
                return result
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a rate limit error
                if '429' in error_str or 'rate limit' in error_str or 'too many requests' in error_str:
                    if attempt < max_retries - 1:
                        # Calculate delay with jitter
                        delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                        print(f"⏳ Rate limit hit. Waiting {delay:.1f} seconds before retry {attempt + 2}/{max_retries}...")
                        time.sleep(delay)
                        continue
                    else:
                        raise e
                else:
                    # Non-rate-limit error, don't retry
                    raise e
        
        # If we get here, all retries failed
        raise Exception("All retry attempts failed")
    
    def extract_comprehensive_financial_data(self, base64_image: str, statement_type_hint: str = "financial statement", page_text: str = "") -> Dict[str, Any]:
        """
        Extract comprehensive financial data from a base64-encoded image.
        
        Args:
            base64_image: Base64-encoded image data
            statement_type_hint: Hint about the type of financial statement
            page_text: Optional text content from the page
            
        Returns:
            Dictionary containing extracted financial data
        """
        try:
            # Build the comprehensive extraction prompt
            prompt = self._build_extraction_prompt(statement_type_hint)
            
            # Make provider-specific API call with retry logic
            if self.provider == "openai":
                response = self._call_openai_api(base64_image, prompt)
            elif self.provider == "anthropic":
                response = self._call_anthropic_api(base64_image, prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # Parse the JSON response
            if not response:
                raise Exception("Empty response from AI model")
            
            # Extract JSON from the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise Exception("No valid JSON found in AI response")
                
            json_str = response[start_idx:end_idx]
            extracted_data = json.loads(json_str)
            
            # Add processing metadata
            extracted_data['processing_method'] = 'comprehensive_extraction'
            extracted_data['ai_provider'] = self.provider
            extracted_data['timestamp'] = time.time()
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            raise Exception(f"JSON parsing error: {str(e)}")
            
        except Exception as e:
            raise Exception(f"Error in comprehensive extraction: {str(e)}")
    
    def _build_extraction_prompt(self, statement_type_hint: str) -> str:
        """Build the comprehensive extraction prompt"""
        return f"""
        You are a financial data extraction expert. Analyze this {statement_type_hint} and extract ALL visible financial line items.

        CORE EXTRACTION RULE: Extract every line that has both a LABEL and a NUMERICAL VALUE.

        STEP-BY-STEP PROCESS:
        1. SCAN the entire document for lines with labels and numbers
        2. IDENTIFY the document's own section headers and organization
        3. EXTRACT using the exact terminology from the document
        4. ORGANIZE into logical categories based on the document's structure
        5. FORMAT using the JSON structure below

        CURRENCY AND NUMBER HANDLING:
        - Handle all currency symbols (₱, $, €, £, ¥, etc.)
        - Parse parentheses as NEGATIVE numbers: ₱(26,278) = -26278
        - Handle comma-separated numbers: ₱249,788,478 = 249788478
        - Remove currency symbols and return just numeric values
        - If no clear number, set value to null and confidence to 0.1

        YEAR HANDLING (RELATIVE APPROACH):
        - Identify ALL years present in columns
        - Use relative positioning: base_year (leftmost/primary), year_1, year_2, year_3
        - Record actual years found for reference
        - Only include year fields that have actual data

        REQUIRED JSON STRUCTURE (adapt field names to match document):
        {{
            "statement_type": "exact statement title from document",
            "company_name": "extracted company name",
            "period": "extracted period/date", 
            "currency": "extracted currency (PHP, USD, etc.)",
            "years_detected": ["2024", "2023", "2022"],  // actual years found
            "base_year": "2024",  // leftmost/primary year
            "year_ordering": "most_recent_first" or "chronological",
            
            "line_items": {{
                // ADAPT these category names to match the document's structure
                // Examples for different statement types:
                
                // FOR BALANCE SHEETS - use document's section names:
                "current_assets": {{
                    "cash_and_equivalents": {{"value": 1000000, "confidence": 0.95, "base_year": 1000000, "year_1": 950000}},
                    "accounts_receivable": {{"value": 500000, "confidence": 0.90, "base_year": 500000, "year_1": 480000}},
                    "inventory": {{"value": 300000, "confidence": 0.85, "base_year": 300000, "year_1": 290000}}
                }},
                "non_current_assets": {{
                    "property_plant_equipment": {{"value": 2000000, "confidence": 0.92, "base_year": 2000000, "year_1": 1900000}}
                }},
                "current_liabilities": {{
                    "accounts_payable": {{"value": 400000, "confidence": 0.88, "base_year": 400000, "year_1": 380000}}
                }},
                "equity": {{
                    "share_capital": {{"value": 1000000, "confidence": 0.95, "base_year": 1000000, "year_1": 1000000}},
                    "retained_earnings": {{"value": 800000, "confidence": 0.90, "base_year": 800000, "year_1": 750000}}
                }},
                
                // FOR INCOME STATEMENTS - use document's section names:
                "revenues": {{
                    "net_sales": {{"value": 5000000, "confidence": 0.95, "base_year": 5000000, "year_1": 4800000}},
                    "other_income": {{"value": 100000, "confidence": 0.80, "base_year": 100000, "year_1": 95000}}
                }},
                "cost_of_sales": {{
                    "cost_of_goods_sold": {{"value": 3000000, "confidence": 0.92, "base_year": 3000000, "year_1": 2900000}}
                }},
                "operating_expenses": {{
                    "selling_expenses": {{"value": 500000, "confidence": 0.88, "base_year": 500000, "year_1": 480000}},
                    "administrative_expenses": {{"value": 300000, "confidence": 0.85, "base_year": 300000, "year_1": 290000}}
                }},
                
                // FOR CASH FLOW STATEMENTS - use document's section names:
                "operating_activities": {{
                    "net_income": {{"value": 1200000, "confidence": 0.95, "base_year": 1200000, "year_1": 1100000}},
                    "depreciation": {{"value": 200000, "confidence": 0.90, "base_year": 200000, "year_1": 190000}}
                }},
                "investing_activities": {{
                    "capital_expenditures": {{"value": -500000, "confidence": 0.88, "base_year": -500000, "year_1": -450000}}
                }},
                "financing_activities": {{
                    "dividends_paid": {{"value": -100000, "confidence": 0.85, "base_year": -100000, "year_1": -95000}}
                }}
            }},
            
            "summary_metrics": {{
                // Key totals for quick overview
                "total_assets": {{"value": 3000000, "confidence": 0.95}},
                "total_liabilities": {{"value": 1200000, "confidence": 0.90}},
                "total_equity": {{"value": 1800000, "confidence": 0.92}},
                "total_revenue": {{"value": 5100000, "confidence": 0.95}},
                "net_income": {{"value": 1200000, "confidence": 0.93}},
                "operating_cash_flow": {{"value": 1400000, "confidence": 0.88}}
            }},
            
            "document_structure": {{
                "main_sections": ["Assets", "Liabilities", "Equity"],  // actual section headers found
                "line_item_count": 15,  // total line items extracted
                "has_multi_year_data": true,
                "special_notes": "any unique aspects of this document"
            }},
            
            "notes": "observations about document structure, data quality, assumptions made"
        }}

        CRITICAL EXTRACTION GUIDELINES:

        1. **EXTRACT EVERYTHING**: Every line with a label and number should be captured
        2. **USE EXACT NAMES**: Convert document terminology to snake_case for JSON keys
           - "Cash and Cash Equivalents" → "cash_and_cash_equivalents"
           - "Accounts Receivable - Net" → "accounts_receivable_net"
           - "Property, Plant & Equipment" → "property_plant_equipment"
        
        3. **ADAPT CATEGORIES**: Use the document's own section organization
           - If document has "Current Assets" and "Non-Current Assets", use those
           - If document has "Operating Revenue" and "Non-Operating Revenue", use those
           - Don't force items into predefined categories if they don't fit
        
        4. **HANDLE TOTALS**: Always extract subtotals and grand totals
           - "Total Current Assets", "Total Assets", "Total Revenue", etc.
        
        5. **CONFIDENCE SCORING**:
           - 0.9-1.0: Crystal clear, unambiguous values
           - 0.7-0.9: Clear values with minor formatting complexity  
           - 0.5-0.7: Somewhat unclear but reasonable interpretation
           - 0.3-0.5: Uncertain, multiple possible interpretations
           - 0.1-0.3: Very uncertain or barely visible

        6. **MULTI-YEAR DATA**: If multiple years are present:
           - **CRITICAL**: Year headers (like "2024", "2023", "2022") are COLUMN HEADERS, not financial values
           - **DO NOT** extract year numbers as financial data values
           - Look for the actual financial amounts under each year column
           - Identify the base year (usually leftmost or most recent year column)
           - Extract the actual financial values for base_year, year_1, year_2, year_3 as available
           - **EXAMPLE**: If you see "Cash  2024: $1,000,000  2023: $950,000", extract:
             * base_year: 1000000 (the amount under 2024, not "2024" itself)
             * year_1: 950000 (the amount under 2023, not "2023" itself)
           - Only include year fields that have actual financial data (not the year labels)

        7. **FALLBACK APPROACH**: If document structure is unusual:
           - Create a "miscellaneous" or "other_items" category
           - Still extract all visible line items
           - Note the unusual structure in the "notes" field

        EXAMPLES OF ADAPTIVE EXTRACTION:

        Document shows: "Cash and Bank Deposits    ₱1,000,000    ₱950,000"
        Extract as: "cash_and_bank_deposits": {{"value": 1000000, "confidence": 0.95, "base_year": 1000000, "year_1": 950000}}

        Document shows: "Total Stockholders' Equity    $5,000,000"  
        Extract as: "total_stockholders_equity": {{"value": 5000000, "confidence": 0.95, "base_year": 5000000}}

        Document shows: "Cost of Sales    (2,000,000)"
        Extract as: "cost_of_sales": {{"value": -2000000, "confidence": 0.95, "base_year": -2000000}}

        **MULTI-YEAR EXAMPLE** - Document shows:
        "                    2024        2023        2022
        Cash                40,506,296  14,011,556  12,500,000
        Accounts Receivable 93,102,625  102,434,862 95,000,000"
        
        Extract as:
        "cash": {{"value": 40506296, "confidence": 0.95, "base_year": 40506296, "year_1": 14011556, "year_2": 12500000}}
        "accounts_receivable": {{"value": 93102625, "confidence": 0.95, "base_year": 93102625, "year_1": 102434862, "year_2": 95000000}}
        
        **WRONG**: Do NOT extract "2024": {{"value": 2024}} - years are headers, not data!

        REMEMBER: Your goal is to capture ALL financial data visible in the document while preserving the document's own terminology and organization. Be thorough but accurate.
        """
    
    def encode_image(self, image_file) -> str:
        """Encode image file to base64 string"""
        if hasattr(image_file, 'read'):
            # File-like object
            image_data = image_file.read()
        elif hasattr(image_file, 'save'):
            # PIL Image object
            import io
            buffer = io.BytesIO()
            image_file.save(buffer, format='PNG')
            image_data = buffer.getvalue()
        else:
            # Assume it's already bytes
            image_data = image_file
        
        return base64.b64encode(image_data).decode('utf-8')
    
    def extract_from_image(self, image_file, statement_type_hint: str = "financial statement") -> Dict[str, Any]:
        """
        Extract financial data from an image file.
        
        Args:
            image_file: Image file (file-like object or bytes)
            statement_type_hint: Hint about the type of financial statement
            
        Returns:
            Dictionary containing extracted financial data
        """
        try:
            # Encode image to base64
            base64_image = self.encode_image(image_file)
            
            # Extract financial data
            return self.extract_comprehensive_financial_data(base64_image, statement_type_hint)
            
        except Exception as e:
            raise Exception(f"Error extracting from image: {str(e)}")
    
    def _call_openai_api(self, base64_image: str, prompt: str) -> str:
        """Make API call to OpenAI with retry logic"""
        def api_call():
            response = self.openai_client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.config.OPENAI_MAX_TOKENS
            )
            return response.choices[0].message.content or ""
        
        return self.exponential_backoff_retry(api_call)
    
    def _call_anthropic_api(self, base64_image: str, prompt: str) -> str:
        """Make API call to Anthropic with retry logic using 2025 v4.2 API"""
        def api_call():
            # Use the correct 2025 v4.2 Anthropic API format
            response = self.anthropic_client.messages.create(
                model=self.config.ANTHROPIC_MODEL,
                max_tokens=self.config.ANTHROPIC_MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": base64_image
                                }
                            }
                        ]
                    }
                ]
            )
            
            # Handle response from 2025 v4.2 API
            if hasattr(response, 'content') and response.content:
                return response.content[0].text if isinstance(response.content, list) else response.content
            else:
                raise Exception(f"Unexpected response format: {type(response)}")
        
        return self.exponential_backoff_retry(api_call)
