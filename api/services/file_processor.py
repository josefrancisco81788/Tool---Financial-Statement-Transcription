import os
import sys
import base64
import time
from typing import Dict, Any, List
import io
from PIL import Image
from openai import OpenAI

# Add the parent directory to the path to import from streamlit app
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
try:
    import app
    convert_pdf_to_images = app.convert_pdf_to_images
    extract_comprehensive_financial_data = app.extract_comprehensive_financial_data
    create_ifrs_csv_export = app.create_ifrs_csv_export
    consolidate_financial_data = app.consolidate_financial_data
    analyze_document_characteristics = app.analyze_document_characteristics
    process_pdf_with_whole_document_context = app.process_pdf_with_whole_document_context
    process_pdf_with_vector_db = app.process_pdf_with_vector_db
    transform_to_analysis_ready_format = app.transform_to_analysis_ready_format
    ensure_confidence_score = app.ensure_confidence_score
except ImportError:
    # Fallback: try importing from streamlit app
    try:
        from streamlit.app import (
            convert_pdf_to_images,
            extract_comprehensive_financial_data,
            create_ifrs_csv_export,
            consolidate_financial_data,
            analyze_document_characteristics,
            process_pdf_with_whole_document_context,
            process_pdf_with_vector_db,
            transform_to_analysis_ready_format,
            ensure_confidence_score
        )
    except ImportError:
        raise ImportError("Could not import required functions from app.py or streamlit.app")

class FileProcessor:
    """Handles file processing and financial data extraction"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        if not self.client.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
    
    async def process_file_sync(
        self, 
        file_content: bytes, 
        filename: str, 
        processing_approach: str = "auto",
        output_format: str = "csv"
    ) -> Dict[str, Any]:
        """Process file synchronously (for small files)"""
        start_time = time.time()
        try:
            # Validate file type
            file_extension = os.path.splitext(filename)[1].lower()
            if file_extension not in ['.pdf', '.jpg', '.jpeg', '.png']:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Preserve what the client requested
            requested_processing_approach = processing_approach
            # Normalize
            processing_approach = str(processing_approach or "auto").strip().lower()
            
            # Analyze document characteristics
            file_obj = io.BytesIO(file_content)
            file_obj.name = filename  # Mock filename for analysis
            characteristics = analyze_document_characteristics(file_obj)
            
            # Determine processing approach only if auto is selected
            if processing_approach == "auto":
                recommendation = characteristics.get("recommendation", "whole_document")
                processing_approach = str(recommendation)
            # If user explicitly chooses an approach, respect that choice
            
            # Process based on file type
            if file_extension == '.pdf':
                result = await self._process_pdf_sync(file_content, processing_approach)
            else:
                result = await self._process_image_sync(file_content, filename)
            
            # Format output
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            # Expose both requested and effective approaches
            result["requested_processing_approach"] = requested_processing_approach
            result["effective_processing_approach"] = processing_approach
            # Back-compat: keep processing_approach as the effective one
            result["processing_approach"] = processing_approach
            result["document_characteristics"] = characteristics
            
            return self._format_output(result, output_format)
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed",
                "processing_time": time.time() - start_time
            }
    
    async def process_file_async(
        self, 
        job_id: str, 
        file_content: bytes, 
        filename: str, 
        processing_approach: str = "auto",
        output_format: str = "csv"
    ) -> None:
        """Process file asynchronously (for large files)"""
        # This would integrate with Celery for background processing
        # For now, we'll process synchronously but in a separate thread
        import threading
        
        def process():
            try:
                result = self.process_file_sync(file_content, filename, processing_approach, output_format)
                # Update job status (this would be done through the job manager)
                print(f"Job {job_id} completed: {result}")
            except Exception as e:
                print(f"Job {job_id} failed: {str(e)}")
        
        thread = threading.Thread(target=process)
        thread.start()
    
    async def _process_pdf_sync(self, file_content: bytes, processing_approach: str) -> Dict[str, Any]:
        """Process PDF file synchronously"""
        try:
            # Create file-like object for processing
            pdf_file = io.BytesIO(file_content)
            pdf_file.name = "uploaded_file.pdf"  # Mock filename
            
            # Process based on approach
            if processing_approach == "whole_document":
                # Use the whole document context approach (same as Streamlit)
                consolidated_data = process_pdf_with_whole_document_context(pdf_file, self.client)
                pages_processed = "all"  # Whole document processes all pages
            elif processing_approach == "vector_database":
                # Use vector database approach
                consolidated_data = process_pdf_with_vector_db(pdf_file, self.client)
                pages_processed = "all"  # Vector approach processes all pages
            else:
                # Fallback to image-based processing
                images = convert_pdf_to_images(pdf_file)
                
                if not images:
                    raise ValueError("Failed to convert PDF to images")
                
                # Process images
                extracted_results = []
                for i, image in enumerate(images):
                    try:
                        # Ensure image is a PIL Image object
                        if hasattr(image, 'save'):
                            # Convert PIL image to base64
                            img_buffer = io.BytesIO()
                            image.save(img_buffer, format='PNG')
                            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                        else:
                            # If it's not a PIL Image, try to convert it
                            if isinstance(image, bytes):
                                img_base64 = base64.b64encode(image).decode('utf-8')
                            else:
                                # Try to convert to PIL Image
                                pil_image = Image.open(io.BytesIO(image))
                                img_buffer = io.BytesIO()
                                pil_image.save(img_buffer, format='PNG')
                                img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                        
                        # Extract financial data
                        result = extract_comprehensive_financial_data(
                            img_base64, 
                            f"page_{i+1}", 
                            ""
                        )
                        if result:
                            extracted_results.append(result)
                            
                    except Exception as page_error:
                        print(f"Warning: Failed to process page {i+1}: {str(page_error)}")
                        continue
                
                # Consolidate results
                if len(extracted_results) > 1:
                    consolidated_data = consolidate_financial_data(extracted_results)
                else:
                    consolidated_data = extracted_results[0] if extracted_results else {}
                
                pages_processed = len(images)
            
            return {
                "status": "success",
                "data": consolidated_data,
                "pages_processed": pages_processed,
                "extraction_method": processing_approach
            }
            
        except Exception as e:
            raise Exception(f"PDF processing failed: {str(e)}")
    
    async def _process_image_sync(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process image file synchronously"""
        try:
            # Convert to base64
            img_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # Extract financial data
            result = extract_comprehensive_financial_data(
                img_base64, 
                "image", 
                ""
            )
            
            return {
                "status": "success",
                "data": result,
                "pages_processed": 1,
                "extraction_method": "image_processing"
            }
            
        except Exception as e:
            raise Exception(f"Image processing failed: {str(e)}")
    
    def _format_output(self, result: Dict[str, Any], output_format: str) -> Dict[str, Any]:
        """Format the output based on requested format"""
        if result.get("status") != "success":
            return result
        
        data = result.get("data", {})
        
        if output_format == "csv":
            csv_data = self._transform_data_for_csv(data)
            return {
                **result,
                "csv_data": csv_data,
                "output_format": "csv"
            }
        elif output_format == "json":
            return {
                **result,
                "json_data": data,
                "output_format": "json"
            }
        elif output_format == "both":
            csv_data = self._transform_data_for_csv(data)
            return {
                **result,
                "csv_data": csv_data,
                "json_data": data,
                "output_format": "both"
            }
        else:
            return result
    
    def validate_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Validate uploaded file"""
        errors = []
        
        # Check file size
        if len(file_content) > 10 * 1024 * 1024:  # 10MB
            errors.append("File size exceeds 10MB limit")
        
        # Check file type
        file_extension = os.path.splitext(filename)[1].lower()
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        if file_extension not in allowed_extensions:
            errors.append(f"File type {file_extension} not supported. Allowed: {', '.join(allowed_extensions)}")
        
        # Check if file is empty
        if len(file_content) == 0:
            errors.append("File is empty")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "file_size": len(file_content),
            "file_type": file_extension
        }
    
    def _transform_data_for_csv(self, data: Dict[str, Any]) -> str:
        """Transform raw data into CSV format with year mapping row"""
        try:
            # Use the working transform_to_analysis_ready_format first
            csv_data = transform_to_analysis_ready_format(data)
            
            # Add year mapping row after the header
            lines = csv_data.split('\r\n')
            if len(lines) < 2:
                return csv_data
            
            # Extract years from the data
            years_detected = data.get("years_detected", [])
            if not years_detected:
                return csv_data
            
            # Sort years (most recent first)
            try:
                sorted_years = sorted(years_detected, key=lambda x: int(x) if str(x).isdigit() else float('inf'), reverse=True)
            except:
                sorted_years = sorted(years_detected, reverse=True)
            
            # Create year mapping row
            year_mapping_row = ["Date", "Year", "Year", "", "0.0"]
            for i in range(4):  # Support up to 4 years
                if i < len(sorted_years):
                    year_mapping_row.append(str(sorted_years[i]))
                else:
                    year_mapping_row.append("")
            
            # Insert year mapping row after header
            header_row = lines[0]
            data_rows = lines[1:]
            
            # Reconstruct CSV with year mapping row
            result_lines = [header_row, ','.join(year_mapping_row)] + data_rows
            
            return '\r\n'.join(result_lines)
            
        except Exception as e:
            print(f"❌ [DEBUG] Error adding year mapping row: {str(e)}")
            # Fall back to original working format
            return transform_to_analysis_ready_format(data) 