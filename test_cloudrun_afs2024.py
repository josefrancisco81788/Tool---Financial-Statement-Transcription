#!/usr/bin/env python3
"""
Test script for Cloud Run API with AFS2024 file to check multi-year issue resolution
"""

import requests
import json
import time
import os
from pathlib import Path
from datetime import datetime

# Cloud Run API URL - Replace with your actual Cloud Run URL
CLOUD_RUN_URL = "https://financial-statement-transcription-api-1027259334816.asia-southeast1.run.app"

def test_cloudrun_api_health():
    """Test if the Cloud Run API is accessible"""
    print("🔍 Testing Cloud Run API health...")
    try:
        response = requests.get(f"{CLOUD_RUN_URL}/", timeout=10)
        if response.status_code == 200:
            print("✅ Cloud Run API is accessible")
            return True
        else:
            print(f"❌ Cloud Run API returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Cloud Run API: {str(e)}")
        print("💡 Make sure to update CLOUD_RUN_URL with your actual Cloud Run service URL")
        return False

def test_afs2024_multi_year_extraction():
    """Test the AFS2024 file for multi-year data extraction"""
    file_path = "data/input/documents/AFS2024 - statement extracted.pdf"
    
    print(f"\n🚀 Testing AFS2024 multi-year extraction: {file_path}")
    print("=" * 80)
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Get file info
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    print(f"📁 File: {file_name}")
    print(f"📏 Size: {file_size / 1024:.1f} KB")
    
    # Use synchronous endpoint for testing
    endpoint = f"{CLOUD_RUN_URL}/api/v1/extract-financial-data/sync"
    
    try:
        # Prepare the file upload
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f, 'application/pdf')}
            data = {
                'processing_approach': 'auto',
                'output_format': 'both'  # Get both CSV and JSON for analysis
            }
            
            print(f"📤 Uploading to Cloud Run: {endpoint}")
            print("⏳ Processing... (this may take a few minutes)")
            
            start_time = time.time()
            
            # Make the request
            response = requests.post(endpoint, files=files, data=data, timeout=300)  # 5 minute timeout
            
            processing_time = time.time() - start_time
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"⏱️ Processing Time: {processing_time:.2f} seconds")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Extraction successful!")
                
                # Analyze the results for multi-year data
                analyze_multi_year_results(result)
                
                # Save results
                save_results(result)
                
                return True
                
            else:
                print(f"❌ Extraction failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
                
    except requests.exceptions.Timeout:
        print("❌ Request timed out. The file might be too large for synchronous processing.")
        print("💡 Consider using the asynchronous endpoint for large files.")
        return False
    except Exception as e:
        print(f"❌ Error during extraction: {str(e)}")
        return False

def analyze_multi_year_results(result):
    """Analyze the results to check for multi-year data extraction"""
    print("\n🔍 Analyzing multi-year data extraction...")
    print("=" * 50)
    
    # Check CSV data for multiple years
    if 'csv_data' in result:
        csv_lines = result['csv_data'].strip().split('\n')
        if len(csv_lines) > 1:
            header = csv_lines[0]
            print(f"📊 CSV Header: {header}")
            
            # Look for year columns
            year_columns = [col for col in header.split(',') if 'year' in col.lower() or '202' in col]
            if year_columns:
                print(f"✅ Found year columns: {year_columns}")
                
                # Check data rows for multiple years
                data_rows = csv_lines[1:]
                print(f"📈 Found {len(data_rows)} data rows")
                
                # Sample a few rows to check for multi-year data
                for i, row in enumerate(data_rows[:5]):  # Check first 5 rows
                    values = row.split(',')
                    if len(values) > 5:  # Ensure we have enough columns
                        print(f"Row {i+1}: {values[:5]}...")  # Show first 5 values
            else:
                print("⚠️ No year columns found in CSV header")
        else:
            print("⚠️ CSV data appears to be empty or has no data rows")
    
    # Check JSON data for multiple years
    if 'json_data' in result:
        try:
            json_data = json.loads(result['json_data'])
            print(f"\n📋 JSON Data Structure:")
            print(f"Type: {type(json_data)}")
            
            if isinstance(json_data, list):
                print(f"Number of items: {len(json_data)}")
                if json_data:
                    print(f"First item keys: {list(json_data[0].keys())}")
                    
                    # Look for year-related fields
                    first_item = json_data[0]
                    year_fields = [key for key in first_item.keys() if 'year' in key.lower() or '202' in str(first_item[key])]
                    if year_fields:
                        print(f"✅ Found year-related fields: {year_fields}")
                    else:
                        print("⚠️ No year-related fields found in JSON data")
            elif isinstance(json_data, dict):
                print(f"Dictionary keys: {list(json_data.keys())}")
                
        except json.JSONDecodeError:
            print("⚠️ Could not parse JSON data")
    
    # Check processing approach used
    if 'effective_processing_approach' in result:
        print(f"\n🔧 Processing Approach Used: {result['effective_processing_approach']}")
    
    if 'pages_processed' in result:
        print(f"📄 Pages Processed: {result['pages_processed']}")

def save_results(result):
    """Save the results to files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save CSV data
    if 'csv_data' in result:
        csv_filename = f"data/output/afs2024_extracted_data_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            f.write(result['csv_data'])
        print(f"💾 CSV data saved to: {csv_filename}")
    
    # Save JSON data
    if 'json_data' in result:
        json_filename = f"afs2024_extracted_data_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            f.write(result['json_data'])
        print(f"💾 JSON data saved to: {json_filename}")
    
    # Save full response
            full_response_filename = f"data/output/afs2024_full_response_{timestamp}.json"
    with open(full_response_filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    print(f"💾 Full response saved to: {full_response_filename}")

def main():
    """Main test function"""
    print("🧪 Cloud Run API Multi-Year Issue Test")
    print("=" * 60)
    print(f"🎯 Target: AFS2024 - statement extracted.pdf")
    print(f"🌐 Cloud Run URL: {CLOUD_RUN_URL}")
    print()
    
    # Check if Cloud Run URL is configured
    if CLOUD_RUN_URL == "https://your-cloud-run-service-url.run.app":
        print("❌ Please update CLOUD_RUN_URL with your actual Cloud Run service URL")
        print("💡 You can find your Cloud Run URL in the Google Cloud Console")
        return
    
    # Test API health
    if not test_cloudrun_api_health():
        return
    
    # Test AFS2024 extraction
    success = test_afs2024_multi_year_extraction()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("📊 Check the saved files for detailed results")
    else:
        print("\n❌ Test failed. Check the error messages above.")

if __name__ == "__main__":
    main()
