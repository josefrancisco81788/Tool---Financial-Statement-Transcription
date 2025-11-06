#!/usr/bin/env python3
"""
Test PDF conversion functionality
"""

import time
from core.pdf_processor import PDFProcessor

def test_pdf_conversion():
    """Test PDF conversion with timeout"""
    print("🔍 Testing PDF conversion...")
    
    try:
        # Initialize processor
        processor = PDFProcessor()
        print("✅ PDFProcessor initialized")
        
        # Test with a simple PDF file
        pdf_path = "tests/fixtures/light/AFS2024 - statement extracted.pdf"
        
        print(f"📄 Testing with: {pdf_path}")
        
        # Open PDF file
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        print(f"📊 PDF size: {len(pdf_data)} bytes")
        
        # Test conversion with timeout
        start_time = time.time()
        try:
            images, page_info = processor.convert_pdf_to_images(pdf_data)
            elapsed = time.time() - start_time
            
            print(f"✅ Conversion successful in {elapsed:.2f}s")
            print(f"📄 Pages converted: {len(images)}")
            print(f"📄 Page info entries: {len(page_info)}")
            
            if images:
                img = images[0]
                print(f"🖼️ First image size: {img.size}")
                print(f"🖼️ First image mode: {img.mode}")
            
            return True
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Conversion failed after {elapsed:.2f}s: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_pdf_conversion()
