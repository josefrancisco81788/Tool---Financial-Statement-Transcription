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
        print(f"🔍 Extractor init - provider: {self.provider}")
        print(f"🔍 Extractor init - config AI_PROVIDER: {self.config.AI_PROVIDER}")
        print(f"🔍 Extractor init - ANTHROPIC_API_KEY length: {len(self.config.ANTHROPIC_API_KEY)}")
        print(f"🔍 Extractor init - OPENAI_API_KEY length: {len(self.config.OPENAI_API_KEY)}")
        
        # Initialize clients based on provider
        try:
            if self.provider == "openai":
                self.openai_client = openai_client or OpenAI(api_key=self.config.OPENAI_API_KEY)
                self.anthropic_client = None
                print("✅ OpenAI client created successfully")
            elif self.provider == "anthropic":
                self.openai_client = None
                self.anthropic_client = anthropic_client or anthropic.Anthropic(api_key=self.config.ANTHROPIC_API_KEY)
                print("✅ Anthropic client created successfully")
            else:
                raise ValueError(f"Unsupported AI provider: {self.provider}. Must be 'openai' or 'anthropic'")
        except Exception as e:
            print(f"❌ Client creation failed: {e}")
            raise
        
        print(f"🔍 Extractor init - has anthropic client: {hasattr(self, 'anthropic_client') and self.anthropic_client is not None}")
        print(f"🔍 Extractor init - has openai client: {hasattr(self, 'openai_client') and self.openai_client is not None}")
    
    def _load_template_fields(self) -> List[str]:
        """Load the 91 template fields for context"""
        try:
            # Single correct path - remove duplicate
            template_path = "tests/fixtures/templates/FS_Input_Template_Fields.csv"
            
            if not os.path.exists(template_path):
                print(f"⚠️ Template file not found at: {template_path}")
                print(f"Current working directory: {os.getcwd()}")
                return self._get_fallback_template_fields()
            
            df = pd.read_csv(template_path)
            template_fields = df['Field'].tolist()
            
            # Validate we have exactly 91 fields
            if len(template_fields) != 91:
                print(f"⚠️ Expected 91 fields, got {len(template_fields)}")
            else:
                print(f"✅ Loaded exactly {len(template_fields)} template fields from {template_path}")
            
            # Log first few fields for verification
            print(f"First 5 template fields: {template_fields[:5]}")
            
            return template_fields
            
        except Exception as e:
            print(f"❌ Error loading template fields: {e}")
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
            print(f"🔍 Using simplified prompt (first 500 chars): {prompt[:500]}...")
            
            # Make provider-specific API call with retry logic
            print(f"🔍 About to make API call with provider: {self.provider}")
            if self.provider == "openai":
                print("🔍 Using OpenAI endpoint")
                response = self._call_openai_api(base64_image, prompt)
            elif self.provider == "anthropic":
                print("🔍 Using Anthropic endpoint")
                response = self._call_anthropic_api(base64_image, prompt)
            else:
                print(f"❌ Unknown provider: {self.provider}")
                raise ValueError(f"Unknown provider: {self.provider}")
            
            print(f"🔍 API call completed with provider: {self.provider}")
            
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

        PRIORITY FIELDS (extract these if present):
        - Revenue, Cost of Sales, Gross Profit, Comprehensive / Net income
        - Total Assets, Total Equity, Total Liabilities
        - Cash and Cash Equivalents, Current Assets, Current Liabilities
        - Property, Plant and Equipment, Trade and Other Current Receivables

        Return format:
        {{
            "template_mappings": {{
                "Revenue": {{"value": 1000000, "confidence": 0.95, "Value_Year_1": 1000000, "Value_Year_2": 950000}},
                "Cost of Sales": {{"value": 800000, "confidence": 0.90, "Value_Year_1": 800000, "Value_Year_2": 750000}},
                "Total Assets": {{"value": 5000000, "confidence": 0.95, "Value_Year_1": 5000000, "Value_Year_2": 4800000}},
                "Total Equity": {{"value": 3000000, "confidence": 0.90, "Value_Year_1": 3000000, "Value_Year_2": 2800000}}
            }}
        }}

        MULTI-YEAR DATA HANDLING:
        - If you see multiple years (like 2022, 2021), extract values for each year
        - Use Value_Year_1 for the most recent year, Value_Year_2 for the previous year
        - Example: If you see "Revenue  2022: 9,843,009  2021: 20,406,722", extract:
          "Revenue": {{"value": 9843009, "confidence": 0.95, "Value_Year_1": 9843009, "Value_Year_2": 20406722}}

        IMPORTANT:
        - Extract as many fields as possible, not just the priority ones
        - If you see "Net Sales" or "Total Sales", map to "Revenue"
        - If you see "Cost of Goods Sold", map to "Cost of Sales"
        - If you see "Net Income" or "Profit", map to "Comprehensive / Net income"
        - Be thorough - extract everything you can see clearly
        - Always include multi-year data if present in the document
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
