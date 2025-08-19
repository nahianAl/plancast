#!/usr/bin/env python3
"""
Simplified Test Pipeline for PlanCast 3D Model Generation

This is a TEMPORARY debugging pipeline that skips coordinate scaling and door/window
integration to isolate and fix core 3D generation issues.

IMPORTANT: This is for debugging only. After fixing core issues, we must integrate
back with the full enhanced pipeline.
"""

import time
import uuid
import os
from typing import List, Dict, Any
import logging

from models.data_structures import (
    ProcessingJob,
    ProcessingStatus,
    CubiCasaOutput,
    Building3D,
    MeshExportResult,
    ExportFormat
)
from services.cubicasa_service import CubiCasaService
from services.test_room_generator import SimpleRoomGenerator
from services.test_wall_generator import SimpleWallGenerator
from services.mesh_exporter import MeshExporter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleTestPipeline:
    """
    Simplified test pipeline for debugging 3D model generation.
    
    This pipeline skips:
    - Coordinate scaling (uses 1:1 pixel to foot ratio)
    - Door/window cutouts
    - Enhanced validation
    - Complex room polygons (uses bounding boxes only)
    
    Focus: Basic room and wall generation from CubiCasa output
    """
    
    def __init__(self):
        """Initialize simplified test pipeline."""
        self.cubicasa_service = CubiCasaService()
        self.room_generator = SimpleRoomGenerator()
        self.wall_generator = SimpleWallGenerator()
        self.mesh_exporter = MeshExporter()
        
        logger.info("🔧 Simplified test pipeline initialized")
    
    def process_test_image(self, 
                          file_content: bytes,
                          filename: str,
                          export_formats: List[str] = None) -> ProcessingJob:
        """
        Process a test image through the simplified pipeline.
        
        Args:
            file_content: Raw file bytes (JPG/PNG/PDF)
            filename: Original filename
            export_formats: List of export formats (default: ["glb", "obj"])
            
        Returns:
            ProcessingJob with test results
        """
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
        
        logger.info(f"🔧 Starting simplified test pipeline: {job_id}")
        logger.info(f"File: {filename} ({len(file_content)} bytes)")
        
        try:
            # Step 1: CubiCasa5K AI Processing
            job.current_step = "ai_processing"
            job.progress_percent = 25
            logger.info(f"🤖 Step 1: Running CubiCasa5K AI analysis")
            
            cubicasa_output = self.cubicasa_service.process_image(file_content, job.job_id)
            job.cubicasa_output = cubicasa_output
            
            logger.info(f"✅ AI processing completed: {len(cubicasa_output.room_bounding_boxes)} rooms detected")
            
            # Step 2: Simple Room Generation (NO SCALING)
            job.current_step = "simple_room_generation"
            job.progress_percent = 50
            logger.info(f"🏠 Step 2: Generating simple room meshes (1:1 pixel to foot)")
            
            # Handle empty CubiCasa detection gracefully
            if not cubicasa_output.room_bounding_boxes:
                logger.warning(f"⚠️ No rooms detected by CubiCasa - creating default room")
                # Create a default room using image dimensions
                default_room_bbox = {
                    "min_x": 0,
                    "min_y": 0, 
                    "max_x": 512,  # Default image width
                    "max_y": 512   # Default image height
                }
                cubicasa_output.room_bounding_boxes = {"default_room": default_room_bbox}
                logger.info(f"✅ Created default room: {default_room_bbox}")
            
            room_meshes = self.room_generator.generate_simple_rooms(cubicasa_output)
            logger.info(f"✅ Simple room generation completed: {len(room_meshes)} room meshes created")
            
            # Step 3: Simple Wall Generation (NO CUTOUTS)
            job.current_step = "simple_wall_generation"
            job.progress_percent = 75
            logger.info(f"🧱 Step 3: Generating simple wall meshes (no cutouts)")
            
            # Handle empty wall coordinates gracefully
            if not cubicasa_output.wall_coordinates:
                logger.warning(f"⚠️ No wall coordinates detected by CubiCasa - will generate from room boundaries")
            
            wall_meshes = self.wall_generator.generate_simple_walls(cubicasa_output)
            logger.info(f"✅ Simple wall generation completed: {len(wall_meshes)} wall meshes created")
            
            # Step 4: Simple Building Assembly
            job.current_step = "simple_building_assembly"
            job.progress_percent = 85
            logger.info(f"🏗️ Step 4: Assembling simple 3D building model")
            
            building_3d = self._assemble_simple_building(room_meshes, wall_meshes, cubicasa_output)
            job.building_3d = building_3d
            
            logger.info(f"✅ Simple building assembly completed: {building_3d.total_vertices} vertices, {building_3d.total_faces} faces")
            
            # Step 5: Basic 3D Model Export
            job.current_step = "basic_model_export"
            job.progress_percent = 95
            logger.info(f"📦 Step 5: Exporting basic 3D models")
            
            if export_formats is None:
                export_formats = ["glb", "obj"]  # Basic formats only
            
            output_dir = "output/test_models"
            os.makedirs(output_dir, exist_ok=True)
            
            export_result = self.mesh_exporter.export_building(
                building=building_3d,
                formats=export_formats,
                out_dir=output_dir
            )
            
            job.exported_files = export_result.files
            job.progress_percent = 100
            job.status = ProcessingStatus.COMPLETED
            job.completed_at = time.time()
            
            logger.info(f"✅ Basic model export completed: {len(export_result.files)} formats exported")
            
            # Log completion
            processing_time = job.total_processing_time()
            logger.info(f"🎉 Simplified test pipeline completed successfully!")
            logger.info(f"   Job ID: {job_id}")
            logger.info(f"   Processing time: {processing_time:.2f} seconds")
            logger.info(f"   Files exported: {list(export_result.files.keys())}")
            logger.info(f"   Total file size: {export_result.summary.get('total_size_bytes', 0)} bytes")
            
            return job
            
        except Exception as e:
            error_msg = f"Simplified test pipeline failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return self._handle_job_error(job, error_msg, "test_pipeline")
    
    def _assemble_simple_building(self, room_meshes: List, wall_meshes: List, cubicasa_output: CubiCasaOutput) -> Building3D:
        """
        Assemble room and wall meshes into a simple Building3D object.
        
        Args:
            room_meshes: List of simple Room3D objects
            wall_meshes: List of simple Wall3D objects
            cubicasa_output: Original CubiCasa output for metadata
            
        Returns:
            Building3D object ready for export
        """
        # Calculate total geometry stats
        total_vertices = sum(len(room.vertices) for room in room_meshes) + sum(len(wall.vertices) for wall in wall_meshes)
        total_faces = sum(len(room.faces) for room in room_meshes) + sum(len(wall.faces) for wall in wall_meshes)
        
        # Calculate bounding box from room bounding boxes (1:1 pixel to foot)
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
            # Fallback to image dimensions (1:1 pixel to foot)
            min_x, max_x = 0, 512  # Default image width
            min_y, max_y = 0, 512  # Default image height
            min_z, max_z = 0, 9.0  # Default height
        
        bounding_box = {
            "min_x": min_x,
            "max_x": max_x,
            "min_y": min_y,
            "max_y": max_y,
            "min_z": min_z,
            "max_z": max_z
        }
        
        # Create simple building metadata
        metadata = {
            "pipeline_type": "simplified_test",
            "scale_factor": 1.0,  # 1:1 pixel to foot
            "room_count": len(room_meshes),
            "wall_count": len(wall_meshes),
            "total_vertices": total_vertices,
            "total_faces": total_faces,
            "bounding_box": bounding_box,
            "cubicasa_rooms": list(cubicasa_output.room_bounding_boxes.keys()),
            "test_notes": "This is a simplified test pipeline - no coordinate scaling or cutouts"
        }
        
        return Building3D(
            rooms=room_meshes,
            walls=wall_meshes,
            total_vertices=total_vertices,
            total_faces=total_faces,
            bounding_box=bounding_box,
            metadata=metadata,
            units="feet"
        )
    
    def _detect_file_format(self, filename: str) -> str:
        """Detect file format from filename."""
        ext = filename.lower().split('.')[-1]
        if ext in ['jpg', 'jpeg']:
            return 'jpg'
        elif ext == 'png':
            return 'png'
        elif ext == 'pdf':
            return 'pdf'
        else:
            return 'unknown'
    
    def _handle_job_error(self, job: ProcessingJob, error_msg: str, step: str) -> ProcessingJob:
        """Handle job errors in simplified pipeline."""
        job.status = ProcessingStatus.FAILED
        job.error_message = error_msg
        job.current_step = step
        job.completed_at = time.time()
        
        logger.error(f"❌ Simplified test pipeline failed at step '{step}': {error_msg}")
        return job


def main():
    """Test the simplified pipeline with a sample image."""
    print("🔧 PlanCast Simplified Test Pipeline")
    print("=" * 50)
    print("This is a TEMPORARY debugging pipeline.")
    print("After fixing core issues, we must integrate back with the full pipeline.")
    print("=" * 50)
    
    # Create test pipeline
    pipeline = SimpleTestPipeline()
    
    # Test with a sample image (you would provide an actual image file)
    print("⚠️  To test this pipeline, provide an actual floor plan image file.")
    print("   Example usage:")
    print("   with open('test_floorplan.jpg', 'rb') as f:")
    print("       result = pipeline.process_test_image(f.read(), 'test_floorplan.jpg')")
    
    print("\n🔧 Simplified test pipeline ready for debugging!")


if __name__ == "__main__":
    main()
