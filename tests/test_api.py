"""
API Testing Script for Financial Statement Transcription

This script tests the API with the test fixtures and validates the results.
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, List


class APITester:
    """API testing class for financial statement transcription"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """Initialize API tester"""
        self.base_url = base_url
        self.fixtures_dir = Path("tests/fixtures")
        self.results_dir = Path("tests/results")
        self.results_dir.mkdir(exist_ok=True)
    
    def test_health(self) -> bool:
        """Test API health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ API health check passed")
                return True
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API health check error: {str(e)}")
            return False
    
    def test_single_document(self, file_path: Path, statement_type: str = "balance_sheet") -> Dict[str, Any]:
        """Test API with a single document"""
        try:
            print(f"🧪 Testing: {file_path.name}")
            
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/pdf')}
                data = {'statement_type': statement_type}
                
                start_time = time.time()
                response = requests.post(f"{self.base_url}/extract", files=files, data=data)
                processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success: {processing_time:.2f}s")
                
                # Save result
                result_file = self.results_dir / f"{file_path.stem}_result.json"
                with open(result_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                return result
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {"error": str(e)}
    
    def test_light_files(self) -> Dict[str, Any]:
        """Test API with light files (extracted statement pages)"""
        light_dir = self.fixtures_dir / "light"
        if not light_dir.exists():
            print("❌ Light files directory not found")
            return {}
        
        results = {}
        pdf_files = list(light_dir.glob("*.pdf"))
        
        if not pdf_files:
            print("❌ No PDF files found in light directory")
            return {}
        
        print(f"🧪 Testing {len(pdf_files)} light files...")
        
        for pdf_file in pdf_files:
            result = self.test_single_document(pdf_file)
            results[pdf_file.name] = result
        
        return results
    
    def test_origin_files(self) -> Dict[str, Any]:
        """Test API with origin files (full documents)"""
        origin_dir = self.fixtures_dir / "origin"
        if not origin_dir.exists():
            print("❌ Origin files directory not found")
            return {}
        
        results = {}
        pdf_files = list(origin_dir.glob("*.pdf"))
        
        if not pdf_files:
            print("❌ No PDF files found in origin directory")
            return {}
        
        print(f"🧪 Testing {len(pdf_files)} origin files...")
        
        for pdf_file in pdf_files:
            result = self.test_single_document(pdf_file)
            results[pdf_file.name] = result
        
        return results
    
    def validate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate API results against expected criteria"""
        validation = {
            "total_tests": len(results),
            "successful_tests": 0,
            "failed_tests": 0,
            "year_coverage": {},
            "row_counts": {},
            "issues": []
        }
        
        for filename, result in results.items():
            if "error" in result:
                validation["failed_tests"] += 1
                validation["issues"].append(f"{filename}: {result['error']}")
                continue
            
            validation["successful_tests"] += 1
            
            # Check year coverage
            if "data" in result and "years_detected" in result["data"]:
                years = result["data"]["years_detected"]
                validation["year_coverage"][filename] = years
                
                # Expected years based on filename
                expected_years = self._get_expected_years(filename)
                if expected_years:
                    missing_years = set(expected_years) - set(years)
                    if missing_years:
                        validation["issues"].append(f"{filename}: Missing years {missing_years}")
            
            # Check row counts
            if "data" in result and "line_items" in result["data"]:
                line_items = result["data"]["line_items"]
                total_rows = sum(len(category) for category in line_items.values() if isinstance(category, dict))
                validation["row_counts"][filename] = total_rows
        
        return validation
    
    def _get_expected_years(self, filename: str) -> List[str]:
        """Get expected years based on filename"""
        if "2021" in filename and "SEC" in filename:
            return ["2021", "2020"]
        elif "2021" in filename and "2023" in filename:
            return ["2022", "2021", "2020"]
        elif "2022" in filename:
            return ["2022", "2021"]
        elif "2024" in filename:
            return ["2024", "2023"]
        return []
    
    def generate_report(self, results: Dict[str, Any], validation: Dict[str, Any]):
        """Generate a test report"""
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "api_url": self.base_url,
            "test_summary": {
                "total_tests": validation["total_tests"],
                "successful_tests": validation["successful_tests"],
                "failed_tests": validation["failed_tests"],
                "success_rate": validation["successful_tests"] / max(validation["total_tests"], 1) * 100
            },
            "year_coverage": validation["year_coverage"],
            "row_counts": validation["row_counts"],
            "issues": validation["issues"],
            "detailed_results": results
        }
        
        # Save report
        report_file = self.results_dir / f"test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Test report saved to: {report_file}")
        return report
    
    def run_full_test(self):
        """Run full test suite"""
        print("🚀 Starting Financial Statement Transcription API Tests")
        print("=" * 60)
        
        # Test health
        if not self.test_health():
            print("❌ API is not healthy. Exiting.")
            return
        
        print("\n🧪 Testing Light Files (Primary Testing)")
        print("-" * 40)
        light_results = self.test_light_files()
        
        print("\n🧪 Testing Origin Files (Comprehensive Testing)")
        print("-" * 40)
        origin_results = self.test_origin_files()
        
        # Combine results
        all_results = {**light_results, **origin_results}
        
        # Validate results
        print("\n📊 Validating Results")
        print("-" * 40)
        validation = self.validate_results(all_results)
        
        # Generate report
        print("\n📋 Generating Test Report")
        print("-" * 40)
        report = self.generate_report(all_results, validation)
        
        # Print summary
        print("\n🎯 Test Summary")
        print("=" * 60)
        print(f"Total Tests: {validation['total_tests']}")
        print(f"Successful: {validation['successful_tests']}")
        print(f"Failed: {validation['failed_tests']}")
        print(f"Success Rate: {validation['successful_tests'] / max(validation['total_tests'], 1) * 100:.1f}%")
        
        if validation['issues']:
            print(f"\n⚠️ Issues Found:")
            for issue in validation['issues']:
                print(f"  - {issue}")
        
        print(f"\n📁 Results saved to: {self.results_dir}")


def main():
    """Main function to run tests"""
    tester = APITester()
    tester.run_full_test()


if __name__ == "__main__":
    main()
