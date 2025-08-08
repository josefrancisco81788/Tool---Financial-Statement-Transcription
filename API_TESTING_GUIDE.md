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

### Upload a File (Synchronous - Small files < 5MB)
```bash
curl -X POST "http://localhost:8000/api/v1/extract-financial-data/sync" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_file.pdf" \
  -F "processing_approach=auto" \
  -F "output_format=csv"
```

### Upload a File (Asynchronous - Large files >= 5MB)
```bash
curl -X POST "http://localhost:8000/api/v1/extract-financial-data" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_file.pdf" \
  -F "processing_approach=auto" \
  -F "output_format=csv"
```

### Check Job Status (for async jobs)
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
  "pages_processed": 4,
  "output_format": "csv",
  "csv_data": "Statement,Category,Line_Item,Value,Confidence...",
  "document_characteristics": {
    "page_count": 4,
    "file_size_mb": 2.1,
    "recommendation": "whole_document"
  }
}
```

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
- `"auto"` - Let AI choose the best approach
- `"whole_document"` - Process entire document at once
- `"vector_database"` - Use vector search for large documents

### Output Formats
- `"csv"` - Structured CSV data
- `"json"` - Raw JSON data
- `"both"` - Both CSV and JSON

## 📁 Supported File Types

- **PDF** (.pdf) - Multi-page documents
- **Images** (.jpg, .jpeg, .png) - Single page documents
- **Max Size**: 10MB per file

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

2. **File Too Large**
   ```
   Error: File too large. Maximum size is 10MB
   Solution: Use a smaller file or compress it
   ```

3. **Invalid File Type**
   ```
   Error: Unsupported file type
   Solution: Use PDF, JPG, JPEG, or PNG files
   ```

4. **OpenAI API Key Missing**
   ```
   Error: OpenAI API key not found
   Solution: Set OPENAI_API_KEY environment variable
   ```

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export DEBUG=true
```

## 📈 Performance Tips

1. **Small Files (< 5MB)**: Use sync endpoint for immediate results
2. **Large Files (>= 5MB)**: Use async endpoint with job tracking
3. **Multiple Files**: Process sequentially to avoid rate limits
4. **Image Quality**: Use high-quality images for better OCR results

## 🎯 Next Steps

1. **Test with Real Data**: Upload actual financial statements
2. **Integrate into Applications**: Use the API in your projects
3. **Add Authentication**: Implement API key authentication
4. **Deploy to Production**: Host the API on cloud platforms
5. **Monitor Performance**: Track processing times and success rates

---

**Happy Testing! 🚀** 