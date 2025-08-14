#!/usr/bin/env python3
"""
Test script for Room Mesh Generator service.
Tests Task 3: Generating 3D room floor meshes from scaled coordinates.

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

from services.room_generator import get_room_generator, RoomMeshGenerator, RoomGenerationError
from services.coordinate_scaler import get_coordinate_scaler
from models.data_structures import (
    CubiCasaOutput,
    ScaledCoordinates,
    Room3D,
    Vertex3D,
    Face,
    ScaleReference,
    BuildingDimensions
)
from utils.logger import get_logger

logger = get_logger("test_room_generator")


class RoomGeneratorTest:
    """
    Production test suite for room mesh generator service.
    Maintains harmony with the complete PlanCast pipeline.
    """
    
    def __init__(self):
        """Initialize test suite with production services."""
        self.room_generator = get_room_generator()
        self.coordinate_scaler = get_coordinate_scaler()
        self.test_job_id = f"test_room_gen_{uuid.uuid4().hex[:8]}"
        
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
        
        # Mock room data in feet
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
                "x_offset_feet": 20.0,
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
    
    def test_room_mesh_generation(self, scaled_coords: ScaledCoordinates) -> List[Room3D]:
        """
        Test room mesh generation.
        
        Args:
            scaled_coords: Scaled coordinates for testing
            
        Returns:
            List of generated Room3D objects
        """
        logger.info("="*60)
        logger.info("Testing Room Mesh Generation")
        logger.info("="*60)
        
        # Test with default parameters
        start_time = time.time()
        room_meshes = self.room_generator.generate_room_meshes(
            scaled_coords=scaled_coords,
            floor_thickness_feet=0.25,
            room_height_feet=9.0
        )
        generation_time = time.time() - start_time
        
        # Validate results
        assert isinstance(room_meshes, list), "Room meshes should be a list"
        assert len(room_meshes) == len(scaled_coords.rooms_feet), "Should generate one mesh per room"
        
        logger.info(f"✅ Room mesh generation successful:")
        logger.info(f"   - Generation time: {generation_time:.3f}s")
        logger.info(f"   - Rooms generated: {len(room_meshes)}")
        
        # Validate each room mesh
        for room_mesh in room_meshes:
            self._validate_room_mesh(room_mesh)
        
        return room_meshes
    
    def _validate_room_mesh(self, room_mesh: Room3D) -> None:
        """
        Validate individual room mesh.
        
        Args:
            room_mesh: Room3D object to validate
        """
        logger.info(f"\n🏠 Validating room: {room_mesh.name}")
        
        # Basic structure validation
        assert isinstance(room_mesh.name, str), "Room name should be string"
        assert isinstance(room_mesh.vertices, list), "Vertices should be list"
        assert isinstance(room_mesh.faces, list), "Faces should be list"
        assert isinstance(room_mesh.elevation_feet, (int, float)), "Elevation should be numeric"
        assert isinstance(room_mesh.height_feet, (int, float)), "Height should be numeric"
        
        # Vertex validation
        assert len(room_mesh.vertices) == 4, f"Expected 4 vertices, got {len(room_mesh.vertices)}"
        for i, vertex in enumerate(room_mesh.vertices):
            assert isinstance(vertex, Vertex3D), f"Vertex {i} should be Vertex3D"
            assert isinstance(vertex.x, (int, float)), f"Vertex {i} x should be numeric"
            assert isinstance(vertex.y, (int, float)), f"Vertex {i} y should be numeric"
            assert isinstance(vertex.z, (int, float)), f"Vertex {i} z should be numeric"
        
        # Face validation
        assert len(room_mesh.faces) == 2, f"Expected 2 faces, got {len(room_mesh.faces)}"
        for i, face in enumerate(room_mesh.faces):
            assert isinstance(face, Face), f"Face {i} should be Face"
            assert len(face.indices) == 3, f"Face {i} should have 3 indices"
            for index in face.indices:
                assert 0 <= index < len(room_mesh.vertices), f"Face {i} has invalid index: {index}"
        
        # Dimension validation
        assert room_mesh.height_feet > 0, "Room height should be positive"
        assert room_mesh.elevation_feet >= 0, "Room elevation should be non-negative"
        
        # Log room details
        logger.info(f"   - Vertices: {len(room_mesh.vertices)}")
        logger.info(f"   - Faces: {len(room_mesh.faces)}")
        logger.info(f"   - Elevation: {room_mesh.elevation_feet:.1f} feet")
        logger.info(f"   - Height: {room_mesh.height_feet:.1f} feet")
        
        # Log vertex coordinates
        for i, vertex in enumerate(room_mesh.vertices):
            logger.info(f"   - Vertex {i}: ({vertex.x:.2f}, {vertex.y:.2f}, {vertex.z:.2f})")
        
        # Log face indices
        for i, face in enumerate(room_mesh.faces):
            logger.info(f"   - Face {i}: {face.indices}")
        
        logger.info(f"   ✅ Room '{room_mesh.name}' validation passed")
    
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
                walls_feet=[],
                rooms_feet={},
                scale_reference=scaled_coords.scale_reference,
                total_building_size=scaled_coords.total_building_size
            )
            self.room_generator.generate_room_meshes(empty_coords)
            logger.error("❌ Should have failed with empty rooms")
            assert False, "Should have failed with empty rooms"
        except RoomGenerationError as e:
            logger.info(f"✅ Correctly failed with empty rooms: {str(e)}")
        
        # Test with missing required fields
        try:
            # Create a valid ScaledCoordinates first, then modify the rooms_feet
            invalid_coords = ScaledCoordinates(
                walls_feet=scaled_coords.walls_feet,
                rooms_feet={"invalid_room": {
                    "width_feet": 10.0,
                    "length_feet": 10.0,
                    "area_sqft": 100.0,
                    # Missing x_offset_feet and y_offset_feet
                }},
                scale_reference=scaled_coords.scale_reference,
                total_building_size=scaled_coords.total_building_size
            )
            self.room_generator.generate_room_meshes(invalid_coords)
            logger.error("❌ Should have failed with missing required fields")
            assert False, "Should have failed with missing required fields"
        except RoomGenerationError as e:
            logger.info(f"✅ Correctly failed with missing required fields: {str(e)}")
        
        # Test with negative dimensions
        try:
            negative_coords = ScaledCoordinates(
                walls_feet=scaled_coords.walls_feet,
                rooms_feet={"negative_room": {
                    "width_feet": -5.0,
                    "length_feet": 10.0,
                    "area_sqft": 50.0,
                    "x_offset_feet": 0.0,
                    "y_offset_feet": 0.0
                }},
                scale_reference=scaled_coords.scale_reference,
                total_building_size=scaled_coords.total_building_size
            )
            self.room_generator.generate_room_meshes(negative_coords)
            logger.error("❌ Should have failed with negative dimensions")
            assert False, "Should have failed with negative dimensions"
        except RoomGenerationError as e:
            logger.info(f"✅ Correctly failed with negative dimensions: {str(e)}")
        
        logger.info("✅ All edge case tests passed")
    
    def test_mesh_validation(self, room_meshes: List[Room3D]) -> None:
        """
        Test mesh validation functionality.
        
        Args:
            room_meshes: List of Room3D objects to validate
        """
        logger.info("="*60)
        logger.info("Testing Mesh Validation")
        logger.info("="*60)
        
        for room_mesh in room_meshes:
            validation_result = self.room_generator.validate_room_mesh(room_mesh)
            
            assert validation_result["is_valid"], f"Room '{room_mesh.name}' validation failed: {validation_result['errors']}"
            assert validation_result["vertex_count"] == 4, f"Expected 4 vertices, got {validation_result['vertex_count']}"
            assert validation_result["face_count"] == 2, f"Expected 2 faces, got {validation_result['face_count']}"
            
            logger.info(f"✅ Room '{room_mesh.name}' validation passed:")
            logger.info(f"   - Valid: {validation_result['is_valid']}")
            logger.info(f"   - Vertices: {validation_result['vertex_count']}")
            logger.info(f"   - Faces: {validation_result['face_count']}")
            
            if validation_result["warnings"]:
                logger.info(f"   - Warnings: {validation_result['warnings']}")
    
    def run_all_tests(self) -> bool:
        """
        Run all room generator tests.
        
        Returns:
            True if all tests pass, False otherwise
        """
        try:
            logger.info("🚀 Starting Room Generator Tests")
            logger.info("="*60)
            
            # Create mock data
            scaled_coords = self.create_mock_scaled_coordinates()
            
            # Run tests
            room_meshes = self.test_room_mesh_generation(scaled_coords)
            self.test_edge_cases(scaled_coords)
            self.test_mesh_validation(room_meshes)
            
            logger.info("="*60)
            logger.info("🎉 ALL TESTS PASSED! Room generator is working correctly.")
            logger.info("="*60)
            
            # Summary
            total_vertices = sum(len(room.vertices) for room in room_meshes)
            total_faces = sum(len(room.faces) for room in room_meshes)
            
            logger.info(f"📊 Final Summary:")
            logger.info(f"   - Rooms generated: {len(room_meshes)}")
            logger.info(f"   - Total vertices: {total_vertices}")
            logger.info(f"   - Total faces: {total_faces}")
            logger.info(f"   - Average vertices per room: {total_vertices / len(room_meshes)}")
            logger.info(f"   - Average faces per room: {total_faces / len(room_meshes)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Test failed: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False


def main():
    """Main test entry point."""
    test_suite = RoomGeneratorTest()
    success = test_suite.run_all_tests()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
