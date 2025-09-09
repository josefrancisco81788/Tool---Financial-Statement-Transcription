#!/usr/bin/env python3
"""
Debug script to identify what's causing the API to hang after startup.
Tests each component individually to isolate the problem.
"""

import sys
import time
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_config_loading():
    """Test configuration loading"""
    print("🔍 Testing configuration loading...")
    try:
        from core.config import Config
        config = Config()
        config.validate()
        print("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        traceback.print_exc()
        return False

def test_openai_client():
    """Test OpenAI client initialization"""
    print("🔍 Testing OpenAI client initialization...")
    try:
        from openai import OpenAI
        from core.config import Config
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        print("✅ OpenAI client initialized successfully")
        return True
    except Exception as e:
        print(f"❌ OpenAI client failed: {e}")
        traceback.print_exc()
        return False

def test_extractor_initialization():
    """Test FinancialDataExtractor initialization"""
    print("🔍 Testing FinancialDataExtractor initialization...")
    try:
        from core.extractor import FinancialDataExtractor
        extractor = FinancialDataExtractor()
        print("✅ FinancialDataExtractor initialized successfully")
        return True
    except Exception as e:
        print(f"❌ FinancialDataExtractor failed: {e}")
        traceback.print_exc()
        return False

def test_pdf_processor_initialization():
    """Test PDFProcessor initialization (this is likely the culprit)"""
    print("🔍 Testing PDFProcessor initialization...")
    try:
        from core.pdf_processor import PDFProcessor
        print("  - Importing PDFProcessor...")
        processor = PDFProcessor()
        print("✅ PDFProcessor initialized successfully")
        return True
    except Exception as e:
        print(f"❌ PDFProcessor failed: {e}")
        traceback.print_exc()
        return False

def test_fastapi_app_creation():
    """Test FastAPI app creation without starting server"""
    print("🔍 Testing FastAPI app creation...")
    try:
        from fastapi import FastAPI
        from core.config import Config
        
        app = FastAPI(
            title=Config.API_TITLE,
            version=Config.API_VERSION,
            description=Config.API_DESCRIPTION
        )
        print("✅ FastAPI app created successfully")
        return True
    except Exception as e:
        print(f"❌ FastAPI app creation failed: {e}")
        traceback.print_exc()
        return False

def test_full_import():
    """Test importing the full api_app module"""
    print("🔍 Testing full api_app import...")
    try:
        import api_app
        print("✅ api_app imported successfully")
        return True
    except Exception as e:
        print(f"❌ api_app import failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests to identify the hanging issue"""
    print("🚀 Starting API hanging investigation...")
    print("=" * 50)
    
    tests = [
        ("Configuration Loading", test_config_loading),
        ("OpenAI Client", test_openai_client),
        ("FinancialDataExtractor", test_extractor_initialization),
        ("PDFProcessor", test_pdf_processor_initialization),
        ("FastAPI App Creation", test_fastapi_app_creation),
        ("Full API App Import", test_full_import),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        start_time = time.time()
        
        try:
            # Set a timeout for each test
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"{test_name} timed out after 30 seconds")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)  # 30 second timeout
            
            result = test_func()
            signal.alarm(0)  # Cancel timeout
            
            elapsed = time.time() - start_time
            results[test_name] = {
                'success': result,
                'time': elapsed,
                'error': None
            }
            
            if result:
                print(f"✅ {test_name} completed in {elapsed:.2f}s")
            else:
                print(f"❌ {test_name} failed in {elapsed:.2f}s")
                
        except TimeoutError as e:
            signal.alarm(0)
            elapsed = time.time() - start_time
            results[test_name] = {
                'success': False,
                'time': elapsed,
                'error': str(e)
            }
            print(f"⏰ {test_name} TIMED OUT after {elapsed:.2f}s - THIS IS LIKELY THE CULPRIT!")
            
        except Exception as e:
            signal.alarm(0)
            elapsed = time.time() - start_time
            results[test_name] = {
                'success': False,
                'time': elapsed,
                'error': str(e)
            }
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print("📊 INVESTIGATION RESULTS:")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        time_str = f"{result['time']:.2f}s"
        if result['error']:
            print(f"{status} {test_name} ({time_str}) - {result['error']}")
        else:
            print(f"{status} {test_name} ({time_str})")
    
    # Identify the likely culprit
    failed_tests = [name for name, result in results.items() if not result['success']]
    timeout_tests = [name for name, result in results.items() if 'timeout' in str(result.get('error', '')).lower()]
    
    if timeout_tests:
        print(f"\n🎯 LIKELY CULPRIT: {timeout_tests[0]} is timing out")
        print("   This component is likely causing the API to hang after startup")
    elif failed_tests:
        print(f"\n🎯 LIKELY CULPRIT: {failed_tests[0]} is failing")
        print("   This component is likely causing the API to hang after startup")
    else:
        print("\n✅ All components loaded successfully")
        print("   The hanging issue might be in the server startup process itself")

if __name__ == "__main__":
    main()
