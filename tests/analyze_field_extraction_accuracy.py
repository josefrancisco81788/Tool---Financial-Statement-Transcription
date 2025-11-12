"""
Analyze field extraction accuracy using the better metric: Fields Extracted / Fields Expected
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


def count_fields_with_data(data: List[Dict[str, str]]) -> int:
    """Count fields that have actual data (non-empty values)"""
    count = 0
    for row in data:
        year1 = row.get('Value_Year_1', '').strip()
        year2 = row.get('Value_Year_2', '').strip()
        if year1 or year2:  # Has data in either year
            count += 1
    return count


def analyze_field_extraction_accuracy():
    """Analyze field extraction using the better metric"""
    print("🔍 Field Extraction Accuracy Analysis")
    print("=" * 60)
    print("Using metric: Fields Extracted / Fields Expected")
    print("(Only counting fields with actual data)")
    print()
    
    # Define file pairs to analyze
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
    
    results = []
    total_extracted = 0
    total_expected = 0
    
    for comp in comparisons:
        if Path(comp['actual']).exists() and Path(comp['expected']).exists():
            print(f"📄 {comp['name']}")
            print("-" * 40)
            
            # Load data
            actual_data = load_csv_data(comp['actual'])
            expected_data = load_csv_data(comp['expected'])
            
            # Count fields with data
            actual_fields_with_data = count_fields_with_data(actual_data)
            expected_fields_with_data = count_fields_with_data(expected_data)
            
            # Calculate extraction rate
            if expected_fields_with_data > 0:
                extraction_rate = (actual_fields_with_data / expected_fields_with_data) * 100
            else:
                extraction_rate = 0
            
            # Determine status
            if extraction_rate >= 80:
                status = "✅ EXCELLENT"
            elif extraction_rate >= 60:
                status = "⚠️ GOOD"
            elif extraction_rate >= 40:
                status = "⚠️ ACCEPTABLE"
            else:
                status = "❌ NEEDS IMPROVEMENT"
            
            print(f"   Fields Extracted: {actual_fields_with_data}")
            print(f"   Fields Expected:  {expected_fields_with_data}")
            print(f"   Extraction Rate:  {extraction_rate:.1f}%")
            print(f"   Status:           {status}")
            print()
            
            results.append({
                'name': comp['name'],
                'fields_extracted': actual_fields_with_data,
                'fields_expected': expected_fields_with_data,
                'extraction_rate': extraction_rate,
                'status': status
            })
            
            total_extracted += actual_fields_with_data
            total_expected += expected_fields_with_data
        else:
            print(f"⚠️ Skipping {comp['name']} - files not found")
    
    # Overall summary
    if total_expected > 0:
        overall_extraction_rate = (total_extracted / total_expected) * 100
    else:
        overall_extraction_rate = 0
    
    print("=" * 60)
    print("📊 OVERALL SUMMARY")
    print("=" * 60)
    print(f"Total Fields Extracted: {total_extracted}")
    print(f"Total Fields Expected:  {total_expected}")
    print(f"Overall Extraction Rate: {overall_extraction_rate:.1f}%")
    print()
    
    # Per-file summary table
    print("📋 Per-File Results:")
    print("-" * 60)
    print(f"{'File':<25} {'Extracted':<10} {'Expected':<10} {'Rate':<8} {'Status'}")
    print("-" * 60)
    for result in results:
        print(f"{result['name']:<25} {result['fields_extracted']:<10} {result['fields_expected']:<10} {result['extraction_rate']:<7.1f}% {result['status']}")
    
    print()
    print("🎯 INTERPRETATION:")
    print("-" * 60)
    print("This metric shows how many fields with actual data were extracted")
    print("compared to how many fields with data were expected.")
    print()
    print("The previous 79.9% 'accuracy' included empty field matches,")
    print("which artificially inflated the score. This metric is more")
    print("meaningful for assessing actual data extraction performance.")
    
    # Save results
    output_file = "tests/outputs/field_extraction_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'overall_extraction_rate': overall_extraction_rate,
            'total_extracted': total_extracted,
            'total_expected': total_expected,
            'per_file_results': results
        }, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    analyze_field_extraction_accuracy()
