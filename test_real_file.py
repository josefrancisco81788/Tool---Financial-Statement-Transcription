#!/usr/bin/env python3
"""
Simple test script for uploading real-world documents to the API
Usage: python test_real_file.py <file_path>
"""

import requests
import json
import time
import os
import sys

# API base URL
API_BASE_URL = "http://localhost:8000"

def test_file_upload(file_path, processing_approach="auto", output_format="csv"):
    """
    Test file upload to the API
    
    Args:
        file_path: Path to the file to upload
        processing_approach: "whole_document", "vector_database", or "auto"
        output_format: "csv", "json", or "both"
    """
    print(f"🚀 Testing file upload: {file_path}")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Get file info
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    print(f"📁 File: {file_name}")
    print(f"📏 Size: {file_size / 1024:.1f} KB")
    
    # Always use sync endpoint (no size limits)
    endpoint = f"{API_BASE_URL}/api/v1/extract-financial-data/sync"
    print("⚡ Using synchronous endpoint")
    
    try:
        # Prepare the file upload
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f, 'application/octet-stream')}
            data = {
                'processing_approach': processing_approach,
                'output_format': output_format
            }
            
            print(f"📤 Uploading to: {endpoint}")
            print(f"🔧 Processing Approach: {processing_approach}")
            print("⏳ Processing...")
            
            # Make the request
            response = requests.post(endpoint, files=files, data=data, timeout=(60, 3600))
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Upload successful!")
                
                # Display results
                if 'job_id' in result:
                    print(f"🆔 Job ID: {result['job_id']}")
                    print(f"📋 Status: {result['status']}")
                    
                    if result['status'] == 'processing':
                        print("⏳ File is being processed in the background...")
                        print("💡 Use the job ID to check status later")
                        return True
                    elif result['status'] == 'completed':
                        print("🎉 Processing completed!")
                        display_results(result.get('result', {}))
                else:
                    # Direct result (sync endpoint)
                    display_results(result)
                    
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error during upload: {str(e)}")
        return False
    
    return True

def check_job_status(job_id):
    """Check the status of a background job"""
    print(f"\n🔍 Checking job status: {job_id}")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/jobs/{job_id}")
        
        if response.status_code == 200:
            job = response.json()
            print(f"📋 Status: {job.get('status', 'unknown')}")
            print(f"📊 Progress: {job.get('progress', 0)}%")
            print(f"💬 Message: {job.get('message', 'No message')}")
            
            if job.get('status') == 'completed':
                print("🎉 Job completed!")
                display_results(job.get('result', {}))
            elif job.get('status') == 'failed':
                print(f"❌ Job failed: {job.get('error', 'Unknown error')}")
            else:
                print("⏳ Job still processing...")
                
        else:
            print(f"❌ Failed to get job status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking job status: {str(e)}")

def display_results(result):
    """Display the processing results"""
    print("\n📊 Processing Results:")
    print("-" * 40)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return
    
    # Display basic info
    print(f"⏱️  Processing Time: {result.get('processing_time', 'N/A')} seconds")
    print(f"🔧 Processing Approach: {result.get('processing_approach', 'N/A')}")
    if 'requested_processing_approach' in result or 'effective_processing_approach' in result:
        print(f"   ├─ Requested: {result.get('requested_processing_approach', 'N/A')}")
        print(f"   └─ Effective: {result.get('effective_processing_approach', 'N/A')}")
    print(f"📄 Pages Processed: {result.get('pages_processed', 'N/A')}")
    
    # Display output format info
    output_format = result.get('output_format', 'unknown')
    print(f"📤 Output Format: {output_format}")
    
    # Display CSV data if available
    if 'csv_data' in result:
        print(f"\n📋 CSV Data Preview:")
        csv_lines = result['csv_data'].split('\n')[:10]  # First 10 lines
        for line in csv_lines:
            print(f"  {line}")
        csv_lines_list = result['csv_data'].split('\n')
        if len(csv_lines_list) > 10:
            print(f"  ... and {len(csv_lines_list) - 10} more lines")
    
    # Display JSON data if available
    if 'json_data' in result:
        print(f"\n📄 JSON Data Structure:")
        json_data = result['json_data']
        if isinstance(json_data, dict):
            for key in json_data.keys():
                print(f"  📁 {key}")
        else:
            print(f"  {type(json_data)}")
    
    # Save results to files
    save_results(result)

def save_results(result):
    """Save results to files"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Save CSV if available
    if 'csv_data' in result:
        csv_filename = f"extracted_data_{timestamp}.csv"
        with open(csv_filename, 'w', encoding='utf-8', newline='') as f:
            f.write(result['csv_data'])
        print(f"💾 CSV saved to: {csv_filename}")
    
    # Save JSON if available
    if 'json_data' in result:
        json_filename = f"extracted_data_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(result['json_data'], f, indent=2)
        print(f"💾 JSON saved to: {json_filename}")

def main():
    """Main test function"""
    print("🧪 Financial Statement Transcription API - Real File Test")
    print("=" * 70)
    
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code != 200:
            print("❌ API is not running. Please start it first:")
            print("   cd api && uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
            return
    except:
        print("❌ Cannot connect to API. Please start it first:")
        print("   cd api && uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        return
    
    print("✅ API is running!")
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("\n📋 Usage: python test_real_file.py <file_path> [processing_approach] [output_format]")
        print("Example: python test_real_file.py financial_statement.pdf whole_document both")
        print("\n💡 Supported processing approaches: whole_document, vector_database, auto")
        print("💡 Supported output formats: csv, json, both")
        print("💡 Supported file types: PDF, JPG, JPEG, PNG")
        return
    
    file_path = sys.argv[1]
    processing_approach = sys.argv[2] if len(sys.argv) > 2 else "auto"
    output_format = sys.argv[3] if len(sys.argv) > 3 else "csv"
    
    # Test the file upload
    success = test_file_upload(file_path, processing_approach, output_format)
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("\n📖 Next steps:")
        print("1. Check the generated CSV/JSON files")
        print("2. Visit http://localhost:8000/docs for interactive testing")
        print("3. Integrate the API into your applications")
    else:
        print("\n❌ Test failed. Check the error messages above.")

if __name__ == "__main__":
    main() 