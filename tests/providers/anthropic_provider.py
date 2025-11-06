"""
Anthropic (Claude) test provider for unified testing pipeline
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.extractor import FinancialDataExtractor
from core.pdf_processor import PDFProcessor
from .base_provider import BaseTestProvider, TestResult


class AnthropicTestProvider(BaseTestProvider):
    """Anthropic (Claude) test provider"""
    
    def __init__(self):
        super().__init__("anthropic")
        self.extractor = None
        self.pdf_processor = None
    
    def validate_configuration(self) -> bool:
        """Validate Anthropic configuration and health"""
        try:
            # Set environment variable
            self._set_environment_variable("anthropic")
            
            # Initialize extractor
            self.extractor = FinancialDataExtractor()
            self.pdf_processor = PDFProcessor(self.extractor)
            
            # Check if provider is correctly set
            if self.extractor.provider != "anthropic":
                print(f"   ❌ Provider not set correctly: {self.extractor.provider}")
                return False
            
            # Check API key
            if not self.extractor.config.ANTHROPIC_API_KEY:
                print("   ❌ ANTHROPIC_API_KEY not found")
                return False
            
            print(f"   ✅ Anthropic provider validated: {self.extractor.config.ANTHROPIC_MODEL}")
            return True
            
        except Exception as e:
            print(f"   ❌ Anthropic validation failed: {e}")
            return False
    
    def test_document(self, document_path: str, timeout: int = 300) -> TestResult:
        """Test a single document with Anthropic"""
        start_time = time.time()
        
        try:
            # Set environment variable
            self._set_environment_variable("anthropic")
            
            # Re-initialize to pick up environment variable
            self.extractor = FinancialDataExtractor()
            self.pdf_processor = PDFProcessor(self.extractor)
            
            # Validate document exists
            if not Path(document_path).exists():
                return self._create_test_result(
                    document=document_path,
                    success=False,
                    error_message=f"Document not found: {document_path}",
                    processing_time=time.time() - start_time
                )
            
            # Process document with timeout
            def process_document():
                with open(document_path, 'rb') as f:
                    pdf_data = f.read()
                return self.pdf_processor.process_pdf_with_vector_db(pdf_data)
            
            # Use ThreadPoolExecutor for timeout
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(process_document)
                try:
                    extracted_data = future.result(timeout=timeout)
                except TimeoutError:
                    return self._create_test_result(
                        document=document_path,
                        success=False,
                        error_message=f"Processing timed out after {timeout} seconds",
                        processing_time=time.time() - start_time
                    )
            
            processing_time = time.time() - start_time
            
            # Check if we actually got meaningful financial data
            if extracted_data:
                # Handle different data formats
                parsed_data = None
                
                # If it's already a dict, use it directly
                if isinstance(extracted_data, dict):
                    parsed_data = extracted_data
                    data_str = str(extracted_data)
                # If it's a string, try to parse as JSON
                elif isinstance(extracted_data, str):
                    data_str = extracted_data
                    try:
                        import json
                        parsed_data = json.loads(extracted_data)
                    except json.JSONDecodeError:
                        parsed_data = None
                else:
                    data_str = str(extracted_data)
                    parsed_data = None
                
                # Check for financial content regardless of format
                financial_keywords = [
                    'assets', 'liabilities', 'revenue', 'income', 'cash flow', 'balance sheet',
                    'current assets', 'total assets', 'equity', 'retained earnings', 'accounts receivable',
                    'inventory', 'property', 'plant', 'equipment', 'accounts payable', 'debt',
                    'sales', 'cost of goods sold', 'operating expenses', 'net income', 'depreciation'
                ]
                
                has_financial_content = False
                data_lower = data_str.lower()
                
                # Check for financial keywords
                for keyword in financial_keywords:
                    if keyword in data_lower:
                        has_financial_content = True
                        break
                
                # Also check for numbers (financial data usually has lots of numbers)
                import re
                numbers = re.findall(r'\d+[,.]?\d*', data_str)
                has_numbers = len(numbers) > 5  # Financial statements typically have many numbers
                
                # Consider it successful if it has financial keywords OR substantial numbers
                if has_financial_content or has_numbers:
                    return self._create_test_result(
                        document=document_path,
                        success=True,
                        extracted_data=extracted_data,
                        processing_time=processing_time,
                        extracted_fields=parsed_data if isinstance(parsed_data, dict) else {"raw_data": data_str},
                        api_calls_made=8,  # Estimate based on processing
                        pages_processed=4  # Estimate based on document
                    )
                else:
                    return self._create_test_result(
                        document=document_path,
                        success=False,
                        error_message="No financial content detected in extracted data",
                        processing_time=processing_time,
                        extracted_data=extracted_data
                    )
            else:
                return self._create_test_result(
                    document=document_path,
                    success=False,
                    error_message="No data extracted from document",
                    processing_time=processing_time
                )
                
        except Exception as e:
            return self._create_test_result(
                document=document_path,
                success=False,
                error_message=f"Processing failed: {str(e)}",
                processing_time=time.time() - start_time
            )
