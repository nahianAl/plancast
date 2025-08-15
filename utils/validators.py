"""
Validation Utilities for PlanCast.

Comprehensive input validation and security checks for production deployment.
Handles file uploads, API inputs, coordinate validation, and security measures.
"""

import os
import re
import math
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import logging
from urllib.parse import urlparse, unquote

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    magic = None

from models.data_structures import (
    FileFormat, ProcessingStatus, ExportFormat,
    ScaleReference, ScaledCoordinates, Building3D,
    CubiCasaOutput, Room3D, Wall3D, Vertex3D, Face
)
from config.settings import (
    MAX_UPLOAD_SIZE, MAX_EXPORT_SIZE,
    DEFAULT_EXPORT_FORMATS, DEFAULT_UNITS
)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class SecurityError(Exception):
    """Custom exception for security violations."""
    pass


class PlanCastValidator:
    """
    Production-ready validation system for PlanCast.
    
    Provides comprehensive validation for:
    - File uploads and security
    - API inputs and sanitization
    - Coordinate and geometry validation
    - Export format validation
    - Building model validation
    """
    
    # File validation constants
    SUPPORTED_MIME_TYPES = {
        'image/jpeg': FileFormat.JPEG,
        'image/jpg': FileFormat.JPG,
        'image/png': FileFormat.PNG,
        'application/pdf': FileFormat.PDF
    }
    
    # Security constants
    MAX_FILENAME_LENGTH = 255
    ALLOWED_FILENAME_CHARS = re.compile(r'^[a-zA-Z0-9._-]+$')
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js',
        '.jar', '.class', '.php', '.asp', '.aspx', '.jsp', '.py', '.pl',
        '.sh', '.bash', '.zsh', '.csh', '.ksh', '.tcsh'
    }
    
    # Coordinate validation constants
    MAX_COORDINATE_VALUE = 10000.0  # feet
    MIN_COORDINATE_VALUE = -10000.0  # feet
    MAX_BUILDING_DIMENSION = 1000.0  # feet
    MIN_BUILDING_DIMENSION = 1.0  # feet
    
    # Scale validation constants
    MAX_SCALE_FACTOR = 1000.0  # pixels per foot
    MIN_SCALE_FACTOR = 0.1  # pixels per foot
    MAX_ROOM_DIMENSION = 100.0  # feet
    MIN_ROOM_DIMENSION = 1.0  # feet
    
    # Export validation constants
    SUPPORTED_EXPORT_FORMATS = [f.value for f in ExportFormat]
    MAX_EXPORT_FORMATS = 10
    
    def __init__(self):
        """Initialize validator with security settings."""
        self.max_upload_size = MAX_UPLOAD_SIZE
        self.max_export_size = MAX_EXPORT_SIZE
        
    def validate_upload_file(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Comprehensive file upload validation with security checks.
        
        Args:
            file_bytes: Raw file content
            filename: Original filename
            
        Returns:
            Dict with validation results and metadata
            
        Raises:
            ValidationError: If file validation fails
            SecurityError: If security checks fail
        """
        logger.info(f"Validating upload file: {filename} ({len(file_bytes)} bytes)")
        
        validation_result = {
            "is_valid": False,
            "filename": filename,
            "file_size": len(file_bytes),
            "file_format": None,
            "mime_type": None,
            "warnings": [],
            "errors": []
        }
        
        try:
            # 1. Security checks
            self._check_file_security(file_bytes, filename)
            
            # 2. File size validation
            self._validate_file_size(file_bytes, validation_result)
            
            # 3. Filename sanitization and validation
            sanitized_filename = self.sanitize_filename(filename)
            validation_result["sanitized_filename"] = sanitized_filename
            
            # 4. MIME type detection and validation
            mime_type = self._detect_mime_type(file_bytes)
            validation_result["mime_type"] = mime_type
            
            if mime_type not in self.SUPPORTED_MIME_TYPES:
                validation_result["errors"].append(
                    f"Unsupported MIME type: {mime_type}. "
                    f"Supported: {', '.join(self.SUPPORTED_MIME_TYPES.keys())}"
                )
            else:
                validation_result["file_format"] = self.SUPPORTED_MIME_TYPES[mime_type]
            
            # 5. Content validation
            self._validate_file_content(file_bytes, mime_type, validation_result)
            
            # 6. Determine overall validity
            validation_result["is_valid"] = len(validation_result["errors"]) == 0
            
            if validation_result["is_valid"]:
                logger.info(f"✅ File validation passed: {filename}")
            else:
                logger.warning(f"⚠️ File validation failed: {filename}")
                logger.warning(f"   Errors: {validation_result['errors']}")
            
            return validation_result
            
        except (ValidationError, SecurityError) as e:
            validation_result["errors"].append(str(e))
            validation_result["is_valid"] = False
            logger.error(f"❌ File validation exception: {str(e)}")
            return validation_result
        except Exception as e:
            validation_result["errors"].append(f"Unexpected validation error: {str(e)}")
            validation_result["is_valid"] = False
            logger.error(f"❌ File validation unexpected error: {str(e)}")
            return validation_result
    
    def validate_scale_reference(self, scale_ref: ScaleReference) -> Dict[str, Any]:
        """
        Validate scale reference for reasonable dimensions and values.
        
        Args:
            scale_ref: ScaleReference object to validate
            
        Returns:
            Dict with validation results
            
        Raises:
            ValidationError: If scale reference is invalid
        """
        logger.info(f"Validating scale reference: {scale_ref.room_type}")
        
        validation_result = {
            "is_valid": False,
            "scale_reference": scale_ref,
            "warnings": [],
            "errors": []
        }
        
        try:
            # 1. Room type validation
            if not scale_ref.room_type or not scale_ref.room_type.strip():
                validation_result["errors"].append("Room type cannot be empty")
            else:
                room_type = scale_ref.room_type.strip().lower()
                if len(room_type) > 50:
                    validation_result["errors"].append("Room type too long (max 50 characters)")
                if not re.match(r'^[a-zA-Z0-9_\s-]+$', room_type):
                    validation_result["errors"].append("Room type contains invalid characters")
            
            # 2. Dimension type validation
            if scale_ref.dimension_type not in ["width", "length"]:
                validation_result["errors"].append(
                    f"Invalid dimension type: {scale_ref.dimension_type}. "
                    f"Must be 'width' or 'length'"
                )
            
            # 3. Real-world measurement validation
            if not self._is_finite_positive(scale_ref.real_world_feet):
                validation_result["errors"].append(
                    f"Invalid real-world measurement: {scale_ref.real_world_feet}. "
                    f"Must be a positive finite number"
                )
            elif scale_ref.real_world_feet < self.MIN_ROOM_DIMENSION:
                validation_result["errors"].append(
                    f"Room dimension too small: {scale_ref.real_world_feet} feet. "
                    f"Minimum: {self.MIN_ROOM_DIMENSION} feet"
                )
            elif scale_ref.real_world_feet > self.MAX_ROOM_DIMENSION:
                validation_result["errors"].append(
                    f"Room dimension too large: {scale_ref.real_world_feet} feet. "
                    f"Maximum: {self.MAX_ROOM_DIMENSION} feet"
                )
            
            # 4. Pixel measurement validation
            if not self._is_finite_positive(scale_ref.pixel_measurement):
                validation_result["errors"].append(
                    f"Invalid pixel measurement: {scale_ref.pixel_measurement}. "
                    f"Must be a positive finite number"
                )
            
            # 5. Scale factor validation
            if not self._is_finite_positive(scale_ref.scale_factor):
                validation_result["errors"].append(
                    f"Invalid scale factor: {scale_ref.scale_factor}. "
                    f"Must be a positive finite number"
                )
            elif scale_ref.scale_factor < self.MIN_SCALE_FACTOR:
                validation_result["errors"].append(
                    f"Scale factor too small: {scale_ref.scale_factor}. "
                    f"Minimum: {self.MIN_SCALE_FACTOR} pixels per foot"
                )
            elif scale_ref.scale_factor > self.MAX_SCALE_FACTOR:
                validation_result["errors"].append(
                    f"Scale factor too large: {scale_ref.scale_factor}. "
                    f"Maximum: {self.MAX_SCALE_FACTOR} pixels per foot"
                )
            
            # 6. Consistency check
            calculated_scale = scale_ref.pixel_measurement / scale_ref.real_world_feet
            scale_tolerance = 0.01  # 1% tolerance
            if abs(calculated_scale - scale_ref.scale_factor) > scale_tolerance:
                validation_result["warnings"].append(
                    f"Scale factor inconsistency: calculated {calculated_scale:.3f}, "
                    f"provided {scale_ref.scale_factor:.3f}"
                )
            
            validation_result["is_valid"] = len(validation_result["errors"]) == 0
            
            if validation_result["is_valid"]:
                logger.info(f"✅ Scale reference validation passed")
            else:
                logger.warning(f"⚠️ Scale reference validation failed")
                logger.warning(f"   Errors: {validation_result['errors']}")
            
            return validation_result
            
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["is_valid"] = False
            logger.error(f"❌ Scale reference validation error: {str(e)}")
            return validation_result
    
    def validate_export_formats(self, formats: List[str]) -> Dict[str, Any]:
        """
        Validate export format list for supported formats and limits.
        
        Args:
            formats: List of format strings to validate
            
        Returns:
            Dict with validation results and normalized formats
            
        Raises:
            ValidationError: If formats are invalid
        """
        logger.info(f"Validating export formats: {formats}")
        
        validation_result = {
            "is_valid": False,
            "requested_formats": formats,
            "valid_formats": [],
            "invalid_formats": [],
            "warnings": [],
            "errors": []
        }
        
        try:
            # 1. Input validation
            if not formats:
                validation_result["warnings"].append("No export formats specified, using defaults")
                validation_result["valid_formats"] = DEFAULT_EXPORT_FORMATS.copy()
                validation_result["is_valid"] = True
                return validation_result
            
            if not isinstance(formats, list):
                validation_result["errors"].append("Formats must be a list")
                return validation_result
            
            if len(formats) > self.MAX_EXPORT_FORMATS:
                validation_result["errors"].append(
                    f"Too many export formats: {len(formats)}. "
                    f"Maximum allowed: {self.MAX_EXPORT_FORMATS}"
                )
            
            # 2. Format validation
            for format_name in formats:
                if not isinstance(format_name, str):
                    validation_result["errors"].append(
                        f"Invalid format type: {type(format_name)}. Must be string"
                    )
                    continue
                
                format_lower = format_name.lower().strip()
                
                if not format_lower:
                    validation_result["errors"].append("Empty format name")
                    continue
                
                if format_lower in self.SUPPORTED_EXPORT_FORMATS:
                    validation_result["valid_formats"].append(format_lower)
                else:
                    validation_result["invalid_formats"].append(format_name)
                    validation_result["warnings"].append(
                        f"Unsupported format: {format_name}. "
                        f"Supported: {', '.join(self.SUPPORTED_EXPORT_FORMATS)}"
                    )
            
            # 3. Duplicate check
            unique_formats = list(set(validation_result["valid_formats"]))
            if len(unique_formats) != len(validation_result["valid_formats"]):
                validation_result["warnings"].append("Duplicate formats removed")
                validation_result["valid_formats"] = unique_formats
            
            # 4. Default format fallback
            if not validation_result["valid_formats"]:
                validation_result["warnings"].append(
                    f"No valid formats specified, using defaults: {DEFAULT_EXPORT_FORMATS}"
                )
                validation_result["valid_formats"] = DEFAULT_EXPORT_FORMATS.copy()
            
            validation_result["is_valid"] = len(validation_result["errors"]) == 0
            
            if validation_result["is_valid"]:
                logger.info(f"✅ Export format validation passed: {validation_result['valid_formats']}")
            else:
                logger.warning(f"⚠️ Export format validation failed")
                logger.warning(f"   Errors: {validation_result['errors']}")
            
            return validation_result
            
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["is_valid"] = False
            logger.error(f"❌ Export format validation error: {str(e)}")
            return validation_result
    
    def validate_coordinates(self, coords: ScaledCoordinates) -> Dict[str, Any]:
        """
        Validate scaled coordinates for reasonable bounds and data integrity.
        
        Args:
            coords: ScaledCoordinates object to validate
            
        Returns:
            Dict with validation results
            
        Raises:
            ValidationError: If coordinates are invalid
        """
        logger.info("Validating scaled coordinates")
        
        validation_result = {
            "is_valid": False,
            "coordinates": coords,
            "warnings": [],
            "errors": []
        }
        
        try:
            # 1. Scale reference validation
            scale_validation = self.validate_scale_reference(coords.scale_reference)
            if not scale_validation["is_valid"]:
                validation_result["errors"].extend(scale_validation["errors"])
            
            # 2. Building dimensions validation
            building = coords.total_building_size
            if not self._is_finite_positive(building.width_feet):
                validation_result["errors"].append(
                    f"Invalid building width: {building.width_feet}"
                )
            elif building.width_feet < self.MIN_BUILDING_DIMENSION:
                validation_result["errors"].append(
                    f"Building width too small: {building.width_feet} feet. "
                    f"Minimum: {self.MIN_BUILDING_DIMENSION} feet"
                )
            elif building.width_feet > self.MAX_BUILDING_DIMENSION:
                validation_result["errors"].append(
                    f"Building width too large: {building.width_feet} feet. "
                    f"Maximum: {self.MAX_BUILDING_DIMENSION} feet"
                )
            
            if not self._is_finite_positive(building.length_feet):
                validation_result["errors"].append(
                    f"Invalid building length: {building.length_feet}"
                )
            elif building.length_feet < self.MIN_BUILDING_DIMENSION:
                validation_result["errors"].append(
                    f"Building length too small: {building.length_feet} feet. "
                    f"Minimum: {self.MIN_BUILDING_DIMENSION} feet"
                )
            elif building.length_feet > self.MAX_BUILDING_DIMENSION:
                validation_result["errors"].append(
                    f"Building length too large: {building.length_feet} feet. "
                    f"Maximum: {self.MAX_BUILDING_DIMENSION} feet"
                )
            
            # 3. Area validation
            calculated_area = building.width_feet * building.length_feet
            if abs(calculated_area - building.area_sqft) > 0.1:  # 0.1 sqft tolerance
                validation_result["warnings"].append(
                    f"Area mismatch: calculated {calculated_area:.1f} sqft, "
                    f"provided {building.area_sqft:.1f} sqft"
                )
            
            # 4. Wall coordinates validation
            if not coords.walls_feet:
                validation_result["warnings"].append("No wall coordinates provided")
            else:
                for i, (x, y) in enumerate(coords.walls_feet):
                    if not self._is_finite_number(x) or not self._is_finite_number(y):
                        validation_result["errors"].append(
                            f"Invalid wall coordinate {i}: ({x}, {y})"
                        )
                    elif x < self.MIN_COORDINATE_VALUE or x > self.MAX_COORDINATE_VALUE:
                        validation_result["errors"].append(
                            f"Wall X coordinate out of bounds: {x}"
                        )
                    elif y < self.MIN_COORDINATE_VALUE or y > self.MAX_COORDINATE_VALUE:
                        validation_result["errors"].append(
                            f"Wall Y coordinate out of bounds: {y}"
                        )
            
            # 5. Room coordinates validation
            if not coords.rooms_feet:
                validation_result["warnings"].append("No room coordinates provided")
            else:
                for room_name, room_data in coords.rooms_feet.items():
                    for key, value in room_data.items():
                        if not self._is_finite_number(value):
                            validation_result["errors"].append(
                                f"Invalid room {room_name} {key}: {value}"
                            )
                        elif value < self.MIN_COORDINATE_VALUE or value > self.MAX_COORDINATE_VALUE:
                            validation_result["errors"].append(
                                f"Room {room_name} {key} out of bounds: {value}"
                            )
            
            validation_result["is_valid"] = len(validation_result["errors"]) == 0
            
            if validation_result["is_valid"]:
                logger.info(f"✅ Coordinate validation passed")
            else:
                logger.warning(f"⚠️ Coordinate validation failed")
                logger.warning(f"   Errors: {validation_result['errors']}")
            
            return validation_result
            
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["is_valid"] = False
            logger.error(f"❌ Coordinate validation error: {str(e)}")
            return validation_result
    
    def validate_building_3d(self, building: Building3D) -> Dict[str, Any]:
        """
        Validate Building3D object for valid mesh data and geometry.
        
        Args:
            building: Building3D object to validate
            
        Returns:
            Dict with validation results
            
        Raises:
            ValidationError: If building data is invalid
        """
        logger.info(f"Validating Building3D: {len(building.rooms)} rooms, {len(building.walls)} walls")
        
        validation_result = {
            "is_valid": False,
            "building": building,
            "warnings": [],
            "errors": []
        }
        
        try:
            # 1. Basic structure validation
            if not building.rooms and not building.walls:
                validation_result["errors"].append("Building has no rooms or walls")
            
            if building.total_vertices <= 0:
                validation_result["errors"].append(
                    f"Invalid total vertices: {building.total_vertices}"
                )
            
            if building.total_faces <= 0:
                validation_result["errors"].append(
                    f"Invalid total faces: {building.total_faces}"
                )
            
            # 2. Room validation
            for i, room in enumerate(building.rooms):
                room_validation = self._validate_room_3d(room, f"room_{i}")
                validation_result["errors"].extend(room_validation["errors"])
                validation_result["warnings"].extend(room_validation["warnings"])
            
            # 3. Wall validation
            for i, wall in enumerate(building.walls):
                wall_validation = self._validate_wall_3d(wall, f"wall_{i}")
                validation_result["errors"].extend(wall_validation["errors"])
                validation_result["warnings"].extend(wall_validation["warnings"])
            
            # 4. Bounding box validation
            if not building.bounding_box:
                validation_result["errors"].append("Missing bounding box")
            else:
                required_keys = ["min_x", "max_x", "min_y", "max_y", "min_z", "max_z"]
                for key in required_keys:
                    if key not in building.bounding_box:
                        validation_result["errors"].append(f"Missing bounding box key: {key}")
                    else:
                        value = building.bounding_box[key]
                        if not self._is_finite_number(value):
                            validation_result["errors"].append(
                                f"Invalid bounding box {key}: {value}"
                            )
                
                # Check bounding box consistency
                if len(validation_result["errors"]) == 0:
                    bbox = building.bounding_box
                    if bbox["max_x"] <= bbox["min_x"]:
                        validation_result["errors"].append("Invalid X bounds in bounding box")
                    if bbox["max_y"] <= bbox["min_y"]:
                        validation_result["errors"].append("Invalid Y bounds in bounding box")
                    if bbox["max_z"] <= bbox["min_z"]:
                        validation_result["errors"].append("Invalid Z bounds in bounding box")
            
            # 5. Export readiness check
            if not building.export_ready:
                validation_result["warnings"].append("Building marked as not export-ready")
            
            validation_result["is_valid"] = len(validation_result["errors"]) == 0
            
            if validation_result["is_valid"]:
                logger.info(f"✅ Building3D validation passed")
            else:
                logger.warning(f"⚠️ Building3D validation failed")
                logger.warning(f"   Errors: {validation_result['errors']}")
            
            return validation_result
            
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["is_valid"] = False
            logger.error(f"❌ Building3D validation error: {str(e)}")
            return validation_result
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for security and compatibility.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for file system operations
        """
        if not filename:
            return "unnamed_file"
        
        # Remove path traversal attempts
        filename = os.path.basename(filename)
        
        # Remove null bytes and control characters
        filename = ''.join(char for char in filename if ord(char) >= 32)
        
        # Replace dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Limit length
        if len(filename) > self.MAX_FILENAME_LENGTH:
            name, ext = os.path.splitext(filename)
            max_name_length = self.MAX_FILENAME_LENGTH - len(ext)
            filename = name[:max_name_length] + ext
        
        # Ensure it's not empty after sanitization
        if not filename.strip():
            return "unnamed_file"
        
        return filename.strip()
    
    def check_file_security(self, file_bytes: bytes) -> bool:
        """
        Perform security checks on file content.
        
        Args:
            file_bytes: Raw file content
            
        Returns:
            True if file passes security checks
            
        Raises:
            SecurityError: If security checks fail
        """
        # 1. Check for null bytes (potential security risk)
        # Allow null bytes in image files (JPEG, PNG) as they're part of the format
        if b'\x00' in file_bytes:
            # Check if it's an image file first
            if not (file_bytes.startswith(b'\xff\xd8\xff') or  # JPEG
                   file_bytes.startswith(b'\x89PNG\r\n\x1a\n')):  # PNG
                raise SecurityError("File contains null bytes (security risk)")
        
        # 2. Check for executable signatures
        executable_signatures = [
            b'MZ',  # Windows PE
            b'\x7fELF',  # Linux ELF
            b'\xfe\xed\xfa',  # Mach-O
            b'#!/',  # Shell script
        ]
        
        for sig in executable_signatures:
            if file_bytes.startswith(sig):
                raise SecurityError(f"File appears to be executable (signature: {sig})")
        
        # 3. Check for suspicious patterns
        suspicious_patterns = [
            b'<script',  # HTML/JavaScript
            b'<?php',  # PHP
            b'<%@',  # ASP
            b'<jsp:',  # JSP
        ]
        
        for pattern in suspicious_patterns:
            if pattern in file_bytes.lower():
                raise SecurityError(f"File contains suspicious pattern: {pattern}")
        
        # 4. Check file size for potential DoS
        if len(file_bytes) > self.max_upload_size:
            raise SecurityError(f"File too large for security: {len(file_bytes)} bytes")
        
        return True
    
    def _check_file_security(self, file_bytes: bytes, filename: str) -> None:
        """Internal security check wrapper."""
        # Check filename for dangerous extensions
        file_ext = Path(filename).suffix.lower()
        if file_ext in self.DANGEROUS_EXTENSIONS:
            raise SecurityError(f"Dangerous file extension: {file_ext}")
        
        # Check filename for path traversal
        if '..' in filename or filename.startswith('/'):
            raise SecurityError("Path traversal attempt detected")
        
        # Perform content security checks
        self.check_file_security(file_bytes)
    
    def _validate_file_size(self, file_bytes: bytes, validation_result: Dict[str, Any]) -> None:
        """Validate file size constraints."""
        file_size = len(file_bytes)
        
        if file_size > self.max_upload_size:
            validation_result["errors"].append(
                f"File too large: {file_size} bytes. "
                f"Maximum allowed: {self.max_upload_size} bytes"
            )
        
        if file_size < 1024:  # 1KB minimum
            validation_result["errors"].append(
                f"File too small: {file_size} bytes. "
                f"Minimum required: 1024 bytes"
            )
    
    def _detect_mime_type(self, file_bytes: bytes) -> str:
        """Detect MIME type using multiple methods with better JPEG detection."""
        
        # Check for JPEG magic numbers first (most reliable)
        if file_bytes.startswith(b'\xff\xd8\xff'):
            return "image/jpeg"
        
        # Check for PNG
        if file_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            return "image/png"
        
        # Check for PDF
        if file_bytes.startswith(b'%PDF'):
            return "application/pdf"
        
        # Try magic library if available
        if MAGIC_AVAILABLE:
            try:
                mime_type = magic.from_buffer(file_bytes, mime=True)
                if mime_type in self.SUPPORTED_MIME_TYPES:
                    return mime_type
            except Exception:
                pass
        
        # Fallback to imghdr
        try:
            import imghdr
            image_type = imghdr.what(None, h=file_bytes)
            if image_type == 'jpeg':
                return "image/jpeg"
            elif image_type == 'png':
                return "image/png"
        except Exception:
            pass
        
        # Default fallback
        return "application/octet-stream"
    
    def _validate_file_content(self, file_bytes: bytes, mime_type: str, validation_result: Dict[str, Any]) -> None:
        """Validate file content based on MIME type."""
        try:
            if mime_type.startswith('image/'):
                from PIL import Image
                from io import BytesIO
                
                # Try to open as image
                img = Image.open(BytesIO(file_bytes))
                img.verify()  # Verify image integrity
                
                # Check dimensions
                img = Image.open(BytesIO(file_bytes))  # Reopen after verify
                width, height = img.size
                
                if width > 4096 or height > 4096:
                    validation_result["warnings"].append(
                        f"Large image dimensions: {width}x{height} pixels"
                    )
                
                if width < 512 or height < 512:
                    validation_result["warnings"].append(
                        f"Small image dimensions: {width}x{height} pixels"
                    )
            
            elif mime_type == 'application/pdf':
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(stream=file_bytes, filetype="pdf")
                    if doc.page_count > 1:
                        validation_result["warnings"].append(
                            f"PDF has {doc.page_count} pages, only first page will be processed"
                        )
                    doc.close()
                except Exception as e:
                    validation_result["errors"].append(f"Invalid PDF file: {str(e)}")
        
        except Exception as e:
            validation_result["warnings"].append(f"Content validation warning: {str(e)}")
    
    def _validate_room_3d(self, room: Room3D, room_id: str) -> Dict[str, Any]:
        """Validate individual Room3D object."""
        validation_result = {"errors": [], "warnings": []}
        
        # Validate vertices
        if not room.vertices:
            validation_result["errors"].append(f"{room_id}: No vertices")
        else:
            for i, vertex in enumerate(room.vertices):
                if not self._is_finite_number(vertex.x) or not self._is_finite_number(vertex.y) or not self._is_finite_number(vertex.z):
                    validation_result["errors"].append(f"{room_id} vertex {i}: Invalid coordinates")
        
        # Validate faces
        if not room.faces:
            validation_result["errors"].append(f"{room_id}: No faces")
        else:
            for i, face in enumerate(room.faces):
                if not face.indices or len(face.indices) < 3:
                    validation_result["errors"].append(f"{room_id} face {i}: Invalid face (need 3+ vertices)")
                else:
                    # Check vertex indices are within bounds
                    max_vertex_index = len(room.vertices) - 1
                    for vertex_index in face.indices:
                        if vertex_index < 0 or vertex_index > max_vertex_index:
                            validation_result["errors"].append(f"{room_id} face {i}: Invalid vertex index {vertex_index}")
        
        # Validate dimensions
        if room.height_feet <= 0:
            validation_result["errors"].append(f"{room_id}: Invalid height: {room.height_feet}")
        
        return validation_result
    
    def _validate_wall_3d(self, wall: Wall3D, wall_id: str) -> Dict[str, Any]:
        """Validate individual Wall3D object."""
        validation_result = {"errors": [], "warnings": []}
        
        # Validate vertices
        if not wall.vertices:
            validation_result["errors"].append(f"{wall_id}: No vertices")
        else:
            for i, vertex in enumerate(wall.vertices):
                if not self._is_finite_number(vertex.x) or not self._is_finite_number(vertex.y) or not self._is_finite_number(vertex.z):
                    validation_result["errors"].append(f"{wall_id} vertex {i}: Invalid coordinates")
        
        # Validate faces
        if not wall.faces:
            validation_result["errors"].append(f"{wall_id}: No faces")
        else:
            for i, face in enumerate(wall.faces):
                if not face.indices or len(face.indices) < 3:
                    validation_result["errors"].append(f"{wall_id} face {i}: Invalid face (need 3+ vertices)")
                else:
                    # Check vertex indices are within bounds
                    max_vertex_index = len(wall.vertices) - 1
                    for vertex_index in face.indices:
                        if vertex_index < 0 or vertex_index > max_vertex_index:
                            validation_result["errors"].append(f"{wall_id} face {i}: Invalid vertex index {vertex_index}")
        
        # Validate dimensions
        if wall.height_feet <= 0:
            validation_result["errors"].append(f"{wall_id}: Invalid height: {wall.height_feet}")
        
        if wall.thickness_feet <= 0:
            validation_result["errors"].append(f"{wall_id}: Invalid thickness: {wall.thickness_feet}")
        
        return validation_result
    
    def _is_finite_number(self, value: Union[int, float]) -> bool:
        """Check if value is a finite number."""
        return isinstance(value, (int, float)) and math.isfinite(value)
    
    def _is_finite_positive(self, value: Union[int, float]) -> bool:
        """Check if value is a finite positive number."""
        return self._is_finite_number(value) and value > 0


# Global validator instance
_validator = None


def get_validator() -> PlanCastValidator:
    """
    Get or create global validator instance.
    
    Returns:
        PlanCastValidator instance
    """
    global _validator
    if _validator is None:
        _validator = PlanCastValidator()
        logger.info("✅ PlanCast validator initialized")
    return _validator


# Convenience functions for common validations
def validate_upload_file(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Convenience function for file upload validation."""
    return get_validator().validate_upload_file(file_bytes, filename)


def validate_scale_reference(scale_ref: ScaleReference) -> Dict[str, Any]:
    """Convenience function for scale reference validation."""
    return get_validator().validate_scale_reference(scale_ref)


def validate_export_formats(formats: List[str]) -> Dict[str, Any]:
    """Convenience function for export format validation."""
    return get_validator().validate_export_formats(formats)


def validate_coordinates(coords: ScaledCoordinates) -> Dict[str, Any]:
    """Convenience function for coordinate validation."""
    return get_validator().validate_coordinates(coords)


def validate_building_3d(building: Building3D) -> Dict[str, Any]:
    """Convenience function for building validation."""
    return get_validator().validate_building_3d(building)


def sanitize_filename(filename: str) -> str:
    """Convenience function for filename sanitization."""
    return get_validator().sanitize_filename(filename)


def check_file_security(file_bytes: bytes) -> bool:
    """Convenience function for file security checks."""
    return get_validator().check_file_security(file_bytes)
