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
                    # Get room polygon if available
                    room_polygon = scaled_coords.room_polygons.get(room_name)
                    
                    room_mesh = self._generate_single_room_mesh(
                        room_name=room_name,
                        room_data=room_data,
                        floor_thickness_feet=floor_thickness_feet,
                        room_height_feet=room_height_feet,
                        room_polygon=room_polygon
                    )
                    room_meshes.append(room_mesh)
                    
                    mesh_type = "polygon" if room_polygon else "bounding box"
                    logger.info(f"✅ Generated {mesh_type} mesh for {room_name}: "
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
                                 room_height_feet: float,
                                 room_polygon: Optional[List[Tuple[float, float]]] = None) -> Room3D:
        """
        Generate 3D mesh for a single room using actual polygon or bounding box.
        
        Args:
            room_name: Room name/type
            room_data: Room dimensions and position
            floor_thickness_feet: Floor thickness
            room_height_feet: Room height
            room_polygon: Optional room polygon coordinates in feet
            
        Returns:
            Room3D object with complete 3D mesh data
        """
        if room_polygon and len(room_polygon) >= 3:
            # Use actual room polygon for more accurate geometry
            vertices, faces = self._build_3d_room_from_polygon(
                room_polygon=room_polygon,
                height_feet=room_height_feet
            )
            
            logger.debug(f"Generated 3D room '{room_name}' from polygon: "
                        f"{len(room_polygon)} points, {len(vertices)} vertices, {len(faces)} faces")
        else:
            # Fallback to bounding box method
            width_feet = room_data['width_feet']
            length_feet = room_data['length_feet']
            x_offset_feet = room_data['x_offset_feet']
            y_offset_feet = room_data['y_offset_feet']
            
            # Calculate room corners
            min_x = x_offset_feet
            max_x = x_offset_feet + width_feet
            min_y = y_offset_feet
            max_y = y_offset_feet + length_feet
            
            # Generate complete 3D room mesh (floor, walls, ceiling)
            vertices, faces = self._build_3d_room_box(
                min_x=min_x,
                min_y=min_y,
                max_x=max_x,
                max_y=max_y,
                height_feet=room_height_feet
            )
            
            logger.debug(f"Generated 3D room '{room_name}' from bounding box: "
                        f"size {width_feet:.1f}' × {length_feet:.1f}' × {room_height_feet:.1f}', "
                        f"position ({x_offset_feet:.1f}, {y_offset_feet:.1f})")
        
        # Create Room3D object
        room_mesh = Room3D(
            name=room_name,
            vertices=vertices,
            faces=faces,
            elevation_feet=0.0,
            height_feet=room_height_feet
        )
        
        return room_mesh
    
    def _build_3d_room_box(self,
                          min_x: float,
                          min_y: float,
                          max_x: float,
                          max_y: float,
                          height_feet: float) -> Tuple[List[Vertex3D], List[Face]]:
        """
        Build complete 3D room box with floor, walls, and ceiling.
        
        Args:
            min_x, min_y: Bottom-left corner
            max_x, max_y: Top-right corner
            height_feet: Room height
            
        Returns:
            Tuple of (vertices, faces) for the complete 3D room
        """
        # Create 8 vertices for the room box (4 bottom + 4 top)
        vertices = [
            # Bottom vertices (z = 0) - floor
            Vertex3D(x=min_x, y=min_y, z=0.0),      # 0: bottom-left
            Vertex3D(x=max_x, y=min_y, z=0.0),      # 1: bottom-right
            Vertex3D(x=max_x, y=max_y, z=0.0),      # 2: top-right
            Vertex3D(x=min_x, y=max_y, z=0.0),      # 3: top-left
            
            # Top vertices (z = height) - ceiling
            Vertex3D(x=min_x, y=min_y, z=height_feet),   # 4: bottom-left
            Vertex3D(x=max_x, y=min_y, z=height_feet),   # 5: bottom-right
            Vertex3D(x=max_x, y=max_y, z=height_feet),   # 6: top-right
            Vertex3D(x=min_x, y=max_y, z=height_feet),   # 7: top-left
        ]
        
        # Create 12 triangular faces (6 quads = 12 triangles)
        # All faces should have counter-clockwise winding when viewed from outside
        faces = [
            # Floor (triangulated) - viewed from below (negative Z)
            Face(indices=[0, 2, 1]),  # Triangle 1 (counter-clockwise from below)
            Face(indices=[0, 3, 2]),  # Triangle 2 (counter-clockwise from below)
            
            # Ceiling (triangulated) - viewed from above (positive Z)
            Face(indices=[4, 5, 6]),  # Triangle 1 (counter-clockwise from above)
            Face(indices=[4, 6, 7]),  # Triangle 2 (counter-clockwise from above)
            
            # Wall 1: Bottom wall (y = min_y) - viewed from negative Y
            Face(indices=[0, 1, 5]),  # Triangle 1 (counter-clockwise from outside)
            Face(indices=[0, 5, 4]),  # Triangle 2 (counter-clockwise from outside)
            
            # Wall 2: Right wall (x = max_x) - viewed from positive X
            Face(indices=[1, 2, 6]),  # Triangle 1 (counter-clockwise from outside)
            Face(indices=[1, 6, 5]),  # Triangle 2 (counter-clockwise from outside)
            
            # Wall 3: Top wall (y = max_y) - viewed from positive Y
            Face(indices=[2, 3, 7]),  # Triangle 1 (counter-clockwise from outside)
            Face(indices=[2, 7, 6]),  # Triangle 2 (counter-clockwise from outside)
            
            # Wall 4: Left wall (x = min_x) - viewed from negative X
            Face(indices=[3, 0, 4]),  # Triangle 1 (counter-clockwise from outside)
            Face(indices=[3, 4, 7]),  # Triangle 2 (counter-clockwise from outside)
        ]
        
        return vertices, faces
    
    def _build_3d_room_from_polygon(self,
                                   room_polygon: List[Tuple[float, float]],
                                   height_feet: float) -> Tuple[List[Vertex3D], List[Face]]:
        """
        Build 3D room mesh from actual polygon coordinates.
        
        Args:
            room_polygon: List of (x, y) coordinates defining room shape
            height_feet: Room height in feet
            
        Returns:
            Tuple of (vertices, faces) for the 3D room mesh
        """
        vertices = []
        faces = []
        
        # Ensure polygon is closed (first and last points are the same)
        if room_polygon[0] != room_polygon[-1]:
            room_polygon = room_polygon + [room_polygon[0]]
        
        num_points = len(room_polygon) - 1  # Exclude the closing point
        
        # Create bottom vertices (floor level)
        bottom_vertices = []
        for x, y in room_polygon[:-1]:  # Exclude the closing point
            vertices.append(Vertex3D(x=x, y=y, z=0.0))
            bottom_vertices.append(len(vertices) - 1)
        
        # Create top vertices (ceiling level)
        top_vertices = []
        for x, y in room_polygon[:-1]:  # Exclude the closing point
            vertices.append(Vertex3D(x=x, y=y, z=height_feet))
            top_vertices.append(len(vertices) - 1)
        
        # Create floor faces (triangulate the polygon)
        floor_faces = self._triangulate_polygon(bottom_vertices)
        faces.extend(floor_faces)
        
        # Create ceiling faces (triangulate the polygon)
        ceiling_faces = self._triangulate_polygon(top_vertices)
        faces.extend(ceiling_faces)
        
        # Create wall faces (connect bottom to top)
        for i in range(num_points):
            next_i = (i + 1) % num_points
            
            # Create two triangles for each wall segment
            # Triangle 1: bottom_i, top_i, bottom_next_i
            faces.append(Face(indices=[
                bottom_vertices[i],
                top_vertices[i],
                bottom_vertices[next_i]
            ]))
            
            # Triangle 2: top_i, top_next_i, bottom_next_i
            faces.append(Face(indices=[
                top_vertices[i],
                top_vertices[next_i],
                bottom_vertices[next_i]
            ]))
        
        return vertices, faces
    
    def _triangulate_polygon(self, vertex_indices: List[int]) -> List[Face]:
        """
        Triangulate a polygon using ear clipping algorithm.
        
        Args:
            vertex_indices: List of vertex indices forming the polygon
            
        Returns:
            List of triangular faces
        """
        if len(vertex_indices) < 3:
            return []
        
        if len(vertex_indices) == 3:
            return [Face(indices=vertex_indices)]
        
        # Simple triangulation for convex polygons
        # For complex polygons, you'd want a more sophisticated algorithm
        faces = []
        for i in range(1, len(vertex_indices) - 1):
            faces.append(Face(indices=[
                vertex_indices[0],
                vertex_indices[i],
                vertex_indices[i + 1]
            ]))
        
        return faces
    
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
        
        # Check vertex count (should be 8 for 3D room box: 4 bottom + 4 top)
        if len(room_mesh.vertices) != 8:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Expected 8 vertices for 3D room, got {len(room_mesh.vertices)}")
        
        # Check face count (should be 12 triangles: 6 quads = 12 triangles)
        if len(room_mesh.faces) != 12:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Expected 12 faces for 3D room, got {len(room_mesh.faces)}")
        
        # Check for valid face indices
        for i, face in enumerate(room_mesh.faces):
            if len(face.indices) != 3:
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"Face {i} has {len(face.indices)} vertices, expected 3")
            
            # Check that indices are within bounds
            for vertex_idx in face.indices:
                if vertex_idx < 0 or vertex_idx >= len(room_mesh.vertices):
                    validation_result["is_valid"] = False
                    validation_result["errors"].append(f"Face {i} has invalid vertex index {vertex_idx}")
        
        # Check for valid vertex coordinates
        for i, vertex in enumerate(room_mesh.vertices):
            if not isinstance(vertex.x, (int, float)) or not isinstance(vertex.y, (int, float)) or not isinstance(vertex.z, (int, float)):
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"Vertex {i} has invalid coordinates: {vertex}")
        
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
