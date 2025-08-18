"""
PlanCast FastAPI Application

Main API server for the PlanCast floor plan to 3D model conversion service.
Provides RESTful endpoints for file upload, processing, and download with
comprehensive error handling, database integration, and Railway deployment compatibility.
"""

import os
import sys
import uuid
import time
import asyncio
import concurrent.futures
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import database models and services
from models.data_structures import ProcessingJob, ProcessingStatus, FileFormat, RoomAnalysisResponse, RoomSuggestion
from models.database import Project, ProjectStatus, User
from models.database_connection import get_db_session
from models.repository import ProjectRepository, UsageRepository, UserRepository
from utils.validators import PlanCastValidator, ValidationError, SecurityError
from services.websocket_manager import websocket_manager
from services.coordinate_scaler import CoordinateScaler

# Initialize FastAPI app
app = FastAPI(
    title="PlanCast API",
    description="AI-powered floor plan to 3D model conversion service",
    version="1.0.2",  # Force restart
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://getplancast.com",
        "https://www.getplancast.com",  # THIS IS CRITICAL
        "http://getplancast.com", 
        "http://www.getplancast.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        "https://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "Cache-Control",
        "Pragma"
    ],
    expose_headers=["*"],
    max_age=3600
)

# Add CORS preflight handler
@app.options("/{full_path:path}")
async def options_handler(request: Request):
    """Handle CORS preflight requests."""
    origin = request.headers.get("origin")
    print(f"🔍 CORS preflight request from origin: {origin}")
    
    # Check if origin is allowed
    allowed_origins = [
        "https://getplancast.com",
        "https://www.getplancast.com",
        "http://getplancast.com", 
        "http://www.getplancast.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        "https://127.0.0.1:3000"
    ]
    
    if origin in allowed_origins:
        return JSONResponse(
            content={"message": "CORS preflight successful"},
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD",
                "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers, Cache-Control, Pragma",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "3600"
            }
        )
    else:
        print(f"❌ CORS preflight rejected for origin: {origin}")
        return JSONResponse(
            content={"error": "CORS not allowed"},
            status_code=403
        )

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging."""
    origin = request.headers.get("origin", "No origin")
    user_agent = request.headers.get("user-agent", "No user agent")
    method = request.method
    url = str(request.url)
    
    print(f"🔍 Request: {method} {url}")
    print(f"🔍 Origin: {origin}")
    print(f"🔍 User-Agent: {user_agent}")
    
    response = await call_next(request)
    
    # Add CORS headers to all responses
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    
    print(f"🔍 Response: {response.status_code}")
    return response

# Initialize services
validator = PlanCastValidator()

# Mount static files for generated models so the frontend can load GLB/OBJ directly
MODELS_ROOT = Path("output/generated_models")
MODELS_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/models", StaticFiles(directory=str(MODELS_ROOT)), name="models")

# Public base URL for building absolute asset links (set in env on prod)
PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", "")

# Pydantic models
class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    database_status: str = "unknown"
    timestamp: float = Field(default_factory=time.time)

class ConvertResponse(BaseModel):
    job_id: str
    filename: str
    file_size_bytes: int
    status: str = "processing"
    message: str = "File uploaded successfully. Processing started."
class ErrorResponse(BaseModel):
    error: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    current_step: str
    progress_percent: int
    message: str
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None

# Database dependency
def get_db():
    """Database session dependency."""
    with get_db_session() as session:
        yield session

# Background task for processing
async def process_floorplan_background(job_id: str, file_content: bytes, filename: str, export_formats: str):
    """Background task for processing floor plan files with real-time updates."""
    try:
        # Import the actual FloorPlanProcessor
        from core.floorplan_processor import FloorPlanProcessor
        
        # Initialize the processor
        processor = FloorPlanProcessor()
        
        # Parse export formats
        formats_list = [fmt.strip() for fmt in export_formats.split(',') if fmt.strip()]
        
        # Create a progress callback function for real-time updates
        async def progress_callback(step: str, progress: int, message: str):
            """Callback function to send real-time updates during processing."""
            # Update database
            with get_db_session() as session:
                ProjectRepository.update_project_status(
                    session, 
                    int(job_id), 
                    ProjectStatus.PROCESSING,
                    current_step=step,
                    progress_percent=progress
                )
            
            # Send WebSocket updates
            await websocket_manager.broadcast_job_update(
                job_id, 
                "processing", 
                progress, 
                message
            )
            await websocket_manager.broadcast_processing_progress(
                job_id, 
                step, 
                progress, 
                message
            )
        
        # Run the actual FloorPlan processing with real progress tracking
        await progress_callback("ai_analysis", 10, "Starting AI analysis...")
        
        # Process the floor plan with timeout handling
        def run_processing():
            return processor.process_floorplan(
                file_content=file_content,
                filename=filename,
                export_formats=formats_list,
                output_dir=f"output/generated_models/{job_id}"
            )
        
        # Run the processing in a thread pool with timeout
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit the processing job with a longer timeout for real model
            future = executor.submit(run_processing)
            
            try:
                # Wait for processing with a longer timeout (5 minutes for real model)
                processing_result = future.result(timeout=300)  # 5 minutes timeout
                
                # Extract result data
                if processing_result.status == ProcessingStatus.COMPLETED and processing_result.exported_files:
                    print(f"🔍 Processing completed successfully for job {job_id}")
                    print(f"🔍 Exported files from processing: {processing_result.exported_files}")
                    
                    # Build URLs to exported files under /models/{job_id}/
                    exported_files = {}
                    for fmt, path in (processing_result.exported_files or {}).items():
                        try:
                            filename_only = Path(path).name
                            relative_url = f"/models/{job_id}/{filename_only}"
                            exported_files[fmt] = (
                                f"{PUBLIC_API_URL}{relative_url}" if PUBLIC_API_URL else relative_url
                            )
                            print(f"🔍 Built URL for {fmt}: {exported_files[fmt]}")
                        except Exception as e:
                            print(f"❌ Error building URL for {fmt}: {e}")
                            # Fallback to raw path if something goes wrong
                            exported_files[fmt] = path

                    # Choose GLB as primary model URL if available
                    glb_url = exported_files.get("glb", next(iter(exported_files.values()), ""))

                    result_data = {
                        "model_url": glb_url,
                        "preview_url": "",
                        "formats": list(exported_files.keys()),
                        "processing_time": (processing_result.total_processing_time() or 0.0),
                        "file_size_mb": sum(os.path.getsize(p) for p in (processing_result.exported_files or {}).values()) / (1024 * 1024) if processing_result.exported_files else 0.0,
                        "output_files": exported_files,
                    }
                    
                    print(f"🔍 Final exported_files for database: {exported_files}")
                    print(f"🔍 Result data: {result_data}")
                else:
                    print(f"❌ Processing failed or no exported files for job {job_id}")
                    print(f"🔍 Status: {processing_result.status}")
                    print(f"🔍 Exported files: {processing_result.exported_files}")
                    raise Exception(f"Processing failed: {processing_result.error_message}")
                
                with get_db_session() as session:
                    print(f"🔍 Updating database for job {job_id} with output_files: {exported_files}")
                    ProjectRepository.update_project_status(
                        session, 
                        int(job_id), 
                        ProjectStatus.COMPLETED,
                        current_step="completed",
                        progress_percent=100,
                        processing_time_seconds=processing_result.total_processing_time() or 0.0,
                        output_files=exported_files,
                        processing_metadata={"result": result_data}
                    )
                    print(f"✅ Database updated successfully for job {job_id}")
                
                # Send completion WebSocket update
                print(f"🔍 Sending completion WebSocket update for job {job_id}")
                print(f"🔍 Result data: {result_data}")
                
                await websocket_manager.broadcast_job_update(
                    job_id, 
                    "completed", 
                    100, 
                    "3D model conversion completed successfully!",
                    result_data
                )
                
                print(f"✅ Completion WebSocket update sent for job {job_id}")
                
            except concurrent.futures.TimeoutError:
                # Processing timed out
                future.cancel()
                raise Exception("Processing timed out after 5 minutes. The floor plan may be too complex or the server is under heavy load.")
                
    except Exception as e:
        # Mark as failed and send error update
        error_message = str(e)
        with get_db_session() as session:
            ProjectRepository.update_project_status(
                session, 
                int(job_id), 
                ProjectStatus.FAILED,
                error_message=error_message
            )
        
        # Send failure WebSocket update
        await websocket_manager.broadcast_job_update(
            job_id, 
            "failed", 
            0, 
            f"Processing failed: {error_message}"
        )

# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with database status."""
    try:
        # Test database connection
        from sqlalchemy import text
        with get_db_session() as session:
            result = session.execute(text("SELECT 1"))
            db_status = "healthy" if result.scalar() == 1 else "unhealthy"
    except Exception:
        db_status = "unhealthy"
    
    return HealthResponse(database_status=db_status)



@app.post("/convert", response_model=ConvertResponse)
async def convert_floorplan(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    export_formats: str = "glb,obj,stl",
    scale_reference: Optional[str] = None
):
    """Upload endpoint with file validation, job creation, and background processing."""
    try:
        # Debug logging
        origin = request.headers.get('origin', 'No origin header')
        print(f"🔍 Received conversion request from origin: {origin}")
        print(f"🔍 User-Agent: {request.headers.get('user-agent', 'Unknown')}")
        print(f"🔍 Content-Type: {request.headers.get('content-type', 'Unknown')}")
        
        # Read file content
        file_content = await file.read()
        
        # Validate file
        try:
            
            validation_result = validator.validate_upload_file(file_content, file.filename)
            
            if not validation_result['is_valid']:
                raise HTTPException(status_code=400, detail=f"File validation failed: {validation_result['errors']}")
                
        except (ValidationError, SecurityError) as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Create project in database (avoid ORM enum coercion issues)
        from sqlalchemy import text as sql_text
        with get_db_session() as session:
            # Resolve admin user id via raw SQL to bypass enum mapping mismatches
            row = session.execute(
                sql_text("SELECT id FROM users WHERE email=:email LIMIT 1"),
                {"email": "admin@plancast.com"}
            ).first()
            if row and len(row) > 0:
                user_id = int(row[0])
            else:
                # Insert admin matching DB enum (lowercase: 'free','pro','enterprise')
                inserted = session.execute(
                    sql_text(
                        """
                        INSERT INTO users (email, password_hash, subscription_tier, is_active, created_at)
                        VALUES (:email, :password_hash, 'free', true, NOW())
                        RETURNING id
                        """
                    ),
                    {"email": "admin@plancast.com", "password_hash": "placeholder"}
                ).first()
                session.commit()
                user_id = int(inserted[0])

            # Create project record via repository (safe; only writes enum-free fields)
            project = ProjectRepository.create_project(
                session=session,
                user_id=user_id,
                filename=f"project_{uuid.uuid4().hex[:8]}",
                original_filename=file.filename,
                input_file_path=f"temp/uploads/{file.filename}",
                file_size_mb=len(file_content) / (1024 * 1024),
                file_format=validation_result.get("file_format", "jpg"),
                scale_reference=scale_reference
            )

            # Log usage (enum value comes from model; column stores as string ok)
            UsageRepository.log_usage(
                session=session,
                user_id=user_id,
                action_type="upload",
                api_endpoint="/convert",
                file_size_mb=len(file_content) / (1024 * 1024),
                request_metadata={"filename": file.filename, "export_formats": export_formats}
            )

            # Capture project ID before session closes to avoid detached refresh
            project_id = int(project.id)
        
        # Start background processing
        background_tasks.add_task(
            process_floorplan_background,
            str(project_id),
            file_content,
            file.filename,
            export_formats
        )
        
        response_data = ConvertResponse(
            job_id=str(project_id),
            filename=file.filename,
            file_size_bytes=len(file_content)
        )
        
        # Create JSONResponse with explicit CORS headers
        response = JSONResponse(content=response_data.model_dump())
        response.headers["Access-Control-Allow-Origin"] = origin if origin != 'No origin header' else "https://www.getplancast.com"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        
        print(f"✅ Sending response with CORS headers for origin: {origin}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"❌ Unexpected error in /convert: {str(e)}")
        print(f"Traceback: {tb}")
        origin = request.headers.get('origin', 'https://www.getplancast.com')
        response = JSONResponse(
            status_code=500,
            content=ErrorResponse(error="Internal server error", message=str(e)).dict()
        )
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "*"
        return response

@app.get("/test-db")
async def test_database_operations():
    """Test endpoint for database operations without file upload."""
    try:
        print("🔍 Starting comprehensive database test...")
        
        with get_db_session() as session:
            print("✅ Database session created")
            
            # Test 1: Basic query
            from sqlalchemy import text
            result = session.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            print(f"✅ Basic query result: {test_value}")
            
            # Test 2: Get admin user
            user = session.query(User).filter(User.email == "admin@plancast.com").first()
            if not user:
                raise HTTPException(status_code=500, detail="No admin user found")
            print(f"✅ Admin user found: {user.email}")
            
            # Test 3: Create test project
            from models.database import Project, ProjectStatus
            project = Project(
                user_id=user.id,
                filename="test_project_123",
                original_filename="test_floorplan.jpg",
                input_file_path="temp/test/test_floorplan.jpg",
                file_size_mb=0.1,
                file_format="jpg"
            )
            session.add(project)
            session.commit()
            session.refresh(project)
            print(f"✅ Project created with ID: {project.id}")
            
            # Test 4: Log usage
            from models.database import UsageLog, ActionType
            usage = UsageLog(
                user_id=user.id,
                project_id=project.id,
                action_type=ActionType.UPLOAD,
                api_endpoint="/test-db",
                file_size_mb=0.1,
                request_metadata={"test": True}
            )
            session.add(usage)
            session.commit()
            print(f"✅ Usage logged with ID: {usage.id}")
            
            # Test 5: Update project status
            project.status = ProjectStatus.PROCESSING
            project.current_step = "ai_analysis"
            project.progress_percent = 25
            session.commit()
            print(f"✅ Project status updated to: {project.status.value}")
            
            # Clean up test data
            session.delete(usage)
            session.delete(project)
            session.commit()
            print("✅ Test data cleaned up")
            
            return {
                "message": "Comprehensive database test successful",
                "user_email": user.email,
                "project_created": True,
                "usage_logged": True,
                "status_updated": True
            }
            
    except Exception as e:
        import traceback
        error_msg = f"Database test error: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str, request: Request):
    """Get job status from database."""
    try:
        # Sanitize job id (handle cases like "%7B6%7D")
        import re as _re
        cleaned_job_id = _re.sub(r"[^0-9]", "", job_id or "")
        if not cleaned_job_id:
            raise HTTPException(status_code=400, detail="Invalid job id")
        job_int = int(cleaned_job_id)

        with get_db_session() as session:
            project = ProjectRepository.get_project_by_id(session, job_int)
            
            if not project:
                raise HTTPException(status_code=404, detail="Job not found")
            
            # Convert project status to response format
            status_mapping = {
                ProjectStatus.PENDING: "pending",
                ProjectStatus.PROCESSING: "processing", 
                ProjectStatus.COMPLETED: "completed",
                ProjectStatus.FAILED: "failed",
                ProjectStatus.CANCELLED: "cancelled"
            }
            
            # Build result payload from stored output files
            exported_files = project.output_files or {}
            result_payload = None
            if exported_files:
                glb_path = exported_files.get('glb')
                if glb_path:
                    filename_only = Path(glb_path).name
                    relative_url = f"/models/{job_id}/{filename_only}"
                    model_url = f"{PUBLIC_API_URL}{relative_url}" if PUBLIC_API_URL else relative_url
                else:
                    first_path = next(iter(exported_files.values()), '')
                    filename_only = Path(first_path).name if first_path else ''
                    relative_url = f"/models/{job_id}/{filename_only}" if first_path else ''
                    model_url = f"{PUBLIC_API_URL}{relative_url}" if PUBLIC_API_URL and relative_url else relative_url
                result_payload = {
                    'model_url': model_url,
                    'formats': list(exported_files.keys()),
                    'output_files': {
                        fmt: ((f"{PUBLIC_API_URL}/models/{job_int}/{Path(p).name}") if PUBLIC_API_URL else f"/models/{job_int}/{Path(p).name}")
                        for fmt, p in exported_files.items()
                    }
                }

            return JobStatusResponse(
                job_id=str(job_int),
                status=status_mapping.get(project.status, "unknown"),
                current_step=project.current_step or "upload",
                progress_percent=project.progress_percent or 0,
                message=(
                    "Processing in progress" if project.status == ProjectStatus.PROCESSING else (
                        project.error_message or ("Completed" if project.status == ProjectStatus.COMPLETED else "Ready")
                    )
                ),
                created_at=project.created_at.timestamp() if project.created_at else time.time(),
                started_at=None,
                completed_at=project.completed_at.timestamp() if project.completed_at else None,
                result=result_payload
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting job status: {str(e)}")
        # Return error with CORS-friendly body
        origin = request.headers.get('origin', 'https://www.getplancast.com')
        response = JSONResponse(
            status_code=500,
            content=ErrorResponse(error="Internal server error", message=str(e)).dict()
        )
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "*"
        return response

@app.get("/projects")
async def list_projects(skip: int = 0, limit: int = 100):
    """List user projects (placeholder for authentication)."""
    try:
        with get_db_session() as session:
            # TODO: Get actual user ID from authentication
            user = session.query(User).filter(User.email == "admin@plancast.com").first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            projects = ProjectRepository.get_projects_by_user(session, user.id, skip, limit)
            
            return {
                "projects": [
                    {
                        "id": p.id,
                        "filename": p.filename,
                        "status": p.status.value,
                        "created_at": p.created_at.isoformat() if p.created_at else None,
                        "progress_percent": p.progress_percent
                    }
                    for p in projects
                ],
                "total": len(projects)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error listing projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/stats")
async def get_user_stats():
    """Get user statistics and usage."""
    try:
        with get_db_session() as session:
            # TODO: Get actual user ID from authentication
            user = session.query(User).filter(User.email == "admin@plancast.com").first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            project_stats = ProjectRepository.get_project_stats(session, user.id)
            usage_summary = UsageRepository.get_usage_summary(session, user.id, days=30)
            
            return {
                "user": {
                    "email": user.email,
                    "subscription_tier": user.subscription_tier.value,
                    "is_active": user.is_active
                },
                "projects": project_stats,
                "usage": usage_summary
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting user stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/websocket/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return websocket_manager.get_connection_stats()

@app.get("/analyze/{job_id}/rooms", response_model=RoomAnalysisResponse)
async def analyze_rooms_for_highlighting(job_id: str, request: Request):
    """
    Analyze detected rooms and provide suggestions for user selection.
    This endpoint is called after AI analysis to get room highlighting data.
    """
    try:
        print(f"🔍 Analyzing rooms for job {job_id}")
        
        # Validate job ID
        try:
            job_int = int(job_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid job ID format")
        
        # Get project from database
        with get_db_session() as session:
            project = session.query(Project).filter(Project.id == job_int).first()
            if not project:
                raise HTTPException(status_code=404, detail="Job not found")
            
            # Check if AI analysis is complete
            if not project.processing_metadata or "cubicasa_output" not in project.processing_metadata:
                raise HTTPException(
                    status_code=400, 
                    detail="AI analysis not complete. Please wait for processing to finish."
                )
            
            # Extract CubiCasa output from metadata
            cubicasa_data = project.processing_metadata.get("cubicasa_output", {})
            if not cubicasa_data:
                raise HTTPException(
                    status_code=400, 
                    detail="No AI analysis data available"
                )
            
            # Convert back to CubiCasaOutput object
            from models.data_structures import CubiCasaOutput
            cubicasa_output = CubiCasaOutput(**cubicasa_data)
            
            # Get room suggestions using coordinate scaler
            coordinate_scaler = CoordinateScaler()
            room_suggestions = coordinate_scaler.get_smart_room_suggestions(cubicasa_output)
            
            # Convert to RoomSuggestion objects
            rooms = []
            for suggestion in room_suggestions:
                room = RoomSuggestion(
                    room_name=suggestion["room_name"],
                    confidence=suggestion["confidence"],
                    bounding_box=cubicasa_output.room_bounding_boxes[suggestion["room_name"]],
                    pixel_dimensions=suggestion["pixel_dimensions"],
                    suggested_dimension=suggestion["suggested_dimension"],
                    is_recommended=suggestion["is_recommended"],
                    highlight_color=suggestion.get("highlight_color", "#4ECDC4"),
                    priority=suggestion.get("priority", 999),
                    reason=suggestion.get("reason", "Standard room")
                )
                rooms.append(room)
            
            # Sort by priority and confidence
            rooms.sort(key=lambda x: (x.priority, -x.confidence))
            
            response = RoomAnalysisResponse(
                job_id=job_id,
                rooms=rooms,
                image_dimensions=cubicasa_output.image_dimensions,
                analysis_complete=True
            )
            
            # Add CORS headers
            origin = request.headers.get('origin', 'https://www.getplancast.com')
            response_obj = JSONResponse(content=response.model_dump())
            response_obj.headers["Access-Control-Allow-Origin"] = origin
            response_obj.headers["Access-Control-Allow-Credentials"] = "true"
            response_obj.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response_obj.headers["Access-Control-Allow-Headers"] = "*"
            
            print(f"✅ Room analysis completed for job {job_id}: {len(rooms)} rooms found")
            return response_obj
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"❌ Error analyzing rooms for job {job_id}: {str(e)}")
        print(f"Traceback: {tb}")
        
        origin = request.headers.get('origin', 'https://www.getplancast.com')
        response = JSONResponse(
            status_code=500,
            content=ErrorResponse(error="Internal server error", message=str(e)).dict()
        )
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

@app.post("/scale/{job_id}")
async def submit_scale_input(job_id: str, scale_input: ScaleInputRequest, request: Request):
    """
    Submit user scale input for room dimension.
    This endpoint is called after room selection to provide scaling reference.
    """
    try:
        print(f"🔍 Submitting scale input for job {job_id}")
        
        # Validate job ID
        try:
            job_int = int(job_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid job ID format")
        
        # Validate scale input
        if scale_input.real_world_feet <= 0:
            raise HTTPException(status_code=400, detail="Real-world measurement must be positive")
        
        if scale_input.dimension_type not in ["width", "length"]:
            raise HTTPException(status_code=400, detail="Dimension type must be 'width' or 'length'")
        
        # Get project from database
        with get_db_session() as session:
            project = session.query(Project).filter(Project.id == job_int).first()
            if not project:
                raise HTTPException(status_code=404, detail="Job not found")
            
            # Check if AI analysis is complete
            if not project.processing_metadata or "cubicasa_output" not in project.processing_metadata:
                raise HTTPException(
                    status_code=400, 
                    detail="AI analysis not complete. Please wait for processing to finish."
                )
            
            # Extract CubiCasa output from metadata
            cubicasa_data = project.processing_metadata.get("cubicasa_output", {})
            if not cubicasa_data:
                raise HTTPException(
                    status_code=400, 
                    detail="No AI analysis data available"
                )
            
            # Convert back to CubiCasaOutput object
            from models.data_structures import CubiCasaOutput
            cubicasa_output = CubiCasaOutput(**cubicasa_data)
            
            # Validate room exists
            if scale_input.room_type not in cubicasa_output.room_bounding_boxes:
                available_rooms = list(cubicasa_output.room_bounding_boxes.keys())
                raise HTTPException(
                    status_code=400, 
                    detail=f"Room '{scale_input.room_type}' not found. Available rooms: {available_rooms}"
                )
            
            # Process scaling with user input
            coordinate_scaler = CoordinateScaler()
            scaled_coords = coordinate_scaler.process_scaling_request(
                cubicasa_output=cubicasa_output,
                room_type=scale_input.room_type,
                dimension_type=scale_input.dimension_type,
                real_world_feet=scale_input.real_world_feet,
                job_id=job_id
            )
            
            # Update project with scaled coordinates
            project.processing_metadata = project.processing_metadata or {}
            project.processing_metadata["scaled_coordinates"] = scaled_coords.model_dump()
            project.processing_metadata["scale_input"] = scale_input.model_dump()
            
            # Update project status to indicate scaling is complete
            project.current_step = "scaling_complete"
            project.progress_percent = 60
            
            session.commit()
            
            print(f"✅ Scale input processed for job {job_id}: {scale_input.room_type} {scale_input.dimension_type} = {scale_input.real_world_feet} feet")
            
            # Add CORS headers
            origin = request.headers.get('origin', 'https://www.getplancast.com')
            response = JSONResponse(content={
                "success": True,
                "message": "Scale input processed successfully",
                "job_id": job_id,
                "scale_factor": scaled_coords.scale_reference.scale_factor
            })
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"❌ Error processing scale input for job {job_id}: {str(e)}")
        print(f"Traceback: {tb}")
        
        origin = request.headers.get('origin', 'https://www.getplancast.com')
        response = JSONResponse(
            status_code=500,
            content=ErrorResponse(error="Internal server error", message=str(e)).dict()
        )
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    origin = request.headers.get('origin', 'https://www.getplancast.com')
    response = JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            message=exc.detail
        ).dict()
    )
    # Ensure CORS headers are present even on errors
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Expose-Headers"] = "*"
    return response

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    print(f"❌ Unhandled exception: {str(exc)}")
    origin = request.headers.get('origin', 'https://www.getplancast.com')
    response = JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            message=str(exc) or "An unexpected error occurred"
        ).dict()
    )
    # Ensure CORS headers are present even on errors
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Expose-Headers"] = "*"
    return response

# Mount Socket.IO to the FastAPI app
socketio_app = websocket_manager.mount_to_app(app)

# Main entry point
if __name__ == "__main__":
    import asyncio
    
    # Get port from environment (for Railway deployment)
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting PlanCast API server on port {port}")
    print(f"📊 Database integration: Enabled")
    print(f"🔄 Background processing: Enabled")
    print(f"🔌 WebSocket support: Enabled")
    
    uvicorn.run(
        socketio_app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
