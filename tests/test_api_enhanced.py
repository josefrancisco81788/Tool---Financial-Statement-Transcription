"""
Enhanced Financial Statement Transcription API Test Suite

Features:
- Individual file testing
- Timeout management
- Progress indicators
- Enhanced error reporting
- Command line interface
- Resumable testing
"""

import os
import sys
import time
import json
import argparse
import signal
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import requests
from tqdm import tqdm
import threading

# Add project root to path for core CSV exporter
sys.path.insert(0, str(Path(__file__).parent.parent))
from tests.core.csv_exporter import CSVExporter


class TimeoutError(Exception):
    """Custom timeout exception"""
    pass


class APITester:
    """Enhanced API tester with individual file testing and timeout management"""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 300):
        """Initialize the API tester"""
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.fixtures_dir = Path("tests/fixtures")
        self.results_dir = Path("tests/results")
        self.results_dir.mkdir(exist_ok=True)
        self.csv_exporter = CSVExporter()  # Initialize core CSV exporter
        
        # Test categories
        self.categories = {
            "light": self.fixtures_dir / "light",
            "origin": self.fixtures_dir / "origin",
            "templates": self.fixtures_dir / "templates"
        }
        
        # Test state management
        self.test_state_file = self.results_dir / "test_state.json"
        self.current_test_state = self._load_test_state()
        
        # Progress tracking
        self.progress_bar = None
        self.test_results = []
        
    def _load_test_state(self) -> Dict[str, Any]:
        """Load test state from file"""
        if self.test_state_file.exists():
            try:
                with open(self.test_state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Could not load test state: {e}")
        return {"completed_tests": [], "failed_tests": [], "last_run": None}
    
    def _save_test_state(self):
        """Save current test state to file"""
        try:
            with open(self.test_state_file, 'w') as f:
                json.dump(self.current_test_state, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save test state: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle timeout signals"""
        raise TimeoutError(f"Test timed out after {self.timeout} seconds")
    
    def _test_with_timeout(self, func, *args, **kwargs):
        """Run a function with timeout (cross-platform)"""
        if platform.system() == "Windows":
            # Use ThreadPoolExecutor for Windows (no SIGALRM support)
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    result = future.result(timeout=self.timeout)
                    return result
                except FutureTimeoutError:
                    raise TimeoutError(f"Test timed out after {self.timeout} seconds")
        else:
            # Use signal-based timeout for Unix-like systems
            old_handler = signal.signal(signal.SIGALRM, self._signal_handler)
            signal.alarm(self.timeout)
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # Cancel the alarm
                return result
            except TimeoutError:
                signal.alarm(0)  # Cancel the alarm
                raise
            finally:
                signal.signal(signal.SIGALRM, old_handler)
    
    def check_api_health(self) -> bool:
        """Check if API is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ API Health: {health_data.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ API Health Check Failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API Health Check Error: {e}")
            return False
    
    def get_available_files(self, category: Optional[str] = None) -> List[Path]:
        """Get list of available test files"""
        files = []
        
        if category and category in self.categories:
            # Specific category
            category_path = self.categories[category]
            if category_path.exists():
                files.extend(category_path.glob("*.pdf"))
        else:
            # All categories
            for cat_path in self.categories.values():
                if cat_path.exists():
                    files.extend(cat_path.glob("*.pdf"))
        
        return sorted(files)
    
    def test_single_file(self, file_path: Path, verbose: bool = False) -> Dict[str, Any]:
        """Test a single file with detailed error reporting"""
        start_time = time.time()
        result = {
            "file": str(file_path),
            "filename": file_path.name,
            "category": self._get_file_category(file_path),
            "success": False,
            "error": None,
            "processing_time": 0,
            "response_data": None,
            "file_size": file_path.stat().st_size if file_path.exists() else 0
        }
        
        try:
            if verbose:
                print(f"\n🧪 Testing: {file_path.name}")
                print(f"   📁 Category: {result['category']}")
                print(f"   📊 Size: {result['file_size'] / (1024*1024):.2f} MB")
            
            # Test with timeout
            def _test_file():
                with open(file_path, 'rb') as f:
                    files = {'file': (file_path.name, f, 'application/pdf')}
                    response = requests.post(
                        f"{self.base_url}/extract",
                        files=files,
                        timeout=self.timeout
                    )
                    return response
            
            response = self._test_with_timeout(_test_file)
            
            result["processing_time"] = time.time() - start_time
            result["status_code"] = response.status_code
            
            if response.status_code == 200:
                result["success"] = True
                result["response_data"] = response.json()
                if verbose:
                    print(f"   ✅ Success: {result['processing_time']:.2f}s")
            else:
                result["error"] = f"HTTP {response.status_code}: {response.text}"
                if verbose:
                    print(f"   ❌ Failed: {result['error']}")
            
        except TimeoutError:
            result["error"] = f"Timeout after {self.timeout} seconds"
            result["processing_time"] = time.time() - start_time
            if verbose:
                print(f"   ⏰ Timeout: {result['error']}")
        except Exception as e:
            result["error"] = str(e)
            result["processing_time"] = time.time() - start_time
            if verbose:
                print(f"   ❌ Error: {result['error']}")
        
        return result
    
    def _get_file_category(self, file_path: Path) -> str:
        """Determine file category from path"""
        for category, category_path in self.categories.items():
            if file_path.is_relative_to(category_path):
                return category
        return "unknown"
    
    def test_files(self, files: List[Path], verbose: bool = False, show_progress: bool = True) -> List[Dict[str, Any]]:
        """Test multiple files with progress tracking"""
        results = []
        
        if show_progress and len(files) > 1:
            self.progress_bar = tqdm(total=len(files), desc="Testing files", unit="file")
        
        try:
            for i, file_path in enumerate(files):
                if show_progress and self.progress_bar:
                    self.progress_bar.set_description(f"Testing {file_path.name}")
                
                result = self.test_single_file(file_path, verbose)
                results.append(result)
                
                # Update test state
                if result["success"]:
                    self.current_test_state["completed_tests"].append(str(file_path))
                else:
                    self.current_test_state["failed_tests"].append(str(file_path))
                
                if show_progress and self.progress_bar:
                    self.progress_bar.update(1)
                
                # Save state after each test
                self._save_test_state()
        
        finally:
            if self.progress_bar:
                self.progress_bar.close()
        
        return results
    
    def generate_report(self, results: List[Dict[str, Any]], save_to_file: bool = True, export_csv: bool = False) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r["success"])
        failed_tests = total_tests - successful_tests
        
        # Calculate statistics
        processing_times = [r["processing_time"] for r in results if r["processing_time"] > 0]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        max_processing_time = max(processing_times) if processing_times else 0
        min_processing_time = min(processing_times) if processing_times else 0
        
        # Categorize results
        by_category = {}
        for result in results:
            category = result["category"]
            if category not in by_category:
                by_category[category] = {"total": 0, "successful": 0, "failed": 0}
            by_category[category]["total"] += 1
            if result["success"]:
                by_category[category]["successful"] += 1
            else:
                by_category[category]["failed"] += 1
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "performance": {
                "average_processing_time": avg_processing_time,
                "max_processing_time": max_processing_time,
                "min_processing_time": min_processing_time,
                "total_processing_time": sum(processing_times)
            },
            "by_category": by_category,
            "results": results,
            "test_state": self.current_test_state
        }
        
        if save_to_file:
            timestamp = int(time.time())
            report_file = self.results_dir / f"enhanced_test_report_{timestamp}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📊 Report saved to: {report_file}")
            
            # CSV export (lazy initialization - no heavy work in __init__)
            if export_csv:
                csv_file = self._export_results_to_csv(results, timestamp)
                print(f"📄 CSV exported to: {csv_file}")
        
        return report
    
    def _export_results_to_csv(self, results: List[Dict[str, Any]], timestamp: int) -> str:
        """Export test results to CSV format using core CSV exporter"""
        csv_filename = f"api_test_results_{timestamp}.csv"
        csv_path = self.results_dir / csv_filename
        
        # Use core CSV exporter for summary CSV
        success = self.csv_exporter.export_to_summary_csv(results, str(csv_path))
        
        if not success:
            # Fallback to manual CSV export if core exporter fails
            import csv
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'File', 'Company', 'Statement Type', 'Years', 'Processing Time (s)',
                    'Pages Processed', 'Line Items Count', 'Total Assets', 'Total Liabilities', 
                    'Total Equity', 'Success', 'Status Code', 'Error Message'
                ])
                
                # Write data for each result
                for result in results:
                    response_data = result.get('response_data', {}) or {}
                    data_content = response_data.get('data', {}) or {}
                    
                    # Extract key information (same pattern as extract_test_results_to_csv.py)
                    filename = result['filename']
                    company = data_content.get('company_name', 'N/A')
                    statement_type = data_content.get('statement_type', 'N/A')
                    years = ', '.join(data_content.get('years_detected', []))
                    processing_time = result['processing_time']
                    pages_processed = response_data.get('pages_processed', 'N/A')
                    line_items_count = data_content.get('document_structure', {}).get('line_item_count', 'N/A')
                    
                    # Extract summary metrics
                    summary = data_content.get('summary_metrics', {})
                    total_assets = summary.get('total_assets', {}).get('value', 'N/A')
                    total_liabilities = summary.get('total_liabilities', {}).get('value', 'N/A')
                    total_equity = summary.get('total_equity', {}).get('value', 'N/A')
                    
                    success = result.get('success', False)
                    status_code = result.get('status_code', 'N/A')
                    error_message = result.get('error', 'N/A')
                    
                    writer.writerow([
                        filename, company, statement_type, years, f"{processing_time:.1f}",
                        pages_processed, line_items_count, total_assets, total_liabilities,
                        total_equity, success, status_code, error_message
                    ])
        
        return str(csv_path)
    
    def print_summary(self, report: Dict[str, Any]):
        """Print test summary to console"""
        summary = report["summary"]
        performance = report["performance"]
        
        print("\n" + "="*60)
        print("🎯 TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Successful: {summary['successful_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Average Processing Time: {performance['average_processing_time']:.2f}s")
        print(f"Total Processing Time: {performance['total_processing_time']:.2f}s")
        
        if report["by_category"]:
            print("\n📊 By Category:")
            for category, stats in report["by_category"].items():
                success_rate = (stats["successful"] / stats["total"] * 100) if stats["total"] > 0 else 0
                print(f"  {category}: {stats['successful']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Show failed tests
        failed_tests = [r for r in report["results"] if not r["success"]]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for result in failed_tests:
                print(f"  - {result['filename']}: {result['error']}")


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Enhanced Financial Statement Transcription API Test Suite")
    
    # Test selection options
    parser.add_argument("--file", type=str, help="Test specific file by name")
    parser.add_argument("--category", choices=["light", "origin", "templates"], help="Test files by category")
    parser.add_argument("--all", action="store_true", help="Test all available files")
    
    # Test configuration
    parser.add_argument("--timeout", type=int, default=300, help="Timeout per test in seconds (default: 300)")
    parser.add_argument("--base-url", type=str, default="http://localhost:8000", help="API base URL")
    
    # Output options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bar")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be tested without running tests")
    parser.add_argument("--export-csv", action="store_true", help="Export results to CSV format")
    parser.add_argument("--csv-filename", type=str, help="Custom CSV filename (optional)")
    
    # State management
    parser.add_argument("--resume", action="store_true", help="Resume from last test state")
    parser.add_argument("--clear-state", action="store_true", help="Clear test state and start fresh")
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = APITester(base_url=args.base_url, timeout=args.timeout)
    
    # Clear state if requested
    if args.clear_state:
        tester.current_test_state = {"completed_tests": [], "failed_tests": [], "last_run": None}
        tester._save_test_state()
        print("🧹 Test state cleared")
        return 0
    
    # Check API health first
    if not args.dry_run:
        print("🔍 Checking API health...")
        if not tester.check_api_health():
            print("❌ API is not healthy. Please start the API server first.")
            return 1
    
    # Determine which files to test
    files_to_test = []
    
    if args.file:
        # Test specific file
        file_found = False
        for category_path in tester.categories.values():
            if category_path.exists():
                for file_path in category_path.glob("*.pdf"):
                    if file_path.name == args.file:
                        files_to_test.append(file_path)
                        file_found = True
                        break
                if file_found:
                    break
        
        if not file_found:
            print(f"❌ File '{args.file}' not found in test fixtures")
            return 1
    
    elif args.category:
        # Test by category
        files_to_test = tester.get_available_files(args.category)
        if not files_to_test:
            print(f"❌ No files found in category '{args.category}'")
            return 1
    
    elif args.all:
        # Test all files
        files_to_test = tester.get_available_files()
        if not files_to_test:
            print("❌ No test files found")
            return 1
    
    else:
        # Default: test light files
        files_to_test = tester.get_available_files("light")
        if not files_to_test:
            print("❌ No light files found")
            return 1
    
    # Filter out completed tests if resuming
    if args.resume:
        completed = set(tester.current_test_state["completed_tests"])
        files_to_test = [f for f in files_to_test if str(f) not in completed]
        if not files_to_test:
            print("✅ All tests already completed")
            return 0
    
    # Show what will be tested
    print(f"\n🧪 Testing {len(files_to_test)} file(s):")
    for file_path in files_to_test:
        category = tester._get_file_category(file_path)
        size_mb = file_path.stat().st_size / (1024*1024)
        print(f"  - {file_path.name} ({category}, {size_mb:.2f} MB)")
    
    if args.dry_run:
        print("🔍 Dry run complete - no tests executed")
        return 0
    
    # Run tests
    print(f"\n🚀 Starting tests (timeout: {args.timeout}s per test)...")
    results = tester.test_files(files_to_test, verbose=args.verbose, show_progress=not args.no_progress)
    
    # Generate and display report
    report = tester.generate_report(results, save_to_file=True, export_csv=args.export_csv)
    tester.print_summary(report)
    
    # Return appropriate exit code
    return 0 if report["summary"]["failed_tests"] == 0 else 1


if __name__ == "__main__":
    exit(main())
