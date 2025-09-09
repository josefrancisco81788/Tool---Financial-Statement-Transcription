"""
PDF processing module for converting PDFs to images and extracting text.
Copied exactly from alpha-testing-v1 for optimal performance.
"""

import io
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
                print("✅ Using PyMuPDF for PDF processing (reliable)")
            elif self._backends["pdf2image"]:
                self.pdf_library = "pdf2image"
                self.pdf_processing_available = True
                print("✅ Using pdf2image for PDF processing (optimal performance)")
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
                images = self._with_timeout(_convert_with_pdf2image, timeout=30)
                
            elif self.pdf_library == "pymupdf":
                def _convert_with_pymupdf():
                    import fitz
                    doc = fitz.Document(stream=pdf_data, filetype="pdf")
                    images = []
                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        pix = page.get_pixmap(matrix=fitz.Matrix(200/72, 200/72))  # 200 DPI
                        img_data = pix.tobytes("png")
                        images.append(Image.open(io.BytesIO(img_data)))
                    doc.close()
                    return images
                images = self._with_timeout(_convert_with_pymupdf, timeout=30)
                
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
            
            response = self.extractor.exponential_backoff_retry(
                lambda: self.extractor.client.chat.completions.create(
                    model=self.config.OPENAI_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=2000
                )
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            raise Exception(f"Error extracting text from page {page_num}: {str(e)}")
    
    def classify_financial_statement_pages(self, page_info: List[Dict[str, Any]], enable_parallel: bool = True) -> List[Dict[str, Any]]:
        """
        Classify pages to identify financial statement content.
        
        Args:
            page_info: List of page info dictionaries
            enable_parallel: Whether to use parallel processing
            
        Returns:
            List of financial statement pages
        """
        financial_pages = []
        
        for page in page_info:
            if not page['success']:
                continue
            
            # Calculate number density score
            text = page['text']
            numbers = [word for word in text.split() if word.replace(',', '').replace('.', '').replace('-', '').isdigit()]
            number_density = len(numbers) / max(len(text.split()), 1)
            
            # Financial statement patterns
            financial_patterns = [
                'balance sheet', 'income statement', 'cash flow', 'statement of financial position',
                'assets', 'liabilities', 'equity', 'revenue', 'expenses', 'profit', 'loss',
                'current assets', 'non-current assets', 'current liabilities', 'non-current liabilities',
                'share capital', 'retained earnings', 'total assets', 'total liabilities',
                'net income', 'gross profit', 'operating income', 'ebitda'
            ]
            
            # Check for financial patterns
            pattern_matches = sum(1 for pattern in financial_patterns if pattern in text)
            confidence = min(0.9, (pattern_matches * 0.1) + (number_density * 0.5))
            
            if confidence > 0.3:  # Threshold for financial content
                financial_pages.append({
                    'page_num': page['page_num'],
                    'statement_type': 'Financial Statement',
                    'confidence': confidence,
                    'image': page['image'],
                    'text': page['text'],
                    'number_density': number_density,
                    'financial_numbers_count': len(numbers),
                    'number_density_score': number_density
                })
        
        # Sort by confidence
        financial_pages.sort(key=lambda x: x['confidence'], reverse=True)
        
        return financial_pages
    
    def process_pdf_with_vector_db(self, pdf_file, enable_parallel: bool = True) -> Optional[Dict[str, Any]]:
        """
        Process PDF using comprehensive vector database approach.
        
        Args:
            pdf_file: PDF file (file-like object or bytes)
            enable_parallel: Whether to use parallel processing
            
        Returns:
            Dictionary containing extracted financial data
        """
        try:
            # Ensure backends are detected (lazy initialization)
            self._ensure_backends()
            
            # Convert PDF to images and extract text
            images, page_info = self.convert_pdf_to_images(pdf_file, enable_parallel)
            if not images or not page_info:
                return None
            
            # Classify financial statement pages
            financial_pages = self.classify_financial_statement_pages(page_info, enable_parallel)
            
            if not financial_pages:
                # Fallback: process first page
                financial_pages = [{
                    'page_num': 1,
                    'statement_type': 'Unknown',
                    'confidence': 0.1,
                    'image': images[0],
                    'text': page_info[0]['text'] if page_info else "",
                    'number_density': 0,
                    'financial_numbers_count': 0,
                    'number_density_score': 0
                }]
            
            # Select top pages for processing
            max_pages_to_process = min(self.config.MAX_PAGES_TO_PROCESS, len(financial_pages))
            selected_pages = financial_pages[:max_pages_to_process]
            
            # Process selected pages
            results = []
            for page in selected_pages:
                try:
                    # Extract financial data from page
                    base64_image = self.extractor.encode_image(page['image'])
                    extracted_data = self.extractor.extract_comprehensive_financial_data(
                        base64_image, 
                        page['statement_type'], 
                        page['text']
                    )
                    
                    results.append({
                        'page_num': page['page_num'],
                        'data': extracted_data,
                        'confidence': page['confidence']
                    })
                    
                except Exception as e:
                    print(f"Error processing page {page['page_num']}: {str(e)}")
                    continue
            
            if not results:
                return None
            
            # Combine results from multiple pages
            combined_data = self._combine_page_results(results)
            
            return combined_data
            
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    def _combine_page_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine results from multiple pages into a single result.
        
        Args:
            results: List of page results
            
        Returns:
            Combined financial data
        """
        if len(results) == 1:
            return results[0]['data']
        
        # For multiple pages, use the highest confidence result as base
        best_result = max(results, key=lambda x: x['confidence'])
        combined_data = best_result['data'].copy()
        
        # Add metadata about multiple pages
        combined_data['pages_processed'] = len(results)
        combined_data['processing_method'] = 'multi_page_vector_database'
        
        return combined_data
