#!/usr/bin/env python3
"""
3D Model Visualization using Matplotlib
This script provides interactive 3D visualization of generated models.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.patches as patches
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.test_room_generator import TestRoomGenerator
from services.test_wall_generator import TestWallGenerator
from models.data_structures import Room3D, Wall3D, ScaledCoordinates

class Model3DVisualizer:
    def __init__(self):
        self.fig = None
        self.ax = None
        self.room_generator = TestRoomGenerator()
        self.wall_generator = TestWallGenerator()
        
    def create_3d_plot(self):
        """Create a new 3D plot"""
        self.fig = plt.figure(figsize=(12, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Set labels and title
        self.ax.set_xlabel('X (feet)')
        self.ax.set_ylabel('Y (feet)')
        self.ax.set_zlabel('Z (feet)')
        self.ax.set_title('3D Building Model')
        
        # Set equal aspect ratio
        self.ax.set_box_aspect([1, 1, 1])
        
        return self.ax
    
    def draw_room_3d(self, room: Room3D, color: str = 'lightblue', alpha: float = 0.6):
        """Draw a room in 3D"""
        if not hasattr(room, 'mesh') or not room.mesh:
            # Create simple box if no mesh
            self.draw_room_box(room, color, alpha)
        else:
            # Draw actual mesh
            self.draw_mesh_3d(room.mesh, color, alpha)
    
    def draw_room_box(self, room: Room3D, color: str = 'lightblue', alpha: float = 0.6):
        """Draw a simple room box"""
        # Create vertices for a box
        x, y, z = 0, 0, 0
        w, l, h = room.width_feet, room.length_feet, room.height_feet
        
        vertices = np.array([
            [x, y, z],           # 0: bottom front left
            [x + w, y, z],       # 1: bottom front right
            [x + w, y + l, z],   # 2: bottom back right
            [x, y + l, z],       # 3: bottom back left
            [x, y, z + h],       # 4: top front left
            [x + w, y, z + h],   # 5: top front right
            [x + w, y + l, z + h], # 6: top back right
            [x, y + l, z + h]    # 7: top back left
        ])
        
        # Define faces (triangles for each face)
        faces = [
            # Bottom face
            [vertices[0], vertices[1], vertices[2]],
            [vertices[0], vertices[2], vertices[3]],
            # Top face
            [vertices[4], vertices[6], vertices[5]],
            [vertices[4], vertices[7], vertices[6]],
            # Front face
            [vertices[0], vertices[4], vertices[5]],
            [vertices[0], vertices[5], vertices[1]],
            # Back face
            [vertices[3], vertices[2], vertices[6]],
            [vertices[3], vertices[6], vertices[7]],
            # Left face
            [vertices[0], vertices[3], vertices[7]],
            [vertices[0], vertices[7], vertices[4]],
            # Right face
            [vertices[1], vertices[5], vertices[6]],
            [vertices[1], vertices[6], vertices[2]]
        ]
        
        # Create 3D polygon collection
        poly3d = Poly3DCollection(faces, alpha=alpha, facecolor=color, edgecolor='black', linewidth=0.5)
        self.ax.add_collection3d(poly3d)
        
        # Add room label
        self.ax.text(w/2, l/2, h/2, room.name, fontsize=8, ha='center', va='center')
    
    def draw_wall_3d(self, wall: Wall3D, color: str = 'gray', alpha: float = 0.8):
        """Draw a wall in 3D"""
        if not hasattr(wall, 'mesh') or not wall.mesh:
            # Create simple wall if no mesh
            self.draw_wall_box(wall, color, alpha)
        else:
            # Draw actual mesh
            self.draw_mesh_3d(wall.mesh, color, alpha)
    
    def draw_wall_box(self, wall: Wall3D, color: str = 'gray', alpha: float = 0.8):
        """Draw a simple wall box"""
        # Calculate wall dimensions
        dx = wall.end_x - wall.start_x
        dy = wall.end_y - wall.start_y
        length = np.sqrt(dx**2 + dy**2)
        
        # Create wall vertices
        x, y, z = wall.start_x, wall.start_y, 0
        w, h = wall.thickness_feet, wall.height_feet
        
        # Create a box for the wall
        vertices = np.array([
            [x, y, z],           # 0: bottom front left
            [x + dx, y + dy, z], # 1: bottom front right
            [x + dx, y + dy, z + h], # 2: top front right
            [x, y, z + h],       # 3: top front left
        ])
        
        # Add thickness perpendicular to wall direction
        # Calculate perpendicular vector
        if abs(dx) > abs(dy):
            perp_x, perp_y = 0, w/2
        else:
            perp_x, perp_y = w/2, 0
        
        # Add thickness vertices
        vertices = np.vstack([
            vertices,
            vertices + [perp_x, perp_y, 0],
            vertices + [perp_x, perp_y, h]
        ])
        
        # Define faces (simplified)
        faces = [
            # Main wall faces
            [vertices[0], vertices[1], vertices[2], vertices[3]],
            [vertices[4], vertices[5], vertices[6], vertices[7]],
            # Side faces
            [vertices[0], vertices[4], vertices[7], vertices[3]],
            [vertices[1], vertices[5], vertices[6], vertices[2]]
        ]
        
        # Create 3D polygon collection
        poly3d = Poly3DCollection(faces, alpha=alpha, facecolor=color, edgecolor='black', linewidth=0.5)
        self.ax.add_collection3d(poly3d)
    
    def draw_mesh_3d(self, mesh, color: str = 'blue', alpha: float = 0.6):
        """Draw a 3D mesh"""
        if not hasattr(mesh, 'vertices') or not hasattr(mesh, 'faces'):
            return
        
        vertices = np.array(mesh.vertices)
        faces = mesh.faces
        
        # Convert faces to vertex lists
        face_vertices = []
        for face in faces:
            if hasattr(face, 'indices'):
                face_verts = [vertices[i] for i in face.indices]
                face_vertices.append(face_verts)
            elif hasattr(face, 'vertex_indices'):
                face_verts = [vertices[i] for i in face.vertex_indices]
                face_vertices.append(face_verts)
        
        if face_vertices:
            poly3d = Poly3DCollection(face_vertices, alpha=alpha, facecolor=color, edgecolor='black', linewidth=0.5)
            self.ax.add_collection3d(poly3d)
    
    def draw_floor_plan_2d(self, rooms: List[Room3D], walls: List[Wall3D]):
        """Draw a 2D floor plan view"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Draw rooms
        for room in rooms:
            rect = patches.Rectangle((0, 0), room.width_feet, room.length_feet, 
                                   linewidth=2, edgecolor='blue', facecolor='lightblue', alpha=0.6)
            ax.add_patch(rect)
            ax.text(room.width_feet/2, room.length_feet/2, room.name, 
                   ha='center', va='center', fontsize=10, fontweight='bold')
        
        # Draw walls
        for wall in walls:
            ax.plot([wall.start_x, wall.end_x], [wall.start_y, wall.end_y], 
                   'k-', linewidth=3, alpha=0.8)
        
        ax.set_xlabel('X (feet)')
        ax.set_ylabel('Y (feet)')
        ax.set_title('2D Floor Plan')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        return fig, ax
    
    def visualize_test_case(self, test_case: Dict[str, Any]):
        """Visualize a complete test case"""
        print(f"🎨 Creating 3D visualization for: {test_case['name']}")
        
        # Create mock data
        scaled_coords = self.create_mock_scaled_coordinates(test_case)
        
        # Generate 3D models
        rooms_3d = self.room_generator.generate_room_meshes(scaled_coords)
        walls_3d = self.wall_generator.generate_wall_meshes(scaled_coords)
        
        # Create 3D plot
        ax = self.create_3d_plot()
        
        # Draw rooms
        for room in rooms_3d:
            self.draw_room_3d(room, color='lightblue', alpha=0.6)
        
        # Draw walls
        for wall in walls_3d:
            self.draw_wall_3d(wall, color='gray', alpha=0.8)
        
        # Set plot limits
        max_x = max(max(r.width_feet for r in rooms_3d), max(w.end_x for w in walls_3d))
        max_y = max(max(r.length_feet for r in rooms_3d), max(w.end_y for w in walls_3d))
        max_z = max(max(r.height_feet for r in rooms_3d), max(w.height_feet for w in walls_3d))
        
        self.ax.set_xlim(0, max_x)
        self.ax.set_ylim(0, max_y)
        self.ax.set_zlim(0, max_z)
        
        # Create 2D floor plan
        fig_2d, ax_2d = self.draw_floor_plan_2d(rooms_3d, walls_3d)
        
        # Save plots
        output_dir = Path("output/local_testing")
        output_dir.mkdir(exist_ok=True)
        
        # Save 3D plot
        plot_3d_path = output_dir / f"{test_case['name']}_3d_view.png"
        self.fig.savefig(plot_3d_path, dpi=300, bbox_inches='tight')
        print(f"   ✅ Saved 3D view: {plot_3d_path}")
        
        # Save 2D floor plan
        plot_2d_path = output_dir / f"{test_case['name']}_floor_plan.png"
        fig_2d.savefig(plot_2d_path, dpi=300, bbox_inches='tight')
        print(f"   ✅ Saved floor plan: {plot_2d_path}")
        
        # Show plots
        plt.show()
        
        return {
            '3d_plot': plot_3d_path,
            '2d_plan': plot_2d_path
        }
    
    def create_mock_scaled_coordinates(self, test_case: Dict[str, Any]) -> ScaledCoordinates:
        """Create mock scaled coordinates for testing"""
        rooms = []
        walls = []
        
        # Create scaled room data
        for i, room_info in enumerate(test_case["rooms"]):
            room = Room3D(
                id=f"room_{i}",
                name=room_info["name"],
                width_feet=room_info["width"],
                length_feet=room_info["length"],
                height_feet=room_info["height"],
                elevation_feet=0,
                area_sqft=room_info["width"] * room_info["length"],
                room_type="room"
            )
            rooms.append(room)
        
        # Create scaled wall data
        for i, wall_info in enumerate(test_case["walls"]):
            wall = Wall3D(
                id=f"wall_{i}",
                start_x=wall_info["start"][0],
                start_y=wall_info["start"][1],
                end_x=wall_info["end"][0],
                end_y=wall_info["end"][1],
                height_feet=wall_info["height"],
                thickness_feet=wall_info["thickness"]
            )
            walls.append(wall)
        
        return ScaledCoordinates(
            rooms_feet=rooms,
            walls_feet=walls,
            doors_feet=[],
            windows_feet=[],
            room_polygons_feet=[],
            scale_factor=1.0,
            reference_room_id="room_0",
            reference_dimension=20.0
        )

def main():
    """Main function for testing visualization"""
    # Test cases
    test_cases = [
        {
            "name": "simple_house",
            "description": "Simple rectangular house with 2 rooms",
            "rooms": [
                {"name": "Living Room", "width": 20, "length": 15, "height": 10},
                {"name": "Bedroom", "width": 12, "length": 10, "height": 10}
            ],
            "walls": [
                {"start": (0, 0), "end": (32, 0), "height": 10, "thickness": 0.5},
                {"start": (32, 0), "end": (32, 15), "height": 10, "thickness": 0.5},
                {"start": (32, 15), "end": (0, 15), "height": 10, "thickness": 0.5},
                {"start": (0, 15), "end": (0, 0), "height": 10, "thickness": 0.5},
                {"start": (20, 0), "end": (20, 15), "height": 10, "thickness": 0.5}
            ]
        }
    ]
    
    # Create visualizer
    visualizer = Model3DVisualizer()
    
    # Visualize each test case
    for test_case in test_cases:
        try:
            result = visualizer.visualize_test_case(test_case)
            print(f"🎉 Visualization completed for {test_case['name']}")
        except Exception as e:
            print(f"❌ Visualization failed for {test_case['name']}: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
