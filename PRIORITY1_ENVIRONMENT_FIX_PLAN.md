# Priority 1: Fix Environment - Detailed Implementation Plan

## **OBJECTIVE**
Fix Poppler configuration to resolve API hanging issue while preserving optimal image quality for image-only PDFs.

## **BACKGROUND**
- **Root Cause**: pdf2image conversion hangs during PDFProcessor initialization
- **Impact**: API startup hangs, blocking all functionality
- **Critical Constraint**: Image-only PDFs require high-quality image conversion for AI accuracy
- **Current State**: pdf2image fails, falls back to PyMuPDF (lower quality)

## **PHASE 1: DIAGNOSE POPPLER ISSUE (1 hour)**

### **Step 1.1: Run Diagnostic Script (15 minutes)**
```bash
python diagnose_poppler_issue.py
```

**Expected Outputs:**
- ✅ Poppler installation status
- ✅ pdf2image import status  
- ✅ pdf2image conversion test (with timeout)
- ✅ PyMuPDF test
- ✅ Environment variables check
- ✅ Antivirus interference test

**Success Criteria:**
- Identify exact cause of hanging
- Determine if Poppler is installed/configured
- Check for antivirus interference

### **Step 1.2: Manual Poppler Check (15 minutes)**
```bash
# Check if Poppler binaries are accessible
where pdftoppm
where pdftocairo
where pdfinfo

# Check PATH for Poppler
echo $PATH | grep -i poppler

# Test Poppler directly
pdftoppm --version
```

**Success Criteria:**
- Poppler binaries found in PATH
- Poppler version information displayed

### **Step 1.3: Test pdf2image in Isolation (15 minutes)**
```python
# Create test script: test_pdf2image_isolated.py
from pdf2image import convert_from_bytes
import time

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

print("Testing pdf2image conversion...")
start_time = time.time()
try:
    images = convert_from_bytes(minimal_pdf, dpi=72)
    elapsed = time.time() - start_time
    print(f"SUCCESS: Converted {len(images)} images in {elapsed:.2f}s")
except Exception as e:
    elapsed = time.time() - start_time
    print(f"FAILED after {elapsed:.2f}s: {e}")
```

**Success Criteria:**
- pdf2image conversion completes within 10 seconds
- No hanging or timeout

### **Step 1.4: Check System Resources (15 minutes)**
```bash
# Check available memory
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory

# Check disk space
dir C:\ | findstr "bytes free"

# Check running processes
tasklist | findstr python
tasklist | findstr poppler
```

**Success Criteria:**
- Sufficient system resources available
- No conflicting processes

## **PHASE 2: FIX POPPLER CONFIGURATION (1-2 hours)**

### **Step 2.1: Install Poppler (if missing) (30 minutes)**

**Option A: Using Chocolatey (Recommended)**
```bash
# Install Chocolatey if not present
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install Poppler
choco install poppler

# Verify installation
where pdftoppm
pdftoppm --version
```

**Option B: Manual Installation**
```bash
# Download Poppler for Windows
# https://github.com/oschwartz10612/poppler-windows/releases
# Extract to C:\poppler
# Add C:\poppler\Library\bin to PATH
```

**Option C: Using Conda**
```bash
conda install -c conda-forge poppler
```

**Success Criteria:**
- Poppler binaries accessible from command line
- `pdftoppm --version` returns version information

### **Step 2.2: Configure PATH (15 minutes)**
```bash
# Add Poppler to PATH permanently
setx PATH "%PATH%;C:\poppler\Library\bin"

# Or add to system PATH via GUI:
# System Properties > Environment Variables > System Variables > PATH
# Add: C:\poppler\Library\bin
```

**Success Criteria:**
- Poppler binaries accessible from new command prompt
- PATH persists after system restart

### **Step 2.3: Set pdf2image Environment Variables (15 minutes)**
```bash
# Set PDF2IMAGE_PATH if needed
setx PDF2IMAGE_PATH "C:\poppler\Library\bin"

# Or set in code:
import os
os.environ['PDF2IMAGE_PATH'] = r'C:\poppler\Library\bin'
```

**Success Criteria:**
- pdf2image can find Poppler binaries
- No "Poppler not found" errors

### **Step 2.4: Test pdf2image with Real PDF (30 minutes)**
```python
# Test with actual financial statement PDF
from pdf2image import convert_from_path
import time

pdf_path = "tests/fixtures/light/AFS2024 - statement extracted.pdf"

print("Testing pdf2image with real PDF...")
start_time = time.time()
try:
    images = convert_from_path(pdf_path, dpi=200)
    elapsed = time.time() - start_time
    print(f"SUCCESS: Converted {len(images)} pages in {elapsed:.2f}s")
    
    # Check image quality
    if images:
        img = images[0]
        print(f"Image size: {img.size}")
        print(f"Image mode: {img.mode}")
        
except Exception as e:
    elapsed = time.time() - start_time
    print(f"FAILED after {elapsed:.2f}s: {e}")
```

**Success Criteria:**
- Real PDF conversion completes successfully
- High-quality images produced (200 DPI)
- No hanging or timeout

## **PHASE 3: TEST API STARTUP (30 minutes)**

### **Step 3.1: Test Module Import (10 minutes)**
```python
# Test importing PDFProcessor without hanging
import time

print("Testing PDFProcessor import...")
start_time = time.time()
try:
    from core.pdf_processor import PDFProcessor
    elapsed = time.time() - start_time
    print(f"SUCCESS: PDFProcessor imported in {elapsed:.2f}s")
    
    # Test instantiation
    processor = PDFProcessor()
    elapsed = time.time() - start_time
    print(f"SUCCESS: PDFProcessor instantiated in {elapsed:.2f}s")
    print(f"PDF Library: {processor.pdf_library}")
    
except Exception as e:
    elapsed = time.time() - start_time
    print(f"FAILED after {elapsed:.2f}s: {e}")
```

**Success Criteria:**
- PDFProcessor imports without hanging
- Initialization completes within 10 seconds
- pdf2image is selected as the library

### **Step 3.2: Test FastAPI Startup (10 minutes)**
```bash
# Start API server
uvicorn api_app:app --host 0.0.0.0 --port 8000 --reload --log-level info
```

**Success Criteria:**
- API starts successfully
- "Application startup complete" message appears
- No hanging during startup

### **Step 3.3: Test Health Endpoint (10 minutes)**
```bash
# Test health endpoint
curl -X GET "http://localhost:8000/health"

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2025-01-XX...",
#   "version": "1.0.0"
# }
```

**Success Criteria:**
- Health endpoint responds quickly
- No hanging or timeout
- Valid JSON response

## **PHASE 4: VALIDATE IMAGE QUALITY (30 minutes)**

### **Step 4.1: Compare Image Quality (15 minutes)**
```python
# Compare pdf2image vs PyMuPDF quality
from pdf2image import convert_from_path
import fitz
from PIL import Image
import time

pdf_path = "tests/fixtures/light/AFS2024 - statement extracted.pdf"

# Test pdf2image
print("Testing pdf2image quality...")
start_time = time.time()
pdf2image_images = convert_from_path(pdf_path, dpi=200)
pdf2image_time = time.time() - start_time
print(f"pdf2image: {len(pdf2image_images)} pages in {pdf2image_time:.2f}s")

# Test PyMuPDF
print("Testing PyMuPDF quality...")
start_time = time.time()
doc = fitz.Document(pdf_path)
pymupdf_images = []
for page_num in range(len(doc)):
    page = doc.load_page(page_num)
    pix = page.get_pixmap(matrix=fitz.Matrix(200/72, 200/72))
    img_data = pix.tobytes("png")
    pymupdf_images.append(Image.open(io.BytesIO(img_data)))
doc.close()
pymupdf_time = time.time() - start_time
print(f"PyMuPDF: {len(pymupdf_images)} pages in {pymupdf_time:.2f}s")

# Compare first page
if pdf2image_images and pymupdf_images:
    pdf2img = pdf2image_images[0]
    pymupdf_img = pymupdf_images[0]
    
    print(f"pdf2image size: {pdf2img.size}, mode: {pdf2img.mode}")
    print(f"PyMuPDF size: {pymupdf_img.size}, mode: {pymupdf_img.mode}")
    
    # Save for visual comparison
    pdf2img.save("pdf2image_test.png")
    pymupdf_img.save("pymupdf_test.png")
    print("Images saved for visual comparison")
```

**Success Criteria:**
- Both libraries produce images
- pdf2image produces higher quality images
- No significant performance difference

### **Step 4.2: Test AI Extraction Accuracy (15 minutes)**
```python
# Test AI extraction with both image qualities
from core.extractor import FinancialDataExtractor

extractor = FinancialDataExtractor()

# Test with pdf2image quality
print("Testing AI extraction with pdf2image quality...")
start_time = time.time()
try:
    result1 = extractor.extract_from_image(pdf2image_images[0])
    elapsed1 = time.time() - start_time
    print(f"pdf2image extraction: {elapsed1:.2f}s")
    print(f"Extracted fields: {len(result1.get('line_items', {}))}")
except Exception as e:
    print(f"pdf2image extraction failed: {e}")

# Test with PyMuPDF quality
print("Testing AI extraction with PyMuPDF quality...")
start_time = time.time()
try:
    result2 = extractor.extract_from_image(pymupdf_images[0])
    elapsed2 = time.time() - start_time
    print(f"PyMuPDF extraction: {elapsed2:.2f}s")
    print(f"Extracted fields: {len(result2.get('line_items', {}))}")
except Exception as e:
    print(f"PyMuPDF extraction failed: {e}")
```

**Success Criteria:**
- AI extraction works with both image qualities
- pdf2image produces better extraction results
- No significant performance difference

## **SUCCESS CRITERIA**

### **Phase 1 Success:**
- ✅ Diagnostic script identifies root cause
- ✅ Poppler installation status confirmed
- ✅ pdf2image conversion test completes without hanging

### **Phase 2 Success:**
- ✅ Poppler properly installed and configured
- ✅ PATH includes Poppler binaries
- ✅ pdf2image can convert real PDFs successfully
- ✅ High-quality images produced (200 DPI)

### **Phase 3 Success:**
- ✅ PDFProcessor imports without hanging
- ✅ FastAPI starts successfully
- ✅ Health endpoint responds quickly
- ✅ No hanging during startup

### **Phase 4 Success:**
- ✅ pdf2image produces higher quality images than PyMuPDF
- ✅ AI extraction accuracy is maintained
- ✅ Performance is acceptable for 30-80 page documents

## **ROLLBACK PLAN**

If environment fix fails:

1. **Immediate Rollback**: Revert to PyMuPDF-only approach
2. **Document Issues**: Record specific Poppler configuration problems
3. **Alternative Solutions**: Consider Docker containerization
4. **Long-term Fix**: Plan proper environment setup for production

## **TIMELINE**

- **Phase 1**: 1 hour (Diagnosis)
- **Phase 2**: 1-2 hours (Fix Configuration)
- **Phase 3**: 30 minutes (Test API)
- **Phase 4**: 30 minutes (Validate Quality)

**Total Time**: 3-4 hours

## **RISK MITIGATION**

- **Low Risk**: No code changes, only environment configuration
- **Reversible**: Can easily revert to PyMuPDF if needed
- **Testable**: Each phase has clear success criteria
- **Documented**: All steps are documented for future reference
