"""
Room Mesh Generator Service for PlanCast.

Task 3: Generate 3D room floor meshes from scaled coordinates.
Converts room bounding boxes into triangulated 3D floor meshes.
"""

import time
import math
from typing import List, Tuple, Dict, Optional, Any
import logging

from models.data_structures import (
    ScaledCoordinates, 
    Room3D, 
    Vertex3D, 
    Face,
    ProcessingJob
)
from utils.logger import get_logger, log_job_start, log_job_complete, log_job_error

logger = get_logger("room_generator")


class RoomGenerationError(Exception):
    """Custom exception for room mesh generation errors."""
    pass


class RoomMeshGenerator:
    """
    Production room mesh generator service.
    
    Converts scaled room coordinates into 3D floor meshes with proper
    triangulation and vertex/face structures.
    """
    
    def __init__(self):
        """Initialize room mesh generator."""
        self.default_floor_thickness_feet = 0.25
        self.default_room_height_feet = 9.0
        
    def generate_room_meshes(self, 
                           scaled_coords: ScaledCoordinates,
                           floor_thickness_feet: float = 0.25,
                           room_height_feet: float = 9.0) -> List[Room3D]:
        """
        Generate 3D room meshes from scaled coordinates.
        
        Args:
            scaled_coords: Scaled coordinates with room bounding boxes in feet
            floor_thickness_feet: Thickness of floor mesh (default: 0.25 feet)
            room_height_feet: Room height for future ceiling generation (default: 9.0 feet)
            
        Returns:
            List of Room3D objects with 3D mesh data
            
        Raises:
            RoomGenerationError: If generation fails
        """
        start_time = time.time()
        
        logger.info(f"Generating room meshes for {len(scaled_coords.rooms_feet)} rooms")
        logger.info(f"Floor thickness: {floor_thickness_feet} feet, Room height: {room_height_feet} feet")
        
        try:
            # Validate input
            self._validate_scaled_coordinates(scaled_coords)
            
            # Generate meshes for each room
            room_meshes = []
            for room_name, room_data in scaled_coords.rooms_feet.items():
                try:
                    room_mesh = self._generate_single_room_mesh(
                        room_name=room_name,
                        room_data=room_data,
                        floor_thickness_feet=floor_thickness_feet,
                        room_height_feet=room_height_feet
                    )
                    room_meshes.append(room_mesh)
                    
                    logger.info(f"✅ Generated mesh for {room_name}: "
                              f"{len(room_mesh.vertices)} vertices, {len(room_mesh.faces)} faces")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to generate mesh for room '{room_name}': {str(e)}")
                    raise RoomGenerationError(f"Room '{room_name}' generation failed: {str(e)}")
            
            processing_time = time.time() - start_time
            
            logger.info(f"✅ Room mesh generation completed: "
                       f"{len(room_meshes)} rooms in {processing_time:.3f}s")
            
            return room_meshes
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Room mesh generation failed after {processing_time:.3f}s: {str(e)}")
            raise RoomGenerationError(f"Room mesh generation failed: {str(e)}")
    
    def _validate_scaled_coordinates(self, scaled_coords: ScaledCoordinates) -> None:
        """
        Validate scaled coordinates input.
        
        Args:
            scaled_coords: Scaled coordinates to validate
            
        Raises:
            RoomGenerationError: If validation fails
        """
        if not scaled_coords.rooms_feet:
            raise RoomGenerationError("No rooms found in scaled coordinates")
        
        for room_name, room_data in scaled_coords.rooms_feet.items():
            required_fields = ['width_feet', 'length_feet', 'area_sqft', 'x_offset_feet', 'y_offset_feet']
            
            for field in required_fields:
                if field not in room_data:
                    raise RoomGenerationError(f"Room '{room_name}' missing required field: {field}")
                
                value = room_data[field]
                if not isinstance(value, (int, float)):
                    raise RoomGenerationError(f"Room '{room_name}' field '{field}' must be numeric")
                
                # Dimensions must be strictly positive; offsets can be zero or positive
                if field in ['width_feet', 'length_feet', 'area_sqft']:
                    if value <= 0:
                        raise RoomGenerationError(f"Room '{room_name}' field '{field}' must be positive")
                else:  # x_offset_feet, y_offset_feet
                    if value < 0:
                        raise RoomGenerationError(f"Room '{room_name}' field '{field}' must be non-negative")
        
        logger.info(f"✅ Validated {len(scaled_coords.rooms_feet)} rooms")
    
    def _generate_single_room_mesh(self,
                                 room_name: str,
                                 room_data: Dict[str, float],
                                 floor_thickness_feet: float,
                                 room_height_feet: float) -> Room3D:
        """
        Generate 3D mesh for a single room.
        
        Args:
            room_name: Name of the room
            room_data: Room dimensions and position data
            floor_thickness_feet: Floor thickness
            room_height_feet: Room height
            
        Returns:
            Room3D object with mesh data
        """
        # Extract room dimensions
        width_feet = room_data['width_feet']
        length_feet = room_data['length_feet']
        x_offset_feet = room_data['x_offset_feet']
        y_offset_feet = room_data['y_offset_feet']
        
        # Calculate room corners
        min_x = x_offset_feet
        max_x = x_offset_feet + width_feet
        min_y = y_offset_feet
        max_y = y_offset_feet + length_feet
        
        # Generate vertices and faces for rectangular floor
        vertices, faces = self._triangulate_rectangle(
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
            elevation_feet=0.0  # Floor at ground level
        )
        
        # Create Room3D object
        room_mesh = Room3D(
            name=room_name,
            vertices=vertices,
            faces=faces,
            elevation_feet=0.0,
            height_feet=room_height_feet
        )
        
        logger.debug(f"Generated room '{room_name}': "
                    f"size {width_feet:.1f}' × {length_feet:.1f}', "
                    f"position ({x_offset_feet:.1f}, {y_offset_feet:.1f})")
        
        return room_mesh
    
    def _triangulate_rectangle(self,
                             min_x: float,
                             min_y: float,
                             max_x: float,
                             max_y: float,
                             elevation_feet: float = 0.0) -> Tuple[List[Vertex3D], List[Face]]:
        """
        Triangulate a rectangular floor into 3D mesh.
        
        Args:
            min_x, min_y: Bottom-left corner
            max_x, max_y: Top-right corner
            elevation_feet: Z-coordinate for the floor
            
        Returns:
            Tuple of (vertices, faces) for the triangulated rectangle
        """
        # Create 4 vertices for the rectangle (counter-clockwise order)
        vertices = [
            Vertex3D(x=min_x, y=min_y, z=elevation_feet),  # Bottom-left
            Vertex3D(x=max_x, y=min_y, z=elevation_feet),  # Bottom-right
            Vertex3D(x=max_x, y=max_y, z=elevation_feet),  # Top-right
            Vertex3D(x=min_x, y=max_y, z=elevation_feet),  # Top-left
        ]
        
        # Create 2 triangular faces to form the rectangle
        # Face 1: Triangle 0-1-2 (bottom-left, bottom-right, top-right)
        face1 = Face(indices=[0, 1, 2])
        
        # Face 2: Triangle 0-2-3 (bottom-left, top-right, top-left)
        face2 = Face(indices=[0, 2, 3])
        
        faces = [face1, face2]
        
        return vertices, faces
    
    def validate_room_mesh(self, room_mesh: Room3D) -> Dict[str, Any]:
        """
        Validate generated room mesh.
        
        Args:
            room_mesh: Room3D object to validate
            
        Returns:
            Validation result dictionary
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "vertex_count": len(room_mesh.vertices),
            "face_count": len(room_mesh.faces)
        }
        
        # Check vertex count (should be 4 for rectangular floor)
        if len(room_mesh.vertices) != 4:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Expected 4 vertices, got {len(room_mesh.vertices)}")
        
        # Check face count (should be 2 triangles)
        if len(room_mesh.faces) != 2:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Expected 2 faces, got {len(room_mesh.faces)}")
        
        # Validate face indices
        for i, face in enumerate(room_mesh.faces):
            if len(face.indices) != 3:
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"Face {i} must have 3 indices, got {len(face.indices)}")
            
            # Check index bounds
            for index in face.indices:
                if index < 0 or index >= len(room_mesh.vertices):
                    validation_result["is_valid"] = False
                    validation_result["errors"].append(f"Face {i} has invalid vertex index: {index}")
        
        # Check room dimensions
        if room_mesh.height_feet <= 0:
            validation_result["is_valid"] = False
            validation_result["errors"].append("Room height must be positive")
        
        if room_mesh.elevation_feet < 0:
            validation_result["warnings"].append("Room elevation is below ground level")
        
        return validation_result


# Global service instance
_room_generator = None


def get_room_generator() -> RoomMeshGenerator:
    """
    Get or create global room generator service instance.
    
    Returns:
        RoomMeshGenerator instance
    """
    global _room_generator
    if _room_generator is None:
        _room_generator = RoomMeshGenerator()
        logger.info("✅ Room mesh generator service initialized")
    return _room_generator
