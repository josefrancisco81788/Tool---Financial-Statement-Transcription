"""
Debug AFS2024 extraction to see what's happening with the AI response
"""

import os
import sys
import json
import time
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.extractor import FinancialDataExtractor
from core.pdf_processor import PDFProcessor


def debug_afs2024_extraction():
    """Debug the AFS2024 extraction process step by step"""
    print("🔍 Debugging AFS2024 extraction...")
    print("=" * 60)
    
    try:
        # Initialize components
        print("🔧 Initializing components...")
        extractor = FinancialDataExtractor()
        processor = PDFProcessor(extractor)
        print("✅ Components initialized")
        
        # Load PDF
        pdf_path = "tests/fixtures/light/AFS2024 - statement extracted.pdf"
        print(f"📄 Loading PDF: {Path(pdf_path).name}")
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        print(f"✅ PDF loaded: {len(pdf_data)} bytes")
        
        # Convert PDF to images
        print("🔄 Converting PDF to images...")
        start_time = time.time()
        images, metadata = processor.convert_pdf_to_images(pdf_data)
        conversion_time = time.time() - start_time
        print(f"✅ PDF conversion completed: {conversion_time:.2f}s")
        print(f"📊 Generated {len(images)} images")
        
        # Process each image
        for i, image in enumerate(images):
            print(f"\n🔄 Processing image {i+1}/{len(images)}...")
            try:
                # Extract data from image
                start_time = time.time()
                result = extractor.extract_from_image(image)
                extraction_time = time.time() - start_time
                print(f"✅ Image {i+1} processed: {extraction_time:.2f}s")
                
                if result:
                    print(f"📊 Result type: {type(result)}")
                    print(f"📊 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                    
                    # Save raw result for inspection
                    output_file = f"tests/outputs/afs2024_debug_image_{i+1}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    print(f"💾 Raw result saved: {output_file}")
                    
                    # Show sample of the result
                    if isinstance(result, dict):
                        print(f"📋 Sample fields:")
                        for key, value in list(result.items())[:5]:
                            print(f"  {key}: {value}")
                else:
                    print("❌ No result from image extraction")
                    
            except Exception as e:
                print(f"❌ Error processing image {i+1}: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n🎉 Debug completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_afs2024_extraction()
