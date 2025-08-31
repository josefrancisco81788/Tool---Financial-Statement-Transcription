#!/usr/bin/env python3
import requests
import json
import time

def test_api_health():
    """Test if the API is responding"""
    try:
        response = requests.get("http://localhost:8000/", timeout=10)
        print(f"✅ API Health Check: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ API Health Check Failed: {e}")
        return False

def test_simple_extraction():
    """Test simple extraction with a small file"""
    try:
        # Test with the sample file
        with open('data/input/samples/test_financial_statement.pdf', 'rb') as f:
            files = {'file': f}
            data = {
                'processing_approach': 'auto',
                'output_format': 'csv'
            }
            
            print("📤 Testing simple extraction...")
            response = requests.post(
                "http://localhost:8000/api/v1/extract-financial-data/sync",
                files=files,
                data=data,
                timeout=120
            )
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Success!")
                
                # Check if CSV data is present
                if 'csv_data' in result:
                    csv_data = result['csv_data']
                    lines = csv_data.split('\r\n')
                    print(f"📄 CSV has {len(lines)} lines")
                    
                    # Check for year mapping row
                    if len(lines) >= 2:
                        print("🔍 Checking year mapping row...")
                        year_row = lines[1]  # Second row should be year mapping
                        print(f"Year mapping row: {year_row}")
                        
                        if "2024" in year_row or "2023" in year_row:
                            print("✅ Year mapping row found!")
                        else:
                            print("❌ Year mapping row missing or incorrect")
                    
                    # Save the result for inspection
                    with open('test_local_result.json', 'w') as f:
                        json.dump(result, f, indent=2)
                    print("💾 Full result saved to test_local_result.json")
                    
                    with open('test_local_result.csv', 'w') as f:
                        f.write(csv_data)
                    print("💾 CSV saved to test_local_result.csv")
                    
                else:
                    print("❌ No CSV data in response")
                    print(f"Response keys: {list(result.keys())}")
            else:
                print(f"❌ Request failed: {response.text}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing Local API Fix")
    print("=" * 40)
    
    if test_api_health():
        test_simple_extraction()
    else:
        print("❌ API not responding, cannot test extraction")
