#!/usr/bin/env python3
"""
Diagnostic script to identify Poppler configuration issues causing API hanging.
This script tests each component individually to isolate the problem.
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def test_poppler_installation():
    """Test if Poppler is installed and accessible"""
    print("🔍 Testing Poppler installation...")
    
    # Test 1: Check if poppler-utils is installed
    try:
        import poppler_utils
        print("✅ poppler-utils package is installed")
    except ImportError:
        print("❌ poppler-utils package is NOT installed")
        return False
    
    # Test 2: Check if Poppler binaries are in PATH
    poppler_binaries = ['pdftoppm', 'pdftocairo', 'pdfinfo']
    poppler_found = []
    
    for binary in poppler_binaries:
        try:
            result = subprocess.run(['where', binary], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                poppler_found.append(binary)
                print(f"✅ {binary} found in PATH: {result.stdout.strip()}")
            else:
                print(f"❌ {binary} NOT found in PATH")
        except subprocess.TimeoutExpired:
            print(f"⏰ {binary} command timed out")
        except Exception as e:
            print(f"❌ Error checking {binary}: {e}")
    
    if poppler_found:
        print(f"✅ Poppler binaries found: {', '.join(poppler_found)}")
        return True
    else:
        print("❌ No Poppler binaries found in PATH")
        return False

def test_pdf2image_import():
    """Test if pdf2image can be imported"""
    print("\n🔍 Testing pdf2image import...")
    
    try:
        from pdf2image import convert_from_bytes
        print("✅ pdf2image imported successfully")
        return True
    except ImportError as e:
        print(f"❌ pdf2image import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error importing pdf2image: {e}")
        return False

def test_pdf2image_conversion():
    """Test pdf2image conversion with timeout"""
    print("\n🔍 Testing pdf2image conversion...")
    
    try:
        from pdf2image import convert_from_bytes
        
        # Create a minimal test PDF
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
        
        print("  - Attempting conversion with 10-second timeout...")
        start_time = time.time()
        
        # Test with timeout using subprocess
        try:
            result = subprocess.run([
                sys.executable, '-c', 
                f"""
import sys
sys.path.insert(0, '{os.getcwd()}')
from pdf2image import convert_from_bytes
minimal_pdf = {minimal_pdf}
images = convert_from_bytes(minimal_pdf, dpi=72)
print(f'SUCCESS: Converted {{len(images)}} images')
"""
            ], capture_output=True, text=True, timeout=10)
            
            elapsed = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ pdf2image conversion successful in {elapsed:.2f}s")
                print(f"   Output: {result.stdout.strip()}")
                return True
            else:
                print(f"❌ pdf2image conversion failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            print(f"⏰ pdf2image conversion TIMED OUT after {elapsed:.2f}s")
            print("   This is likely the cause of the API hanging!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing pdf2image conversion: {e}")
        return False

def test_pymupdf():
    """Test PyMuPDF functionality"""
    print("\n🔍 Testing PyMuPDF...")
    
    try:
        import fitz
        
        # Test with timeout
        start_time = time.time()
        try:
            result = subprocess.run([
                sys.executable, '-c', 
                """
import fitz
doc = fitz.Document()
doc.close()
print('SUCCESS: PyMuPDF test passed')
"""
            ], capture_output=True, text=True, timeout=5)
            
            elapsed = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ PyMuPDF test successful in {elapsed:.2f}s")
                return True
            else:
                print(f"❌ PyMuPDF test failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            print(f"⏰ PyMuPDF test TIMED OUT after {elapsed:.2f}s")
            return False
            
    except ImportError as e:
        print(f"❌ PyMuPDF import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing PyMuPDF: {e}")
        return False

def test_environment_variables():
    """Test relevant environment variables"""
    print("\n🔍 Testing environment variables...")
    
    # Check PATH
    path = os.environ.get('PATH', '')
    print(f"PATH length: {len(path)} characters")
    
    # Look for Poppler in PATH
    poppler_paths = [p for p in path.split(os.pathsep) if 'poppler' in p.lower()]
    if poppler_paths:
        print(f"✅ Poppler paths found in PATH: {poppler_paths}")
    else:
        print("❌ No Poppler paths found in PATH")
    
    # Check for pdf2image specific environment variables
    pdf2image_path = os.environ.get('PDF2IMAGE_PATH')
    if pdf2image_path:
        print(f"✅ PDF2IMAGE_PATH set: {pdf2image_path}")
    else:
        print("❌ PDF2IMAGE_PATH not set")

def test_antivirus_interference():
    """Test for potential antivirus interference"""
    print("\n🔍 Testing for antivirus interference...")
    
    # Check if we can create temporary files
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(b"test")
            print("✅ Can create temporary files")
    except Exception as e:
        print(f"❌ Cannot create temporary files: {e}")
        print("   This might indicate antivirus interference")
    
    # Check if we can run subprocesses
    try:
        result = subprocess.run(['echo', 'test'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Can run subprocesses")
        else:
            print("❌ Subprocess execution failed")
    except subprocess.TimeoutExpired:
        print("⏰ Subprocess execution timed out")
        print("   This might indicate antivirus interference")
    except Exception as e:
        print(f"❌ Error running subprocess: {e}")

def main():
    """Run all diagnostic tests"""
    print("🚀 Starting Poppler Environment Diagnosis")
    print("=" * 50)
    
    tests = [
        ("Poppler Installation", test_poppler_installation),
        ("pdf2image Import", test_pdf2image_import),
        ("pdf2image Conversion", test_pdf2image_conversion),
        ("PyMuPDF Test", test_pymupdf),
        ("Environment Variables", test_environment_variables),
        ("Antivirus Interference", test_antivirus_interference),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC RESULTS:")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    # Identify the likely cause
    if not results.get("pdf2image Conversion", True):
        print("\n🎯 LIKELY CAUSE: pdf2image conversion is hanging")
        print("   This is causing the API to hang during startup")
        print("\n💡 RECOMMENDED FIXES:")
        print("   1. Fix Poppler installation/configuration")
        print("   2. Check antivirus settings")
        print("   3. Verify PATH configuration")
    elif not results.get("Poppler Installation", True):
        print("\n🎯 LIKELY CAUSE: Poppler is not properly installed")
        print("   pdf2image requires Poppler to convert PDFs to images")
        print("\n💡 RECOMMENDED FIXES:")
        print("   1. Install Poppler binaries")
        print("   2. Add Poppler to PATH")
        print("   3. Set PDF2IMAGE_PATH environment variable")
    else:
        print("\n✅ All tests passed - the issue might be elsewhere")

if __name__ == "__main__":
    main()
