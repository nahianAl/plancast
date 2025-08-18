"""
Simple Room Generator for PlanCast Test Pipeline

This is a TEMPORARY simplified room generator for debugging 3D model generation issues.
It skips coordinate scaling and uses basic bounding box generation.

IMPORTANT: This is for debugging only. After fixing core issues, we must integrate
back with the full enhanced pipeline.
"""

import time
import math
from typing import List, Tuple, Dict, Optional, Any
import logging

from models.data_structures import (
    CubiCasaOutput, 
    Room3D, 
    Vertex3D, 
    Face
)
from utils.logger import get_logger

logger = get_logger("test_room_generator")


class SimpleRoomGenerationError(Exception):
    """Custom exception for simple room generation errors."""
    pass


class SimpleRoomGenerator:
    """
    Simplified room mesh generator for debugging.
    
    Features:
    - 1:1 pixel to foot scaling (no coordinate scaling)
    - Basic bounding box generation (no complex polygons)
    - Simple rectangular floor meshes
    - No enhanced validation
    """
    
    def __init__(self):
        """Initialize simple room generator."""
        self.default_floor_thickness_feet = 0.25
        self.default_room_height_feet = 9.0
        
    def generate_simple_rooms(self, 
                            cubicasa_output: CubiCasaOutput,
                            floor_thickness_feet: float = 0.25,
                            room_height_feet: float = 9.0) -> List[Room3D]:
        """
        Generate simple 3D room meshes from CubiCasa output.
        
        Args:
            cubicasa_output: Raw CubiCasa output with room bounding boxes
            floor_thickness_feet: Thickness of floor mesh (default: 0.25 feet)
            room_height_feet: Room height for metadata (default: 9.0 feet)
            
        Returns:
            List of Room3D objects with simple 3D mesh data
            
        Raises:
            SimpleRoomGenerationError: If generation fails
        """
        start_time = time.time()
        
        logger.info(f"🔧 Generating simple room meshes for {len(cubicasa_output.room_bounding_boxes)} rooms")
        logger.info(f"🔧 Using 1:1 pixel to foot scaling (NO COORDINATE SCALING)")
        logger.info(f"Floor thickness: {floor_thickness_feet} feet, Room height: {room_height_feet} feet")
        
        try:
            # Validate input
            if not cubicasa_output.room_bounding_boxes:
                raise SimpleRoomGenerationError("No room bounding boxes found in CubiCasa output")
            
            # Generate meshes for each room
            room_meshes = []
            for room_name, room_bbox in cubicasa_output.room_bounding_boxes.items():
                try:
                    room_mesh = self._generate_simple_room_mesh(
                        room_name=room_name,
                        room_bbox=room_bbox,
                        floor_thickness_feet=floor_thickness_feet,
                        room_height_feet=room_height_feet
                    )
                    room_meshes.append(room_mesh)
                    
                    logger.info(f"✅ Generated simple mesh for {room_name}: "
                              f"{len(room_mesh.vertices)} vertices, {len(room_mesh.faces)} faces")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to generate simple mesh for room '{room_name}': {str(e)}")
                    raise SimpleRoomGenerationError(f"Room '{room_name}' generation failed: {str(e)}")
            
            processing_time = time.time() - start_time
            
            logger.info(f"✅ Simple room mesh generation completed: "
                       f"{len(room_meshes)} rooms in {processing_time:.3f}s")
            
            return room_meshes
            
        except Exception as e:
            logger.error(f"❌ Simple room generation failed: {str(e)}")
            raise SimpleRoomGenerationError(f"Simple room generation failed: {str(e)}")
    
    def _generate_simple_room_mesh(self,
                                  room_name: str,
                                  room_bbox: Dict[str, int],
                                  floor_thickness_feet: float,
                                  room_height_feet: float) -> Room3D:
        """
        Generate a simple room mesh from bounding box.
        
        Args:
            room_name: Name of the room
            room_bbox: Room bounding box in pixels
            floor_thickness_feet: Floor thickness in feet
            room_height_feet: Room height in feet
            
        Returns:
            Room3D object with simple mesh
        """
        # Extract bounding box coordinates (1:1 pixel to foot scaling)
        min_x = float(room_bbox["min_x"])  # Direct pixel to foot conversion
        max_x = float(room_bbox["max_x"])
        min_y = float(room_bbox["min_y"])
        max_y = float(room_bbox["max_y"])
        
        # Validate dimensions
        if min_x >= max_x or min_y >= max_y:
            raise SimpleRoomGenerationError(f"Invalid room dimensions for {room_name}: {room_bbox}")
        
        # Generate simple rectangular floor mesh
        vertices, faces = self._create_simple_floor_mesh(
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
            floor_thickness_feet=floor_thickness_feet
        )
        
        # Calculate room dimensions
        width_feet = max_x - min_x
        length_feet = max_y - min_y
        area_sqft = width_feet * length_feet
        
        # Create room metadata
        metadata = {
            "room_type": room_name,
            "width_feet": width_feet,
            "length_feet": length_feet,
            "area_sqft": area_sqft,
            "height_feet": room_height_feet,
            "floor_thickness_feet": floor_thickness_feet,
            "pipeline_type": "simplified_test",
            "scaling_method": "1:1_pixel_to_foot",
            "mesh_type": "simple_bounding_box"
        }
        
        return Room3D(
            id=room_name,
            name=room_name,
            vertices=vertices,
            faces=faces,
            room_type=room_name,
            width_feet=width_feet,
            length_feet=length_feet,
            height_feet=room_height_feet,
            area_sqft=area_sqft,
            metadata=metadata
        )
    
    def _create_simple_floor_mesh(self,
                                 min_x: float,
                                 min_y: float,
                                 max_x: float,
                                 max_y: float,
                                 floor_thickness_feet: float) -> Tuple[List[Vertex3D], List[Face]]:
        """
        Create a simple rectangular floor mesh.
        
        Args:
            min_x, min_y, max_x, max_y: Room dimensions in feet
            floor_thickness_feet: Floor thickness in feet
            
        Returns:
            Tuple of (vertices, faces) for the floor mesh
        """
        # Create vertices for a simple rectangular floor
        # Top face vertices (Z = 0)
        v0 = Vertex3D(x=min_x, y=min_y, z=0.0)
        v1 = Vertex3D(x=max_x, y=min_y, z=0.0)
        v2 = Vertex3D(x=max_x, y=max_y, z=0.0)
        v3 = Vertex3D(x=min_x, y=max_y, z=0.0)
        
        # Bottom face vertices (Z = -floor_thickness)
        v4 = Vertex3D(x=min_x, y=min_y, z=-floor_thickness_feet)
        v5 = Vertex3D(x=max_x, y=min_y, z=-floor_thickness_feet)
        v6 = Vertex3D(x=max_x, y=max_y, z=-floor_thickness_feet)
        v7 = Vertex3D(x=min_x, y=max_y, z=-floor_thickness_feet)
        
        vertices = [v0, v1, v2, v3, v4, v5, v6, v7]
        
        # Create faces for a simple rectangular floor
        # Top face (counter-clockwise winding)
        top_face = Face(vertex_indices=[0, 1, 2, 3])
        
        # Bottom face (counter-clockwise winding)
        bottom_face = Face(vertex_indices=[7, 6, 5, 4])
        
        # Side faces (4 rectangular sides)
        side_faces = [
            Face(vertex_indices=[0, 4, 5, 1]),  # Front
            Face(vertex_indices=[1, 5, 6, 2]),  # Right
            Face(vertex_indices=[2, 6, 7, 3]),  # Back
            Face(vertex_indices=[3, 7, 4, 0])   # Left
        ]
        
        faces = [top_face, bottom_face] + side_faces
        
        return vertices, faces
