#!/usr/bin/env python3
"""
Extract test results to CSV format for manual review
"""

import json
import csv
from datetime import datetime

def extract_results_to_csv():
    """Extract the latest test results to CSV format"""
    
    # Read the latest test results
    with open('tests/results/enhanced_test_report_1757388877.json', 'r') as f:
        data = json.load(f)
    
    # Create CSV output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f'tests/outputs/light_test_results_{timestamp}.csv'
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow([
            'File', 'Company', 'Statement Type', 'Years', 'Processing Time (s)',
            'Pages Processed', 'Line Items Count', 'Total Assets', 'Total Liabilities', 
            'Total Equity', 'Success', 'Status Code'
        ])
        
        # Write data for each test result
        for result in data['results']:
            response_data = result['response_data']
            data_content = response_data['data']
            
            # Extract key information
            filename = result['filename']
            company = data_content.get('company_name', 'N/A')
            statement_type = data_content.get('statement_type', 'N/A')
            years = ', '.join(data_content.get('years_detected', []))
            processing_time = result['processing_time']
            pages_processed = response_data.get('pages_processed', 'N/A')
            line_items_count = data_content.get('document_structure', {}).get('line_item_count', 'N/A')
            
            # Extract summary metrics
            summary = data_content.get('summary_metrics', {})
            total_assets = summary.get('total_assets', {}).get('value', 'N/A')
            total_liabilities = summary.get('total_liabilities', {}).get('value', 'N/A')
            total_equity = summary.get('total_equity', {}).get('value', 'N/A')
            
            success = result['success']
            status_code = result['status_code']
            
            writer.writerow([
                filename, company, statement_type, years, f"{processing_time:.1f}",
                pages_processed, line_items_count, total_assets, total_liabilities,
                total_equity, success, status_code
            ])
    
    print(f"✅ CSV file created: {csv_filename}")
    return csv_filename

if __name__ == "__main__":
    csv_file = extract_results_to_csv()
    print(f"📄 You can review the results in: {csv_file}")
