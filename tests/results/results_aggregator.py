"""
Results aggregation system for unified testing pipeline
"""

import json
import csv
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import TestResult from providers
sys.path.insert(0, str(Path(__file__).parent.parent))
from providers.base_provider import TestResult


@dataclass
class AggregatedResults:
    """Aggregated results from multiple test runs"""
    
    total_tests: int
    successful_tests: int
    failed_tests: int
    success_rate: float
    
    # Performance metrics
    average_processing_time: float
    min_processing_time: float
    max_processing_time: float
    
    # Framework metrics
    average_extraction_rate: float
    average_format_accuracy: float
    average_overall_score: float
    
    # Production readiness
    production_ready_count: int
    production_ready_rate: float
    
    # Provider comparison
    provider_results: Dict[str, Dict[str, Any]]


@dataclass
class ComparisonReport:
    """Report comparing current results with baseline"""
    
    baseline_file: str
    current_results: AggregatedResults
    baseline_results: AggregatedResults
    
    # Comparison metrics
    extraction_rate_change: float
    processing_time_change: float
    success_rate_change: float
    
    # Regression detection
    regression_detected: bool
    regression_threshold: float = 0.1  # 10% threshold


@dataclass
class ProviderComparisonReport:
    """Report comparing multiple providers"""
    
    providers: List[str]
    results: Dict[str, TestResult]
    
    # Comparison metrics
    winner: Optional[str]
    performance_differences: Dict[str, float]
    statistical_significance: bool
    
    # Recommendations
    recommendation: str
    reasoning: str


class ResultsAggregator:
    """Aggregates and analyzes test results"""
    
    def __init__(self):
        self.results_dir = Path("tests/results")
        self.results_dir.mkdir(exist_ok=True)
    
    def aggregate_results(self, results: List[TestResult]) -> AggregatedResults:
        """Aggregate multiple test results"""
        if not results:
            return AggregatedResults(
                total_tests=0, successful_tests=0, failed_tests=0, success_rate=0.0,
                average_processing_time=0.0, min_processing_time=0.0, max_processing_time=0.0,
                average_extraction_rate=0.0, average_format_accuracy=0.0, average_overall_score=0.0,
                production_ready_count=0, production_ready_rate=0.0, provider_results={}
            )
        
        # Basic metrics
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - successful_tests
        success_rate = successful_tests / total_tests if total_tests > 0 else 0.0
        
        # Processing time metrics
        processing_times = [r.processing_time for r in results if r.success]
        average_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
        min_processing_time = min(processing_times) if processing_times else 0.0
        max_processing_time = max(processing_times) if processing_times else 0.0
        
        # Framework metrics (only for successful results)
        successful_results = [r for r in results if r.success]
        extraction_rates = [r.extraction_rate for r in successful_results if r.extraction_rate is not None]
        format_accuracies = [r.format_accuracy for r in successful_results if r.format_accuracy is not None]
        overall_scores = [r.overall_score for r in successful_results if r.overall_score is not None]
        
        average_extraction_rate = sum(extraction_rates) / len(extraction_rates) if extraction_rates else 0.0
        average_format_accuracy = sum(format_accuracies) / len(format_accuracies) if format_accuracies else 0.0
        average_overall_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0
        
        # Production readiness
        production_ready_count = sum(1 for r in successful_results if r.production_ready)
        production_ready_rate = production_ready_count / len(successful_results) if successful_results else 0.0
        
        # Provider results
        provider_results = {}
        for provider in set(r.provider for r in results):
            provider_tests = [r for r in results if r.provider == provider]
            provider_successful = [r for r in provider_tests if r.success]
            
            provider_results[provider] = {
                'total_tests': len(provider_tests),
                'successful_tests': len(provider_successful),
                'success_rate': len(provider_successful) / len(provider_tests) if provider_tests else 0.0,
                'average_processing_time': sum(r.processing_time for r in provider_successful) / len(provider_successful) if provider_successful else 0.0,
                'average_extraction_rate': sum(r.extraction_rate for r in provider_successful if r.extraction_rate is not None) / len([r for r in provider_successful if r.extraction_rate is not None]) if [r for r in provider_successful if r.extraction_rate is not None] else 0.0
            }
        
        return AggregatedResults(
            total_tests=total_tests,
            successful_tests=successful_tests,
            failed_tests=failed_tests,
            success_rate=success_rate,
            average_processing_time=average_processing_time,
            min_processing_time=min_processing_time,
            max_processing_time=max_processing_time,
            average_extraction_rate=average_extraction_rate,
            average_format_accuracy=average_format_accuracy,
            average_overall_score=average_overall_score,
            production_ready_count=production_ready_count,
            production_ready_rate=production_ready_rate,
            provider_results=provider_results
        )
    
    def compare_with_baseline(self, current: AggregatedResults, baseline_file: str) -> ComparisonReport:
        """Compare current results with baseline"""
        # Load baseline results
        baseline_path = self.results_dir / baseline_file
        if not baseline_path.exists():
            raise FileNotFoundError(f"Baseline file not found: {baseline_path}")
        
        with open(baseline_path, 'r') as f:
            baseline_data = json.load(f)
        
        # Create baseline AggregatedResults (simplified)
        baseline_results = AggregatedResults(
            total_tests=baseline_data.get('total_tests', 0),
            successful_tests=baseline_data.get('successful_tests', 0),
            failed_tests=baseline_data.get('failed_tests', 0),
            success_rate=baseline_data.get('success_rate', 0.0),
            average_processing_time=baseline_data.get('average_processing_time', 0.0),
            min_processing_time=baseline_data.get('min_processing_time', 0.0),
            max_processing_time=baseline_data.get('max_processing_time', 0.0),
            average_extraction_rate=baseline_data.get('average_extraction_rate', 0.0),
            average_format_accuracy=baseline_data.get('average_format_accuracy', 0.0),
            average_overall_score=baseline_data.get('average_overall_score', 0.0),
            production_ready_count=baseline_data.get('production_ready_count', 0),
            production_ready_rate=baseline_data.get('production_ready_rate', 0.0),
            provider_results=baseline_data.get('provider_results', {})
        )
        
        # Calculate changes
        extraction_rate_change = current.average_extraction_rate - baseline_results.average_extraction_rate
        processing_time_change = current.average_processing_time - baseline_results.average_processing_time
        success_rate_change = current.success_rate - baseline_results.success_rate
        
        # Detect regression
        regression_detected = (
            extraction_rate_change < -0.1 or  # 10% decrease in extraction rate
            processing_time_change > 30.0 or  # 30 second increase in processing time
            success_rate_change < -0.05       # 5% decrease in success rate
        )
        
        return ComparisonReport(
            baseline_file=baseline_file,
            current_results=current,
            baseline_results=baseline_results,
            extraction_rate_change=extraction_rate_change,
            processing_time_change=processing_time_change,
            success_rate_change=success_rate_change,
            regression_detected=regression_detected
        )
    
    def generate_provider_comparison(self, results: Dict[str, TestResult]) -> ProviderComparisonReport:
        """Generate provider comparison report"""
        if len(results) < 2:
            return ProviderComparisonReport(
                providers=list(results.keys()),
                results=results,
                winner=None,
                performance_differences={},
                statistical_significance=False,
                recommendation="Need at least 2 providers for comparison",
                reasoning="Insufficient data for comparison"
            )
        
        # Calculate performance differences
        successful_results = {k: v for k, v in results.items() if v.success}
        if len(successful_results) < 2:
            return ProviderComparisonReport(
                providers=list(results.keys()),
                results=results,
                winner=None,
                performance_differences={},
                statistical_significance=False,
                recommendation="No successful results for comparison",
                reasoning="All providers failed"
            )
        
        # Compare extraction rates
        extraction_rates = {k: v.extraction_rate for k, v in successful_results.items() if v.extraction_rate is not None}
        if not extraction_rates:
            return ProviderComparisonReport(
                providers=list(results.keys()),
                results=results,
                winner=None,
                performance_differences={},
                statistical_significance=False,
                recommendation="No extraction rate data available",
                reasoning="Missing framework assessment"
            )
        
        # Find winner based on extraction rate
        winner = max(extraction_rates, key=extraction_rates.get)
        winner_rate = extraction_rates[winner]
        
        # Calculate differences
        performance_differences = {}
        for provider, rate in extraction_rates.items():
            if provider != winner:
                performance_differences[provider] = rate - winner_rate
        
        # Simple statistical significance (difference > 5%)
        max_difference = max(abs(diff) for diff in performance_differences.values()) if performance_differences else 0
        statistical_significance = max_difference > 0.05
        
        # Generate recommendation
        if statistical_significance:
            recommendation = f"Use {winner} for production"
            reasoning = f"{winner} has {winner_rate:.1%} extraction rate, significantly better than alternatives"
        else:
            recommendation = "Providers are comparable, choose based on other factors"
            reasoning = "Performance differences are not statistically significant"
        
        return ProviderComparisonReport(
            providers=list(results.keys()),
            results=results,
            winner=winner,
            performance_differences=performance_differences,
            statistical_significance=statistical_significance,
            recommendation=recommendation,
            reasoning=reasoning
        )
    
    def save_results(self, results: AggregatedResults, filename: str):
        """Save aggregated results to file"""
        output_path = self.results_dir / filename
        
        # Convert to dictionary for JSON serialization
        data = {
            'total_tests': results.total_tests,
            'successful_tests': results.successful_tests,
            'failed_tests': results.failed_tests,
            'success_rate': results.success_rate,
            'average_processing_time': results.average_processing_time,
            'min_processing_time': results.min_processing_time,
            'max_processing_time': results.max_processing_time,
            'average_extraction_rate': results.average_extraction_rate,
            'average_format_accuracy': results.average_format_accuracy,
            'average_overall_score': results.average_overall_score,
            'production_ready_count': results.production_ready_count,
            'production_ready_rate': results.production_ready_rate,
            'provider_results': results.provider_results
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Results saved to: {output_path}")
