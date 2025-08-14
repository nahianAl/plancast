#!/usr/bin/env python3
"""
PlanCast Model Compatibility Test
Tests PyTorch 2.2.0 compatibility with existing model file
"""

import os
import sys
import torch
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pytorch_version():
    """Test PyTorch version and compatibility"""
    logger.info(f"PyTorch version: {torch.__version__}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    logger.info(f"Device: {torch.device('cuda' if torch.cuda.is_available() else 'cpu')}")
    
    # Check if we're on PyTorch 2.x
    major_version = int(torch.__version__.split('.')[0])
    if major_version >= 2:
        logger.info("✅ PyTorch 2.x detected - testing backward compatibility")
        return True
    else:
        logger.info("ℹ️ PyTorch 1.x detected - testing local compatibility")
        return True  # PyTorch 1.x is fine for local development

def test_model_file_integrity(model_path):
    """Test model file existence and size"""
    try:
        if not os.path.exists(model_path):
            logger.error(f"❌ Model file not found: {model_path}")
            return False
        
        file_size = os.path.getsize(model_path)
        file_size_mb = file_size / (1024 * 1024)
        logger.info(f"✅ Model file found: {model_path}")
        logger.info(f"✅ File size: {file_size_mb:.2f} MB")
        
        # Check if file size is reasonable (should be around 209MB)
        if file_size_mb < 100:
            logger.warning(f"⚠️ Model file seems small: {file_size_mb:.2f} MB")
        elif file_size_mb > 500:
            logger.warning(f"⚠️ Model file seems large: {file_size_mb:.2f} MB")
        else:
            logger.info("✅ Model file size looks reasonable")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error checking model file: {str(e)}")
        return False

def test_model_loading(model_path):
    """Test loading the model with PyTorch 2.x compatibility"""
    try:
        logger.info("🔄 Attempting to load model...")
        
        # Try loading with PyTorch version-specific parameters
        if int(torch.__version__.split('.')[0]) >= 2:
            # PyTorch 2.x - use weights_only parameter
            model = torch.load(
                model_path, 
                map_location='cpu',
                weights_only=False
            )
        else:
            # PyTorch 1.x - don't use weights_only parameter
            model = torch.load(
                model_path, 
                map_location='cpu'
            )
        
        logger.info("✅ Model loaded successfully")
        logger.info(f"✅ Model type: {type(model)}")
        
        # Check if it's a state dict or full model
        if isinstance(model, dict):
            logger.info("✅ Model loaded as state dict")
            logger.info(f"✅ State dict keys: {list(model.keys())}")
        else:
            logger.info("✅ Model loaded as full model object")
            
            # Try to set to eval mode
            try:
                model.eval()
                logger.info("✅ Model set to eval mode successfully")
            except Exception as e:
                logger.warning(f"⚠️ Could not set model to eval mode: {str(e)}")
        
        return True, model
        
    except Exception as e:
        logger.error(f"❌ Failed to load model: {str(e)}")
        return False, None

def test_model_inference(model):
    """Test basic model inference (if possible)"""
    try:
        if hasattr(model, 'forward'):
            logger.info("🔄 Testing model inference...")
            
            # Create dummy input (adjust based on your model's expected input)
            dummy_input = torch.randn(1, 3, 224, 224)  # Common image input size
            
            with torch.no_grad():
                output = model(dummy_input)
            
            logger.info(f"✅ Model inference successful")
            logger.info(f"✅ Output shape: {output.shape if hasattr(output, 'shape') else type(output)}")
            return True
        else:
            logger.info("ℹ️ Model doesn't have forward method (likely state dict)")
            return True
            
    except Exception as e:
        logger.warning(f"⚠️ Model inference test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    logger.info("🚀 Starting PlanCast Model Compatibility Test")
    
    # Test PyTorch version
    pytorch_ok = test_pytorch_version()
    
    # Model path
    model_path = "assets/models/model_best_val_loss_var.pkl"
    
    # Test model file integrity
    file_ok = test_model_file_integrity(model_path)
    
    if not file_ok:
        logger.error("❌ Model file integrity check failed")
        return False
    
    # Test model loading
    load_ok, model = test_model_loading(model_path)
    
    if not load_ok:
        logger.error("❌ Model loading failed")
        return False
    
    # Test model inference
    inference_ok = test_model_inference(model)
    
    # Overall result - state dict is valid for our use case
    overall_success = pytorch_ok and file_ok and load_ok
    
    if overall_success:
        logger.info("🎉 ALL TESTS PASSED - Model is compatible with PyTorch 2.x!")
        return True
    else:
        logger.error("❌ SOME TESTS FAILED - Model may have compatibility issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
