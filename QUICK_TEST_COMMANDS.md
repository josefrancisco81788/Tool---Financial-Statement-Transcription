# 🚀 Quick Test Commands for Real-World Documents

## 📋 Method 1: Python Script (Recommended)

```bash
# Test with any PDF or image file
python test_real_file.py your_financial_statement.pdf

# Test with image file
python test_real_file.py screenshot.png

# Test with JSON output instead of CSV
python test_real_file.py document.pdf --output-format json
```

## 📋 Method 2: cURL Commands

### Test Health Check
```bash
curl http://localhost:8000/
```

### Upload Small File (< 5MB) - Immediate Results
```bash
curl -X POST "http://localhost:8000/api/v1/extract-financial-data/sync" \
  -F "file=@your_document.pdf" \
  -F "processing_approach=auto" \
  -F "output_format=csv"
```

### Upload Large File (>= 5MB) - Background Processing
```bash
curl -X POST "http://localhost:8000/api/v1/extract-financial-data" \
  -F "file=@large_document.pdf" \
  -F "processing_approach=auto" \
  -F "output_format=csv"
```

### Check Job Status (for large files)
```bash
curl http://localhost:8000/api/v1/jobs/{job_id_from_previous_response}
```

## 📋 Method 3: Web Interface

Visit: **http://localhost:8000/docs**

- Interactive API documentation
- Upload files directly through browser
- See request/response schemas
- Test all endpoints

## 📋 Method 4: Simple Python Script

```python
import requests

# Upload your file
with open('your_document.pdf', 'rb') as f:
    files = {'file': ('your_document.pdf', f, 'application/pdf')}
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
        print("Success!")
        if 'csv_data' in result:
            with open('extracted_data.csv', 'w') as f:
                f.write(result['csv_data'])
            print("CSV saved to extracted_data.csv")
    else:
        print(f"Error: {response.text}")
```

## 🔧 Processing Options

### Processing Approaches
- `auto` - Let AI choose best approach
- `whole_document` - Process entire document at once  
- `vector_database` - Use vector search for large documents

### Output Formats
- `csv` - Structured CSV data
- `json` - Raw JSON data
- `both` - Both CSV and JSON

## 📁 Supported File Types

- **PDF** (.pdf) - Multi-page documents
- **Images** (.jpg, .jpeg, .png) - Single page documents
- **Max Size**: 10MB per file

## 🎯 Quick Start Steps

1. **Start the API** (if not running):
   ```bash
   cd api
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Test with your document**:
   ```bash
   python test_real_file.py your_document.pdf
   ```

3. **Check results**:
   - CSV file will be saved as `extracted_data_TIMESTAMP.csv`
   - JSON file will be saved as `extracted_data_TIMESTAMP.json`

## 🔍 Troubleshooting

### API Not Running
```bash
# Start the API
cd api && uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### File Too Large
- Compress the file or use a smaller version
- Use the async endpoint for files >= 5MB

### OpenAI API Key Missing
```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

---

**Ready to test with your real documents! 🚀** 