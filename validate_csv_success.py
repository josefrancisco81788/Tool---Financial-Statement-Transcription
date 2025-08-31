#!/usr/bin/env python3
"""
CSV Success Criteria Validator

This script validates CSV output against the success criteria defined in CSV_FORMAT_SPECIFICATION.md.
Every test from here on out MUST pass this validation.

Usage:
    python validate_csv_success.py your_output.csv
"""

import sys
import csv
import re

def validate_csv_success(csv_file_path):
    """Validate CSV against success criteria"""
    print("🧪 CSV Success Criteria Validation")
    print("=" * 50)
    
    try:
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ File not found: {csv_file_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    # Remove empty lines and strip whitespace
    lines = [line.strip() for line in lines if line.strip()]
    
    if len(lines) < 3:
        print("❌ CSV must have at least 3 lines (header, year mapping, data)")
        return False
    
    results = {
        'column_structure': False,
        'year_mapping_row': False,
        'data_completeness': False,
        'row_integrity': False
    }
    
    # 1. Column Structure Check
    print("\n1️⃣ Column Structure Check...")
    header = lines[0]
    expected_columns = ['Category', 'Subcategory', 'Field', 'Confidence', 'Value_Year_1', 'Value_Year_2', 'Value_Year_3', 'Value_Year_4']
    
    # Parse header
    header_columns = [col.strip() for col in header.split(',')]
    
    # Check for required columns
    missing_columns = []
    extra_columns = []
    
    for expected in expected_columns:
        if expected not in header_columns:
            missing_columns.append(expected)
    
    for actual in header_columns:
        if actual not in expected_columns:
            extra_columns.append(actual)
    
    if missing_columns:
        print(f"❌ Missing required columns: {missing_columns}")
    elif extra_columns:
        print(f"❌ Extra columns found: {extra_columns}")
    else:
        print("✅ Column structure is correct")
        results['column_structure'] = True
    
    # 2. Year Mapping Row Check
    print("\n2️⃣ Year Mapping Row Check...")
    year_mapping_row = lines[1]
    year_columns = [col.strip() for col in year_mapping_row.split(',')]
    
    # Check year mapping row structure
    expected_year_row = ['Date', 'Year', 'Year', '', '0.0']
    
    if len(year_columns) < 5:
        print("❌ Year mapping row too short")
    elif year_columns[:5] != expected_year_row:
        print(f"❌ Year mapping row structure incorrect")
        print(f"   Expected: {expected_year_row}")
        print(f"   Found: {year_columns[:5]}")
    else:
        # Check for year values in Value_Year columns
        year_values = year_columns[5:9] if len(year_columns) >= 9 else []
        if len(year_values) >= 2 and year_values[0] and year_values[1]:
            print(f"✅ Year mapping row correct: {year_values[0]}, {year_values[1]}")
            results['year_mapping_row'] = True
        else:
            print("❌ Year mapping row missing year values")
    
    # 3. Row Integrity Check
    print("\n3️⃣ Row Integrity Check...")
    # Check for empty rows in the original file
    with open(csv_file_path, 'r', newline='', encoding='utf-8') as f:
        original_lines = f.readlines()
    
    empty_row_count = 0
    for i, line in enumerate(original_lines):
        if line.strip() == '':
            empty_row_count += 1
            print(f"   ⚠️  Empty row found at line {i+1}")
    
    if empty_row_count == 0:
        print("✅ No empty rows found")
        results['row_integrity'] = True
    else:
        print(f"❌ Found {empty_row_count} empty row(s)")
    
    # 4. Data Completeness Check
    print("\n4️⃣ Data Completeness Check...")
    data_rows = lines[2:]  # Skip header and year mapping row
    
    empty_cells = 0
    none_values = 0
    total_cells = 0
    
    for i, row in enumerate(data_rows):
        if not row.strip():
            continue
            
        columns = [col.strip() for col in row.split(',')]
        if len(columns) < 6:  # Must have at least Category, Subcategory, Field, Confidence, Value_Year_1, Value_Year_2
            continue
            
        # Check Value_Year columns (indices 5-8)
        for j in range(5, min(9, len(columns))):
            total_cells += 1
            value = columns[j]
            
            if value == '':
                empty_cells += 1
            elif value.lower() == 'none':
                none_values += 1
                print(f"   ⚠️  'None' value found at row {i+3}, column {j+1}")
    
    if empty_cells == 0 and none_values == 0:
        print("✅ All financial values are present")
        results['data_completeness'] = True
    else:
        print(f"❌ Found {empty_cells} empty cells and {none_values} 'None' values")
        if total_cells > 0:
            completeness_rate = ((total_cells - empty_cells - none_values) / total_cells) * 100
            print(f"   Data completeness rate: {completeness_rate:.1f}%")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL SUCCESS CRITERIA MET")
        print("✅ CSV output meets all standards")
        return True
    else:
        print("❌ SUCCESS CRITERIA NOT MET")
        print("❌ CSV output needs improvement")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_csv_success.py <csv_file>")
        print("Example: python validate_csv_success.py extracted_data.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    success = validate_csv_success(csv_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
