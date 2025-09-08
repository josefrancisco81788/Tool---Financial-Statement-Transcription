"""
Debug script to test with a real financial document image

This will help us see if the issue is with the image content or the encoding.
"""

import os
import sys
import json
import base64
from pathlib import Path
import fitz  # PyMuPDF

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.extractor import FinancialDataExtractor


def debug_real_image():
    """Debug with a real financial document image"""
    print("🔍 Debugging with Real Financial Document Image...")
    print("=" * 60)
    
    try:
        # Initialize extractor
        extractor = FinancialDataExtractor()
        
        # Load a real PDF file
        pdf_path = Path("tests/fixtures/light/AFS2024 - statement extracted.pdf")
        if not pdf_path.exists():
            print(f"❌ PDF file not found: {pdf_path}")
            return
        
        print(f"📄 Loading PDF: {pdf_path.name}")
        
        # Convert first page to image
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        doc = fitz.Document(stream=pdf_data, filetype="pdf")
        page = doc[0]  # First page
        
        # Convert to image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
        img_data = pix.tobytes("png")
        doc.close()
        
        print(f"✅ PDF converted to image: {len(img_data)} bytes")
        
        # Encode to base64
        base64_image = extractor.encode_image(img_data)
        print(f"✅ Image encoded: {len(base64_image)} characters")
        
        # Build prompt
        print("📝 Building prompt...")
        prompt = extractor._build_extraction_prompt("financial_statement")
        print(f"✅ Prompt built: {len(prompt)} characters")
        
        # Make the API call
        print("🌐 Making API call...")
        
        response = extractor.client.chat.completions.create(
            model=extractor.config.OPENAI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=extractor.config.OPENAI_MAX_TOKENS,
            temperature=0.1
        )
        
        # Get the raw response
        raw_response = response.choices[0].message.content
        print(f"📥 Raw AI Response:")
        print("-" * 60)
        print(raw_response)
        print("-" * 60)
        print(f"📊 Response length: {len(raw_response)} characters")
        
        # Try to parse as JSON
        print("\n🔍 Attempting JSON parsing...")
        try:
            # Try to find JSON in the response
            json_start = raw_response.find('{')
            json_end = raw_response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = raw_response[json_start:json_end]
                print(f"📋 Extracted JSON string:")
                print(json_str[:500] + "..." if len(json_str) > 500 else json_str)
                
                # Try to parse
                parsed_json = json.loads(json_str)
                print("✅ JSON parsing successful!")
                print(f"📊 Parsed data keys: {list(parsed_json.keys())}")
                
                # Show some sample data
                if 'financial_data' in parsed_json:
                    financial_data = parsed_json['financial_data']
                    if isinstance(financial_data, list) and len(financial_data) > 0:
                        print(f"📊 Sample financial data: {financial_data[0]}")
                
            else:
                print("❌ No JSON structure found in response")
                
                # Look for other patterns
                if '```json' in raw_response:
                    print("📋 Found ```json block")
                elif '```' in raw_response:
                    print("📋 Found ``` block")
                else:
                    print("📋 No code blocks found")
                    
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print("🔍 Response might contain non-JSON content")
        
        return raw_response
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    debug_real_image()
