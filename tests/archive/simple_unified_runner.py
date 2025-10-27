#!/usr/bin/env python3
"""
Simplified Unified Test Runner - Robust version without timeout issues
"""

import os
import sys
import time
import signal
import argparse
from pathlib import Path
from typing import List, Dict, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TimeoutError(Exception):
    """Timeout exception"""
    pass


def timeout_handler(signum, frame):
    """Handle timeout signal"""
    raise TimeoutError("Operation timed out")


class SimpleUnifiedRunner:
    """Simplified unified test runner with robust timeout handling"""
    
    def __init__(self):
        self.results_dir = Path("tests/results")
        self.results_dir.mkdir(exist_ok=True)
    
    def validate_provider(self, provider: str) -> bool:
        """Validate a single provider with timeout protection"""
        print(f"🔍 Validating {provider} provider...")
        
        try:
            # Set timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)  # 30 second timeout for validation
            
            # Set environment variable
            os.environ['AI_PROVIDER'] = provider
            
            # Import and initialize
            from core.config import Config
            from core.extractor import FinancialDataExtractor
            
            config = Config()
            extractor = FinancialDataExtractor()
            
            # Check configuration
            if provider == "openai" and not config.OPENAI_API_KEY:
                print(f"   ❌ OPENAI_API_KEY not found")
                return False
            elif provider == "anthropic" and not config.ANTHROPIC_API_KEY:
                print(f"   ❌ ANTHROPIC_API_KEY not found")
                return False
            
            # Check provider is set correctly
            if extractor.provider != provider:
                print(f"   ❌ Provider not set correctly: {extractor.provider}")
                return False
            
            print(f"   ✅ {provider} provider validated: {getattr(config, f'{provider.upper()}_MODEL', 'N/A')}")
            return True
            
        except TimeoutError:
            print(f"   ❌ {provider} validation timed out")
            return False
        except Exception as e:
            print(f"   ❌ {provider} validation failed: {e}")
            return False
        finally:
            signal.alarm(0)  # Disable alarm
    
    def test_single_document(self, provider: str, document_path: str, timeout: int = 180) -> Dict:
        """Test a single document with robust timeout handling"""
        print(f"🧪 Testing {provider} with {Path(document_path).name}")
        
        start_time = time.time()
        result = {
            'provider': provider,
            'document': document_path,
            'success': False,
            'error': None,
            'processing_time': 0,
            'extracted_data': None
        }
        
        try:
            # Set timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
            
            # Set environment variable
            os.environ['AI_PROVIDER'] = provider
            
            # Import and initialize
            from core.extractor import FinancialDataExtractor
            from core.pdf_processor import PDFProcessor
            
            extractor = FinancialDataExtractor()
            pdf_processor = PDFProcessor(extractor)
            
            # Check if document exists
            if not Path(document_path).exists():
                result['error'] = f"Document not found: {document_path}"
                return result
            
            # Process document
            with open(document_path, 'rb') as f:
                pdf_data = f.read()
            
            extracted_data = pdf_processor.process_pdf_with_vector_db(pdf_data)
            
            processing_time = time.time() - start_time
            
            if extracted_data:
                result['success'] = True
                result['extracted_data'] = extracted_data
                result['processing_time'] = processing_time
                print(f"   ✅ Success: {processing_time:.1f}s")
            else:
                result['error'] = "No data extracted"
                result['processing_time'] = processing_time
                print(f"   ❌ Failed: No data extracted")
            
            return result
            
        except TimeoutError:
            result['error'] = f"Processing timed out after {timeout} seconds"
            result['processing_time'] = time.time() - start_time
            print(f"   ❌ Timed out after {timeout}s")
            return result
        except Exception as e:
            result['error'] = f"Processing failed: {str(e)}"
            result['processing_time'] = time.time() - start_time
            print(f"   ❌ Error: {str(e)}")
            return result
        finally:
            signal.alarm(0)  # Disable alarm
    
    def compare_providers(self, providers: List[str], document_path: str, timeout: int = 180) -> Dict:
        """Compare multiple providers on same document"""
        print(f"🔄 Comparing providers: {', '.join(providers)}")
        print(f"📄 Document: {Path(document_path).name}")
        print("=" * 60)
        
        results = {}
        
        for provider in providers:
            print(f"\n📊 Testing {provider}...")
            result = self.test_single_document(provider, document_path, timeout)
            results[provider] = result
        
        # Print comparison
        print(f"\n📊 PROVIDER COMPARISON RESULTS")
        print("=" * 60)
        
        successful_results = {k: v for k, v in results.items() if v['success']}
        
        if successful_results:
            # Find winner by processing time
            winner = min(successful_results.keys(), 
                        key=lambda k: successful_results[k]['processing_time'])
            
            print(f"🏆 Winner: {winner}")
            print(f"⏱️  Processing Time: {successful_results[winner]['processing_time']:.1f}s")
            
            # Show all results
            for provider, result in results.items():
                status = "✅" if result['success'] else "❌"
                time_str = f"{result['processing_time']:.1f}s" if result['processing_time'] > 0 else "N/A"
                print(f"   {status} {provider}: {time_str}")
                if not result['success'] and result['error']:
                    print(f"      Error: {result['error']}")
        else:
            print("❌ All providers failed")
            for provider, result in results.items():
                print(f"   ❌ {provider}: {result['error']}")
        
        return results
    
    def run_quick_test(self, provider: str = "anthropic", document_path: str = None) -> Dict:
        """Run a quick test with default settings"""
        if not document_path:
            # Use first light document
            light_dir = Path("tests/fixtures/light")
            if light_dir.exists():
                pdf_files = list(light_dir.glob("*.pdf"))
                if pdf_files:
                    document_path = str(pdf_files[0])
                else:
                    print("❌ No PDF files found in tests/fixtures/light")
                    return {}
            else:
                print("❌ Light fixtures directory not found")
                return {}
        
        print(f"🚀 Running quick test")
        print(f"📄 Document: {Path(document_path).name}")
        print("=" * 60)
        
        # Validate provider first
        if not self.validate_provider(provider):
            print(f"❌ Provider validation failed")
            return {}
        
        # Test document
        result = self.test_single_document(provider, document_path, timeout=180)
        
        if result['success']:
            print(f"\n🎉 Quick test completed successfully!")
            print(f"⏱️  Processing time: {result['processing_time']:.1f}s")
            
            # Show basic extracted data info
            if result['extracted_data']:
                data = result['extracted_data']
                print(f"🏢 Company: {data.get('company_name', 'N/A')}")
                print(f"📝 Statement: {data.get('statement_type', 'N/A')}")
                print(f"💰 Currency: {data.get('currency', 'N/A')}")
                print(f"📅 Years: {', '.join(data.get('years_detected', []))}")
                
                line_items = data.get('line_items', {})
                total_items = sum(len(items) if isinstance(items, dict) else 0 
                                for items in line_items.values())
                print(f"📈 Line items: {total_items}")
        else:
            print(f"\n❌ Quick test failed: {result['error']}")
        
        return result


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Simple Unified Test Runner")
    
    parser.add_argument("--provider", default="anthropic", 
                       help="Provider to test (openai, anthropic)")
    parser.add_argument("--file", help="Document file to test")
    parser.add_argument("--compare", action="store_true", 
                       help="Compare multiple providers")
    parser.add_argument("--providers", default="openai,anthropic",
                       help="Providers to compare (comma-separated)")
    parser.add_argument("--timeout", type=int, default=180,
                       help="Timeout in seconds")
    
    args = parser.parse_args()
    
    runner = SimpleUnifiedRunner()
    
    if args.compare:
        providers = [p.strip() for p in args.providers.split(',')]
        if not args.file:
            print("❌ --file required for provider comparison")
            sys.exit(1)
        runner.compare_providers(providers, args.file, args.timeout)
    else:
        runner.run_quick_test(args.provider, args.file)


if __name__ == "__main__":
    main()












