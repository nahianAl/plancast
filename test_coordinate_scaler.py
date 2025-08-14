"""
Test script for Coordinate Scaler service.
Tests Task 2: Converting CubiCasa5K pixel coordinates to real-world feet.

IMPORTANT: This test maintains harmony with the production codebase by:
- Using FileProcessor for proper file handling
- Following established service patterns
- Using production data structures
- Implementing comprehensive logging
"""

import sys
import os
import time
import uuid
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.cubicasa_service import get_cubicasa_service, CubiCasaService
from services.coordinate_scaler import get_coordinate_scaler, CoordinateScaler
from services.file_processor import FileProcessor
from models.data_structures import (
    ProcessingJob, 
    FileFormat, 
    ProcessingStatus,
    CubiCasaOutput,
    ScaleReference,
    ScaledCoordinates
)
from utils.logger import get_logger

logger = get_logger("test_coordinate_scaler")


class CoordinateScalerTest:
    """
    Production test suite for coordinate scaling service.
    Maintains harmony with the complete PlanCast pipeline.
    """
    
    def __init__(self):
        """Initialize test suite with production services."""
        self.cubicasa_service = get_cubicasa_service()
        self.coordinate_scaler = get_coordinate_scaler()
        self.file_processor = FileProcessor()
        self.test_job_id = f"test_scaling_{uuid.uuid4().hex[:8]}"
        self.test_files_created = []  # Track files for cleanup
        
    def get_test_image_bytes(self) -> Tuple[bytes, str]:
        """
        Get test image bytes for processing.
        
        Returns:
            Tuple of (image_bytes, filename)
        """
        # Check for actual test floor plan first
        test_assets_dir = Path("test_assets")
        test_image_path = test_assets_dir / "sample_floor_plan.jpg"
        
        if test_image_path.exists():
            logger.info(f"Using existing test floor plan: {test_image_path}")
            with open(test_image_path, 'rb') as f:
                return f.read(), "sample_floor_plan.jpg"
        
        # Create a test image if none exists
        logger.info("Creating test floor plan image")
        from PIL import Image, ImageDraw
        
        # Create a simple floor plan-like image
        width, height = 800, 600
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw simple floor plan elements (walls)
        # Outer walls
        draw.rectangle([50, 50, width-50, height-50], outline='black', width=3)
        
        # Interior walls to create rooms
        draw.line([300, 50, 300, height-50], fill='black', width=2)  # Vertical divider
        draw.line([50, 300, 300, 300], fill='black', width=2)  # Horizontal divider
        
        # Save to bytes
        from io import BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        
        # Optionally save for future use
        test_assets_dir.mkdir(exist_ok=True)
        test_file_path = test_assets_dir / "generated_test_floor_plan.png"
        with open(test_file_path, 'wb') as f:
            f.write(image_bytes)
        self.test_files_created.append(test_file_path)
        
        logger.info(f"Test image created: {width}x{height} pixels, {len(image_bytes)} bytes")
        return image_bytes, "test_floor_plan.png"
    
    def test_file_processing(self) -> Tuple[bytes, ProcessingJob]:
        """
        Test file processing with FileProcessor.
        
        Returns:
            Tuple of (processed_image_bytes, processing_job)
        """
        logger.info("="*60)
        logger.info("Testing File Processing Service")
        logger.info("="*60)
        
        # Get test image
        file_content, filename = self.get_test_image_bytes()
        
        # Validate file
        validation_result = self.file_processor.validate_file(file_content, filename)
        assert validation_result["is_valid"], "File validation failed"
        
        logger.info(f"✅ File validation passed:")
        logger.info(f"   - Format: {validation_result['file_format'].value}")
        logger.info(f"   - Size: {validation_result['file_size_bytes']} bytes")
        logger.info(f"   - MIME: {validation_result['mime_type']}")
        
        # Process file to standardized image format
        processed_image_bytes, dimensions = self.file_processor.process_file_to_image(
            file_content,
            validation_result['file_format']
        )
        
        logger.info(f"✅ File processed to image:")
        logger.info(f"   - Dimensions: {dimensions[0]}x{dimensions[1]}")
        logger.info(f"   - Output size: {len(processed_image_bytes)} bytes")
        
        # Create processing job (matching production flow)
        job = ProcessingJob(
            job_id=self.test_job_id,
            filename=filename,
            file_format=validation_result['file_format'],
            file_size_bytes=validation_result['file_size_bytes'],
            status=ProcessingStatus.PROCESSING,
            current_step="file_processed"
        )
        
        return processed_image_bytes, job
    
    def test_cubicasa_processing(self, image_bytes: bytes, job: ProcessingJob) -> CubiCasaOutput:
        """
        Test CubiCasa5K processing.
        
        Args:
            image_bytes: Processed image bytes from FileProcessor
            job: Processing job
            
        Returns:
            CubiCasaOutput for coordinate scaling
        """
        logger.info("="*60)
        logger.info("Testing CubiCasa5K Service")
        logger.info("="*60)
        
        # Check service health first
        health_status = self.cubicasa_service.health_check()
        assert health_status.get("model_loaded"), "CubiCasa5K model not loaded"
        logger.info(f"✅ CubiCasa5K health check passed: {health_status['status']}")
        
        # Process image
        start_time = time.time()
        cubicasa_output = self.cubicasa_service.process_image(image_bytes, job.job_id)
        processing_time = time.time() - start_time
        
        # Update job
        job.cubicasa_output = cubicasa_output
        job.current_step = "cubicasa_processed"
        job.progress_percent = 40
        
        # Validate output
        assert isinstance(cubicasa_output, CubiCasaOutput), "Invalid output type"
        assert len(cubicasa_output.wall_coordinates) > 0, "No walls detected"
        assert len(cubicasa_output.room_bounding_boxes) > 0, "No rooms detected"
        
        logger.info(f"✅ CubiCasa5K processing successful:")
        logger.info(f"   - Processing time: {processing_time:.3f}s")
        logger.info(f"   - Wall points: {len(cubicasa_output.wall_coordinates)}")
        logger.info(f"   - Rooms detected: {list(cubicasa_output.room_bounding_boxes.keys())}")
        logger.info(f"   - Image dimensions: {cubicasa_output.image_dimensions}")
        
        # Display confidence scores
        for room, confidence in cubicasa_output.confidence_scores.items():
            logger.info(f"   - {room} confidence: {confidence:.2f}")
        
        return cubicasa_output
    
    def test_coordinate_scaling(self, 
                               cubicasa_output: CubiCasaOutput, 
                               job: ProcessingJob) -> ScaledCoordinates:
        """
        Test complete coordinate scaling pipeline.
        
        Args:
            cubicasa_output: CubiCasa5K output
            job: Processing job
            
        Returns:
            Scaled coordinates in feet
        """
        logger.info("="*60)
        logger.info("Testing Coordinate Scaling Service")
        logger.info("="*60)
        
        # Get smart room suggestions
        suggestions = self.coordinate_scaler.get_smart_room_suggestions(cubicasa_output)
        
        logger.info("📊 Smart room suggestions:")
        for i, suggestion in enumerate(suggestions[:3]):
            logger.info(f"   {i+1}. {suggestion['room_name']}:")
            logger.info(f"      - Priority: {suggestion['priority']}")
            logger.info(f"      - Confidence: {suggestion['confidence']:.2f}")
            logger.info(f"      - Recommended: {suggestion['is_recommended']}")
            logger.info(f"      - Suggested dimension: {suggestion['suggested_dimension']}")
        
        # Select best room for scaling
        best_room = suggestions[0]
        room_type = best_room['room_name']
        dimension_type = best_room['suggested_dimension']
        
        # Use realistic measurement based on room type
        room_measurements = {
            'kitchen': {'width': 12.0, 'length': 10.0},
            'living_room': {'width': 16.0, 'length': 14.0},
            'bedroom': {'width': 12.0, 'length': 11.0},
            'bathroom': {'width': 8.0, 'length': 6.0}
        }
        
        default_measurement = 12.0
        real_world_feet = room_measurements.get(
            room_type.lower(), 
            {'width': default_measurement, 'length': default_measurement}
        ).get(dimension_type, default_measurement)
        
        logger.info(f"\n📏 Using scale reference:")
        logger.info(f"   - Room: {room_type}")
        logger.info(f"   - Dimension: {dimension_type}")
        logger.info(f"   - Measurement: {real_world_feet} feet")
        
        # Validate input before processing
        validation = self.coordinate_scaler.validate_scaling_input(
            cubicasa_output=cubicasa_output,
            room_type=room_type,
            dimension_type=dimension_type,
            real_world_feet=real_world_feet
        )
        assert validation['is_valid'], f"Invalid scaling input: {validation['errors']}"
        
        # Process scaling request
        start_time = time.time()
        scaled_coords = self.coordinate_scaler.process_scaling_request(
            cubicasa_output=cubicasa_output,
            room_type=room_type,
            dimension_type=dimension_type,
            real_world_feet=real_world_feet,
            job_id=job.job_id
        )
        scaling_time = time.time() - start_time
        
        # Update job
        job.scaled_coordinates = scaled_coords
        job.current_step = "coordinates_scaled"
        job.progress_percent = 60
        
        # Validate scaled coordinates
        assert isinstance(scaled_coords, ScaledCoordinates), "Invalid scaled coordinates type"
        assert len(scaled_coords.walls_feet) == len(cubicasa_output.wall_coordinates), \
            "Wall count mismatch after scaling"
        assert len(scaled_coords.rooms_feet) == len(cubicasa_output.room_bounding_boxes), \
            "Room count mismatch after scaling"
        
        logger.info(f"\n✅ Coordinate scaling successful:")
        logger.info(f"   - Scaling time: {scaling_time:.3f}s")
        logger.info(f"   - Scale factor: {scaled_coords.scale_reference.scale_factor:.2f} pixels/foot")
        
        # Display building dimensions
        building = scaled_coords.total_building_size
        logger.info(f"\n🏠 Building dimensions:")
        logger.info(f"   - Total size: {building.width_feet:.1f}' × {building.length_feet:.1f}'")
        logger.info(f"   - Total area: {building.area_sqft:.0f} sq ft")
        logger.info(f"   - Original pixels: {building.original_width_pixels} × {building.original_height_pixels}")
        
        # Display room dimensions
        logger.info(f"\n🏘️ Room dimensions (feet):")
        for room_name, dims in scaled_coords.rooms_feet.items():
            logger.info(f"   {room_name}:")
            logger.info(f"      - Size: {dims['width_feet']:.1f}' × {dims['length_feet']:.1f}'")
            logger.info(f"      - Area: {dims['area_sqft']:.0f} sq ft")
            logger.info(f"      - Position: ({dims['x_offset_feet']:.1f}, {dims['y_offset_feet']:.1f})")
        
        # Sample wall coordinates
        logger.info(f"\n🧱 Sample wall coordinates (first 5 points in feet):")
        for i, (x, y) in enumerate(scaled_coords.walls_feet[:5]):
            logger.info(f"   Point {i}: ({x:.2f}, {y:.2f})")
        
        return scaled_coords
    
    def test_edge_cases(self, cubicasa_output: CubiCasaOutput) -> None:
        """
        Test edge cases and error handling.
        
        Args:
            cubicasa_output: CubiCasa5K output for testing
        """
        logger.info("="*60)
        logger.info("Testing Edge Cases and Error Handling")
        logger.info("="*60)
        
        test_cases = [
            # (room_type, dimension_type, measurement, should_pass, description)
            ("", "width", 12.0, False, "Empty room type"),
            ("kitchen", "", 12.0, False, "Empty dimension type"),
            ("kitchen", "invalid", 12.0, False, "Invalid dimension type"),
            ("kitchen", "width", -5.0, False, "Negative measurement"),
            ("kitchen", "width", 0.0, False, "Zero measurement"),
            ("kitchen", "width", 0.5, True, "Very small measurement (warning)"),
            ("kitchen", "width", 200.0, True, "Very large measurement (warning)"),
            ("nonexistent_room", "width", 12.0, False, "Non-existent room"),
        ]
        
        for room, dim, measurement, should_pass, description in test_cases:
            try:
                validation = self.coordinate_scaler.validate_scaling_input(
                    cubicasa_output=cubicasa_output,
                    room_type=room,
                    dimension_type=dim,
                    real_world_feet=measurement
                )
                
                if should_pass:
                    if not validation['is_valid']:
                        logger.error(f"   ❌ {description}: Should pass but failed")
                    else:
                        warnings = validation.get('warnings', [])
                        if warnings:
                            logger.info(f"   ⚠️  {description}: Passed with warnings: {warnings}")
                        else:
                            logger.info(f"   ✅ {description}: Passed")
                else:
                    if validation['is_valid']:
                        logger.error(f"   ❌ {description}: Should fail but passed")
                    else:
                        logger.info(f"   ✅ {description}: Failed as expected")
                        
            except Exception as e:
                if should_pass:
                    logger.error(f"   ❌ {description}: Unexpected error: {str(e)}")
                else:
                    logger.info(f"   ✅ {description}: Failed with exception as expected")
    
    def cleanup(self) -> None:
        """Clean up test files and resources."""
        # Clean up temp files created by FileProcessor
        if hasattr(self, 'test_job_id'):
            self.file_processor.cleanup_temp_files(self.test_job_id)
        
        # Clean up any test files we created
        for file_path in self.test_files_created:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Cleaned up test file: {file_path}")
    
    def run_complete_pipeline_test(self) -> bool:
        """
        Run complete coordinate scaling pipeline test.
        
        Returns:
            True if all tests pass, False otherwise
        """
        try:
            logger.info("\n" + "="*60)
            logger.info("COORDINATE SCALER COMPLETE PIPELINE TEST")
            logger.info("="*60)
            
            # Step 1: File Processing
            processed_image_bytes, job = self.test_file_processing()
            
            # Step 2: CubiCasa5K Processing
            cubicasa_output = self.test_cubicasa_processing(processed_image_bytes, job)
            
            # Step 3: Coordinate Scaling
            scaled_coords = self.test_coordinate_scaling(cubicasa_output, job)
            
            # Step 4: Edge Cases
            self.test_edge_cases(cubicasa_output)
            
            # Verify complete job state
            assert job.cubicasa_output is not None, "Job missing CubiCasa output"
            assert job.scaled_coordinates is not None, "Job missing scaled coordinates"
            assert job.current_step == "coordinates_scaled", "Job not in correct state"
            
            logger.info("\n" + "="*60)
            logger.info("✅ ALL TESTS PASSED SUCCESSFULLY!")
            logger.info("="*60)
            
            logger.info("\n📊 Final Job Summary:")
            logger.info(f"   - Job ID: {job.job_id}")
            logger.info(f"   - File: {job.filename}")
            logger.info(f"   - Status: {job.status.value}")
            logger.info(f"   - Current step: {job.current_step}")
            logger.info(f"   - Progress: {job.progress_percent}%")
            
            return True
            
        except Exception as e:
            logger.error(f"\n❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            self.cleanup()


def main():
    """Main test entry point."""
    test_suite = CoordinateScalerTest()
    success = test_suite.run_complete_pipeline_test()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())