"""
Test Phase 3: Multi-page year extraction through full pipeline
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import FinancialDataExtractor, PDFProcessor

# Test the problematic file through FULL pipeline
test_file = 'tests/fixtures/light/afs-2021-2023 - statement extracted.pdf'
expected_years = [2022, 2021, 2020]

print("Testing Phase 3: Multi-page year extraction")
print(f"Expected: {expected_years}")
print()

# Explicitly set provider to Anthropic (Claude is also the default)
# This test explicitly sets it to ensure consistent behavior
os.environ['AI_PROVIDER'] = 'anthropic'  # Faster

extractor = FinancialDataExtractor()
pdf_processor = PDFProcessor(extractor)

with open(test_file, 'rb') as f:
    result = pdf_processor.process_pdf_with_vector_db(f.read(), enable_parallel=False)

if result:
    year_field = result.get('template_mappings', {}).get('Year', {})
    extracted = [
        year_field.get('Value_Year_1'),
        year_field.get('Value_Year_2'),
        year_field.get('Value_Year_3'),
        year_field.get('Value_Year_4')
    ]
    extracted = [y for y in extracted if y is not None]
    
    print(f"\nExtracted years: {extracted}")
    print(f"Match: {extracted == expected_years}")
    print(f"Total fields: {len(result.get('template_mappings', {}))}")
else:
    print("No result!")













