"""
Quick test to verify enhanced year extraction on the 3-year document
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import FinancialDataExtractor, PDFProcessor

# Test the problematic file
test_file = 'tests/fixtures/light/afs-2021-2023 - statement extracted.pdf'
expected_years = [2022, 2021, 2020]

print("Testing enhanced year extraction on afs-2021-2023...")
print(f"Expected: {expected_years}")
print()

# Test with both providers
for provider in ['openai', 'anthropic']:
    os.environ['AI_PROVIDER'] = provider
    print(f"Provider: {provider.upper()}")
    
    extractor = FinancialDataExtractor()
    pdf_processor = PDFProcessor(extractor)
    
    with open(test_file, 'rb') as f:
        pdf_bytes = f.read()
    
    images, page_info = pdf_processor.convert_pdf_to_images(pdf_bytes, enable_parallel=False)
    first_page_image = extractor.encode_image(images[0])
    year_data = extractor.extract_years_from_image(first_page_image)
    
    extracted = year_data.get('years', [])
    print(f"  Extracted: {extracted}")
    print(f"  Match: {extracted == expected_years}")
    print()

print("Done!")









