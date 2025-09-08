#!/usr/bin/env python3
"""
Debug script to test image resizing for large origin documents
"""

import os
import sys
import base64
from PIL import Image

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.extractor import FinancialDataExtractor
from core.pdf_processor import PDFProcessor

def resize_image_if_needed(image, max_size=(1024, 1024)):
    """Resize image if it's too large for the API"""
    if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
        print(f"📏 Resizing image from {image.size} to fit within {max_size}")
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        print(f"📏 New size: {image.size}")
    return image

def test_resized_image():
    """Test with resized image"""
    
    print("🔍 Testing with resized image...")
    
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
        
        if len(images) == 0:
            print("❌ No images generated")
            return False
        
        # Test with first image
        first_image = images[0]
        print(f"📸 Original image size: {first_image.size}")
        
        # Resize if needed
        resized_image = resize_image_if_needed(first_image)
        
        # Test base64 encoding
        print("\n🔄 Testing base64 encoding with resized image...")
        try:
            encoded = extractor.encode_image(resized_image)
            print(f"✅ Base64 encoding successful")
            print(f"📏 Encoded length: {len(encoded)} characters")
            
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
        
        # Test AI Vision API call with resized image
        print("\n🤖 Testing AI Vision API call with resized image...")
        try:
            result = extractor.extract_comprehensive_financial_data(resized_image)
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
    success = test_resized_image()
    if success:
        print("\n🎉 Resized image test passed!")
    else:
        print("\n💥 Resized image test failed!")
        sys.exit(1)
