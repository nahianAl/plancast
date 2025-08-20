#!/usr/bin/env python3
"""
Simple conversion test that bypasses CubiCasa model to test basic pipeline.
"""

import sys
import os
import time
import uuid
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.data_structures import (
    ProcessingJob,
    ProcessingStatus,
    CubiCasaOutput,
    Building3D,
    Room3D,
    Wall3D,
    Vertex3D,
    Face
)
from services.test_room_generator import SimpleRoomGenerator
from services.test_wall_generator import SimpleWallGenerator
from services.mesh_exporter import MeshExporter

def create_mock_cubicasa_output():
    """Create a mock CubiCasa output for testing."""
    return CubiCasaOutput(
        room_bounding_boxes={
            "test_room": {
                "min_x": 0,
                "min_y": 0,
                "max_x": 512,
                "max_y": 512
            }
        },
        wall_coordinates=[],
        room_polygons={},
        door_coordinates=[],
        window_coordinates=[],
        icon_detections=[],
        processing_time=0.1,
        image_dimensions=(512, 512)  # Add missing field
    )

def test_simple_pipeline():
    """Test the simple pipeline without CubiCasa model."""
    print("🚀 Testing simple pipeline without CubiCasa model...")
    
    try:
        # Create mock data
        job_id = str(uuid.uuid4())
        cubicasa_output = create_mock_cubicasa_output()
        
        print(f"✅ Created mock CubiCasa output with 1 room")
        
        # Test room generation
        print("🔧 Testing room generation...")
        room_generator = SimpleRoomGenerator()
        room_meshes = room_generator.generate_simple_rooms(cubicasa_output)
        print(f"✅ Generated {len(room_meshes)} room meshes")
        
        # Test wall generation
        print("🔧 Testing wall generation...")
        wall_generator = SimpleWallGenerator()
        wall_meshes = wall_generator.generate_simple_walls(cubicasa_output)
        print(f"✅ Generated {len(wall_meshes)} wall meshes")
        
        # Test building assembly
        print("🔧 Testing building assembly...")
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
            min_x, max_x = 0, 512
            min_y, max_y = 0, 512
            min_z, max_z = 0, 9.0
        
        bounding_box = {
            "min_x": min_x,
            "min_y": min_y,
            "min_z": min_z,
            "max_x": max_x,
            "max_y": max_y,
            "max_z": max_z
        }
        
        building_3d = Building3D(
            rooms=room_meshes,
            walls=wall_meshes,
            units="feet",
            total_vertices=total_vertices,
            total_faces=total_faces,
            bounding_box=bounding_box,
            metadata={
                "pipeline_type": "simple_test",
                "total_vertices": total_vertices,
                "total_faces": total_faces
            }
        )
        print(f"✅ Assembled building with {total_vertices} vertices, {total_faces} faces")
        
        # Test export
        print("🔧 Testing model export...")
        mesh_exporter = MeshExporter()
        output_dir = "output/test_models"
        os.makedirs(output_dir, exist_ok=True)
        
        export_result = mesh_exporter.export_building(
            building=building_3d,
            formats=["glb", "obj"],
            out_dir=output_dir
        )
        
        print(f"✅ Exported {len(export_result.files)} formats")
        for fmt, path in export_result.files.items():
            file_size = os.path.getsize(path)
            print(f"   - {fmt.upper()}: {path} ({file_size} bytes)")
        
        print("\n🎉 Simple pipeline test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Simple pipeline test failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_simple_pipeline()
    sys.exit(0 if success else 1)
