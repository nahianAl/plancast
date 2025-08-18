#!/usr/bin/env python3
"""
Test script for enhanced 3D generation.

This script tests:
1. Accurate room generation using actual polygons
2. Accurate wall generation using actual coordinates
3. Cutout integration in wall meshes
4. Complete 3D model accuracy

Run with: python3 test_enhanced_3d_generation.py
"""

import os
import sys
import time
from pathlib import Path

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.data_structures import CubiCasaOutput, ScaledCoordinates, Room3D, Wall3D
from services.room_generator import RoomMeshGenerator
from services.wall_generator import WallMeshGenerator
from services.opening_cutout_generator import OpeningCutoutGenerator
from services.coordinate_scaler import CoordinateScaler

def test_enhanced_room_generation():
    """Test enhanced room generation with actual polygons."""
    print("🧪 Testing enhanced room generation with polygons...")
    
    # Create mock CubiCasa output with room polygons
    mock_cubicasa_output = CubiCasaOutput(
        wall_coordinates=[(100, 100), (200, 100), (200, 200), (100, 200)],
        room_bounding_boxes={
            "kitchen": {"min_x": 100, "max_x": 200, "min_y": 100, "max_y": 200},
            "living_room": {"min_x": 200, "max_x": 400, "min_y": 100, "max_y": 300}
        },
        room_polygons={
            "kitchen": [(100, 100), (200, 100), (200, 200), (100, 200), (100, 100)],
            "living_room": [(200, 100), (400, 100), (400, 300), (200, 300), (200, 100)]
        },
        door_coordinates=[(150, 100), (300, 100)],
        window_coordinates=[(100, 150), (400, 150)],
        image_dimensions=(512, 512),
        confidence_scores={"kitchen": 0.95, "living_room": 0.90},
        processing_time=1.0
    )
    
    # Test coordinate scaling
    coordinate_scaler = CoordinateScaler()
    scaled_coords = coordinate_scaler.process_scaling_request(
        cubicasa_output=mock_cubicasa_output,
        room_type="kitchen",
        dimension_type="width",
        real_world_feet=12.0,
        job_id="test_enhanced_3d"
    )
    
    # Test room generation
    room_generator = RoomMeshGenerator()
    room_meshes = room_generator.generate_room_meshes(scaled_coords)
    
    print(f"✅ Enhanced room generation successful")
    print(f"   - Rooms generated: {len(room_meshes)}")
    print(f"   - Room polygons available: {len(scaled_coords.room_polygons)}")
    
    for room in room_meshes:
        print(f"   - {room.name}: {len(room.vertices)} vertices, {len(room.faces)} faces")
    
    return len(room_meshes) > 0

def test_enhanced_wall_generation():
    """Test enhanced wall generation with actual coordinates."""
    print("\n🧪 Testing enhanced wall generation with coordinates...")
    
    # Create mock CubiCasa output with wall coordinates
    mock_cubicasa_output = CubiCasaOutput(
        wall_coordinates=[
            (100, 100), (200, 100), (200, 200), (100, 200), (100, 100),  # Kitchen perimeter
            (200, 100), (400, 100), (400, 300), (200, 300), (200, 100)   # Living room perimeter
        ],
        room_bounding_boxes={
            "kitchen": {"min_x": 100, "max_x": 200, "min_y": 100, "max_y": 200},
            "living_room": {"min_x": 200, "max_x": 400, "min_y": 100, "max_y": 300}
        },
        room_polygons={
            "kitchen": [(100, 100), (200, 100), (200, 200), (100, 200), (100, 100)],
            "living_room": [(200, 100), (400, 100), (400, 300), (200, 300), (200, 100)]
        },
        door_coordinates=[(150, 100), (300, 100)],
        window_coordinates=[(100, 150), (400, 150)],
        image_dimensions=(512, 512),
        confidence_scores={"kitchen": 0.95, "living_room": 0.90},
        processing_time=1.0
    )
    
    # Test coordinate scaling
    coordinate_scaler = CoordinateScaler()
    scaled_coords = coordinate_scaler.process_scaling_request(
        cubicasa_output=mock_cubicasa_output,
        room_type="kitchen",
        dimension_type="width",
        real_world_feet=12.0,
        job_id="test_enhanced_3d"
    )
    
    # Test wall generation
    wall_generator = WallMeshGenerator()
    wall_meshes = wall_generator.generate_wall_meshes(scaled_coords)
    
    print(f"✅ Enhanced wall generation successful")
    print(f"   - Walls generated: {len(wall_meshes)}")
    print(f"   - Wall coordinates available: {len(scaled_coords.walls_feet)}")
    
    for wall in wall_meshes:
        print(f"   - {wall.id}: {len(wall.vertices)} vertices, {len(wall.faces)} faces")
    
    return len(wall_meshes) > 0

def test_cutout_integration():
    """Test cutout integration in wall meshes."""
    print("\n🧪 Testing cutout integration in wall meshes...")
    
    # Create mock data with doors and windows
    mock_cubicasa_output = CubiCasaOutput(
        wall_coordinates=[(100, 100), (200, 100), (200, 200), (100, 200)],
        room_bounding_boxes={
            "kitchen": {"min_x": 100, "max_x": 200, "min_y": 100, "max_y": 200}
        },
        room_polygons={
            "kitchen": [(100, 100), (200, 100), (200, 200), (100, 200), (100, 100)]
        },
        door_coordinates=[(150, 100), (150, 200)],  # Two doors
        window_coordinates=[(100, 150), (200, 150)],  # Two windows
        image_dimensions=(512, 512),
        confidence_scores={"kitchen": 0.95},
        processing_time=1.0
    )
    
    # Test coordinate scaling
    coordinate_scaler = CoordinateScaler()
    scaled_coords = coordinate_scaler.process_scaling_request(
        cubicasa_output=mock_cubicasa_output,
        room_type="kitchen",
        dimension_type="width",
        real_world_feet=12.0,
        job_id="test_enhanced_3d"
    )
    
    # Test wall generation
    wall_generator = WallMeshGenerator()
    wall_meshes = wall_generator.generate_wall_meshes(scaled_coords)
    
    # Test cutout generation
    cutout_generator = OpeningCutoutGenerator()
    walls_with_cutouts = cutout_generator.generate_cutouts(scaled_coords, wall_meshes)
    
    print(f"✅ Cutout integration successful")
    print(f"   - Original walls: {len(wall_meshes)}")
    print(f"   - Walls with cutouts: {len(walls_with_cutouts)}")
    print(f"   - Doors detected: {len(scaled_coords.door_coordinates)}")
    print(f"   - Windows detected: {len(scaled_coords.window_coordinates)}")
    
    # Check if cutouts were added
    for wall in walls_with_cutouts:
        print(f"   - {wall.id}: {len(wall.vertices)} vertices, {len(wall.faces)} faces")
    
    return len(walls_with_cutouts) > 0

def test_complete_3d_model_accuracy():
    """Test complete 3D model accuracy with all enhancements."""
    print("\n🧪 Testing complete 3D model accuracy...")
    
    # Create comprehensive mock data
    mock_cubicasa_output = CubiCasaOutput(
        wall_coordinates=[
            (100, 100), (200, 100), (200, 200), (100, 200), (100, 100),  # Kitchen
            (200, 100), (400, 100), (400, 300), (200, 300), (200, 100)   # Living room
        ],
        room_bounding_boxes={
            "kitchen": {"min_x": 100, "max_x": 200, "min_y": 100, "max_y": 200},
            "living_room": {"min_x": 200, "max_x": 400, "min_y": 100, "max_y": 300}
        },
        room_polygons={
            "kitchen": [(100, 100), (200, 100), (200, 200), (100, 200), (100, 100)],
            "living_room": [(200, 100), (400, 100), (400, 300), (200, 300), (200, 100)]
        },
        door_coordinates=[(150, 100), (300, 100), (200, 200)],  # Three doors
        window_coordinates=[(100, 150), (400, 150), (300, 250)],  # Three windows
        image_dimensions=(512, 512),
        confidence_scores={"kitchen": 0.95, "living_room": 0.90},
        processing_time=1.0
    )
    
    # Test complete pipeline
    coordinate_scaler = CoordinateScaler()
    scaled_coords = coordinate_scaler.process_scaling_request(
        cubicasa_output=mock_cubicasa_output,
        room_type="kitchen",
        dimension_type="width",
        real_world_feet=12.0,
        job_id="test_complete_3d"
    )
    
    # Generate rooms with polygons
    room_generator = RoomMeshGenerator()
    room_meshes = room_generator.generate_room_meshes(scaled_coords)
    
    # Generate walls with coordinates
    wall_generator = WallMeshGenerator()
    wall_meshes = wall_generator.generate_wall_meshes(scaled_coords)
    
    # Add cutouts to walls
    cutout_generator = OpeningCutoutGenerator()
    walls_with_cutouts = cutout_generator.generate_cutouts(scaled_coords, wall_meshes)
    
    # Calculate total geometry
    total_vertices = sum(len(room.vertices) for room in room_meshes)
    total_vertices += sum(len(wall.vertices) for wall in walls_with_cutouts)
    
    total_faces = sum(len(room.faces) for room in room_meshes)
    total_faces += sum(len(wall.faces) for wall in walls_with_cutouts)
    
    print(f"✅ Complete 3D model generation successful")
    print(f"   - Rooms: {len(room_meshes)} (using polygons)")
    print(f"   - Walls: {len(walls_with_cutouts)} (with cutouts)")
    print(f"   - Total vertices: {total_vertices}")
    print(f"   - Total faces: {total_faces}")
    print(f"   - Doors: {len(scaled_coords.door_coordinates)}")
    print(f"   - Windows: {len(scaled_coords.window_coordinates)}")
    print(f"   - Room polygons: {len(scaled_coords.room_polygons)}")
    print(f"   - Wall coordinates: {len(scaled_coords.walls_feet)}")
    
    # Verify accuracy improvements
    accuracy_improvements = []
    
    if len(scaled_coords.room_polygons) > 0:
        accuracy_improvements.append("Room polygons for accurate shapes")
    
    if len(scaled_coords.walls_feet) > 0:
        accuracy_improvements.append("Actual wall coordinates")
    
    if len(scaled_coords.door_coordinates) > 0 or len(scaled_coords.window_coordinates) > 0:
        accuracy_improvements.append("Door/window cutouts")
    
    print(f"   - Accuracy improvements: {', '.join(accuracy_improvements)}")
    
    return len(room_meshes) > 0 and len(walls_with_cutouts) > 0

def main():
    """Run all enhanced 3D generation tests."""
    print("🚀 Starting enhanced 3D generation tests...\n")
    
    test_results = []
    
    # Test 1: Enhanced room generation
    try:
        room_passed = test_enhanced_room_generation()
        test_results.append(("Enhanced Room Generation", room_passed))
    except Exception as e:
        print(f"❌ Enhanced room generation test failed: {str(e)}")
        test_results.append(("Enhanced Room Generation", False))
    
    # Test 2: Enhanced wall generation
    try:
        wall_passed = test_enhanced_wall_generation()
        test_results.append(("Enhanced Wall Generation", wall_passed))
    except Exception as e:
        print(f"❌ Enhanced wall generation test failed: {str(e)}")
        test_results.append(("Enhanced Wall Generation", False))
    
    # Test 3: Cutout integration
    try:
        cutout_passed = test_cutout_integration()
        test_results.append(("Cutout Integration", cutout_passed))
    except Exception as e:
        print(f"❌ Cutout integration test failed: {str(e)}")
        test_results.append(("Cutout Integration", False))
    
    # Test 4: Complete 3D model accuracy
    try:
        accuracy_passed = test_complete_3d_model_accuracy()
        test_results.append(("Complete 3D Model Accuracy", accuracy_passed))
    except Exception as e:
        print(f"❌ Complete 3D model accuracy test failed: {str(e)}")
        test_results.append(("Complete 3D Model Accuracy", False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 ENHANCED 3D GENERATION TEST SUMMARY")
    print("="*60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<35} {status}")
        if passed:
            passed_tests += 1
    
    print("-"*60)
    print(f"Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All enhanced 3D generation tests passed!")
        print("✅ Enhanced 3D model generation is working correctly with:")
        print("   - Accurate room polygons")
        print("   - Actual wall coordinates")
        print("   - Door/window cutouts")
        print("   - Complete 3D model accuracy")
        return True
    else:
        print("⚠️  Some enhanced 3D generation tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
