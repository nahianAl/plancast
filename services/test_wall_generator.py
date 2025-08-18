"""
Simple Wall Generator for PlanCast Test Pipeline

This is a TEMPORARY simplified wall generator for debugging 3D model generation issues.
It skips coordinate scaling and door/window cutouts.

IMPORTANT: This is for debugging only. After fixing core issues, we must integrate
back with the full enhanced pipeline.
"""

import time
import math
from typing import List, Tuple, Dict, Optional, Any
import logging

from models.data_structures import (
    CubiCasaOutput, 
    Wall3D, 
    Vertex3D, 
    Face
)
from utils.logger import get_logger

logger = get_logger("test_wall_generator")


class SimpleWallGenerationError(Exception):
    """Custom exception for simple wall generation errors."""
    pass


class SimpleWallGenerator:
    """
    Simplified wall mesh generator for debugging.
    
    Features:
    - 1:1 pixel to foot scaling (no coordinate scaling)
    - Basic wall generation from room boundaries (no complex wall coordinates)
    - Simple rectangular wall meshes
    - No door/window cutouts
    - No enhanced validation
    """
    
    def __init__(self):
        """Initialize simple wall generator."""
        self.default_wall_thickness_feet = 0.5
        self.default_wall_height_feet = 9.0
        self.min_wall_length_feet = 2.0  # Minimum wall segment length
        
    def generate_simple_walls(self, 
                            cubicasa_output: CubiCasaOutput,
                            wall_thickness_feet: float = 0.5,
                            wall_height_feet: float = 9.0) -> List[Wall3D]:
        """
        Generate simple 3D wall meshes from CubiCasa output.
        
        Args:
            cubicasa_output: Raw CubiCasa output with room bounding boxes
            wall_thickness_feet: Thickness of wall mesh (default: 0.5 feet)
            wall_height_feet: Wall height in feet (default: 9.0 feet)
            
        Returns:
            List of Wall3D objects with simple 3D mesh data
            
        Raises:
            SimpleWallGenerationError: If generation fails
        """
        start_time = time.time()
        
        logger.info(f"🔧 Generating simple wall meshes from {len(cubicasa_output.room_bounding_boxes)} rooms")
        logger.info(f"🔧 Using 1:1 pixel to foot scaling (NO COORDINATE SCALING)")
        logger.info(f"🔧 NO DOOR/WINDOW CUTOUTS")
        logger.info(f"Wall thickness: {wall_thickness_feet} feet, Wall height: {wall_height_feet} feet")
        
        try:
            # Validate input
            if not cubicasa_output.room_bounding_boxes:
                raise SimpleWallGenerationError("No room bounding boxes found in CubiCasa output")
            
            # Extract wall segments from room boundaries
            wall_segments = self._extract_simple_wall_segments(cubicasa_output.room_bounding_boxes)
            
            logger.info(f"🔧 Extracted {len(wall_segments)} wall segments from room boundaries")
            
            # Generate meshes for each wall segment
            wall_meshes = []
            wall_id_counter = 0
            
            for segment in wall_segments:
                try:
                    wall_mesh = self._generate_simple_wall_mesh(
                        wall_id=f"simple_wall_{wall_id_counter:03d}",
                        start_point=segment[0],
                        end_point=segment[1],
                        wall_thickness_feet=wall_thickness_feet,
                        wall_height_feet=wall_height_feet
                    )
                    wall_meshes.append(wall_mesh)
                    wall_id_counter += 1
                    
                    logger.info(f"✅ Generated simple wall {wall_mesh.id}: "
                              f"{len(wall_mesh.vertices)} vertices, {len(wall_mesh.faces)} faces")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to generate simple wall segment {wall_id_counter}: {str(e)}")
                    # Continue with other walls instead of failing completely
                    continue
            
            processing_time = time.time() - start_time
            
            logger.info(f"✅ Simple wall mesh generation completed: "
                       f"{len(wall_meshes)} walls in {processing_time:.3f}s")
            
            return wall_meshes
            
        except Exception as e:
            logger.error(f"❌ Simple wall generation failed: {str(e)}")
            raise SimpleWallGenerationError(f"Simple wall generation failed: {str(e)}")
    
    def _extract_simple_wall_segments(self, room_bounding_boxes: Dict[str, Dict[str, int]]) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Extract simple wall segments from room bounding boxes.
        
        Args:
            room_bounding_boxes: Room bounding boxes from CubiCasa output
            
        Returns:
            List of wall segments as (start_point, end_point) tuples
        """
        wall_segments = []
        
        # Convert room bounding boxes to wall segments
        for room_name, bbox in room_bounding_boxes.items():
            # Extract room boundaries (1:1 pixel to foot scaling)
            min_x = float(bbox["min_x"])
            max_x = float(bbox["max_x"])
            min_y = float(bbox["min_y"])
            max_y = float(bbox["max_y"])
            
            # Create 4 walls for each room (simple rectangular approach)
            walls = [
                # Bottom wall (min_y)
                ((min_x, min_y), (max_x, min_y)),
                # Right wall (max_x)
                ((max_x, min_y), (max_x, max_y)),
                # Top wall (max_y)
                ((max_x, max_y), (min_x, max_y)),
                # Left wall (min_x)
                ((min_x, max_y), (min_x, min_y))
            ]
            
            # Add walls that meet minimum length requirement
            for wall in walls:
                start, end = wall
                length = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
                if length >= self.min_wall_length_feet:
                    wall_segments.append(wall)
        
        # Remove duplicate wall segments (walls shared between rooms)
        unique_segments = []
        for segment in wall_segments:
            if not self._is_duplicate_segment(segment, unique_segments):
                unique_segments.append(segment)
        
        return unique_segments
    
    def _is_duplicate_segment(self, segment: Tuple[Tuple[float, float], Tuple[float, float]], 
                            existing_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]]) -> bool:
        """
        Check if a wall segment is a duplicate of existing segments.
        
        Args:
            segment: Wall segment to check
            existing_segments: List of existing wall segments
            
        Returns:
            True if segment is a duplicate
        """
        start1, end1 = segment
        
        for existing in existing_segments:
            start2, end2 = existing
            
            # Check if segments are the same (allowing for reversed direction)
            if ((abs(start1[0] - start2[0]) < 0.1 and abs(start1[1] - start2[1]) < 0.1 and
                 abs(end1[0] - end2[0]) < 0.1 and abs(end1[1] - end2[1]) < 0.1) or
                (abs(start1[0] - end2[0]) < 0.1 and abs(start1[1] - end2[1]) < 0.1 and
                 abs(end1[0] - start2[0]) < 0.1 and abs(end1[1] - start2[1]) < 0.1)):
                return True
        
        return False
    
    def _generate_simple_wall_mesh(self,
                                  wall_id: str,
                                  start_point: Tuple[float, float],
                                  end_point: Tuple[float, float],
                                  wall_thickness_feet: float,
                                  wall_height_feet: float) -> Wall3D:
        """
        Generate a simple wall mesh from start and end points.
        
        Args:
            wall_id: Unique identifier for the wall
            start_point: Start point (x, y) in feet
            end_point: End point (x, y) in feet
            wall_thickness_feet: Wall thickness in feet
            wall_height_feet: Wall height in feet
            
        Returns:
            Wall3D object with simple mesh
        """
        # Calculate wall direction and length
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        length = math.sqrt(dx**2 + dy**2)
        
        if length < 0.1:  # Very short wall
            raise SimpleWallGenerationError(f"Wall {wall_id} is too short: {length} feet")
        
        # Calculate wall normal (perpendicular to wall direction)
        normal_x = -dy / length
        normal_y = dx / length
        
        # Calculate wall corners (offset by half thickness)
        half_thickness = wall_thickness_feet / 2
        
        # Inner corners (toward room center)
        inner_start = (start_point[0] - normal_x * half_thickness, start_point[1] - normal_y * half_thickness)
        inner_end = (end_point[0] - normal_x * half_thickness, end_point[1] - normal_y * half_thickness)
        
        # Outer corners (away from room center)
        outer_start = (start_point[0] + normal_x * half_thickness, start_point[1] + normal_y * half_thickness)
        outer_end = (end_point[0] + normal_x * half_thickness, end_point[1] + normal_y * half_thickness)
        
        # Create vertices for the wall
        # Bottom vertices (Z = 0)
        v0 = Vertex3D(x=inner_start[0], y=inner_start[1], z=0.0)
        v1 = Vertex3D(x=outer_start[0], y=outer_start[1], z=0.0)
        v2 = Vertex3D(x=outer_end[0], y=outer_end[1], z=0.0)
        v3 = Vertex3D(x=inner_end[0], y=inner_end[1], z=0.0)
        
        # Top vertices (Z = wall_height)
        v4 = Vertex3D(x=inner_start[0], y=inner_start[1], z=wall_height_feet)
        v5 = Vertex3D(x=outer_start[0], y=outer_start[1], z=wall_height_feet)
        v6 = Vertex3D(x=outer_end[0], y=outer_end[1], z=wall_height_feet)
        v7 = Vertex3D(x=inner_end[0], y=inner_end[1], z=wall_height_feet)
        
        vertices = [v0, v1, v2, v3, v4, v5, v6, v7]
        
        # Create faces for the wall
        # Front face (Z = 0)
        front_face = Face(indices=[0, 1, 2, 3])
        
        # Back face (Z = wall_height)
        back_face = Face(indices=[7, 6, 5, 4])
        
        # Side faces (4 rectangular sides)
        side_faces = [
            Face(indices=[0, 4, 5, 1]),  # Left side
            Face(indices=[1, 5, 6, 2]),  # Top side
            Face(indices=[2, 6, 7, 3]),  # Right side
            Face(indices=[3, 7, 4, 0])   # Bottom side
        ]
        
        faces = [front_face, back_face] + side_faces
        
        # Create wall metadata
        metadata = {
            "wall_type": "simple_interior",
            "length_feet": length,
            "height_feet": wall_height_feet,
            "thickness_feet": wall_thickness_feet,
            "start_point": start_point,
            "end_point": end_point,
            "pipeline_type": "simplified_test",
            "scaling_method": "1:1_pixel_to_foot",
            "mesh_type": "simple_rectangular",
            "cutouts": "none"
        }
        
        return Wall3D(
            id=wall_id,
            vertices=vertices,
            faces=faces,
            wall_type="interior",
            length_feet=length,
            height_feet=wall_height_feet,
            thickness_feet=wall_thickness_feet,
            metadata=metadata
        )
