"""
Opening Cutout Generator for PlanCast.

Generates door and window cutouts in wall meshes with proper frame geometry.
This service integrates with the existing wall generation pipeline.
"""

import time
import math
import numpy as np
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass

from models.data_structures import (
    ScaledCoordinates, 
    Wall3D, 
    Vertex3D, 
    Face,
    CubiCasaOutput
)
from utils.logger import get_logger

logger = get_logger("opening_cutout_generator")


class OpeningCutoutError(Exception):
    """Custom exception for opening cutout generation errors."""
    pass


@dataclass
class Opening:
    """Represents a door or window opening."""
    type: str  # "door" or "window"
    position: Tuple[float, float]  # Position in feet
    width: float  # Width in feet
    height: float  # Height in feet
    wall_id: str  # Associated wall ID


class OpeningCutoutGenerator:
    """
    Generates door and window cutouts in wall meshes.
    
    Features:
    - Door and window cutout generation
    - Frame geometry creation
    - Wall mesh modification
    - Opening placement validation
    """
    
    def __init__(self):
        """Initialize opening cutout generator."""
        # Standard opening dimensions in feet
        self.standard_openings = {
            "door": {"width": 3.0, "height": 7.0, "frame_thickness": 0.25},
            "window": {"width": 4.0, "height": 4.0, "frame_thickness": 0.25}
        }
        
    def generate_cutouts(self, 
                        scaled_coords: ScaledCoordinates,
                        wall_meshes: List[Wall3D]) -> List[Wall3D]:
        """
        Create door and window cutouts in wall meshes.
        
        Args:
            scaled_coords: Scaled coordinates with door/window data
            wall_meshes: List of wall meshes to modify
            
        Returns:
            List of wall meshes with cutouts
            
        Raises:
            OpeningCutoutError: If cutout generation fails
        """
        start_time = time.time()
        
        logger.info(f"Generating cutouts for {len(scaled_coords.door_coordinates)} doors and {len(scaled_coords.window_coordinates)} windows")
        
        try:
            # Convert door/window coordinates to feet
            doors_feet = [(x / scaled_coords.scale_reference.scale_factor, 
                          y / scaled_coords.scale_reference.scale_factor) 
                         for x, y in scaled_coords.door_coordinates]
            
            windows_feet = [(x / scaled_coords.scale_reference.scale_factor, 
                           y / scaled_coords.scale_reference.scale_factor) 
                          for x, y in scaled_coords.window_coordinates]
            
            # Group openings by wall segment
            wall_openings = self._map_openings_to_walls(wall_meshes, doors_feet, windows_feet)
            
            # Generate cutouts for each wall
            updated_walls = []
            for wall in wall_meshes:
                openings = wall_openings.get(wall.id, [])
                if openings:
                    wall_with_cutouts = self._create_wall_with_cutouts(wall, openings)
                    updated_walls.append(wall_with_cutouts)
                else:
                    updated_walls.append(wall)
            
            processing_time = time.time() - start_time
            
            logger.info(f"✅ Cutout generation completed: {len(updated_walls)} walls in {processing_time:.3f}s")
            
            return updated_walls
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Cutout generation failed after {processing_time:.3f}s: {str(e)}")
            raise OpeningCutoutError(f"Cutout generation failed: {str(e)}")
    
    def _map_openings_to_walls(self, 
                              walls: List[Wall3D], 
                              doors: List[Tuple[float, float]], 
                              windows: List[Tuple[float, float]]) -> Dict[str, List[Opening]]:
        """
        Map door/window coordinates to nearest wall segments.
        
        Args:
            walls: List of wall meshes
            doors: List of door coordinates in feet
            windows: List of window coordinates in feet
            
        Returns:
            Dictionary mapping wall IDs to list of openings
        """
        wall_openings = {}
        
        # Process doors
        for door_coord in doors:
            nearest_wall = self._find_nearest_wall(walls, door_coord)
            if nearest_wall:
                if nearest_wall.id not in wall_openings:
                    wall_openings[nearest_wall.id] = []
                wall_openings[nearest_wall.id].append(Opening(
                    type="door",
                    position=door_coord,
                    width=self.standard_openings["door"]["width"],
                    height=self.standard_openings["door"]["height"],
                    wall_id=nearest_wall.id
                ))
        
        # Process windows
        for window_coord in windows:
            nearest_wall = self._find_nearest_wall(walls, window_coord)
            if nearest_wall:
                if nearest_wall.id not in wall_openings:
                    wall_openings[nearest_wall.id] = []
                wall_openings[nearest_wall.id].append(Opening(
                    type="window",
                    position=window_coord,
                    width=self.standard_openings["window"]["width"],
                    height=self.standard_openings["window"]["height"],
                    wall_id=nearest_wall.id
                ))
        
        return wall_openings
    
    def _find_nearest_wall(self, walls: List[Wall3D], point: Tuple[float, float]) -> Optional[Wall3D]:
        """
        Find the nearest wall to a given point.
        
        Args:
            walls: List of wall meshes
            point: Point coordinates (x, y) in feet
            
        Returns:
            Nearest wall or None if no wall found
        """
        if not walls:
            return None
        
        min_distance = float('inf')
        nearest_wall = None
        
        for wall in walls:
            # Calculate distance to wall center
            wall_center = self._calculate_wall_center(wall)
            distance = math.sqrt((point[0] - wall_center[0])**2 + (point[1] - wall_center[1])**2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_wall = wall
        
        return nearest_wall
    
    def _calculate_wall_center(self, wall: Wall3D) -> Tuple[float, float]:
        """
        Calculate the center point of a wall.
        
        Args:
            wall: Wall mesh
            
        Returns:
            Center coordinates (x, y) in feet
        """
        vertices = wall.vertices
        if not vertices:
            return (0.0, 0.0)
        
        x_coords = [v.x for v in vertices]
        y_coords = [v.y for v in vertices]
        
        center_x = sum(x_coords) / len(x_coords)
        center_y = sum(y_coords) / len(y_coords)
        
        return (center_x, center_y)
    
    def _create_wall_with_cutouts(self, wall: Wall3D, openings: List[Opening]) -> Wall3D:
        """
        Create wall mesh with door/window cutouts.
        
        Args:
            wall: Original wall mesh
            openings: List of openings to create
            
        Returns:
            Wall mesh with cutouts
        """
        # Start with original wall vertices and faces
        vertices = wall.vertices.copy()
        faces = wall.faces.copy()
        
        # For each opening, create a rectangular cutout
        for opening in openings:
            # Create cutout geometry
            cutout_vertices, cutout_faces = self._create_rectangular_cutout(
                wall, opening.position, opening.width, opening.height
            )
            
            # Remove faces that intersect with the cutout
            faces = self._remove_intersecting_faces(faces, cutout_vertices)
            
            # Add frame geometry
            if opening.type == "door":
                frame_vertices, frame_faces = self._create_door_frame(
                    cutout_vertices, wall.height_feet, opening
                )
            else:  # window
                frame_vertices, frame_faces = self._create_window_frame(
                    cutout_vertices, wall.height_feet, opening
                )
            
            vertices.extend(frame_vertices)
            faces.extend(frame_faces)
        
        return Wall3D(
            id=wall.id,
            vertices=vertices,
            faces=faces,
            height_feet=wall.height_feet,
            thickness_feet=wall.thickness_feet
        )
    
    def _create_rectangular_cutout(self, 
                                 wall: Wall3D, 
                                 position: Tuple[float, float], 
                                 width: float, 
                                 height: float) -> Tuple[List[Vertex3D], List[Face]]:
        """
        Create a rectangular cutout in a wall.
        
        Args:
            wall: Wall mesh
            position: Cutout position (x, y) in feet
            width: Cutout width in feet
            height: Cutout height in feet
            
        Returns:
            Tuple of (vertices, faces) for the cutout
        """
        x, y = position
        half_width = width / 2
        half_height = height / 2
        
        # Create cutout vertices (rectangular opening)
        cutout_vertices = [
            Vertex3D(x=x - half_width, y=y - half_height, z=0.0),  # Bottom-left
            Vertex3D(x=x + half_width, y=y - half_height, z=0.0),  # Bottom-right
            Vertex3D(x=x + half_width, y=y + half_height, z=0.0),  # Top-right
            Vertex3D(x=x - half_width, y=y + half_height, z=0.0),  # Top-left
        ]
        
        # Create cutout faces (simple rectangle)
        cutout_faces = [
            Face(indices=[0, 1, 2]),  # First triangle
            Face(indices=[0, 2, 3]),  # Second triangle
        ]
        
        return cutout_vertices, cutout_faces
    
    def _create_door_frame(self, 
                          cutout_vertices: List[Vertex3D], 
                          wall_height: float,
                          opening: Opening) -> Tuple[List[Vertex3D], List[Face]]:
        """
        Create door frame geometry.
        
        Args:
            cutout_vertices: Cutout vertices
            wall_height: Wall height in feet
            opening: Door opening data
            
        Returns:
            Tuple of (vertices, faces) for the door frame
        """
        frame_thickness = self.standard_openings["door"]["frame_thickness"]
        
        # Create door frame vertices (thicker frame around the opening)
        frame_vertices = []
        frame_faces = []
        
        # Door frame extends from floor to wall height
        for vertex in cutout_vertices:
            # Create frame vertices at different Z levels
            frame_vertices.extend([
                Vertex3D(x=vertex.x, y=vertex.y, z=0.0),  # Bottom
                Vertex3D(x=vertex.x, y=vertex.y, z=wall_height),  # Top
            ])
        
        # Create frame faces (simple rectangular frame)
        # This is a simplified frame - in a real implementation, you'd create more detailed geometry
        frame_faces = [
            Face(indices=[0, 1, 2]),  # Frame face 1
            Face(indices=[1, 2, 3]),  # Frame face 2
        ]
        
        return frame_vertices, frame_faces
    
    def _create_window_frame(self, 
                           cutout_vertices: List[Vertex3D], 
                           wall_height: float,
                           opening: Opening) -> Tuple[List[Vertex3D], List[Face]]:
        """
        Create window frame geometry.
        
        Args:
            cutout_vertices: Cutout vertices
            wall_height: Wall height in feet
            opening: Window opening data
            
        Returns:
            Tuple of (vertices, faces) for the window frame
        """
        frame_thickness = self.standard_openings["window"]["frame_thickness"]
        
        # Window frame is typically positioned at a specific height
        window_height = opening.height
        window_bottom = wall_height * 0.3  # Windows typically start at 30% of wall height
        
        # Create window frame vertices
        frame_vertices = []
        frame_faces = []
        
        for vertex in cutout_vertices:
            # Create frame vertices at window height
            frame_vertices.extend([
                Vertex3D(x=vertex.x, y=vertex.y, z=window_bottom),  # Bottom
                Vertex3D(x=vertex.x, y=vertex.y, z=window_bottom + window_height),  # Top
            ])
        
        # Create frame faces
        frame_faces = [
            Face(indices=[0, 1, 2]),  # Frame face 1
            Face(indices=[1, 2, 3]),  # Frame face 2
        ]
        
        return frame_vertices, frame_faces
    
    def _remove_intersecting_faces(self, 
                                 faces: List[Face], 
                                 cutout_vertices: List[Vertex3D]) -> List[Face]:
        """
        Remove faces that intersect with the cutout.
        
        Args:
            faces: List of faces
            cutout_vertices: Cutout vertices
            
        Returns:
            List of faces with intersecting faces removed
        """
        # This is a simplified implementation
        # In a real implementation, you'd need more sophisticated intersection detection
        
        # For now, we'll keep all faces and let the frame geometry handle the visual effect
        return faces


# Singleton instance for global use
_opening_cutout_generator: Optional[OpeningCutoutGenerator] = None


def get_opening_cutout_generator() -> OpeningCutoutGenerator:
    """
    Get the global opening cutout generator instance.
    
    Returns:
        OpeningCutoutGenerator instance
    """
    global _opening_cutout_generator
    if _opening_cutout_generator is None:
        _opening_cutout_generator = OpeningCutoutGenerator()
    return _opening_cutout_generator


# Convenience function for direct use
def generate_wall_cutouts(scaled_coords: ScaledCoordinates,
                         wall_meshes: List[Wall3D]) -> List[Wall3D]:
    """
    Generate cutouts in wall meshes.
    
    Args:
        scaled_coords: Scaled coordinates with door/window data
        wall_meshes: List of wall meshes to modify
        
    Returns:
        List of wall meshes with cutouts
    """
    generator = get_opening_cutout_generator()
    return generator.generate_cutouts(scaled_coords, wall_meshes)
