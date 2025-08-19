"""
CubiCasa5K Service for PlanCast.

Production-ready integration with CubiCasa5K model for floor plan analysis.
Handles dependency issues, provides fallback systems, and ensures 24/7 reliability.

TODO: Replace placeholder model with real CubiCasa5K architecture before production
"""

import os
import time
import gdown
import torch
import torch.nn as nn
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from io import BytesIO
from PIL import Image
import logging

from models.data_structures import CubiCasaOutput, ProcessingJob
from utils.logger import CubiCasaLogger, get_logger
from services.floortrans.models import get_model
from services.floortrans.post_prosessing import split_prediction, get_polygons

logger = get_logger("cubicasa_service")
cubicasa_logger = CubiCasaLogger()


class CubiCasaError(Exception):
    """Custom exception for CubiCasa5K processing errors."""
    pass


class DependencyError(Exception):
    """Exception for dependency-related issues."""
    pass


# Global model instance to avoid reinitializing for every job
_global_cubicasa_service = None

def get_cubicasa_service() -> 'CubiCasaService':
    """
    Get the global CubiCasa service instance.
    This ensures the model is only loaded once and reused across jobs.
    """
    global _global_cubicasa_service
    if _global_cubicasa_service is None:
        logger.info("Initializing global CubiCasa service...")
        _global_cubicasa_service = CubiCasaService()
        logger.info("Global CubiCasa service initialized successfully")
    return _global_cubicasa_service

class CubiCasaService:
    """
    Production CubiCasa5K service with robust error handling and fallback systems.
    
    Features:
    - Automatic model downloading and caching
    - Dependency compatibility checking
    - Graceful error handling and recovery
    - Performance monitoring
    - Fallback processing options
    """
    
    # Model configuration (URL can be overridden via env var CUBICASA_MODEL_URL)
    MODEL_URL = "https://drive.google.com/uc?export=download&id=1uOjLlp7n0mrEcSAmAhcdazWF4ST9rzBB"
    MODEL_FILENAME = "model_best_val_loss_var.pkl"
    
    def __init__(self, models_dir: str = None):
        """
        Initialize CubiCasa5K service.
        
        Args:
            models_dir: Directory to store model files (defaults to persistent storage on Railway)
        """
        # Use Railway's /tmp directory for model storage (persists between requests)
        if models_dir is None:
            # Try Railway's /tmp directory first (persists during container lifetime)
            tmp_dir = "/tmp"
            if os.path.exists(tmp_dir) and os.access(tmp_dir, os.W_OK):
                models_dir = os.path.join(tmp_dir, "models")
                logger.info(f"Using Railway /tmp storage: {models_dir}")
            else:
                # Fallback to local storage
                models_dir = "assets/models"
                logger.info(f"Using local storage: {models_dir}")
        
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_path = self.models_dir / self.MODEL_FILENAME
        self.model_url = os.getenv("CUBICASA_MODEL_URL", self.MODEL_URL)
        self.model = None
        self.model_loaded = False
        self.device = "cpu"  # Force CPU for compatibility
        
        # Initialize service
        self._check_dependencies()
        self._ensure_model_available()
        self._load_model()
    
    def _check_dependencies(self) -> None:
        """
        Check all dependencies and log versions for debugging.
        Critical for identifying compatibility issues.
        """
        dependencies = {}
        
        try:
            import torch
            dependencies["torch"] = torch.__version__
            
            import torchvision
            dependencies["torchvision"] = torchvision.__version__
            
            import cv2
            dependencies["opencv"] = cv2.__version__
            
            import numpy
            dependencies["numpy"] = numpy.__version__
            
            import PIL
            dependencies["pillow"] = PIL.__version__
            
            # Log all versions for debugging
            cubicasa_logger.log_dependency_check(dependencies)
            
            # Check PyTorch compatibility
            if not torch.cuda.is_available():
                logger.info("CUDA not available, using CPU mode")
                self.device = "cpu"
            
            # Verify minimum versions
            torch_version = tuple(map(int, torch.__version__.split('.')[:2]))
            if torch_version < (1, 7):
                raise DependencyError(f"PyTorch version {torch.__version__} too old. Minimum: 1.7")
                
        except ImportError as e:
            raise DependencyError(f"Required dependency missing: {str(e)}")
        except Exception as e:
            logger.warning(f"Dependency check warning: {str(e)}")
    
    def _ensure_model_available(self) -> None:
        """
        Download CubiCasa5K model if not present.
        """
        # Helper to detect Git LFS pointer
        def _is_lfs_pointer(path: Path) -> bool:
            try:
                with open(path, 'rb') as f:
                    head = f.read(64)
                return head.startswith(b'version https://git-lfs.github.com/spec/v1')
            except Exception:
                return False

        # 1) If a valid model file already exists (and isn't an LFS pointer), use it
        if self.model_path.exists() and not _is_lfs_pointer(self.model_path):
            logger.info(f"CubiCasa5K model found: {self.model_path}")
            return

        # 2) Try to copy a bundled model from the repo if present and valid
        bundled_model = Path('assets/models') / self.MODEL_FILENAME
        if bundled_model.exists() and not _is_lfs_pointer(bundled_model):
            try:
                logger.info(f"Copying bundled model from {bundled_model} -> {self.model_path}")
                self.model_path.write_bytes(bundled_model.read_bytes())
                logger.info("Bundled model copied successfully")
                return
            except Exception as e:
                logger.warning(f"Failed to copy bundled model: {e}")

        # 3) If we got here, download it
        if self.model_path.exists() and _is_lfs_pointer(self.model_path):
            logger.warning("Detected Git LFS pointer for model file; re-downloading actual model...")
            try:
                self.model_path.unlink()
            except Exception:
                pass
            
        logger.info("Downloading CubiCasa5K model...")
        start_time = time.time()
        
        try:
            # Ensure parent dir exists
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            # Some environments block Google Drive; allow fallback later
            gdown.download(self.model_url, str(self.model_path), quiet=False)
            download_time = time.time() - start_time

            if not self.model_path.exists():
                logger.error("Model download reported success but file not created")
                return  # Defer to placeholder fallback in _load_model

            file_size = self.model_path.stat().st_size
            logger.info(f"Model downloaded successfully: {file_size} bytes in {download_time:.1f}s")

        except Exception as e:
            logger.error(f"Failed to download CubiCasa5K model: {str(e)}")
            # Do not raise here; _load_model will fall back to placeholder model
    
    def _load_model(self) -> None:
        """
        Load CubiCasa5K model with comprehensive error handling and PyTorch 2.x compatibility.
        TODO: Update this method to use real CubiCasa5K architecture before production.
        """
        if self.model_loaded:
            return
            
        logger.info("Loading CubiCasa5K model...")
        start_time = time.time()
        
        # Log PyTorch version for debugging
        logger.info(f"PyTorch version: {torch.__version__}")
        logger.info(f"Device: {self.device}")
        
        try:
            # Validate model file integrity; if missing, raise an error as we can't fall back anymore
            if not self.model_path.exists():
                raise CubiCasaError(f"Model file not found at {self.model_path}. Cannot proceed.")

            file_size = self.model_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            logger.info(f"Model file size: {file_size_mb:.2f} MB")
            
            # Check file size is reasonable
            if file_size_mb < 50:
                logger.warning(f"Model file seems small: {file_size_mb:.2f} MB")
            elif file_size_mb > 1000:
                logger.warning(f"Model file seems large: {file_size_mb:.2f} MB")
            
            # Load model checkpoint with PyTorch 2.x compatibility
            logger.info("Attempting to load model checkpoint...")
            
            # Try loading with PyTorch version-specific parameters
            if int(torch.__version__.split('.')[0]) >= 2:
                checkpoint = torch.load(
                    self.model_path, 
                    map_location=torch.device(self.device),
                    weights_only=False
                )
            else:
                checkpoint = torch.load(
                    self.model_path, 
                    map_location=torch.device(self.device)
                )
            
            logger.info("✅ Model checkpoint loaded successfully.")
            logger.info(f"Checkpoint keys: {list(checkpoint.keys())}")
            
            # Initialize the real CubiCasa5K model architecture
            logger.info("Initializing real CubiCasa5K model architecture...")
            self.model = get_model('hg_furukawa_original', 51)
            n_classes = 44
            self.model.conv4_ = torch.nn.Conv2d(256, n_classes, bias=True, kernel_size=1)
            self.model.upsample = torch.nn.ConvTranspose2d(n_classes, n_classes, kernel_size=4, stride=4)
            logger.info("✅ Real model architecture initialized.")

            # Load the state dict from the checkpoint
            if 'model_state' in checkpoint:
                logger.info("Loading 'model_state' from checkpoint into model...")
                self.model.load_state_dict(checkpoint['model_state'])
                logger.info("✅ Model state loaded successfully.")
            else:
                raise CubiCasaError("Checkpoint does not contain 'model_state' key.")

            # Set to evaluation mode
            self.model.eval()
            logger.info("✅ Model set to eval mode")

            load_time = time.time() - start_time
            self.model_loaded = True
            
            cubicasa_logger.log_model_loading(True, load_time)
            logger.info(f"✅ CubiCasa5K model loaded successfully in {load_time:.2f}s")
            
        except Exception as e:
            load_time = time.time() - start_time
            error_msg = f"Failed to load CubiCasa5K model: {str(e)}"
            
            cubicasa_logger.log_model_loading(False, load_time, error_msg)
            logger.error(f"❌ Model loading failed: {error_msg}")
            raise CubiCasaError(f"Fatal error during model loading: {error_msg}")
    
    def _load_model_fallback(self) -> None:
        """
        Fallback model loading method for compatibility issues.
        """
        logger.info("Using fallback model loading method...")
        
        try:
            # Try loading with different parameters
            if int(torch.__version__.split('.')[0]) >= 2:
                checkpoint = torch.load(
                    self.model_path, 
                    map_location='cpu',
                    weights_only=False,
                    pickle_module=torch.serialization._get_safe_globals()
                )
            else:
                checkpoint = torch.load(
                    self.model_path, 
                    map_location='cpu',
                    pickle_module=torch.serialization._get_safe_globals()
                )
            
            # Use placeholder model as fallback
            self.model = PlaceholderModel()
            self.model.eval()
            self.model_loaded = True
            
            logger.info("✅ Fallback model loading successful")
            
        except Exception as e:
            raise CubiCasaError(f"Fallback loading failed: {str(e)}")
    
    def _preprocess_image(self, image_bytes: bytes) -> Tuple[torch.Tensor, Tuple[int, int]]:
        """
        Preprocess image for CubiCasa5K model.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Tuple of (processed_tensor, original_dimensions)
        """
        try:
            # Load image
            image = Image.open(BytesIO(image_bytes))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            original_size = image.size  # (width, height)
            
            # Convert to numpy array
            image_np = np.array(image)
            
            # Resize to model input size (typically 512x512 for CubiCasa5K)
            target_size = (512, 512)
            image_resized = cv2.resize(image_np, target_size)
            
            # Normalize to [0, 1]
            image_normalized = image_resized.astype(np.float32) / 255.0
            
            # Convert to tensor format: (batch, channels, height, width)
            image_tensor = torch.from_numpy(image_normalized)
            image_tensor = image_tensor.permute(2, 0, 1)  # HWC to CHW
            image_tensor = image_tensor.unsqueeze(0)  # Add batch dimension
            
            logger.debug(f"Image preprocessed: {original_size} -> {target_size}")
            return image_tensor, original_size
            
        except Exception as e:
            raise CubiCasaError(f"Image preprocessing failed: {str(e)}")
    
    def _run_inference(self, image_tensor: torch.Tensor) -> torch.Tensor:
        """
        Run CubiCasa5K inference on preprocessed image.
        
        Args:
            image_tensor: Preprocessed image tensor
            
        Returns:
            Raw model output tensor
        """
        try:
            with torch.no_grad():
                # Run model inference and return the raw tensor
                outputs = self.model(image_tensor)
                return outputs
                
        except Exception as e:
            raise CubiCasaError(f"Model inference failed: {str(e)}")
    
    def _postprocess_outputs(self, 
                           outputs: torch.Tensor, 
                           original_size: Tuple[int, int]) -> CubiCasaOutput:
        """
        Post-process CubiCasa5K outputs to extract structured data using the real floortrans logic.
        
        Args:
            outputs: Raw model output tensor
            original_size: Original image dimensions
            
        Returns:
            Structured CubiCasaOutput
        """
        try:
            height, width = original_size[1], original_size[0]
            img_size = (height, width)
            split = [21, 12, 11] # Based on the notebook analysis
            
            # 1. Split the raw prediction tensor
            heatmaps, rooms, icons = split_prediction(outputs, img_size, split)

            # 2. Call the main polygon extraction function
            # Note: We can fine-tune the threshold and opening types later
            polygons, types, room_polygons, room_types = get_polygons((heatmaps, rooms, icons), 0.2, [1, 2])

            # 3. Convert shapely polygons to simple coordinate lists for our data structures
            wall_coordinates = []
            room_bounding_boxes = {}
            
            # Calculate total image area for size comparison
            total_image_area = original_size[0] * original_size[1]
            max_room_area_ratio = 0.5  # Room should not cover more than 50% of the image
            
            # Process room polygons
            room_polygons_dict = {}
            for i, room_poly in enumerate(room_polygons):
                room_class_id = room_types[i]['class']
                # You might want a mapping from class ID to a name like "living_room"
                room_name = f"room_{room_class_id}_{i}"
                
                # Get bounding box from the shapely polygon
                min_x, min_y, max_x, max_y = room_poly.bounds
                
                # Check for NaN values and handle them
                if not (np.isnan(min_x) or np.isnan(min_y) or np.isnan(max_x) or np.isnan(max_y)):
                    # Calculate room area
                    room_width = max_x - min_x
                    room_height = max_y - min_y
                    room_area = room_width * room_height
                    room_area_ratio = room_area / total_image_area
                    
                    # Filter out rooms that are too large (likely covering the entire building)
                    if room_area_ratio > max_room_area_ratio:
                        logger.warning(f"Skipping room {room_name} - too large: {room_area_ratio:.2%} of image (area: {room_area})")
                        continue
                    
                    # Filter out rooms that are too small (likely noise)
                    min_room_area = 100  # Minimum 100 pixels
                    if room_area < min_room_area:
                        logger.warning(f"Skipping room {room_name} - too small: {room_area} pixels")
                        continue
                    
                    room_bounding_boxes[room_name] = {
                        "min_x": int(min_x),
                        "max_x": int(max_x),
                        "min_y": int(min_y),
                        "max_y": int(max_y)
                    }
                    
                    # Extract room polygon coordinates
                    try:
                        # Get polygon coordinates from shapely polygon
                        if hasattr(room_poly, 'exterior'):
                            coords = list(room_poly.exterior.coords)
                        else:
                            # Fallback to bounding box if polygon is not available
                            coords = [
                                (min_x, min_y), (max_x, min_y), 
                                (max_x, max_y), (min_x, max_y), (min_x, min_y)
                            ]
                        
                        # Convert to integer coordinates
                        room_polygons_dict[room_name] = [(int(x), int(y)) for x, y in coords]
                        
                        logger.info(f"Added room {room_name}: {room_width:.0f}×{room_height:.0f} pixels ({room_area_ratio:.1%} of image) with {len(room_polygons_dict[room_name])} polygon points")
                    except Exception as e:
                        logger.warning(f"Failed to extract polygon for room {room_name}: {str(e)}")
                        # Fallback to bounding box
                        room_polygons_dict[room_name] = [
                            (int(min_x), int(min_y)), (int(max_x), int(min_y)), 
                            (int(max_x), int(max_y)), (int(min_x), int(max_y)), (int(min_x), int(min_y))
                        ]
                else:
                    logger.warning(f"Skipping room {room_name} due to NaN bounds")

            # Process wall and icon polygons
            door_coordinates = []
            window_coordinates = []
            
            for i, poly in enumerate(polygons):
                if types[i]['type'] == 'wall':
                    wall_coordinates.extend([tuple(map(int, coord)) for coord in poly])
                elif types[i]['type'] == 'icon':
                    # Extract door and window coordinates
                    icon_class = types[i]['class']
                    
                    # Map icon classes to door/window types based on CubiCasa5K classes
                    if icon_class in [1, 2]:  # Door classes
                        door_coordinates.extend([tuple(map(int, coord)) for coord in poly])
                    elif icon_class in [3, 4]:  # Window classes
                        window_coordinates.extend([tuple(map(int, coord)) for coord in poly])
            
            # For now, confidence scores are static. This can be improved later.
            confidence_scores = {room: 0.95 for room in room_bounding_boxes.keys()}

            return CubiCasaOutput(
                wall_coordinates=wall_coordinates,
                room_bounding_boxes=room_bounding_boxes,
                door_coordinates=door_coordinates,
                window_coordinates=window_coordinates,
                room_polygons=room_polygons_dict,
                image_dimensions=original_size,
                confidence_scores=confidence_scores,
                processing_time=0.0  # Will be set by caller
            )
            
        except Exception as e:
            # Add more context to the error
            logger.error(f"Post-processing failed with error: {e}", exc_info=True)
            raise CubiCasaError(f"Output post-processing failed: {str(e)}")
    
    def process_image(self, image_bytes: bytes, job_id: str) -> CubiCasaOutput:
        """
        Process floor plan image with CubiCasa5K model.
        
        Args:
            image_bytes: Raw image bytes
            job_id: Job ID for logging
            
        Returns:
            CubiCasaOutput with detected rooms and walls
            
        Raises:
            CubiCasaError: If processing fails
        """
        try:
            logger.info(f"🚀 Starting CubiCasa5K processing for job {job_id}")
            start_time = time.time()
            
            # Preprocess image
            logger.info(f"📸 Preprocessing image for job {job_id}")
            image_tensor, original_size = self._preprocess_image(image_bytes)
            logger.info(f"✅ Image preprocessed: {original_size} -> {image_tensor.shape}")
            
            # Run inference
            logger.info(f"🤖 Running CubiCasa5K inference for job {job_id}")
            outputs = self._run_inference(image_tensor)
            logger.info(f"✅ Model inference completed: {outputs.shape}")
            
            # Post-process outputs
            logger.info(f"🔧 Post-processing outputs for job {job_id}")
            result = self._postprocess_outputs(outputs, original_size)
            
            processing_time = time.time() - start_time
            logger.info(f"🎉 CubiCasa5K processing completed for job {job_id} in {processing_time:.2f}s")
            logger.info(f"   Wall coordinates: {len(result.wall_coordinates)}")
            logger.info(f"   Room bounding boxes: {len(result.room_bounding_boxes)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ CubiCasa5K processing failed for job {job_id}: {str(e)}")
            raise CubiCasaError(f"Failed to process image: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check on CubiCasa5K service.
        
        Returns:
            Health status information
        """
        status = {
            "service": "cubicasa",
            "model_loaded": self.model_loaded,
            "device": self.device,
            "model_path_exists": self.model_path.exists(),
            "using_placeholder": False,
            "timestamp": time.time(),
            "pytorch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available()
        }
        
        # Check model file integrity
        if self.model_path.exists():
            file_size = self.model_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            status["model_file_size_mb"] = round(file_size_mb, 2)
            status["model_file_valid"] = 50 <= file_size_mb <= 1000
        else:
            status["model_file_size_mb"] = 0
            status["model_file_valid"] = False
        
        if self.model_loaded:
            try:
                # Test with small dummy image
                dummy_image = Image.new('RGB', (256, 256), color='white')
                dummy_bytes = BytesIO()
                dummy_image.save(dummy_bytes, format='PNG')
                dummy_bytes = dummy_bytes.getvalue()
                
                start_time = time.time()
                test_tensor, _ = self._preprocess_image(dummy_bytes)
                test_outputs = self._run_inference(test_tensor)
                test_time = time.time() - start_time
                
                status.update({
                    "status": "healthy",
                    "test_inference_time": round(test_time, 3),
                    "test_passed": True,
                    "model_has_forward": hasattr(self.model, 'forward'),
                    "model_has_eval": hasattr(self.model, 'eval')
                })
                
            except Exception as e:
                status.update({
                    "status": "degraded",
                    "test_passed": False,
                    "error": str(e),
                    "model_has_forward": hasattr(self.model, 'forward') if self.model else False,
                    "model_has_eval": hasattr(self.model, 'eval') if self.model else False
                })
        else:
            status.update({
                "status": "unhealthy",
                "test_passed": False,
                "error": "Model not loaded",
                "model_has_forward": False,
                "model_has_eval": False
            })
        
        return status