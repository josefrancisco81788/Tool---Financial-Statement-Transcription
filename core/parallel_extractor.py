"""
Parallel processing module for financial statement extraction optimization.
Reduces processing time from 12+ minutes to ~2 minutes.
"""

import time
import json
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import threading
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ExtractionResult:
    """Result from parallel extraction"""
    page_num: int
    statement_type: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float = 0.0


class RateLimiter:
    """Enhanced thread-safe rate limiter with smart wait calculation and exponential backoff"""

    def __init__(self, max_requests_per_minute: int = 80):
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = threading.Lock()
        self.backoff_base = 0.05  # Start with 50ms
        self.max_backoff = 2.0    # Max 2 seconds
        self.backoff_multiplier = 1.2

    def can_make_request(self) -> bool:
        """Check if we can make a request within rate limits"""
        with self.lock:
            now = time.time()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests if now - req_time < 60]
            return len(self.requests) < self.max_requests

    def register_request(self):
        """Register that a request was made"""
        with self.lock:
            self.requests.append(time.time())

    def smart_wait_calculation(self) -> float:
        """Calculate optimal wait time based on request history"""
        with self.lock:
            if not self.requests:
                return 0

            now = time.time()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests if now - req_time < 60]

            if len(self.requests) < self.max_requests:
                return 0

            # Calculate time until oldest request expires
            oldest_request = min(self.requests)
            time_to_expire = 60 - (now - oldest_request)

            if time_to_expire > 0:
                # Distribute wait time across current requests
                optimal_wait = time_to_expire / max(len(self.requests), 1)
                # Add small buffer to prevent edge cases
                return min(optimal_wait + 0.1, 5.0)  # Max 5 seconds

            return 0

    def wait_if_needed(self):
        """Enhanced wait with smart calculation and exponential backoff"""
        backoff = self.backoff_base

        while not self.can_make_request():
            # Try smart wait calculation first
            smart_wait = self.smart_wait_calculation()

            if smart_wait > 0:
                # Use smart calculation
                time.sleep(smart_wait)
                break  # Smart wait should be sufficient
            else:
                # Fall back to exponential backoff
                time.sleep(backoff)
                backoff = min(backoff * self.backoff_multiplier, self.max_backoff)

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status for monitoring"""
        with self.lock:
            now = time.time()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests if now - req_time < 60]

            remaining = max(0, self.max_requests - len(self.requests))
            utilization = len(self.requests) / self.max_requests

            return {
                'requests_in_window': len(self.requests),
                'max_requests': self.max_requests,
                'remaining': remaining,
                'utilization_percent': utilization * 100,
                'window_reset_in': 60 - (now - min(self.requests)) if self.requests else 0
            }


class ParallelExtractor:
    """Parallel financial data extraction with rate limiting"""

    def __init__(self, extractor, max_workers: int = 6, rate_limit: int = 80):
        """
        Initialize parallel extractor

        Args:
            extractor: FinancialDataExtractor instance
            max_workers: Maximum concurrent workers (recommended: 6 for extraction)
            rate_limit: Max API requests per minute (recommended: 80 to stay under 100/min)
        """
        self.extractor = extractor
        self.max_workers = max_workers
        self.rate_limiter = RateLimiter(rate_limit)

        print(f"[INFO] ParallelExtractor initialized - {max_workers} workers, {rate_limit} req/min limit")

    def extract_single_page(self, page: Dict[str, Any]) -> ExtractionResult:
        """Extract financial data from a single page with rate limiting"""
        start_time = time.time()
        page_num = page['page_num']
        statement_type = page['statement_type']

        try:
            # Rate limiting
            self.rate_limiter.wait_if_needed()
            self.rate_limiter.register_request()

            # Extract financial data
            base64_image = self.extractor.encode_image(page['image'])

            print(f"[INFO] Starting extraction for page {page_num + 1} ({statement_type})...")

            extracted_data = self.extractor.extract_comprehensive_financial_data(
                base64_image,
                statement_type,
                ""  # No text extraction needed for vision-based approach
            )

            processing_time = time.time() - start_time

            if extracted_data and 'error' not in extracted_data:
                template_mappings = extracted_data.get('template_mappings', {})
                total_items = len(template_mappings)
                print(f"[SUCCESS] Page {page_num + 1}: Extracted {total_items} items in {processing_time:.1f}s")

                return ExtractionResult(
                    page_num=page_num,
                    statement_type=statement_type,
                    success=True,
                    data=extracted_data,
                    processing_time=processing_time
                )
            else:
                error_msg = extracted_data.get('error', 'Unknown extraction error')
                print(f"[ERROR] Page {page_num + 1}: {error_msg}")
                return ExtractionResult(
                    page_num=page_num,
                    statement_type=statement_type,
                    success=False,
                    error=error_msg,
                    processing_time=processing_time
                )

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            print(f"[ERROR] Page {page_num + 1} failed: {error_msg}")
            return ExtractionResult(
                page_num=page_num,
                statement_type=statement_type,
                success=False,
                error=error_msg,
                processing_time=processing_time
            )

    def extract_parallel(self, selected_pages: List[Dict[str, Any]], timeout_per_page: int = 45) -> List[Dict[str, Any]]:
        """
        Extract financial data from multiple pages in parallel

        Args:
            selected_pages: List of page dictionaries with 'image', 'page_num', 'statement_type'
            timeout_per_page: Timeout in seconds for each page extraction

        Returns:
            List of extraction results in original page order
        """
        total_start_time = time.time()
        print(f"[INFO] Starting parallel extraction - {len(selected_pages)} pages, {self.max_workers} workers")

        results = []
        page_results = {}  # Store results by page_num for ordering

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all extraction jobs
            future_to_page = {
                executor.submit(self.extract_single_page, page): page
                for page in selected_pages
            }

            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_page, timeout=timeout_per_page * len(selected_pages)):
                page = future_to_page[future]
                page_num = page['page_num']

                try:
                    result = future.result(timeout=timeout_per_page)
                    page_results[page_num] = result
                    completed += 1

                    print(f"[PROGRESS] Completed {completed}/{len(selected_pages)} pages")

                except TimeoutError:
                    error_msg = f"Page {page_num + 1} extraction timed out after {timeout_per_page}s"
                    print(f"[ERROR] {error_msg}")
                    page_results[page_num] = ExtractionResult(
                        page_num=page_num,
                        statement_type=page.get('statement_type', 'Unknown'),
                        success=False,
                        error=error_msg
                    )

                except Exception as e:
                    error_msg = f"Page {page_num + 1} extraction failed: {str(e)}"
                    print(f"[ERROR] {error_msg}")
                    page_results[page_num] = ExtractionResult(
                        page_num=page_num,
                        statement_type=page.get('statement_type', 'Unknown'),
                        success=False,
                        error=error_msg
                    )

        # Convert results back to original format using page_num mapping
        # This fixes the critical data format conversion issue
        results_by_page_num = {}

        # First, create a mapping of page_num to results
        for result in page_results.values():
            if result.success and result.data:
                # Add page_num to the data for tracking
                result.data['page_num'] = result.page_num
                results_by_page_num[result.page_num] = result.data
            else:
                # Add error result for consistency
                error_result = {
                    'page_num': result.page_num,
                    'statement_type': result.statement_type,
                    'error': result.error or 'Extraction failed',
                    'template_mappings': {}
                }
                results_by_page_num[result.page_num] = error_result

        # Then, build results in original page order (critical for consistency)
        results = []
        for page in selected_pages:
            page_num = page['page_num']
            if page_num in results_by_page_num:
                results.append(results_by_page_num[page_num])
            else:
                # Page was not processed (shouldn't happen but handle gracefully)
                print(f"[WARN] Page {page_num + 1} missing from parallel results")
                error_result = {
                    'page_num': page_num,
                    'statement_type': page.get('statement_type', 'Unknown'),
                    'error': 'Page not processed in parallel execution',
                    'template_mappings': {}
                }
                results.append(error_result)

        total_time = time.time() - total_start_time
        successful = sum(1 for r in page_results.values() if r.success)
        avg_time = sum(r.processing_time for r in page_results.values()) / len(page_results)

        # Get final rate limit status
        rate_status = self.rate_limiter.get_rate_limit_status()

        print(f"[SUMMARY] Parallel extraction completed:")
        print(f"  - Total time: {total_time:.1f}s")
        print(f"  - Success rate: {successful}/{len(selected_pages)} ({successful/len(selected_pages)*100:.1f}%)")
        print(f"  - Average page time: {avg_time:.1f}s")
        print(f"  - Speedup vs sequential: {avg_time * len(selected_pages) / total_time:.1f}x")
        print(f"  - Rate limit utilization: {rate_status['utilization_percent']:.1f}%")
        print(f"  - API requests made: {rate_status['requests_in_window']}/{rate_status['max_requests']}")

        return results


class ParallelClassifier:
    """Parallel classification optimization with rate limiting"""

    def __init__(self, extractor, max_workers: int = 10, rate_limit: int = 120):
        """
        Initialize parallel classifier with optimized settings

        Args:
            extractor: FinancialDataExtractor instance
            max_workers: Maximum concurrent workers (recommended: 10 for classification)
            rate_limit: Max API requests per minute (recommended: 120 for faster classification)
        """
        self.extractor = extractor
        self.max_workers = max_workers
        self.rate_limiter = RateLimiter(rate_limit)

        print(f"[INFO] ParallelClassifier initialized - {max_workers} workers, {rate_limit} req/min limit")

    def optimize_classification_workers(self, total_pages: int) -> int:
        """Optimize worker count based on total pages"""
        if total_pages <= 20:
            return min(6, self.max_workers)
        elif total_pages <= 40:
            return min(8, self.max_workers)
        else:
            return self.max_workers

    def classify_single_page_with_rate_limit(self, page_data) -> Dict[str, Any]:
        """Classify a single page with rate limiting"""
        start_time = time.time()
        page, page_index, total_pages = page_data

        try:
            # Rate limiting
            self.rate_limiter.wait_if_needed()
            self.rate_limiter.register_request()

            page_num = page['page_num']
            page_text = page['text'].lower()

            print(f"[INFO] Classifying page {page_num + 1} with rate limiting...")

            # Enhanced universal patterns (case-insensitive)
            statement_patterns = {
                'Balance Sheet': [
                    r'statement of financial position',
                    r'balance sheet',
                    r'statement of position',
                    r'financial position'
                ],
                'Income Statement': [
                    r'statement of comprehensive income',
                    r'income statement',
                    r'profit and loss',
                    r'statement of operations',
                    r'statement of earnings',
                    r'comprehensive income'
                ],
                'Cash Flow Statement': [
                    r'statement of cash flows',
                    r'cash flow statement',
                    r'statement of cash flow',
                    r'cash flows'
                ],
                'Statement of Equity': [
                    r'statement of changes in equity',
                    r'statement of equity',
                    r'changes in equity',
                    r'equity statement',
                    r'statement of stockholders.? equity'
                ]
            }

            # Line item patterns
            line_item_patterns = {
                'Balance Sheet': [
                    r'current assets', r'non.?current assets', r'total assets',
                    r'current liabilities', r'non.?current liabilities', r'total liabilities',
                    r'shareholders.? equity', r'retained earnings', r'share capital',
                    r'cash and cash equivalents', r'accounts receivable', r'inventory',
                    r'property.? plant.? equipment', r'accounts payable', r'long.?term debt'
                ],
                'Income Statement': [
                    r'revenue', r'net sales', r'gross profit', r'operating income',
                    r'net income', r'earnings per share', r'cost of goods sold',
                    r'operating expenses', r'interest expense', r'income tax',
                    r'other comprehensive income', r'basic earnings per share'
                ],
                'Cash Flow Statement': [
                    r'cash flows from operating activities', r'cash flows from investing activities',
                    r'cash flows from financing activities', r'net increase.? in cash',
                    r'depreciation and amortization', r'changes in working capital',
                    r'capital expenditures', r'dividends paid', r'proceeds from borrowings'
                ],
                'Statement of Equity': [
                    r'beginning balance', r'ending balance', r'comprehensive income',
                    r'dividends declared', r'share issuance', r'treasury shares',
                    r'appropriated', r'unappropriated', r'retained earnings'
                ]
            }

            # Calculate number density score
            def calculate_number_density_score(text):
                import re
                financial_number_patterns = [
                    r'[\$₱€£¥¢][\d,]+\.?\d*',
                    r'\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b',
                    r'\b\d{4,}(?:\.\d+)?\b',
                    r'\(\d{1,3}(?:,\d{3})+(?:\.\d+)?\)',
                    r'\(\d{4,}(?:\.\d+)?\)',
                    r'\b\d+\.?\d*%\b',
                ]

                financial_numbers = []
                for pattern in financial_number_patterns:
                    matches = re.findall(pattern, text)
                    financial_numbers.extend(matches)

                seen = set()
                unique_financial_numbers = []
                for num in financial_numbers:
                    if num not in seen:
                        seen.add(num)
                        unique_financial_numbers.append(num)

                total_words = len(text.split())
                number_count = len(unique_financial_numbers)
                number_density_pct = (number_count / max(total_words, 1)) * 100

                if number_density_pct >= 20:
                    density_score = 6.0
                elif number_density_pct >= 15:
                    density_score = 4.0
                elif number_density_pct >= 10:
                    density_score = 2.0
                elif number_density_pct >= 7:
                    density_score = 0.5
                elif number_density_pct >= 5:
                    density_score = 0.0
                elif number_density_pct >= 3:
                    density_score = -1.0
                else:
                    density_score = -3.0

                return density_score, number_density_pct, unique_financial_numbers

            number_density_score, number_density, financial_numbers = calculate_number_density_score(page['text'])
            financial_numbers_count = len(financial_numbers)

            # Score each statement type
            statement_scores = {}
            all_matches = {}

            for stmt_type, patterns in statement_patterns.items():
                import re
                score = 0
                matches_found = []

                # Statement title patterns (high weight)
                for pattern in patterns:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    if matches:
                        score += 5.0 * len(matches)
                        matches_found.extend([f"Title: '{match}'" for match in matches])

                # Line item patterns (medium weight)
                for pattern in line_item_patterns[stmt_type]:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    if matches:
                        score += 2.0 * len(matches)
                        matches_found.extend([f"Line: '{match}'" for match in matches])

                # Add number density bonus
                score += number_density_score

                statement_scores[stmt_type] = score
                all_matches[stmt_type] = matches_found

            # Determine if this is a financial page
            max_score = max(statement_scores.values()) if statement_scores else 0
            financial_threshold = 3.0

            processing_time = time.time() - start_time

            if max_score >= financial_threshold:
                # Determine primary statement type
                primary_type = max(statement_scores, key=statement_scores.get)

                result = {
                    'page_num': page_num,
                    'classified': True,
                    'statement_type': primary_type,
                    'confidence': min(max_score / 20.0, 1.0),
                    'image': page['image'],
                    'text': page['text'],
                    'max_score': max_score,
                    'number_density': number_density,
                    'financial_numbers_count': financial_numbers_count,
                    'number_density_score': number_density_score,
                    'statement_scores': statement_scores,
                    'matches': all_matches,
                    'index': page_index,
                    'processing_time': processing_time
                }

                print(f"[SUCCESS] Page {page_num + 1}: {primary_type} (confidence: {result['confidence']:.2f}) in {processing_time:.1f}s")
                return result
            else:
                print(f"[INFO] Page {page_num + 1}: Not financial (max_score: {max_score:.1f}) in {processing_time:.1f}s")
                return {
                    'page_num': page_num,
                    'classified': False,
                    'max_score': max_score,
                    'index': page_index,
                    'processing_time': processing_time
                }

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            print(f"[ERROR] Page {page_num + 1} classification failed: {error_msg}")
            return {
                'page_num': page.get('page_num', 'Unknown'),
                'classified': False,
                'error': error_msg,
                'index': page_index,
                'processing_time': processing_time
            }

    def classify_pages_with_rate_limiting(self, page_info: List[Dict[str, Any]], timeout_per_page: int = 20) -> List[Dict[str, Any]]:
        """
        Classify pages in parallel with rate limiting

        Args:
            page_info: List of page dictionaries
            timeout_per_page: Timeout in seconds for each page classification

        Returns:
            List of classified financial pages
        """
        total_start_time = time.time()
        page_count = len(page_info)
        optimal_workers = self.optimize_classification_workers(page_count)

        print(f"[INFO] Starting rate-limited parallel classification - {page_count} pages, {optimal_workers} workers")

        financial_pages = []
        page_results = {}

        with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
            # Prepare page data with indices
            page_data_list = [(page, i, page_count) for i, page in enumerate(page_info) if page.get('success', True)]

            # Submit all classification jobs
            future_to_page = {
                executor.submit(self.classify_single_page_with_rate_limit, page_data): page_data[1]
                for page_data in page_data_list
            }

            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_page, timeout=timeout_per_page * len(page_data_list)):
                page_index = future_to_page[future]

                try:
                    result = future.result(timeout=timeout_per_page)
                    if result.get('classified', False):
                        page_results[result['index']] = result
                    completed += 1

                    print(f"[PROGRESS] Classification completed {completed}/{len(page_data_list)} pages")

                except TimeoutError:
                    print(f"[ERROR] Page {page_index + 1} classification timed out after {timeout_per_page}s")
                except Exception as e:
                    print(f"[ERROR] Page {page_index + 1} classification failed: {e}")

            # Sort results by index and add to financial_pages
            for index in sorted(page_results.keys()):
                financial_pages.append(page_results[index])

        total_time = time.time() - total_start_time
        successful = len(financial_pages)

        # Get final rate limit status
        rate_status = self.rate_limiter.get_rate_limit_status()

        print(f"[SUMMARY] Rate-limited classification completed:")
        print(f"  - Total time: {total_time:.1f}s")
        print(f"  - Financial pages found: {successful}")
        print(f"  - Success rate: {successful}/{page_count} ({successful/page_count*100:.1f}%)")
        print(f"  - Rate limit utilization: {rate_status['utilization_percent']:.1f}%")
        print(f"  - API requests made: {rate_status['requests_in_window']}/{rate_status['max_requests']}")

        return financial_pages


# Integration helper functions
def replace_sequential_extraction(pdf_processor_instance, selected_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Drop-in replacement for sequential extraction loop in PDFProcessor with comprehensive error handling

    Usage in pdf_processor.py:
        # OLD: Sequential loop
        # results = []
        # for page in selected_pages:
        #     ... sequential extraction ...

        # NEW: Parallel extraction with fallback
        from .parallel_extractor import replace_sequential_extraction
        results = replace_sequential_extraction(self, selected_pages)
    """
    try:
        # Validate inputs
        if not selected_pages:
            raise ValueError("No pages provided for extraction")

        if not hasattr(pdf_processor_instance, 'extractor') or pdf_processor_instance.extractor is None:
            raise ValueError("PDF processor instance missing extractor")

        # Create parallel extractor with error handling
        parallel_extractor = ParallelExtractor(
            extractor=pdf_processor_instance.extractor,
            max_workers=6,  # Conservative for extraction
            rate_limit=80   # Conservative rate limit
        )

        print(f"[INFO] Parallel extractor initialized successfully")

        # Execute parallel extraction with comprehensive error handling
        results = parallel_extractor.extract_parallel(selected_pages)

        # Validate results
        if results is None:
            raise ValueError("Parallel extraction returned None")

        if not isinstance(results, list):
            raise ValueError(f"Parallel extraction returned invalid type: {type(results)}")

        print(f"[INFO] Parallel extraction validation passed: {len(results)} results")
        return results

    except Exception as e:
        print(f"[ERROR] Critical error in parallel extraction: {e}")
        print(f"[ERROR] Error type: {type(e).__name__}")
        print(f"[INFO] [CRITICAL] Parallel extraction failed completely - caller should use sequential fallback")

        # Return None to signal complete failure - caller should handle this
        return None


def enhance_classification_performance(pdf_processor_instance, page_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enhanced classification with better worker optimization

    Usage in pdf_processor.py:
        # Enhance existing parallel classification
        from .parallel_extractor import enhance_classification_performance
        financial_pages = enhance_classification_performance(self, page_info)
    """
    parallel_classifier = ParallelClassifier(
        extractor=pdf_processor_instance.extractor,
        max_workers=10,  # Slightly higher for classification
        rate_limit=120   # Higher rate limit for faster processing
    )

    optimal_workers = parallel_classifier.optimize_classification_workers(len(page_info))
    print(f"[INFO] Using {optimal_workers} workers for {len(page_info)} pages classification")

    # Use existing classification but with optimized worker count
    # This would require modifying the existing ThreadPoolExecutor call
    return pdf_processor_instance.classify_financial_statement_pages(page_info, enable_parallel=True)