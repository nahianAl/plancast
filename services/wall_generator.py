"""
Wall Mesh Generator Service for PlanCast.

Task 4: Generate 3D wall meshes from scaled coordinates.
Converts wall polylines into 3D wall geometry with thickness and height.
"""

import time
import math
from typing import List, Tuple, Dict, Optional, Any
import logging

from models.data_structures import (
    ScaledCoordinates, 
    Wall3D, 
    Vertex3D, 
    Face,
    ProcessingJob
)
from utils.logger import get_logger, log_job_start, log_job_complete, log_job_error

logger = get_logger("wall_generator")


class WallGenerationError(Exception):
    """Custom exception for wall mesh generation errors."""
    pass


class WallMeshGenerator:
    """
    Production wall mesh generator service.
    
    Converts scaled wall coordinates into 3D wall meshes with proper
    extrusion, thickness, and vertex/face structures.
    """
    
    def __init__(self):
        """Initialize wall mesh generator."""
        self.default_wall_thickness_feet = 0.5
        self.default_wall_height_feet = 9.0
        
    def generate_wall_meshes(self, 
                           scaled_coords: ScaledCoordinates,
                           wall_thickness_feet: float = 0.5,
                           wall_height_feet: float = 9.0) -> List[Wall3D]:
        """
        Generate 3D wall meshes from scaled coordinates.
        
        Args:
            scaled_coords: Scaled coordinates with wall polylines in feet
            wall_thickness_feet: Thickness of wall mesh (default: 0.5 feet)
            wall_height_feet: Wall height in feet (default: 9.0 feet)
            
        Returns:
            List of Wall3D objects with 3D mesh data
            
        Raises:
            WallGenerationError: If generation fails
        """
        start_time = time.time()
        
        logger.info(f"Generating wall meshes from {len(scaled_coords.walls_feet)} wall points")
        logger.info(f"Wall thickness: {wall_thickness_feet} feet, Wall height: {wall_height_feet} feet")
        
        try:
            # Validate input
            self._validate_scaled_coordinates(scaled_coords)
            
            # Extract wall segments from room boundaries
            wall_segments = self._extract_wall_segments_from_rooms(scaled_coords)
            
            # Generate meshes for each wall segment
            wall_meshes = []
            wall_id_counter = 0
            
            for segment in wall_segments:
                try:
                    wall_mesh = self._generate_single_wall_mesh(
                        wall_id=f"wall_{wall_id_counter:03d}",
                        start_point=segment[0],
                        end_point=segment[1],
                        wall_thickness_feet=wall_thickness_feet,
                        wall_height_feet=wall_height_feet
                    )
                    wall_meshes.append(wall_mesh)
                    wall_id_counter += 1
                    
                    logger.info(f"✅ Generated wall {wall_mesh.id}: "
                              f"{len(wall_mesh.vertices)} vertices, {len(wall_mesh.faces)} faces")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to generate wall segment {wall_id_counter}: {str(e)}")
                    raise WallGenerationError(f"Wall segment {wall_id_counter} generation failed: {str(e)}")
            
            processing_time = time.time() - start_time
            
            logger.info(f"✅ Wall mesh generation completed: "
                       f"{len(wall_meshes)} walls in {processing_time:.3f}s")
            
            return wall_meshes
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Wall mesh generation failed after {processing_time:.3f}s: {str(e)}")
            raise WallGenerationError(f"Wall mesh generation failed: {str(e)}")
    
    def _validate_scaled_coordinates(self, scaled_coords: ScaledCoordinates) -> None:
        """
        Validate scaled coordinates input.
        
        Args:
            scaled_coords: Scaled coordinates to validate
            
        Raises:
            WallGenerationError: If validation fails
        """
        if not scaled_coords.rooms_feet:
            raise WallGenerationError("No rooms found in scaled coordinates")
        
        if len(scaled_coords.walls_feet) < 2:
            raise WallGenerationError("Insufficient wall points for wall generation")
        
        # Validate room data
        for room_name, room_data in scaled_coords.rooms_feet.items():
            required_fields = ['width_feet', 'length_feet', 'area_sqft', 'x_offset_feet', 'y_offset_feet']
            
            for field in required_fields:
                if field not in room_data:
                    raise WallGenerationError(f"Room '{room_name}' missing required field: {field}")
                
                if not isinstance(room_data[field], (int, float)):
                    raise WallGenerationError(f"Room '{room_name}' field '{field}' must be numeric")
                
                if room_data[field] <= 0:
                    raise WallGenerationError(f"Room '{room_name}' field '{field}' must be positive")
        
        logger.info(f"✅ Validated {len(scaled_coords.rooms_feet)} rooms and {len(scaled_coords.walls_feet)} wall points")
    
    def _extract_wall_segments_from_rooms(self, scaled_coords: ScaledCoordinates) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Extract wall segments from room boundaries.
        
        Args:
            scaled_coords: Scaled coordinates with room data
            
        Returns:
            List of wall segments as (start_point, end_point) tuples
        """
        wall_segments = []
        rooms = list(scaled_coords.rooms_feet.items())
        
        # Generate walls between adjacent rooms
        for i, (room1_name, room1_data) in enumerate(rooms):
            for j, (room2_name, room2_data) in enumerate(rooms[i+1:], i+1):
                # Check if rooms are adjacent (share a wall)
                shared_wall = self._find_shared_wall(room1_data, room2_data)
                if shared_wall:
                    wall_segments.append(shared_wall)
                    logger.debug(f"Found shared wall between {room1_name} and {room2_name}")
        
        # Add outer walls (building perimeter)
        outer_walls = self._generate_outer_walls(scaled_coords)
        wall_segments.extend(outer_walls)
        
        logger.info(f"Extracted {len(wall_segments)} wall segments from room boundaries")
        return wall_segments
    
    def _find_shared_wall(self, room1_data: Dict[str, float], room2_data: Dict[str, float]) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Find shared wall between two rooms.
        
        Args:
            room1_data: First room data
            room2_data: Second room data
            
        Returns:
            Wall segment if rooms share a wall, None otherwise
        """
        # Room 1 boundaries
        r1_min_x = room1_data['x_offset_feet']
        r1_max_x = r1_min_x + room1_data['width_feet']
        r1_min_y = room1_data['y_offset_feet']
        r1_max_y = r1_min_y + room1_data['length_feet']
        
        # Room 2 boundaries
        r2_min_x = room2_data['x_offset_feet']
        r2_max_x = r2_min_x + room2_data['width_feet']
        r2_min_y = room2_data['y_offset_feet']
        r2_max_y = r2_min_y + room2_data['length_feet']
        
        # Check for vertical shared wall (same x-coordinate)
        if abs(r1_max_x - r2_min_x) < 0.1 or abs(r2_max_x - r1_min_x) < 0.1:
            # Vertical wall
            if r1_max_x - r2_min_x < 0.1:  # Room 1 right edge touches Room 2 left edge
                x = r1_max_x
                y_min = max(r1_min_y, r2_min_y)
                y_max = min(r1_max_y, r2_max_y)
                if y_max > y_min:
                    return ((x, y_min), (x, y_max))
            elif r2_max_x - r1_min_x < 0.1:  # Room 2 right edge touches Room 1 left edge
                x = r2_max_x
                y_min = max(r1_min_y, r2_min_y)
                y_max = min(r1_max_y, r2_max_y)
                if y_max > y_min:
                    return ((x, y_min), (x, y_max))
        
        # Check for horizontal shared wall (same y-coordinate)
        if abs(r1_max_y - r2_min_y) < 0.1 or abs(r2_max_y - r1_min_y) < 0.1:
            # Horizontal wall
            if r1_max_y - r2_min_y < 0.1:  # Room 1 top edge touches Room 2 bottom edge
                y = r1_max_y
                x_min = max(r1_min_x, r2_min_x)
                x_max = min(r1_max_x, r2_max_x)
                if x_max > x_min:
                    return ((x_min, y), (x_max, y))
            elif r2_max_y - r1_min_y < 0.1:  # Room 2 top edge touches Room 1 bottom edge
                y = r2_max_y
                x_min = max(r1_min_x, r2_min_x)
                x_max = min(r1_max_x, r2_max_x)
                if x_max > x_min:
                    return ((x_min, y), (x_max, y))
        
        return None
    
    def _generate_outer_walls(self, scaled_coords: ScaledCoordinates) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Generate outer walls for building perimeter.
        
        Args:
            scaled_coords: Scaled coordinates with building dimensions
            
        Returns:
            List of outer wall segments
        """
        building = scaled_coords.total_building_size
        outer_walls = []
        
        # Calculate building bounds
        min_x = 0
        max_x = building.width_feet
        min_y = 0
        max_y = building.length_feet
        
        # Bottom wall
        outer_walls.append(((min_x, min_y), (max_x, min_y)))
        # Top wall
        outer_walls.append(((min_x, max_y), (max_x, max_y)))
        # Left wall
        outer_walls.append(((min_x, min_y), (min_x, max_y)))
        # Right wall
        outer_walls.append(((max_x, min_y), (max_x, max_y)))
        
        logger.debug(f"Generated {len(outer_walls)} outer wall segments")
        return outer_walls
    
    def _generate_single_wall_mesh(self,
                                 wall_id: str,
                                 start_point: Tuple[float, float],
                                 end_point: Tuple[float, float],
                                 wall_thickness_feet: float,
                                 wall_height_feet: float) -> Wall3D:
        """
        Generate 3D mesh for a single wall segment.
        
        Args:
            wall_id: Unique wall identifier
            start_point: Wall start point (x, y)
            end_point: Wall end point (x, y)
            wall_thickness_feet: Wall thickness
            wall_height_feet: Wall height
            
        Returns:
            Wall3D object with mesh data
        """
        # Calculate wall direction and length
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        wall_length = math.sqrt(dx*dx + dy*dy)
        
        if wall_length < 0.1:
            raise WallGenerationError(f"Wall {wall_id} is too short: {wall_length:.3f} feet")
        
        # Calculate wall normal (perpendicular to wall direction)
        wall_normal_x = -dy / wall_length
        wall_normal_y = dx / wall_length
        
        # Calculate offset points for wall thickness
        half_thickness = wall_thickness_feet / 2
        
        # Left side of wall
        left_start = (
            start_point[0] + wall_normal_x * half_thickness,
            start_point[1] + wall_normal_y * half_thickness
        )
        left_end = (
            end_point[0] + wall_normal_x * half_thickness,
            end_point[1] + wall_normal_y * half_thickness
        )
        
        # Right side of wall
        right_start = (
            start_point[0] - wall_normal_x * half_thickness,
            start_point[1] - wall_normal_y * half_thickness
        )
        right_end = (
            end_point[0] - wall_normal_x * half_thickness,
            end_point[1] - wall_normal_y * half_thickness
        )
        
        # Generate vertices and faces for wall prism
        vertices, faces = self._build_wall_prism(
            left_start, left_end, right_start, right_end, wall_height_feet
        )
        
        # Create Wall3D object
        wall_mesh = Wall3D(
            id=wall_id,
            vertices=vertices,
            faces=faces,
            height_feet=wall_height_feet,
            thickness_feet=wall_thickness_feet
        )
        
        logger.debug(f"Generated wall '{wall_id}': "
                    f"length {wall_length:.1f}', position ({start_point[0]:.1f}, {start_point[1]:.1f})")
        
        return wall_mesh
    
    def _build_wall_prism(self,
                         left_start: Tuple[float, float],
                         left_end: Tuple[float, float],
                         right_start: Tuple[float, float],
                         right_end: Tuple[float, float],
                         height_feet: float) -> Tuple[List[Vertex3D], List[Face]]:
        """
        Build wall prism from offset polylines.
        
        Args:
            left_start, left_end: Left side of wall
            right_start, right_end: Right side of wall
            height_feet: Wall height
            
        Returns:
            Tuple of (vertices, faces) for the wall prism
        """
        # Create 8 vertices for the wall box (4 bottom + 4 top)
        vertices = [
            # Bottom vertices (z = 0)
            Vertex3D(x=left_start[0], y=left_start[1], z=0.0),      # 0: left start bottom
            Vertex3D(x=left_end[0], y=left_end[1], z=0.0),          # 1: left end bottom
            Vertex3D(x=right_end[0], y=right_end[1], z=0.0),        # 2: right end bottom
            Vertex3D(x=right_start[0], y=right_start[1], z=0.0),    # 3: right start bottom
            
            # Top vertices (z = height)
            Vertex3D(x=left_start[0], y=left_start[1], z=height_feet),   # 4: left start top
            Vertex3D(x=left_end[0], y=left_end[1], z=height_feet),       # 5: left end top
            Vertex3D(x=right_end[0], y=right_end[1], z=height_feet),     # 6: right end top
            Vertex3D(x=right_start[0], y=right_start[1], z=height_feet), # 7: right start top
        ]
        
        # Create 12 triangular faces (6 quads = 12 triangles)
        faces = [
            # Bottom face (triangulated)
            Face(indices=[0, 1, 2]),  # Triangle 1
            Face(indices=[0, 2, 3]),  # Triangle 2
            
            # Top face (triangulated)
            Face(indices=[4, 6, 5]),  # Triangle 1 (note: counter-clockwise for top)
            Face(indices=[4, 7, 6]),  # Triangle 2
            
            # Left side face
            Face(indices=[0, 4, 5]),  # Triangle 1
            Face(indices=[0, 5, 1]),  # Triangle 2
            
            # Right side face
            Face(indices=[2, 6, 7]),  # Triangle 1
            Face(indices=[2, 7, 3]),  # Triangle 2
            
            # Start end face
            Face(indices=[0, 3, 7]),  # Triangle 1
            Face(indices=[0, 7, 4]),  # Triangle 2
            
            # End end face
            Face(indices=[1, 5, 6]),  # Triangle 1
            Face(indices=[1, 6, 2]),  # Triangle 2
        ]
        
        return vertices, faces
    
    def validate_wall_mesh(self, wall_mesh: Wall3D) -> Dict[str, Any]:
        """
        Validate generated wall mesh.
        
        Args:
            wall_mesh: Wall3D object to validate
            
        Returns:
            Validation result dictionary
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "vertex_count": len(wall_mesh.vertices),
            "face_count": len(wall_mesh.faces)
        }
        
        # Check vertex count (should be 8 for wall prism)
        if len(wall_mesh.vertices) != 8:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Expected 8 vertices, got {len(wall_mesh.vertices)}")
        
        # Check face count (should be 12 triangles for wall prism)
        if len(wall_mesh.faces) != 12:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Expected 12 faces, got {len(wall_mesh.faces)}")
        
        # Validate face indices
        for i, face in enumerate(wall_mesh.faces):
            if len(face.indices) != 3:
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"Face {i} must have 3 indices, got {len(face.indices)}")
            
            # Check index bounds
            for index in face.indices:
                if index < 0 or index >= len(wall_mesh.vertices):
                    validation_result["is_valid"] = False
                    validation_result["errors"].append(f"Face {i} has invalid vertex index: {index}")
        
        # Check wall dimensions
        if wall_mesh.height_feet <= 0:
            validation_result["is_valid"] = False
            validation_result["errors"].append("Wall height must be positive")
        
        if wall_mesh.thickness_feet <= 0:
            validation_result["is_valid"] = False
            validation_result["errors"].append("Wall thickness must be positive")
        
        return validation_result


# Global service instance
_wall_generator = None


def get_wall_generator() -> WallMeshGenerator:
    """
    Get or create global wall generator service instance.
    
    Returns:
        WallMeshGenerator instance
    """
    global _wall_generator
    if _wall_generator is None:
        _wall_generator = WallMeshGenerator()
        logger.info("✅ Wall mesh generator service initialized")
    return _wall_generator
