# Cloud Shell API Testing Guide

## Overview
This guide provides commands to test the Financial Statement Transcription API using the files available in your Cloud Shell home directory.

## Available Files
Based on your Cloud Shell directory, you have:
- `AFS2024 - statement extracted.pdf` - Main test file
- `extracted_data.csv` - Previous output (for comparison)
- `response.json` - Previous response (for comparison)
- `README-cloudshell.txt` - Cloud Shell instructions

## Cloud Shell Setup Commands

### 1. Install Required Tools
```bash
# Update package list
sudo apt-get update

# Install curl and jq for API testing
sudo apt-get install -y curl jq

# Install Python and pip if not already available
sudo apt-get install -y python3 python3-pip

# Install Python requests library
pip3 install requests
```

### 2. Set API URL
```bash
# Set the Cloud Run API URL
export API_URL="https://financial-statement-transcription-api-1027259334816.asia-southeast1.run.app"

# Verify the URL is set
echo "API URL: $API_URL"
```

## API Testing Commands

### 3. Test API Health
```bash
# Test if the API is accessible
curl -X GET "$API_URL/" --max-time 10

# Expected response: API information or health status
```

### 4. Test AFS2024 Multi-Year Extraction

#### 4.1 Basic CSV Test
```bash
# Test with AFS2024 file for CSV output
curl -X POST "$API_URL/api/v1/extract-financial-data/sync" \
  -F "file=@AFS2024 - statement extracted.pdf" \
  -F "processing_approach=auto" \
  -F "output_format=csv" \
  --max-time 300 \
  -o afs2024_test_response.json
```

#### 4.2 Both CSV and JSON Output
```bash
# Test with both CSV and JSON output
curl -X POST "$API_URL/api/v1/extract-financial-data/sync" \
  -F "file=@AFS2024 - statement extracted.pdf" \
  -F "processing_approach=auto" \
  -F "output_format=both" \
  --max-time 300 \
  -o afs2024_full_response.json
```

### 5. Analyze Results

#### 5.1 Check Response Structure
```bash
# View the response structure
jq 'keys' afs2024_full_response.json

# Check if CSV data is present
jq 'has("csv_data")' afs2024_full_response.json

# Check if JSON data is present
jq 'has("json_data")' afs2024_full_response.json
```

#### 5.2 Extract CSV Data
```bash
# Extract CSV data to a separate file
jq -r '.csv_data' afs2024_full_response.json > afs2024_extracted_data.csv

# View first few lines of CSV
head -10 afs2024_extracted_data.csv

# Check for year mapping row (should be line 2)
sed -n '2p' afs2024_extracted_data.csv
```

#### 5.3 Check Multi-Year Data
```bash
# Check if years are detected in JSON
jq '.json_data.years_detected' afs2024_full_response.json

# Check processing approach used
jq '.effective_processing_approach' afs2024_full_response.json

# Check pages processed
jq '.pages_processed' afs2024_full_response.json
```

### 6. Compare with Previous Results
```bash
# Compare with previous CSV output
echo "=== NEW CSV OUTPUT ==="
head -5 afs2024_extracted_data.csv

echo -e "\n=== PREVIOUS CSV OUTPUT ==="
head -5 extracted_data.csv

# Compare file sizes
echo -e "\n=== FILE SIZE COMPARISON ==="
ls -lh afs2024_extracted_data.csv extracted_data.csv
```

### 7. Test Different Processing Approaches

#### 7.1 Whole Document Approach
```bash
curl -X POST "$API_URL/api/v1/extract-financial-data/sync" \
  -F "file=@AFS2024 - statement extracted.pdf" \
  -F "processing_approach=whole_document" \
  -F "output_format=both" \
  --max-time 300 \
  -o afs2024_whole_document.json
```

#### 7.2 Vector Database Approach
```bash
curl -X POST "$API_URL/api/v1/extract-financial-data/sync" \
  -F "file=@AFS2024 - statement extracted.pdf" \
  -F "processing_approach=vector_database" \
  -F "output_format=both" \
  --max-time 300 \
  -o afs2024_vector_db.json
```

### 8. Success Indicators

#### 8.1 Check for Year Mapping Row
```bash
# This should show the year mapping row with actual years
echo "=== CHECKING YEAR MAPPING ROW ==="
sed -n '2p' afs2024_extracted_data.csv | grep -E "(2024|2023)"

# Expected output: Date,Year,Year,,0.0,2024,2023,,
```

#### 8.2 Check for Multi-Year Columns
```bash
# This should show Value_Year_X columns
echo "=== CHECKING HEADER ROW ==="
head -1 afs2024_extracted_data.csv | grep -o "Value_Year_[0-9]"

# Expected output: Value_Year_1 Value_Year_2 (etc.)
```

#### 8.3 Check for Multi-Year Data
```bash
# This should show data in multiple year columns
echo "=== CHECKING DATA ROWS ==="
tail -n +3 afs2024_extracted_data.csv | head -3 | cut -d',' -f6-8
```

### 9. Cleanup and Organization
```bash
# Create organized output directory
mkdir -p test_outputs

# Move test files to organized directory
mv afs2024_*.json test_outputs/
mv afs2024_*.csv test_outputs/

# List organized files
ls -la test_outputs/
```

### 10. Quick Test Script
```bash
# Create a quick test script
cat > test_api.sh << 'EOF'
#!/bin/bash

API_URL="https://financial-statement-transcription-api-1027259334816.asia-southeast1.run.app"
FILE="AFS2024 - statement extracted.pdf"

echo "🧪 Testing Financial Statement Transcription API"
echo "================================================"
echo "API URL: $API_URL"
echo "Test File: $FILE"
echo ""

# Test API health
echo "🔍 Testing API health..."
if curl -s "$API_URL/" > /dev/null; then
    echo "✅ API is accessible"
else
    echo "❌ API is not accessible"
    exit 1
fi

# Test file extraction
echo -e "\n🚀 Testing file extraction..."
curl -X POST "$API_URL/api/v1/extract-financial-data/sync" \
  -F "file=@$FILE" \
  -F "processing_approach=auto" \
  -F "output_format=both" \
  --max-time 300 \
  -o test_response.json

if [ $? -eq 0 ]; then
    echo "✅ Extraction completed"
    
    # Extract CSV
    jq -r '.csv_data' test_response.json > test_output.csv
    
    # Check year mapping row
    echo -e "\n📊 Checking year mapping row..."
    YEAR_ROW=$(sed -n '2p' test_output.csv)
    echo "Year mapping row: $YEAR_ROW"
    
    if echo "$YEAR_ROW" | grep -q "2024\|2023"; then
        echo "✅ Year mapping row contains correct years"
    else
        echo "❌ Year mapping row missing or incorrect"
    fi
    
    # Show first few lines
    echo -e "\n📋 CSV Preview:"
    head -5 test_output.csv
    
else
    echo "❌ Extraction failed"
fi

echo -e "\n🎯 Test completed!"
EOF

# Make script executable
chmod +x test_api.sh

# Run the test
./test_api.sh
```

## Expected Results

### ✅ Success Indicators
- **Year Mapping Row**: CSV contains second row showing actual years (e.g., "Date,Year,Year,,0.0,2024,2023,,")
- **Multiple Year Columns**: CSV header contains columns like "Value_Year_1", "Value_Year_2", etc.
- **Year Data**: Multiple years of financial data extracted
- **Processing Approach**: Uses appropriate approach for multi-year documents
- **Data Completeness**: Extracts data from multiple years in the document

### 📊 Expected CSV Format
```csv
Category,Subcategory,Field,Confidence,Confidence_Score,Value_Year_1,Value_Year_2,Value_Year_3,Value_Year_4
Date,Year,Year,,0.0,2024,2023,,
Balance Sheet,Current Assets,Cash And Equivalents,95.0%,0.95,40506296,14011556,,
```

## Troubleshooting

### Common Issues
1. **Connection Timeout**: Increase `--max-time` value
2. **File Not Found**: Ensure file is in current directory
3. **Permission Denied**: Check file permissions with `ls -la`
4. **API Unavailable**: Check if Cloud Run service is running

### Debug Commands
```bash
# Check file exists and size
ls -lh "AFS2024 - statement extracted.pdf"

# Check API response details
curl -v "$API_URL/" 2>&1 | head -20

# Check JSON response structure
jq '.' test_response.json | head -50
```

## Next Steps
After successful testing:
1. Review the generated CSV files for data quality
2. Compare with previous outputs
3. Test with different processing approaches
4. Document any issues or improvements needed
