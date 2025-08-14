#!/usr/bin/env python3
"""
Test script for Mesh Exporter service.
Tests Task 5: Exporting 3D building models in multiple formats.

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
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.mesh_exporter import get_mesh_exporter, MeshExporter, MeshExportError, DependencyError
from services.room_generator import get_room_generator
from services.wall_generator import get_wall_generator
from models.data_structures import (
    Building3D,
    Room3D,
    Wall3D,
    Vertex3D,
    Face,
    MeshExportResult,
    WebPreviewData,
    ScaledCoordinates,
    ScaleReference,
    BuildingDimensions
)
from utils.logger import get_logger

logger = get_logger("test_mesh_exporter")


class MeshExporterTest:
    """
    Production test suite for mesh exporter service.
    Maintains harmony with the complete PlanCast pipeline.
    """
    
    def __init__(self):
        """Initialize test suite with production services."""
        self.mesh_exporter = get_mesh_exporter()
        self.room_generator = get_room_generator()
        self.wall_generator = get_wall_generator()
        self.test_job_id = f"test_mesh_export_{uuid.uuid4().hex[:8]}"
        
        # Create temporary test directory
        self.test_dir = Path(tempfile.mkdtemp(prefix="plancast_test_"))
        logger.info(f"Created test directory: {self.test_dir}")
        
    def __del__(self):
        """Clean up test directory."""
        try:
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)
                logger.info(f"Cleaned up test directory: {self.test_dir}")
        except Exception as e:
            logger.warning(f"Failed to clean up test directory: {e}")
    
    def create_mock_building(self) -> Building3D:
        """
        Create mock building data for testing.
        
        Returns:
            Mock Building3D with realistic room and wall data
        """
        logger.info("Creating mock building data for testing...")
        
        # Create mock scaled coordinates first
        scaled_coords = self._create_mock_scaled_coordinates()
        
        # Generate room meshes
        room_meshes = self.room_generator.generate_room_meshes(scaled_coords)
        
        # Generate wall meshes
        wall_meshes = self.wall_generator.generate_wall_meshes(scaled_coords)
        
        # Calculate total vertices and faces
        total_vertices = sum(len(room.vertices) for room in room_meshes) + sum(len(wall.vertices) for wall in wall_meshes)
        total_faces = sum(len(room.faces) for room in room_meshes) + sum(len(wall.faces) for wall in wall_meshes)
        
        # Calculate bounding box
        all_vertices = []
        for room in room_meshes:
            all_vertices.extend([(v.x, v.y, v.z) for v in room.vertices])
        for wall in wall_meshes:
            all_vertices.extend([(v.x, v.y, v.z) for v in wall.vertices])
        
        if all_vertices:
            x_coords = [v[0] for v in all_vertices]
            y_coords = [v[1] for v in all_vertices]
            z_coords = [v[2] for v in all_vertices]
            
            bounding_box = {
                "min_x": min(x_coords),
                "max_x": max(x_coords),
                "min_y": min(y_coords),
                "max_y": max(y_coords),
                "min_z": min(z_coords),
                "max_z": max(z_coords)
            }
        else:
            bounding_box = {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0, "min_z": 0, "max_z": 0}
        
        # Create Building3D
        building = Building3D(
            rooms=room_meshes,
            walls=wall_meshes,
            total_vertices=total_vertices,
            total_faces=total_faces,
            bounding_box=bounding_box,
            export_ready=True
        )
        
        logger.info(f"✅ Mock building created:")
        logger.info(f"   - Rooms: {len(room_meshes)}")
        logger.info(f"   - Walls: {len(wall_meshes)}")
        logger.info(f"   - Total vertices: {total_vertices}")
        logger.info(f"   - Total faces: {total_faces}")
        logger.info(f"   - Bounding box: {bounding_box}")
        
        return building
    
    def _create_mock_scaled_coordinates(self) -> ScaledCoordinates:
        """
        Create mock scaled coordinates for testing.
        
        Returns:
            Mock ScaledCoordinates with realistic room data
        """
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
        
        return scaled_coords
    
    def test_mesh_export(self, building: Building3D) -> MeshExportResult:
        """
        Test mesh export functionality.
        
        Args:
            building: Building3D object for testing
            
        Returns:
            MeshExportResult from export operation
        """
        logger.info("="*60)
        logger.info("Testing Mesh Export")
        logger.info("="*60)
        
        # Test with multiple formats
        formats = ["glb", "obj", "stl"]
        out_dir = str(self.test_dir / "exports")
        
        # Export building
        start_time = time.time()
        result = self.mesh_exporter.export_building(
            building=building,
            formats=formats,
            out_dir=out_dir
        )
        export_time = time.time() - start_time
        
        # Validate results
        assert isinstance(result, MeshExportResult), "Result should be MeshExportResult"
        assert len(result.files) > 0, "Should export at least one file"
        assert "glb" in result.files, "Should export GLB format"
        assert "obj" in result.files, "Should export OBJ format"
        assert "stl" in result.files, "Should export STL format"
        
        logger.info(f"✅ Mesh export successful:")
        logger.info(f"   - Export time: {export_time:.3f}s")
        logger.info(f"   - Files exported: {len(result.files)}")
        logger.info(f"   - Formats: {list(result.files.keys())}")
        logger.info(f"   - Total size: {result.summary['total_size_bytes']} bytes")
        
        # Log file details
        for format_name, file_path in result.files.items():
            file_size = os.path.getsize(file_path)
            logger.info(f"   - {format_name.upper()}: {file_path} ({file_size} bytes)")
        
        return result
    
    def test_individual_format_exports(self, building: Building3D) -> None:
        """
        Test individual format export functions.
        
        Args:
            building: Building3D object for testing
        """
        logger.info("="*60)
        logger.info("Testing Individual Format Exports")
        logger.info("="*60)
        
        # Test GLB export
        glb_path = str(self.test_dir / "test_building.glb")
        exported_glb = self.mesh_exporter.export_glb(building, glb_path, web_optimized=True)
        assert os.path.exists(exported_glb), "GLB file should exist"
        assert os.path.getsize(exported_glb) > 0, "GLB file should not be empty"
        logger.info(f"✅ GLB export: {exported_glb} ({os.path.getsize(exported_glb)} bytes)")
        
        # Test OBJ export
        obj_path = str(self.test_dir / "test_building.obj")
        exported_obj = self.mesh_exporter.export_obj(building, obj_path)
        assert os.path.exists(exported_obj), "OBJ file should exist"
        assert os.path.getsize(exported_obj) > 0, "OBJ file should not be empty"
        logger.info(f"✅ OBJ export: {exported_obj} ({os.path.getsize(exported_obj)} bytes)")
        
        # Test STL export
        stl_path = str(self.test_dir / "test_building.stl")
        exported_stl = self.mesh_exporter.export_stl(building, stl_path)
        assert os.path.exists(exported_stl), "STL file should exist"
        assert os.path.getsize(exported_stl) > 0, "STL file should not be empty"
        logger.info(f"✅ STL export: {exported_stl} ({os.path.getsize(exported_stl)} bytes)")
    
    def test_web_preview_data(self, result: MeshExportResult) -> None:
        """
        Test web preview data generation.
        
        Args:
            result: MeshExportResult from export operation
        """
        logger.info("="*60)
        logger.info("Testing Web Preview Data")
        logger.info("="*60)
        
        preview_data = result.preview_data
        
        # Validate preview data structure
        assert isinstance(preview_data, WebPreviewData), "Preview data should be WebPreviewData"
        assert preview_data.glb_url, "GLB URL should be set"
        assert preview_data.thumbnail_url, "Thumbnail URL should be set"
        assert isinstance(preview_data.scene_metadata, dict), "Scene metadata should be dict"
        
        logger.info(f"✅ Web preview data generated:")
        logger.info(f"   - GLB URL: {preview_data.glb_url}")
        logger.info(f"   - Thumbnail URL: {preview_data.thumbnail_url}")
        logger.info(f"   - Scene metadata keys: {list(preview_data.scene_metadata.keys())}")
        
        # Validate scene metadata
        metadata = preview_data.scene_metadata
        required_keys = ["building_center", "building_dimensions", "bounding_box", "camera_positions", "units"]
        
        for key in required_keys:
            assert key in metadata, f"Scene metadata should contain '{key}'"
        
        logger.info(f"   - Building center: {metadata['building_center']}")
        logger.info(f"   - Building dimensions: {metadata['building_dimensions']}")
        logger.info(f"   - Units: {metadata['units']}")
        logger.info(f"   - Camera positions: {list(metadata['camera_positions'].keys())}")
    
    def test_export_validation(self, result: MeshExportResult) -> None:
        """
        Test export result validation.
        
        Args:
            result: MeshExportResult to validate
        """
        logger.info("="*60)
        logger.info("Testing Export Validation")
        logger.info("="*60)
        
        validation_result = self.mesh_exporter.validate_export_result(result)
        
        # Validate validation result structure
        assert validation_result["is_valid"], f"Export should be valid: {validation_result['errors']}"
        assert validation_result["files_exported"] > 0, "Should have exported files"
        assert validation_result["total_size_bytes"] > 0, "Should have total file size"
        
        logger.info(f"✅ Export validation passed:")
        logger.info(f"   - Valid: {validation_result['is_valid']}")
        logger.info(f"   - Files exported: {validation_result['files_exported']}")
        logger.info(f"   - Total size: {validation_result['total_size_bytes']} bytes")
        
        if validation_result["warnings"]:
            logger.info(f"   - Warnings: {validation_result['warnings']}")
    
    def test_edge_cases(self, building: Building3D) -> None:
        """
        Test edge cases and error handling.
        
        Args:
            building: Building3D object for testing
        """
        logger.info("="*60)
        logger.info("Testing Edge Cases and Error Handling")
        logger.info("="*60)
        
        # Test with empty formats list
        try:
            self.mesh_exporter.export_building(building, [], str(self.test_dir))
            logger.error("❌ Should have failed with empty formats")
            assert False, "Should have failed with empty formats"
        except MeshExportError as e:
            logger.info(f"✅ Correctly failed with empty formats: {str(e)}")
        
        # Test with unsupported format
        try:
            result = self.mesh_exporter.export_building(building, ["unsupported"], str(self.test_dir))
            logger.info(f"✅ Handled unsupported format gracefully: {list(result.files.keys())}")
        except Exception as e:
            logger.error(f"❌ Failed to handle unsupported format: {str(e)}")
            assert False, "Should handle unsupported formats gracefully"
        
        # Test with invalid building (no rooms or walls)
        try:
            empty_building = Building3D(
                rooms=[],
                walls=[],
                total_vertices=0,
                total_faces=0,
                bounding_box={"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0, "min_z": 0, "max_z": 0},
                export_ready=True
            )
            self.mesh_exporter.export_building(empty_building, ["glb"], str(self.test_dir))
            logger.error("❌ Should have failed with empty building")
            assert False, "Should have failed with empty building"
        except MeshExportError as e:
            logger.info(f"✅ Correctly failed with empty building: {str(e)}")
        
        logger.info("✅ All edge case tests passed")
    
    def run_all_tests(self) -> bool:
        """
        Run all mesh exporter tests.
        
        Returns:
            True if all tests pass, False otherwise
        """
        try:
            logger.info("🚀 Starting Mesh Exporter Tests")
            logger.info("="*60)
            
            # Create mock building
            building = self.create_mock_building()
            
            # Run tests
            result = self.test_mesh_export(building)
            self.test_individual_format_exports(building)
            self.test_web_preview_data(result)
            self.test_export_validation(result)
            self.test_edge_cases(building)
            
            logger.info("="*60)
            logger.info("🎉 ALL TESTS PASSED! Mesh exporter is working correctly.")
            logger.info("="*60)
            
            # Summary
            logger.info(f"📊 Final Summary:")
            logger.info(f"   - Formats supported: {self.mesh_exporter.supported_formats}")
            logger.info(f"   - Files exported: {len(result.files)}")
            logger.info(f"   - Total size: {result.summary['total_size_bytes']} bytes")
            logger.info(f"   - Export time: {result.summary['export_time_seconds']:.3f}s")
            logger.info(f"   - Building stats: {result.summary['building_stats']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Test failed: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False


def main():
    """Main test entry point."""
    test_suite = MeshExporterTest()
    success = test_suite.run_all_tests()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
