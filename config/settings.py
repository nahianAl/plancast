"""
Configuration settings for PlanCast.

Production settings for file paths, export options, and system configuration.
"""

import os
from pathlib import Path
from typing import List

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Output directories
OUTPUT_DIR = PROJECT_ROOT / "output"
GENERATED_MODELS_DIR = OUTPUT_DIR / "generated_models"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Ensure output directories exist
GENERATED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Export settings
DEFAULT_EXPORT_FORMATS = ["glb", "obj", "stl"]
WEB_OPTIMIZED_GLB = True
DEFAULT_WALL_THICKNESS_FEET = 0.5
DEFAULT_WALL_HEIGHT_FEET = 9.0
DEFAULT_FLOOR_THICKNESS_FEET = 0.25

# File size limits (in bytes)
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
MAX_EXPORT_SIZE = 100 * 1024 * 1024  # 100MB

# Coordinate system settings
USE_Y_UP_FOR_WEB = True  # Convert to Y-up for web compatibility
DEFAULT_UNITS = "feet"

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "json"

# Processing settings
DEFAULT_ROOM_HEIGHT_FEET = 9.0
DEFAULT_SCALE_FACTOR = 6.25  # pixels per foot
