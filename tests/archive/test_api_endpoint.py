#!/usr/bin/env python3
"""
Test API endpoint functionality
"""

import requests
import time
import os

def test_api_endpoint():
    """Test the API extract endpoint"""
    print("🔍 Testing API extract endpoint...")
    
    # Test file path
    pdf_path = "tests/fixtures/light/AFS2024 - statement extracted.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Test file not found: {pdf_path}")
        return False
    
    print(f"📄 Testing with: {pdf_path}")
    
    try:
        # Prepare the request
        with open(pdf_path, 'rb') as f:
            files = {'file': f}
            data = {'statement_type': 'financial statement'}
            
            print("🚀 Sending request to API...")
            start_time = time.time()
            
            # Send request with timeout
            response = requests.post(
                'http://localhost:8000/extract',
                files=files,
                data=data,
                timeout=120  # 2 minutes timeout
            )
            
            elapsed = time.time() - start_time
            print(f"✅ Request completed in {elapsed:.2f}s")
            print(f"📊 Status code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"📄 Pages processed: {result.get('pages_processed', 'N/A')}")
                print(f"⏱️ Processing time: {result.get('processing_time', 'N/A')}s")
                print("✅ API endpoint working correctly!")
                return True
            else:
                print(f"❌ API returned error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"⏰ Request timed out after {elapsed:.2f}s")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Request failed after {elapsed:.2f}s: {e}")
        return False

if __name__ == "__main__":
    test_api_endpoint()
