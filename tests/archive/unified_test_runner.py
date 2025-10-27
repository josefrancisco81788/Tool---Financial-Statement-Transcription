"""
Unified test runner for all testing scenarios
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.config.test_config import TestConfig, QUICK_CONFIG, COMPREHENSIVE_CONFIG, REGRESSION_CONFIG
from tests.providers.provider_manager import ProviderManager
from tests.results.results_aggregator import ResultsAggregator
from tests.results.csv_exporter import CSVExporter


class UnifiedTestRunner:
    """Single test runner for all testing scenarios"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.provider_manager = ProviderManager()
        self.results_aggregator = ResultsAggregator()
        self.csv_exporter = CSVExporter()
        self.results_dir = Path("tests/results")
        self.results_dir.mkdir(exist_ok=True)
    
    def run_provider_comparison(self, providers: List[str], documents: List[str]) -> Dict[str, any]:
        """Compare multiple providers on same documents"""
        print(f"🔄 Running provider comparison: {', '.join(providers)}")
        print(f"📄 Documents: {', '.join(documents)}")
        print("=" * 60)
        
        all_results = []
        provider_results = {}
        
        for document in documents:
            print(f"\n📄 Testing document: {document}")
            
            # Test all providers on this document
            doc_results = self.provider_manager.test_multiple_providers(
                providers, document, self.config.timeout_seconds
            )
            
            # Store results
            for provider, result in doc_results.items():
                all_results.append(result)
                if provider not in provider_results:
                    provider_results[provider] = []
                provider_results[provider].append(result)
        
        # Generate comparison report
        comparison_report = self.results_aggregator.generate_provider_comparison(
            {provider: results[0] for provider, results in provider_results.items() if results}
        )
        
        # Print results
        self._print_provider_comparison(comparison_report)
        
        # Save results
        timestamp = int(time.time())
        self.results_aggregator.save_results(
            self.results_aggregator.aggregate_results(all_results),
            f"provider_comparison_{timestamp}.json"
        )
        
        # Export CSV results if configured
        if "csv" in self.config.output_formats:
            print(f"\n📊 Exporting CSV results...")
            csv_file = self.csv_exporter.export_test_results(all_results)
            print(f"✅ Detailed CSV exported: {csv_file}")
            
            # Export field-level analysis
            field_csv = self.csv_exporter.export_field_level_analysis(all_results)
            print(f"✅ Field-level analysis exported: {field_csv}")
            
            # Export provider comparison
            provider_csv = self.csv_exporter.export_provider_comparison(provider_results)
            print(f"✅ Provider comparison exported: {provider_csv}")
        
        return {
            'comparison_report': comparison_report,
            'all_results': all_results,
            'provider_results': provider_results
        }
    
    def run_baseline_establishment(self, provider: str, documents: List[str]) -> Dict[str, any]:
        """Establish performance baseline for a provider"""
        print(f"📊 Establishing baseline for {provider}")
        print(f"📄 Documents: {', '.join(documents)}")
        print("=" * 60)
        
        results = []
        
        for document in documents:
            print(f"\n📄 Testing document: {document}")
            result = self.provider_manager.test_provider(provider, document, self.config.timeout_seconds)
            results.append(result)
        
        # Aggregate results
        aggregated = self.results_aggregator.aggregate_results(results)
        
        # Print baseline summary
        self._print_baseline_summary(aggregated, provider)
        
        # Save baseline
        timestamp = int(time.time())
        baseline_filename = f"baseline_{provider}_{timestamp}.json"
        self.results_aggregator.save_results(aggregated, baseline_filename)
        
        return {
            'baseline_results': aggregated,
            'baseline_filename': baseline_filename,
            'individual_results': results
        }
    
    def run_regression_testing(self, provider: str, documents: List[str], baseline_file: str) -> Dict[str, any]:
        """Compare current results against baseline"""
        print(f"🔄 Running regression test for {provider}")
        print(f"📄 Documents: {', '.join(documents)}")
        print(f"📊 Baseline: {baseline_file}")
        print("=" * 60)
        
        # Run current tests
        results = []
        for document in documents:
            print(f"\n📄 Testing document: {document}")
            result = self.provider_manager.test_provider(provider, document, self.config.timeout_seconds)
            results.append(result)
        
        # Aggregate current results
        current_aggregated = self.results_aggregator.aggregate_results(results)
        
        # Compare with baseline
        comparison_report = self.results_aggregator.compare_with_baseline(current_aggregated, baseline_file)
        
        # Print regression results
        self._print_regression_results(comparison_report)
        
        # Save results
        timestamp = int(time.time())
        self.results_aggregator.save_results(current_aggregated, f"regression_test_{provider}_{timestamp}.json")
        
        return {
            'comparison_report': comparison_report,
            'current_results': current_aggregated,
            'individual_results': results
        }
    
    def run_accuracy_validation(self, documents: List[str]) -> Dict[str, any]:
        """Validate accuracy against templates"""
        print("🎯 Running accuracy validation")
        print(f"📄 Documents: {', '.join(documents)}")
        print("=" * 60)
        
        # This would integrate with the scoring framework
        # For now, we'll run a basic validation
        print("📊 Accuracy validation would integrate with scoring framework")
        print("   - Field extraction rate analysis")
        print("   - Template format accuracy")
        print("   - CSV export integration")
        
        return {'status': 'validation_placeholder'}
    
    def run_comprehensive_test(self) -> Dict[str, any]:
        """Run all test types based on configuration"""
        print("🚀 Running comprehensive test suite")
        print("=" * 60)
        
        # Get document list
        documents = self._get_document_list()
        
        results = {}
        
        # Provider comparison if enabled
        if self.config.provider_comparison and len(self.config.providers) > 1:
            results['provider_comparison'] = self.run_provider_comparison(
                self.config.providers, documents
            )
        
        # Individual provider tests
        for provider in self.config.providers:
            print(f"\n🧪 Testing {provider} provider")
            provider_results = []
            
            for document in documents:
                result = self.provider_manager.test_provider(provider, document, self.config.timeout_seconds)
                provider_results.append(result)
            
            results[f'{provider}_results'] = provider_results
        
        # Baseline comparison if enabled
        if self.config.baseline_comparison:
            print("\n📊 Baseline comparison would be performed here")
        
        return results
    
    def _get_document_list(self) -> List[str]:
        """Get list of documents to test"""
        documents = []
        
        # Add document sets
        for doc_set in self.config.document_sets:
            if doc_set == "light":
                light_dir = Path("tests/fixtures/light")
                if light_dir.exists():
                    documents.extend([str(f) for f in light_dir.glob("*.pdf")])
            elif doc_set == "origin":
                origin_dir = Path("tests/fixtures/origin")
                if origin_dir.exists():
                    documents.extend([str(f) for f in origin_dir.glob("*.pdf")])
        
        # Add custom documents
        documents.extend(self.config.custom_documents)
        
        return documents
    
    def _print_provider_comparison(self, report):
        """Print provider comparison results"""
        print(f"\n📊 PROVIDER COMPARISON RESULTS")
        print("=" * 60)
        
        if report.winner:
            print(f"🏆 Winner: {report.winner}")
            print(f"📈 Recommendation: {report.recommendation}")
            print(f"💡 Reasoning: {report.reasoning}")
            
            if report.performance_differences:
                print(f"\n📊 Performance Differences:")
                for provider, diff in report.performance_differences.items():
                    print(f"   {provider}: {diff:+.1%} vs {report.winner}")
        else:
            print(f"❌ No clear winner determined")
            print(f"📝 {report.recommendation}")
    
    def _print_baseline_summary(self, aggregated, provider):
        """Print baseline establishment summary"""
        print(f"\n📊 BASELINE ESTABLISHED FOR {provider.upper()}")
        print("=" * 60)
        print(f"Total Tests: {aggregated.total_tests}")
        print(f"Success Rate: {aggregated.success_rate:.1%}")
        print(f"Average Processing Time: {aggregated.average_processing_time:.1f}s")
        print(f"Average Extraction Rate: {aggregated.average_extraction_rate:.1%}")
        print(f"Production Ready Rate: {aggregated.production_ready_rate:.1%}")
    
    def _print_regression_results(self, report):
        """Print regression test results"""
        print(f"\n📊 REGRESSION TEST RESULTS")
        print("=" * 60)
        
        if report.regression_detected:
            print("⚠️ REGRESSION DETECTED!")
        else:
            print("✅ NO REGRESSION DETECTED")
        
        print(f"Extraction Rate Change: {report.extraction_rate_change:+.1%}")
        print(f"Processing Time Change: {report.processing_time_change:+.1f}s")
        print(f"Success Rate Change: {report.success_rate_change:+.1%}")


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Unified Test Runner for Financial Statement Transcription API")
    
    # Configuration options
    parser.add_argument("--config", help="Configuration file (YAML or JSON)")
    parser.add_argument("--preset", choices=["quick", "comprehensive", "regression"], 
                       help="Use preset configuration")
    
    # Provider options
    parser.add_argument("--providers", help="Comma-separated list of providers (openai,anthropic)")
    parser.add_argument("--provider", help="Single provider for baseline/regression testing")
    
    # Document options
    parser.add_argument("--documents", help="Comma-separated list of document sets (light,origin)")
    parser.add_argument("--file", help="Single document file to test")
    
    # Test type options
    parser.add_argument("--compare", action="store_true", help="Compare multiple providers")
    parser.add_argument("--baseline", action="store_true", help="Establish baseline")
    parser.add_argument("--regression", action="store_true", help="Run regression test")
    parser.add_argument("--validate", action="store_true", help="Run accuracy validation")
    
    # Baseline file for regression testing
    parser.add_argument("--baseline-file", help="Baseline file for regression testing")
    
    # Other options
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        if args.config.endswith('.yaml') or args.config.endswith('.yml'):
            config = TestConfig.from_yaml(args.config)
        else:
            config = TestConfig.from_json(args.config)
    elif args.preset:
        if args.preset == "quick":
            config = QUICK_CONFIG
        elif args.preset == "comprehensive":
            config = COMPREHENSIVE_CONFIG
        elif args.preset == "regression":
            config = REGRESSION_CONFIG
    else:
        config = TestConfig()
    
    # Override with command line arguments
    if args.providers:
        config.providers = [p.strip() for p in args.providers.split(',')]
    if args.documents:
        config.document_sets = [d.strip() for d in args.documents.split(',')]
    if args.timeout:
        config.timeout_seconds = args.timeout
    
    # Initialize runner
    runner = UnifiedTestRunner(config)
    
    # Validate providers
    print("🔍 Validating providers...")
    validation_results = runner.provider_manager.validate_all_providers()
    for provider, is_valid in validation_results.items():
        if not is_valid:
            print(f"❌ Provider {provider} validation failed")
            sys.exit(1)
    
    # Run tests based on arguments
    if args.compare:
        documents = [args.file] if args.file else runner._get_document_list()
        runner.run_provider_comparison(config.providers, documents)
    elif args.baseline:
        if not args.provider:
            print("❌ --provider required for baseline establishment")
            sys.exit(1)
        documents = [args.file] if args.file else runner._get_document_list()
        runner.run_baseline_establishment(args.provider, documents)
    elif args.regression:
        if not args.provider or not args.baseline_file:
            print("❌ --provider and --baseline-file required for regression testing")
            sys.exit(1)
        documents = [args.file] if args.file else runner._get_document_list()
        runner.run_regression_testing(args.provider, documents, args.baseline_file)
    elif args.validate:
        documents = [args.file] if args.file else runner._get_document_list()
        runner.run_accuracy_validation(documents)
    else:
        # Run comprehensive test
        runner.run_comprehensive_test()


if __name__ == "__main__":
    main()
