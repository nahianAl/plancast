#!/usr/bin/env python3
"""
PlanCast Deployment Test Script
Tests the full pipeline with a sample image for Railway deployment validation.
"""

import os
import sys
import time
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.cubicasa_service import CubiCasaService
from services.coordinate_scaler import CoordinateScaler
from services.room_generator import RoomMeshGenerator
from services.wall_generator import WallMeshGenerator
from services.mesh_exporter import MeshExporter
from core.floorplan_processor import FloorPlanProcessor
from utils.logger import get_logger

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeploymentTester:
    """Comprehensive deployment testing for PlanCast pipeline."""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
    def test_environment(self) -> bool:
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
            
            self.test_results["environment"] = True
            return True
            
        except ImportError as e:
            logger.error(f"❌ Environment test failed: {str(e)}")
            self.test_results["environment"] = False
            return False
    
    def test_model_file(self) -> bool:
        """Test model file integrity."""
        logger.info("🔍 Testing model file...")
        
        model_path = Path("assets/models/model_best_val_loss_var.pkl")
        
        if not model_path.exists():
            logger.error(f"❌ Model file not found: {model_path}")
            self.test_results["model_file"] = False
            return False
        
        file_size = model_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        logger.info(f"✅ Model file found: {file_size_mb:.2f} MB")
        
        if 50 <= file_size_mb <= 1000:
            logger.info("✅ Model file size is reasonable")
            self.test_results["model_file"] = True
            return True
        else:
            logger.warning(f"⚠️ Model file size seems unusual: {file_size_mb:.2f} MB")
            self.test_results["model_file"] = False
            return False
    
    def test_cubicasa_service(self) -> bool:
        """Test CubiCasa service."""
        logger.info("🔍 Testing CubiCasa service...")
        
        try:
            service = CubiCasaService()
            
            # Test health check
            health = service.health_check()
            logger.info(f"✅ CubiCasa health: {health['status']}")
            
            if health['status'] == 'healthy':
                self.test_results["cubicasa"] = True
                return True
            else:
                logger.error(f"❌ CubiCasa health check failed: {health.get('error', 'Unknown error')}")
                self.test_results["cubicasa"] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ CubiCasa service test failed: {str(e)}")
            self.test_results["cubicasa"] = False
            return False
    
    def test_coordinate_scaler(self) -> bool:
        """Test coordinate scaler service."""
        logger.info("🔍 Testing coordinate scaler...")
        
        try:
            scaler = CoordinateScaler()
            
            # Test with mock data
            from models.data_structures import ScaleReference
            
            scale_ref = ScaleReference(
                room_type="kitchen",
                dimension_type="width",
                real_world_feet=10.0,
                pixel_measurement=200
            )
            
            # Mock CubiCasa output
            from models.data_structures import CubiCasaOutput
            
            mock_output = CubiCasaOutput(
                wall_coordinates=[(100, 100), (200, 100), (200, 200), (100, 200)],
                room_bounding_boxes={
                    "kitchen": {"min_x": 0, "max_x": 200, "min_y": 0, "max_y": 200}
                },
                image_dimensions=(400, 400),
                confidence_scores={"kitchen": 0.9},
                processing_time=1.0
            )
            
            result = scaler.scale_coordinates(mock_output, scale_ref)
            logger.info("✅ Coordinate scaler test passed")
            
            self.test_results["coordinate_scaler"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Coordinate scaler test failed: {str(e)}")
            self.test_results["coordinate_scaler"] = False
            return False
    
    def test_room_generator(self) -> bool:
        """Test room generator service."""
        logger.info("🔍 Testing room generator...")
        
        try:
            generator = RoomMeshGenerator()
            
            # Test with mock scaled coordinates
            from models.data_structures import ScaledCoordinates, BuildingDimensions
            
            mock_coords = ScaledCoordinates(
                scale_reference=ScaleReference(
                    room_type="kitchen",
                    dimension_type="width",
                    real_world_feet=10.0,
                    pixel_measurement=200
                ),
                walls_feet=[(5.0, 5.0), (15.0, 5.0), (15.0, 10.0), (5.0, 10.0)],
                rooms_feet={
                    "kitchen": {"min_x": 0, "max_x": 10, "min_y": 0, "max_y": 8}
                },
                total_building_size=BuildingDimensions(
                    width_feet=20.0,
                    height_feet=15.0,
                    area_sq_feet=300.0
                )
            )
            
            rooms = generator.generate_room_meshes(mock_coords)
            logger.info(f"✅ Room generator created {len(rooms)} rooms")
            
            self.test_results["room_generator"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Room generator test failed: {str(e)}")
            self.test_results["room_generator"] = False
            return False
    
    def test_wall_generator(self) -> bool:
        """Test wall generator service."""
        logger.info("🔍 Testing wall generator...")
        
        try:
            generator = WallMeshGenerator()
            
            # Use the same mock coordinates from room generator test
            walls = generator.generate_wall_meshes(mock_coords)
            logger.info(f"✅ Wall generator created {len(walls)} walls")
            
            self.test_results["wall_generator"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Wall generator test failed: {str(e)}")
            self.test_results["wall_generator"] = False
            return False
    
    def test_mesh_exporter(self) -> bool:
        """Test mesh exporter service."""
        logger.info("🔍 Testing mesh exporter...")
        
        try:
            exporter = MeshExporter()
            
            # Create mock building
            from models.data_structures import Building3D
            
            mock_building = Building3D(
                rooms=rooms,  # From room generator test
                walls=walls,  # From wall generator test
                total_vertices=100,
                total_faces=50,
                bounding_box={"min_x": 0, "max_x": 20, "min_y": 0, "max_y": 15, "min_z": 0, "max_z": 9}
            )
            
            # Test export to temporary directory
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                result = exporter.export_building(mock_building, ["obj"], temp_dir)
                logger.info(f"✅ Mesh exporter created {len(result.exported_files)} files")
            
            self.test_results["mesh_exporter"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Mesh exporter test failed: {str(e)}")
            self.test_results["mesh_exporter"] = False
            return False
    
    def test_full_pipeline(self) -> bool:
        """Test the complete pipeline."""
        logger.info("🔍 Testing full pipeline...")
        
        try:
            processor = FloorPlanProcessor()
            
            # Create a simple test image
            from PIL import Image
            import io
            
            # Create a white image
            test_image = Image.new('RGB', (400, 400), color='white')
            image_bytes = io.BytesIO()
            test_image.save(image_bytes, format='PNG')
            image_bytes = image_bytes.getvalue()
            
            # Test the pipeline
            job_id = "test_deployment"
            result = processor.process_floor_plan(image_bytes, job_id)
            
            logger.info("✅ Full pipeline test passed")
            
            self.test_results["full_pipeline"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Full pipeline test failed: {str(e)}")
            self.test_results["full_pipeline"] = False
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test API endpoints if running."""
        logger.info("🔍 Testing API endpoints...")
        
        try:
            # Try to connect to local API
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ API health endpoint accessible")
                self.test_results["api_endpoints"] = True
                return True
            else:
                logger.warning(f"⚠️ API health endpoint returned {response.status_code}")
                self.test_results["api_endpoints"] = False
                return False
                
        except requests.exceptions.RequestException:
            logger.info("ℹ️ API not running (this is normal for deployment tests)")
            self.test_results["api_endpoints"] = None
            return True  # Not a failure if API isn't running
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all deployment tests."""
        logger.info("🚀 Starting PlanCast Deployment Tests")
        
        tests = [
            ("environment", self.test_environment),
            ("model_file", self.test_model_file),
            ("cubicasa", self.test_cubicasa_service),
            ("coordinate_scaler", self.test_coordinate_scaler),
            ("room_generator", self.test_room_generator),
            ("wall_generator", self.test_wall_generator),
            ("mesh_exporter", self.test_mesh_exporter),
            ("full_pipeline", self.test_full_pipeline),
            ("api_endpoints", self.test_api_endpoints)
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                logger.error(f"❌ {test_name} test crashed: {str(e)}")
                self.test_results[test_name] = False
        
        # Calculate overall results
        total_time = time.time() - self.start_time
        passed_tests = sum(1 for result in self.test_results.values() if result is True)
        total_tests = len([r for r in self.test_results.values() if r is not None])
        
        overall_success = passed_tests == total_tests
        
        results = {
            "overall_success": overall_success,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "test_time_seconds": round(total_time, 2),
            "test_results": self.test_results
        }
        
        # Log results
        logger.info("📊 Test Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result is True else "❌ FAIL" if result is False else "ℹ️ SKIP"
            logger.info(f"  {test_name}: {status}")
        
        logger.info(f"⏱️ Total test time: {total_time:.2f}s")
        
        if overall_success:
            logger.info("🎉 ALL TESTS PASSED - PlanCast is ready for deployment!")
        else:
            logger.error(f"❌ {total_tests - passed_tests} TESTS FAILED - Review issues before deployment")
        
        return results

def main():
    """Main test function."""
    tester = DeploymentTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_success"] else 1)

if __name__ == "__main__":
    main()
