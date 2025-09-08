"""
Debug script to see what the AI is actually returning

This will help us understand why the JSON parsing is failing.
"""

import os
import sys
import json
import base64
from pathlib import Path
from PIL import Image
import io

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.extractor import FinancialDataExtractor


def debug_ai_response():
    """Debug what the AI is actually returning"""
    print("🔍 Debugging AI Response...")
    print("=" * 50)
    
    try:
        # Initialize extractor
        extractor = FinancialDataExtractor()
        
        # Create a simple test image
        print("📸 Creating test image...")
        test_img = Image.new('RGB', (200, 200), color='white')
        img_buffer = io.BytesIO()
        test_img.save(img_buffer, format='PNG')
        img_data = img_buffer.getvalue()
        
        # Encode to base64 using the extractor's method
        base64_image = extractor.encode_image(img_data)
        print(f"✅ Image encoded: {len(base64_image)} characters")
        
        # Build prompt
        print("📝 Building prompt...")
        prompt = extractor._build_extraction_prompt("financial_statement")
        print(f"✅ Prompt built: {len(prompt)} characters")
        
        # Make the API call directly to see raw response
        print("🌐 Making API call...")
        
        # Use the extractor's client directly
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
        print("-" * 50)
        print(raw_response)
        print("-" * 50)
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
                print(json_str)
                
                # Try to parse
                parsed_json = json.loads(json_str)
                print("✅ JSON parsing successful!")
                print(f"📊 Parsed data keys: {list(parsed_json.keys())}")
                
            else:
                print("❌ No JSON structure found in response")
                print("🔍 Looking for other patterns...")
                
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
        return None


if __name__ == "__main__":
    debug_ai_response()
