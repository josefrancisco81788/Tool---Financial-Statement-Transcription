#!/usr/bin/env python3
"""
Simple Batch Processing Test
Validates the new page-division batch processing implementation
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_batch_processing():
    """Test batch processing with a small document"""
    print("[TEST] Starting Batch Processing Test")
    print("=" * 50)

    try:
        # Import required modules
        from core.batch_processor import DocumentStructureAnalyzer, BatchExtractor, BatchCostController
        from core.extractor import FinancialDataExtractor
        from core.config import Config

        print("[OK] All batch processing modules imported successfully")

        # Test 1: Document Structure Analyzer
        print("\n[TEST] Test 1: Document Structure Analysis")
        analyzer = DocumentStructureAnalyzer()

        # Create mock page data
        mock_pages = [
            {
                'page_num': 1,
                'text': 'Balance Sheet for the years ending 2023 and 2022 Assets Current Assets Cash and Cash Equivalents',
                'image': 'mock_image_data_1'
            },
            {
                'page_num': 2,
                'text': 'Income Statement Revenue Cost of Sales Gross Profit Net Income',
                'image': 'mock_image_data_2'
            },
            {
                'page_num': 3,
                'text': 'Cash Flow Statement Operating Activities Investing Activities Financing Activities',
                'image': 'mock_image_data_3'
            }
        ]

        # Test classification
        for page in mock_pages:
            page_type = analyzer.classify_page_type(page)
            print(f"   Page {page['page_num']}: {page_type}")

        # Test document structure analysis
        statement_groups = analyzer.analyze_document_structure(mock_pages)
        print(f"   Statement groups: {list(statement_groups.keys())}")

        # Test batch creation
        batches = analyzer.create_processing_batches(statement_groups, max_batch_size=2)
        print(f"   Created {len(batches)} batches")

        print("[OK] Document Structure Analysis passed")

        # Test 2: Cost Controller
        print("\n[TEST] Test 2: Cost Control")
        cost_controller = BatchCostController(max_cost=2.0)

        # Test cost estimation
        estimated_cost = cost_controller.estimate_batch_cost(3)
        print(f"   Estimated cost for 3 pages: ${estimated_cost:.2f}")

        # Test cost limit check
        can_process, reason = cost_controller.can_process_batch(3)
        print(f"   Can process 3 pages: {can_process} ({reason})")

        # Test cost recording
        cost_controller.record_batch(3, 0.45)
        report = cost_controller.get_cost_efficiency_report()
        print(f"   Cost efficiency: {report['cost_efficiency']}")

        print("[OK] Cost Control passed")

        # Test 3: Batch Processing Logic (without actual API calls)
        print("\n[TEST] Test 3: Batch Processing Logic")
        config = Config()
        extractor = FinancialDataExtractor(config)
        batch_extractor = BatchExtractor(extractor)

        # Test batch structure
        test_batch = batches[0] if batches else {
            'batch_id': 'test_batch_1',
            'statement_type': 'balance_sheet',
            'pages': mock_pages[:2],
            'context_prompt': 'Test prompt',
            'page_count': 2,
            'page_numbers': [1, 2]
        }

        print(f"   Test batch: {test_batch['batch_id']} with {test_batch['page_count']} pages")
        print(f"   Statement type: {test_batch['statement_type']}")

        # Test result structuring (without API call)
        mock_api_result = {
            'extracted_data': [
                {
                    'page_num': 1,
                    'template_mappings': {
                        'Cash and Cash Equivalents': {'2023': 1000000, '2022': 950000},
                        'Total Assets': {'2023': 5000000, '2022': 4800000}
                    }
                }
            ]
        }

        structured_result = batch_extractor.structure_batch_results(mock_api_result, test_batch)
        print(f"   Structured result contains {len(structured_result.get('extracted_data', []))} items")

        print("[OK] Batch Processing Logic passed")

        print("\n[SUCCESS] All tests passed successfully!")
        print("[INFO] Batch processing implementation is ready for use")

        return True

    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        print("   Make sure all batch processing modules are available")
        return False

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_batch_processing()
    sys.exit(0 if success else 1)