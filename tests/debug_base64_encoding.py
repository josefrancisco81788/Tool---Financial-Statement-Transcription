#!/usr/bin/env python3
"""
Debug script to test base64 encoding issues with origin documents
"""

import os
import sys
import base64
from PIL import Image

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.extractor import FinancialDataExtractor
from core.pdf_processor import PDFProcessor

def test_base64_encoding():
    """Test base64 encoding with a single page from origin document"""
    
    print("🔍 Testing base64 encoding with origin document...")
    
    # Initialize components
    extractor = FinancialDataExtractor()
    pdf_processor = PDFProcessor()
    
    # File paths
    pdf_path = "tests/fixtures/origin/AFS2024.pdf"
    
    try:
        # Convert PDF to images (just first page)
        print(f"📄 Converting first page of: {pdf_path}")
        with open(pdf_path, 'rb') as pdf_file:
            images, page_info = pdf_processor.convert_pdf_to_images(pdf_file)
        
        print(f"✅ Converted to {len(images)} images")
        
        if len(images) == 0:
            print("❌ No images generated")
            return False
        
        # Test with first image
        first_image = images[0]
        print(f"📸 First image type: {type(first_image)}")
        print(f"📸 First image size: {first_image.size}")
        print(f"📸 First image mode: {first_image.mode}")
        
        # Test base64 encoding
        print("\n🔄 Testing base64 encoding...")
        try:
            encoded = extractor.encode_image(first_image)
            print(f"✅ Base64 encoding successful")
            print(f"📏 Encoded length: {len(encoded)} characters")
            print(f"📏 First 100 chars: {encoded[:100]}...")
            
            # Test if it's valid base64
            try:
                decoded = base64.b64decode(encoded)
                print(f"✅ Base64 decoding successful")
                print(f"📏 Decoded length: {len(decoded)} bytes")
            except Exception as e:
                print(f"❌ Base64 decoding failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Base64 encoding failed: {e}")
            return False
        
        # Test AI Vision API call with this image
        print("\n🤖 Testing AI Vision API call...")
        try:
            result = extractor.extract_comprehensive_financial_data(first_image)
            if result:
                print(f"✅ AI Vision API call successful")
                print(f"📊 Result keys: {list(result.keys())}")
                return True
            else:
                print(f"❌ AI Vision API call returned no data")
                return False
        except Exception as e:
            print(f"❌ AI Vision API call failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_base64_encoding()
    if success:
        print("\n🎉 Base64 encoding test passed!")
    else:
        print("\n💥 Base64 encoding test failed!")
        sys.exit(1)
