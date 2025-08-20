"""
Temporary Test Pipeline for PlanCast Debugging

This module contains a simplified pipeline for processing floor plan images.
It is intended for debugging purposes only and should be removed once the
main processing pipeline is stable.

Key features of this test pipeline:
- Skips coordinate scaling
- Bypasses door/window cutout generation
- Uses simplified room and wall generators

"""

from services.test_room_generator import SimpleRoomGenerator
from services.test_wall_generator import SimpleWallGenerator
from services.mesh_exporter import MeshExporter
from models.data_structures import ProcessingJob, ProcessingStatus
import time

class SimpleTestPipeline:
    """A simplified pipeline for testing and debugging."""

    def __init__(self):
        self.room_generator = SimpleRoomGenerator()
        self.wall_generator = SimpleWallGenerator()
        self.mesh_exporter = MeshExporter()

    def process_test_image(self, file_content: bytes, filename: str, export_formats: list[str]) -> ProcessingJob:
        job = ProcessingJob(job_id="test_job", status=ProcessingStatus.PROCESSING)
        start_time = time.time()

        try:
            # This is a placeholder for the actual CubiCasa output
            cubicasa_output = {"wall_coordinates": [], "room_bounding_boxes": {}}
            
            rooms = self.room_generator.generate_rooms(cubicasa_output)
            walls = self.wall_generator.generate_walls(cubicasa_output)
            
            exported_files = self.mesh_exporter.export_meshes(
                rooms=rooms,
                walls=walls,
                job_id="test_job",
                formats=export_formats
            )
            
            job.status = ProcessingStatus.COMPLETED
            job.exported_files = exported_files
            
        except Exception as e:
            job.status = ProcessingStatus.FAILED
            job.error_message = str(e)
            
        job.processing_time_seconds = time.time() - start_time
        return job
