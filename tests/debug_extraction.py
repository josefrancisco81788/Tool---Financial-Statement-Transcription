"""
Debug script for core extraction issues

This script helps diagnose why the core extraction logic is failing
by testing each component individually.
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.config import Config
from core.extractor import FinancialDataExtractor
from core.pdf_processor import PDFProcessor


class ExtractionDebugger:
    """Debug the core extraction logic step by step"""
    
    def __init__(self):
        """Initialize the debugger"""
        self.fixtures_dir = Path("tests/fixtures")
        self.light_dir = self.fixtures_dir / "light"
        self.results_dir = Path("tests/results")
        self.results_dir.mkdir(exist_ok=True)
        
    def debug_configuration(self) -> Dict[str, Any]:
        """Debug configuration setup"""
        print("🔧 Debugging Configuration...")
        print("-" * 40)
        
        config = Config()
        results = {}
        
        # Check API key
        api_key = config.OPENAI_API_KEY
        results["api_key_set"] = bool(api_key)
        results["api_key_length"] = len(api_key) if api_key else 0
        results["api_key_prefix"] = api_key[:10] + "..." if api_key and len(api_key) > 10 else api_key
        
        print(f"  API Key: {'✅ Set' if results['api_key_set'] else '❌ Not Set'}")
        if results['api_key_set']:
            print(f"  Length: {results['api_key_length']} characters")
            print(f"  Prefix: {results['api_key_prefix']}")
        
        # Check other config
        results["model"] = config.OPENAI_MODEL
        results["max_tokens"] = config.OPENAI_MAX_TOKENS
        results["max_file_size"] = config.MAX_FILE_SIZE
        
        print(f"  Model: {results['model']}")
        print(f"  Max Tokens: {results['max_tokens']}")
        print(f"  Max File Size: {results['max_file_size'] / (1024*1024):.0f} MB")
        
        return results
    
    def debug_extractor_initialization(self) -> Dict[str, Any]:
        """Debug extractor initialization"""
        print("\n🤖 Debugging Extractor Initialization...")
        print("-" * 40)
        
        results = {}
        
        try:
            extractor = FinancialDataExtractor()
            results["initialization_success"] = True
            results["extractor_type"] = type(extractor).__name__
            print("  ✅ Extractor initialized successfully")
            
            # Test OpenAI client
            if hasattr(extractor, 'client'):
                results["openai_client_available"] = True
                print("  ✅ OpenAI client available")
            else:
                results["openai_client_available"] = False
                print("  ❌ OpenAI client not available")
            
        except Exception as e:
            results["initialization_success"] = False
            results["error"] = str(e)
            print(f"  ❌ Extractor initialization failed: {e}")
        
        return results
    
    def debug_pdf_processor_initialization(self) -> Dict[str, Any]:
        """Debug PDF processor initialization"""
        print("\n📄 Debugging PDF Processor Initialization...")
        print("-" * 40)
        
        results = {}
        
        try:
            extractor = FinancialDataExtractor()
            processor = PDFProcessor(extractor)
            results["initialization_success"] = True
            results["processor_type"] = type(processor).__name__
            print("  ✅ PDF Processor initialized successfully")
            
        except Exception as e:
            results["initialization_success"] = False
            results["error"] = str(e)
            print(f"  ❌ PDF Processor initialization failed: {e}")
        
        return results
    
    def debug_file_processing(self, filename: str) -> Dict[str, Any]:
        """Debug file processing for a specific file"""
        print(f"\n📁 Debugging File Processing: {filename}")
        print("-" * 40)
        
        file_path = self.light_dir / filename
        results = {
            "filename": filename,
            "file_exists": file_path.exists(),
            "file_size": 0,
            "processing_steps": {}
        }
        
        if not file_path.exists():
            print(f"  ❌ File not found: {file_path}")
            return results
        
        # Get file info
        results["file_size"] = file_path.stat().st_size
        print(f"  📊 File size: {results['file_size'] / (1024*1024):.2f} MB")
        
        try:
            # Test PDF to image conversion
            print("  🔄 Testing PDF to image conversion...")
            with open(file_path, 'rb') as f:
                pdf_data = f.read()
            
            import fitz
            doc = fitz.Document(stream=pdf_data, filetype="pdf")
            page_count = len(doc)
            results["processing_steps"]["pdf_parsing"] = {
                "success": True,
                "page_count": page_count
            }
            print(f"    ✅ PDF parsed: {page_count} pages")
            doc.close()
            
            # Test image conversion
            print("  🖼️ Testing image conversion...")
            extractor = FinancialDataExtractor()
            processor = PDFProcessor(extractor)
            
            # Convert first page to image
            doc = fitz.Document(stream=pdf_data, filetype="pdf")
            page = doc[0]
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            doc.close()
            
            results["processing_steps"]["image_conversion"] = {
                "success": True,
                "image_size": len(img_data)
            }
            print(f"    ✅ Image converted: {len(img_data)} bytes")
            
            # Test base64 encoding
            print("  🔐 Testing base64 encoding...")
            import base64
            base64_image = base64.b64encode(img_data).decode('utf-8')
            results["processing_steps"]["base64_encoding"] = {
                "success": True,
                "encoded_size": len(base64_image)
            }
            print(f"    ✅ Base64 encoded: {len(base64_image)} characters")
            
            # Test prompt building
            print("  📝 Testing prompt building...")
            prompt = extractor._build_extraction_prompt("financial_statement")
            results["processing_steps"]["prompt_building"] = {
                "success": True,
                "prompt_length": len(prompt)
            }
            print(f"    ✅ Prompt built: {len(prompt)} characters")
            
        except Exception as e:
            results["processing_steps"]["error"] = str(e)
            print(f"  ❌ Processing failed: {e}")
        
        return results
    
    def debug_api_call(self, filename: str) -> Dict[str, Any]:
        """Debug actual API call (without full processing)"""
        print(f"\n🌐 Debugging API Call: {filename}")
        print("-" * 40)
        
        file_path = self.light_dir / filename
        results = {
            "filename": filename,
            "api_call_success": False,
            "response_data": None,
            "error": None
        }
        
        if not file_path.exists():
            print(f"  ❌ File not found: {file_path}")
            return results
        
        try:
            # Test with a small image first
            print("  🧪 Testing with small image...")
            extractor = FinancialDataExtractor()
            
            # Create a simple test image
            from PIL import Image
            import io
            
            # Create a small test image
            test_img = Image.new('RGB', (100, 100), color='white')
            img_buffer = io.BytesIO()
            test_img.save(img_buffer, format='PNG')
            img_data = img_buffer.getvalue()
            
            # Test extraction
            print("  🔄 Attempting extraction...")
            start_time = time.time()
            
            # This will test the actual API call
            result = extractor.extract_from_image(img_data, "financial_statement")
            
            processing_time = time.time() - start_time
            results["api_call_success"] = True
            results["processing_time"] = processing_time
            results["response_data"] = result
            
            print(f"    ✅ API call successful: {processing_time:.2f}s")
            if result:
                print(f"    📊 Result type: {type(result)}")
                if isinstance(result, dict):
                    print(f"    📊 Result keys: {list(result.keys())}")
            
        except Exception as e:
            results["error"] = str(e)
            print(f"  ❌ API call failed: {e}")
        
        return results
    
    def run_full_debug(self, filename: str = "AFS2024 - statement extracted.pdf") -> Dict[str, Any]:
        """Run full debugging suite"""
        print("🔍 Starting Full Extraction Debug")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all debug steps
        config_results = self.debug_configuration()
        extractor_results = self.debug_extractor_initialization()
        processor_results = self.debug_pdf_processor_initialization()
        file_results = self.debug_file_processing(filename)
        api_results = self.debug_api_call(filename)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Compile results
        all_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "debug_duration": total_time,
            "configuration": config_results,
            "extractor_initialization": extractor_results,
            "pdf_processor_initialization": processor_results,
            "file_processing": file_results,
            "api_call": api_results
        }
        
        # Save results
        results_file = self.results_dir / f"extraction_debug_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        # Print summary
        print("\n📊 Debug Summary")
        print("=" * 60)
        
        config_ok = config_results.get("api_key_set", False)
        extractor_ok = extractor_results.get("initialization_success", False)
        processor_ok = processor_results.get("initialization_success", False)
        file_ok = file_results.get("processing_steps", {}).get("pdf_parsing", {}).get("success", False)
        api_ok = api_results.get("api_call_success", False)
        
        print(f"Configuration: {'✅' if config_ok else '❌'}")
        print(f"Extractor Init: {'✅' if extractor_ok else '❌'}")
        print(f"Processor Init: {'✅' if processor_ok else '❌'}")
        print(f"File Processing: {'✅' if file_ok else '❌'}")
        print(f"API Call: {'✅' if api_ok else '❌'}")
        
        print(f"\nTotal Debug Time: {total_time:.2f} seconds")
        print(f"Results saved to: {results_file}")
        
        return all_results


def main():
    """Main function"""
    debugger = ExtractionDebugger()
    
    # Run full debug
    results = debugger.run_full_debug()
    
    # Return success/failure based on key metrics
    config_ok = results["configuration"].get("api_key_set", False)
    extractor_ok = results["extractor_initialization"].get("initialization_success", False)
    
    if config_ok and extractor_ok:
        print("\n🎉 Core components are working!")
        return 0
    else:
        print("\n⚠️ Core components have issues - check the debug results")
        return 1


if __name__ == "__main__":
    exit(main())
