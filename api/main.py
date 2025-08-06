from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import uuid
import os
import json
from datetime import datetime
from typing import Optional
import base64
import io

# Import our services
from services.file_processor import FileProcessor
from services.job_manager import JobManager
from core.config import settings

app = FastAPI(
    title="Financial Statement Transcription API",
    description="AI-powered API for extracting financial data from documents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
file_processor = FileProcessor()
job_manager = JobManager()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Financial Statement Transcription API",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/api/v1/extract-financial-data")
async def extract_financial_data(
    file: UploadFile = File(...),
    processing_approach: Optional[str] = "auto",
    output_format: Optional[str] = "csv",
    background_tasks: BackgroundTasks = None
):
    """
    Extract financial data from uploaded document
    
    Args:
        file: PDF or image file
        processing_approach: "whole_document", "vector_database", or "auto"
        output_format: "csv", "json", or "both"
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size (10MB limit)
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")
        
        # Create job
        job_id = str(uuid.uuid4())
        job_manager.create_job(job_id, {
            "filename": file.filename,
            "file_size": len(file_content),
            "processing_approach": processing_approach,
            "output_format": output_format,
            "status": "processing"
        })
        
        # For small files, process immediately
        if len(file_content) < 5 * 1024 * 1024:  # 5MB
            result = await file_processor.process_file_sync(
                file_content, 
                file.filename, 
                processing_approach,
                output_format
            )
            job_manager.update_job(job_id, {
                "status": "completed",
                "result": result,
                "completed_at": datetime.utcnow().isoformat()
            })
            return {
                "job_id": job_id,
                "status": "completed",
                "result": result
            }
        else:
            # For larger files, process in background
            background_tasks.add_task(
                file_processor.process_file_async,
                job_id,
                file_content,
                file.filename,
                processing_approach,
                output_format
            )
            return {
                "job_id": job_id,
                "status": "processing",
                "estimated_time": "30-60 seconds",
                "message": "File is being processed in the background"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get the status and result of a processing job"""
    try:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/extract-financial-data/sync")
async def extract_financial_data_sync(
    file: UploadFile = File(...),
    processing_approach: Optional[str] = "auto",
    output_format: Optional[str] = "csv"
):
    """
    Synchronous endpoint for small files (< 5MB)
    Returns results immediately
    """
    try:
        file_content = await file.read()
        
        if len(file_content) > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(
                status_code=400, 
                detail="File too large for sync processing. Use async endpoint for files > 5MB"
            )
        
        result = await file_processor.process_file_sync(
            file_content,
            file.filename,
            processing_approach,
            output_format
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "file_processor": "ok",
            "job_manager": "ok"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 