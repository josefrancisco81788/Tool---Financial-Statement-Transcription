#!/usr/bin/env python3
"""
Direct vision model test with timeout protection
"""

import os
import sys
import time
import json
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_with_timeout(func, timeout_seconds=600):
    """Run a function with timeout protection using threading"""
    result = [None]
    exception = [None]
    
    def target():
        try:
            result[0] = func()
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)
    
    if thread.is_alive():
        print(f"⏰ Operation timed out after {timeout_seconds} seconds")
        return None
    
    if exception[0]:
        raise exception[0]
    
    return result[0]

def test_direct_vision():
    """Test vision models directly with PDF converted to image"""
    print("🚀 Direct Vision Model Test")
    print("=" * 50)
    
    # Convert PDF to image first
    print("🖼️  Converting PDF to image...")
    
    try:
        import fitz
        from PIL import Image
        import io
        
        pdf_path = 'tests/fixtures/light/AFS2024 - statement extracted.pdf'
        doc = fitz.open(pdf_path)
        
        # Get first page and convert to image
        page = doc[0]
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        doc.close()
        
        print(f"   ✅ Image created: {image.size[0]}x{image.size[1]} pixels")
        
    except Exception as e:
        print(f"   ❌ Failed to convert PDF to image: {e}")
        return False
    
    def test_openai_vision():
        """Test OpenAI vision directly"""
        print("\n🔍 Testing OpenAI Vision...")
        
        # Set provider to OpenAI
        os.environ['AI_PROVIDER'] = 'openai'
        
        try:
            from core.config import Config
            from core.extractor import FinancialDataExtractor
            
            config = Config()
            print(f"   📋 Provider: {config.AI_PROVIDER}")
            
            extractor = FinancialDataExtractor()
            print(f"   🤖 Extractor provider: {extractor.provider}")
            
            print("   🔄 Making OpenAI API call...")
            start_time = time.time()
            
            result = extractor.extract_from_image(image, "financial statement")
            
            processing_time = time.time() - start_time
            
            print(f"   ✅ OpenAI completed in {processing_time:.2f} seconds")
            print(f"   📊 Provider used: {result.get('ai_provider', 'Unknown')}")
            print(f"   📝 Statement type: {result.get('statement_type', 'Unknown')}")
            print(f"   🏢 Company: {result.get('company_name', 'Unknown')}")
            print(f"   💰 Currency: {result.get('currency', 'Unknown')}")
            
            # Count line items
            line_items = result.get('line_items', {})
            total_items = 0
            for category, items in line_items.items():
                if isinstance(items, dict):
                    total_items += len(items)
            
            print(f"   📈 Line items extracted: {total_items}")
            
            return {
                'provider': 'openai',
                'success': True,
                'processing_time': processing_time,
                'line_items_count': total_items,
                'ai_provider': result.get('ai_provider'),
                'statement_type': result.get('statement_type'),
                'company_name': result.get('company_name'),
                'currency': result.get('currency'),
                'years_detected': result.get('years_detected', [])
            }
                
        except Exception as e:
            print(f"   ❌ OpenAI error: {str(e)}")
            return {
                'provider': 'openai',
                'success': False,
                'error': str(e)
            }
    
    def test_anthropic_vision():
        """Test Anthropic vision directly"""
        print("\n🔍 Testing Anthropic Vision...")
        
        # Set provider to Anthropic
        os.environ['AI_PROVIDER'] = 'anthropic'
        
        try:
            from core.config import Config
            from core.extractor import FinancialDataExtractor
            
            config = Config()
            print(f"   📋 Provider: {config.AI_PROVIDER}")
            
            extractor = FinancialDataExtractor()
            print(f"   🤖 Extractor provider: {extractor.provider}")
            
            print("   🔄 Making Anthropic API call...")
            start_time = time.time()
            
            result = extractor.extract_from_image(image, "financial statement")
            
            processing_time = time.time() - start_time
            
            print(f"   ✅ Anthropic completed in {processing_time:.2f} seconds")
            print(f"   📊 Provider used: {result.get('ai_provider', 'Unknown')}")
            print(f"   📝 Statement type: {result.get('statement_type', 'Unknown')}")
            print(f"   🏢 Company: {result.get('company_name', 'Unknown')}")
            print(f"   💰 Currency: {result.get('currency', 'Unknown')}")
            
            # Count line items
            line_items = result.get('line_items', {})
            total_items = 0
            for category, items in line_items.items():
                if isinstance(items, dict):
                    total_items += len(items)
            
            print(f"   📈 Line items extracted: {total_items}")
            
            return {
                'provider': 'anthropic',
                'success': True,
                'processing_time': processing_time,
                'line_items_count': total_items,
                'ai_provider': result.get('ai_provider'),
                'statement_type': result.get('statement_type'),
                'company_name': result.get('company_name'),
                'currency': result.get('currency'),
                'years_detected': result.get('years_detected', [])
            }
                
        except Exception as e:
            print(f"   ❌ Anthropic error: {str(e)}")
            return {
                'provider': 'anthropic',
                'success': False,
                'error': str(e)
            }
    
    # Test both providers with timeout
    results = []
    
    print("\n⏱️  Running OpenAI vision test with 10-minute timeout...")
    openai_result = run_with_timeout(test_openai_vision, 600)
    if openai_result:
        results.append(openai_result)
    
    print("\n⏱️  Running Anthropic vision test with 10-minute timeout...")
    anthropic_result = run_with_timeout(test_anthropic_vision, 600)
    if anthropic_result:
        results.append(anthropic_result)
    
    # Display results
    print("\n" + "=" * 50)
    print("📊 VISION MODEL TEST RESULTS")
    print("=" * 50)
    
    for result in results:
        provider = result['provider'].upper()
        print(f"\n{provider} Results:")
        if result['success']:
            print(f"   ✅ Success: {result['processing_time']:.2f}s")
            print(f"   🤖 AI Provider: {result['ai_provider']}")
            print(f"   📈 Line Items: {result['line_items_count']}")
            print(f"   📝 Statement Type: {result['statement_type']}")
            print(f"   🏢 Company: {result['company_name']}")
            print(f"   💰 Currency: {result['currency']}")
            print(f"   📅 Years: {result['years_detected']}")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Save results
    timestamp = int(time.time())
    results_file = f"vision_model_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    # Summary
    successful_results = [r for r in results if r['success']]
    print(f"\n📊 Summary: {len(successful_results)}/{len(results)} providers successful")
    
    if len(successful_results) == 2:
        print("🎉 Both vision models working! Claude integration successful!")
        
        # Performance comparison
        openai_time = next((r['processing_time'] for r in results if r['provider'] == 'openai' and r['success']), None)
        anthropic_time = next((r['processing_time'] for r in results if r['provider'] == 'anthropic' and r['success']), None)
        
        if openai_time and anthropic_time:
            print(f"\n⚡ Performance Comparison:")
            print(f"   OpenAI: {openai_time:.2f}s")
            print(f"   Claude: {anthropic_time:.2f}s")
            
            if anthropic_time < openai_time:
                print(f"   🏆 Claude is {((openai_time - anthropic_time) / openai_time * 100):.1f}% faster!")
            elif openai_time < anthropic_time:
                print(f"   🏆 OpenAI is {((anthropic_time - openai_time) / anthropic_time * 100):.1f}% faster!")
            else:
                print("   🤝 Both providers have similar performance")
        
        return True
    else:
        print("⚠️  Some vision models failed. Check the results above.")
        return False

def main():
    """Run the direct vision test"""
    try:
        success = test_direct_vision()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())












