"""
PlanCast FastAPI Application

Main API server for the PlanCast floor plan to 3D model conversion service.
Provides RESTful endpoints for file upload, processing, and download with
comprehensive error handling and Railway deployment compatibility.
"""

import os
import sys
import uuid
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import only what we need
from models.data_structures import ProcessingJob, ProcessingStatus, FileFormat
from utils.validators import PlanCastValidator, ValidationError, SecurityError

# Initialize FastAPI app
app = FastAPI(
    title="PlanCast API",
    description="AI-powered floor plan to 3D model conversion service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
validator = PlanCastValidator()

# In-memory job storage (replace with database in production)
jobs: Dict[str, ProcessingJob] = {}

# Pydantic models
class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: float = Field(default_factory=time.time)

class ConvertResponse(BaseModel):
    job_id: str
    status: str = "processing"
    message: str = "Upload successful"
    filename: str
    file_size_bytes: int

class ErrorResponse(BaseModel):
    error: str
    message: str
    job_id: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)

# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse()

@app.post("/convert", response_model=ConvertResponse)
async def convert_floorplan(
    file: UploadFile = File(...),
    export_formats: str = "glb,obj,stl"
):
    """Upload endpoint with file validation and job creation."""
    try:
        print(f"📁 Starting upload: {file.filename}")
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        print(f"🆔 Job ID: {job_id}")
        
        # Read file content
        file_content = await file.read()
        print(f"📄 File size: {len(file_content)} bytes")
        
        # Validate file
        try:
            print(f"🔍 Validating file...")
            validation_result = validator.validate_upload_file(file_content, file.filename)
            print(f"✅ Validation result: {validation_result['is_valid']}")
            
            if not validation_result['is_valid']:
                raise HTTPException(status_code=400, detail=f"File validation failed: {validation_result['errors']}")
                
        except (ValidationError, SecurityError) as e:
            print(f"❌ Validation error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        
        # Create job record
        job = ProcessingJob(
            job_id=job_id,
            filename=file.filename,
            file_format=validation_result.get("file_format", FileFormat.JPEG),
            file_size_bytes=len(file_content),
            status=ProcessingStatus.PROCESSING,
            started_at=time.time()
        )
        
        # Store job
        jobs[job_id] = job
        print(f"💾 Job stored: {job_id}")
        
        print(f"✅ Upload completed successfully")
        
        return ConvertResponse(
            job_id=job_id,
            filename=file.filename,
            file_size_bytes=len(file_content)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Get job status."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = jobs[job_id]
    return {
        "job_id": job.job_id,
        "status": job.status,
        "current_step": job.current_step,
        "progress_percent": job.progress_percent
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            message=exc.detail
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    print(f"❌ Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            message="An unexpected error occurred"
        ).dict()
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
