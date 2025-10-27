"""
Core financial data extraction logic extracted from the proven alpha-testing-v1 Streamlit app.
"""

import json
import base64
import time
import random
import pandas as pd
import os
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
        
        # Debug provider configuration
        print(f"[DEBUG] Extractor init - provider: {self.provider}")
        print(f"[DEBUG] Extractor init - config AI_PROVIDER: {self.config.AI_PROVIDER}")
        print(f"[DEBUG] Extractor init - ANTHROPIC_API_KEY length: {len(self.config.ANTHROPIC_API_KEY)}")
        print(f"[DEBUG] Extractor init - OPENAI_API_KEY length: {len(self.config.OPENAI_API_KEY)}")
        
        # Initialize clients based on provider
        try:
            if self.provider == "openai":
                self.openai_client = openai_client or OpenAI(api_key=self.config.OPENAI_API_KEY)
                self.anthropic_client = None
                print("[INFO] OpenAI client created successfully")
            elif self.provider == "anthropic":
                self.openai_client = None
                self.anthropic_client = anthropic_client or anthropic.Anthropic(api_key=self.config.ANTHROPIC_API_KEY)
                print("[INFO] Anthropic client created successfully")
            else:
                raise ValueError(f"Unsupported AI provider: {self.provider}. Must be 'openai' or 'anthropic'")
        except Exception as e:
            print(f"[ERROR] Client creation failed: {e}")
            raise
        
        print(f"[DEBUG] Extractor init - has anthropic client: {hasattr(self, 'anthropic_client') and self.anthropic_client is not None}")
        print(f"[DEBUG] Extractor init - has openai client: {hasattr(self, 'openai_client') and self.openai_client is not None}")
    
    def _load_template_fields(self) -> List[str]:
        """Load the 91 template fields for context"""
        try:
            # Single correct path - remove duplicate
            template_path = "tests/fixtures/templates/FS_Input_Template_Fields.csv"
            
            if not os.path.exists(template_path):
                print(f"[WARN] Template file not found at: {template_path}")
                print(f"Current working directory: {os.getcwd()}")
                return self._get_fallback_template_fields()
            
            df = pd.read_csv(template_path)
            template_fields = df['Field'].tolist()
            
            # Validate we have exactly 91 fields
            if len(template_fields) != 91:
                print(f"[WARN] Expected 91 fields, got {len(template_fields)}")
            else:
                print(f"[INFO] Loaded exactly {len(template_fields)} template fields from {template_path}")
            
            # Log first few fields for verification
            print(f"First 5 template fields: {template_fields[:5]}")
            
            return template_fields
            
        except Exception as e:
            print(f"[ERROR] Error loading template fields: {e}")
            return self._get_fallback_template_fields()
    
    def _get_fallback_template_fields(self) -> List[str]:
        """Fallback template fields if CSV loading fails"""
        return [
            "Cash and Cash Equivalents", "Total Revenue", "Net Income", "Total Assets", "Total Equity",
            "Cost of Sales", "Gross Profit", "Operating Income", "Total Liabilities", "Current Assets",
            "Non-Current Assets", "Current Liabilities", "Non-Current Liabilities", "Share Capital",
            "Retained Earnings", "Depreciation", "Amortization", "Interest Expense", "Tax Expense"
        ]
    
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
            
            # Debug: Show the prompt being used
            print(f"[DEBUG] Using simplified prompt (first 500 chars): {prompt[:500]}...")
            
            # Make provider-specific API call with retry logic
            print(f"[DEBUG] About to make API call with provider: {self.provider}")
            if self.provider == "openai":
                print("[DEBUG] Using OpenAI endpoint")
                response = self._call_openai_api(base64_image, prompt)
            elif self.provider == "anthropic":
                print("[DEBUG] Using Anthropic endpoint")
                response = self._call_anthropic_api(base64_image, prompt)
            else:
                print(f"[ERROR] Unknown provider: {self.provider}")
                raise ValueError(f"Unknown provider: {self.provider}")
            
            print(f"[DEBUG] API call completed with provider: {self.provider}")
            
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
        """Build enhanced but focused LLM-first direct mapping extraction prompt"""
        template_fields = self._load_template_fields()
        
        return f"""
        Extract ALL financial data from this {statement_type_hint} and map to template fields.

        AVAILABLE TEMPLATE FIELDS: {', '.join(template_fields)}

        EXTRACTION RULES:
        1. Extract EVERY line item with both a label and numerical value
        2. Map each item to the most appropriate template field from the list above
        3. Use EXACT template field names (case-sensitive)
        4. Extract values as numbers (remove currency symbols, handle parentheses as negative)
        5. Set confidence: 0.9+ for clear values, 0.7+ for somewhat clear, 0.5+ for uncertain

        CRITICAL FIELDS (MUST extract if visible):
        - **TOTALS ARE CRITICAL**: Total Assets, Total Equity, Total Liabilities
        - **TOTALS ARE CRITICAL**: Total Current Assets, Total Non-Current Assets
        - **TOTALS ARE CRITICAL**: Total Current Liabilities, Total Non-Current Liabilities
        - Revenue, Cost of Sales, Gross Profit, Comprehensive / Net income
        - Cash and Cash Equivalents, Current Assets, Current Liabilities
        - Property, Plant and Equipment, Trade and Other Current Receivables
        
        CASH FLOW STATEMENT FIELDS (if present):
        - Cash flows from (used in) operating activities
        - Cash flows from (used in) investing activities  
        - Cash flows from (used in) financing activities
        - Net increase (decrease) in cash and cash equivalents

        Return format:
        {{
            "template_mappings": {{
                "Revenue": {{"value": 1000000, "confidence": 0.95, "Value_Year_1": 1000000, "Value_Year_2": 950000}},
                "Cost of Sales": {{"value": 800000, "confidence": 0.90, "Value_Year_1": 800000, "Value_Year_2": 750000}},
                "Total Assets": {{"value": 5000000, "confidence": 0.95, "Value_Year_1": 5000000, "Value_Year_2": 4800000}},
                "Total Equity": {{"value": 3000000, "confidence": 0.90, "Value_Year_1": 3000000, "Value_Year_2": 2800000}}
            }}
        }}

        MULTI-YEAR DATA HANDLING (CRITICAL):
        - Documents may have 2, 3, or even 4 years of comparative data
        - Look for year columns in the headers (e.g., "2023", "2022", "2021", "2020")
        - Extract values for ALL years present, up to 4 years
        - Use Value_Year_1 for MOST RECENT year, Value_Year_2 for next, Value_Year_3 for third, Value_Year_4 for fourth
        
        Examples:
        - 2 years: "Revenue  2022: 9,843,009  2021: 20,406,722"
          → {{"value": 9843009, "confidence": 0.95, "Value_Year_1": 9843009, "Value_Year_2": 20406722}}
        
        - 3 years: "Total Assets  2022: 500M  2021: 450M  2020: 400M"
          → {{"value": 500000000, "confidence": 0.95, "Value_Year_1": 500000000, "Value_Year_2": 450000000, "Value_Year_3": 400000000}}
        
        - 4 years: Include Value_Year_4 for the oldest year
        
        IMPORTANT - COMPLETE EXTRACTION:
        - Extract as many fields as possible, not just the priority ones
        - Extract ALL years visible in each row (don't stop at 2 years if you see 3 or 4)
        - If you see "Net Sales" or "Total Sales", map to "Revenue"
        - If you see "Cost of Goods Sold", map to "Cost of Sales"
        - If you see "Net Income" or "Profit", map to "Comprehensive / Net income"
        - Be thorough - extract everything you can see clearly
        - For cash flow statements, include Operating, Investing, and Financing activities
        - Always include multi-year data - check if there are 2, 3, or 4 year columns
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
    
    def extract_years_from_image(self, base64_image: str) -> Dict[str, Any]:
        """
        Extract year information from financial statement image.
        Uses a simple, focused prompt for high accuracy.
        
        Args:
            base64_image: Base64-encoded image data
            
        Returns:
            Dictionary with year data: {"years": [2023, 2022, 2021], "confidence": 0.95}
        """
        try:
            # Simple, focused prompt - enhanced for 3-4 years
            year_prompt = """What years are covered by this financial statement?

CRITICAL: Look for ALL years present - some documents have 2, 3, or even 4 years of data!

Look for years in:
- Document title/header (e.g., "For the Years 2022, 2021, and 2020")
- Column headers - scan the ENTIRE width of tables for year labels
- Table column headers showing multiple years (2023 | 2022 | 2021 | 2020)
- "Years Covered:", "As of December 31,", "For the year ended" phrases
- Comparative financial data - count the number of value columns

SCAN CAREFULLY:
- If you see 2 value columns → likely 2 years
- If you see 3 value columns → likely 3 years (extract all 3!)
- If you see 4 value columns → likely 4 years (extract all 4!)

Return ONLY a JSON object with ALL years found (most recent first):
{"years": [2023, 2022, 2021]}  // for 3 years
{"years": [2022, 2021, 2020, 2019]}  // for 4 years

Examples:
- 2 years: {"years": [2023, 2022]}
- 3 years: {"years": [2022, 2021, 2020]}
- 4 years: {"years": [2023, 2022, 2021, 2020]}

If no years found, return: {"years": []}

IMPORTANT: Return years in descending order (newest to oldest). Extract ALL years you see, not just the first 2!"""
            
            # Make API call with appropriate provider
            if self.provider == "openai":
                response = self._call_openai_api(base64_image, year_prompt)
            elif self.provider == "anthropic":
                response = self._call_anthropic_api(base64_image, year_prompt)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
            
            # Parse JSON response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                print(f"[WARN] No JSON found in year extraction response")
                return {"years": [], "confidence": 0.0, "source": "vision_extraction"}
            
            json_str = response[start_idx:end_idx]
            year_data = json.loads(json_str)
            
            # Validate and clean
            years = year_data.get('years', [])
            
            # Filter to valid years (1900-2100)
            years = [y for y in years if isinstance(y, int) and 1900 <= y <= 2100]
            
            # Sort descending (most recent first)
            years = sorted(years, reverse=True)
            
            # Limit to 4 years (template supports Value_Year_1 through Value_Year_4)
            years = years[:4]
            
            # Determine confidence based on number of years found
            confidence = 0.95 if len(years) >= 2 else (0.8 if len(years) == 1 else 0.0)
            
            return {
                "years": years,
                "confidence": confidence,
                "source": "vision_extraction"
            }
            
        except json.JSONDecodeError as e:
            print(f"[WARN] Failed to parse year extraction response: {e}")
            return {"years": [], "confidence": 0.0, "source": "vision_extraction"}
            
        except Exception as e:
            print(f"[WARN] Year extraction error: {e}")
            return {"years": [], "confidence": 0.0, "source": "vision_extraction"}
    
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
