import requests
import json
import pandas as pd
import base64
import time

# Test files and their corresponding target templates
test_files = [
    {
        'file': 'tests/fixtures/light/2021 AFS with SEC Stamp - statement extracted.pdf',
        'target': 'tests/fixtures/templates/FS_Input_Template_Fields_2021_AFS_with_SEC_Stamp.csv',
        'name': '2021 AFS with SEC Stamp'
    },
    {
        'file': 'tests/fixtures/light/afs-2021-2023 - statement extracted.pdf', 
        'target': 'tests/fixtures/templates/FS_Input_Template_Fields_afs_2021_2023.csv',
        'name': 'afs-2021-2023'
    },
    {
        'file': 'tests/fixtures/light/AFS-2022 - statement extracted.pdf',
        'target': 'tests/fixtures/templates/FS_Input_Template_Fields_AFS_2022.csv', 
        'name': 'AFS-2022'
    },
    {
        'file': 'tests/fixtures/light/AFS2024 - statement extracted.pdf',
        'target': 'tests/fixtures/templates/FS_Input_Template_Fields_AFS2024.csv',
        'name': 'AFS2024'
    }
]

results = []

for i, test in enumerate(test_files):
    print(f'\n=== Testing {test["name"]} ({i+1}/4) ===')
    
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
        except:
            target_count = 0
            print(f'⚠️ Could not load target template: {test["target"]}')
        
        # Analyze extraction results
        data = result['data']
        mappings = data.get('template_mappings', {})
        extracted_count = len(mappings)
        
        # Calculate accuracy
        if target_count > 0:
            accuracy = (extracted_count / target_count) * 100
        else:
            accuracy = 0
        
        results.append({
            'File': test['name'],
            'Extracted_Fields': extracted_count,
            'Target_Fields': target_count,
            'Accuracy_%': round(accuracy, 1),
            'Processing_Time_s': round(processing_time, 1),
            'Success': True
        })
        
        print(f'✅ Extracted: {extracted_count} fields')
        print(f'📊 Target: {target_count} fields')
        print(f'🎯 Accuracy: {accuracy:.1f}%')
        print(f'⏱️ Time: {processing_time:.1f}s')
        
        # Show key extracted fields
        key_fields = ['Revenue', 'Cost of Sales', 'Total Assets', 'Total Equity', 'Comprehensive / Net income']
        print('Key fields:')
        for field in key_fields:
            if field in mappings:
                value = mappings[field].get('value', 'N/A')
                print(f'  ✅ {field}: {value}')
            else:
                print(f'  ❌ {field}: Not found')
                
    else:
        print(f'❌ Error: {response.status_code}')
        results.append({
            'File': test['name'],
            'Extracted_Fields': 0,
            'Target_Fields': 0,
            'Accuracy_%': 0,
            'Processing_Time_s': 0,
            'Success': False
        })

# Create comparison table
print('\n' + '='*80)
print('COMPARISON TABLE - LLM-First Direct Mapping Results')
print('='*80)

df_results = pd.DataFrame(results)
print(df_results.to_string(index=False))

# Summary statistics
successful_tests = df_results[df_results['Success'] == True]
if len(successful_tests) > 0:
    avg_accuracy = successful_tests['Accuracy_%'].mean()
    avg_time = successful_tests['Processing_Time_s'].mean()
    total_extracted = successful_tests['Extracted_Fields'].sum()
    total_target = successful_tests['Target_Fields'].sum()
    
    print(f'\nSUMMARY:')
    print(f'• Average Accuracy: {avg_accuracy:.1f}%')
    print(f'• Average Processing Time: {avg_time:.1f}s')
    print(f'• Total Fields Extracted: {total_extracted}')
    print(f'• Total Target Fields: {total_target}')
    print(f'• Overall Coverage: {(total_extracted/total_target*100):.1f}%' if total_target > 0 else '• Overall Coverage: N/A')











