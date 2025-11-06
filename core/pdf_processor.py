"""
PDF processing module for converting PDFs to images and extracting text.
Copied exactly from alpha-testing-v1 for optimal performance.
"""

import io
import json
import fitz  # PyMuPDF
from PIL import Image
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from .extractor import FinancialDataExtractor
from .config import Config


class PDFProcessor:
    """PDF processing class for converting PDFs to images and extracting text"""
    
    def __init__(self, extractor: Optional[FinancialDataExtractor] = None):
        """Initialize PDF processor with optional extractor - NO WORK DONE IN INIT"""
        self.extractor = extractor or FinancialDataExtractor()
        self.config = Config()
        
        # Lazy initialization - no work done during import
        self._backends = None
        self.pdf_processing_available = False
        self.pdf_library = None
        self.pdf_error_message = None
    
    def _detect_backends(self):
        """Detect available PDF processing backends with timeout protection"""
        import os
        import shutil
        
        backends = {"pymupdf": False, "pdf2image": False, "poppler_path": None}
        
        # Test PyMuPDF first (more reliable on Windows)
        try:
            import fitz
            test_doc = fitz.Document()
            test_doc.close()
            backends["pymupdf"] = True
        except Exception:
            pass
        
        # Test pdf2image only if not disabled
        if not os.getenv("DISABLE_PDF2IMAGE", "").lower() in ("1", "true", "yes"):
            try:
                import pdf2image
                # Check for Poppler
                poppler_path = os.getenv("POPPLER_PATH")
                if poppler_path or shutil.which("pdftoppm"):
                    backends["pdf2image"] = True
                    backends["poppler_path"] = poppler_path
            except Exception:
                pass
        
        return backends
    
    def _ensure_backends(self):
        """Ensure backends are detected (lazy initialization)"""
        if self._backends is None:
            self._backends = self._detect_backends()
            
            # Set the primary library based on availability
            if self._backends["pymupdf"]:
                self.pdf_library = "pymupdf"
                self.pdf_processing_available = True
                print("[INFO] Using PyMuPDF for PDF processing (reliable)")
            elif self._backends["pdf2image"]:
                self.pdf_library = "pdf2image"
                self.pdf_processing_available = True
                print("[INFO] Using pdf2image for PDF processing (optimal performance)")
            else:
                self.pdf_error_message = "No usable PDF processing library available"
                self.pdf_processing_available = False
    
    def _with_timeout(self, fn, timeout=15):
        """Execute function with timeout protection"""
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(fn)
            try:
                return future.result(timeout=timeout)
            except FutureTimeoutError:
                raise TimeoutError(f"Operation timed out after {timeout} seconds")
    
    def convert_pdf_to_images(self, pdf_file, enable_parallel: bool = True) -> Tuple[List[Image.Image], List[Dict[str, Any]]]:
        """
        Convert PDF to images and extract text using AI Vision API.
        Uses lazy initialization with timeout protection.
        
        Args:
            pdf_file: PDF file (file-like object or bytes)
            enable_parallel: Whether to use parallel processing
            
        Returns:
            Tuple of (images, page_info)
        """
        # Ensure backends are detected (lazy initialization)
        self._ensure_backends()
        
        if not self.pdf_processing_available:
            raise Exception(f"PDF processing is not available: {self.pdf_error_message}")
        
        try:
            # Get PDF data
            if hasattr(pdf_file, 'read'):
                pdf_data = pdf_file.read()
            else:
                pdf_data = pdf_file
            
            # Use backend-specific conversion with timeout protection
            if self.pdf_library == "pdf2image":
                def _convert_with_pdf2image():
                    from pdf2image import convert_from_bytes
                    return convert_from_bytes(
                        pdf_data, 
                        dpi=200,
                        poppler_path=self._backends.get("poppler_path")
                    )
                images = self._with_timeout(_convert_with_pdf2image, timeout=120)
                
            elif self.pdf_library == "pymupdf":
                def _convert_with_pymupdf():
                    import fitz
                    # Try opening with file path first, then fallback to bytes
                    if isinstance(pdf_file, str):
                        doc = fitz.open(pdf_file)
                    else:
                        doc = fitz.open(stream=pdf_data)
                    images = []
                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        pix = page.get_pixmap(matrix=fitz.Matrix(200/72, 200/72))  # 200 DPI
                        img_data = pix.tobytes("png")
                        images.append(Image.open(io.BytesIO(img_data)))
                    doc.close()
                    return images
                images = self._with_timeout(_convert_with_pymupdf, timeout=120)
                
            else:
                raise Exception("No PDF processing library available")
            
            # Extract text from images using the same parallel processing as alpha-testing-v1
            page_info = self._extract_text_from_images(images, enable_parallel)
            
            return images, page_info
            
        except Exception as e:
            raise Exception(f"Error converting PDF to images: {str(e)}")
    
    def _extract_text_from_images(self, images: List[Image.Image], enable_parallel: bool = True) -> List[Dict[str, Any]]:
        """
        Extract text from images using AI Vision API.
        
        Args:
            images: List of PIL Images
            enable_parallel: Whether to use parallel processing
            
        Returns:
            List of page info dictionaries
        """
        if not enable_parallel:
            return self._extract_text_sequential(images)
        
        # Parallel text extraction
        def extract_text_for_page(page_data):
            """Extract text from a single page - designed for parallel execution"""
            page_num, image = page_data
            try:
                page_text = self._extract_text_with_vision_api(image, page_num + 1)
                return {
                    'page_num': page_num + 1,
                    'text': page_text.lower(),
                    'image': image,
                    'success': True,
                    'error': None
                }
            except Exception as e:
                return {
                    'page_num': page_num + 1,
                    'text': '',
                    'image': image,
                    'success': False,
                    'error': str(e)
                }
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=self.config.PARALLEL_WORKERS) as executor:
            # Submit all pages for processing
            page_data_list = [(page_num, image) for page_num, image in enumerate(images)]
            future_to_page = {executor.submit(extract_text_for_page, page_data): page_data[0] 
                             for page_data in page_data_list}
            
            # Collect results as they complete
            results = {}
            failed_pages = []
            
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    result = future.result()
                    results[result['page_num']] = result
                    
                    if not result['success']:
                        failed_pages.append(result)
                        
                except Exception as e:
                    failed_pages.append({
                        'page_num': page_num + 1,
                        'text': '',
                        'image': images[page_num],
                        'success': False,
                        'error': str(e)
                    })
            
            # Sort results by page number
            page_info = [results[page_num] for page_num in sorted(results.keys())]
            
            # Add failed pages
            page_info.extend(failed_pages)
            
            return page_info
    
    def _extract_text_sequential(self, images: List[Image.Image]) -> List[Dict[str, Any]]:
        """Extract text from images sequentially"""
        page_info = []
        
        for page_num, image in enumerate(images):
            try:
                page_text = self._extract_text_with_vision_api(image, page_num + 1)
                page_info.append({
                    'page_num': page_num + 1,
                    'text': page_text.lower(),
                    'image': image,
                    'success': True,
                    'error': None
                })
            except Exception as e:
                page_info.append({
                    'page_num': page_num + 1,
                    'text': '',
                    'image': image,
                    'success': False,
                    'error': str(e)
                })
        
        return page_info
    
    def _extract_text_with_vision_api(self, image: Image.Image, page_num: int) -> str:
        """
        Extract text from a single image using AI Vision API.
        
        Args:
            image: PIL Image
            page_num: Page number for logging
            
        Returns:
            Extracted text
        """
        try:
            # Convert image to base64
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            img_data = img_buffer.getvalue()
            base64_image = self.extractor.encode_image(img_data)
            
            # Use AI Vision API to extract text
            prompt = """
            Extract all text from this image. Return only the text content, no formatting or explanations.
            Focus on financial data, numbers, and labels.
            """
            
            # Use the dual-provider system for text extraction
            if self.extractor.provider == "openai":
                response = self.extractor._call_openai_api(base64_image, prompt)
            elif self.extractor.provider == "anthropic":
                response = self.extractor._call_anthropic_api(base64_image, prompt)
            else:
                raise Exception(f"Unknown provider: {self.extractor.provider}")
            
            return response or ""
            
        except Exception as e:
            raise Exception(f"Error extracting text from page {page_num}: {str(e)}")
    
    def classify_financial_statement_pages(self, page_info: List[Dict[str, Any]], enable_parallel: bool = True) -> List[Dict[str, Any]]:
        """
        Enhanced classification with universal patterns, number density scoring, and case-insensitive matching.
        Copied exactly from working Streamlit version.
        """
        import re
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        financial_pages = []
        
        # Enhanced universal patterns (case-insensitive) - copied from Streamlit
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
        
        # Enhanced line item patterns (case-insensitive) - copied from Streamlit
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
        
        # Supporting indicators (case-insensitive) - copied from Streamlit
        supporting_indicators = [
            r'with comparative figures', r'see notes to', r'notes to financial statements',
            r'audited', r'unaudited', r'management.?s discussion',
            r'for the year ended', r'as of', r'december 31', r'march 31',
            r'amounts in', r'thousands', r'millions', r'philippine peso',
            r'us dollars', r'consolidated', r'parent company'
        ]
        
        def calculate_number_density_score(page_text):
            """Calculate enhanced number density score - copied from Streamlit"""
            # Smart financial number detection
            financial_number_patterns = [
                r'[\$₱€£¥¢][\d,]+\.?\d*',  # Currency amounts: $1,000.00, ₱500,000
                r'\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b',  # Comma-separated numbers: 1,000,000.50
                r'\b\d{4,}(?:\.\d+)?\b',  # Large numbers without commas: 50000, 1000000.5
                r'\(\d{1,3}(?:,\d{3})+(?:\.\d+)?\)',  # Negative numbers in parentheses: (1,000.00)
                r'\(\d{4,}(?:\.\d+)?\)',  # Negative large numbers: (50000)
                r'\b\d+\.?\d*%\b',  # Percentages: 15.5%, 20%
            ]
            
            # Find all financial numbers
            financial_numbers = []
            for pattern in financial_number_patterns:
                matches = re.findall(pattern, page_text)
                financial_numbers.extend(matches)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_financial_numbers = []
            for num in financial_numbers:
                if num not in seen:
                    seen.add(num)
                    unique_financial_numbers.append(num)
            
            # Calculate density metrics
            total_chars = len(page_text)
            total_words = len(page_text.split())
            number_count = len(unique_financial_numbers)
            
            # Calculate number density as percentage of words
            number_density_pct = (number_count / max(total_words, 1)) * 100
            
            # Enhanced scoring system - copied from Streamlit
            if number_density_pct >= 20:    # Very high density - strong positive (financial tables)
                density_score = 6.0
            elif number_density_pct >= 15:  # High density - positive
                density_score = 4.0
            elif number_density_pct >= 10:  # Medium-high density - positive
                density_score = 2.0
            elif number_density_pct >= 7:   # Low-medium density - slight positive
                density_score = 0.5
            elif number_density_pct >= 5:   # Low density - neutral
                density_score = 0.0
            elif number_density_pct >= 3:   # Very low density - slight negative
                density_score = -1.0
            else:                           # Extremely low density - strong negative (narrative text)
                density_score = -3.0
            
            return density_score, number_density_pct, unique_financial_numbers
        
        def classify_single_page(page_data):
            """Classify a single page - copied from Streamlit"""
            page, page_index, total_pages = page_data
            try:
                page_num = page['page_num']
                page_text = page['text'].lower()  # Convert to lowercase for case-insensitive matching
                
                # Calculate number density score
                number_density_score, number_density, financial_numbers = calculate_number_density_score(page['text'])
                financial_numbers_count = len(financial_numbers)
                
                # Score each statement type
                statement_scores = {}
                all_matches = {}
                
                for stmt_type, patterns in statement_patterns.items():
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
                    
                    # Supporting indicators (low weight)
                    for pattern in supporting_indicators:
                        matches = re.findall(pattern, page_text, re.IGNORECASE)
                        if matches:
                            score += 1.0 * len(matches)
                            matches_found.extend([f"Support: '{match}'" for match in matches])
                    
                    # Add number density score (enhanced weight)
                    score += number_density_score
                    
                    statement_scores[stmt_type] = score
                    all_matches[stmt_type] = matches_found
                
                # Determine classification - find the highest scoring statement type
                max_score = max(statement_scores.values())
                
                # ENHANCED THRESHOLD - copied from Streamlit
                if max_score >= 3.0:
                    # Find which statement type has the highest score
                    statement_type = max(statement_scores.keys(), key=lambda k: statement_scores[k])
                    
                    return {
                        'page_num': page_num,
                        'statement_type': statement_type,
                        'confidence': max_score,
                        'number_density': number_density,
                        'financial_numbers_count': financial_numbers_count,
                        'number_density_score': number_density_score,
                        'image': page['image'],
                        'text': page['text'],  # Keep original text for processing
                        'classified': True,
                        'statement_scores': statement_scores,
                        'matches': all_matches,
                        'index': page_index
                    }
                else:
                    return {
                        'page_num': page_num,
                        'classified': False,
                        'max_score': max_score,
                        'number_density': number_density,
                        'financial_numbers_count': financial_numbers_count,
                        'number_density_score': number_density_score,
                        'statement_scores': statement_scores,
                        'matches': all_matches,
                        'index': page_index
                    }
                    
            except Exception as e:
                return {
                    'page_num': page.get('page_num', 'Unknown'),
                    'classified': False,
                    'error': str(e),
                    'index': page_index
                }
        
        if not enable_parallel or len(page_info) <= 3:
            # Sequential processing for small documents
            for i, page in enumerate(page_info):
                if not page['success']:
                    continue
                result = classify_single_page((page, i, len(page_info)))
                if result.get('classified', False):
                    financial_pages.append(result)
        else:
            # Parallel processing - OPTIMIZED for large documents with RATE LIMITING
            page_count = len(page_info)

            # Use rate-limited parallel classification for large documents
            if page_count > 10:
                print(f"[INFO] Using RATE-LIMITED parallel classification: {page_count} pages")

                try:
                    from .parallel_extractor import ParallelClassifier

                    # Dynamic worker count based on document size
                    if page_count <= 20:
                        optimal_workers = 6
                    elif page_count <= 40:
                        optimal_workers = 8
                    else:
                        optimal_workers = 12  # For 54-page documents

                    classifier = ParallelClassifier(
                        extractor=self.extractor,
                        max_workers=optimal_workers,
                        rate_limit=120  # Conservative rate limit for classification
                    )

                    # Use rate-limited classification
                    financial_pages = classifier.classify_pages_with_rate_limiting(page_info)
                    print(f"[SUCCESS] Rate-limited classification completed: {len(financial_pages)} financial pages found")

                except ImportError as e:
                    print(f"[WARN] ParallelClassifier not available: {e}")
                    print("[INFO] Falling back to basic parallel classification")
                    # Fall back to basic parallel processing
                    optimal_workers = min(8, page_count)  # Conservative fallback

                except Exception as e:
                    print(f"[ERROR] Rate-limited classification failed: {e}")
                    print("[INFO] Falling back to basic parallel classification")
                    # Fall back to basic parallel processing
                    optimal_workers = min(8, page_count)  # Conservative fallback
                else:
                    # Rate-limited classification succeeded, return results
                    return financial_pages

            # Basic parallel processing (fallback or small documents)
            if page_count <= 20:
                optimal_workers = 6
            elif page_count <= 40:
                optimal_workers = 8
            else:
                optimal_workers = 10  # Reduced from 12 for safety

            print(f"[INFO] Basic parallel classification: {page_count} pages, {optimal_workers} workers")

            with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
                # Prepare page data with indices
                page_data_list = [(page, i, len(page_info)) for i, page in enumerate(page_info) if page['success']]
                
                # Submit all pages for classification
                future_to_page = {executor.submit(classify_single_page, page_data): page_data[1] 
                                 for page_data in page_data_list}
                
                # Collect results as they complete
                results = {}
                for future in as_completed(future_to_page):
                    page_index = future_to_page[future]
                    try:
                        result = future.result()
                        if result.get('classified', False):
                            results[result['index']] = result
                    except Exception as e:
                        print(f"Error classifying page {page_index}: {str(e)}")
                
                # Sort results by index and add to financial_pages
                for index in sorted(results.keys()):
                    financial_pages.append(results[index])
        
        # Sort by confidence
        financial_pages.sort(key=lambda x: x['confidence'], reverse=True)
        
        return financial_pages
    
    def classify_pages_batch_vision(self, images: List[str], batch_size: int = 4) -> List[int]:
        """
        Classify pages in batches using vision model to identify financial statement pages
        
        Args:
            images: List of base64-encoded page images
            batch_size: Number of pages to process per batch
            
        Returns:
            List of page numbers containing financial statements
        """
        financial_pages = []
        
        # Process pages in batches
        for i in range(0, len(images), batch_size):
            batch_images = images[i:i + batch_size]
            batch_pages = self.classify_single_batch_vision(batch_images, i)
            financial_pages.extend(batch_pages)
        
        return financial_pages
    
    def classify_single_batch_vision(self, batch_images: List[str], start_page_num: int) -> List[tuple]:
        """
        Classify a single batch of pages using vision model
        
        Args:
            batch_images: List of base64-encoded page images for this batch
            start_page_num: Starting page number for this batch
            
        Returns:
            List of page numbers in this batch that contain financial statements
        """
        try:
            # Classify each page in the batch individually
            financial_pages = []
            
            for i, page_image in enumerate(batch_images):
                try:
                    page_num = start_page_num + i
                    prompt = self._build_simple_classification_prompt()
                    result = self.extractor._call_anthropic_api(page_image, prompt)
                    
                    # Simple binary classification
                    if "yes" in result.lower():
                        financial_pages.append((page_num, "financial"))
                        print(f"[INFO] Page {page_num + 1}: Contains financial data")
                    else:
                        print(f"[INFO] Page {page_num + 1}: No financial data")
                        
                except Exception as e:
                    print(f"[ERROR] Error classifying page {page_num + 1}: {e}")
            
            return financial_pages
            
        except Exception as e:
            print(f"Batch classification failed: {e}")
            return []
    
    def classify_pages_with_vision(self, page_images: List[Image.Image]) -> List[Dict[str, Any]]:
        """
        Classify pages using four-score vision-based system (Balance Sheet, Income Statement, Cash Flow, Equity Statement)
        
        Args:
            page_images: List of PIL Image objects for each page
            
        Returns:
            List of financial pages with statement type and confidence scores
        """
        print(f"[INFO] Starting four-score vision classification on {len(page_images)} pages...")
        
        financial_pages = []
        
        for i, page_image in enumerate(page_images):
            try:
                # Convert PIL image to base64
                base64_image = self.extractor.encode_image(page_image)
                
                # Get four scores for this page
                scores = self._classify_page_four_scores(base64_image)
                
                # Determine if this page should be included
                max_score = max(scores['balance_sheet'], scores['income_statement'], scores['cash_flow'], scores['equity_statement'])
                
                if max_score >= 70:  # High confidence threshold
                    # Identify primary statement type
                    if scores['balance_sheet'] == max_score:
                        statement_type = "balance_sheet"
                    elif scores['income_statement'] == max_score:
                        statement_type = "income_statement"
                    elif scores['cash_flow'] == max_score:
                        statement_type = "cash_flow"
                    else:
                        statement_type = "equity_statement"
                    
                    financial_pages.append({
                        'page_num': i,
                        'statement_type': statement_type,
                        'scores': scores,
                        'confidence': max_score / 100,
                        'image': page_image
                    })
                    
                    print(f"[INFO] Page {i + 1}: {statement_type} (BS:{scores['balance_sheet']}, IS:{scores['income_statement']}, CF:{scores['cash_flow']}, ES:{scores['equity_statement']})")
                else:
                    print(f"[INFO] Page {i + 1}: Not financial (BS:{scores['balance_sheet']}, IS:{scores['income_statement']}, CF:{scores['cash_flow']}, ES:{scores['equity_statement']})")
                    
            except Exception as e:
                print(f"[ERROR] Error classifying page {i + 1}: {e}")
                continue
        
        print(f"[INFO] Four-score classification complete: {len(financial_pages)} financial pages identified")
        return financial_pages
    
    def _classify_page_four_scores(self, base64_image: str) -> Dict[str, int]:
        """
        Classify a single page and return four scores (Balance Sheet, Income Statement, Cash Flow, Equity Statement)
        
        Args:
            base64_image: Base64-encoded page image
            
        Returns:
            Dict with balance_sheet, income_statement, cash_flow, equity_statement scores (0-100)
        """
        prompt = self._build_four_score_classification_prompt()
        
        try:
            result = self.extractor._call_anthropic_api(base64_image, prompt)
            
            # Debug: Show raw API response
            print(f"[DEBUG] Raw API response: '{result[:200]}...' (length: {len(result)})")
            
            if not result or result.strip() == "":
                print(f"[WARN] Empty API response")
                return {'balance_sheet': 0, 'income_statement': 0, 'cash_flow': 0, 'equity_statement': 0}
            
            # Parse the JSON response
            scores = json.loads(result)
            
            # Validate scores are in range 0-100
            for key in ['balance_sheet', 'income_statement', 'cash_flow', 'equity_statement']:
                if key not in scores:
                    scores[key] = 0
                else:
                    scores[key] = max(0, min(100, int(scores[key])))
            
            return scores
            
        except json.JSONDecodeError as e:
            print(f"[WARN] JSON decode error: {e}")
            print(f"[WARN] Raw response: '{result[:500]}'")
            return {'balance_sheet': 0, 'income_statement': 0, 'cash_flow': 0, 'equity_statement': 0}
        except Exception as e:
            print(f"[WARN] Failed to parse classification scores: {e}")
            print(f"[WARN] Raw response: '{result[:500] if 'result' in locals() else 'No response'}'")
            return {'balance_sheet': 0, 'income_statement': 0, 'cash_flow': 0, 'equity_statement': 0}
    
    def _build_four_score_classification_prompt(self) -> str:
        """Build four-score classification prompt for Balance Sheet, Income Statement, Cash Flow, Equity Statement"""
        return """You must respond with ONLY a valid JSON object. Do not include any explanation or analysis.

Score this page 0-100 for each financial statement type:

1. Balance Sheet likelihood (0-100):
   - Contains: Assets, Liabilities, Equity
   - Structure: Current/Non-current categorization
   - Equation: Assets = Liabilities + Equity
   - Examples: "Total Assets", "Current Liabilities", "Shareholders' Equity"

2. Income Statement likelihood (0-100):
   - Contains: Revenue, Expenses, Profit/Loss
   - Structure: Operating/Non-operating sections
   - Shows: Performance over a period
   - Examples: "Total Revenue", "Operating Expenses", "Net Income"

3. Cash Flow Statement likelihood (0-100):
   - Contains: Operating/Investing/Financing activities
   - Structure: Cash inflows/outflows
   - Shows: Cash movement over period
   - Examples: "Cash from Operations", "Capital Expenditures", "Dividends Paid"

4. Equity Statement likelihood (0-100):
   - Contains: Share capital movements, Retained earnings changes
   - Structure: Beginning balance, adjustments, ending balance
   - Shows: Equity changes over period
   - Examples: "Retained Earnings Beginning", "Prior Year Adjustment", "Appropriation", "Share Capital"

Scoring guide:
0-20: Not this statement type
20-50: Minor mentions (likely notes/appendix)
50-70: Partial statement or summary
70-100: Primary statement page

RESPOND WITH ONLY THIS JSON FORMAT (no other text):
{
    "balance_sheet": X,
    "income_statement": Y,
    "cash_flow": Z,
    "equity_statement": W
}"""
    
    def _build_four_score_classification_prompt_batch(self, num_images: int) -> str:
        """Build four-score classification prompt for multiple images in a batch"""
        return f"""You must respond with ONLY a valid JSON array. Do not include any explanation or analysis.

Analyze each of the {num_images} images provided and score each page 0-100 for each financial statement type.

For EACH image, provide scores for:

1. Balance Sheet likelihood (0-100):
   - Contains: Assets, Liabilities, Equity
   - Structure: Current/Non-current categorization
   - Equation: Assets = Liabilities + Equity
   - Examples: "Total Assets", "Current Liabilities", "Shareholders' Equity"

2. Income Statement likelihood (0-100):
   - Contains: Revenue, Expenses, Profit/Loss
   - Structure: Operating/Non-operating sections
   - Shows: Performance over a period
   - Examples: "Total Revenue", "Operating Expenses", "Net Income"

3. Cash Flow Statement likelihood (0-100):
   - Contains: Operating/Investing/Financing activities
   - Structure: Cash inflows/outflows
   - Shows: Cash movement over period
   - Examples: "Cash from Operations", "Capital Expenditures", "Dividends Paid"

4. Equity Statement likelihood (0-100):
   - Contains: Share capital movements, Retained earnings changes
   - Structure: Beginning balance, adjustments, ending balance
   - Shows: Equity changes over period
   - Examples: "Retained Earnings Beginning", "Prior Year Adjustment", "Appropriation", "Share Capital"

Scoring guide:
0-20: Not this statement type
20-50: Minor mentions (likely notes/appendix)
50-70: Partial statement or summary
70-100: Primary statement page

RESPOND WITH ONLY THIS JSON ARRAY FORMAT (one object per image, in order):
[
    {{"balance_sheet": X1, "income_statement": Y1, "cash_flow": Z1, "equity_statement": W1}},
    {{"balance_sheet": X2, "income_statement": Y2, "cash_flow": Z2, "equity_statement": W2}},
    ...
    {{"balance_sheet": X{num_images}, "income_statement": Y{num_images}, "cash_flow": Z{num_images}, "equity_statement": W{num_images}}}
]"""
    
    def classify_pages_with_vision_batch(self, page_images: List[Image.Image]) -> List[Dict[str, Any]]:
        """
        Classify pages using four-score vision-based system with BATCH processing (4-5 pages per API call)
        
        Args:
            page_images: List of PIL Image objects for each page
            
        Returns:
            List of financial pages with statement type and confidence scores
        """
        print(f"[INFO] Starting BATCH four-score vision classification on {len(page_images)} pages...")
        
        financial_pages = []
        page_count = len(page_images)
        batch_size = 5  # Send 5 pages per API call
        batches = []
        
        # Create batches of page images
        for i in range(0, page_count, batch_size):
            batch_pages = page_images[i:i + batch_size]
            batches.append((i, batch_pages))  # (start_index, page_images)
        
        print(f"[INFO] Processing {page_count} pages in {len(batches)} batches (batch size: {batch_size})")
        
        # Process batches sequentially (can be parallelized in Phase 3 if needed)
        for batch_idx, (start_idx, batch_images) in enumerate(batches):
            try:
                print(f"[INFO] Processing batch {batch_idx + 1}/{len(batches)} (pages {start_idx + 1}-{start_idx + len(batch_images)})")
                
                # Encode batch images
                encoded_images = []
                for img in batch_images:
                    base64_image = self.extractor.encode_image(img)
                    encoded_images.append({
                        'image': base64_image
                    })
                
                # Call batch API to classify all images in this batch
                batch_scores = self._classify_batch_four_scores(encoded_images)
                
                # Process scores for each page in batch
                for page_offset, scores in enumerate(batch_scores):
                    page_index = start_idx + page_offset
                    
                    # Determine if this page should be included (same logic as sequential)
                    max_score = max(scores['balance_sheet'], scores['income_statement'], scores['cash_flow'], scores['equity_statement'])
                    
                    if max_score >= 70:  # High confidence threshold
                        # Identify primary statement type
                        if scores['balance_sheet'] == max_score:
                            statement_type = "balance_sheet"
                        elif scores['income_statement'] == max_score:
                            statement_type = "income_statement"
                        elif scores['cash_flow'] == max_score:
                            statement_type = "cash_flow"
                        else:
                            statement_type = "equity_statement"
                        
                        financial_pages.append({
                            'page_num': page_index,
                            'statement_type': statement_type,
                            'scores': scores,
                            'confidence': max_score / 100,
                            'image': batch_images[page_offset]
                        })
                        
                        print(f"[INFO] Page {page_index + 1}: {statement_type} (BS:{scores['balance_sheet']}, IS:{scores['income_statement']}, CF:{scores['cash_flow']}, ES:{scores['equity_statement']})")
                    else:
                        print(f"[INFO] Page {page_index + 1}: Not financial (BS:{scores['balance_sheet']}, IS:{scores['income_statement']}, CF:{scores['cash_flow']}, ES:{scores['equity_statement']})")
                        
            except Exception as e:
                print(f"[ERROR] Error classifying batch {batch_idx + 1}: {e}")
                # Fallback: classify pages in batch individually
                print(f"[WARN] Falling back to individual classification for batch {batch_idx + 1}")
                for page_offset, img in enumerate(batch_images):
                    page_index = start_idx + page_offset
                    try:
                        base64_image = self.extractor.encode_image(img)
                        scores = self._classify_page_four_scores(base64_image)
                        
                        # Same logic to determine if page is financial
                        max_score = max(scores['balance_sheet'], scores['income_statement'], scores['cash_flow'], scores['equity_statement'])
                        
                        if max_score >= 70:
                            if scores['balance_sheet'] == max_score:
                                statement_type = "balance_sheet"
                            elif scores['income_statement'] == max_score:
                                statement_type = "income_statement"
                            elif scores['cash_flow'] == max_score:
                                statement_type = "cash_flow"
                            else:
                                statement_type = "equity_statement"
                            
                            financial_pages.append({
                                'page_num': page_index,
                                'statement_type': statement_type,
                                'scores': scores,
                                'confidence': max_score / 100,
                                'image': img
                            })
                    except Exception as e2:
                        print(f"[ERROR] Error classifying page {page_index + 1} in fallback: {e2}")
                        continue
        
        print(f"[INFO] BATCH four-score classification complete: {len(financial_pages)} financial pages identified")
        return financial_pages
    
    def _classify_batch_four_scores(self, encoded_images: List[Dict[str, str]]) -> List[Dict[str, int]]:
        """
        Classify a batch of pages and return scores for each
        
        Args:
            encoded_images: List of dicts with 'image' key containing base64-encoded images
            
        Returns:
            List of score dicts, one per image, each with balance_sheet, income_statement, cash_flow, equity_statement scores (0-100)
        """
        num_images = len(encoded_images)
        prompt = self._build_four_score_classification_prompt_batch(num_images)
        
        try:
            # Call batch API (extractor handles the API call with multiple images)
            result = self.extractor._call_anthropic_api_batch(encoded_images, prompt)
            
            # Debug: Show raw API response
            print(f"[DEBUG] Raw batch API response: '{result[:200]}...' (length: {len(result)})")
            
            if not result or result.strip() == "":
                print(f"[WARN] Empty batch API response")
                # Return default scores for all images
                return [{'balance_sheet': 0, 'income_statement': 0, 'cash_flow': 0, 'equity_statement': 0} for _ in range(num_images)]
            
            # Parse the JSON array response
            scores_list = json.loads(result)
            
            # Validate it's a list
            if not isinstance(scores_list, list):
                print(f"[WARN] Batch API response is not a list: {type(scores_list)}")
                # Try to extract if it's wrapped in an object
                if isinstance(scores_list, dict) and 'scores' in scores_list:
                    scores_list = scores_list['scores']
                else:
                    raise ValueError("Response is not a list of scores")
            
            # Validate we have the right number of scores
            if len(scores_list) != num_images:
                print(f"[WARN] Expected {num_images} scores, got {len(scores_list)}")
                # Pad or truncate as needed
                if len(scores_list) < num_images:
                    scores_list.extend([{'balance_sheet': 0, 'income_statement': 0, 'cash_flow': 0, 'equity_statement': 0}] * (num_images - len(scores_list)))
                else:
                    scores_list = scores_list[:num_images]
            
            # Validate and normalize scores
            for i, scores in enumerate(scores_list):
                for key in ['balance_sheet', 'income_statement', 'cash_flow', 'equity_statement']:
                    if key not in scores:
                        scores[key] = 0
                    else:
                        scores[key] = max(0, min(100, int(scores[key])))
            
            return scores_list
            
        except json.JSONDecodeError as e:
            print(f"[WARN] JSON decode error in batch classification: {e}")
            print(f"[WARN] Raw response: '{result[:500]}'")
            # Return default scores for all images
            return [{'balance_sheet': 0, 'income_statement': 0, 'cash_flow': 0, 'equity_statement': 0} for _ in range(num_images)]
        except Exception as e:
            print(f"[WARN] Failed to parse batch classification scores: {e}")
            print(f"[WARN] Raw response: '{result[:500] if 'result' in locals() else 'No response'}'")
            # Return default scores for all images
            return [{'balance_sheet': 0, 'income_statement': 0, 'cash_flow': 0, 'equity_statement': 0} for _ in range(num_images)]
    
    def _extract_years_from_financial_pages(self, page_images: List[Image.Image], financial_pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract years from identified financial pages (not hardcoded pages)
        
        Args:
            page_images: All page images
            financial_pages: List of identified financial pages with statement types
            
        Returns:
            Dict with years, confidence, and source
        """
        all_years = set()
        
        if not financial_pages:
            print("[WARN] No financial pages identified - cannot extract years")
            return {"years": [], "confidence": 0.0, "source": "vision_extraction"}
        
        try:
            # Extract years from first few financial pages (up to 3 pages to avoid too many API calls)
            pages_to_check = financial_pages[:3]
            
            for page_info in pages_to_check:
                page_num = page_info['page_num']
                statement_type = page_info['statement_type']
                
                print(f"[INFO] Extracting years from page {page_num + 1} ({statement_type})...")
                
                try:
                    # Skip if page image is None
                    if page_images[page_num] is None:
                        continue
                    # Convert PIL image to base64 for year extraction
                    base64_image = self.extractor.encode_image(page_images[page_num])
                    page_years = self.extractor.extract_years_from_image(base64_image)
                    if page_years.get('years'):
                        all_years.update(page_years['years'])
                        print(f"[INFO] Page {page_num + 1} years: {page_years['years']}")
                except Exception as e:
                    print(f"[WARN] Year extraction error: {e}")
                    continue
            
            # Sort years descending (most recent first) and convert to list
            years_list = sorted(list(all_years), reverse=True)
            
            if years_list:
                year_data = {
                    "years": years_list[:4],  # Limit to 4 years max
                    "confidence": 0.95,
                    "source": "financial_pages_vision_extraction"
                }
                print(f"[INFO] Complete year set extracted: {years_list} ({len(years_list)} years)")
                return year_data
            else:
                print(f"[WARN] No years extracted from financial pages")
                return {"years": [], "confidence": 0.0, "source": "vision_extraction"}
                
        except Exception as e:
            print(f"[WARN] Year extraction from financial pages failed: {e}")
            return {"years": [], "confidence": 0.0, "source": "vision_extraction"}

    def _build_simple_classification_prompt(self) -> str:
        """Build simple binary classification prompt (legacy method)"""
        return """
        Does this page contain financial tables with numbers?
        
        Look for:
        - Tables with financial data
        - Currency symbols (₱, $, €, £, ¥)
        - Year columns (2024, 2023, 2022, etc.)
        - Financial terminology
        
        Answer only: YES or NO
        """
    
    def _build_simple_extraction_prompt(self) -> str:
        """Build simple comprehensive extraction prompt"""
        return """
        Extract ALL financial data from this page.
        
        Look for:
        - Assets, Liabilities, Equity
        - Revenue, Expenses, Profit
        - Cash flows, Operating activities
        - Any financial line items with numbers
        
        Return JSON format:
        {
            "statement_type": "type of statement",
            "company_name": "company name",
            "period": "period/date",
            "currency": "currency",
            "years_detected": ["2024", "2023", "2022"],
            "line_items": {
                "category_name": {
                    "item_name": {"value": 1000000, "confidence": 0.9}
                }
            },
            "summary_metrics": {
                "total_assets": {"value": 1000000, "confidence": 0.9}
            }
        }
        
        Extract EVERY financial line item you can see clearly.
        """
    
    def _parse_classification_result(self, result: str, start_page: int, batch_size: int) -> List[int]:
        """Parse classification result to identify financial pages"""
        financial_pages = []
        
        # Simple parsing - look for financial classifications
        result_lower = result.lower()
        if any(keyword in result_lower for keyword in ["financial_balance_sheet", "financial_income", "financial_cash_flow", "financial_notes"]):
            # For now, assume the classified page is financial
            # TODO: Implement proper page-by-page parsing when multi-image batching is available
            financial_pages.append(start_page)
        
        return financial_pages
    
    def extract_from_financial_page_enhanced(self, page_image: str, statement_type_hint: str) -> Dict[str, Any]:
        """
        Extract financial data from a single identified financial statement page with enhanced prompt
        
        Args:
            page_image: Base64-encoded page image
            statement_type_hint: Hint for statement type
            
        Returns:
            Dict containing extracted financial data
        """
        try:
            # Use enhanced extraction prompt for financial pages
            enhanced_prompt = self._build_enhanced_financial_extraction_prompt(statement_type_hint)
            
            extracted_data = self.extractor._call_anthropic_api(page_image, enhanced_prompt)
            
            # Parse the JSON response
            try:
                parsed_data = json.loads(extracted_data)
                return parsed_data
            except json.JSONDecodeError:
                # If not JSON, return as text for now
                return {"raw_extraction": extracted_data}
                
        except Exception as e:
            return {"error": f"Financial page extraction failed: {str(e)}"}
    
    def _build_enhanced_financial_extraction_prompt(self, statement_type_hint: str) -> str:
        """Build enhanced prompt for financial statement extraction"""
        return f"""
        This is a scanned image of a financial statement page. Extract ALL visible financial line items with maximum detail.
        
        VISUAL ANALYSIS FOCUS:
        - Look for tabular data with row labels on the left and numerical values in columns
        - Identify multiple years of data across columns
        - Extract currency symbols and convert to numeric values
        - Handle parentheses as negative numbers: (26,278) = -26278
        - Process comma-separated numbers: 249,788,478 = 249788478
        
        EXTRACTION REQUIREMENTS:
        - Extract EVERY line item you can see clearly, even if formatting varies
        - Use the exact terminology from the document
        - Organize into logical categories based on the document's structure
        - Provide confidence scores for each extracted value
        
        REQUIRED JSON STRUCTURE:
        {{
            "statement_type": "exact statement title from document",
            "company_name": "extracted company name",
            "period": "extracted period/date", 
            "currency": "extracted currency (PHP, USD, etc.)",
            "years_detected": ["2024", "2023", "2022"],
            "base_year": "2024",
            "year_ordering": "most_recent_first",
            
            "line_items": {{
                "current_assets": {{
                    "cash_and_equivalents": {{"value": 1000000, "confidence": 0.95, "base_year": 1000000, "year_1": 950000}},
                    "accounts_receivable": {{"value": 500000, "confidence": 0.90, "base_year": 500000, "year_1": 480000}}
                }},
                "non_current_assets": {{
                    "property_plant_equipment": {{"value": 2000000, "confidence": 0.92, "base_year": 2000000, "year_1": 1900000}}
                }},
                "current_liabilities": {{
                    "accounts_payable": {{"value": 400000, "confidence": 0.88, "base_year": 400000, "year_1": 380000}}
                }},
                "equity": {{
                    "share_capital": {{"value": 1000000, "confidence": 0.95, "base_year": 1000000, "year_1": 1000000}},
                    "retained_earnings": {{"value": 800000, "confidence": 0.90, "base_year": 800000, "year_1": 750000}}
                }},
                "revenues": {{
                    "net_sales": {{"value": 5000000, "confidence": 0.95, "base_year": 5000000, "year_1": 4800000}}
                }},
                "operating_expenses": {{
                    "selling_expenses": {{"value": 500000, "confidence": 0.88, "base_year": 500000, "year_1": 480000}}
                }}
            }},
            
            "summary_metrics": {{
                "total_assets": {{"value": 3000000, "confidence": 0.95}},
                "total_liabilities": {{"value": 1200000, "confidence": 0.90}},
                "total_equity": {{"value": 1800000, "confidence": 0.92}},
                "total_revenue": {{"value": 5100000, "confidence": 0.95}},
                "net_income": {{"value": 1200000, "confidence": 0.93}}
            }}
        }}
        
        Focus on extracting as many line items as possible from this financial statement page.
        """
    
    def get_extraction_prompt_by_type(self, statement_type: str) -> str:
        """Get statement-specific extraction prompt"""
        if "balance_sheet" in statement_type.lower():
            return self._build_balance_sheet_extraction_prompt()
        elif "income" in statement_type.lower():
            return self._build_income_statement_extraction_prompt()
        elif "cash_flow" in statement_type.lower():
            return self._build_cash_flow_extraction_prompt()
        else:
            return self._build_enhanced_financial_extraction_prompt(statement_type)
    
    def _build_balance_sheet_extraction_prompt(self) -> str:
        """Build prompt specifically for Balance Sheet extraction"""
        return """
        This is a scanned Balance Sheet page. Extract ALL visible financial line items with focus on:
        
        BALANCE SHEET SPECIFIC TERMS:
        - Assets: "Cash and Cash Equivalents", "Accounts Receivable", "Inventory", "Property Plant Equipment"
        - Liabilities: "Accounts Payable", "Current Liabilities", "Long-term Debt", "Total Liabilities"
        - Equity: "Share Capital", "Retained Earnings", "Total Equity"
        
        Look for the fundamental equation: Assets = Liabilities + Equity
        
        Extract EVERY line item you can see, including:
        - Current Assets and Non-Current Assets
        - Current Liabilities and Non-Current Liabilities  
        - All Equity components
        - Total amounts for each section
        
        Return in the same JSON structure with appropriate categories.
        """
    
    def _build_income_statement_extraction_prompt(self) -> str:
        """Build prompt specifically for Income Statement extraction"""
        return """
        This is a scanned Income Statement page. Extract ALL visible financial line items with focus on:
        
        INCOME STATEMENT SPECIFIC TERMS:
        - Revenue: "Revenue", "Sales", "Net Sales", "Operating Revenue", "Total Revenue"
        - Cost of Sales: "Cost of Sales", "Cost of Goods Sold", "Direct Costs"
        - Operating Expenses: "Operating Expenses", "Selling Expenses", "Administrative Expenses", "General & Administrative"
        - Profit: "Gross Profit", "Operating Profit", "Net Income", "Profit After Tax", "Earnings"
        
        Look for the fundamental structure: Revenue - Expenses = Net Income
        
        Extract EVERY line item you can see, including:
        - All revenue sources
        - Cost of sales and operating expenses
        - Profit calculations at each level
        - Tax expenses and net income
        
        Return in the same JSON structure with appropriate categories.
        """
    
    def _build_cash_flow_extraction_prompt(self) -> str:
        """Build prompt specifically for Cash Flow Statement extraction"""
        return """
        This is a scanned Cash Flow Statement page. Extract ALL visible financial line items with focus on:
        
        CASH FLOW SPECIFIC TERMS:
        - Operating Activities: "Net Cash from Operations", "Operating Cash Flow", "Cash from Operating Activities"
        - Investing Activities: "Capital Expenditures", "Investments", "Cash from Investing Activities"
        - Financing Activities: "Dividends Paid", "Debt Repayment", "Cash from Financing Activities"
        - Net Change: "Net Increase in Cash", "Net Change in Cash", "Cash at Beginning/End"
        
        Look for the fundamental structure: Operating + Investing + Financing = Net Change in Cash
        
        Extract EVERY line item you can see, including:
        - All operating cash flows
        - All investing activities
        - All financing activities
        - Net cash changes and ending balances
        
        Return in the same JSON structure with appropriate categories.
        """
    
    def process_pdf_with_vector_db(self, pdf_file, enable_parallel: bool = True) -> Optional[Dict[str, Any]]:
        """
        Process PDF using comprehensive vector database approach.
        
        Args:
            pdf_file: PDF file (file-like object or bytes)
            enable_parallel: Whether to use parallel processing
            
        Returns:
            Dictionary containing extracted financial data
        """
        print("[DEBUG] process_pdf_with_vector_db called - using corrected version")
        try:
            # Ensure backends are detected (lazy initialization)
            self._ensure_backends()
            
            # Convert PDF to images and extract text
            images, page_info = self.convert_pdf_to_images(pdf_file, enable_parallel)
            if not images or not page_info:
                return None
            
            # VISION-ONLY CLASSIFICATION for scanned documents
            # Use PIL Image objects for vision classification
            page_images = []
            for page in page_info:
                if page['success'] and 'image' in page:
                    page_images.append(page['image'])  # Use PIL Image directly
            
            if not page_images:
                print("[ERROR] No images extracted from PDF - cannot process scanned document")
                return None
            
            # FOUR-SCORE VISION CLASSIFICATION: Identify financial pages with statement types (BATCH MODE)
            financial_pages = self.classify_pages_with_vision_batch(page_images)
            
            # ===== PHASE 3: Extract years from identified financial pages =====
            # For multi-year documents, years may appear on different pages
            # Example: Page 1 has [2022, 2021], Page 5 has [2021, 2020] = [2022, 2021, 2020]
            year_data = self._extract_years_from_financial_pages(page_images, financial_pages)
            # ==================================================
            
            print(f"[INFO] Four-score classification identified {len(financial_pages)} financial pages")
            
            if not financial_pages:
                print("[ERROR] No financial statement pages detected by vision classification.")
                print("   This indicates either:")
                print("   1. Document contains no financial statements")
                print("   2. Vision classification needs improvement")
                print("   3. Document format is not supported")
                return None
            
            # Process ALL identified financial pages (no arbitrary limit)
            max_pages_to_process = min(self.config.MAX_PAGES_TO_PROCESS, len(financial_pages))
            selected_pages = financial_pages[:max_pages_to_process]
            
            print(f"[INFO] Processing {len(selected_pages)} financial pages (max limit: {self.config.MAX_PAGES_TO_PROCESS})")
            
            # Process selected pages with PARALLEL statement-specific extraction
            # ⚡ OPTIMIZATION: Parallel extraction reduces 220s → ~30s (85% improvement)

            # Check if batch extraction is enabled (default: True for 8+ pages)
            enable_batch_extraction = len(selected_pages) >= 8  # Use batch for larger documents

            # Initialize results to avoid "local variable" error
            results = []

            if enable_batch_extraction:
                print(f"[INFO] Using BATCH extraction for {len(selected_pages)} pages")

                try:
                    # Batch extraction with cost control and error handling
                    batch_results = self.process_with_batch_extraction(selected_pages)
                    print("[INFO] Batch extraction completed successfully")

                    # Display cost summary for batch processing
                    self.display_cost_summary(batch_results)

                    # Batch processing returns a dict (combined results), not a list
                    # This is the correct format - it's already combined
                    if batch_results is not None and isinstance(batch_results, dict):
                        # Batch processing succeeded - return the combined results directly
                        # Add year data if needed (already done in process_with_batch_extraction)
                        return batch_results
                    elif batch_results is None:
                        print("[ERROR] Batch extraction returned None - complete failure")
                        print("[INFO] Falling back to sequential processing")
                        enable_batch_extraction = False
                    else:
                        print(f"[WARN] Batch extraction returned unexpected type: {type(batch_results)}")
                        print("[INFO] Falling back to sequential processing")
                        enable_batch_extraction = False

                except ImportError as e:
                    print(f"[WARN] Batch extraction module not available: {e}")
                    print("[INFO] Falling back to sequential processing")
                    enable_batch_extraction = False  # Trigger sequential fallback

                except Exception as e:
                    print(f"[ERROR] Batch extraction failed: {e}")
                    print("[INFO] Falling back to sequential processing")
                    enable_batch_extraction = False  # Trigger sequential fallback

            if not enable_batch_extraction:
                # Sequential processing fallback for small documents or when parallel fails
                print(f"[INFO] Using SEQUENTIAL extraction for {len(selected_pages)} pages")
                results = []
                for page in selected_pages:
                    try:
                        # Extract financial data from page using statement-specific prompt
                        base64_image = self.extractor.encode_image(page['image'])
                        statement_type = page['statement_type']

                        print(f"[INFO] Extracting from page {page['page_num'] + 1} ({statement_type})...")

                        # Use the existing extraction method for proper integration
                        extracted_data = self.extractor.extract_comprehensive_financial_data(
                            base64_image,
                            statement_type,
                            ""  # No text extraction needed for vision-based approach
                        )

                        if extracted_data and 'error' not in extracted_data:
                            # Debug: Show what was extracted from this page
                            template_mappings = extracted_data.get('template_mappings', {})
                            total_items = len(template_mappings)
                            print(f"[INFO] Page {page['page_num'] + 1}: Extracted {total_items} template mappings")
                            if total_items > 0:
                                print(f"   Sample fields: {list(template_mappings.keys())[:5]}")
                            else:
                                print(f"   [WARN] No template mappings found on this page")

                            results.append({
                                'page_num': page['page_num'],
                                'data': extracted_data,
                                'confidence': page['confidence']
                            })
                        else:
                            print(f"[ERROR] Failed to extract data from page {page['page_num'] + 1}")
                            continue

                    except Exception as e:
                        print(f"[ERROR] Error processing page {page['page_num'] + 1}: {str(e)}")
                        continue
            
            if not results:
                return None
            
            # Combine results from multiple pages
            combined_data = self._combine_page_results(results)
            
            # ===== PHASE 1: Add year data to combined results =====
            if year_data and year_data.get('years'):
                years = year_data['years']
                # Add Year field with all year values
                combined_data['template_mappings']['Year'] = {
                    'value': years[0] if years else None,
                    'confidence': year_data.get('confidence', 0.95),
                    'Value_Year_1': years[0] if len(years) > 0 else None,
                    'Value_Year_2': years[1] if len(years) > 1 else None,
                    'Value_Year_3': years[2] if len(years) > 2 else None,
                    'Value_Year_4': years[3] if len(years) > 3 else None,
                    'source': year_data.get('source', 'vision_extraction')
                }
                print(f"[INFO] Year field populated: {years}")
            else:
                print(f"[WARN] No year data to add to results")
            # ====================================================
            
            # Debug: Check what format we're returning
            print(f"[DEBUG] Returning combined_data with keys: {list(combined_data.keys())}")
            print(f"[DEBUG] Template mappings: {len(combined_data.get('template_mappings', {}))}")
            print(f"[DEBUG] Line items: {len(combined_data.get('line_items', {}))}")
            
            return combined_data
            
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    def _combine_page_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine results from multiple pages into a single result.
        Now handles template_mappings instead of line_items.
        
        Args:
            results: List of page results
            
        Returns:
            Combined financial data with template_mappings
        """
        if len(results) == 1:
            # Single result - return as is (should already be in template_mappings format)
            return results[0]['data']
        
        # Combine template_mappings from all pages
        combined_mappings = {}
        print(f"[DEBUG] convert_batch_results_to_standard_format: Processing {len(results)} results")
        
        for idx, result in enumerate(results):
            if 'data' not in result:
                print(f"[DEBUG] Result {idx} missing 'data' key: {result.keys()}")
                continue
            page_data = result['data']
            page_mappings = page_data.get('template_mappings', {})
            print(f"[DEBUG] Result {idx} (page {result.get('page_num', '?')}): {len(page_mappings)} template_mappings")
            
            # Merge mappings - handle multi-year data properly
            for field_name, mapping in page_mappings.items():
                if field_name not in combined_mappings:
                    combined_mappings[field_name] = mapping
                else:
                    existing = combined_mappings[field_name]
                    existing_year = str(existing.get('year', '')) if existing.get('year') else ''
                    new_year = str(mapping.get('year', '')) if mapping.get('year') else ''
                    
                    # Check if we already have Value_Year_X keys (multi-year format)
                    has_multi_year_format = any(key.startswith('Value_Year_') for key in existing.keys())
                    
                    # If different years, merge into Value_Year_X columns
                    if existing_year and new_year and existing_year != new_year:
                        # Get years_detected to determine column mapping
                        years_detected = []
                        if results:
                            first_data = results[0].get('data', {})
                            years_detected = first_data.get('years_detected', [])
                        
                        # If years_detected not available yet, infer from all results
                        if not years_detected:
                            all_years = set()
                            # Collect all years from all results processed so far
                            for r in results[:idx+1]:
                                if 'data' in r:
                                    for fname, fmap in r['data'].get('template_mappings', {}).items():
                                        if fmap.get('year'):
                                            all_years.add(str(fmap['year']))
                            # Also include current mapping
                            if new_year:
                                all_years.add(new_year)
                            if existing_year:
                                all_years.add(existing_year)
                            
                            if all_years:
                                years_detected = sorted([int(y) for y in all_years if str(y).isdigit()], reverse=True)
                                years_detected = [str(y) for y in years_detected]
                        
                        if years_detected:
                            # Sort years (most recent first)
                            years_detected = sorted([str(y) for y in years_detected], key=lambda x: int(x) if str(x).isdigit() else 0, reverse=True)
                            
                            # Start with existing data, preserving any Value_Year_X keys
                            merged = existing.copy()
                            
                            # Map existing year to column
                            if existing_year in years_detected:
                                year_index = years_detected.index(existing_year)
                                existing_value = existing.get('value')
                                if year_index == 0:
                                    merged['Value_Year_1'] = existing_value
                                    if not merged.get('value'):
                                        merged['value'] = existing_value
                                    if not merged.get('year'):
                                        merged['year'] = existing_year
                                elif year_index == 1:
                                    merged['Value_Year_2'] = existing_value
                                elif year_index == 2:
                                    merged['Value_Year_3'] = existing_value
                                elif year_index == 3:
                                    merged['Value_Year_4'] = existing_value
                            
                            # Map new year to column
                            if new_year in years_detected:
                                year_index = years_detected.index(new_year)
                                new_value = mapping.get('value')
                                if year_index == 0:
                                    merged['Value_Year_1'] = new_value
                                    merged['value'] = new_value  # Most recent year is the main value
                                    merged['year'] = new_year  # Most recent year
                                elif year_index == 1:
                                    merged['Value_Year_2'] = new_value
                                elif year_index == 2:
                                    merged['Value_Year_3'] = new_value
                                elif year_index == 3:
                                    merged['Value_Year_4'] = new_value
                            
                            # Use higher confidence
                            merged['confidence'] = max(existing.get('confidence', 0), mapping.get('confidence', 0))
                            
                            combined_mappings[field_name] = merged
                            print(f"[DEBUG] Merged multi-year data for '{field_name}': {existing_year}={existing.get('value')}, {new_year}={mapping.get('value')}")
                        else:
                            # No years_detected - fallback to keeping higher confidence
                            existing_confidence = existing.get('confidence', 0)
                            new_confidence = mapping.get('confidence', 0)
                            if new_confidence > existing_confidence:
                                combined_mappings[field_name] = mapping
                    elif has_multi_year_format:
                        # Existing already has Value_Year_X format - merge new year if it's different
                        # Get years_detected first to understand year-to-column mapping
                        years_detected = []
                        if results:
                            first_data = results[0].get('data', {})
                            years_detected = first_data.get('years_detected', [])
                        
                        # If years_detected not available, infer from all results
                        if not years_detected:
                            all_years = set()
                            # Collect all years from all results processed so far
                            for r in results[:idx+1]:
                                if 'data' in r:
                                    for fname, fmap in r['data'].get('template_mappings', {}).items():
                                        if fmap.get('year'):
                                            all_years.add(str(fmap['year']))
                            # Include existing year and new year
                            if existing.get('year'):
                                all_years.add(str(existing.get('year')))
                            if new_year:
                                all_years.add(new_year)
                            
                            if all_years:
                                years_detected = sorted([int(y) for y in all_years if str(y).isdigit()], reverse=True)
                                years_detected = [str(y) for y in years_detected]
                        
                        # Check which years are already represented in Value_Year_X columns
                        existing_years = set()
                        if years_detected:
                            for i in range(1, 5):
                                year_key = f'Value_Year_{i}'
                                if year_key in existing and existing[year_key] is not None and existing[year_key] != '':
                                    # Use years_detected to map column index to year
                                    if i <= len(years_detected):
                                        existing_years.add(str(years_detected[i-1]))
                        
                        # Also check the year field
                        if existing.get('year'):
                            existing_years.add(str(existing.get('year')))
                        
                        if new_year and new_year not in existing_years:
                            # Try to add new year to existing multi-year format
                            # years_detected already computed above
                            if years_detected and new_year in years_detected:
                                year_index = years_detected.index(new_year)
                                new_value = mapping.get('value')
                                merged = existing.copy()
                                if year_index == 0:
                                    merged['Value_Year_1'] = new_value
                                    merged['value'] = new_value
                                    merged['year'] = new_year
                                elif year_index == 1:
                                    merged['Value_Year_2'] = new_value
                                elif year_index == 2:
                                    merged['Value_Year_3'] = new_value
                                elif year_index == 3:
                                    merged['Value_Year_4'] = new_value
                                merged['confidence'] = max(existing.get('confidence', 0), mapping.get('confidence', 0))
                                combined_mappings[field_name] = merged
                                print(f"[DEBUG] Added year {new_year} to existing multi-year '{field_name}' at Value_Year_{year_index + 1}")
                            else:
                                # Can't determine year position - keep existing
                                pass
                        else:
                            # Same year or no year - keep higher confidence
                            existing_confidence = existing.get('confidence', 0)
                            new_confidence = mapping.get('confidence', 0)
                            if new_confidence > existing_confidence:
                                combined_mappings[field_name] = mapping
                    else:
                        # Same year or no year info - keep higher confidence value
                        existing_confidence = existing.get('confidence', 0)
                        new_confidence = mapping.get('confidence', 0)
                        if new_confidence > existing_confidence:
                            combined_mappings[field_name] = mapping
        
        # Use metadata from the first result
        combined_data = {
            'template_mappings': combined_mappings,
            'company_name': '',
            'period': '',
            'currency': '',
            'years_detected': [],
            'base_year': '',
            'year_ordering': '',
            'document_structure': {},
            'notes': '',
            'processing_method': 'multi_page_vector_database',
            'ai_provider': 'anthropic',
            'timestamp': '',
            'pages_processed': len(results)
        }
        
        if results:
            first_data = results[0]['data']
            combined_data['company_name'] = first_data.get('company_name', '')
            combined_data['period'] = first_data.get('period', '')
            combined_data['currency'] = first_data.get('currency', '')
            combined_data['years_detected'] = first_data.get('years_detected', [])
            combined_data['base_year'] = first_data.get('base_year', '')
            combined_data['year_ordering'] = first_data.get('year_ordering', '')
            combined_data['document_structure'] = first_data.get('document_structure', {})
            combined_data['notes'] = first_data.get('notes', '')
            combined_data['ai_provider'] = first_data.get('ai_provider', 'anthropic')
            combined_data['timestamp'] = first_data.get('timestamp', '')
        
        return combined_data


    def process_with_batch_extraction(self, selected_pages: list) -> Dict[str, Any]:
        """
        Process pages using batch extraction instead of parallel processing.
        
        Returns:
            Dict with 'template_mappings' key containing combined field mappings
            and 'pages_processed' key with count of pages processed.
        """

        print(f"[INFO] Using BATCH extraction for {len(selected_pages)} pages")

        # Initialize year_data to empty in case extraction fails
        year_data = {"years": [], "confidence": 0.0, "source": "vision_extraction"}

        try:
            # Phase 0: Extract years from financial pages (before batch processing)
            # Build page_images list indexed by page_num for _extract_years_from_financial_pages
            # Find max page_num to size the array correctly
            max_page_num = max((page.get('page_num', 0) for page in selected_pages), default=0)
            page_images = [None] * (max_page_num + 1)
            
            for page in selected_pages:
                page_num = page.get('page_num', 0)
                if 'image' in page:
                    page_images[page_num] = page['image']
            
            # Extract years from identified financial pages
            print("[INFO] Extracting years from financial pages...")
            year_data = self._extract_years_from_financial_pages(page_images, selected_pages)
            
            # Phase 1: Analyze document structure
            from .batch_processor import DocumentStructureAnalyzer, BatchExtractor

            structure_analyzer = DocumentStructureAnalyzer()
            statement_groups = structure_analyzer.analyze_document_structure(selected_pages)
            
            # Load template fields for batch prompt (fixes root cause)
            template_fields = self.extractor._load_template_fields()
            processing_batches = structure_analyzer.create_processing_batches(statement_groups, template_fields=template_fields)

            print(f"[INFO] Created {len(processing_batches)} processing batches")

            # Phase 2: Process batches sequentially
            batch_extractor = BatchExtractor(self.extractor)
            all_results = []
            
            # Collect all unique field names for analysis (no normalization needed - prompt fixed)
            all_field_names = set()

            for i, batch in enumerate(processing_batches):
                print(f"[BATCH] Processing batch {i+1}/{len(processing_batches)}: {batch['batch_id']}")

                batch_result = batch_extractor.extract_batch(batch)
                if batch_result and batch_result.get('extracted_data'):
                    # Convert batch result format to expected format
                    batch_extracted_data = batch_result['extracted_data']
                    statement_type = batch_result.get('statement_type', 'unknown')
                    print(f"[DEBUG] Batch {batch['batch_id']}: Got {len(batch_extracted_data)} extracted items")
                    
                    # Group extracted items by page_num
                    pages_data = {}
                    for item in batch_extracted_data:
                        page_num = item.get('page_num', 0)
                        if page_num not in pages_data:
                            pages_data[page_num] = {
                                'template_mappings': {}
                            }
                        
                        # Convert item to template_mapping format (no normalization - prompt fixed)
                        field_name = item.get('field_name', '')
                        if field_name:
                            # Collect field name for analysis
                            all_field_names.add(field_name)
                            
                            # Use field name directly from batch extraction (LLM should return exact template field names)
                            value = item.get('value', '')
                            year = item.get('year', 'N/A')
                            confidence = item.get('confidence', 0.0)
                            
                            print(f"[FIELD_MAP] Page {page_num}: '{field_name}' = {value} (Year: {year}, Confidence: {confidence:.2f})")
                            
                            # Use field name directly (should already be template field name from improved prompt)
                            pages_data[page_num]['template_mappings'][field_name] = {
                                'value': value,
                                'confidence': confidence,
                                'year': year,
                                'page_num': page_num
                            }
                        else:
                            print(f"[WARN] Item missing 'field_name' on page {page_num}: {list(item.keys())}")
                    
                    print(f"[DEBUG] Batch {batch['batch_id']}: Grouped into {len(pages_data)} pages with template_mappings")
                    
                    # Convert to expected format for convert_batch_results_to_standard_format
                    for page_num, page_data in pages_data.items():
                        all_results.append({
                            'page_num': page_num,
                            'statement_type': statement_type,
                            'data': page_data
                        })
                    
                    print(f"[DEBUG] Batch {batch['batch_id']}: Added {len(pages_data)} results to all_results (total: {len(all_results)})")

                # Cost monitoring
                total_cost = batch_extractor.total_cost
                if total_cost > 2.0:  # Cost threshold
                    print(f"[WARN] Cost threshold reached: ${total_cost:.2f}")
                    break

            # Phase 3: Structure results for existing pipeline
            print(f"[DEBUG] Total all_results before conversion: {len(all_results)}")
            
            # Log all unique field names found for mapping analysis
            if all_field_names:
                print(f"\n[FIELD_MAP] ========================================")
                print(f"[FIELD_MAP] FIELD NAME MAPPING ANALYSIS")
                print(f"[FIELD_MAP] ========================================")
                print(f"[FIELD_MAP] Total unique field names extracted: {len(all_field_names)}")
                print(f"[FIELD_MAP] Field names (sorted):")
                for field_name in sorted(all_field_names):
                    print(f"[FIELD_MAP]   - '{field_name}'")
                print(f"[FIELD_MAP] ========================================\n")
            
            if all_results:
                print(f"[DEBUG] First result structure: {list(all_results[0].keys()) if isinstance(all_results[0], dict) else type(all_results[0])}")
                if isinstance(all_results[0], dict) and 'data' in all_results[0]:
                    print(f"[DEBUG] First result data keys: {list(all_results[0]['data'].keys())}")
                    if 'template_mappings' in all_results[0]['data']:
                        print(f"[DEBUG] First result template_mappings count: {len(all_results[0]['data']['template_mappings'])}")
            
            # Use _combine_page_results() to combine into single dict with template_mappings
            converted_results = self._combine_page_results(all_results)
            print(f"[DEBUG] Conversion complete - return type: {type(converted_results)}")
            print(f"[DEBUG] Conversion complete - return keys: {list(converted_results.keys()) if isinstance(converted_results, dict) else 'Not a dict'}")
            if isinstance(converted_results, dict) and 'template_mappings' in converted_results:
                print(f"[DEBUG] Conversion complete - template_mappings count: {len(converted_results['template_mappings'])}")
            
            # Add year data to combined results (matching process_pdf_with_vector_db behavior)
            if isinstance(converted_results, dict) and year_data and year_data.get('years'):
                years = year_data['years']
                # Ensure template_mappings exists
                if 'template_mappings' not in converted_results:
                    converted_results['template_mappings'] = {}
                # Add Year field with all year values
                converted_results['template_mappings']['Year'] = {
                    'value': years[0] if years else None,
                    'confidence': year_data.get('confidence', 0.95),
                    'Value_Year_1': years[0] if len(years) > 0 else None,
                    'Value_Year_2': years[1] if len(years) > 1 else None,
                    'Value_Year_3': years[2] if len(years) > 2 else None,
                    'Value_Year_4': years[3] if len(years) > 3 else None,
                    'source': year_data.get('source', 'vision_extraction')
                }
                print(f"[INFO] Year field populated: {years}")
            elif isinstance(converted_results, dict):
                print(f"[WARN] No year data to add to results (year_data: {year_data})")
            
            # Add cost metadata to return value (Phase 2: Cost Tracking)
            if isinstance(converted_results, dict):
                # Capture cost information from batch_extractor
                total_cost = batch_extractor.total_cost if 'batch_extractor' in locals() else 0.0
                total_batches = len(processing_batches) if 'processing_batches' in locals() else 0
                total_pages = len(selected_pages)
                
                converted_results['batch_processing_metadata'] = {
                    'total_batches': total_batches,
                    'total_pages': total_pages,
                    'total_cost': total_cost,
                    'cost_per_page': total_cost / total_pages if total_pages > 0 else 0.0,
                    'api_calls': total_batches,  # Each batch is one API call
                    'processing_method': 'batch_extraction'
                }
                print(f"[INFO] Cost metadata added: ${total_cost:.2f} for {total_batches} batches, {total_pages} pages")
            
            return converted_results

        except Exception as e:
            # Sanitize error message for Windows console encoding
            error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
            print(f"[ERROR] Batch extraction failed: {error_msg}")
            print("[INFO] Falling back to sequential processing")
            return self.process_pages_sequentially(selected_pages)

    def display_cost_summary(self, batch_results):
        """Display cost summary for batch processing - handles both dict and list formats"""
        try:
            total_cost = 0
            total_pages = 0
            total_batches = 0

            # Handle new dict format (from _combine_page_results)
            if isinstance(batch_results, dict):
                # Check for batch_processing_metadata in the dict
                metadata = batch_results.get('batch_processing_metadata', {})
                if metadata:
                    total_cost = metadata.get('total_cost', 0)
                    total_pages = metadata.get('total_pages', batch_results.get('pages_processed', 0))
                    total_batches = metadata.get('total_batches', 0)
                else:
                    # Fallback: try to get pages_processed from dict
                    total_pages = batch_results.get('pages_processed', 0)
                    print(f"[WARN] Cost metadata not found in batch results, showing page count only")
            
            # Handle legacy list format
            elif isinstance(batch_results, list):
                for result in batch_results:
                    if isinstance(result, dict) and 'processing_metadata' in result:
                        metadata = result['processing_metadata']
                        cost = metadata.get('cost', 0)
                        pages = metadata.get('pages_processed', [])
                        total_cost += cost
                        total_pages += len(pages)
                        total_batches += 1

            print(f"\n[COST SUMMARY]")
            print(f"[COST SUMMARY] Batch Processing Results:")
            print(f"   • Total batches: {total_batches}")
            print(f"   • Total pages: {total_pages}")
            print(f"   • Total cost: ${total_cost:.2f}")
            if total_pages > 0:
                print(f"   • Cost per page: ${total_cost/total_pages:.3f}")
                individual_cost = total_pages * 0.15
                savings = individual_cost - total_cost
                print(f"   • Estimated savings vs individual: ${savings:.2f}")
            print()

        except Exception as e:
            print(f"[WARN] Failed to display cost summary: {e}")

    def convert_batch_results_to_standard_format(self, batch_results: list) -> list:
        """Convert batch results to match existing pipeline format"""
        standard_results = []

        for result in batch_results:
            # Ensure compatibility with existing result processing
            standard_result = {
                'page_num': result.get('page_num', 0),
                'extracted_data': result.get('extracted_data', {}),
                'confidence': result.get('confidence', 0.0),
                'statement_type': result.get('statement_type', 'unknown'),
                'batch_processed': True  # Flag to indicate batch processing
            }
            standard_results.append(standard_result)

        return standard_results

    def process_pages_sequentially(self, selected_pages: list) -> list:
        """Fallback sequential processing for small documents or when batch fails"""
        print(f"[INFO] 📄 Using sequential extraction for {len(selected_pages)} pages")
        
        # Extract years from financial pages before processing
        max_page_num = max((page.get('page_num', 0) for page in selected_pages), default=0)
        page_images = [None] * (max_page_num + 1)
        for page in selected_pages:
            page_num = page.get('page_num', 0)
            if 'image' in page:
                page_images[page_num] = page['image']
        
        print("[INFO] Extracting years from financial pages...")
        year_data = self._extract_years_from_financial_pages(page_images, selected_pages)
        
        results = []

        for i, page in enumerate(selected_pages):
            try:
                print(f"[INFO] Processing page {i+1}/{len(selected_pages)}: {page.get('page_num', '?')}")

                # Extract from single page
                page_num = page.get('page_num', i + 1)
                image_data = page.get('image', '')

                if not image_data:
                    print(f"[WARN] No image data for page {page_num}")
                    continue

                # Use existing single-page extraction
                extracted_data = self.extractor.extract_financial_data(image_data)

                results.append({
                    'page_num': page_num,
                    'extracted_data': extracted_data,
                    'confidence': 0.8,  # Default confidence
                    'statement_type': 'sequential',
                    'batch_processed': False
                })

            except Exception as e:
                print(f"[ERROR] Failed to process page {page.get('page_num', '?')}: {e}")
                continue

        return results
