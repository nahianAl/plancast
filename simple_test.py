#!/usr/bin/env python3
print("🚀 Starting simple test...")

try:
    import sys
    print(f"✅ Python version: {sys.version}")
    
    import torch
    print(f"✅ PyTorch: {torch.__version__}")
    
    import cv2
    print(f"✅ OpenCV: {cv2.__version__}")
    
    from PIL import Image
    print(f"✅ PIL imported successfully")
    
    print("🎉 All basic imports successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")
    
print("Test completed.")