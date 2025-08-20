"""
Coordinate Scaling Service for PlanCast.

Task 2: Convert CubiCasa5K pixel coordinates to real-world measurements.
Takes user input like "Kitchen is 12 feet wide" and scales entire floor plan.
"""

import time
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging

from models.data_structures import (
    CubiCasaOutput, 
    ScaleReference, 
    ScaledCoordinates,
    BuildingDimensions,
    ProcessingJob
)
from utils.logger import get_logger, log_job_start, log_job_complete, log_job_error

logger = get_logger("coordinate_scaler")


class ScalingError(Exception):
    """Custom exception for coordinate scaling errors."""
    pass


@dataclass
class RoomDimensions:
    """Calculated room dimensions in feet."""
    width_feet: float
    length_feet: float
    area_sqft: float
    x_offset_feet: float
    y_offset_feet: float


class CoordinateScaler:
    """
    Production coordinate scaling service.
    
    Converts CubiCasa5K pixel coordinates to real-world measurements using
    user-provided reference dimensions.
    """
    
    def __init__(self):
        """Initialize coordinate scaler with performance optimizations."""
        self.scale_reference: Optional[ScaleReference] = None
        self.scale_cache = {}  # Cache for scale factors
        self.room_suggestion_cache = {}  # Cache for room suggestions
        self.validation_cache = {}  # Cache for validation results
        
    def calculate_scale_factor(self, 
                             cubicasa_output: CubiCasaOutput,
                             room_type: str,
                             dimension_type: str,
                             real_world_feet: float) -> ScaleReference:
        """
        Calculate scale factor from user input.
        
        Args:
            cubicasa_output: Raw CubiCasa5K data
            room_type: Room name (e.g., "kitchen")
            dimension_type: "width" or "length"
            real_world_feet: User-provided measurement in feet
            
        Returns:
            ScaleReference with calculated scale factor
            
        Raises:
            ScalingError: If calculation fails
        """
        logger.info(f"Calculating scale factor for {room_type} {dimension_type}: {real_world_feet} feet")
        
        try:
            # Find the specified room
            if room_type not in cubicasa_output.room_bounding_boxes:
                available_rooms = list(cubicasa_output.room_bounding_boxes.keys())
                raise ScalingError(
                    f"Room '{room_type}' not found. Available rooms: {available_rooms}"
                )
            
            room_bbox = cubicasa_output.room_bounding_boxes[room_type]
            
            # Calculate pixel measurement based on dimension type
            if dimension_type.lower() == "width":
                pixel_measurement = room_bbox["max_x"] - room_bbox["min_x"]
            elif dimension_type.lower() == "length":
                pixel_measurement = room_bbox["max_y"] - room_bbox["min_y"]
            else:
                raise ScalingError(f"Dimension type must be 'width' or 'length', got: {dimension_type}")
            
            # Validate measurements
            if pixel_measurement <= 0:
                raise ScalingError(f"Invalid pixel measurement: {pixel_measurement}")
            
            if real_world_feet <= 0:
                raise ScalingError(f"Real world measurement must be positive: {real_world_feet}")
            
            # Calculate scale factor: pixels per foot
            scale_factor = pixel_measurement / real_world_feet
            
            scale_reference = ScaleReference(
                room_type=room_type,
                dimension_type=dimension_type,
                real_world_feet=real_world_feet,
                pixel_measurement=float(pixel_measurement),
                scale_factor=scale_factor
            )
            
            logger.info(f"Scale factor calculated: {scale_factor:.2f} pixels/foot "
                       f"({pixel_measurement} pixels = {real_world_feet} feet)")
            
            self.scale_reference = scale_reference
            return scale_reference
            
        except Exception as e:
            error_msg = f"Scale factor calculation failed: {str(e)}"
            logger.error(error_msg)
            raise ScalingError(error_msg)
    
    def convert_coordinates_to_feet(self, 
                                  cubicasa_output: CubiCasaOutput,
                                  scale_reference: ScaleReference) -> ScaledCoordinates:
        """
        Convert all pixel coordinates to real-world feet.
        
        Args:
            cubicasa_output: Raw CubiCasa5K data
            scale_reference: Scale factor information
            
        Returns:
            ScaledCoordinates with all measurements in feet
            
        Raises:
            ScalingError: If conversion fails
        """
        logger.info("Converting pixel coordinates to feet")
        
        try:
            scale_factor = scale_reference.scale_factor
            
            # Convert wall coordinates to feet
            walls_feet = [
                (x / scale_factor, y / scale_factor)
                for x, y in cubicasa_output.wall_coordinates
            ]
            
            # Convert door coordinates to feet
            doors_feet = [
                (x / scale_factor, y / scale_factor)
                for x, y in cubicasa_output.door_coordinates
            ]
            
            # Convert window coordinates to feet
            windows_feet = [
                (x / scale_factor, y / scale_factor)
                for x, y in cubicasa_output.window_coordinates
            ]
            
            # Convert room polygons to feet
            room_polygons_feet = {}
            for room_name, polygon_coords in cubicasa_output.room_polygons.items():
                room_polygons_feet[room_name] = [
                    (x / scale_factor, y / scale_factor)
                    for x, y in polygon_coords
                ]
            
            logger.info(f"Converted {len(walls_feet)} wall coordinate points to feet")
            
            # Convert room bounding boxes to feet with positioning
            rooms_feet = {}
            for room_name, bbox in cubicasa_output.room_bounding_boxes.items():
                room_dims = self._calculate_room_dimensions(bbox, scale_factor)
                
                rooms_feet[room_name] = {
                    "width_feet": room_dims.width_feet,
                    "length_feet": room_dims.length_feet,
                    "area_sqft": room_dims.area_sqft,
                    "x_offset_feet": room_dims.x_offset_feet,
                    "y_offset_feet": room_dims.y_offset_feet
                }
                
                logger.info(f"Room '{room_name}': {room_dims.width_feet:.1f}' × {room_dims.length_feet:.1f}' "
                           f"({room_dims.area_sqft:.0f} sq ft)")
            
            # Calculate total building dimensions
            total_building_size = self._calculate_building_dimensions(
                cubicasa_output.image_dimensions, 
                scale_factor
            )
            
            scaled_coordinates = ScaledCoordinates(
                walls_feet=walls_feet,
                rooms_feet=rooms_feet,
                door_coordinates=doors_feet,
                window_coordinates=windows_feet,
                room_polygons=room_polygons_feet,
                scale_reference=scale_reference,
                total_building_size=total_building_size
            )
            
            logger.info(f"Coordinate scaling completed: "
                       f"{total_building_size.width_feet:.1f}' × {total_building_size.length_feet:.1f}' building "
                       f"({total_building_size.area_sqft:.0f} sq ft)")
            
            return scaled_coordinates
            
        except Exception as e:
            error_msg = f"Coordinate conversion failed: {str(e)}"
            logger.error(error_msg)
            raise ScalingError(error_msg)
    
    def _calculate_room_dimensions(self, bbox: Dict[str, int], scale_factor: float) -> RoomDimensions:
        """
        Calculate room dimensions in feet from pixel bounding box.
        
        Args:
            bbox: Room bounding box in pixels
            scale_factor: Pixels per foot conversion factor
            
        Returns:
            RoomDimensions with measurements in feet
        """
        # Calculate dimensions in feet
        width_feet = (bbox["max_x"] - bbox["min_x"]) / scale_factor
        length_feet = (bbox["max_y"] - bbox["min_y"]) / scale_factor
        area_sqft = width_feet * length_feet
        
        # Calculate position offsets in feet
        x_offset_feet = bbox["min_x"] / scale_factor
        y_offset_feet = bbox["min_y"] / scale_factor
        
        return RoomDimensions(
            width_feet=width_feet,
            length_feet=length_feet,
            area_sqft=area_sqft,
            x_offset_feet=x_offset_feet,
            y_offset_feet=y_offset_feet
        )
    
    def _calculate_building_dimensions(self, 
                                    image_dimensions: Tuple[int, int], 
                                    scale_factor: float) -> BuildingDimensions:
        """
        Calculate total building dimensions.
        
        Args:
            image_dimensions: Image (width, height) in pixels
            scale_factor: Pixels per foot conversion factor
            
        Returns:
            BuildingDimensions object with all measurements
        """
        width_pixels, height_pixels = image_dimensions
        
        width_feet = width_pixels / scale_factor
        length_feet = height_pixels / scale_factor
        area_sqft = width_feet * length_feet
        
        return BuildingDimensions(
            width_feet=width_feet,
            length_feet=length_feet,
            area_sqft=area_sqft,
            scale_factor=scale_factor,
            original_width_pixels=width_pixels,
            original_height_pixels=height_pixels
        )
    
    def process_scaling_request(self,
                              cubicasa_output: CubiCasaOutput,
                              room_type: str,
                              dimension_type: str,
                              real_world_feet: float,
                              job_id: str) -> ScaledCoordinates:
        """
        Main method to process coordinate scaling request.
        
        Args:
            cubicasa_output: Raw CubiCasa5K data
            room_type: Room for scaling reference
            dimension_type: "width" or "length"
            real_world_feet: Real-world measurement
            job_id: Processing job ID
            
        Returns:
            ScaledCoordinates with all data in feet
            
        Raises:
            ScalingError: If processing fails
        """
        start_time = time.time()
        
        log_job_start(job_id, "coordinate_scaling", {
            "room_type": room_type,
            "dimension_type": dimension_type,
            "real_world_feet": real_world_feet,
            "wall_points": len(cubicasa_output.wall_coordinates),
            "rooms_detected": len(cubicasa_output.room_bounding_boxes)
        })
        
        try:
            # Calculate scale factor
            try:
                scale_reference = self.calculate_scale_factor(
                    cubicasa_output, room_type, dimension_type, real_world_feet
                )
            except Exception as e:
                raise ScalingError(f"Failed to calculate scale factor: {str(e)}")

            # Convert coordinates to feet
            try:
                scaled_coordinates = self.convert_coordinates_to_feet(
                    cubicasa_output, scale_reference
                )
            except Exception as e:
                raise ScalingError(f"Failed to convert coordinates to feet: {str(e)}")

            processing_time = time.time() - start_time
            
            log_job_complete(job_id, "coordinate_scaling", processing_time, {
                "scale_factor": scale_reference.scale_factor,
                "total_building_sqft": scaled_coordinates.total_building_size.area_sqft,
                "rooms_processed": len(scaled_coordinates.rooms_feet)
            })
            
            logger.info(f"Coordinate scaling completed for job {job_id} in {processing_time:.3f}s")
            
            return scaled_coordinates
            
        except ScalingError as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            log_job_error(job_id, "coordinate_scaling", error_msg, {
                "processing_time": processing_time
            })
            
            logger.error(f"Coordinate scaling failed for job {job_id}: {error_msg}")
            raise
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"An unexpected error occurred during scaling: {str(e)}"
            
            log_job_error(job_id, "coordinate_scaling", error_msg, {
                "processing_time": processing_time
            })
            
            logger.error(f"Coordinate scaling failed for job {job_id}: {error_msg}")
            raise ScalingError(error_msg)
    
    def validate_scaling_input(self,
                             cubicasa_output: CubiCasaOutput,
                             room_type: str,
                             dimension_type: str,
                             real_world_feet: float) -> Dict[str, Any]:
        """
        Validate user input for scaling against actual CubiCasa5K data.
        
        Args:
            cubicasa_output: CubiCasa5K output data to validate against
            room_type: Room name to validate
            dimension_type: Dimension type ("width" or "length")
            real_world_feet: Measurement in feet
            
        Returns:
            Dictionary with validation results, errors, warnings, and suggestions
            
        Raises:
            ScalingError: If validation fails critically
        """
        logger.info(f"Validating scaling input: {room_type} {dimension_type} = {real_world_feet} feet")
        
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Validate CubiCasa output structure
        if not cubicasa_output.room_bounding_boxes:
            validation_result["is_valid"] = False
            validation_result["errors"].append("No rooms detected in floor plan")
            return validation_result
        
        if not cubicasa_output.wall_coordinates:
            validation_result["warnings"].append("No wall coordinates detected - wall generation may be limited")
        
        if not cubicasa_output.room_polygons:
            validation_result["warnings"].append("No room polygons detected - using bounding boxes for room shapes")
        
        if not cubicasa_output.door_coordinates and not cubicasa_output.window_coordinates:
            validation_result["warnings"].append("No doors or windows detected - cutouts will not be generated")
        
        # Validate room type format
        if not room_type or not room_type.strip():
            validation_result["is_valid"] = False
            validation_result["errors"].append("Room type cannot be empty")
            return validation_result
        
        room_type = room_type.strip()
        
        # Validate room exists in CubiCasa5K output
        if room_type not in cubicasa_output.room_bounding_boxes:
            available_rooms = list(cubicasa_output.room_bounding_boxes.keys())
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                f"Room '{room_type}' not found in floor plan. "
                f"Available rooms: {', '.join(available_rooms)}"
            )
            validation_result["suggestions"].append(
                f"Try one of the detected rooms: {', '.join(available_rooms[:3])}"
            )
            return validation_result
        
        # Validate dimension type
        valid_dimensions = ["width", "length"]
        if dimension_type.lower() not in valid_dimensions:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Dimension type must be one of: {valid_dimensions}")
            return validation_result
        
        dimension_type = dimension_type.lower()
        
        # Room-specific dimension validation
        room_type_lower = room_type.lower()
        room_dimension_limits = {
            "kitchen": {"min": 8, "max": 20, "typical": 12},
            "living_room": {"min": 12, "max": 30, "typical": 16},
            "bedroom": {"min": 10, "max": 25, "typical": 12},
            "bathroom": {"min": 5, "max": 15, "typical": 8},
            "dining_room": {"min": 10, "max": 25, "typical": 14}
        }
        
        # Get limits for this room type
        limits = room_dimension_limits.get(room_type_lower, {"min": 5, "max": 30, "typical": 12})
        
        # Validate measurement
        if real_world_feet <= 0:
            validation_result["is_valid"] = False
            validation_result["errors"].append("Measurement must be positive")
            return validation_result
        elif real_world_feet < limits["min"]:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                f"{room_type} {dimension_type} too small: {real_world_feet} feet. "
                f"Minimum: {limits['min']} feet"
            )
            validation_result["suggestions"].append(
                f"Typical {room_type} {dimension_type}: {limits['typical']} feet"
            )
            return validation_result
        elif real_world_feet > limits["max"]:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                f"{room_type} {dimension_type} too large: {real_world_feet} feet. "
                f"Maximum: {limits['max']} feet"
            )
            validation_result["suggestions"].append(
                f"Typical {room_type} {dimension_type}: {limits['typical']} feet"
            )
            return validation_result
        
        # Warning for unusual dimensions
        typical = limits["typical"]
        if abs(real_world_feet - typical) > typical * 0.5:  # More than 50% off typical
            validation_result["warnings"].append(
                f"Unusual {room_type} {dimension_type}: {real_world_feet} feet "
                f"(typical: {typical} feet). Please verify this measurement."
            )
        
        # Validate measurement against room size
        room_bbox = cubicasa_output.room_bounding_boxes[room_type]
        if dimension_type == "width":
            pixel_measurement = room_bbox["max_x"] - room_bbox["min_x"]
        else:  # length
            pixel_measurement = room_bbox["max_y"] - room_bbox["min_y"]
        
        # Calculate implied scale factor
        implied_scale_factor = pixel_measurement / real_world_feet
        
        # Validate scale factor is reasonable (between 1-50 pixels per foot)
        if implied_scale_factor < 1:
            validation_result["warnings"].append(
                f"Scale factor seems very small ({implied_scale_factor:.2f} pixels/foot). "
                f"Floor plan may be very low resolution."
            )
        elif implied_scale_factor > 50:
            validation_result["warnings"].append(
                f"Scale factor seems very large ({implied_scale_factor:.2f} pixels/foot). "
                f"Measurement may be too small for this room."
            )
        
        # Reasonable range suggestions
        if 5 <= real_world_feet <= 50:
            validation_result["suggestions"].append("Measurement is in typical room range")
        
        # Room-specific suggestions
        room_confidence = cubicasa_output.confidence_scores.get(room_type, 0.5)
        if room_confidence < 0.7:
            validation_result["warnings"].append(
                f"Room '{room_type}' has low confidence ({room_confidence:.2f}). "
                f"Consider using a different room for scaling."
            )
        
        # Log validation result
        if validation_result["is_valid"]:
            logger.info(f"✅ Scaling input validation passed for {room_type}")
            if validation_result["warnings"]:
                logger.warning(f"⚠️  Warnings: {validation_result['warnings']}")
        else:
            logger.error(f"❌ Scaling input validation failed: {validation_result['errors']}")
        
        return validation_result
    
    def get_smart_room_suggestions(self, 
                                 cubicasa_output: CubiCasaOutput) -> List[Dict[str, any]]:
        """
        Get smart suggestions for which room to use for scaling.
        
        Args:
            cubicasa_output: CubiCasa5K data
            
        Returns:
            List of room suggestions with confidence and reasoning
        """
        # Check cache first
        cache_key = hash(str(cubicasa_output.room_bounding_boxes))
        if cache_key in self.room_suggestion_cache:
            logger.debug("Using cached room suggestions")
            return self.room_suggestion_cache[cache_key]
        
        suggestions = []
        
        # Priority order for room selection with highlighting colors
        room_priority = {
            "kitchen": {"priority": 1, "color": "#FF6B6B", "reason": "Kitchens are easy to measure and commonly known"},
            "living_room": {"priority": 2, "color": "#4ECDC4", "reason": "Living rooms are typically the largest, easy to measure"},
            "bedroom": {"priority": 3, "color": "#45B7D1", "reason": "Bedrooms have standard sizes"},
            "bathroom": {"priority": 4, "color": "#FFEAA7", "reason": "Bathrooms are smaller but well-defined"},
            "dining_room": {"priority": 5, "color": "#96CEB4", "reason": "Dining rooms are clearly defined spaces"}
        }
        
        for room_name, bbox in cubicasa_output.room_bounding_boxes.items():
            room_width = bbox["max_x"] - bbox["min_x"]
            room_height = bbox["max_y"] - bbox["min_y"]
            room_area = room_width * room_height
            
            # Get priority info
            priority_info = room_priority.get(room_name.lower(), {"priority": 6, "color": "#DDA0DD", "reason": "Standard room"})
            
            # Calculate confidence based on size and type
            confidence = cubicasa_output.confidence_scores.get(room_name, 0.5)
            
            # Adjust confidence based on room size (larger rooms often easier to measure)
            size_factor = min(room_area / 10000, 1.0)  # Normalize to reasonable range
            adjusted_confidence = confidence * (0.7 + 0.3 * size_factor)
            
            suggestion = {
                "room_name": room_name,
                "confidence": adjusted_confidence,
                "priority": priority_info["priority"],
                "reason": priority_info["reason"],
                "highlight_color": priority_info["color"],
                "pixel_dimensions": {"width": room_width, "height": room_height},
                "suggested_dimension": "width" if room_width >= room_height else "length",
                "is_recommended": priority_info["priority"] <= 3 and adjusted_confidence > 0.7
            }
            
            suggestions.append(suggestion)
        
        # Sort by priority and confidence
        suggestions.sort(key=lambda x: (x["priority"], -x["confidence"]))
        
        # Cache the result
        self.room_suggestion_cache[cache_key] = suggestions
        
        logger.info(f"Generated {len(suggestions)} room scaling suggestions")
        return suggestions


# Singleton instance for global use
_coordinate_scaler: Optional[CoordinateScaler] = None


def get_coordinate_scaler() -> CoordinateScaler:
    """
    Get the global coordinate scaler instance.
    
    Returns:
        CoordinateScaler instance
    """
    global _coordinate_scaler
    if _coordinate_scaler is None:
        _coordinate_scaler = CoordinateScaler()
    return _coordinate_scaler


# Convenience function for direct use
def scale_floor_plan_coordinates(cubicasa_output: CubiCasaOutput,
                                room_type: str,
                                dimension_type: str,
                                real_world_feet: float,
                                job_id: str) -> ScaledCoordinates:
    """
    Scale floor plan coordinates to real-world measurements.
    
    Args:
        cubicasa_output: Raw CubiCasa5K data
        room_type: Room for scaling reference
        dimension_type: "width" or "length"
        real_world_feet: Real-world measurement
        job_id: Processing job ID
        
    Returns:
        ScaledCoordinates with all data in feet
    """
    scaler = get_coordinate_scaler()
    return scaler.process_scaling_request(
        cubicasa_output, room_type, dimension_type, real_world_feet, job_id
    )