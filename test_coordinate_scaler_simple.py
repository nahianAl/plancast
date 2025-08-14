#!/usr/bin/env python3
"""
Simplified test for Coordinate Scaler service.
Tests Task 2: Converting CubiCasa5K pixel coordinates to real-world feet.

This test bypasses file processing dependencies and focuses on coordinate scaling logic.
"""

import sys
import os
import time
import uuid
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.coordinate_scaler import get_coordinate_scaler, CoordinateScaler
from models.data_structures import (
    CubiCasaOutput,
    ScaleReference,
    ScaledCoordinates,
    ProcessingJob,
    ProcessingStatus
)
from utils.logger import get_logger

logger = get_logger("test_coordinate_scaler_simple")


class SimpleCoordinateScalerTest:
    """
    Simplified test suite for coordinate scaling service.
    Bypasses file processing dependencies.
    """
    
    def __init__(self):
        """Initialize test suite."""
        self.coordinate_scaler = get_coordinate_scaler()
        self.test_job_id = f"test_scaling_{uuid.uuid4().hex[:8]}"
        
    def create_mock_cubicasa_output(self) -> CubiCasaOutput:
        """
        Create mock CubiCasa5K output for testing.
        
        Returns:
            Mock CubiCasaOutput with realistic test data
        """
        logger.info("Creating mock CubiCasa5K output for testing...")
        
        # Mock wall coordinates (simplified floor plan)
        wall_coordinates = [
            (50, 50), (200, 50), (200, 150), (50, 150), (50, 50),  # Outer walls
            (125, 50), (125, 150),  # Interior wall
        ]
        
        # Mock room bounding boxes
        room_bounding_boxes = {
            "kitchen": {
                "min_x": 50, "max_x": 125, "min_y": 50, "max_y": 150
            },
            "living_room": {
                "min_x": 125, "max_x": 200, "min_y": 50, "max_y": 150
            }
        }
        
        # Mock confidence scores
        confidence_scores = {
            "kitchen": 0.89,
            "living_room": 0.76
        }
        
        # Create CubiCasaOutput
        cubicasa_output = CubiCasaOutput(
            wall_coordinates=wall_coordinates,
            room_bounding_boxes=room_bounding_boxes,
            image_dimensions=(250, 200),  # 250x200 pixel image
            confidence_scores=confidence_scores,
            processing_time=0.01
        )
        
        logger.info(f"✅ Mock data created:")
        logger.info(f"   - Wall points: {len(wall_coordinates)}")
        logger.info(f"   - Rooms: {list(room_bounding_boxes.keys())}")
        logger.info(f"   - Image size: {cubicasa_output.image_dimensions}")
        
        return cubicasa_output
    
    def test_smart_room_suggestions(self, cubicasa_output: CubiCasaOutput) -> None:
        """Test smart room suggestion logic."""
        logger.info("="*60)
        logger.info("Testing Smart Room Suggestions")
        logger.info("="*60)
        
        suggestions = self.coordinate_scaler.get_smart_room_suggestions(cubicasa_output)
        
        logger.info("📊 Smart room suggestions:")
        for i, suggestion in enumerate(suggestions):
            logger.info(f"   {i+1}. {suggestion['room_name']}:")
            logger.info(f"      - Priority: {suggestion['priority']}")
            logger.info(f"      - Confidence: {suggestion['confidence']:.2f}")
            logger.info(f"      - Recommended: {suggestion['is_recommended']}")
            logger.info(f"      - Suggested dimension: {suggestion['suggested_dimension']}")
        
        # Validate suggestions
        assert len(suggestions) > 0, "No room suggestions generated"
        assert any(s['is_recommended'] for s in suggestions), "No recommended room found"
        
        logger.info("✅ Smart room suggestions test passed")
    
    def test_scale_factor_calculation(self, cubicasa_output: CubiCasaOutput) -> ScaleReference:
        """Test scale factor calculation."""
        logger.info("="*60)
        logger.info("Testing Scale Factor Calculation")
        logger.info("="*60)
        
        # Test with kitchen width
        room_type = "kitchen"
        dimension_type = "width"
        real_world_feet = 12.0  # Kitchen is 12 feet wide
        
        logger.info(f"📏 Testing scale calculation:")
        logger.info(f"   - Room: {room_type}")
        logger.info(f"   - Dimension: {dimension_type}")
        logger.info(f"   - Real world: {real_world_feet} feet")
        
        # Calculate scale factor
        scale_ref = self.coordinate_scaler.calculate_scale_factor(
            cubicasa_output=cubicasa_output,
            room_type=room_type,
            dimension_type=dimension_type,
            real_world_feet=real_world_feet
        )
        
        # Validate scale reference
        assert isinstance(scale_ref, ScaleReference), "Invalid scale reference type"
        assert scale_ref.scale_factor > 0, "Scale factor must be positive"
        assert scale_ref.room_type == room_type, "Room type mismatch"
        assert scale_ref.dimension_type == dimension_type, "Dimension type mismatch"
        assert scale_ref.real_world_feet == real_world_feet, "Real world measurement mismatch"
        
        logger.info(f"✅ Scale factor calculation successful:")
        logger.info(f"   - Scale factor: {scale_ref.scale_factor:.2f} pixels/foot")
        logger.info(f"   - Pixel measurement: {scale_ref.pixel_measurement:.1f} pixels")
        logger.info(f"   - Real world: {scale_ref.real_world_feet} feet")
        
        return scale_ref
    
    def test_coordinate_scaling(self, cubicasa_output: CubiCasaOutput) -> ScaledCoordinates:
        """Test complete coordinate scaling."""
        logger.info("="*60)
        logger.info("Testing Complete Coordinate Scaling")
        logger.info("="*60)
        
        # Use kitchen width as reference
        room_type = "kitchen"
        dimension_type = "width"
        real_world_feet = 12.0
        
        logger.info(f"📏 Scaling coordinates using {room_type} {dimension_type}: {real_world_feet} feet")
        
        # Process scaling request
        start_time = time.time()
        scaled_coords = self.coordinate_scaler.process_scaling_request(
            cubicasa_output=cubicasa_output,
            room_type=room_type,
            dimension_type=dimension_type,
            real_world_feet=real_world_feet,
            job_id=self.test_job_id
        )
        scaling_time = time.time() - start_time
        
        # Validate scaled coordinates
        assert isinstance(scaled_coords, ScaledCoordinates), "Invalid scaled coordinates type"
        assert len(scaled_coords.walls_feet) == len(cubicasa_output.wall_coordinates), \
            "Wall count mismatch after scaling"
        assert len(scaled_coords.rooms_feet) == len(cubicasa_output.room_bounding_boxes), \
            "Room count mismatch after scaling"
        
        logger.info(f"✅ Coordinate scaling successful:")
        logger.info(f"   - Scaling time: {scaling_time:.3f}s")
        logger.info(f"   - Scale factor: {scaled_coords.scale_reference.scale_factor:.2f} pixels/foot")
        
        # Display building dimensions
        building = scaled_coords.total_building_size
        logger.info(f"\n🏠 Building dimensions:")
        logger.info(f"   - Total size: {building.width_feet:.1f}' × {building.length_feet:.1f}'")
        logger.info(f"   - Total area: {building.area_sqft:.0f} sq ft")
        
        # Display room dimensions
        logger.info(f"\n🏘️ Room dimensions (feet):")
        for room_name, dims in scaled_coords.rooms_feet.items():
            logger.info(f"   {room_name}:")
            logger.info(f"      - Size: {dims['width_feet']:.1f}' × {dims['length_feet']:.1f}'")
            logger.info(f"      - Area: {dims['area_sqft']:.0f} sq ft")
        
        # Sample wall coordinates
        logger.info(f"\n🧱 Sample wall coordinates (first 5 points in feet):")
        for i, (x, y) in enumerate(scaled_coords.walls_feet[:5]):
            logger.info(f"   Point {i}: ({x:.2f}, {y:.2f})")
        
        return scaled_coords
    
    def test_validation(self, cubicasa_output: CubiCasaOutput) -> None:
        """Test input validation."""
        logger.info("="*60)
        logger.info("Testing Input Validation")
        logger.info("="*60)
        
        # Test valid input
        valid_result = self.coordinate_scaler.validate_scaling_input(
            cubicasa_output=cubicasa_output,
            room_type="kitchen",
            dimension_type="width",
            real_world_feet=12.0
        )
        assert valid_result['is_valid'], f"Valid input failed validation: {valid_result['errors']}"
        logger.info("✅ Valid input validation passed")
        
        # Test invalid room
        invalid_room = self.coordinate_scaler.validate_scaling_input(
            cubicasa_output=cubicasa_output,
            room_type="nonexistent_room",
            dimension_type="width",
            real_world_feet=12.0
        )
        assert not invalid_room['is_valid'], "Invalid room should fail validation"
        logger.info("✅ Invalid room validation passed")
        
        # Test invalid dimension
        invalid_dim = self.coordinate_scaler.validate_scaling_input(
            cubicasa_output=cubicasa_output,
            room_type="kitchen",
            dimension_type="invalid_dimension",
            real_world_feet=12.0
        )
        assert not invalid_dim['is_valid'], "Invalid dimension should fail validation"
        logger.info("✅ Invalid dimension validation passed")
        
        # Test invalid measurement
        invalid_measure = self.coordinate_scaler.validate_scaling_input(
            cubicasa_output=cubicasa_output,
            room_type="kitchen",
            dimension_type="width",
            real_world_feet=-5.0
        )
        assert not invalid_measure['is_valid'], "Invalid measurement should fail validation"
        logger.info("✅ Invalid measurement validation passed")
        
        logger.info("✅ All validation tests passed")
    
    def run_all_tests(self) -> bool:
        """Run all coordinate scaler tests."""
        logger.info("🚀 Starting Coordinate Scaler Tests")
        logger.info("="*60)
        
        try:
            # Create mock data
            cubicasa_output = self.create_mock_cubicasa_output()
            
            # Run tests
            self.test_smart_room_suggestions(cubicasa_output)
            self.test_scale_factor_calculation(cubicasa_output)
            self.test_coordinate_scaling(cubicasa_output)
            self.test_validation(cubicasa_output)
            
            logger.info("="*60)
            logger.info("🎉 ALL TESTS PASSED! Coordinate scaler is working correctly.")
            logger.info("="*60)
            return True
            
        except Exception as e:
            logger.error(f"❌ Test failed: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False


def main():
    """Main test runner."""
    test_suite = SimpleCoordinateScalerTest()
    success = test_suite.run_all_tests()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
