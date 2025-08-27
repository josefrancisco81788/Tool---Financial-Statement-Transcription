#!/usr/bin/env python3
"""
Simple API test to debug processing approach issue
"""

import requests
import json

def test_api_response():
    """Test API response and see what's happening"""
    print("🔍 Testing API Response")
    print("=" * 40)
    
    # Test with sample file
    with open('test_financial_statement.pdf', 'rb') as f:
        files = {'file': ('test_financial_statement.pdf', f, 'application/pdf')}
        data = {
            'processing_approach': 'whole_document',
            'output_format': 'both'
        }
        
        print("📤 Sending request...")
        response = requests.post(
            'http://localhost:8000/api/v1/extract-financial-data/sync',
            files=files,
            data=data
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            
            # Show the exact response structure
            print(f"\n📋 Response keys: {list(result.keys())}")
            
            # Check processing approach
            print(f"🔧 Processing Approach: {result.get('processing_approach', 'NOT_FOUND')}")
            print(f"📄 Pages Processed: {result.get('pages_processed', 'NOT_FOUND')}")
            print(f"⏱️ Processing Time: {result.get('processing_time', 'NOT_FOUND')}")
            
            # Check if there's a nested result
            if 'result' in result:
                print(f"\n📦 Nested result keys: {list(result['result'].keys())}")
                print(f"🔧 Nested Processing Approach: {result['result'].get('processing_approach', 'NOT_FOUND')}")
            
            # Show CSV data
            if 'csv_data' in result:
                csv_data = result['csv_data']
                print(f"\n📋 CSV Data Length: {len(csv_data)}")
                if csv_data and csv_data != "No data available for export":
                    lines = csv_data.split('\n')[:5]
                    print("📋 CSV Preview:")
                    for line in lines:
                        print(f"  {line}")
                else:
                    print(f"📋 CSV Content: {csv_data}")
            
            # Show JSON data structure
            if 'json_data' in result:
                json_data = result['json_data']
                print(f"\n📄 JSON Data Keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'Not a dict'}")
            
        else:
            print(f"❌ Error: {response.text}")

if __name__ == "__main__":
    test_api_response() 