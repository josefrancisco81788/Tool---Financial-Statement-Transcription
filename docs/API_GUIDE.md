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
- **Cloud Ready**: Optimized for Google Cloud Run deployment
- **RESTful API**: Simple HTTP endpoints with JSON responses

### Performance Characteristics
- **Year Coverage**: Consistently extracts all available years
- **Row Extraction**: 20-30+ financial line items per document
- **Processing Time**: ~30 seconds per page (parallel processing)
- **Reliability**: Built-in retry logic and error handling

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

# Usage
result = extract_financial_data("financial_statement.pdf", "your-api-key")
print(json.dumps(result, indent=2))
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
- **Small documents** (<5 pages): 15-30 seconds
- **Medium documents** (5-15 pages): 30-90 seconds  
- **Large documents** (>15 pages): 90-300 seconds

## 🔄 Version History

### v1.0.0 (Current)
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

*Last updated: January 2025*
