#!/usr/bin/env python3
"""
Simple Provider Comparison Script

Uses the existing working API server to compare OpenAI vs Anthropic providers.
This approach avoids breaking the working system by using what already functions.
"""

import os
import sys
import requests
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any, List


def compare_providers(test_file_path: str, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Compare OpenAI vs Anthropic using the working API server"""
    print(f"🔍 Comparing providers on: {Path(test_file_path).name}")
    print(f"🌐 API Server: {base_url}")
    print("-" * 60)
    
    results = {}
    
    # Test OpenAI
    print("🧪 Testing OpenAI...")
    os.environ['AI_PROVIDER'] = 'openai'
    results['openai'] = test_with_api(test_file_path, base_url)
    
    # Test Anthropic  
    print("🧪 Testing Anthropic...")
    os.environ['AI_PROVIDER'] = 'anthropic'
    results['anthropic'] = test_with_api(test_file_path, base_url)
    
    return results


def test_with_api(file_path: str, base_url: str) -> Dict[str, Any]:
    """Use the existing /extract endpoint that already works"""
    start_time = time.time()
    
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{base_url}/extract",
                files={'file': (Path(file_path).name, f, 'application/pdf')},
                timeout=300  # 5 minute timeout
            )
        
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'duration': duration,
                'data': data,
                'provider': os.environ.get('AI_PROVIDER'),
                'status_code': response.status_code,
                'error': None
            }
        else:
            return {
                'success': False,
                'duration': duration,
                'data': None,
                'provider': os.environ.get('AI_PROVIDER'),
                'status_code': response.status_code,
                'error': response.text
            }
            
    except requests.exceptions.RequestException as e:
        duration = time.time() - start_time
        return {
            'success': False,
            'duration': duration,
            'data': None,
            'provider': os.environ.get('AI_PROVIDER'),
            'status_code': None,
            'error': str(e)
        }
    except Exception as e:
        duration = time.time() - start_time
        return {
            'success': False,
            'duration': duration,
            'data': None,
            'provider': os.environ.get('AI_PROVIDER'),
            'status_code': None,
            'error': str(e)
        }


def generate_comparison_report(results: Dict[str, Any], save_json: bool = True) -> None:
    """Generate simple comparison report"""
    print("\n" + "=" * 60)
    print("🎯 PROVIDER COMPARISON RESULTS")
    print("=" * 60)
    
    for provider, result in results.items():
        print(f"\n📊 {provider.upper()}:")
        print(f"   ✅ Success: {result['success']}")
        print(f"   ⏱️  Duration: {result['duration']:.2f}s")
        
        if result['success']:
            data = result['data']
            print(f"   📄 Pages processed: {data.get('pages_processed', 'N/A')}")
            
            # Check if we have actual financial data
            financial_data = data.get('data', {})
            has_financial_data = bool(financial_data)
            print(f"   💰 Has financial data: {has_financial_data}")
            
            if has_financial_data:
                # Show some key metrics
                statement_type = financial_data.get('statement_type', 'Unknown')
                company_name = financial_data.get('company_name', 'Unknown')
                print(f"   🏢 Company: {company_name}")
                print(f"   📋 Statement Type: {statement_type}")
                
                # Count line items if available
                line_items = financial_data.get('line_items', {})
                if isinstance(line_items, dict):
                    total_items = sum(len(items) if isinstance(items, list) else 1 for items in line_items.values())
                    print(f"   📊 Line items extracted: {total_items}")
        else:
            print(f"   ❌ Error: {result['error']}")
            print(f"   🔢 Status Code: {result.get('status_code', 'N/A')}")
    
    # Overall comparison
    print(f"\n🏆 SUMMARY:")
    successful_providers = [p for p, r in results.items() if r['success']]
    if len(successful_providers) == 2:
        # Both succeeded - compare performance
        openai_duration = results['openai']['duration']
        anthropic_duration = results['anthropic']['duration']
        faster_provider = 'anthropic' if anthropic_duration < openai_duration else 'openai'
        speed_difference = abs(openai_duration - anthropic_duration)
        
        print(f"   ✅ Both providers succeeded")
        print(f"   🚀 Faster provider: {faster_provider} ({speed_difference:.2f}s difference)")
        
        # Compare data quality (simple check)
        openai_has_data = bool(results['openai']['data'].get('data', {}))
        anthropic_has_data = bool(results['anthropic']['data'].get('data', {}))
        
        if openai_has_data and anthropic_has_data:
            print(f"   📊 Both providers extracted financial data")
        elif openai_has_data:
            print(f"   📊 Only OpenAI extracted financial data")
        elif anthropic_has_data:
            print(f"   📊 Only Anthropic extracted financial data")
        else:
            print(f"   ⚠️  Neither provider extracted meaningful financial data")
            
    elif len(successful_providers) == 1:
        print(f"   ⚠️  Only {successful_providers[0]} succeeded")
    else:
        print(f"   ❌ Both providers failed")
    
    # Save results to JSON if requested
    if save_json:
        timestamp = int(time.time())
        results_file = f"provider_comparison_{timestamp}.json"
        
        # Prepare clean results for JSON export
        json_results = {}
        for provider, result in results.items():
            json_results[provider] = {
                'success': result['success'],
                'duration': result['duration'],
                'provider': result['provider'],
                'status_code': result.get('status_code'),
                'error': result['error'],
                'has_financial_data': bool(result.get('data', {}).get('data', {})) if result['success'] else False
            }
            
            if result['success'] and result['data']:
                financial_data = result['data'].get('data', {})
                json_results[provider]['extracted_info'] = {
                    'statement_type': financial_data.get('statement_type'),
                    'company_name': financial_data.get('company_name'),
                    'pages_processed': result['data'].get('pages_processed')
                }
        
        with open(results_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")


def check_api_health(base_url: str) -> bool:
    """Check if API server is healthy before running tests"""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API Server Healthy: {health_data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ API Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Health Check Error: {e}")
        return False


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Simple Provider Comparison using working API server")
    
    parser.add_argument("--file", type=str, 
                       default="tests/fixtures/light/AFS-2022 - statement extracted.pdf",
                       help="PDF file to test")
    parser.add_argument("--base-url", type=str, default="http://localhost:8000",
                       help="API server base URL")
    parser.add_argument("--no-json", action="store_true",
                       help="Don't save results to JSON file")
    
    args = parser.parse_args()
    
    # Validate file exists
    if not Path(args.file).exists():
        print(f"❌ File not found: {args.file}")
        sys.exit(1)
    
    # Check API health
    print("🔍 Checking API server health...")
    if not check_api_health(args.base_url):
        print("❌ API server is not healthy. Please start the API server first.")
        print("💡 Run: python api_app.py")
        sys.exit(1)
    
    # Run comparison
    results = compare_providers(args.file, args.base_url)
    
    # Generate report
    generate_comparison_report(results, save_json=not args.no_json)
    
    # Return appropriate exit code
    successful_tests = sum(1 for r in results.values() if r['success'])
    if successful_tests == 0:
        sys.exit(1)  # All failed
    elif successful_tests == 2:
        sys.exit(0)  # All succeeded
    else:
        sys.exit(2)  # Partial success


if __name__ == "__main__":
    main()












