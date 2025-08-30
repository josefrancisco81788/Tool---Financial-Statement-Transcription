# 🧪 Financial Statement Transcription API - Testing Guide

## 🚀 Quick Start

### 1. Start the API
```bash
cd api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Test Methods

## 📋 Method 1: Interactive Web Interface

Visit the automatic API documentation:
- **URL**: http://localhost:8000/docs
- **Features**: 
  - Interactive testing interface
  - Try out endpoints directly
  - See request/response schemas
  - Upload files through web interface

## 📋 Method 2: Python Test Script

Use our automated test script:
```bash
python test_file_upload.py
```

This script will:
- ✅ Check if API is running
- 📁 List available files in directory
- 🚀 Upload and process files
- 📊 Display results
- 💾 Save CSV/JSON outputs

## 📋 Method 3: cURL Commands

### Test Health Check
```bash
curl http://localhost:8000/
```

### Upload a File (Synchronous - Recommended)
```bash
curl -X POST "http://localhost:8000/api/v1/extract-financial-data/sync" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_file.pdf" \
  -F "processing_approach=auto" \
  -F "output_format=csv"
```

### Check Job Status (only if using the non-sync endpoint)
```bash
curl http://localhost:8000/api/v1/jobs/{job_id}
```

## 📋 Method 4: Python Requests

### Simple File Upload
```python
import requests

# Upload file
with open('your_file.pdf', 'rb') as f:
    files = {'file': ('your_file.pdf', f, 'application/pdf')}
    data = {
        'processing_approach': 'auto',
        'output_format': 'csv'
    }
    
    response = requests.post(
        'http://localhost:8000/api/v1/extract-financial-data/sync',
        files=files,
        data=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("Success:", result)
    else:
        print("Error:", response.text)
```

## 📋 Method 5: JavaScript/Fetch

### Browser-based Upload
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('processing_approach', 'auto');
formData.append('output_format', 'csv');

fetch('http://localhost:8000/api/v1/extract-financial-data/sync', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('Success:', data);
    // Handle CSV data
    if (data.csv_data) {
        downloadCSV(data.csv_data, 'extracted_data.csv');
    }
})
.catch(error => {
    console.error('Error:', error);
});
```

## 📊 Expected Response Format

### Successful Response
```json
{
  "status": "success",
  "processing_time": 15.2,
  "processing_approach": "whole_document",
  "requested_processing_approach": "whole_document",
  "effective_processing_approach": "whole_document",
  "pages_processed": 4,
  "output_format": "csv",
  "csv_data": "Category,Subcategory,Field,Confidence,Confidence_Score,Value_Year_1,Value_Year_2,Value_Year_3,Value_Year_4\nDate,Year,Year,,0.0,2024,2023,,\nBalance Sheet,Current Assets,Cash And Equivalents,95.0%,0.95,40506296,14011556,,",
  "document_characteristics": {
    "page_count": 4,
    "file_size_mb": 2.1,
    "recommendation": "whole_document"
  }
}
```

## 📊 CSV Output Format Specification

### Correct Format (DO NOT CHANGE)
The API produces CSV files with the following structure:

**Header Row**: Standard column headers with `Value_Year_X` columns
**Year Mapping Row**: Shows which years each `Value_Year_X` represents
**Data Rows**: Financial data for each line item

Example:
```csv
Category,Subcategory,Field,Confidence,Confidence_Score,Value_Year_1,Value_Year_2,Value_Year_3,Value_Year_4
Date,Year,Year,,0.0,2024,2023,,
Balance Sheet,Current Assets,Cash And Equivalents,95.0%,0.95,40506296,14011556,,
```

### Why This Format?
- **Scalable**: Works for any number of years (1-4)
- **Consistent**: Same column structure regardless of years present
- **Clear**: Year mapping row shows exactly what each column represents
- **Standard**: Compatible with financial analysis tools

### Common Mistakes to Avoid
❌ **Don't change column names** from `Value_Year_X` to `Value_2024`, `Value_2023`
✅ **Do use the year mapping row** to understand what years the data represents

### Error Response
```json
{
  "error": "File processing failed: Invalid file format",
  "status": "failed",
  "processing_time": 0.5
}
```

## 🔧 Processing Options

### Processing Approaches
- `auto` - Let AI choose the best approach
- `whole_document` - Process entire document at once
- `vector_database` - Use vector search for large documents

### Output Formats
- `csv` - Structured CSV data
- `json` - Raw JSON data
- `both` - Both CSV and JSON

## 📁 Supported File Types

- **PDF** (.pdf) - Multi-page documents
- **Images** (.jpg, .jpeg, .png) - Single page documents

## 🧪 Sample Test Files

To test the API, you can use:

1. **Sample PDF**: Any financial statement PDF
2. **Sample Images**: Screenshots of financial data
3. **Test Files**: Create simple test documents

### Creating a Test File
```python
# Create a simple test PDF with financial data
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

c = canvas.Canvas("test_financial_statement.pdf", pagesize=letter)
c.drawString(100, 750, "Financial Statement")
c.drawString(100, 700, "Revenue: $1,000,000")
c.drawString(100, 650, "Expenses: $800,000")
c.drawString(100, 600, "Net Income: $200,000")
c.save()
```

## 🔍 Troubleshooting

### Common Issues

1. **API Not Running**
   ```
   Error: Connection refused
   Solution: Start the API with uvicorn
   ```

2. **OpenAI API Key Missing**
   ```
   Error: OpenAI API key not found
   Solution: Set OPENAI_API_KEY environment variable
   ```

3. **Excel shows blank lines**
   ```
   Use the CSV returned by the API directly. It uses CRLF line endings for Excel compatibility.
   ```

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export DEBUG=true
```

## 📈 POC Notes & Limits
- Synchronous processing; long documents may take several minutes and risk request timeouts depending on your platform.
- No authentication or rate limiting; restrict access in POC environments.
- In-memory job tracking is ephemeral; restarts clear job history.
- PDF processing depends on platform setup (Poppler or PyMuPDF available).

---

**Happy Testing! 🚀** 