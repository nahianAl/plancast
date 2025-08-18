"""
Core Floor Plan Processor for PlanCast.

Main orchestrator that coordinates the entire pipeline:
FileProcessor → CubiCasa → CoordinateScaler → RoomGenerator → WallGenerator → Building Assembly → MeshExporter

This is the central service that manages the complete 2D to 3D conversion process.
"""

import time
import uuid
from typing import List, Optional, Dict, Any
import logging
import os

from models.data_structures import (
    ProcessingJob,
    ProcessingStatus,
    CubiCasaOutput,
    ScaledCoordinates,
    Building3D,
    MeshExportResult,
    ExportConfig,
    ExportFormat,
    FileFormat
)
from services.file_processor import FileProcessor, FileProcessingError
from services.cubicasa_service import CubiCasaService, CubiCasaError
from services.coordinate_scaler import CoordinateScaler, ScalingError
from services.room_generator import RoomMeshGenerator, RoomGenerationError
from services.wall_generator import WallMeshGenerator, WallGenerationError
from services.opening_cutout_generator import OpeningCutoutGenerator, OpeningCutoutError
from services.mesh_exporter import MeshExporter, MeshExportError
from utils.logger import get_logger, log_job_start, log_job_complete, log_job_error

logger = get_logger("floorplan_processor")


class FloorPlanProcessingError(Exception):
    """Custom exception for floor plan processing errors."""
    pass


class FloorPlanProcessor:
    """
    Production orchestrator for the complete PlanCast pipeline.
    
    Manages the entire workflow from file upload to 3D model export,
    with comprehensive error handling, progress tracking, and logging.
    """
    
    def __init__(self):
        """Initialize the floor plan processor with all services."""
        self.file_processor = FileProcessor()
        # Use global CubiCasa service to avoid reinitializing model for every job
        from services.cubicasa_service import get_cubicasa_service
        self.cubicasa_service = get_cubicasa_service()
        self.coordinate_scaler = CoordinateScaler()
        self.room_generator = RoomMeshGenerator()
        self.wall_generator = WallMeshGenerator()
        self.opening_cutout_generator = OpeningCutoutGenerator()
        self.mesh_exporter = MeshExporter()
        
        logger.info("✅ Floor plan processor initialized with all services")
    
    def process_floorplan(self,
                         file_content: bytes,
                         filename: str,
                         scale_reference: Optional[Dict[str, Any]] = None,
                         export_formats: List[str] = None,
                         output_dir: str = None) -> ProcessingJob:
        """
        Process a floor plan through the complete pipeline.
        
        Args:
            file_content: Raw file bytes (JPG/PNG/PDF)
            filename: Original filename
            scale_reference: Optional scaling reference for coordinate conversion
            export_formats: List of export formats (glb, obj, stl, fbx, skp)
            output_dir: Output directory for generated files (defaults to persistent storage)
            
        Returns:
            ProcessingJob with complete results and status
            
        Raises:
            FloorPlanProcessingError: If processing fails at any step
        """
        # Use persistent storage if available, otherwise fallback to local
        if output_dir is None:
            railway_persistent = os.getenv("RAILWAY_PERSISTENT_DIR", "/data")
            if os.path.exists(railway_persistent):
                output_dir = os.path.join(railway_persistent, "output", "generated_models")
            else:
                output_dir = "output/generated_models"
        
        # Initialize job
        job_id = str(uuid.uuid4())
        job = ProcessingJob(
            job_id=job_id,
            filename=filename,
            file_format=self._detect_file_format(filename),
            file_size_bytes=len(file_content),
            status=ProcessingStatus.PROCESSING,
            started_at=time.time()
        )
        
        logger.info(f"🚀 Starting floor plan processing: {job_id}")
        logger.info(f"File: {filename} ({len(file_content)} bytes)")
        
        try:
            # Step 1: File Processing
            job.current_step = "file_processing"
            job.progress_percent = 10
            logger.info(f"📁 Step 1: Processing file {filename}")
            
            file_validation = self.file_processor.validate_file(file_content, filename)
            logger.info(f"✅ File validation passed: {file_validation}")
            
            # Step 2: CubiCasa5K AI Processing
            job.current_step = "ai_processing"
            job.progress_percent = 25
            logger.info(f"🤖 Step 2: Running CubiCasa5K AI analysis")
            
            cubicasa_output = self.cubicasa_service.process_image(file_content, job.job_id)
            job.cubicasa_output = cubicasa_output
            
            logger.info(f"✅ AI processing completed: {len(cubicasa_output.room_bounding_boxes)} rooms detected")
            
            # Step 3: Coordinate Scaling
            job.current_step = "coordinate_scaling"
            job.progress_percent = 40
            logger.info(f"📏 Step 3: Converting coordinates to real-world measurements")
            
            if scale_reference:
                scaled_coords = self.coordinate_scaler.process_scaling_request(
                    cubicasa_output=cubicasa_output,
                    room_type=scale_reference["room_type"],
                    dimension_type=scale_reference["dimension_type"],
                    real_world_feet=scale_reference["real_world_feet"],
                    job_id=job.job_id
                )
            else:
                # Use default scaling if no reference provided
                first_room = list(cubicasa_output.room_bounding_boxes.keys())[0]
                scaled_coords = self.coordinate_scaler.process_scaling_request(
                    cubicasa_output=cubicasa_output,
                    room_type=first_room,
                    dimension_type="width",
                    real_world_feet=12.0,  # Default 12-foot room width
                    job_id=job.job_id
                )
            
            job.scaled_coordinates = scaled_coords
            logger.info(f"✅ Coordinate scaling completed: {len(scaled_coords.rooms_feet)} rooms scaled")
            
            # Step 4: Room Mesh Generation
            job.current_step = "room_generation"
            job.progress_percent = 55
            logger.info(f"🏠 Step 4: Generating 3D room meshes")
            
            room_meshes = self.room_generator.generate_room_meshes(scaled_coords)
            logger.info(f"✅ Room generation completed: {len(room_meshes)} room meshes created")
            
            # Step 5: Wall Mesh Generation
            job.current_step = "wall_generation"
            job.progress_percent = 70
            logger.info(f"🧱 Step 5: Generating 3D wall meshes")
            
            wall_meshes = self.wall_generator.generate_wall_meshes(scaled_coords)
            logger.info(f"✅ Wall generation completed: {len(wall_meshes)} wall meshes created")
            
            # Step 5.5: Door/Window Cutout Generation
            job.current_step = "cutout_generation"
            job.progress_percent = 75
            logger.info(f"🚪 Step 5.5: Generating door and window cutouts")
            
            wall_meshes_with_cutouts = self.opening_cutout_generator.generate_cutouts(scaled_coords, wall_meshes)
            logger.info(f"✅ Cutout generation completed: {len(wall_meshes_with_cutouts)} walls with cutouts")
            
            # Step 6: Building Assembly
            job.current_step = "building_assembly"
            job.progress_percent = 80
            logger.info(f"🏗️ Step 6: Assembling complete 3D building model")
            
            building_3d = self._assemble_building(room_meshes, wall_meshes_with_cutouts, scaled_coords)
            job.building_3d = building_3d
            
            logger.info(f"✅ Building assembly completed: {building_3d.total_vertices} vertices, {building_3d.total_faces} faces")
            
            # Step 7: 3D Model Export
            job.current_step = "model_export"
            job.progress_percent = 90
            logger.info(f"📦 Step 7: Exporting 3D models")
            
            if export_formats is None:
                export_formats = ["glb", "obj", "stl"]  # Default formats
            
            export_result = self.mesh_exporter.export_building(
                building=building_3d,
                formats=export_formats,
                out_dir=output_dir
            )
            
            job.exported_files = export_result.files
            job.progress_percent = 100
            job.status = ProcessingStatus.COMPLETED
            job.completed_at = time.time()
            
            logger.info(f"✅ Model export completed: {len(export_result.files)} formats exported")
            
            # Log completion
            processing_time = job.total_processing_time()
            logger.info(f"🎉 Floor plan processing completed successfully!")
            logger.info(f"   Job ID: {job_id}")
            logger.info(f"   Processing time: {processing_time:.2f} seconds")
            logger.info(f"   Files exported: {list(export_result.files.keys())}")
            logger.info(f"   Total file size: {export_result.summary.get('total_size_bytes', 0)} bytes")
            
            return job
            
        except FileProcessingError as e:
            error_msg = f"File processing failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return self._handle_job_error(job, error_msg, "file_processing")
            
        except CubiCasaError as e:
            error_msg = f"AI processing failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return self._handle_job_error(job, error_msg, "ai_processing")
            
        except ScalingError as e:
            error_msg = f"Coordinate scaling failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return self._handle_job_error(job, error_msg, "coordinate_scaling")
            
        except RoomGenerationError as e:
            error_msg = f"Room generation failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return self._handle_job_error(job, error_msg, "room_generation")
            
        except WallGenerationError as e:
            error_msg = f"Wall generation failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return self._handle_job_error(job, error_msg, "wall_generation")
            
        except OpeningCutoutError as e:
            error_msg = f"Cutout generation failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return self._handle_job_error(job, error_msg, "cutout_generation")
            
        except MeshExportError as e:
            error_msg = f"Model export failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return self._handle_job_error(job, error_msg, "model_export")
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return self._handle_job_error(job, error_msg, "unknown")
    
    def _assemble_building(self, room_meshes: List, wall_meshes: List, scaled_coords) -> Building3D:
        """
        Assemble room and wall meshes into a complete Building3D object.
        
        Args:
            room_meshes: List of Room3D objects
            wall_meshes: List of Wall3D objects
            scaled_coords: ScaledCoordinates for metadata
            
        Returns:
            Building3D object ready for export
        """
        # Calculate total geometry stats
        total_vertices = sum(len(room.vertices) for room in room_meshes) + sum(len(wall.vertices) for wall in wall_meshes)
        total_faces = sum(len(room.faces) for room in room_meshes) + sum(len(wall.faces) for wall in wall_meshes)
        
        # Calculate bounding box
        all_vertices = []
        for room in room_meshes:
            all_vertices.extend([(v.x, v.y, v.z) for v in room.vertices])
        for wall in wall_meshes:
            all_vertices.extend([(v.x, v.y, v.z) for v in wall.vertices])
        
        if all_vertices:
            min_x = min(v[0] for v in all_vertices)
            max_x = max(v[0] for v in all_vertices)
            min_y = min(v[1] for v in all_vertices)
            max_y = max(v[1] for v in all_vertices)
            min_z = min(v[2] for v in all_vertices)
            max_z = max(v[2] for v in all_vertices)
        else:
            # Fallback to building dimensions
            building = scaled_coords.total_building_size
            min_x, max_x = 0, building.width_feet
            min_y, max_y = 0, building.length_feet
            min_z, max_z = 0, 9.0  # Default height
        
        bounding_box = {
            "min_x": min_x,
            "max_x": max_x,
            "min_y": min_y,
            "max_y": max_y,
            "min_z": min_z,
            "max_z": max_z
        }
        
        building_3d = Building3D(
            rooms=room_meshes,
            walls=wall_meshes,
            total_vertices=total_vertices,
            total_faces=total_faces,
            bounding_box=bounding_box,
            export_ready=True
        )
        
        logger.info(f"✅ Building assembled: {total_vertices} vertices, {total_faces} faces")
        logger.info(f"   Bounding box: {bounding_box}")
        
        return building_3d
    
    def _handle_job_error(self, job: ProcessingJob, error_message: str, failed_step: str) -> ProcessingJob:
        """
        Handle job errors and update job status.
        
        Args:
            job: ProcessingJob to update
            error_message: Error description
            failed_step: Step that failed
            
        Returns:
            Updated ProcessingJob with error status
        """
        job.status = ProcessingStatus.FAILED
        job.error_message = error_message
        job.current_step = failed_step
        job.completed_at = time.time()
        
        processing_time = job.total_processing_time()
        logger.error(f"❌ Job {job.job_id} failed at step '{failed_step}' after {processing_time:.2f}s")
        logger.error(f"   Error: {error_message}")
        
        return job
    
    def _detect_file_format(self, filename: str) -> FileFormat:
        """
        Detect file format from filename.
        
        Args:
            filename: Original filename
            
        Returns:
            FileFormat enum value
        """
        extension = filename.lower().split('.')[-1]
        
        if extension in ['jpg', 'jpeg']:
            return FileFormat.JPEG
        elif extension == 'png':
            return FileFormat.PNG
        elif extension == 'pdf':
            return FileFormat.PDF
        else:
            return FileFormat.JPEG  # Default fallback
    
    def get_job_status(self, job_id: str) -> Optional[ProcessingJob]:
        """
        Get job status by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            ProcessingJob if found, None otherwise
        """
        # TODO: Implement job storage/retrieval
        # For now, this is a placeholder
        logger.warning(f"Job status retrieval not yet implemented for job: {job_id}")
        return None
    
    def validate_export_formats(self, formats: List[str]) -> List[str]:
        """
        Validate and normalize export format list.
        
        Args:
            formats: List of format strings
            
        Returns:
            List of valid format strings
        """
        valid_formats = []
        supported_formats = [f.value for f in ExportFormat]
        
        for format_name in formats:
            format_lower = format_name.lower()
            if format_lower in supported_formats:
                valid_formats.append(format_lower)
            else:
                logger.warning(f"Unsupported export format: {format_name}")
        
        if not valid_formats:
            logger.info("No valid formats specified, using defaults: ['glb', 'obj', 'stl']")
            valid_formats = ['glb', 'obj', 'stl']
        
        return valid_formats


# Global service instance
_floorplan_processor = None


def get_floorplan_processor() -> FloorPlanProcessor:
    """
    Get or create global floor plan processor instance.
    
    Returns:
        FloorPlanProcessor instance
    """
    global _floorplan_processor
    if _floorplan_processor is None:
        _floorplan_processor = FloorPlanProcessor()
        logger.info("✅ Floor plan processor service initialized")
    return _floorplan_processor
