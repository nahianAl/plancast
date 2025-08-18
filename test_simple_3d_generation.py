#!/usr/bin/env python3
"""
Test Script for Simplified 3D Model Generation Pipeline

This script tests the simplified pipeline that skips coordinate scaling and
door/window integration to debug 3D model generation issues.

IMPORTANT: This is for debugging only. After fixing core issues, we must integrate
back with the full enhanced pipeline.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from test_pipeline_simple import SimpleTestPipeline
from models.data_structures import CubiCasaOutput

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_mock_cubicasa_output() -> CubiCasaOutput:
    """
    Create a mock CubiCasa output for testing.
    
    Returns:
        Mock CubiCasaOutput with sample room bounding boxes
    """
    # Sample room bounding boxes (pixel coordinates)
    room_bounding_boxes = {
        "kitchen": {
            "min_x": 100,
            "max_x": 286,
            "min_y": 200,
            "max_y": 340
        },
        "living_room": {
            "min_x": 50,
            "max_x": 350,
            "min_y": 50,
            "max_y": 200
        },
        "bedroom": {
            "min_x": 300,
            "max_x": 450,
            "min_y": 200,
            "max_y": 350
        },
        "bathroom": {
            "min_x": 450,
            "max_x": 500,
            "min_y": 100,
            "max_y": 200
        }
    }
    
    # Sample wall coordinates (simplified)
    wall_coordinates = [
        (100, 200), (286, 200),  # Kitchen bottom wall
        (286, 200), (286, 340),  # Kitchen right wall
        (286, 340), (100, 340),  # Kitchen top wall
        (100, 340), (100, 200),  # Kitchen left wall
        (50, 50), (350, 50),     # Living room bottom wall
        (350, 50), (350, 200),   # Living room right wall
        (350, 200), (50, 200),   # Living room top wall
        (50, 200), (50, 50),     # Living room left wall
    ]
    
    return CubiCasaOutput(
        room_bounding_boxes=room_bounding_boxes,
        wall_coordinates=wall_coordinates,
        door_coordinates=[],  # No doors for simplified test
        window_coordinates=[],  # No windows for simplified test
        room_polygons={},  # No complex polygons for simplified test
        raw_output=None,
        post_processed_output=None,
        image_dimensions=(512, 512),  # Required field
        processing_time=1.5  # Required field
    )


def test_simple_pipeline_components():
    """Test individual components of the simplified pipeline."""
    print("🔧 Testing Simplified Pipeline Components")
    print("=" * 50)
    
    try:
        # Test 1: Simple Room Generator
        print("\n📋 Test 1: Simple Room Generator")
        from services.test_room_generator import SimpleRoomGenerator
        
        room_generator = SimpleRoomGenerator()
        mock_output = create_mock_cubicasa_output()
        
        room_meshes = room_generator.generate_simple_rooms(mock_output)
        
        print(f"✅ Room generation successful: {len(room_meshes)} rooms created")
        for room in room_meshes:
            print(f"   - {room.name}: {len(room.vertices)} vertices, {len(room.faces)} faces")
            print(f"     Height: {room.height_feet:.1f}' feet")
        
        # Test 2: Simple Wall Generator
        print("\n📋 Test 2: Simple Wall Generator")
        from services.test_wall_generator import SimpleWallGenerator
        
        wall_generator = SimpleWallGenerator()
        wall_meshes = wall_generator.generate_simple_walls(mock_output)
        
        print(f"✅ Wall generation successful: {len(wall_meshes)} walls created")
        for wall in wall_meshes:
            print(f"   - {wall.id}: {len(wall.vertices)} vertices, {len(wall.faces)} faces")
            print(f"     Length: {wall.length_feet:.1f}' × {wall.height_feet:.1f}' × {wall.thickness_feet:.1f}'")
        
        # Test 3: Building Assembly
        print("\n📋 Test 3: Building Assembly")
        total_vertices = sum(len(room.vertices) for room in room_meshes) + sum(len(wall.vertices) for wall in wall_meshes)
        total_faces = sum(len(room.faces) for room in room_meshes) + sum(len(wall.faces) for wall in wall_meshes)
        
        print(f"✅ Building assembly successful:")
        print(f"   - Total vertices: {total_vertices}")
        print(f"   - Total faces: {total_faces}")
        print(f"   - Rooms: {len(room_meshes)}")
        print(f"   - Walls: {len(wall_meshes)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_pipeline_with_mock_data():
    """Test the complete simplified pipeline with mock data."""
    print("\n🔧 Testing Complete Simplified Pipeline")
    print("=" * 50)
    
    try:
        # Create simplified test pipeline
        pipeline = SimpleTestPipeline()
        
        # Create mock image data (simple test pattern)
        # This is a minimal test - in real usage you would provide an actual image file
        mock_image_data = b"mock_image_data_for_testing"
        
        # Test the pipeline
        result = pipeline.process_test_image(
            file_content=mock_image_data,
            filename="test_floorplan.jpg",
            export_formats=["glb", "obj"]
        )
        
        print(f"✅ Simplified pipeline test completed:")
        print(f"   - Job ID: {result.job_id}")
        print(f"   - Status: {result.status}")
        print(f"   - Processing time: {result.total_processing_time():.2f} seconds")
        print(f"   - Exported files: {list(result.exported_files.keys()) if result.exported_files else 'None'}")
        
        if result.building_3d:
            print(f"   - Building vertices: {result.building_3d.total_vertices}")
            print(f"   - Building faces: {result.building_3d.total_faces}")
            print(f"   - Rooms: {len(result.building_3d.rooms)}")
            print(f"   - Walls: {len(result.building_3d.walls)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Simplified pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_with_actual_image_file():
    """Test the simplified pipeline with an actual image file if available."""
    print("\n🔧 Testing with Actual Image File")
    print("=" * 50)
    
    # Look for test image files
    test_image_paths = [
        "test_image.jpg",  # Use the real test image first
        "test_floorplan.jpg",
        "test_floorplan.png",
        "sample_floorplan.jpg",
        "sample_floorplan.png",
        "assets/test_images/floorplan.jpg",
        "assets/test_images/floorplan.png"
    ]
    
    test_image_path = None
    for path in test_image_paths:
        if os.path.exists(path):
            test_image_path = path
            break
    
    if not test_image_path:
        print("⚠️  No test image file found. Skipping actual image test.")
        print("   To test with an actual image, place a floor plan image file in the project root.")
        print("   Supported formats: JPG, PNG")
        return True
    
    try:
        print(f"📁 Found test image: {test_image_path}")
        
        # Read the image file
        with open(test_image_path, 'rb') as f:
            image_data = f.read()
        
        print(f"📊 Image size: {len(image_data)} bytes")
        
        # Create simplified test pipeline
        pipeline = SimpleTestPipeline()
        
        # Process the image
        result = pipeline.process_test_image(
            file_content=image_data,
            filename=os.path.basename(test_image_path),
            export_formats=["glb", "obj"]
        )
        
        print(f"✅ Actual image test completed:")
        print(f"   - Job ID: {result.job_id}")
        print(f"   - Status: {result.status}")
        print(f"   - Processing time: {result.total_processing_time():.2f} seconds")
        
        if result.exported_files:
            print(f"   - Exported files:")
            for format_name, file_path in result.exported_files.items():
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"     - {format_name.upper()}: {file_path} ({file_size} bytes)")
                else:
                    print(f"     - {format_name.upper()}: {file_path} (file not found)")
        
        if result.building_3d:
            print(f"   - Building statistics:")
            print(f"     - Total vertices: {result.building_3d.total_vertices}")
            print(f"     - Total faces: {result.building_3d.total_faces}")
            print(f"     - Rooms: {len(result.building_3d.rooms)}")
            print(f"     - Walls: {len(result.building_3d.walls)}")
            
            # Check for gibberish results
            if result.building_3d.total_vertices > 0 and result.building_3d.total_faces > 0:
                print("✅ 3D model appears to have valid geometry")
            else:
                print("❌ 3D model has no geometry - possible gibberish result")
        
        return True
        
    except Exception as e:
        print(f"❌ Actual image test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all simplified pipeline tests."""
    print("🔧 PlanCast Simplified 3D Generation Test")
    print("=" * 60)
    print("This is a TEMPORARY debugging pipeline.")
    print("After fixing core issues, we must integrate back with the full pipeline.")
    print("=" * 60)
    
    tests = [
        ("Component Tests", test_simple_pipeline_components),
        ("Mock Data Pipeline Test", test_simple_pipeline_with_mock_data),
        ("Actual Image Test", test_with_actual_image_file),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 60)
    print("📊 Simplified Pipeline Test Results:")
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All simplified pipeline tests passed!")
        print("🔧 The core 3D generation logic appears to be working correctly.")
        print("📋 Next steps:")
        print("   1. Identify specific issues in the simplified pipeline")
        print("   2. Fix core 3D generation logic")
        print("   3. Gradually reintegrate coordinate scaling")
        print("   4. Add back door/window cutouts")
        print("   5. Restore enhanced validation")
        print("   6. Test complete pipeline")
    else:
        print("⚠️ Some tests failed. Check the output above for issues.")
        print("🔧 The simplified pipeline has revealed core 3D generation problems.")
        print("📋 Focus on fixing the failing components before proceeding.")
    
    return all_passed


if __name__ == "__main__":
    main()
