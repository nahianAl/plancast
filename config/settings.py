"""
Configuration settings for PlanCast application.
"""

# File upload limits
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB in bytes
MAX_EXPORT_SIZE = 100 * 1024 * 1024  # 100MB in bytes

# Default export formats
DEFAULT_EXPORT_FORMATS = ["glb", "obj", "stl"]

# Default units
DEFAULT_UNITS = "feet"

# API settings
API_VERSION = "1.0.0"
API_TITLE = "PlanCast API"

# Processing settings
DEFAULT_WALL_HEIGHT_FEET = 9.0
DEFAULT_WALL_THICKNESS_FEET = 0.5
DEFAULT_FLOOR_THICKNESS_FEET = 0.25
