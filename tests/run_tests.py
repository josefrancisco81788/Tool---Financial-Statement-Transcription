"""
Test runner for Financial Statement Transcription API tests.
"""

import os
import sys
import subprocess
import time
from pathlib import Path


class TestRunner:
    """Test runner for the API test suite"""
    
    def __init__(self):
        """Initialize test runner"""
        self.project_root = Path(__file__).parent.parent
        self.test_dir = Path(__file__).parent
        self.results_dir = self.test_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
    
    def run_unit_tests(self):
        """Run unit tests"""
        print("🧪 Running Unit Tests...")
        print("-" * 40)
        
        cmd = [
            sys.executable, "-m", "pytest", 
            str(self.test_dir / "unit"),
            "-v",
            "--tb=short",
            f"--junitxml={self.results_dir}/unit_tests.xml"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    
    def run_integration_tests(self):
        """Run integration tests"""
        print("\n🔗 Running Integration Tests...")
        print("-" * 40)
        
        cmd = [
            sys.executable, "-m", "pytest", 
            str(self.test_dir / "integration"),
            "-v",
            "--tb=short",
            f"--junitxml={self.results_dir}/integration_tests.xml"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    
    def run_performance_tests(self):
        """Run performance tests"""
        print("\n⚡ Running Performance Tests...")
        print("-" * 40)
        
        cmd = [
            sys.executable, "-m", "pytest", 
            str(self.test_dir / "performance"),
            "-v",
            "--tb=short",
            f"--junitxml={self.results_dir}/performance_tests.xml"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    
    def run_validation_tests(self):
        """Run validation tests"""
        print("\n✅ Running Validation Tests...")
        print("-" * 40)
        
        cmd = [
            sys.executable, "-m", "pytest", 
            str(self.test_dir / "validation"),
            "-v",
            "--tb=short",
            f"--junitxml={self.results_dir}/validation_tests.xml"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Financial Statement Transcription API Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run test suites
        unit_success = self.run_unit_tests()
        integration_success = self.run_integration_tests()
        performance_success = self.run_performance_tests()
        validation_success = self.run_validation_tests()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Print summary
        print("\n📊 Test Summary")
        print("=" * 60)
        print(f"Unit Tests: {'✅ PASSED' if unit_success else '❌ FAILED'}")
        print(f"Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
        print(f"Performance Tests: {'✅ PASSED' if performance_success else '❌ FAILED'}")
        print(f"Validation Tests: {'✅ PASSED' if validation_success else '❌ FAILED'}")
        print(f"Total Time: {total_time:.2f} seconds")
        
        # Overall success
        overall_success = all([unit_success, integration_success, performance_success, validation_success])
        print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        return overall_success
    
    def run_specific_test(self, test_path: str):
        """Run a specific test"""
        print(f"🎯 Running Specific Test: {test_path}")
        print("-" * 40)
        
        cmd = [
            sys.executable, "-m", "pytest", 
            str(self.test_dir / test_path),
            "-v",
            "--tb=short"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Financial Statement Transcription API tests")
    parser.add_argument("--test-type", choices=["unit", "integration", "performance", "validation", "all"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--specific", help="Run a specific test file")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.specific:
        success = runner.run_specific_test(args.specific)
    elif args.test_type == "unit":
        success = runner.run_unit_tests()
    elif args.test_type == "integration":
        success = runner.run_integration_tests()
    elif args.test_type == "performance":
        success = runner.run_performance_tests()
    elif args.test_type == "validation":
        success = runner.run_validation_tests()
    else:  # all
        success = runner.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
