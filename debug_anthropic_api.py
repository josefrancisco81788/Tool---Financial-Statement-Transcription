"""
Debug test for Anthropic API to identify the exact issue
"""

import anthropic
import os
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    os.environ[key] = value

def test_anthropic_api():
    """Test minimal Anthropic API call to debug HTTP 400 errors"""
    
    # Load environment variables
    load_env_file()
    
    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found")
        return
    
    print(f"🔑 API Key found: {api_key[:10]}...")
    
    # Initialize client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Test 1: Minimal text-only call
    print("\n🧪 Test 1: Minimal text-only call")
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "Hello, can you respond with 'API working'?"
                }
            ]
        )
        print("✅ SUCCESS:", response.content[0].text)
    except anthropic.BadRequestError as e:
        print("❌ Bad Request Details:")
        print(f"   Status: {e.status_code}")
        print(f"   Error: {e.response.text}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 2: Check if our current model name works
    print("\n🧪 Test 2: Current model name test")
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",  # Our current model
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "Hello, can you respond with 'Model working'?"
                }
            ]
        )
        print("✅ SUCCESS:", response.content[0].text)
    except anthropic.BadRequestError as e:
        print("❌ Bad Request Details:")
        print(f"   Status: {e.status_code}")
        print(f"   Error: {e.response.text}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 3: Test with image (base64)
    print("\n🧪 Test 3: Image with base64 (minimal)")
    try:
        # Create a minimal base64 image (1x1 pixel PNG)
        minimal_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What do you see in this image?"},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": minimal_base64
                            }
                        }
                    ]
                }
            ]
        )
        print("✅ SUCCESS:", response.content[0].text)
    except anthropic.BadRequestError as e:
        print("❌ Bad Request Details:")
        print(f"   Status: {e.status_code}")
        print(f"   Error: {e.response.text}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_anthropic_api()
