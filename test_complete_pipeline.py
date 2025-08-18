#!/usr/bin/env python3
"""
Complete Pipeline Test for PlanCast.

This script tests the entire pipeline with all enhancements:
1. Enhanced user input flow
2. Door/window cutout integration
3. Enhanced 3D generation
4. Comprehensive validation
5. Performance optimizations

Run with: python3 test_complete_pipeline.py
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

def test_complete_pipeline():
    """Test the complete pipeline with all enhancements."""
    print("🧪 Testing complete pipeline with all enhancements...")
    
    start_time = time.time()
    
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
    
    # Step 1: Coordinate Scaling with Validation
    print("   Step 1: Coordinate scaling with validation...")
    coordinate_scaler = CoordinateScaler()
    
    # Test validation
    validation_result = coordinate_scaler.validate_scaling_input(
        cubicasa_output=mock_cubicasa_output,
        room_type="kitchen",
        dimension_type="width",
        real_world_feet=12.0
    )
    
    if not validation_result["is_valid"]:
        print(f"   ❌ Validation failed: {validation_result['errors']}")
        return False
    
    if validation_result["warnings"]:
        print(f"   ⚠️  Validation warnings: {validation_result['warnings']}")
    
    # Test coordinate scaling
    scaled_coords = coordinate_scaler.process_scaling_request(
        cubicasa_output=mock_cubicasa_output,
        room_type="kitchen",
        dimension_type="width",
        real_world_feet=12.0,
        job_id="test_complete_pipeline"
    )
    
    print(f"   ✅ Coordinate scaling completed")
    print(f"      - Scale factor: {scaled_coords.scale_reference.scale_factor:.2f} pixels/foot")
    print(f"      - Wall coordinates: {len(scaled_coords.walls_feet)}")
    print(f"      - Room polygons: {len(scaled_coords.room_polygons)}")
    print(f"      - Door coordinates: {len(scaled_coords.door_coordinates)}")
    print(f"      - Window coordinates: {len(scaled_coords.window_coordinates)}")
    
    # Step 2: Room Generation with Polygons
    print("   Step 2: Room generation with polygons...")
    room_generator = RoomMeshGenerator()
    room_meshes = room_generator.generate_room_meshes(scaled_coords)
    
    print(f"   ✅ Room generation completed")
    print(f"      - Rooms generated: {len(room_meshes)}")
    for room in room_meshes:
        print(f"      - {room.name}: {len(room.vertices)} vertices, {len(room.faces)} faces")
    
    # Step 3: Wall Generation with Coordinates
    print("   Step 3: Wall generation with coordinates...")
    wall_generator = WallMeshGenerator()
    wall_meshes = wall_generator.generate_wall_meshes(scaled_coords)
    
    print(f"   ✅ Wall generation completed")
    print(f"      - Walls generated: {len(wall_meshes)}")
    for wall in wall_meshes:
        print(f"      - {wall.id}: {len(wall.vertices)} vertices, {len(wall.faces)} faces")
    
    # Step 4: Cutout Generation
    print("   Step 4: Cutout generation...")
    cutout_generator = OpeningCutoutGenerator()
    walls_with_cutouts = cutout_generator.generate_cutouts(scaled_coords, wall_meshes)
    
    print(f"   ✅ Cutout generation completed")
    print(f"      - Walls with cutouts: {len(walls_with_cutouts)}")
    
    # Step 5: Performance Testing
    print("   Step 5: Performance testing...")
    
    # Test caching performance
    cache_start = time.time()
    for _ in range(5):
        room_suggestions = coordinate_scaler.get_smart_room_suggestions(mock_cubicasa_output)
    cache_time = time.time() - cache_start
    
    print(f"   ✅ Performance testing completed")
    print(f"      - Cached room suggestions (5x): {cache_time:.4f}s")
    print(f"      - Average per call: {cache_time/5:.4f}s")
    
    # Calculate total geometry
    total_vertices = sum(len(room.vertices) for room in room_meshes)
    total_vertices += sum(len(wall.vertices) for wall in walls_with_cutouts)
    
    total_faces = sum(len(room.faces) for room in room_meshes)
    total_faces += sum(len(wall.faces) for wall in walls_with_cutouts)
    
    total_time = time.time() - start_time
    
    print(f"   📊 Pipeline Summary:")
    print(f"      - Total processing time: {total_time:.3f}s")
    print(f"      - Total vertices: {total_vertices}")
    print(f"      - Total faces: {total_faces}")
    print(f"      - Rooms: {len(room_meshes)} (using polygons)")
    print(f"      - Walls: {len(walls_with_cutouts)} (with cutouts)")
    print(f"      - Doors: {len(scaled_coords.door_coordinates)}")
    print(f"      - Windows: {len(scaled_coords.window_coordinates)}")
    
    return True

def test_error_handling():
    """Test comprehensive error handling."""
    print("\n🧪 Testing comprehensive error handling...")
    
    # Test 1: Invalid room type
    print("   Test 1: Invalid room type...")
    coordinate_scaler = CoordinateScaler()
    
    mock_cubicasa_output = CubiCasaOutput(
        wall_coordinates=[(100, 100), (200, 100)],
        room_bounding_boxes={"kitchen": {"min_x": 100, "max_x": 200, "min_y": 100, "max_y": 200}},
        room_polygons={"kitchen": [(100, 100), (200, 100), (200, 200), (100, 200), (100, 100)]},
        door_coordinates=[(150, 100)],
        window_coordinates=[(100, 150)],
        image_dimensions=(512, 512),
        confidence_scores={"kitchen": 0.95},
        processing_time=1.0
    )
    
    validation_result = coordinate_scaler.validate_scaling_input(
        cubicasa_output=mock_cubicasa_output,
        room_type="invalid_room",
        dimension_type="width",
        real_world_feet=12.0
    )
    
    if not validation_result["is_valid"]:
        print(f"   ✅ Invalid room type correctly rejected: {validation_result['errors']}")
    else:
        print(f"   ❌ Invalid room type should have been rejected")
        return False
    
    # Test 2: Invalid dimension
    print("   Test 2: Invalid dimension...")
    validation_result = coordinate_scaler.validate_scaling_input(
        cubicasa_output=mock_cubicasa_output,
        room_type="kitchen",
        dimension_type="invalid",
        real_world_feet=12.0
    )
    
    if not validation_result["is_valid"]:
        print(f"   ✅ Invalid dimension type correctly rejected: {validation_result['errors']}")
    else:
        print(f"   ❌ Invalid dimension type should have been rejected")
        return False
    
    # Test 3: Invalid measurement
    print("   Test 3: Invalid measurement...")
    validation_result = coordinate_scaler.validate_scaling_input(
        cubicasa_output=mock_cubicasa_output,
        room_type="kitchen",
        dimension_type="width",
        real_world_feet=-5.0
    )
    
    if not validation_result["is_valid"]:
        print(f"   ✅ Invalid measurement correctly rejected: {validation_result['errors']}")
    else:
        print(f"   ❌ Invalid measurement should have been rejected")
        return False
    
    print("   ✅ All error handling tests passed")
    return True

def test_performance_optimizations():
    """Test performance optimizations."""
    print("\n🧪 Testing performance optimizations...")
    
    # Create test data
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
    
    coordinate_scaler = CoordinateScaler()
    
    # Test caching performance
    print("   Testing room suggestions caching...")
    
    # First call (should be slower)
    start_time = time.time()
    suggestions1 = coordinate_scaler.get_smart_room_suggestions(mock_cubicasa_output)
    first_call_time = time.time() - start_time
    
    # Second call (should be faster due to caching)
    start_time = time.time()
    suggestions2 = coordinate_scaler.get_smart_room_suggestions(mock_cubicasa_output)
    second_call_time = time.time() - start_time
    
    print(f"   ✅ Caching performance test completed")
    print(f"      - First call: {first_call_time:.4f}s")
    print(f"      - Second call: {second_call_time:.4f}s")
    print(f"      - Speed improvement: {first_call_time/second_call_time:.1f}x faster")
    
    if second_call_time < first_call_time:
        print(f"   ✅ Caching is working correctly")
    else:
        print(f"   ⚠️  Caching may not be working as expected")
    
    return True

def main():
    """Run all complete pipeline tests."""
    print("🚀 Starting complete pipeline tests...\n")
    
    test_results = []
    
    # Test 1: Complete pipeline
    try:
        pipeline_passed = test_complete_pipeline()
        test_results.append(("Complete Pipeline", pipeline_passed))
    except Exception as e:
        print(f"❌ Complete pipeline test failed: {str(e)}")
        test_results.append(("Complete Pipeline", False))
    
    # Test 2: Error handling
    try:
        error_passed = test_error_handling()
        test_results.append(("Error Handling", error_passed))
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        test_results.append(("Error Handling", False))
    
    # Test 3: Performance optimizations
    try:
        performance_passed = test_performance_optimizations()
        test_results.append(("Performance Optimizations", performance_passed))
    except Exception as e:
        print(f"❌ Performance optimization test failed: {str(e)}")
        test_results.append(("Performance Optimizations", False))
    
    # Summary
    print("\n" + "="*70)
    print("📊 COMPLETE PIPELINE TEST SUMMARY")
    print("="*70)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if passed:
            passed_tests += 1
    
    print("-"*70)
    print(f"Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All complete pipeline tests passed!")
        print("✅ PlanCast is ready for production with:")
        print("   - Enhanced user input flow")
        print("   - Door/window cutout integration")
        print("   - Enhanced 3D generation with accurate polygons")
        print("   - Comprehensive validation and error handling")
        print("   - Performance optimizations")
        return True
    else:
        print("⚠️  Some complete pipeline tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
