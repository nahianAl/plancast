"""
PlanCast FastAPI Application

Main API server for the PlanCast floor plan to 3D model conversion service.
Provides RESTful endpoints for file upload, processing, and download with
comprehensive error handling and Railway deployment compatibility.
"""

import os
import uuid
import time
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# Import existing pipeline components
from core.floorplan_processor import FloorPlanProcessor, FloorPlanProcessingError
from models.data_structures import (
    ProcessingJob, ProcessingStatus, ExportFormat, FileFormat,
    UploadResponse, JobStatusResponse, ExportRequest, ExportResponse
)
from utils.validators import PlanCastValidator, ValidationError, SecurityError
from utils.logger import get_logger

# Configure logging
logger = get_logger("api")

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
processor = FloorPlanProcessor()
validator = PlanCastValidator()

# In-memory job storage (replace with database in production)
jobs: Dict[str, ProcessingJob] = {}

# Pydantic models for API requests
class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    pipeline_ready: bool = True
    timestamp: float = Field(default_factory=time.time)

class ConvertRequest(BaseModel):
    scale_reference: Optional[Dict[str, Any]] = None
    export_formats: List[str] = Field(
        default=["glb", "obj", "stl"],
        description="Export formats: glb, obj, stl, fbx, skp"
    )

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

# Dependency for job validation
def get_job(job_id: str) -> ProcessingJob:
    """Get job by ID or raise 404."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return jobs[job_id]

# Background task for processing
async def process_job_background(job_id: str, file_content: bytes, filename: str, 
                               scale_reference: Optional[Dict], export_formats: List[str]):
    """Background task for processing floor plans."""
    try:
        logger.info(f"🚀 Starting background processing for job {job_id}")
        
        # Process the floor plan
        job = processor.process_floorplan(
            file_content=file_content,
            filename=filename,
            scale_reference=scale_reference,
            export_formats=export_formats,
            output_dir="output/generated_models"
        )
        
        # Update job in memory
        jobs[job_id] = job
        
        logger.info(f"✅ Job {job_id} completed successfully")
        
    except FloorPlanProcessingError as e:
        logger.error(f"❌ Job {job_id} failed: {str(e)}")
        if job_id in jobs:
            jobs[job_id].status = ProcessingStatus.FAILED
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = time.time()
    except Exception as e:
        logger.error(f"❌ Unexpected error in job {job_id}: {str(e)}")
        if job_id in jobs:
            jobs[job_id].status = ProcessingStatus.FAILED
            jobs[job_id].error_message = f"Unexpected error: {str(e)}"
            jobs[job_id].completed_at = time.time()

# API Endpoints

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with health information."""
    return HealthResponse()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring and deployment."""
    return HealthResponse()

@app.post("/convert", response_model=ConvertResponse)
async def convert_floorplan(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    scale_reference: Optional[str] = None,
    export_formats: str = "glb,obj,stl"
):
    """
    Upload and convert a floor plan to 3D model.
    
    Accepts JPG, PNG, or PDF files and returns a job ID for tracking.
    Processing happens in the background.
    """
    try:
        logger.info(f"📁 Starting file upload: {file.filename}")
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        logger.info(f"🆔 Generated job ID: {job_id}")
        
        # Read file content
        file_content = await file.read()
        logger.info(f"📄 Read file content: {len(file_content)} bytes")
        
        # Validate file
        try:
            logger.info(f"🔍 Validating file: {file.filename}")
            validation_result = validator.validate_upload_file(file_content, file.filename)
            logger.info(f"✅ File validation passed: {validation_result}")
        except (ValidationError, SecurityError) as e:
            logger.error(f"❌ File validation failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        
        # Parse export formats
        try:
            formats = [f.strip().lower() for f in export_formats.split(",")]
            formats = [f for f in formats if f in ["glb", "obj", "stl", "fbx", "skp"]]
            if not formats:
                formats = ["glb", "obj", "stl"]
            logger.info(f"📦 Export formats: {formats}")
        except Exception as e:
            logger.warning(f"⚠️ Export format parsing failed: {str(e)}, using defaults")
            formats = ["glb", "obj", "stl"]
        
        # Parse scale reference if provided
        scale_ref = None
        if scale_reference:
            try:
                import json
                scale_ref = json.loads(scale_reference)
                logger.info(f"📏 Scale reference: {scale_ref}")
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Invalid scale reference JSON for job {job_id}")
        
        # Create initial job record
        job = ProcessingJob(
            job_id=job_id,
            filename=file.filename,
            file_format=validation_result.get("file_format", FileFormat.JPG),  # Fallback to JPG
            file_size_bytes=len(file_content),
            status=ProcessingStatus.PROCESSING,
            started_at=time.time()
        )
        
        # Store job
        jobs[job_id] = job
        logger.info(f"💾 Stored job in memory: {job_id}")
        
        # Start background processing
        logger.info(f"🚀 Starting background processing for job {job_id}")
        background_tasks.add_task(
            process_job_background,
            job_id,
            file_content,
            file.filename,
            scale_ref,
            formats
        )
        
        logger.info(f"📁 File upload completed: {file.filename} -> Job {job_id}")
        
        return ConvertResponse(
            job_id=job_id,
            filename=file.filename,
            file_size_bytes=len(file_content)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error during upload")

@app.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of a processing job."""
    try:
        job = get_job(job_id)
        
        processing_time = None
        if job.started_at:
            if job.completed_at:
                processing_time = job.completed_at - job.started_at
            else:
                processing_time = time.time() - job.started_at
        
        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            current_step=job.current_step,
            progress_percent=job.progress_percent,
            processing_time=processing_time,
            error_message=job.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Status check error for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/download/{job_id}/{format}")
async def download_file(job_id: str, format: str):
    """
    Download a processed 3D model file.
    
    Supported formats: glb, obj, stl, fbx, skp
    """
    try:
        job = get_job(job_id)
        
        # Check if job is completed
        if job.status != ProcessingStatus.COMPLETED:
            raise HTTPException(
                status_code=400, 
                detail=f"Job not completed. Current status: {job.status}"
            )
        
        # Validate format
        format = format.lower()
        if format not in ["glb", "obj", "stl", "fbx", "skp"]:
            raise HTTPException(status_code=400, detail="Unsupported format")
        
        # Check if file exists
        if format not in job.exported_files:
            raise HTTPException(
                status_code=404, 
                detail=f"File not found in {format} format"
            )
        
        file_path = job.exported_files[format]
        
        # Check if file exists on disk
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404, 
                detail=f"File not found on disk: {file_path}"
            )
        
        # Return file for download
        filename = f"{Path(job.filename).stem}_{format}.{format}"
        
        logger.info(f"📥 Download: {filename} for job {job_id}")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Download error for job {job_id}, format {format}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during download")

@app.get("/jobs/{job_id}/results")
async def get_job_results(job_id: str):
    """Get detailed results for a completed job."""
    try:
        job = get_job(job_id)
        
        if job.status != ProcessingStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Job not completed. Current status: {job.status}"
            )
        
        # Return job results
        return {
            "job_id": job.job_id,
            "status": job.status,
            "filename": job.filename,
            "exported_files": job.exported_files,
            "processing_time": job.total_processing_time(),
            "completed_at": job.completed_at,
            "warnings": job.warnings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Results error for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its associated files."""
    try:
        job = get_job(job_id)
        
        # Delete exported files
        for file_path in job.exported_files.values():
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"🗑️ Deleted file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {file_path}: {str(e)}")
        
        # Remove from memory
        del jobs[job_id]
        
        logger.info(f"🗑️ Deleted job: {job_id}")
        
        return {"message": f"Job {job_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete error for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/jobs")
async def list_jobs(limit: int = 50, offset: int = 0):
    """List all jobs with pagination."""
    try:
        job_list = list(jobs.values())
        job_list.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        start = offset
        end = start + limit
        paginated_jobs = job_list[start:end]
        
        return {
            "jobs": [
                {
                    "job_id": job.job_id,
                    "filename": job.filename,
                    "status": job.status,
                    "created_at": job.created_at,
                    "progress_percent": job.progress_percent
                }
                for job in paginated_jobs
            ],
            "total": len(job_list),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"❌ List jobs error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            message=exc.detail
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"❌ Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            message="An unexpected error occurred"
        ).dict()
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("🚀 PlanCast API starting up...")
    
    # Create output directory if it doesn't exist
    os.makedirs("output/generated_models", exist_ok=True)
    
    logger.info("✅ PlanCast API ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("🛑 PlanCast API shutting down...")

# Main entry point for Railway deployment
if __name__ == "__main__":
    # Get port from environment variable (Railway requirement)
    port = int(os.getenv("PORT", 8000))
    
    # Run with uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload for production
        log_level="info"
    )
