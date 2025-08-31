# 🧪 Cloud Run API Testing Guide - Multi-Year Issue Resolution

## 🎯 Objective
Test the Cloud Run API with "AFS2024 - statement extracted.pdf" to verify if the multi-year data extraction issue has been resolved.

## 📋 Prerequisites

1. **Cloud Run Service URL**: Your deployed Cloud Run service URL
2. **Test File**: "AFS2024 - statement extracted.pdf" in the current directory
3. **Python Dependencies**: `requests` library installed

## 🚀 Quick Start

### Step 1: Get Your Cloud Run URL
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to Cloud Run
3. Find your service and copy the URL (format: `https://your-service-name-xxxxx-uc.a.run.app`)

### Step 2: Update Test Scripts
Edit either test script and replace the placeholder URL:

**For Python script (`test_cloudrun_afs2024.py`):**
```python
CLOUD_RUN_URL = "https://your-actual-cloud-run-url.run.app"
```

**For Shell script (`test_cloudrun_curl.sh`):**
```bash
CLOUD_RUN_URL="https://your-actual-cloud-run-url.run.app"
```

### Step 3: Run the Test

**Option A: Python Script (Recommended)**
```bash
python test_cloudrun_afs2024.py
```

**Option B: Shell Script**
```bash
./test_cloudrun_curl.sh
```

## 📊 What the Test Does

### 1. Health Check
- Verifies the Cloud Run API is accessible
- Tests basic connectivity

### 2. File Upload & Processing
- Uploads "AFS2024 - statement extracted.pdf"
- Uses synchronous processing endpoint
- Requests both CSV and JSON output formats

### 3. Multi-Year Analysis
- Analyzes CSV headers for year-related columns
- Checks for multiple year data in the extracted results
- Examines JSON structure for year fields
- Reports processing approach used

### 4. Results Storage
- Saves CSV data to timestamped file
- Saves JSON data to timestamped file
- Saves full API response for detailed analysis

## 🔍 Expected Results for Multi-Year Issue Resolution

### ✅ Success Indicators (Updated)
**ALL of the following must be true:**

1. **Column Structure**: CSV header contains `Value_Year_1, Value_Year_2, Value_Year_3, Value_Year_4`
2. **Year Mapping Row**: Second row shows `Date,Year,Year,,0.0,2024,2023,,`
3. **Data Completeness**: All financial values present (no empty cells where data should exist)
4. **Row Integrity**: No empty rows between data rows
5. **Multi-Year Data**: Values present in both `Value_Year_1` and `Value_Year_2` columns

**Reference**: See `CSV_FORMAT_SPECIFICATION.md` for complete success criteria.

### 📊 Expected CSV Format
```csv
Category,Subcategory,Field,Confidence,Confidence_Score,Value_Year_1,Value_Year_2,Value_Year_3,Value_Year_4
Date,Year,Year,,0.0,2024,2023,,
Balance Sheet,Current Assets,Cash And Equivalents,95.0%,0.95,40506296,14011556,,
```

**Key Points:**
- ✅ **Value_Year_X columns** are correct and should not be changed
- ✅ **Year mapping row** (second row) shows which years each column represents
- ✅ **Scalable format** works for any number of years

### ❌ Failure Indicators
- **Single Year Only**: Only one year of data extracted
- **Missing Years**: Years mentioned in document not captured
- **Processing Errors**: API errors or timeouts
- **Empty Results**: No data extracted

## 📁 Output Files

After running the test, you'll get:

1. **`afs2024_extracted_data_YYYYMMDD_HHMMSS.csv`** - Structured CSV data
2. **`afs2024_extracted_data_YYYYMMDD_HHMMSS.json`** - Raw JSON data
3. **`afs2024_full_response_YYYYMMDD_HHMMSS.json`** - Complete API response

## 🔧 Troubleshooting

### Common Issues

1. **Cloud Run URL Not Found**
   ```
   ❌ Cannot connect to Cloud Run API
   Solution: Verify your Cloud Run URL is correct
   ```

2. **File Not Found**
   ```
   ❌ File not found: AFS2024 - statement extracted.pdf
   Solution: Ensure the file is in the current directory
   ```

3. **Request Timeout**
   ```
   ❌ Request timed out
   Solution: The file might be too large for synchronous processing
   ```

4. **API Key Issues**
   ```
   ❌ OpenAI API key not found
   Solution: Ensure Cloud Run has access to OpenAI API key
   ```

### Debug Mode

For detailed debugging, check the full response file:
```bash
cat afs2024_full_response_*.json
```

## 📈 Manual Testing

### Using cURL
```bash
curl -X POST "https://your-cloud-run-url.run.app/api/v1/extract-financial-data/sync" \
  -F "file=@AFS2024 - statement extracted.pdf" \
  -F "processing_approach=auto" \
  -F "output_format=both"
```

### Using Web Interface
1. Visit your Cloud Run URL in a browser
2. Navigate to `/docs` for interactive API documentation
3. Upload the file through the web interface

## 🎯 Multi-Year Issue Verification Checklist

- [ ] API successfully processes AFS2024 file
- [ ] Multiple years of data are extracted
- [ ] CSV contains year mapping row (second row shows years)
- [ ] CSV contains Value_Year_X columns (DO NOT change these names)
- [ ] JSON contains year-related fields
- [ ] Processing time is reasonable (< 5 minutes)
- [ ] No data loss between years
- [ ] Financial data accuracy maintained

## 📊 CSV Format Validation

### ✅ Correct Format
```csv
Category,Subcategory,Field,Confidence,Confidence_Score,Value_Year_1,Value_Year_2,Value_Year_3,Value_Year_4
Date,Year,Year,,0.0,2024,2023,,
[Financial data rows...]
```

### ❌ Common Mistakes
- Changing `Value_Year_X` to `Value_2024`, `Value_2023`
- Missing year mapping row
- Incorrect year data placement

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the full response JSON file
3. Verify Cloud Run service is running
4. Check Cloud Run logs for errors

---

**Happy Testing! 🚀**
