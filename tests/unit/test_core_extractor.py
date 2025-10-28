"""
Unit tests for the core financial data extractor.
"""

import pytest
import base64
import json
from unittest.mock import Mock, patch, MagicMock
from core.extractor import FinancialDataExtractor
from core.config import Config


class TestCoreExtractor:
    """Test cases for the FinancialDataExtractor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = FinancialDataExtractor()
        self.sample_image_data = b"fake_image_data"
        self.sample_base64 = base64.b64encode(self.sample_image_data).decode('utf-8')
    
    def test_init(self):
        """Test extractor initialization"""
        extractor = FinancialDataExtractor()
        # Check that at least one client is available
        assert extractor.anthropic_client is not None or extractor.openai_client is not None
        assert extractor.config is not None
        assert isinstance(extractor.config, Config)
    
    def test_encode_image_with_file_like_object(self):
        """Test image encoding with file-like object"""
        mock_file = Mock()
        mock_file.read.return_value = self.sample_image_data
        
        result = self.extractor.encode_image(mock_file)
        expected = base64.b64encode(self.sample_image_data).decode('utf-8')
        
        assert result == expected
        mock_file.read.assert_called_once()
    
    def test_encode_image_with_bytes(self):
        """Test image encoding with bytes data"""
        result = self.extractor.encode_image(self.sample_image_data)
        expected = base64.b64encode(self.sample_image_data).decode('utf-8')
        
        assert result == expected
    
    def test_build_extraction_prompt(self):
        """Test prompt building for different statement types"""
        # Test balance sheet prompt
        prompt = self.extractor._build_extraction_prompt("balance_sheet")
        assert "balance_sheet" in prompt
        assert "EXTRACTION RULES" in prompt
        assert "template fields" in prompt
        
        # Test income statement prompt
        prompt = self.extractor._build_extraction_prompt("income_statement")
        assert "income_statement" in prompt
        
        # Test cash flow prompt
        prompt = self.extractor._build_extraction_prompt("cash_flow")
        assert "cash_flow" in prompt
    
    @patch('core.extractor.FinancialDataExtractor._call_anthropic_api')
    def test_extract_comprehensive_financial_data_success(self, mock_api):
        """Test successful financial data extraction"""
        # Mock API response - return a JSON string directly
        mock_api.return_value = json.dumps({
            "statement_type": "Balance Sheet",
            "company_name": "Test Company",
            "years_detected": ["2024", "2023"],
            "line_items": {
                "current_assets": {
                    "cash": {"value": 1000000, "confidence": 0.95}
                }
            }
        })
        
        result = self.extractor.extract_comprehensive_financial_data(
            self.sample_base64, "balance_sheet"
        )
        
        assert result["statement_type"] == "Balance Sheet"
        assert result["company_name"] == "Test Company"
        assert result["years_detected"] == ["2024", "2023"]
        assert "processing_method" in result
        assert "timestamp" in result
    
    @patch('core.extractor.FinancialDataExtractor._call_anthropic_api')
    def test_extract_comprehensive_financial_data_empty_response(self, mock_api):
        """Test handling of empty API response"""
        mock_api.return_value = ""
        
        with pytest.raises(Exception, match="Empty response from AI model"):
            self.extractor.extract_comprehensive_financial_data(
                self.sample_base64, "balance_sheet"
            )
    
    @patch('core.extractor.FinancialDataExtractor._call_anthropic_api')
    def test_extract_comprehensive_financial_data_invalid_json(self, mock_api):
        """Test handling of invalid JSON response"""
        mock_api.return_value = "Invalid JSON response"
        
        with pytest.raises(Exception, match="No valid JSON found in AI response"):
            self.extractor.extract_comprehensive_financial_data(
                self.sample_base64, "balance_sheet"
            )
    
    def test_exponential_backoff_retry_success(self):
        """Test successful retry logic"""
        mock_func = Mock()
        mock_func.return_value = "success"
        
        result = self.extractor.exponential_backoff_retry(mock_func)
        
        assert result == "success"
        mock_func.assert_called_once()
    
    def test_exponential_backoff_retry_rate_limit(self):
        """Test retry logic with rate limiting"""
        mock_func = Mock()
        mock_func.side_effect = Exception("429 rate limit exceeded")
        
        with pytest.raises(Exception, match="429 rate limit exceeded"):
            self.extractor.exponential_backoff_retry(mock_func, max_retries=1)
    
    def test_exponential_backoff_retry_non_rate_limit_error(self):
        """Test retry logic with non-rate-limit error"""
        mock_func = Mock()
        mock_func.side_effect = Exception("Other error")
        
        with pytest.raises(Exception, match="Other error"):
            self.extractor.exponential_backoff_retry(mock_func, max_retries=1)
    
    @patch('core.extractor.FinancialDataExtractor.extract_comprehensive_financial_data')
    def test_extract_from_image_success(self, mock_extract):
        """Test successful image extraction"""
        mock_extract.return_value = {"statement_type": "Balance Sheet"}
        
        result = self.extractor.extract_from_image(
            self.sample_image_data, "balance_sheet"
        )
        
        assert result["statement_type"] == "Balance Sheet"
        mock_extract.assert_called_once()
    
    def test_extract_from_image_error(self):
        """Test image extraction error handling"""
        with patch('core.extractor.FinancialDataExtractor.extract_comprehensive_financial_data') as mock_extract:
            mock_extract.side_effect = Exception("Extraction failed")
            
            with pytest.raises(Exception, match="Error extracting from image"):
                self.extractor.extract_from_image(
                    self.sample_image_data, "balance_sheet"
                )
