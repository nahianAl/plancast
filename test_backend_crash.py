#!/usr/bin/env python3
"""
Test script to isolate backend crash issues.
"""

import sys
import os
import traceback

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        print("  - Testing test_pipeline_simple...")
        from test_pipeline_simple import SimpleTestPipeline
        print("    ✅ SimpleTestPipeline imported successfully")
        
        print("  - Testing CubiCasaService...")
        from services.cubicasa_service import CubiCasaService
        print("    ✅ CubiCasaService imported successfully")
        
        print("  - Testing SimpleRoomGenerator...")
        from services.test_room_generator import SimpleRoomGenerator
        print("    ✅ SimpleRoomGenerator imported successfully")
        
        print("  - Testing SimpleWallGenerator...")
        from services.test_wall_generator import SimpleWallGenerator
        print("    ✅ SimpleWallGenerator imported successfully")
        
        print("  - Testing MeshExporter...")
        from services.mesh_exporter import MeshExporter
        print("    ✅ MeshExporter imported successfully")
        
        print("  - Testing data structures...")
        from models.data_structures import ProcessingJob, ProcessingStatus
        print("    ✅ Data structures imported successfully")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Import failed: {str(e)}")
        print(f"    Traceback: {traceback.format_exc()}")
        return False

def test_pipeline_initialization():
    """Test if the test pipeline can be initialized."""
    print("\n🔍 Testing pipeline initialization...")
    
    try:
        from test_pipeline_simple import SimpleTestPipeline
        
        print("  - Creating SimpleTestPipeline instance...")
        pipeline = SimpleTestPipeline()
        print("    ✅ SimpleTestPipeline initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Initialization failed: {str(e)}")
        print(f"    Traceback: {traceback.format_exc()}")
        return False

def test_cubicasa_service():
    """Test if CubiCasa service can be initialized."""
    print("\n🔍 Testing CubiCasa service...")
    
    try:
        from services.cubicasa_service import CubiCasaService
        
        print("  - Creating CubiCasaService instance...")
        service = CubiCasaService()
        print("    ✅ CubiCasaService initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"    ❌ CubiCasaService failed: {str(e)}")
        print(f"    Traceback: {traceback.format_exc()}")
        return False

def test_with_sample_image():
    """Test the pipeline with a sample image."""
    print("\n🔍 Testing with sample image...")
    
    try:
        # Check if test image exists
        test_image_path = "test_floorplan.jpg"
        if not os.path.exists(test_image_path):
            print(f"    ❌ Test image not found: {test_image_path}")
            return False
        
        print(f"  - Found test image: {test_image_path}")
        
        # Read the image
        with open(test_image_path, 'rb') as f:
            file_content = f.read()
        
        print(f"  - Image size: {len(file_content)} bytes")
        
        # Test pipeline initialization
        from test_pipeline_simple import SimpleTestPipeline
        pipeline = SimpleTestPipeline()
        
        print("  - Running test pipeline...")
        result = pipeline.process_test_image(
            file_content=file_content,
            filename="test_floorplan.jpg",
            export_formats=["glb", "obj"]
        )
        
        print(f"    ✅ Test pipeline completed successfully")
        print(f"    - Status: {result.status}")
        print(f"    - Exported files: {result.exported_files}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Test pipeline failed: {str(e)}")
        print(f"    Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run all tests."""
    print("🚀 PlanCast Backend Crash Test")
    print("=" * 50)
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Import test failed - this is likely the root cause")
        return False
    
    # Test 2: Pipeline initialization
    if not test_pipeline_initialization():
        print("\n❌ Pipeline initialization failed")
        return False
    
    # Test 3: CubiCasa service
    if not test_cubicasa_service():
        print("\n❌ CubiCasa service failed")
        return False
    
    # Test 4: Full pipeline test
    if not test_with_sample_image():
        print("\n❌ Full pipeline test failed")
        return False
    
    print("\n✅ All tests passed! Backend should work correctly.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
