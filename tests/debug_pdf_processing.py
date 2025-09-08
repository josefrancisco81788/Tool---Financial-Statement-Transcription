"""
Debug script for PDF processing pipeline

This will help us identify where the PDF processing is getting stuck.
"""

import os
import sys
import time
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.extractor import FinancialDataExtractor
from core.pdf_processor import PDFProcessor


def debug_pdf_processing():
    """Debug the PDF processing pipeline step by step"""
    print("🔍 Debugging PDF Processing Pipeline...")
    print("=" * 60)
    
    try:
        # Initialize components
        print("🔧 Initializing components...")
        extractor = FinancialDataExtractor()
        processor = PDFProcessor(extractor)
        print("✅ Components initialized")
        
        # Load test PDF
        pdf_path = Path("tests/fixtures/light/AFS2024 - statement extracted.pdf")
        print(f"📄 Loading PDF: {pdf_path.name}")
        
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        print(f"✅ PDF loaded: {len(pdf_data)} bytes")
        
        # Step 1: Convert PDF to images
        print("\n🖼️ Step 1: Converting PDF to images...")
        start_time = time.time()
        
        images, page_info = processor.convert_pdf_to_images(pdf_data, enable_parallel=False)
        
        step1_time = time.time() - start_time
        print(f"✅ PDF conversion completed: {step1_time:.2f}s")
        print(f"📊 Images: {len(images) if images else 0}")
        print(f"📊 Page info: {len(page_info) if page_info else 0}")
        
        if not images:
            print("❌ No images generated")
            return
        
        # Step 2: Classify financial statement pages
        print("\n🔍 Step 2: Classifying financial statement pages...")
        start_time = time.time()
        
        financial_pages = processor.classify_financial_statement_pages(page_info, enable_parallel=False)
        
        step2_time = time.time() - start_time
        print(f"✅ Classification completed: {step2_time:.2f}s")
        print(f"📊 Financial pages: {len(financial_pages) if financial_pages else 0}")
        
        if not financial_pages:
            print("⚠️ No financial pages detected, using fallback")
            financial_pages = [{
                'page_num': 1,
                'statement_type': 'Unknown',
                'confidence': 0.1,
                'image': images[0],
                'text': page_info[0]['text'] if page_info else "",
                'number_density': 0,
                'financial_numbers_count': 0,
                'number_density_score': 0
            }]
        
        # Step 3: Test image encoding
        print("\n🔐 Step 3: Testing image encoding...")
        start_time = time.time()
        
        first_page = financial_pages[0]
        base64_image = extractor.encode_image(first_page['image'])
        
        step3_time = time.time() - start_time
        print(f"✅ Image encoding completed: {step3_time:.2f}s")
        print(f"📊 Base64 length: {len(base64_image)} characters")
        
        # Step 4: Test extraction (with timeout)
        print("\n🤖 Step 4: Testing extraction (with 30s timeout)...")
        start_time = time.time()
        
        try:
            # Test extraction without timeout for now
            extracted_data = extractor.extract_comprehensive_financial_data(
                base64_image, 
                first_page['statement_type'], 
                first_page['text']
            )
            
            step4_time = time.time() - start_time
            print(f"✅ Extraction completed: {step4_time:.2f}s")
            print(f"📊 Extracted data keys: {list(extracted_data.keys()) if extracted_data else 'None'}")
            
            if extracted_data and 'line_items' in extracted_data:
                line_items = extracted_data['line_items']
                print(f"📊 Line items categories: {list(line_items.keys()) if isinstance(line_items, dict) else 'Not a dict'}")
            
        except TimeoutError:
            step4_time = time.time() - start_time
            print(f"⏰ Extraction timed out after {step4_time:.2f}s")
            print("❌ This is where the issue is - the extraction is taking too long")
        except Exception as e:
            step4_time = time.time() - start_time
            print(f"❌ Extraction failed after {step4_time:.2f}s: {e}")
        
        # Summary
        print(f"\n📊 Processing Summary:")
        print(f"  PDF Conversion: {step1_time:.2f}s")
        print(f"  Classification: {step2_time:.2f}s")
        print(f"  Image Encoding: {step3_time:.2f}s")
        print(f"  Extraction: {step4_time:.2f}s")
        print(f"  Total: {step1_time + step2_time + step3_time + step4_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_pdf_processing()
