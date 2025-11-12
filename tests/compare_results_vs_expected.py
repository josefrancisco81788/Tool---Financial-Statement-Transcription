"""
Compare actual extraction results against expected template files
"""

import os
import sys
import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_csv_data(file_path: str) -> List[Dict[str, str]]:
    """Load CSV data into a list of dictionaries"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def compare_csv_files(actual_path: str, expected_path: str) -> Dict[str, Any]:
    """Compare actual vs expected CSV files"""
    print(f"🔍 Comparing: {Path(actual_path).name} vs {Path(expected_path).name}")
    
    # Load both files
    actual_data = load_csv_data(actual_path)
    expected_data = load_csv_data(expected_path)
    
    # Initialize comparison results
    comparison = {
        'file_actual': Path(actual_path).name,
        'file_expected': Path(expected_path).name,
        'total_fields': len(actual_data),
        'matches': 0,
        'mismatches': 0,
        'missing_actual': 0,
        'missing_expected': 0,
        'field_comparisons': [],
        'summary': {}
    }
    
    # Create lookup dictionaries for faster comparison
    actual_lookup = {}
    expected_lookup = {}
    
    for row in actual_data:
        key = f"{row['Category']}|{row['Subcategory']}|{row['Field']}"
        actual_lookup[key] = row
    
    for row in expected_data:
        key = f"{row['Category']}|{row['Subcategory']}|{row['Field']}"
        expected_lookup[key] = row
    
    # Compare fields
    all_keys = set(actual_lookup.keys()) | set(expected_lookup.keys())
    
    for key in sorted(all_keys):
        actual_row = actual_lookup.get(key)
        expected_row = expected_lookup.get(key)
        
        if actual_row and expected_row:
            # Both exist, compare values
            actual_year1 = actual_row.get('Value_Year_1', '').strip()
            actual_year2 = actual_row.get('Value_Year_2', '').strip()
            expected_year1 = expected_row.get('Value_Year_1', '').strip()
            expected_year2 = expected_row.get('Value_Year_2', '').strip()
            
            year1_match = actual_year1 == expected_year1
            year2_match = actual_year2 == expected_year2
            
            if year1_match and year2_match:
                comparison['matches'] += 1
                status = 'MATCH'
            else:
                comparison['mismatches'] += 1
                status = 'MISMATCH'
            
            comparison['field_comparisons'].append({
                'field': key,
                'status': status,
                'actual_year1': actual_year1,
                'actual_year2': actual_year2,
                'expected_year1': expected_year1,
                'expected_year2': expected_year2,
                'year1_match': year1_match,
                'year2_match': year2_match
            })
            
        elif actual_row and not expected_row:
            # Only in actual
            comparison['missing_expected'] += 1
            comparison['field_comparisons'].append({
                'field': key,
                'status': 'ONLY_IN_ACTUAL',
                'actual_year1': actual_row.get('Value_Year_1', ''),
                'actual_year2': actual_row.get('Value_Year_2', ''),
                'expected_year1': '',
                'expected_year2': '',
                'year1_match': False,
                'year2_match': False
            })
            
        elif not actual_row and expected_row:
            # Only in expected
            comparison['missing_actual'] += 1
            comparison['field_comparisons'].append({
                'field': key,
                'status': 'ONLY_IN_EXPECTED',
                'actual_year1': '',
                'actual_year2': '',
                'expected_year1': expected_row.get('Value_Year_1', ''),
                'expected_year2': expected_row.get('Value_Year_2', ''),
                'year1_match': False,
                'year2_match': False
            })
    
    # Calculate summary statistics
    total_comparable = comparison['matches'] + comparison['mismatches']
    if total_comparable > 0:
        accuracy = (comparison['matches'] / total_comparable) * 100
    else:
        accuracy = 0
    
    comparison['summary'] = {
        'accuracy_percentage': accuracy,
        'total_comparable_fields': total_comparable,
        'fields_with_data_actual': sum(1 for row in actual_data if row.get('Value_Year_1', '').strip() or row.get('Value_Year_2', '').strip()),
        'fields_with_data_expected': sum(1 for row in expected_data if row.get('Value_Year_1', '').strip() or row.get('Value_Year_2', '').strip())
    }
    
    return comparison


def print_comparison_summary(comparison: Dict[str, Any]):
    """Print a summary of the comparison results"""
    print(f"\n📊 Comparison Summary:")
    print(f"   File: {comparison['file_actual']}")
    print(f"   Total Fields: {comparison['total_fields']}")
    print(f"   Matches: {comparison['matches']}")
    print(f"   Mismatches: {comparison['mismatches']}")
    print(f"   Only in Actual: {comparison['missing_expected']}")
    print(f"   Only in Expected: {comparison['missing_actual']}")
    print(f"   Accuracy: {comparison['summary']['accuracy_percentage']:.1f}%")
    print(f"   Fields with Data (Actual): {comparison['summary']['fields_with_data_actual']}")
    print(f"   Fields with Data (Expected): {comparison['summary']['fields_with_data_expected']}")


def print_detailed_mismatches(comparison: Dict[str, Any], max_display: int = 10):
    """Print detailed mismatch information"""
    mismatches = [comp for comp in comparison['field_comparisons'] if comp['status'] == 'MISMATCH']
    
    if mismatches:
        print(f"\n❌ Mismatches (showing first {min(max_display, len(mismatches))}):")
        for i, mismatch in enumerate(mismatches[:max_display]):
            print(f"   {i+1}. {mismatch['field']}")
            print(f"      Year 1: Actual='{mismatch['actual_year1']}' vs Expected='{mismatch['expected_year1']}'")
            print(f"      Year 2: Actual='{mismatch['actual_year2']}' vs Expected='{mismatch['expected_year2']}'")
    
    only_in_actual = [comp for comp in comparison['field_comparisons'] if comp['status'] == 'ONLY_IN_ACTUAL']
    if only_in_actual:
        print(f"\n➕ Only in Actual (showing first {min(max_display, len(only_in_actual))}):")
        for i, field in enumerate(only_in_actual[:max_display]):
            print(f"   {i+1}. {field['field']}")
    
    only_in_expected = [comp for comp in comparison['field_comparisons'] if comp['status'] == 'ONLY_IN_EXPECTED']
    if only_in_expected:
        print(f"\n➖ Only in Expected (showing first {min(max_display, len(only_in_expected))}):")
        for i, field in enumerate(only_in_expected[:max_display]):
            print(f"   {i+1}. {field['field']}")


def main():
    """Main comparison function"""
    print("🔍 Comparing Actual Results vs Expected Templates")
    print("=" * 60)
    
    # Define file pairs to compare
    comparisons = [
        {
            'actual': 'tests/outputs/AFS2024_robust_template.csv',
            'expected': 'core/templates/FS_Input_Template_Fields_AFS2024.csv',
            'name': 'AFS2024'
        },
        {
            'actual': 'tests/outputs/afs_2022_robust_template.csv',
            'expected': 'core/templates/FS_Input_Template_Fields_AFS-2022.csv',
            'name': 'AFS-2022'
        },
        {
            'actual': 'tests/outputs/2021_afs_sec_robust_template.csv',
            'expected': 'core/templates/FS_Input_Template_Fields_2021_AFS_with_SEC_Stamp.csv',
            'name': '2021 AFS with SEC Stamp'
        },
        {
            'actual': 'tests/outputs/afs_2021_2023_robust_template.csv',
            'expected': 'core/templates/FS_Input_Template_Fields_afs_2021_2023.csv',
            'name': 'afs-2021-2023'
        }
    ]
    
    all_results = []
    
    for comp in comparisons:
        if Path(comp['actual']).exists() and Path(comp['expected']).exists():
            print(f"\n{'='*60}")
            print(f"📄 {comp['name']}")
            print(f"{'='*60}")
            
            result = compare_csv_files(comp['actual'], comp['expected'])
            result['name'] = comp['name']
            all_results.append(result)
            
            print_comparison_summary(result)
            print_detailed_mismatches(result)
        else:
            print(f"\n⚠️ Skipping {comp['name']} - files not found")
            print(f"   Actual: {comp['actual']} ({'exists' if Path(comp['actual']).exists() else 'missing'})")
            print(f"   Expected: {comp['expected']} ({'exists' if Path(comp['expected']).exists() else 'missing'})")
    
    # Overall summary
    print(f"\n{'='*60}")
    print("📊 OVERALL SUMMARY")
    print(f"{'='*60}")
    
    if all_results:
        total_matches = sum(r['matches'] for r in all_results)
        total_mismatches = sum(r['mismatches'] for r in all_results)
        total_comparable = total_matches + total_mismatches
        overall_accuracy = (total_matches / total_comparable * 100) if total_comparable > 0 else 0
        
        print(f"Total Files Compared: {len(all_results)}")
        print(f"Total Matches: {total_matches}")
        print(f"Total Mismatches: {total_mismatches}")
        print(f"Overall Accuracy: {overall_accuracy:.1f}%")
        
        print(f"\nPer-File Results:")
        for result in all_results:
            accuracy = result['summary']['accuracy_percentage']
            status = "✅" if accuracy >= 90 else "⚠️" if accuracy >= 70 else "❌"
            print(f"   {status} {result['name']}: {accuracy:.1f}% accuracy")
    
    # Save detailed results
    output_file = "tests/outputs/comparison_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Detailed results saved to: {output_file}")


if __name__ == "__main__":
    main()
