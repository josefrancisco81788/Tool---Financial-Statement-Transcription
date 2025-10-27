"""
Test script to check what data is actually being extracted
"""

import sys
from pathlib import Path
import os

# Load environment
def load_env():
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"').strip("'")
                    os.environ[key] = value

load_env()

# Add project root to path
sys.path.insert(0, '.')

from core.extractor import FinancialDataExtractor
import base64

def test_extraction():
    print("🧪 Testing extraction data format...")
    
    # Initialize extractor
    extractor = FinancialDataExtractor()
    print(f"Provider: {extractor.provider}")
    print(f"Config AI Provider: {extractor.config.AI_PROVIDER}")
    
    # Create a minimal test image (1x1 pixel PNG)
    test_image = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
    base64_image = base64.b64encode(test_image).decode('utf-8')
    
    try:
        # Test extraction
        result = extractor.extract_comprehensive_financial_data(base64_image, 'test')
        print(f"\n📊 Extraction Result:")
        print(f"Type: {type(result)}")
        print(f"Length: {len(result) if result else 0}")
        print(f"Content (first 500 chars): {result[:500] if result else None}")
        
        # Check if it's JSON
        if result:
            try:
                import json
                parsed = json.loads(result)
                print(f"\n✅ Valid JSON detected!")
                print(f"JSON keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'Not a dict'}")
            except json.JSONDecodeError:
                print(f"\n❌ Not valid JSON")
                
    except Exception as e:
        print(f"❌ Error during extraction: {e}")

if __name__ == "__main__":
    test_extraction()












