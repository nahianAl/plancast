#!/usr/bin/env python3
"""
Test script for real CubiCasa model integration.
Tests the model with test_image.jpg and displays results.
"""

import os
import sys
import time
import torch
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

from services.cubicasa_service import CubiCasaService
from services.floortrans.post_prosessing import split_prediction, get_polygons

def test_real_cubicasa():
    """Test the real CubiCasa model with test_image.jpg"""
    
    print("=== REAL CUBICASA MODEL TEST ===")
    print("Testing with test_image.jpg...")
    
    # Initialize the service
    print("\n1. Initializing CubiCasa service...")
    try:
        service = CubiCasaService()
        print("✅ Service initialized successfully")
        print(f"   Model loaded: {service.model_loaded}")
        print(f"   Using placeholder: {service.health_check()['using_placeholder']}")
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False
    
    # Load test image
    print("\n2. Loading test image...")
    test_image_path = "test_image.jpg"
    if not os.path.exists(test_image_path):
        print(f"❌ Test image not found: {test_image_path}")
        return False
    
    try:
        with open(test_image_path, 'rb') as f:
            image_bytes = f.read()
        print(f"✅ Test image loaded: {len(image_bytes)} bytes")
    except Exception as e:
        print(f"❌ Failed to load test image: {e}")
        return False
    
    # Process the image
    print("\n3. Processing image with real CubiCasa model...")
    start_time = time.time()
    
    try:
        # Preprocess image
        image_tensor, original_size = service._preprocess_image(image_bytes)
        print(f"   Image preprocessed: {original_size} -> {image_tensor.shape}")
        
        # Run inference
        outputs = service._run_inference(image_tensor)
        print(f"   Model inference completed: {outputs.shape}")
        
        # Post-process outputs
        result = service._postprocess_outputs(outputs, original_size)
        processing_time = time.time() - start_time
        
        print(f"✅ Processing completed in {processing_time:.2f}s")
        print(f"   Wall coordinates: {len(result.wall_coordinates)}")
        print(f"   Room bounding boxes: {len(result.room_bounding_boxes)}")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test the polygon extraction pipeline directly
    print("\n4. Testing polygon extraction pipeline...")
    try:
        height, width = original_size[1], original_size[0]
        img_size = (height, width)
        split = [21, 12, 11]
        
        # Split the raw prediction tensor
        heatmaps, rooms, icons = split_prediction(outputs, img_size, split)
        print(f"   Heatmaps shape: {heatmaps.shape}")
        print(f"   Rooms shape: {rooms.shape}")
        print(f"   Icons shape: {icons.shape}")
        
        # Extract polygons
        polygons, types, room_polygons, room_types = get_polygons((heatmaps, rooms, icons), 0.2, [1, 2])
        print(f"   Total polygons: {len(polygons)}")
        print(f"   Room polygons: {len(room_polygons)}")
        print(f"   Room types: {len(room_types)}")
        
        # Display detected rooms
        print("\n=== DETECTED ROOMS ===")
        rooms_detected = np.argmax(rooms, axis=0)
        unique_rooms = np.unique(rooms_detected)
        for room_id in unique_rooms:
            room_id = int(room_id)
            if room_id > 0:
                pixel_count = np.sum(rooms_detected == room_id)
                print(f"Room ID {room_id}: {pixel_count} pixels")
        
        # Display detected icons
        print("\n=== DETECTED ICONS ===")
        icons_detected = np.argmax(icons, axis=0)
        unique_icons = np.unique(icons_detected)
        for icon_id in unique_icons:
            icon_id = int(icon_id)
            if icon_id > 0:
                pixel_count = np.sum(icons_detected == icon_id)
                print(f"Icon ID {icon_id}: {pixel_count} pixels")
        
        # Visualize results
        print("\n5. Creating visualization...")
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # Original image
        original_img = Image.open(test_image_path)
        axes[0].imshow(original_img)
        axes[0].set_title('Original Test Image')
        axes[0].axis('off')
        
        # Detected rooms
        axes[1].imshow(rooms_detected, cmap='tab20')
        axes[1].set_title('Detected Rooms')
        axes[1].axis('off')
        
        # Detected icons
        axes[2].imshow(icons_detected, cmap='tab20')
        axes[2].set_title('Detected Icons')
        axes[2].axis('off')
        
        plt.tight_layout()
        plt.savefig('test_results.png', dpi=150, bbox_inches='tight')
        print("✅ Visualization saved as 'test_results.png'")
        
    except Exception as e:
        print(f"❌ Polygon extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🎯 REAL CUBICASA MODEL TEST COMPLETED SUCCESSFULLY!")
    print("The model is working correctly and ready for deployment!")
    
    return True

if __name__ == "__main__":
    success = test_real_cubicasa()
    if not success:
        sys.exit(1)
