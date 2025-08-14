#!/usr/bin/env python3
"""
Test script for CubiCasa5K service.

This script tests:
1. Dependency compatibility
2. Model downloading and loading
3. Image processing pipeline
4. Error handling and logging

Run this to verify everything works before building the rest of the pipeline.
"""

import sys
import os
import time
from pathlib import Path
from PIL import Image
from io import BytesIO

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_test_image() -> bytes:
    """Create a simple test floor plan image."""
    # Create a simple floor plan-like image
    image = Image.new('RGB', (800, 600), color='white')
    
    # Draw some simple rectangles to simulate rooms
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    
    # Draw walls (black lines)
    draw.rectangle([100, 100, 700, 500], outline='black', width=3)
    draw.line([400, 100, 400, 500], fill='black', width=3)
    draw.line([100, 300, 700, 300], fill='black', width=3)
    
    # Add some text
    draw.text((200, 200), "KITCHEN", fill='black')
    draw.text((500, 200), "LIVING", fill='black')
    draw.text((200, 400), "BEDROOM", fill='black')
    draw.text((500, 400), "BATH", fill='black')
    
    # Convert to bytes
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()

def test_dependencies():
    """Test 1: Check all dependencies are available."""
    print("🔍 Testing Dependencies...")
    
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
        
        import torchvision
        print(f"✅ TorchVision: {torchvision.__version__}")
        
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
        
        import numpy
        print(f"✅ NumPy: {numpy.__version__}")
        
        import PIL
        print(f"✅ Pillow: {PIL.__version__}")
        
        import gdown
        print(f"✅ gdown: Available")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Dependency warning: {e}")
        return True

def test_logging_setup():
    """Test 2: Verify logging system works."""
    print("\n📝 Testing Logging Setup...")
    
    try:
        from utils.logger import setup_logging, get_logger
        
        # Setup development logging
        setup_logging("development", "INFO")
        
        logger = get_logger("test")
        logger.info("Test log message")
        
        print("✅ Logging system working")
        return True
        
    except Exception as e:
        print(f"❌ Logging setup failed: {e}")
        return False

def test_cubicasa_service_init():
    """Test 3: Initialize CubiCasa5K service."""
    print("\n🤖 Testing CubiCasa5K Service Initialization...")
    
    try:
        from services.cubicasa_service import CubiCasaService
        
        print("  - Creating service instance...")
        start_time = time.time()
        
        service = CubiCasaService()
        
        init_time = time.time() - start_time
        print(f"  - Service initialized in {init_time:.2f}s")
        
        # Check if model loaded
        if service.model_loaded:
            print("✅ CubiCasa5K model loaded successfully")
        else:
            print("⚠️  CubiCasa5K model not loaded (might be downloading)")
        
        return service
        
    except Exception as e:
        print(f"❌ CubiCasa5K service initialization failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

def test_health_check(service):
    """Test 4: Service health check."""
    print("\n🏥 Testing Health Check...")
    
    try:
        health = service.health_check()
        
        print(f"  - Service status: {health.get('status', 'unknown')}")
        print(f"  - Model loaded: {health.get('model_loaded', False)}")
        print(f"  - Device: {health.get('device', 'unknown')}")
        print(f"  - Test passed: {health.get('test_passed', False)}")
        
        if health.get('status') == 'healthy':
            print("✅ Service health check passed")
            return True
        else:
            print(f"⚠️  Service health check issues: {health.get('error', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_image_processing(service):
    """Test 5: Process test image."""
    print("\n🖼️  Testing Image Processing...")
    
    try:
        # Create test image
        print("  - Creating test floor plan image...")
        test_image_bytes = create_test_image()
        print(f"  - Test image created: {len(test_image_bytes)} bytes")
        
        # Process image
        print("  - Processing with CubiCasa5K...")
        start_time = time.time()
        
        result = service.process_image(test_image_bytes, "test_job_001")
        
        processing_time = time.time() - start_time
        print(f"  - Processing completed in {processing_time:.2f}s")
        
        # Check results
        print(f"  - Wall coordinates found: {len(result.wall_coordinates)}")
        print(f"  - Rooms detected: {len(result.room_bounding_boxes)}")
        print(f"  - Image dimensions: {result.image_dimensions}")
        print(f"  - Confidence scores: {result.confidence_scores}")
        
        # Display sample data
        if result.wall_coordinates:
            print(f"  - Sample wall coords: {result.wall_coordinates[:5]}...")
            
        if result.room_bounding_boxes:
            for room, bbox in result.room_bounding_boxes.items():
                print(f"  - {room}: {bbox}")
        
        print("✅ Image processing successful")
        return True
        
    except Exception as e:
        print(f"❌ Image processing failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling(service):
    """Test 6: Error handling with invalid input."""
    print("\n🚨 Testing Error Handling...")
    
    try:
        # Test with invalid image data
        invalid_data = b"not an image"
        
        try:
            service.process_image(invalid_data, "test_error_job")
            print("⚠️  Expected error but processing succeeded")
            return False
        except Exception as e:
            print(f"✅ Error handling working: {type(e).__name__}")
            return True
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Main test runner."""
    print("🚀 PlanCast CubiCasa5K Service Test")
    print("=" * 50)
    
    # Track test results
    tests_passed = 0
    total_tests = 6
    
    # Test 1: Dependencies
    if test_dependencies():
        tests_passed += 1
    
    # Test 2: Logging
    if test_logging_setup():
        tests_passed += 1
    
    # Test 3: Service initialization
    service = test_cubicasa_service_init()
    if service is not None:
        tests_passed += 1
        
        # Test 4: Health check
        if test_health_check(service):
            tests_passed += 1
        
        # Test 5: Image processing (only if service is healthy)
        if service.model_loaded:
            if test_image_processing(service):
                tests_passed += 1
            
            # Test 6: Error handling
            if test_error_handling(service):
                tests_passed += 1
        else:
            print("\n⚠️  Skipping image processing tests - model not loaded")
    
    # Final results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! CubiCasa5K service is ready.")
        return True
    elif tests_passed >= 3:
        print("⚠️  Partial success. Service initialized but may have issues.")
        return False
    else:
        print("❌ Critical failures. Service needs debugging.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)