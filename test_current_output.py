#!/usr/bin/env python3
import requests
import json

def test_current_output():
    """Test the current API output"""
    try:
        with open('data/input/documents/AFS2024 - statement extracted.pdf', 'rb') as f:
            files = {'file': f}
            data = {
                'processing_approach': 'auto',
                'output_format': 'csv'
            }
            
            print("📤 Testing current API output...")
            response = requests.post(
                "http://localhost:8000/api/v1/extract-financial-data/sync",
                files=files,
                data=data,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if 'csv_data' in result:
                    csv_data = result['csv_data']
                    lines = csv_data.split('\r\n')
                    
                    print(f"📄 CSV has {len(lines)} lines")
                    print("🔍 First 5 lines:")
                    for i, line in enumerate(lines[:5]):
                        print(f"  Line {i+1}: {line}")
                    
                    # Save to a new file
                    with open('current_api_output.csv', 'w', newline='') as f:
                        f.write(csv_data)
                    print("💾 Saved to current_api_output.csv")
                    
                    # Check for year mapping row
                    if len(lines) >= 2:
                        year_row = lines[1]
                        if "2024" in year_row and "2023" in year_row:
                            print("✅ Year mapping row is present and correct!")
                        else:
                            print("❌ Year mapping row missing or incorrect")
                else:
                    print("❌ No CSV data in response")
            else:
                print(f"❌ Request failed: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_current_output()
