#!/usr/bin/env python3
"""
Complete PlanCast Deployment Test
Tests core components using actual service outputs for Railway deployment validation.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment():
    """Test environment and dependencies."""
    logger.info("🔍 Testing environment...")
    
    try:
        import torch
        logger.info(f"✅ PyTorch: {torch.__version__}")
        
        import cv2
        logger.info(f"✅ OpenCV: {cv2.__version__}")
        
        import numpy as np
        logger.info(f"✅ NumPy: {np.__version__}")
        
        import trimesh
        logger.info(f"✅ Trimesh: {trimesh.__version__}")
        
        logger.info("✅ Environment test passed")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Environment test failed: {str(e)}")
        return False

def test_model_file():
    """Test model file integrity."""
    logger.info("🔍 Testing model file...")
    
    model_path = Path("assets/models/model_best_val_loss_var.pkl")
    
    if not model_path.exists():
        logger.error(f"❌ Model file not found: {model_path}")
        return False
    
    file_size = model_path.stat().st_size
    file_size_mb = file_size / (1024 * 1024)
    
    logger.info(f"✅ Model file found: {file_size_mb:.2f} MB")
    
    if 50 <= file_size_mb <= 1000:
        logger.info("✅ Model file size is reasonable")
        return True
    else:
        logger.warning(f"⚠️ Model file size seems unusual: {file_size_mb:.2f} MB")
        return False

def test_cubicasa_service():
    """Test CubiCasa service."""
    logger.info("🔍 Testing CubiCasa service...")
    
    try:
        from services.cubicasa_service import CubiCasaService
        service = CubiCasaService()
        
        # Test health check
        health = service.health_check()
        logger.info(f"✅ CubiCasa health: {health['status']}")
        
        if health['status'] == 'healthy':
            logger.info("✅ CubiCasa service test passed")
            return True
        else:
            logger.error(f"❌ CubiCasa health check failed: {health.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ CubiCasa service test failed: {str(e)}")
        return False

def test_coordinate_scaler():
    """Test coordinate scaler service."""
    logger.info("🔍 Testing coordinate scaler...")
    
    try:
        from services.coordinate_scaler import CoordinateScaler
        scaler = CoordinateScaler()
        
        # Test with mock data
        from models.data_structures import CubiCasaOutput
        
        mock_output = CubiCasaOutput(
            wall_coordinates=[(100, 100), (200, 100), (200, 200), (100, 200)],
            room_bounding_boxes={
                "kitchen": {"min_x": 100, "max_x": 300, "min_y": 100, "max_y": 300}
            },
            image_dimensions=(400, 400),
            confidence_scores={"kitchen": 0.9},
            processing_time=1.0
        )
        
        # Use the actual coordinate scaler
        result = scaler.process_scaling_request(
            mock_output, "kitchen", "width", 10.0, "test_job"
        )
        logger.info("✅ Coordinate scaler test passed")
        return result  # Return the actual result for other tests
        
    except Exception as e:
        logger.error(f"❌ Coordinate scaler test failed: {str(e)}")
        return None

def test_room_generator(scaled_coords):
    """Test room generator service."""
    logger.info("🔍 Testing room generator...")
    
    if scaled_coords is None:
        logger.error("❌ Room generator test failed: No scaled coordinates from previous test")
        return False
    
    try:
        from services.room_generator import RoomMeshGenerator
        generator = RoomMeshGenerator()
        
        # Use the actual scaled coordinates from coordinate scaler
        rooms = generator.generate_room_meshes(scaled_coords)
        logger.info(f"✅ Room generator created {len(rooms)} rooms")
        return True
        
    except Exception as e:
        logger.error(f"❌ Room generator test failed: {str(e)}")
        return False

def test_wall_generator(scaled_coords):
    """Test wall generator service."""
    logger.info("🔍 Testing wall generator...")
    
    if scaled_coords is None:
        logger.error("❌ Wall generator test failed: No scaled coordinates from previous test")
        return False
    
    try:
        from services.wall_generator import WallMeshGenerator
        generator = WallMeshGenerator()
        
        # Use the actual scaled coordinates from coordinate scaler
        walls = generator.generate_wall_meshes(scaled_coords)
        logger.info(f"✅ Wall generator created {len(walls)} walls")
        return True
        
    except Exception as e:
        logger.error(f"❌ Wall generator test failed: {str(e)}")
        return False

def test_mesh_exporter():
    """Test mesh exporter service."""
    logger.info("🔍 Testing mesh exporter...")
    
    try:
        from services.mesh_exporter import MeshExporter
        exporter = MeshExporter()
        
        # Create mock building
        from models.data_structures import Building3D, Room3D, Wall3D, Vertex3D, Face
        
        # Create mock room
        mock_room = Room3D(
            name="kitchen",
            vertices=[Vertex3D(x=0, y=0, z=0), Vertex3D(x=10, y=0, z=0), Vertex3D(x=10, y=8, z=0)],
            faces=[Face(indices=[0, 1, 2])],
            elevation_feet=0.0,
            height_feet=9.0
        )
        
        # Create mock wall
        mock_wall = Wall3D(
            id="wall_1",
            vertices=[Vertex3D(x=0, y=0, z=0), Vertex3D(x=10, y=0, z=0), Vertex3D(x=10, y=0, z=9)],
            faces=[Face(indices=[0, 1, 2])],
            height_feet=9.0,
            thickness_feet=0.5
        )
        
        mock_building = Building3D(
            rooms=[mock_room],
            walls=[mock_wall],
            total_vertices=6,
            total_faces=2,
            bounding_box={"min_x": 0, "max_x": 20, "min_y": 0, "max_y": 15, "min_z": 0, "max_z": 9}
        )
        
        # Test export to temporary directory
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            result = exporter.export_building(mock_building, ["obj"], temp_dir)
            logger.info(f"✅ Mesh exporter created {len(result.files)} files")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Mesh exporter test failed: {str(e)}")
        return False

def main():
    """Main test function."""
    logger.info("🚀 Starting Complete PlanCast Deployment Tests")
    
    start_time = time.time()
    results = {}
    
    # Test 1: Environment
    results["environment"] = test_environment()
    
    # Test 2: Model file
    results["model_file"] = test_model_file()
    
    # Test 3: CubiCasa service
    results["cubicasa"] = test_cubicasa_service()
    
    # Test 4: Coordinate scaler (returns actual result for other tests)
    scaled_coords = test_coordinate_scaler()
    results["coordinate_scaler"] = scaled_coords is not None
    
    # Test 5: Room generator (uses actual scaled coordinates)
    results["room_generator"] = test_room_generator(scaled_coords)
    
    # Test 6: Wall generator (uses actual scaled coordinates)
    results["wall_generator"] = test_wall_generator(scaled_coords)
    
    # Test 7: Mesh exporter
    results["mesh_exporter"] = test_mesh_exporter()
    
    # Calculate overall results
    total_time = time.time() - start_time
    passed_tests = sum(1 for result in results.values() if result is True)
    total_tests = len(results)
    
    overall_success = passed_tests == total_tests
    
    # Log results
    logger.info("📊 Test Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result is True else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"⏱️ Total test time: {total_time:.2f}s")
    
    if overall_success:
        logger.info("🎉 ALL TESTS PASSED - PlanCast is ready for Railway deployment!")
    else:
        logger.error(f"❌ {total_tests - passed_tests} TESTS FAILED - Review issues before deployment")
    
    # Exit with appropriate code
    sys.exit(0 if overall_success else 1)

if __name__ == "__main__":
    main()
