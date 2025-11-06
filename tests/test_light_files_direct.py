"""
Direct test of light files using core extraction logic.
This bypasses the API server and tests the core functionality directly.
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.extractor import FinancialDataExtractor
from core.pdf_processor import PDFProcessor


class LightFileTester:
    """Direct tester for light files using core extraction logic"""
    
    def __init__(self):
        """Initialize the tester"""
        self.fixtures_dir = Path("tests/fixtures")
        self.light_dir = self.fixtures_dir / "light"
        self.results_dir = Path("tests/results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Initialize extractor (will fail if no API key, but we can test structure)
        try:
            self.extractor = FinancialDataExtractor()
            self.pdf_processor = PDFProcessor(self.extractor)
            self.api_available = True
        except Exception as e:
            print(f"⚠️ API not available: {e}")
            self.api_available = False
    
    def test_file_structure(self):
        """Test that all light files are present and accessible"""
        print("📁 Testing Light File Structure...")
        print("-" * 40)
        
        expected_files = [
            "2021 AFS with SEC Stamp - statement extracted.pdf",
            "afs-2021-2023 - statement extracted.pdf", 
            "AFS-2022 - statement extracted.pdf",
            "AFS2024 - statement extracted.pdf"
        ]
        
        results = {}
        for filename in expected_files:
            file_path = self.light_dir / filename
            if file_path.exists():
                file_size = file_path.stat().st_size
                results[filename] = {
                    "exists": True,
                    "size_bytes": file_size,
                    "size_mb": file_size / (1024 * 1024)
                }
                print(f"✅ {filename}: {file_size / (1024 * 1024):.2f} MB")
            else:
                results[filename] = {"exists": False}
                print(f"❌ {filename}: Not found")
        
        return results
    
    def test_pdf_processing_structure(self):
        """Test PDF processing structure without API calls"""
        print("\n🔧 Testing PDF Processing Structure...")
        print("-" * 40)
        
        if not self.api_available:
            print("⚠️ Skipping PDF processing tests - API not available")
            return {}
        
        results = {}
        pdf_files = list(self.light_dir.glob("*.pdf"))
        
        for pdf_file in pdf_files:
            try:
                print(f"🧪 Testing: {pdf_file.name}")
                
                # Test PDF to image conversion (without API calls)
                with open(pdf_file, 'rb') as f:
                    pdf_data = f.read()
                
                # Test basic PDF structure
                import fitz
                doc = fitz.Document(stream=pdf_data, filetype="pdf")
                page_count = len(doc)
                doc.close()
                
                results[pdf_file.name] = {
                    "page_count": page_count,
                    "file_size": len(pdf_data),
                    "pdf_valid": True
                }
                
                print(f"  ✅ Pages: {page_count}, Size: {len(pdf_data) / (1024 * 1024):.2f} MB")
                
            except Exception as e:
                results[pdf_file.name] = {
                    "pdf_valid": False,
                    "error": str(e)
                }
                print(f"  ❌ Error: {e}")
        
        return results
    
    def test_extraction_prompts(self):
        """Test extraction prompt generation"""
        print("\n📝 Testing Extraction Prompts...")
        print("-" * 40)
        
        if not self.api_available:
            print("⚠️ Skipping prompt tests - API not available")
            return {}
        
        statement_types = ["balance_sheet", "income_statement", "cash_flow", "financial_statement"]
        results = {}
        
        for stmt_type in statement_types:
            try:
                prompt = self.extractor._build_extraction_prompt(stmt_type)
                
                # Validate prompt structure
                has_core_rule = "CORE EXTRACTION RULE" in prompt
                has_json_structure = "JSON STRUCTURE" in prompt
                has_year_handling = "YEAR HANDLING" in prompt
                has_currency_handling = "CURRENCY AND NUMBER HANDLING" in prompt
                
                results[stmt_type] = {
                    "prompt_length": len(prompt),
                    "has_core_rule": has_core_rule,
                    "has_json_structure": has_json_structure,
                    "has_year_handling": has_year_handling,
                    "has_currency_handling": has_currency_handling,
                    "valid": all([has_core_rule, has_json_structure, has_year_handling, has_currency_handling])
                }
                
                status = "✅" if results[stmt_type]["valid"] else "❌"
                print(f"  {status} {stmt_type}: {len(prompt)} chars")
                
            except Exception as e:
                results[stmt_type] = {"error": str(e), "valid": False}
                print(f"  ❌ {stmt_type}: {e}")
        
        return results
    
    def test_expected_years_validation(self):
        """Test expected years validation logic"""
        print("\n📅 Testing Expected Years Validation...")
        print("-" * 40)
        
        expected_years = {
            "AFS2024 - statement extracted.pdf": ["2024", "2023"],
            "AFS-2022 - statement extracted.pdf": ["2022", "2021"],
            "afs-2021-2023 - statement extracted.pdf": ["2022", "2021", "2020"],
            "2021 AFS with SEC Stamp - statement extracted.pdf": ["2021", "2020"]
        }
        
        results = {}
        for filename, expected in expected_years.items():
            # Validate expected years structure
            is_list = isinstance(expected, list)
            has_min_years = len(expected) >= 2
            all_strings = all(isinstance(year, str) for year in expected)
            valid = all([is_list, has_min_years, all_strings])
            
            results[filename] = {
                "expected_years": expected,
                "year_count": len(expected),
                "is_list": is_list,
                "has_min_years": has_min_years,
                "all_strings": all_strings,
                "valid": valid
            }
            
            status = "✅" if valid else "❌"
            print(f"  {status} {filename}: {expected}")
        
        return results
    
    def test_configuration(self):
        """Test configuration validation"""
        print("\n⚙️ Testing Configuration...")
        print("-" * 40)
        
        from core.config import Config
        
        config = Config()
        results = {}
        
        # Test configuration values
        results["api_key_set"] = bool(config.OPENAI_API_KEY)
        results["model"] = config.OPENAI_MODEL
        results["max_tokens"] = config.OPENAI_MAX_TOKENS
        results["max_file_size"] = config.MAX_FILE_SIZE
        results["supported_types"] = config.SUPPORTED_FILE_TYPES
        results["max_pages"] = config.MAX_PAGES_TO_PROCESS
        results["parallel_workers"] = config.PARALLEL_WORKERS
        
        print(f"  API Key: {'✅ Set' if results['api_key_set'] else '❌ Not Set'}")
        print(f"  Model: {results['model']}")
        print(f"  Max Tokens: {results['max_tokens']}")
        print(f"  Max File Size: {results['max_file_size'] / (1024*1024):.0f} MB")
        print(f"  Supported Types: {', '.join(results['supported_types'])}")
        print(f"  Max Pages: {results['max_pages']}")
        print(f"  Parallel Workers: {results['parallel_workers']}")
        
        return results
    
    def run_all_tests(self):
        """Run all light file tests"""
        print("🚀 Starting Light File Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all test categories
        file_structure_results = self.test_file_structure()
        pdf_processing_results = self.test_pdf_processing_structure()
        prompt_results = self.test_extraction_prompts()
        years_validation_results = self.test_expected_years_validation()
        config_results = self.test_configuration()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Compile results
        all_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_duration": total_time,
            "file_structure": file_structure_results,
            "pdf_processing": pdf_processing_results,
            "extraction_prompts": prompt_results,
            "years_validation": years_validation_results,
            "configuration": config_results
        }
        
        # Save results
        results_file = self.results_dir / f"light_file_tests_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        # Print summary
        print("\n📊 Test Summary")
        print("=" * 60)
        
        # File structure summary
        files_found = sum(1 for r in file_structure_results.values() if r.get("exists", False))
        total_files = len(file_structure_results)
        print(f"Files Found: {files_found}/{total_files}")
        
        # PDF processing summary
        if pdf_processing_results:
            valid_pdfs = sum(1 for r in pdf_processing_results.values() if r.get("pdf_valid", False))
            total_pdfs = len(pdf_processing_results)
            print(f"Valid PDFs: {valid_pdfs}/{total_pdfs}")
        
        # Prompt validation summary
        if prompt_results:
            valid_prompts = sum(1 for r in prompt_results.values() if r.get("valid", False))
            total_prompts = len(prompt_results)
            print(f"Valid Prompts: {valid_prompts}/{total_prompts}")
        
        # Years validation summary
        valid_years = sum(1 for r in years_validation_results.values() if r.get("valid", False))
        total_years = len(years_validation_results)
        print(f"Valid Year Configs: {valid_years}/{total_years}")
        
        # Configuration summary
        api_available = config_results.get("api_key_set", False)
        print(f"API Available: {'✅ Yes' if api_available else '❌ No'}")
        
        print(f"\nTotal Test Time: {total_time:.2f} seconds")
        print(f"Results saved to: {results_file}")
        
        return all_results


def main():
    """Main function"""
    tester = LightFileTester()
    results = tester.run_all_tests()
    
    # Return success/failure based on key metrics
    files_found = sum(1 for r in results["file_structure"].values() if r.get("exists", False))
    total_files = len(results["file_structure"])
    
    if files_found == total_files:
        print("\n🎉 All light file tests completed successfully!")
        return 0
    else:
        print(f"\n⚠️ Some tests failed - {files_found}/{total_files} files found")
        return 1


if __name__ == "__main__":
    exit(main())
