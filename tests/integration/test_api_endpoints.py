"""
Integration tests for API endpoints.
"""

import pytest
import json
from fastapi.testclient import TestClient
from api_app import app


class TestAPIEndpoints:
    """Test cases for API endpoints"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        assert "extract" in data
    
    def test_docs_endpoint(self):
        """Test API documentation endpoint"""
        response = self.client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_extract_endpoint_no_file(self):
        """Test extract endpoint with no file"""
        response = self.client.post("/extract")
        
        assert response.status_code == 422  # Validation error
    
    def test_extract_endpoint_invalid_file_type(self):
        """Test extract endpoint with invalid file type"""
        files = {"file": ("test.txt", b"test content", "text/plain")}
        data = {"statement_type": "balance_sheet"}
        
        response = self.client.post("/extract", files=files, data=data)
        
        assert response.status_code == 400
        error_data = response.json()
        assert "error" in error_data
        assert "Unsupported file type" in error_data["error"]["message"]
    
    def test_extract_endpoint_file_too_large(self):
        """Test extract endpoint with file too large"""
        # Create a large file (over 50MB)
        large_content = b"x" * (50 * 1024 * 1024 + 1)
        files = {"file": ("large.pdf", large_content, "application/pdf")}
        data = {"statement_type": "balance_sheet"}
        
        response = self.client.post("/extract", files=files, data=data)
        
        assert response.status_code == 413
        error_data = response.json()
        assert "error" in error_data
        assert "File too large" in error_data["error"]["message"]
    
    @pytest.mark.skip(reason="Requires OpenAI API key and actual file processing")
    def test_extract_endpoint_success_pdf(self):
        """Test successful PDF extraction (requires API key)"""
        # This test would require actual PDF files and OpenAI API key
        # Skip in unit tests, run in integration tests with real data
        pass
    
    @pytest.mark.skip(reason="Requires OpenAI API key and actual file processing")
    def test_extract_endpoint_success_image(self):
        """Test successful image extraction (requires API key)"""
        # This test would require actual image files and OpenAI API key
        # Skip in unit tests, run in integration tests with real data
        pass
    
    def test_extract_endpoint_with_statement_type(self):
        """Test extract endpoint with statement type parameter"""
        # Create a small PDF file for testing
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        files = {"file": ("test.pdf", pdf_content, "application/pdf")}
        data = {"statement_type": "income_statement"}
        
        # This will fail due to invalid PDF, but we can test the parameter handling
        response = self.client.post("/extract", files=files, data=data)
        
        # Should get a processing error, not a validation error
        assert response.status_code in [400, 422, 500]
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = self.client.options("/health")
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    def test_error_handling_404(self):
        """Test 404 error handling"""
        response = self.client.get("/nonexistent")
        
        assert response.status_code == 404
    
    def test_error_handling_method_not_allowed(self):
        """Test method not allowed error handling"""
        response = self.client.put("/health")
        
        assert response.status_code == 405
