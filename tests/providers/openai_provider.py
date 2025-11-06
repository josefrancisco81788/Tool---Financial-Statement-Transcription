"""
OpenAI test provider for unified testing pipeline
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


class OpenAITestProvider(BaseTestProvider):
    """OpenAI test provider"""
    
    def __init__(self):
        super().__init__("openai")
        self.extractor = None
        self.pdf_processor = None
    
    def validate_configuration(self) -> bool:
        """Validate OpenAI configuration and health"""
        try:
            # Set environment variable
            self._set_environment_variable("openai")
            
            # Initialize extractor
            self.extractor = FinancialDataExtractor()
            self.pdf_processor = PDFProcessor(self.extractor)
            
            # Check if provider is correctly set
            if self.extractor.provider != "openai":
                print(f"   ❌ Provider not set correctly: {self.extractor.provider}")
                return False
            
            # Check API key
            if not self.extractor.config.OPENAI_API_KEY:
                print("   ❌ OPENAI_API_KEY not found")
                return False
            
            print(f"   ✅ OpenAI provider validated: {self.extractor.config.OPENAI_MODEL}")
            return True
            
        except Exception as e:
            print(f"   ❌ OpenAI validation failed: {e}")
            return False
    
    def test_document(self, document_path: str, timeout: int = 300) -> TestResult:
        """Test a single document with OpenAI"""
        start_time = time.time()
        
        try:
            # Set environment variable
            self._set_environment_variable("openai")
            
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
                # Try to parse as JSON to check for actual financial data
                try:
                    import json
                    parsed_data = json.loads(extracted_data)
                    
                    # Check if we have actual financial fields
                    has_financial_data = False
                    if isinstance(parsed_data, dict):
                        # Look for financial statement sections
                        financial_keys = ['balance_sheet', 'income_statement', 'cash_flow', 'financial_data', 'current_assets', 'revenues']
                        for key in financial_keys:
                            if key in parsed_data and parsed_data[key]:
                                has_financial_data = True
                                break
                    
                    if has_financial_data:
                        return self._create_test_result(
                            document=document_path,
                            success=True,
                            extracted_data=extracted_data,
                            processing_time=processing_time,
                            extracted_fields=parsed_data if isinstance(parsed_data, dict) else {},
                            api_calls_made=8,  # Estimate based on processing
                            pages_processed=4  # Estimate based on document
                        )
                    else:
                        return self._create_test_result(
                            document=document_path,
                            success=False,
                            error_message="No meaningful financial data extracted",
                            processing_time=processing_time,
                            extracted_data=extracted_data
                        )
                        
                except json.JSONDecodeError:
                    # If not JSON, check if it contains financial keywords
                    financial_keywords = ['assets', 'liabilities', 'revenue', 'income', 'cash flow', 'balance sheet']
                    has_keywords = any(keyword in extracted_data.lower() for keyword in financial_keywords)
                    
                    if has_keywords:
                        return self._create_test_result(
                            document=document_path,
                            success=True,
                            extracted_data=extracted_data,
                            processing_time=processing_time,
                            api_calls_made=8,
                            pages_processed=4
                        )
                    else:
                        return self._create_test_result(
                            document=document_path,
                            success=False,
                            error_message="No financial data detected in response",
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
