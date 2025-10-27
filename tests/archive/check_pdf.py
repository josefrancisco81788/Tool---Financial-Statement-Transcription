#!/usr/bin/env python3
"""
Check PDF content
"""

import fitz

def check_pdf():
    pdf_path = 'tests/fixtures/light/AFS2024 - statement extracted.pdf'
    
    try:
        doc = fitz.open(pdf_path)
        print(f"📄 PDF: {pdf_path}")
        print(f"📊 Total pages: {len(doc)}")
        
        total_text = 0
        for i in range(len(doc)):
            page = doc[i]
            text = page.get_text()
            total_text += len(text)
            print(f"   Page {i+1} text length: {len(text)}")
            
            if len(text) > 0:
                print(f"   First 200 chars: {text[:200]}")
        
        print(f"\n📈 Total text across all pages: {total_text}")
        
        if total_text == 0:
            print("⚠️  This appears to be a scanned/image-based PDF with no extractable text")
            print("💡 The AI vision models should still be able to process this as images")
        
        doc.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_pdf()












