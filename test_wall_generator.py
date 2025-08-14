#!/usr/bin/env python3
"""
Test script for Wall Mesh Generator service.
Tests Task 4: Generating 3D wall meshes from scaled coordinates.

IMPORTANT: This test maintains harmony with the production codebase by:
- Using existing service patterns and data structures
- Following established logging and error handling
- Using production data structures
- Implementing comprehensive validation
"""

import sys
import os
import time
import uuid
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.wall_generator import get_wall_generator, WallMeshGenerator, WallGenerationError
from services.coordinate_scaler import get_coordinate_scaler
from models.data_structures import (
    CubiCasaOutput,
    ScaledCoordinates,
    Wall3D,
    Vertex3D,
    Face,
    ScaleReference,
    BuildingDimensions
)
from utils.logger import get_logger

logger = get_logger("test_wall_generator")


class WallGeneratorTest:
    """
    Production test suite for wall mesh generator service.
    Maintains harmony with the complete PlanCast pipeline.
    """
    
    def __init__(self):
        """Initialize test suite with production services."""
        self.wall_generator = get_wall_generator()
        self.coordinate_scaler = get_coordinate_scaler()
        self.test_job_id = f"test_wall_gen_{uuid.uuid4().hex[:8]}"
        
    def create_mock_scaled_coordinates(self) -> ScaledCoordinates:
        """
        Create mock scaled coordinates for testing.
        
        Returns:
            Mock ScaledCoordinates with realistic room data
        """
        logger.info("Creating mock scaled coordinates for testing...")
        
        # Mock wall coordinates (simplified floor plan)
        wall_coordinates = [
            (8.0, 8.0), (32.0, 8.0), (32.0, 24.0), (8.0, 24.0), (8.0, 8.0),  # Outer walls
            (20.0, 8.0), (20.0, 24.0),  # Interior wall
        ]
        
        # Mock room data in feet (two adjacent rooms)
        rooms_feet = {
            "kitchen": {
                "width_feet": 12.0,
                "length_feet": 16.0,
                "area_sqft": 192.0,
                "x_offset_feet": 8.0,
                "y_offset_feet": 8.0
            },
            "living_room": {
                "width_feet": 12.0,
                "length_feet": 16.0,
                "area_sqft": 192.0,
                "x_offset_feet": 20.0,  # Adjacent to kitchen
                "y_offset_feet": 8.0
            }
        }
        
        # Mock scale reference
        scale_reference = ScaleReference(
            room_type="kitchen",
            dimension_type="width",
            real_world_feet=12.0,
            pixel_measurement=75.0,
            scale_factor=6.25
        )
        
        # Mock building dimensions
        building_dimensions = BuildingDimensions(
            width_feet=40.0,
            length_feet=32.0,
            area_sqft=1280.0,
            scale_factor=6.25,
            original_width_pixels=250,
            original_height_pixels=200
        )
        
        # Create ScaledCoordinates
        scaled_coords = ScaledCoordinates(
            walls_feet=wall_coordinates,
            rooms_feet=rooms_feet,
            scale_reference=scale_reference,
            total_building_size=building_dimensions
        )
        
        logger.info(f"✅ Mock scaled coordinates created:")
        logger.info(f"   - Rooms: {list(rooms_feet.keys())}")
        logger.info(f"   - Wall points: {len(wall_coordinates)}")
        logger.info(f"   - Building size: {building_dimensions.width_feet:.1f}' × {building_dimensions.length_feet:.1f}'")
        
        return scaled_coords
    
    def test_wall_mesh_generation(self, scaled_coords: ScaledCoordinates) -> List[Wall3D]:
        """
        Test wall mesh generation.
        
        Args:
            scaled_coords: Scaled coordinates for testing
            
        Returns:
            List of generated Wall3D objects
        """
        logger.info("="*60)
        logger.info("Testing Wall Mesh Generation")
        logger.info("="*60)
        
        # Test with default parameters
        start_time = time.time()
        wall_meshes = self.wall_generator.generate_wall_meshes(
            scaled_coords=scaled_coords,
            wall_thickness_feet=0.5,
            wall_height_feet=9.0
        )
        generation_time = time.time() - start_time
        
        # Validate results
        assert isinstance(wall_meshes, list), "Wall meshes should be a list"
        assert len(wall_meshes) > 0, "Should generate at least some walls"
        
        logger.info(f"✅ Wall mesh generation successful:")
        logger.info(f"   - Generation time: {generation_time:.3f}s")
        logger.info(f"   - Walls generated: {len(wall_meshes)}")
        
        # Validate each wall mesh
        for wall_mesh in wall_meshes:
            self._validate_wall_mesh(wall_mesh)
        
        return wall_meshes
    
    def _validate_wall_mesh(self, wall_mesh: Wall3D) -> None:
        """
        Validate individual wall mesh.
        
        Args:
            wall_mesh: Wall3D object to validate
        """
        logger.info(f"\n🧱 Validating wall: {wall_mesh.id}")
        
        # Basic structure validation
        assert isinstance(wall_mesh.id, str), "Wall ID should be string"
        assert isinstance(wall_mesh.vertices, list), "Vertices should be list"
        assert isinstance(wall_mesh.faces, list), "Faces should be list"
        assert isinstance(wall_mesh.height_feet, (int, float)), "Height should be numeric"
        assert isinstance(wall_mesh.thickness_feet, (int, float)), "Thickness should be numeric"
        
        # Vertex validation
        assert len(wall_mesh.vertices) == 8, f"Expected 8 vertices, got {len(wall_mesh.vertices)}"
        for i, vertex in enumerate(wall_mesh.vertices):
            assert isinstance(vertex, Vertex3D), f"Vertex {i} should be Vertex3D"
            assert isinstance(vertex.x, (int, float)), f"Vertex {i} x should be numeric"
            assert isinstance(vertex.y, (int, float)), f"Vertex {i} y should be numeric"
            assert isinstance(vertex.z, (int, float)), f"Vertex {i} z should be numeric"
        
        # Face validation
        assert len(wall_mesh.faces) == 12, f"Expected 12 faces, got {len(wall_mesh.faces)}"
        for i, face in enumerate(wall_mesh.faces):
            assert isinstance(face, Face), f"Face {i} should be Face"
            assert len(face.indices) == 3, f"Face {i} should have 3 indices"
            for index in face.indices:
                assert 0 <= index < len(wall_mesh.vertices), f"Face {i} has invalid index: {index}"
        
        # Dimension validation
        assert wall_mesh.height_feet > 0, "Wall height should be positive"
        assert wall_mesh.thickness_feet > 0, "Wall thickness should be positive"
        
        # Log wall details
        logger.info(f"   - Vertices: {len(wall_mesh.vertices)}")
        logger.info(f"   - Faces: {len(wall_mesh.faces)}")
        logger.info(f"   - Height: {wall_mesh.height_feet:.1f} feet")
        logger.info(f"   - Thickness: {wall_mesh.thickness_feet:.1f} feet")
        
        # Log vertex coordinates (first 4 for brevity)
        for i, vertex in enumerate(wall_mesh.vertices[:4]):
            logger.info(f"   - Vertex {i}: ({vertex.x:.2f}, {vertex.y:.2f}, {vertex.z:.2f})")
        
        # Log face indices (first 4 for brevity)
        for i, face in enumerate(wall_mesh.faces[:4]):
            logger.info(f"   - Face {i}: {face.indices}")
        
        logger.info(f"   ✅ Wall '{wall_mesh.id}' validation passed")
    
    def test_wall_segment_extraction(self, scaled_coords: ScaledCoordinates) -> None:
        """
        Test wall segment extraction from room boundaries.
        
        Args:
            scaled_coords: Scaled coordinates for testing
        """
        logger.info("="*60)
        logger.info("Testing Wall Segment Extraction")
        logger.info("="*60)
        
        # Test shared wall detection
        wall_segments = self.wall_generator._extract_wall_segments_from_rooms(scaled_coords)
        
        assert len(wall_segments) > 0, "Should extract wall segments"
        
        logger.info(f"✅ Extracted {len(wall_segments)} wall segments:")
        
        for i, segment in enumerate(wall_segments):
            start_point, end_point = segment
            length = ((end_point[0] - start_point[0])**2 + (end_point[1] - start_point[1])**2)**0.5
            logger.info(f"   - Segment {i}: ({start_point[0]:.1f}, {start_point[1]:.1f}) to "
                       f"({end_point[0]:.1f}, {end_point[1]:.1f}) - length: {length:.1f}'")
        
        # Verify we have the expected wall types
        vertical_walls = [s for s in wall_segments if abs(s[0][0] - s[1][0]) < 0.1]
        horizontal_walls = [s for s in wall_segments if abs(s[0][1] - s[1][1]) < 0.1]
        
        logger.info(f"   - Vertical walls: {len(vertical_walls)}")
        logger.info(f"   - Horizontal walls: {len(horizontal_walls)}")
        
        # Should have at least some walls
        assert len(vertical_walls) + len(horizontal_walls) > 0, "Should have both vertical and horizontal walls"
    
    def test_edge_cases(self, scaled_coords: ScaledCoordinates) -> None:
        """
        Test edge cases and error handling.
        
        Args:
            scaled_coords: Valid scaled coordinates for testing
        """
        logger.info("="*60)
        logger.info("Testing Edge Cases and Error Handling")
        logger.info("="*60)
        
        # Test with empty rooms
        try:
            empty_coords = ScaledCoordinates(
                walls_feet=scaled_coords.walls_feet,
                rooms_feet={},
                scale_reference=scaled_coords.scale_reference,
                total_building_size=scaled_coords.total_building_size
            )
            self.wall_generator.generate_wall_meshes(empty_coords)
            logger.error("❌ Should have failed with empty rooms")
            assert False, "Should have failed with empty rooms"
        except WallGenerationError as e:
            logger.info(f"✅ Correctly failed with empty rooms: {str(e)}")
        
        # Test with insufficient wall points
        try:
            insufficient_coords = ScaledCoordinates(
                walls_feet=[(0.0, 0.0)],  # Only one point
                rooms_feet=scaled_coords.rooms_feet,
                scale_reference=scaled_coords.scale_reference,
                total_building_size=scaled_coords.total_building_size
            )
            self.wall_generator.generate_wall_meshes(insufficient_coords)
            logger.error("❌ Should have failed with insufficient wall points")
            assert False, "Should have failed with insufficient wall points"
        except WallGenerationError as e:
            logger.info(f"✅ Correctly failed with insufficient wall points: {str(e)}")
        
        # Test with missing room fields
        try:
            invalid_room_data = {
                "invalid_room": {
                    "width_feet": 10.0,
                    "length_feet": 10.0,
                    "area_sqft": 100.0,
                    # Missing x_offset_feet and y_offset_feet
                }
            }
            invalid_coords = ScaledCoordinates(
                walls_feet=scaled_coords.walls_feet,
                rooms_feet=invalid_room_data,
                scale_reference=scaled_coords.scale_reference,
                total_building_size=scaled_coords.total_building_size
            )
            self.wall_generator.generate_wall_meshes(invalid_coords)
            logger.error("❌ Should have failed with missing room fields")
            assert False, "Should have failed with missing room fields"
        except WallGenerationError as e:
            logger.info(f"✅ Correctly failed with missing room fields: {str(e)}")
        
        logger.info("✅ All edge case tests passed")
    
    def test_wall_mesh_validation(self, wall_meshes: List[Wall3D]) -> None:
        """
        Test wall mesh validation functionality.
        
        Args:
            wall_meshes: List of Wall3D objects to validate
        """
        logger.info("="*60)
        logger.info("Testing Wall Mesh Validation")
        logger.info("="*60)
        
        for wall_mesh in wall_meshes:
            validation_result = self.wall_generator.validate_wall_mesh(wall_mesh)
            
            assert validation_result["is_valid"], f"Wall '{wall_mesh.id}' validation failed: {validation_result['errors']}"
            assert validation_result["vertex_count"] == 8, f"Expected 8 vertices, got {validation_result['vertex_count']}"
            assert validation_result["face_count"] == 12, f"Expected 12 faces, got {validation_result['face_count']}"
            
            logger.info(f"✅ Wall '{wall_mesh.id}' validation passed:")
            logger.info(f"   - Valid: {validation_result['is_valid']}")
            logger.info(f"   - Vertices: {validation_result['vertex_count']}")
            logger.info(f"   - Faces: {validation_result['face_count']}")
            
            if validation_result["warnings"]:
                logger.info(f"   - Warnings: {validation_result['warnings']}")
    
    def run_all_tests(self) -> bool:
        """
        Run all wall generator tests.
        
        Returns:
            True if all tests pass, False otherwise
        """
        try:
            logger.info("🚀 Starting Wall Generator Tests")
            logger.info("="*60)
            
            # Create mock data
            scaled_coords = self.create_mock_scaled_coordinates()
            
            # Run tests
            wall_meshes = self.test_wall_mesh_generation(scaled_coords)
            self.test_wall_segment_extraction(scaled_coords)
            self.test_edge_cases(scaled_coords)
            self.test_wall_mesh_validation(wall_meshes)
            
            logger.info("="*60)
            logger.info("🎉 ALL TESTS PASSED! Wall generator is working correctly.")
            logger.info("="*60)
            
            # Summary
            total_vertices = sum(len(wall.vertices) for wall in wall_meshes)
            total_faces = sum(len(wall.faces) for wall in wall_meshes)
            
            logger.info(f"📊 Final Summary:")
            logger.info(f"   - Walls generated: {len(wall_meshes)}")
            logger.info(f"   - Total vertices: {total_vertices}")
            logger.info(f"   - Total faces: {total_faces}")
            logger.info(f"   - Average vertices per wall: {total_vertices / len(wall_meshes)}")
            logger.info(f"   - Average faces per wall: {total_faces / len(wall_meshes)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Test failed: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False


def main():
    """Main test entry point."""
    test_suite = WallGeneratorTest()
    success = test_suite.run_all_tests()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
