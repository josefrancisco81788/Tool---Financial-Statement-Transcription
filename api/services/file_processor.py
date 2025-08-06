import os
import sys
import base64
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
import io
from PIL import Image
import fitz  # PyMuPDF
import pandas as pd
from openai import OpenAI

# Add the parent directory to the path to import from streamlit app
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from streamlit.app import (
    convert_pdf_to_images,
    extract_comprehensive_financial_data,
    create_ifrs_csv_export,
    consolidate_financial_data,
    analyze_document_characteristics
)

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
        try:
            start_time = time.time()
            
            # Validate file type
            file_extension = os.path.splitext(filename)[1].lower()
            if file_extension not in ['.pdf', '.jpg', '.jpeg', '.png']:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Analyze document characteristics
            file_obj = io.BytesIO(file_content)
            file_obj.name = filename  # Mock filename for analysis
            characteristics = analyze_document_characteristics(file_obj)
            
            # Determine processing approach
            if processing_approach == "auto":
                processing_approach = characteristics.get("recommendation", "whole_document")
            
            # Process based on file type
            if file_extension == '.pdf':
                result = await self._process_pdf_sync(file_content, processing_approach)
            else:
                result = await self._process_image_sync(file_content, filename)
            
            # Format output
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            result["processing_approach"] = processing_approach
            result["document_characteristics"] = characteristics
            
            return self._format_output(result, output_format)
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed",
                "processing_time": time.time() - start_time if 'start_time' in locals() else 0
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
            # Convert PDF to images
            pdf_file = io.BytesIO(file_content)
            images = convert_pdf_to_images(pdf_file)
            
            if not images:
                raise ValueError("Failed to convert PDF to images")
            
            # Process images
            extracted_results = []
            for i, image in enumerate(images):
                # Convert PIL image to base64
                img_buffer = io.BytesIO()
                image.save(img_buffer, format='PNG')
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                
                # Extract financial data
                result = extract_comprehensive_financial_data(
                    img_base64, 
                    f"page_{i+1}", 
                    ""
                )
                if result:
                    extracted_results.append(result)
            
            # Consolidate results
            if len(extracted_results) > 1:
                consolidated_data = consolidate_financial_data(extracted_results)
            else:
                consolidated_data = extracted_results[0] if extracted_results else {}
            
            return {
                "status": "success",
                "data": consolidated_data,
                "pages_processed": len(images),
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
            csv_data = create_ifrs_csv_export(data)
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
            csv_data = create_ifrs_csv_export(data)
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