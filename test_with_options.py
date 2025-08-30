#!/usr/bin/env python3
"""
Test script with different processing options for real-world documents
"""

import requests
import json
import time
import os
import sys

# API base URL
API_BASE_URL = "http://localhost:8000"

def test_with_options(file_path, processing_approach="whole_document", output_format="both"):
    """
    Test file upload with specific processing options
    
    Args:
        file_path: Path to the file to upload
        processing_approach: "whole_document", "vector_database", or "auto"
        output_format: "csv", "json", or "both"
    """
    print(f"🚀 Testing file upload: {file_path}")
    print(f"🔧 Processing Approach: {processing_approach}")
    print(f"📤 Output Format: {output_format}")
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
    
    # Use sync endpoint for testing
    endpoint = f"{API_BASE_URL}/api/v1/extract-financial-data/sync"
    print(f"⚡ Using synchronous endpoint")
    
    try:
        # Prepare the file upload
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f, 'application/octet-stream')}
            data = {
                'processing_approach': processing_approach,
                'output_format': output_format
            }
            
            print(f"📤 Uploading to: {endpoint}")
            print("⏳ Processing...")
            
            # Make the request
            response = requests.post(endpoint, files=files, data=data)
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Upload successful!")
                display_detailed_results(result)
                return True
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error during upload: {str(e)}")
        return False

def display_detailed_results(result):
    """Display detailed processing results"""
    print("\n📊 Processing Results:")
    print("-" * 40)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return
    
    # Display basic info
    print(f"⏱️  Processing Time: {result.get('processing_time', 'N/A')} seconds")
    print(f"🔧 Processing Approach: {result.get('processing_approach', 'N/A')}")
    print(f"📄 Pages Processed: {result.get('pages_processed', 'N/A')}")
    
    # Display document characteristics
    if 'document_characteristics' in result:
        chars = result['document_characteristics']
        print(f"\n📋 Document Characteristics:")
        print(f"  📄 Page Count: {chars.get('page_count', 'N/A')}")
        print(f"  📏 File Size: {chars.get('file_size_mb', 'N/A')} MB")
        print(f"  🎯 Recommendation: {chars.get('recommendation', 'N/A')}")
        print(f"  💬 Reason: {chars.get('reason', 'N/A')}")
    
    # Display output format info
    output_format = result.get('output_format', 'unknown')
    print(f"\n📤 Output Format: {output_format}")
    
    # Display CSV data if available
    if 'csv_data' in result:
        print(f"\n📋 CSV Data:")
        csv_content = result['csv_data']
        if csv_content and csv_content != "No data available for export":
            csv_lines = csv_content.split('\n')[:20]  # First 20 lines
            for line in csv_lines:
                print(f"  {line}")
            csv_lines_list = csv_content.split('\n')
            if len(csv_lines_list) > 20:
                print(f"  ... and {len(csv_lines_list) - 20} more lines")
        else:
            print(f"  {csv_content}")
    
    # Display JSON data if available
    if 'json_data' in result:
        print(f"\n📄 JSON Data Structure:")
        json_data = result['json_data']
        if isinstance(json_data, dict):
            print(f"  📁 Keys found: {list(json_data.keys())}")
            # Show some sample data
            for key, value in json_data.items():
                if isinstance(value, dict):
                    print(f"  📂 {key}: {list(value.keys()) if value else 'Empty'}")
                elif isinstance(value, list):
                    print(f"  📂 {key}: {len(value)} items")
                else:
                    print(f"  📂 {key}: {type(value).__name__}")
        else:
            print(f"  {type(json_data)}")
    
    # Save results to files
    save_results(result)

def save_results(result):
    """Save results to files"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    approach = result.get('processing_approach', 'unknown')
    
    # Save CSV if available
    if 'csv_data' in result:
        csv_filename = f"data/output/extracted_data_{approach}_{timestamp}.csv"
        with open(csv_filename, 'w', encoding='utf-8') as f:
            f.write(result['csv_data'])
        print(f"\n💾 CSV saved to: {csv_filename}")
    
    # Save JSON if available
    if 'json_data' in result:
        json_filename = f"extracted_data_{approach}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(result['json_data'], f, indent=2)
        print(f"💾 JSON saved to: {json_filename}")

def main():
    """Main test function"""
    print("🧪 Financial Statement Transcription API - Advanced Testing")
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
        print("\n📋 Usage: python test_with_options.py <file_path> [processing_approach] [output_format]")
        print("Example: python test_with_options.py AFS2022.pdf whole_document both")
        print("\n💡 Processing Approaches: auto, whole_document, vector_database")
        print("💡 Output Formats: csv, json, both")
        return
    
    file_path = sys.argv[1]
    processing_approach = sys.argv[2] if len(sys.argv) > 2 else "whole_document"
    output_format = sys.argv[3] if len(sys.argv) > 3 else "both"
    
    # Test with specified options
    success = test_with_options(file_path, processing_approach, output_format)
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("\n💡 Try different approaches:")
        print("  python test_with_options.py AFS2022.pdf whole_document both")
        print("  python test_with_options.py AFS2022.pdf vector_database both")
        print("  python test_with_options.py AFS2022.pdf auto both")
    else:
        print("\n❌ Test failed. Check the error messages above.")

if __name__ == "__main__":
    main() 