#!/usr/bin/env python3
"""
Script to demonstrate how CSV should be formatted with proper year labels
"""

import json
import csv
from datetime import datetime

def create_proper_csv_with_year_labels():
    """Create a properly formatted CSV with actual year labels"""
    
    # Read the JSON response to get year information
    with open('data/output/afs2024_full_response_20250830_142905.json', 'r') as f:
        response = json.load(f)
    
    # Extract year information
    years_detected = response['data']['years_detected']
    base_year = response['data']['base_year']
    
    print(f"📅 Years detected: {years_detected}")
    print(f"📅 Base year: {base_year}")
    
    # Create proper CSV header with actual years
    csv_header = ['Category', 'Subcategory', 'Field', 'Confidence', 'Confidence_Score']
    
    # Add year-specific columns with actual year labels
    for i, year in enumerate(years_detected):
        csv_header.append(f'Value_{year}')
    
    print(f"📊 Proper CSV Header: {csv_header}")
    
    # Create sample data rows
    sample_data = [
        ['Balance Sheet', 'Current Assets', 'Cash And Equivalents', '95.0%', '0.95', '40506296.0', '14011556.0'],
        ['Balance Sheet', 'Current Assets', 'Accounts Receivable', '90.0%', '0.9', '93102625.0', '102434862.0'],
        ['Income Statement', 'Revenues', 'Net Sales', '95.0%', '0.95', '249788478.0', '292800617.0'],
    ]
    
    # Write the properly formatted CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"afs2024_proper_format_{timestamp}.csv"
    
    with open(output_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(csv_header)
        writer.writerows(sample_data)
    
    print(f"💾 Properly formatted CSV saved to: {output_filename}")
    
    # Show the difference
    print("\n" + "="*80)
    print("🔍 COMPARISON: Current vs Proper Format")
    print("="*80)
    
    print("❌ CURRENT FORMAT (Confusing):")
    print("Category,Subcategory,Field,Confidence,Confidence_Score,Value_Year_1,Value_Year_2")
    print("Balance Sheet,Current Assets,Cash And Equivalents,95.0%,0.95,40506296.0,14011556.0")
    
    print("\n✅ PROPER FORMAT (Clear):")
    print("Category,Subcategory,Field,Confidence,Confidence_Score,Value_2024,Value_2023")
    print("Balance Sheet,Current Assets,Cash And Equivalents,95.0%,0.95,40506296.0,14011556.0")
    
    print("\n🎯 BENEFITS OF PROPER FORMAT:")
    print("- ✅ Users immediately know what years the data represents")
    print("- ✅ No need to refer to JSON or documentation")
    print("- ✅ Self-documenting CSV files")
    print("- ✅ Better for data analysis and reporting")
    print("- ✅ Compatible with financial analysis tools")

if __name__ == "__main__":
    create_proper_csv_with_year_labels()
