#!/usr/bin/env python3
"""
Poppler Installation Test Script
Tests if Poppler is properly installed and functioning with pdf2image
"""

import sys
import traceback

def test_poppler_installation():
    """Test that Poppler is properly installed and functioning"""
    print("🔍 Testing Poppler Installation...")
    print("=" * 50)
    
    # Test 1: Import pdf2image
    try:
        from pdf2image import convert_from_bytes
        print("✅ pdf2image import: SUCCESS")
    except ImportError as e:
        print(f"❌ pdf2image import: FAILED - {e}")
        return False
    
    # Test 2: Create minimal PDF
    minimal_pdf = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000074 00000 n 
0000000120 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
0
%%EOF"""
    
    print("✅ Minimal PDF created: SUCCESS")
    
    # Test 3: Convert PDF to images using pdf2image
    try:
        print("🔄 Testing PDF to image conversion...")
        images = convert_from_bytes(minimal_pdf, dpi=72)
        
        if images and len(images) == 1:
            print(f"✅ PDF conversion: SUCCESS - {len(images)} image(s) created")
            print(f"   Image size: {images[0].size}")
            print(f"   Image mode: {images[0].mode}")
        else:
            print(f"❌ PDF conversion: FAILED - Expected 1 image, got {len(images) if images else 0}")
            return False
            
    except Exception as e:
        print(f"❌ PDF conversion: FAILED - {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Full traceback:")
        traceback.print_exc()
        return False
    
    # Test 4: Test with higher DPI
    try:
        print("🔄 Testing high DPI conversion...")
        images_hd = convert_from_bytes(minimal_pdf, dpi=200)
        
        if images_hd and len(images_hd) == 1:
            print(f"✅ High DPI conversion: SUCCESS - {len(images_hd)} image(s) created")
            print(f"   High DPI image size: {images_hd[0].size}")
        else:
            print(f"❌ High DPI conversion: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ High DPI conversion: FAILED - {e}")
        return False
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Poppler is properly installed and functioning")
    print("✅ pdf2image is ready for production use")
    return True

def test_system_info():
    """Display system information for debugging"""
    print("\n📊 System Information:")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    # Try to get pdf2image version
    try:
        import pdf2image
        print(f"pdf2image version: {pdf2image.__version__}")
    except:
        print("pdf2image version: Unknown")
    
    # Try to get PIL version
    try:
        from PIL import Image
        print(f"Pillow version: {Image.__version__}")
    except:
        print("Pillow version: Unknown")

if __name__ == "__main__":
    print("🧪 Poppler Installation Test")
    print("=" * 50)
    
    # Display system info
    test_system_info()
    
    # Run main test
    success = test_poppler_installation()
    
    if success:
        print("\n🚀 Ready to proceed with Poppler integration!")
        sys.exit(0)
    else:
        print("\n❌ Poppler installation issues detected.")
        print("Please refer to POPPLER_INTEGRATION_PLAN.md for installation instructions.")
        sys.exit(1)



