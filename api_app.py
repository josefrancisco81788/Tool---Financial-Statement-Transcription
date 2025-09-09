"""
Financial Statement Transcription API

A FastAPI application for extracting financial data from PDF documents and images
using AI-powered analysis. Built on the proven alpha-testing-v1 foundation.
"""

import os
import time
from typing import Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from core import FinancialDataExtractor, PDFProcessor, Config


# Initialize FastAPI app
app = FastAPI(
    title=Config.API_TITLE,
    version=Config.API_VERSION,
    description=Config.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
config = Config()
extractor = FinancialDataExtractor()
pdf_processor = PDFProcessor(extractor)


# Request/Response Models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: Dict[str, str]
    timestamp: str


class SuccessResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]
    processing_time: float
    pages_processed: int
    timestamp: str


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    try:
        # Validate configuration
        config.validate()
        print("✅ Configuration validated successfully")
        
    except Exception as e:
        print(f"❌ Startup error: {str(e)}")
        raise


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API service status"""
    return HealthResponse(
        status="healthy",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        version=config.API_VERSION
    )


# Main extraction endpoint
@app.post("/extract", response_model=SuccessResponse)
async def extract_financial_data(
    file: UploadFile = File(...),
    statement_type: Optional[str] = Form(None)
):
    """
    Extract financial data from uploaded PDF or image file.
    
    Args:
        file: PDF or image file (PNG, JPG, JPEG)
        statement_type: Optional hint for statement type (balance_sheet, income_statement, cash_flow)
    
    Returns:
        JSON response with extracted financial data
    """
    start_time = time.time()
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size
        file_content = await file.read()
        if len(file_content) > config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size: {config.MAX_FILE_SIZE} bytes"
            )
        
        # Check file type
        file_extension = os.path.splitext(file.filename.lower())[1]
        if file_extension not in config.SUPPORTED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported types: {', '.join(config.SUPPORTED_FILE_TYPES)}"
            )
        
        # Process file based on type
        if file_extension == '.pdf':
            # Process PDF
            extracted_data = pdf_processor.process_pdf_with_vector_db(file_content)
            pages_processed = extracted_data.get('pages_processed', 1) if extracted_data else 0
        else:
            # Process image
            extracted_data = extractor.extract_from_image(file_content, statement_type or "financial statement")
            pages_processed = 1
        
        if not extracted_data:
            raise HTTPException(status_code=422, detail="No financial data could be extracted from the document")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return SuccessResponse(
            data=extracted_data,
            processing_time=processing_time,
            pages_processed=pages_processed,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        error_response = ErrorResponse(
            error={
                "code": "PROCESSING_ERROR",
                "message": "Failed to extract financial data from document",
                "details": str(e)
            },
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        raise HTTPException(status_code=500, detail=error_response.dict())


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": f"HTTP {exc.status_code} error"
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "Internal server error",
                "details": str(exc)
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Financial Statement Transcription API",
        "version": config.API_VERSION,
        "docs": "/docs",
        "health": "/health",
        "extract": "/extract"
    }


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "api_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )
