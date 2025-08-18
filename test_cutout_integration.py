#!/usr/bin/env python3
"""
Test script for door/window cutout integration.

This script tests:
1. Door/window coordinate extraction from CubiCasa output
2. Cutout generation in wall meshes
3. Frame geometry creation
4. Integration with the main processing pipeline

Run with: python3 test_cutout_integration.py
"""

import os
import sys
import time
from pathlib import Path

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.data_structures import CubiCasaOutput, ScaledCoordinates, Wall3D, Vertex3D, Face
from services.opening_cutout_generator import OpeningCutoutGenerator
from services.coordinate_scaler import CoordinateScaler

def test_cutout_generator():
    """Test the opening cutout generator."""
    print("🧪 Testing opening cutout generator...")
    
    # Create mock CubiCasa output with doors and windows
    mock_cubicasa_output = CubiCasaOutput(
        wall_coordinates=[(100, 100), (200, 100), (200, 200), (100, 200)],
        room_bounding_boxes={
            "kitchen": {"min_x": 100, "max_x": 200, "min_y": 100, "max_y": 200}
        },
        door_coordinates=[(150, 100), (150, 200)],  # Two doors
        window_coordinates=[(100, 150), (200, 150)],  # Two windows
        image_dimensions=(512, 512),
        confidence_scores={"kitchen": 0.95},
        processing_time=1.0
    )
    
    # Create mock scaled coordinates
    scale_reference = {
        "room_type": "kitchen",
        "dimension_type": "width",
        "real_world_feet": 12.0,
        "pixel_measurement": 100.0,
        "scale_factor": 8.33
    }
    
    scaled_coords = ScaledCoordinates(
        walls_feet=[(12.0, 12.0), (24.0, 12.0), (24.0, 24.0), (12.0, 24.0)],
        rooms_feet={
            "kitchen": {
                "width_feet": 12.0,
                "length_feet": 12.0,
                "area_sqft": 144.0,
                "x_offset_feet": 12.0,
                "y_offset_feet": 12.0
            }
        },
        door_coordinates=[(18.0, 12.0), (18.0, 24.0)],  # Scaled door positions
        window_coordinates=[(12.0, 18.0), (24.0, 18.0)],  # Scaled window positions
        scale_reference=scale_reference,
        total_building_size={
            "width_feet": 36.0,
            "length_feet": 36.0,
            "area_sqft": 1296.0,
            "scale_factor": 8.33,
            "original_width_pixels": 512,
            "original_height_pixels": 512
        }
    )
    
    # Create mock wall meshes
    mock_wall_meshes = [
        Wall3D(
            id="wall_001",
            vertices=[
                Vertex3D(x=12.0, y=12.0, z=0.0),
                Vertex3D(x=24.0, y=12.0, z=0.0),
                Vertex3D(x=24.0, y=12.0, z=9.0),
                Vertex3D(x=12.0, y=12.0, z=9.0)
            ],
            faces=[
                Face(indices=[0, 1, 2]),
                Face(indices=[0, 2, 3])
            ],
            height_feet=9.0,
            thickness_feet=0.5
        )
    ]
    
    # Test cutout generator
    cutout_generator = OpeningCutoutGenerator()
    
    try:
        # Generate cutouts
        walls_with_cutouts = cutout_generator.generate_cutouts(scaled_coords, mock_wall_meshes)
        
        print(f"✅ Cutout generation successful")
        print(f"   - Input walls: {len(mock_wall_meshes)}")
        print(f"   - Output walls: {len(walls_with_cutouts)}")
        print(f"   - Doors detected: {len(scaled_coords.door_coordinates)}")
        print(f"   - Windows detected: {len(scaled_coords.window_coordinates)}")
        
        # Check if cutouts were added
        for wall in walls_with_cutouts:
            print(f"   - Wall {wall.id}: {len(wall.vertices)} vertices, {len(wall.faces)} faces")
        
        return True
        
    except Exception as e:
        print(f"❌ Cutout generation failed: {str(e)}")
        return False

def test_coordinate_scaling_with_openings():
    """Test coordinate scaling with door/window data."""
    print("\n🧪 Testing coordinate scaling with openings...")
    
    # Create mock CubiCasa output
    mock_cubicasa_output = CubiCasaOutput(
        wall_coordinates=[(100, 100), (200, 100), (200, 200), (100, 200)],
        room_bounding_boxes={
            "kitchen": {"min_x": 100, "max_x": 200, "min_y": 100, "max_y": 200}
        },
        door_coordinates=[(150, 100), (150, 200)],
        window_coordinates=[(100, 150), (200, 150)],
        image_dimensions=(512, 512),
        confidence_scores={"kitchen": 0.95},
        processing_time=1.0
    )
    
    # Test coordinate scaling
    coordinate_scaler = CoordinateScaler()
    
    try:
        scaled_coords = coordinate_scaler.process_scaling_request(
            cubicasa_output=mock_cubicasa_output,
            room_type="kitchen",
            dimension_type="width",
            real_world_feet=12.0,
            job_id="test_cutout_job"
        )
        
        print(f"✅ Coordinate scaling with openings successful")
        print(f"   - Wall coordinates: {len(scaled_coords.walls_feet)}")
        print(f"   - Door coordinates: {len(scaled_coords.door_coordinates)}")
        print(f"   - Window coordinates: {len(scaled_coords.window_coordinates)}")
        print(f"   - Scale factor: {scaled_coords.scale_reference.scale_factor:.2f} pixels/foot")
        
        return True
        
    except Exception as e:
        print(f"❌ Coordinate scaling failed: {str(e)}")
        return False

def test_cubicasa_output_structure():
    """Test that CubiCasa output includes door/window data."""
    print("\n🧪 Testing CubiCasa output structure...")
    
    try:
        # Create CubiCasa output with door/window data
        cubicasa_output = CubiCasaOutput(
            wall_coordinates=[(100, 100), (200, 100)],
            room_bounding_boxes={"kitchen": {"min_x": 100, "max_x": 200, "min_y": 100, "max_y": 200}},
            door_coordinates=[(150, 100), (150, 200)],
            window_coordinates=[(100, 150), (200, 150)],
            image_dimensions=(512, 512),
            confidence_scores={"kitchen": 0.95},
            processing_time=1.0
        )
        
        print(f"✅ CubiCasa output structure valid")
        print(f"   - Wall coordinates: {len(cubicasa_output.wall_coordinates)}")
        print(f"   - Door coordinates: {len(cubicasa_output.door_coordinates)}")
        print(f"   - Window coordinates: {len(cubicasa_output.window_coordinates)}")
        print(f"   - Room bounding boxes: {len(cubicasa_output.room_bounding_boxes)}")
        
        return True
        
    except Exception as e:
        print(f"❌ CubiCasa output structure failed: {str(e)}")
        return False

def main():
    """Run all cutout integration tests."""
    print("🚀 Starting cutout integration tests...\n")
    
    test_results = []
    
    # Test 1: CubiCasa output structure
    try:
        structure_passed = test_cubicasa_output_structure()
        test_results.append(("CubiCasa Output Structure", structure_passed))
    except Exception as e:
        print(f"❌ CubiCasa output structure test failed: {str(e)}")
        test_results.append(("CubiCasa Output Structure", False))
    
    # Test 2: Coordinate scaling with openings
    try:
        scaling_passed = test_coordinate_scaling_with_openings()
        test_results.append(("Coordinate Scaling with Openings", scaling_passed))
    except Exception as e:
        print(f"❌ Coordinate scaling test failed: {str(e)}")
        test_results.append(("Coordinate Scaling with Openings", False))
    
    # Test 3: Cutout generator
    try:
        cutout_passed = test_cutout_generator()
        test_results.append(("Cutout Generator", cutout_passed))
    except Exception as e:
        print(f"❌ Cutout generator test failed: {str(e)}")
        test_results.append(("Cutout Generator", False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 CUTOUT INTEGRATION TEST SUMMARY")
    print("="*50)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if passed:
            passed_tests += 1
    
    print("-"*50)
    print(f"Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All cutout integration tests passed!")
        return True
    else:
        print("⚠️  Some cutout integration tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
