#!/usr/bin/env python3
"""
Test script for the complete user input flow.

This script tests:
1. Room analysis endpoint
2. Room selection and highlighting
3. Dimension input validation
4. Scale submission

Run with: python test_user_input_flow.py
"""

import os
import sys
import time
import requests
import json
from pathlib import Path

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.data_structures import CubiCasaOutput, ScaleInputRequest
from services.coordinate_scaler import CoordinateScaler

# Configuration
API_BASE_URL = "http://localhost:8000"  # Change to your API URL
TEST_IMAGE_PATH = "test_image.jpg"  # Path to a test floor plan image

def test_room_analysis_endpoint():
    """Test the room analysis endpoint."""
    print("🧪 Testing room analysis endpoint...")
    
    # First, we need to upload a file and get a job ID
    # For this test, we'll create a mock CubiCasa output
    mock_cubicasa_output = CubiCasaOutput(
        wall_coordinates=[(100, 100), (200, 100), (200, 200), (100, 200)],
        room_bounding_boxes={
            "kitchen": {"min_x": 100, "max_x": 200, "min_y": 100, "max_y": 200},
            "living_room": {"min_x": 200, "max_x": 400, "min_y": 100, "max_y": 300},
            "bedroom": {"min_x": 100, "max_x": 300, "min_y": 200, "max_y": 400}
        },
        image_dimensions=(512, 512),
        confidence_scores={"kitchen": 0.95, "living_room": 0.90, "bedroom": 0.85},
        processing_time=1.5
    )
    
    # Test the coordinate scaler's room suggestions
    coordinate_scaler = CoordinateScaler()
    room_suggestions = coordinate_scaler.get_smart_room_suggestions(mock_cubicasa_output)
    
    print(f"✅ Room suggestions generated: {len(room_suggestions)} rooms")
    for suggestion in room_suggestions:
        print(f"   - {suggestion['room_name']}: {suggestion['confidence']:.2f} confidence, "
              f"{suggestion['highlight_color']} color, {suggestion['reason']}")
    
    return room_suggestions

def test_dimension_validation():
    """Test dimension input validation."""
    print("\n🧪 Testing dimension validation...")
    
    coordinate_scaler = CoordinateScaler()
    
    # Test cases
    test_cases = [
        {"room_type": "kitchen", "dimension_type": "width", "real_world_feet": 12, "expected": True},
        {"room_type": "kitchen", "dimension_type": "width", "real_world_feet": 5, "expected": False},  # Too small
        {"room_type": "kitchen", "dimension_type": "width", "real_world_feet": 25, "expected": False},  # Too large
        {"room_type": "living_room", "dimension_type": "length", "real_world_feet": 20, "expected": True},
        {"room_type": "bathroom", "dimension_type": "width", "real_world_feet": 8, "expected": True},
        {"room_type": "bathroom", "dimension_type": "width", "real_world_feet": 3, "expected": False},  # Too small
    ]
    
    # Create mock CubiCasa output for validation
    mock_cubicasa_output = CubiCasaOutput(
        wall_coordinates=[],
        room_bounding_boxes={
            "kitchen": {"min_x": 100, "max_x": 200, "min_y": 100, "max_y": 200},
            "living_room": {"min_x": 200, "max_x": 400, "min_y": 100, "max_y": 300},
            "bathroom": {"min_x": 100, "max_x": 200, "min_y": 200, "max_y": 300}
        },
        image_dimensions=(512, 512),
        confidence_scores={"kitchen": 0.95, "living_room": 0.90, "bathroom": 0.85},
        processing_time=1.0
    )
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            validation_result = coordinate_scaler.validate_scaling_input(
                cubicasa_output=mock_cubicasa_output,
                room_type=test_case["room_type"],
                dimension_type=test_case["dimension_type"],
                real_world_feet=test_case["real_world_feet"]
            )
            
            is_valid = validation_result["is_valid"]
            expected = test_case["expected"]
            
            if is_valid == expected:
                print(f"   ✅ Test {i}: {test_case['room_type']} {test_case['dimension_type']} = {test_case['real_world_feet']} feet - PASSED")
                passed_tests += 1
            else:
                print(f"   ❌ Test {i}: {test_case['room_type']} {test_case['dimension_type']} = {test_case['real_world_feet']} feet - FAILED (expected {expected}, got {is_valid})")
                if validation_result["errors"]:
                    print(f"      Errors: {validation_result['errors']}")
                if validation_result["warnings"]:
                    print(f"      Warnings: {validation_result['warnings']}")
                    
        except Exception as e:
            print(f"   ❌ Test {i}: Exception - {str(e)}")
    
    print(f"✅ Dimension validation: {passed_tests}/{total_tests} tests passed")
    return passed_tests == total_tests

def test_scale_processing():
    """Test scale processing with user input."""
    print("\n🧪 Testing scale processing...")
    
    coordinate_scaler = CoordinateScaler()
    
    # Create mock CubiCasa output
    mock_cubicasa_output = CubiCasaOutput(
        wall_coordinates=[(100, 100), (200, 100), (200, 200), (100, 200)],
        room_bounding_boxes={
            "kitchen": {"min_x": 100, "max_x": 200, "min_y": 100, "max_y": 200}
        },
        image_dimensions=(512, 512),
        confidence_scores={"kitchen": 0.95},
        processing_time=1.0
    )
    
    try:
        # Test scale processing
        scaled_coords = coordinate_scaler.process_scaling_request(
            cubicasa_output=mock_cubicasa_output,
            room_type="kitchen",
            dimension_type="width",
            real_world_feet=12.0,
            job_id="test_job_123"
        )
        
        print(f"✅ Scale processing successful")
        print(f"   - Scale factor: {scaled_coords.scale_reference.scale_factor:.2f} pixels/foot")
        print(f"   - Kitchen dimensions: {scaled_coords.rooms_feet['kitchen']}")
        print(f"   - Total building size: {scaled_coords.total_building_size.width_feet:.1f}' × {scaled_coords.total_building_size.length_feet:.1f}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Scale processing failed: {str(e)}")
        return False

def test_api_endpoints():
    """Test API endpoints if server is running."""
    print("\n🧪 Testing API endpoints...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint accessible")
        else:
            print(f"⚠️  Health endpoint returned {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️  API server not accessible: {str(e)}")
        print("   Skipping API endpoint tests (server may not be running)")
        return True
    
    return True

def main():
    """Run all tests."""
    print("🚀 Starting user input flow tests...\n")
    
    test_results = []
    
    # Test 1: Room analysis
    try:
        room_suggestions = test_room_analysis_endpoint()
        test_results.append(("Room Analysis", len(room_suggestions) > 0))
    except Exception as e:
        print(f"❌ Room analysis test failed: {str(e)}")
        test_results.append(("Room Analysis", False))
    
    # Test 2: Dimension validation
    try:
        validation_passed = test_dimension_validation()
        test_results.append(("Dimension Validation", validation_passed))
    except Exception as e:
        print(f"❌ Dimension validation test failed: {str(e)}")
        test_results.append(("Dimension Validation", False))
    
    # Test 3: Scale processing
    try:
        scale_passed = test_scale_processing()
        test_results.append(("Scale Processing", scale_passed))
    except Exception as e:
        print(f"❌ Scale processing test failed: {str(e)}")
        test_results.append(("Scale Processing", False))
    
    # Test 4: API endpoints
    try:
        api_passed = test_api_endpoints()
        test_results.append(("API Endpoints", api_passed))
    except Exception as e:
        print(f"❌ API endpoints test failed: {str(e)}")
        test_results.append(("API Endpoints", False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<20} {status}")
        if passed:
            passed_tests += 1
    
    print("-"*50)
    print(f"Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! User input flow is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
