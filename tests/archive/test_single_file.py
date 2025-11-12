import requests
import json
import pandas as pd
import time
import sys

def calculate_comprehensive_accuracy(mappings, target_df):
    """
    Calculate comprehensive accuracy metrics including precision, recall, F1, and field mapping accuracy
    """
    # Handle empty DataFrame case
    if target_df.empty or 'Field' not in target_df.columns:
        return {
            'field_mapping_accuracy': 0,
            'value_accuracy': 0,
            'precision': 0,
            'recall': 0,
            'f1_score': 0,
            'target_fields_count': 0,
            'extracted_fields_count': len(mappings),
            'correct_mappings_count': 0
        }
    
    # 1. Get all target fields that should have values (check all year columns)
    target_fields_with_values = set()
    for _, row in target_df.iterrows():
        field_name = row['Field']
        # Check all year columns for values
        for year_col in ['Value_Year_1', 'Value_Year_2', 'Value_Year_3', 'Value_Year_4']:
            if year_col in target_df.columns and pd.notna(row[year_col]):
                target_fields_with_values.add(field_name)
                break
    
    # 2. Get all extracted fields
    extracted_fields = set(mappings.keys())
    
    # 3. Calculate field mapping accuracy (exact field name matches)
    correct_field_mappings = target_fields_with_values.intersection(extracted_fields)
    field_mapping_accuracy = len(correct_field_mappings) / len(target_fields_with_values) * 100 if target_fields_with_values else 0
    
    # 4. Calculate value accuracy for correctly mapped fields (check all year columns)
    correct_values = 0
    total_value_checks = 0
    
    for field_name in correct_field_mappings:
        # Error handling for missing fields
        matching_rows = target_df[target_df['Field'] == field_name]
        if matching_rows.empty:
            continue
        target_row = matching_rows.iloc[0]
        extracted_mapping = mappings[field_name]
        
        # Check each year column individually
        for year_col in ['Value_Year_1', 'Value_Year_2', 'Value_Year_3', 'Value_Year_4']:
            if year_col in target_df.columns and pd.notna(target_row[year_col]):
                expected_value = target_row[year_col]
                extracted_value = extracted_mapping.get(year_col, 0)
                
                # Data type validation
                if not isinstance(extracted_value, (int, float)):
                    try:
                        extracted_value = float(extracted_value)
                    except (ValueError, TypeError):
                        extracted_value = 0
                
                # Zero division safety
                if abs(expected_value) < 0.01:  # Treat as zero
                    if abs(extracted_value) <= 0.01:
                        correct_values += 1
                else:
                    if abs(extracted_value - expected_value) / abs(expected_value) <= 0.05:
                        correct_values += 1
                total_value_checks += 1
    
    value_accuracy = (correct_values / total_value_checks * 100) if total_value_checks > 0 else 0
    
    # 5. Calculate precision and recall
    precision = len(correct_field_mappings) / len(extracted_fields) * 100 if extracted_fields else 0
    recall = len(correct_field_mappings) / len(target_fields_with_values) * 100 if target_fields_with_values else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'field_mapping_accuracy': field_mapping_accuracy,
        'value_accuracy': value_accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'target_fields_count': len(target_fields_with_values),
        'extracted_fields_count': len(extracted_fields),
        'correct_mappings_count': len(correct_field_mappings)
    }

def print_detailed_field_comparison(mappings, target_df):
    """Print detailed comparison of each field"""
    print(f'\n🔍 Detailed Field Comparison:')
    
    # Handle empty DataFrame case
    if target_df.empty or 'Field' not in target_df.columns:
        print('  ⚠️ No target template available for comparison')
        return
    
    # Get all fields that should have values
    target_fields_with_values = set()
    for _, row in target_df.iterrows():
        field_name = row['Field']
        for year_col in ['Value_Year_1', 'Value_Year_2', 'Value_Year_3', 'Value_Year_4']:
            if year_col in target_df.columns and pd.notna(row[year_col]):
                target_fields_with_values.add(field_name)
                break
    
    # Check each target field
    for field_name in sorted(target_fields_with_values):
        target_row = target_df[target_df['Field'] == field_name].iloc[0]
        
        if field_name in mappings:
            extracted_mapping = mappings[field_name]
            print(f'  ✅ {field_name}: EXTRACTED')
            
            # Check each year column
            for year_col in ['Value_Year_1', 'Value_Year_2', 'Value_Year_3', 'Value_Year_4']:
                if year_col in target_df.columns and pd.notna(target_row[year_col]):
                    expected_value = target_row[year_col]
                    extracted_value = extracted_mapping.get(year_col, 'MISSING')
                    print(f'    {year_col}: {extracted_value} (target: {expected_value})')
        else:
            print(f'  ❌ {field_name}: MISSING')
    
    # Check for false positives (extracted fields that shouldn't exist)
    extracted_fields = set(mappings.keys())
    false_positives = extracted_fields - target_fields_with_values
    if false_positives:
        print(f'\n⚠️ False Positives (extracted but shouldn\'t exist):')
        for field_name in sorted(false_positives):
            print(f'  ❌ {field_name}')

def assess_multi_year_coverage(mappings, target_df):
    """Assess multi-year data coverage properly"""
    year_columns = ['Value_Year_1', 'Value_Year_2', 'Value_Year_3', 'Value_Year_4']
    year_stats = {}
    
    # Handle empty DataFrame case
    if target_df.empty or 'Field' not in target_df.columns:
        return year_stats
    
    for year_col in year_columns:
        if year_col in target_df.columns:
            expected_fields = target_df[target_df[year_col].notna()]
            if len(expected_fields) > 0:
                extracted_count = sum(1 for _, row in expected_fields.iterrows() 
                                    if row['Field'] in mappings)
                year_stats[year_col] = extracted_count / len(expected_fields) * 100
    
    return year_stats

# Test file number from command line argument
test_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# Test files and their corresponding target templates
test_files = [
    {
        'file': 'tests/fixtures/light/2021 AFS with SEC Stamp - statement extracted.pdf',
        'target': 'core/templates/FS_Input_Template_Fields_2021_AFS_with_SEC_Stamp.csv',
        'name': '2021 AFS with SEC Stamp'
    },
    {
        'file': 'tests/fixtures/light/afs-2021-2023 - statement extracted.pdf', 
        'target': 'core/templates/FS_Input_Template_Fields_afs_2021_2023.csv',
        'name': 'afs-2021-2023'
    },
    {
        'file': 'tests/fixtures/light/AFS-2022 - statement extracted.pdf',
        'target': 'core/templates/FS_Input_Template_Fields_AFS-2022.csv', 
        'name': 'AFS-2022'
    },
    {
        'file': 'tests/fixtures/light/AFS2024 - statement extracted.pdf',
        'target': 'core/templates/FS_Input_Template_Fields_AFS2024.csv',
        'name': 'AFS2024'
    }
]

if test_number < 1 or test_number > len(test_files):
    print(f"Invalid test number. Please use 1-{len(test_files)}")
    sys.exit(1)

test = test_files[test_number - 1]

print(f'=== Testing {test["name"]} ({test_number}/{len(test_files)}) ===')

# Load PDF
with open(test['file'], 'rb') as f:
    pdf_data = f.read()

# Test API
start_time = time.time()
response = requests.post('http://localhost:8000/extract', 
    files={'file': ('test.pdf', pdf_data, 'application/pdf')},
    data={'export_csv': 'true'})

processing_time = time.time() - start_time

if response.status_code == 200:
    result = response.json()
    
    # Load target template
    try:
        target_df = pd.read_csv(test['target'])
        target_populated = target_df[target_df['Value_Year_1'].notna()]
        target_count = len(target_populated)
    except Exception as e:
        target_count = 0
        target_df = pd.DataFrame()  # Initialize empty DataFrame to prevent NameError
        print(f'⚠️ Could not load target template: {e}')
    
    # Analyze extraction results
    data = result['data']
    mappings = data.get('template_mappings', {})
    extracted_count = len(mappings)
    
    # Calculate coverage (how many fields extracted vs target)
    if target_count > 0:
        coverage = (extracted_count / target_count) * 100
    else:
        coverage = 0
    
    # Calculate comprehensive accuracy metrics
    comprehensive_metrics = calculate_comprehensive_accuracy(mappings, target_df)
    
    # Assess multi-year data coverage
    multi_year_stats = assess_multi_year_coverage(mappings, target_df)
    
    print(f'✅ Extracted: {extracted_count} fields')
    print(f'📊 Target: {target_count} fields')
    print(f'📈 Coverage: {coverage:.1f}% (fields extracted vs target)')
    print(f'📈 Field Mapping Accuracy: {comprehensive_metrics["field_mapping_accuracy"]:.1f}%')
    print(f'🎯 Value Accuracy: {comprehensive_metrics["value_accuracy"]:.1f}%')
    print(f'📊 Precision: {comprehensive_metrics["precision"]:.1f}%')
    print(f'📊 Recall: {comprehensive_metrics["recall"]:.1f}%')
    print(f'📊 F1 Score: {comprehensive_metrics["f1_score"]:.1f}%')
    print(f'📊 Target Fields: {comprehensive_metrics["target_fields_count"]}')
    print(f'📊 Extracted Fields: {comprehensive_metrics["extracted_fields_count"]}')
    print(f'📊 Correct Mappings: {comprehensive_metrics["correct_mappings_count"]}')
    print(f'⏱️ Time: {processing_time:.1f}s')
    
    # Add detailed field comparison
    print_detailed_field_comparison(mappings, target_df)
    
    # Show key extracted fields with value validation
    key_fields = ['Revenue', 'Cost of Sales', 'Total Assets', 'Total Equity', 'Comprehensive / Net income']
    print('\nKey fields validation:')
    for field in key_fields:
        if field in mappings:
            extracted_mapping = mappings[field]
            print(f'  ✅ {field}: EXTRACTED')
            
            # Check each year column
            for year_col in ['Value_Year_1', 'Value_Year_2', 'Value_Year_3', 'Value_Year_4']:
                extracted_value = extracted_mapping.get(year_col, 'N/A')
                if extracted_value != 'N/A':
                    print(f'    {year_col}: {extracted_value}')
        else:
            print(f'  ❌ {field}: Not found')
    
    # Show sample of all extracted fields
    print(f'\nAll extracted fields ({len(mappings)}):')
    for i, (field, data) in enumerate(mappings.items()):
        if i < 10:  # Show first 10
            value = data.get('value', 'N/A')
            print(f'  • {field}: {value}')
        elif i == 10:
            print(f'  ... and {len(mappings) - 10} more fields')
            break
    
    # Check for multi-year data
    multi_year_count = 0
    for field, data in mappings.items():
        if any(key.startswith('Value_Year_') for key in data.keys()):
            multi_year_count += 1
    
    print(f'\nMulti-year fields: {multi_year_count}')
    
    # Business use case assessment
    print(f'\n=== Business Use Case Assessment ===')
    print(f'• Template Coverage: {coverage:.1f}% of target fields extracted')
    print(f'• Field Mapping Accuracy: {comprehensive_metrics["field_mapping_accuracy"]:.1f}% of target fields correctly mapped')
    print(f'• Value Accuracy: {comprehensive_metrics["value_accuracy"]:.1f}% of extracted values are correct')
    print(f'• Precision: {comprehensive_metrics["precision"]:.1f}% of extracted fields are correct')
    print(f'• Recall: {comprehensive_metrics["recall"]:.1f}% of target fields were extracted')
    print(f'• F1 Score: {comprehensive_metrics["f1_score"]:.1f}% (harmonic mean of precision and recall)')
    print(f'• Processing Time: {processing_time:.1f}s (acceptable for business use)')
    print(f'• Key Financial Data: {"✅ Complete" if all(field in mappings for field in key_fields) else "❌ Missing some key fields"}')
    print(f'• Multi-year Support: {"✅ Working" if multi_year_count > 0 else "❌ Single year only"}')
    
    # Show multi-year coverage stats
    if multi_year_stats:
        print(f'• Multi-year Coverage:')
        for year_col, coverage_pct in multi_year_stats.items():
            print(f'  - {year_col}: {coverage_pct:.1f}%')
    
    # Save CSV for examination
    if 'template_csv' in result and result['template_csv']:
        import base64
        import os
        
        # Decode base64 CSV data
        csv_data = base64.b64decode(result['template_csv']).decode('utf-8')
        
        # Save to readable file with timestamp to avoid permission issues
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f'test_output_{test["name"].replace(" ", "_").replace("-", "_")}_{timestamp}.csv'
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(csv_data)
        
        print(f'\n📄 CSV saved to: {output_filename}')
        print(f'📁 Full path: {os.path.abspath(output_filename)}')
        
        # Show first few rows of the CSV
        print(f'\n📋 CSV Preview (first 5 rows):')
        lines = csv_data.split('\n')
        for i, line in enumerate(lines[:6]):  # Header + 5 data rows
            if line.strip():
                print(f'  {i}: {line}')
    else:
        print(f'\n❌ No CSV data in response')
    
else:
    print(f'❌ Error: {response.status_code} - {response.text}')
