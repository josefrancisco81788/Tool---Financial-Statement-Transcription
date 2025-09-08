# 🚀 Financial Statement Transcription API Guide

A comprehensive guide for using the Financial Statement Transcription API - a cloud-ready service for extracting financial data from PDF documents and images using AI-powered analysis.

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Request/Response Formats](#requestresponse-formats)
- [Error Handling](#error-handling)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Deployment](#deployment)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## 🌟 Overview

The Financial Statement Transcription API provides programmatic access to our AI-powered financial data extraction capabilities. Built on the proven `alpha-testing-v1` foundation, it offers:

### Key Features
- **Multi-format Support**: PDF files, PNG, JPG, JPEG images
- **AI-Powered Extraction**: OpenAI GPT-4 Vision for intelligent data recognition
- **Multi-year Support**: Handles comparative financial statements (2024, 2023, 2022, etc.)
- **High Accuracy**: Proven extraction logic with consistent year coverage
- **Standardized Output**: Template CSV format matching `FS_Input_Template_Fields.csv`
- **Cloud Ready**: Optimized for Google Cloud Run deployment
- **RESTful API**: Simple HTTP endpoints with JSON responses

### Performance Characteristics
- **Year Coverage**: Consistently extracts all available years
- **Row Extraction**: 20-30+ financial line items per document
- **PDF Conversion**: 19-23 seconds for 3-page documents
- **Individual Image Processing**: 20-45 seconds per image
- **Total Processing**: 85-120 seconds for typical 3-page financial statements
- **Template Output**: 7,443 bytes for complete balance sheet data
- **Reliability**: Built-in retry logic and error handling

### Processing Architecture

#### Robust Individual Processing
The API uses a robust processing approach that handles each page individually to ensure maximum reliability:

- **Individual Image Processing**: Each PDF page is converted to an image and processed separately
- **Smart Statement Selection**: Automatically identifies and prioritizes Balance Sheet data over Operations or Equity statements
- **Fallback Processing**: Graceful handling of PDF library failures (pdf2image → PyMuPDF fallback)
- **Error Isolation**: Processing errors on one page don't affect other pages

#### Multi-Page Document Handling
- **Page-by-Page Analysis**: Each page is analyzed independently for optimal accuracy
- **Statement Type Detection**: Automatically identifies Financial Position, Operations, and Changes in Equity
- **Data Consolidation**: Combines results from multiple pages while maintaining data integrity
- **Template Mapping**: Maps extracted data to standardized template format

## 🚀 Quick Start

### Prerequisites
- API access credentials
- OpenAI API key (configured on server)
- HTTP client (curl, Postman, or your preferred tool)

### First API Call

```bash
curl -X POST "https://your-api-url.com/extract" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your-financial-statement.pdf" \
  -F "statement_type=balance_sheet"
```

### Response
```json
{
  "success": true,
  "data": {
    "statement_type": "Balance Sheet",
    "company_name": "Sample Company Inc.",
    "period": "December 31, 2024",
    "currency": "USD",
    "years_detected": ["2024", "2023"],
    "line_items": {
      "current_assets": {
        "cash_and_equivalents": {
          "value": 1000000,
          "confidence": 0.95,
          "2024": 1000000,
          "2023": 950000
        }
      }
    }
  },
  "processing_time": 45.2,
  "pages_processed": 3
}
```

## 🔌 API Endpoints

### Base URL
```
https://your-api-url.com
```

### Endpoints

#### 1. Extract Financial Data
**POST** `/extract`

Extract financial data from uploaded documents.

**Parameters:**
- `file` (required): PDF or image file
- `statement_type` (optional): Hint for statement type (`balance_sheet`, `income_statement`, `cash_flow`)

**Response:** JSON with extracted financial data

#### 2. Health Check
**GET** `/health`

Check API service status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

#### 3. API Documentation
**GET** `/docs`

Interactive API documentation (Swagger UI).

## 📊 Request/Response Formats

### Standardized CSV Output

The API now provides standardized CSV output that matches the `FS_Input_Template_Fields.csv` format, ensuring compatibility with financial analysis tools and databases.

#### Template Format Structure
```csv
Category,Subcategory,Field,Confidence,Confidence_Score,Value_Year_1,Value_Year_2,Value_Year_3,Value_Year_4
Meta,Reference,Year,High,0.95,2024,2023,,
Balance Sheet,Current Assets,Cash and Cash Equivalents,High,0.95,40506296,14011556,,
Balance Sheet,Current Assets,Trade and Other Current Receivables,High,0.95,93102625,102434862,,
```

#### Template Compliance Features
- **91 Standardized Fields**: Complete coverage of Balance Sheet, Income Statement, and Cash Flow categories
- **Multi-year Support**: Up to 4 years of comparative data
- **Confidence Scoring**: High/Medium confidence levels with numerical scores
- **Field Mapping**: Automatic mapping from extracted data to standardized field names
- **Empty Field Handling**: Unavailable fields left empty for clear data structure

#### Template Categories
- **Meta**: Document reference information (Year, Company, Period)
- **Balance Sheet**: Assets, Liabilities, Equity with subcategories
- **Income Statement**: Revenue, Expenses, Profit/Loss items
- **Cash Flow Statement**: Operating, Investing, Financing activities

### Request Format

#### File Upload
```bash
Content-Type: multipart/form-data

file: [binary file data]
statement_type: "balance_sheet"  # optional
```

#### Supported File Types
- **PDF**: `.pdf` (recommended for multi-page documents)
- **Images**: `.png`, `.jpg`, `.jpeg`

#### File Size Limits
- **Maximum**: 50MB
- **Recommended**: <10MB for optimal performance

### Response Format

#### Success Response
```json
{
  "success": true,
  "data": {
    "statement_type": "string",
    "company_name": "string",
    "period": "string",
    "currency": "string",
    "years_detected": ["string"],
    "base_year": "string",
    "year_ordering": "most_recent_first",
    "line_items": {
      "category_name": {
        "line_item_name": {
          "value": number,
          "confidence": number,
          "year_2024": number,
          "year_2023": number
        }
      }
    },
    "summary_metrics": {
      "total_assets": {"value": number, "confidence": number},
      "total_liabilities": {"value": number, "confidence": number},
      "total_equity": {"value": number, "confidence": number}
    },
    "document_structure": {
      "main_sections": ["string"],
      "line_item_count": number,
      "pages_analyzed": number
    }
  },
  "template_csv": "base64_encoded_csv_data",
  "template_fields_mapped": 20,
  "processing_time": number,
  "pages_processed": number,
  "timestamp": "ISO 8601 timestamp"
}
```

#### Error Response
```json
{
  "success": false,
  "error": {
    "code": "string",
    "message": "string",
    "details": "string"
  },
  "timestamp": "ISO 8601 timestamp"
}
```

## ❌ Error Handling

### Error Codes

| Code | Description | Action |
|------|-------------|---------|
| `INVALID_FILE` | Unsupported file type or corrupted file | Check file format and integrity |
| `FILE_TOO_LARGE` | File exceeds size limit | Reduce file size or split document |
| `PROCESSING_ERROR` | AI processing failed | Retry request or contact support |
| `JSON_PARSING_ERROR` | AI response parsing failed | Retry request or contact support |
| `CONSOLIDATION_ERROR` | Multi-page data consolidation failed | Retry request or contact support |
| `TEMPLATE_MAPPING_ERROR` | Field mapping to template format failed | Retry request or contact support |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Wait and retry with backoff |
| `AUTHENTICATION_ERROR` | Invalid credentials | Check API key |
| `SERVER_ERROR` | Internal server error | Retry request or contact support |

### Error Response Example
```json
{
  "success": false,
  "error": {
    "code": "PROCESSING_ERROR",
    "message": "Failed to extract financial data from document",
    "details": "AI processing timeout after 120 seconds"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🔐 Authentication

### API Key Authentication
Include your API key in the request header:

```bash
curl -X POST "https://your-api-url.com/extract" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### Environment Variables
For server-side integration:

```bash
export FINANCIAL_API_KEY="your-api-key-here"
export FINANCIAL_API_URL="https://your-api-url.com"
```

## ⚡ Rate Limiting

### Limits
- **Requests per minute**: 60
- **Requests per hour**: 1000
- **Concurrent requests**: 10

### Rate Limit Headers
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1642248600
```

### Rate Limit Exceeded Response
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please wait before retrying.",
    "details": "Limit: 60 requests per minute. Reset in 45 seconds."
  }
}
```

## 🚀 Deployment

### Google Cloud Run

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### Deploy Command
```bash
gcloud run deploy financial-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900
```

### Environment Variables
```bash
OPENAI_API_KEY=your-openai-key
LOG_LEVEL=INFO
MAX_FILE_SIZE=52428800  # 50MB
RATE_LIMIT_PER_MINUTE=60
```

## 💡 Examples

### Python Example
```python
import requests
import json
import base64
import csv
import io

def extract_financial_data(file_path, api_key):
    url = "https://your-api-url.com/extract"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    files = {
        "file": open(file_path, "rb")
    }
    
    data = {
        "statement_type": "balance_sheet"
    }
    
    response = requests.post(url, headers=headers, files=files, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API Error: {response.status_code} - {response.text}")

def save_template_csv(api_response, output_path):
    """Extract and save template CSV from API response"""
    if 'template_csv' in api_response:
        # Decode base64 CSV data
        csv_data = base64.b64decode(api_response['template_csv']).decode('utf-8')
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(csv_data)
        
        print(f"Template CSV saved to: {output_path}")
        print(f"Fields mapped: {api_response.get('template_fields_mapped', 0)}")
    else:
        print("No template CSV data in response")

# Usage
result = extract_financial_data("financial_statement.pdf", "your-api-key")
print(json.dumps(result, indent=2))

# Save template CSV
save_template_csv(result, "extracted_data.csv")
```

### Multi-Page Document Example
```python
import requests
import time

def process_multi_page_document(file_path, api_key):
    """Process a multi-page financial document with progress tracking"""
    url = "https://your-api-url.com/extract"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    files = {
        "file": open(file_path, "rb")
    }
    
    print(f"Processing {file_path}...")
    start_time = time.time()
    
    response = requests.post(url, headers=headers, files=files)
    
    if response.status_code == 200:
        result = response.json()
        processing_time = time.time() - start_time
        
        print(f"✅ Processing completed in {processing_time:.2f} seconds")
        print(f"📊 Pages processed: {result.get('pages_processed', 0)}")
        print(f"📋 Fields mapped: {result.get('template_fields_mapped', 0)}")
        print(f"🏢 Company: {result['data'].get('company_name', 'Unknown')}")
        print(f"📅 Years: {result['data'].get('years_detected', [])}")
        
        return result
    else:
        raise Exception(f"API Error: {response.status_code} - {response.text}")

# Usage
result = process_multi_page_document("multi_page_financial_statement.pdf", "your-api-key")
```

### JavaScript Example
```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function extractFinancialData(filePath, apiKey) {
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    form.append('statement_type', 'balance_sheet');
    
    try {
        const response = await axios.post('https://your-api-url.com/extract', form, {
            headers: {
                ...form.getHeaders(),
                'Authorization': `Bearer ${apiKey}`
            }
        });
        
        return response.data;
    } catch (error) {
        throw new Error(`API Error: ${error.response.status} - ${error.response.data}`);
    }
}

// Usage
extractFinancialData('financial_statement.pdf', 'your-api-key')
    .then(result => console.log(JSON.stringify(result, null, 2)))
    .catch(error => console.error(error));
```

### cURL Examples

#### Basic Extraction
```bash
curl -X POST "https://your-api-url.com/extract" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@balance_sheet.pdf" \
  -F "statement_type=balance_sheet"
```

#### Health Check
```bash
curl -X GET "https://your-api-url.com/health"
```

#### API Documentation
```bash
curl -X GET "https://your-api-url.com/docs"
```

## 🔧 Troubleshooting

### Common Issues

#### 1. File Upload Errors
**Problem**: "Invalid file type" error
**Solution**: Ensure file is PDF, PNG, JPG, or JPEG format

#### 2. Processing Timeouts
**Problem**: Request times out after 2 minutes
**Solution**: 
- Reduce file size
- Split large documents
- Check network connectivity

#### 3. Incomplete Data Extraction
**Problem**: Missing years or line items
**Solution**:
- Ensure document has clear financial data
- Try different statement_type hint
- Check document quality and resolution

#### 4. Rate Limit Issues
**Problem**: "Rate limit exceeded" errors
**Solution**:
- Implement exponential backoff
- Reduce request frequency
- Consider upgrading API plan

#### 5. JSON Parsing Errors
**Problem**: "JSON_PARSING_ERROR" - AI response parsing failed
**Solution**:
- Retry the request (temporary AI response issue)
- Check document quality and resolution
- Ensure document contains clear financial data
- Contact support if issue persists

#### 6. Consolidation Errors
**Problem**: "CONSOLIDATION_ERROR" - Multi-page data consolidation failed
**Solution**:
- Retry the request (temporary processing issue)
- Split large documents into smaller sections
- Check if all pages contain readable financial data
- Use individual page processing if available

#### 7. Template Mapping Errors
**Problem**: "TEMPLATE_MAPPING_ERROR" - Field mapping to template format failed
**Solution**:
- Retry the request (temporary mapping issue)
- Check if document follows standard financial statement format
- Verify document contains recognizable financial line items
- Contact support with document sample if issue persists

### Debug Mode
Enable debug logging by setting environment variable:
```bash
LOG_LEVEL=DEBUG
```

### Support
For technical support:
- Check API status: `GET /health`
- Review error messages and codes
- Contact support with request ID and error details

## 📈 Performance Tips

### Optimization Recommendations
1. **File Size**: Keep files under 10MB for best performance
2. **Image Quality**: Use high-resolution images for better OCR
3. **Document Structure**: Well-formatted financial statements extract better
4. **Batch Processing**: Use parallel requests for multiple documents
5. **Caching**: Cache results for repeated processing of same documents

### Expected Performance
- **Small documents** (1-2 pages): 40-65 seconds
- **Medium documents** (3-5 pages): 85-120 seconds  
- **Large documents** (6+ pages): 120-300 seconds

### Performance Breakdown
- **PDF Conversion**: 19-23 seconds for 3-page documents
- **Individual Image Processing**: 20-45 seconds per image
- **Template CSV Generation**: <1 second
- **Total Processing**: Varies by document size and complexity

## 🧪 Testing & Validation

### Test Files Available
The API includes comprehensive test files for validation and benchmarking:

#### Light Test Files (Recommended for Testing)
- **AFS2024 - statement extracted.pdf**: 3-page financial statement with Balance Sheet, Operations, and Equity
- **afs-2021-2023 - statement extracted.pdf**: Multi-year comparative statement
- **AFS-2022 - statement extracted.pdf**: Single-year financial statement
- **2021 AFS with SEC Stamp - statement extracted.pdf**: SEC-filed financial statement

#### Origin Test Files (Full Documents)
- **AFS2024.pdf**: Complete annual financial statement
- **afs-2021-2023.pdf**: Multi-year complete document
- **AFS-2022.pdf**: Complete single-year document
- **2021 AFS with SEC Stamp.pdf**: Complete SEC-filed document

### Expected Test Results

#### AFS2024 Test Results (Benchmark)
- **Processing Time**: 85-120 seconds
- **Pages Processed**: 3
- **Fields Extracted**: 21/32 (65.6% extraction rate)
- **Template Compliance**: 100% format match
- **Confidence Scores**: 0.95 (High) for all mapped fields
- **Years Detected**: 2024, 2023
- **Output Size**: 7,443 bytes (template CSV)

#### Performance Benchmarks
| Document Type | Pages | Processing Time | Extraction Rate | Success Rate |
|---------------|-------|-----------------|-----------------|--------------|
| Light Files | 1-3 | 40-120s | 11.8-65.6% | 100% |
| Origin Files | 3-10 | 120-300s | TBD | 95%+ |

### Template Compliance Verification
All test files produce output that:
- ✅ Matches `FS_Input_Template_Fields.csv` format exactly
- ✅ Includes proper Category, Subcategory, Field structure
- ✅ Provides confidence scores and multi-year data
- ✅ Handles empty fields gracefully
- ✅ Maintains data integrity across all financial categories

### Running Tests
```bash
# Test individual file
python tests/extract_afs2024_to_template_csv.py

# Run field extraction analysis (PRIMARY METRIC)
python tests/analyze_field_extraction_accuracy.py

# Run comprehensive test suite
python tests/test_api_enhanced.py --file "AFS2024 - statement extracted.pdf"

# Test all light files
python tests/test_api_enhanced.py --category light
```

## 🔄 Version History

### v1.1.0 (Current)
- **Standardized CSV Output**: Template format matching `FS_Input_Template_Fields.csv`
- **Robust Individual Processing**: Page-by-page processing for maximum reliability
- **Smart Statement Selection**: Automatic identification of Balance Sheet vs Operations vs Equity
- **Enhanced Error Handling**: New error codes for JSON parsing, consolidation, and template mapping
- **Improved Performance**: Optimized processing with real-world benchmarks
- **Template Compliance**: 91 standardized fields with multi-year support
- **Fallback Processing**: Graceful handling of PDF library failures (pdf2image → PyMuPDF)
- **Comprehensive Testing**: Full test suite with performance benchmarks

### v1.0.0
- Initial API release
- Based on proven alpha-testing-v1 extraction logic
- Multi-year financial statement support
- Cloud Run deployment ready
- Comprehensive error handling

---

## 📞 Support & Contact

- **API Documentation**: `/docs` endpoint
- **Health Status**: `/health` endpoint
- **Technical Support**: Contact your API provider
- **Feature Requests**: Submit through your API provider

---

*Last updated: January 2025 - v1.1.0*
