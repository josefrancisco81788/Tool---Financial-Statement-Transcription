#!/usr/bin/env python3
"""
Local test to verify the CSV fix works correctly
"""

import json
import sys
import os

# Add the api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from services.file_processor import FileProcessor

def test_csv_fix():
    """Test the CSV fix with the AFS2024 data"""
    
    # Load the test data from the JSON response
    with open('data/output/afs2024_full_response_20250830_142905.json', 'r') as f:
        test_data = json.load(f)
    
    print("🧪 Testing CSV fix locally...")
    print("=" * 50)
    
    # Create file processor instance
    processor = FileProcessor()
    
    # Test the CSV transformation
    try:
        csv_output = processor._transform_data_for_csv(test_data['data'])
        
        print("✅ CSV transformation successful!")
        print(f"📊 CSV output length: {len(csv_output)} characters")
        
        # Split into lines and show first few lines
        lines = csv_output.split('\r\n')
        print(f"📄 Number of lines: {len(lines)}")
        
        print("\n📋 First 5 lines of CSV output:")
        print("-" * 50)
        for i, line in enumerate(lines[:5]):
            print(f"Line {i+1}: {line}")
        
        # Check if year mapping row is present
        if len(lines) >= 2:
            header_line = lines[0]
            year_mapping_line = lines[1]
            
            print(f"\n🔍 Header line: {header_line}")
            print(f"🔍 Year mapping line: {year_mapping_line}")
            
            # Check if year mapping line contains years
            if "2024" in year_mapping_line and "2023" in year_mapping_line:
                print("✅ Year mapping row is present and contains correct years!")
            else:
                print("❌ Year mapping row is missing or incorrect")
        else:
            print("❌ Not enough lines in CSV output")
        
        # Save the test output
        with open('tests/outputs/test_csv_fix_output.csv', 'w', newline='', encoding='utf-8') as f:
            f.write(csv_output)
        print(f"\n💾 Test output saved to: test_csv_fix_output.csv")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing CSV fix: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_csv_fix()
    if success:
        print("\n🎉 CSV fix test passed!")
    else:
        print("\n❌ CSV fix test failed!")
