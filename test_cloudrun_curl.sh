#!/bin/bash

# Cloud Run API Test Script for AFS2024 Multi-Year Issue
# Replace YOUR_CLOUD_RUN_URL with your actual Cloud Run service URL

CLOUD_RUN_URL="https://financial-statement-transcription-api-1027259334816.asia-southeast1.run.app"

echo "🧪 Cloud Run API Test for AFS2024 Multi-Year Issue"
echo "=================================================="
echo "🌐 Cloud Run URL: $CLOUD_RUN_URL"
echo ""

# Check if Cloud Run URL is configured
if [ "$CLOUD_RUN_URL" = "https://your-cloud-run-service-url.run.app" ]; then
    echo "❌ Please update CLOUD_RUN_URL with your actual Cloud Run service URL"
    echo "💡 You can find your Cloud Run URL in the Google Cloud Console"
    exit 1
fi

# Test 1: Health Check
echo "🔍 Test 1: Health Check"
echo "----------------------"
curl -s "$CLOUD_RUN_URL/"
echo ""
echo ""

# Test 2: Upload AFS2024 file
echo "🚀 Test 2: Upload AFS2024 file for multi-year extraction"
echo "--------------------------------------------------------"

if [ ! -f "AFS2024 - statement extracted.pdf" ]; then
    echo "❌ File 'AFS2024 - statement extracted.pdf' not found"
    echo "💡 Make sure the file is in the current directory"
    exit 1
fi

echo "📁 Uploading: AFS2024 - statement extracted.pdf"
echo "⏳ Processing... (this may take a few minutes)"

# Upload the file and save response
curl -X POST "$CLOUD_RUN_URL/api/v1/extract-financial-data/sync" \
  -F "file=@AFS2024 - statement extracted.pdf" \
  -F "processing_approach=auto" \
  -F "output_format=both" \
  -o "afs2024_response.json" \
  -w "\n\n📊 HTTP Status: %{http_code}\n⏱️ Total Time: %{time_total}s\n"

echo ""
echo "✅ Response saved to: afs2024_response.json"
echo ""

# Test 3: Check if response contains multi-year data
echo "🔍 Test 3: Analyzing response for multi-year data"
echo "------------------------------------------------"

if [ -f "afs2024_response.json" ]; then
    echo "📊 Checking for year columns in CSV data..."
    
    # Extract CSV data and check for year columns
    if command -v jq &> /dev/null; then
        echo "CSV Header (first line):"
        jq -r '.csv_data' afs2024_response.json | head -1
        
        echo ""
        echo "Year columns found:"
        jq -r '.csv_data' afs2024_response.json | head -1 | tr ',' '\n' | grep -i "year\|202"
        
        echo ""
        echo "Sample data rows:"
        jq -r '.csv_data' afs2024_response.json | head -5
    else
        echo "💡 Install 'jq' for better JSON parsing: sudo apt-get install jq"
        echo "📄 Raw response file: afs2024_response.json"
    fi
else
    echo "❌ Response file not found"
fi

echo ""
echo "🎉 Test completed!"
echo "📊 Check afs2024_response.json for detailed results"
