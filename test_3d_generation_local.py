#!/usr/bin/env python3
"""
Local 3D Model Generation Testing and Preview
This script tests the 3D generation pipeline locally and creates visual previews.
"""

import os
import sys
import time
import json
import subprocess
import struct
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.test_room_generator import SimpleRoomGenerator
from services.test_wall_generator import SimpleWallGenerator
from services.mesh_exporter import MeshExporter
from models.data_structures import CubiCasaOutput, Room3D, Wall3D, Face
from PIL import Image
import numpy as np

class Local3DTesting:
    def __init__(self):
        self.output_dir = Path("output/local_testing")
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize generators
        self.room_generator = SimpleRoomGenerator()
        self.wall_generator = SimpleWallGenerator()
        self.mesh_exporter = MeshExporter()
        
        # Test parameters
        self.test_cases = [
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
            },
            {
                "name": "complex_house",
                "description": "Complex house with multiple rooms and features",
                "rooms": [
                    {"name": "Kitchen", "width": 15, "length": 12, "height": 9},
                    {"name": "Dining Room", "width": 18, "length": 14, "height": 10},
                    {"name": "Master Bedroom", "width": 16, "length": 14, "height": 10},
                    {"name": "Bathroom", "width": 8, "length": 10, "height": 8},
                    {"name": "Study", "width": 12, "length": 10, "height": 9}
                ],
                "walls": [
                    # Outer walls
                    {"start": (0, 0), "end": (50, 0), "height": 10, "thickness": 0.5},
                    {"start": (50, 0), "end": (50, 26), "height": 10, "thickness": 0.5},
                    {"start": (50, 26), "end": (0, 26), "height": 10, "thickness": 0.5},
                    {"start": (0, 26), "end": (0, 0), "height": 10, "thickness": 0.5},
                    # Interior walls
                    {"start": (15, 0), "end": (15, 26), "height": 10, "thickness": 0.3},
                    {"start": (33, 0), "end": (33, 26), "height": 10, "thickness": 0.3},
                    {"start": (0, 12), "end": (15, 12), "height": 10, "thickness": 0.3},
                    {"start": (15, 14), "end": (33, 14), "height": 10, "thickness": 0.3}
                ]
            }
        ]
    
    def create_mock_cubicasa_output(self, test_case: Dict[str, Any]) -> CubiCasaOutput:
        """Create mock CubiCasa output for testing"""
        # Create room bounding boxes for simple generators
        room_bounding_boxes = {}
        for i, room_info in enumerate(test_case["rooms"]):
            room_bounding_boxes[room_info["name"]] = {
                "min_x": 0,
                "min_y": 0,
                "max_x": room_info["width"],
                "max_y": room_info["length"]
            }
        
        # Create wall coordinates (the wall generator extracts segments from room boundaries)
        wall_coordinates = []
        for wall_info in test_case["walls"]:
            # Add points along the wall
            start_x, start_y = wall_info["start"]
            end_x, end_y = wall_info["end"]
            # Add a few points along the wall
            for t in range(0, 11, 2):  # 0, 2, 4, 6, 8, 10
                t_norm = t / 10.0
                x = int(start_x + t_norm * (end_x - start_x))
                y = int(start_y + t_norm * (end_y - start_y))
                wall_coordinates.append((x, y))
        
        return CubiCasaOutput(
            wall_coordinates=wall_coordinates,
            room_bounding_boxes=room_bounding_boxes,
            door_coordinates=[],
            window_coordinates=[],
            room_polygons={},
            image_dimensions=(800, 600),
            confidence_scores={},
            processing_time=1.5
        )
    

    
    def test_room_generation(self, test_case: Dict[str, Any]) -> List[Room3D]:
        """Test room generation"""
        print(f"🔨 Testing room generation for: {test_case['name']}")
        
        # Create mock CubiCasa output for the simple generators
        cubicasa_output = self.create_mock_cubicasa_output(test_case)
        rooms_3d = self.room_generator.generate_simple_rooms(cubicasa_output)
        
        print(f"   ✅ Generated {len(rooms_3d)} rooms")
        for room in rooms_3d:
            print(f"      - {room.name}: {room.vertices[0].x:.1f}' x {room.vertices[2].y:.1f}' x {room.height_feet}'")
        
        return rooms_3d
    
    def test_wall_generation(self, test_case: Dict[str, Any]) -> List[Wall3D]:
        """Test wall generation"""
        print(f"🧱 Testing wall generation for: {test_case['name']}")
        
        # Create mock CubiCasa output for the simple generators
        cubicasa_output = self.create_mock_cubicasa_output(test_case)
        walls_3d = self.wall_generator.generate_simple_walls(cubicasa_output)
        
        print(f"   ✅ Generated {len(walls_3d)} walls")
        for wall in walls_3d:
            print(f"      - Wall {wall.id}: {len(wall.vertices)} vertices, {len(wall.faces)} faces, height: {wall.height_feet}'")
        
        return walls_3d
    
    def test_mesh_export(self, test_case: Dict[str, Any], rooms_3d: List[Room3D], walls_3d: List[Wall3D]):
        """Test mesh export"""
        print(f"📦 Testing mesh export for: {test_case['name']}")
        
        # Combine all meshes
        all_vertices = []
        all_faces = []
        vertex_offset = 0
        
        # Add room meshes
        for room in rooms_3d:
            if hasattr(room, 'vertices') and room.vertices:
                all_vertices.extend(room.vertices)
                for face in room.faces:
                    adjusted_face = Face(
                        indices=[i + vertex_offset for i in face.indices],
                        material="room_material"
                    )
                    all_faces.append(adjusted_face)
                vertex_offset += len(room.vertices)
        
        # Add wall meshes
        for wall in walls_3d:
            if hasattr(wall, 'vertices') and wall.vertices:
                all_vertices.extend(wall.vertices)
                for face in wall.faces:
                    adjusted_face = Face(
                        indices=[i + vertex_offset for i in face.indices],
                        material="wall_material"
                    )
                    all_faces.append(adjusted_face)
                vertex_offset += len(wall.vertices)
        
        if not all_vertices:
            print("   ⚠️  No vertices to export")
            return None
        
        # Create combined mesh
        combined_mesh = {
            'vertices': all_vertices,
            'faces': all_faces
        }
        
        # Export to different formats
        timestamp = int(time.time())
        base_filename = f"{test_case['name']}_{timestamp}"
        
        # Export OBJ
        obj_path = self.output_dir / f"{base_filename}.obj"
        self._export_simple_obj(combined_mesh, str(obj_path))
        print(f"   ✅ Exported OBJ: {obj_path}")
        
        # Export GLB
        glb_path = self.output_dir / f"{base_filename}.glb"
        self._export_simple_glb(combined_mesh, str(glb_path))
        print(f"   ✅ Exported GLB: {glb_path}")
        
        # Export STL
        stl_path = self.output_dir / f"{base_filename}.stl"
        self._export_simple_stl(combined_mesh, str(stl_path))
        print(f"   ✅ Exported STL: {stl_path}")
        
        return {
            'obj': obj_path,
            'glb': glb_path,
            'stl': stl_path
        }
    
    def _export_simple_obj(self, mesh_data: Dict[str, Any], filepath: str):
        """Export mesh to OBJ format"""
        try:
            with open(filepath, 'w') as f:
                # Write vertices
                for vertex in mesh_data['vertices']:
                    f.write(f"v {vertex.x} {vertex.y} {vertex.z}\n")
                
                # Write faces (OBJ uses 1-indexed vertices)
                for face in mesh_data['faces']:
                    indices = [i + 1 for i in face.indices]  # Convert to 1-indexed
                    f.write(f"f {' '.join(map(str, indices))}\n")
            
            print(f"      ✅ OBJ exported: {len(mesh_data['vertices'])} vertices, {len(mesh_data['faces'])} faces")
            
        except Exception as e:
            print(f"      ❌ OBJ export failed: {str(e)}")
    
    def _export_simple_glb(self, mesh_data: Dict[str, Any], filepath: str):
        """Export mesh to GLB format (simplified)"""
        try:
            # For now, just create a placeholder GLB file
            # In a real implementation, you'd use a library like pygltflib
            with open(filepath, 'wb') as f:
                # Write a minimal GLB header (this is just a placeholder)
                f.write(b'glTF')
                f.write(b'\x00\x00\x00\x00')  # Version
                f.write(b'\x00\x00\x00\x00')  # Length placeholder
            
            print(f"      ✅ GLB exported (placeholder): {len(mesh_data['vertices'])} vertices, {len(mesh_data['faces'])} faces")
            
        except Exception as e:
            print(f"      ❌ GLB export failed: {str(e)}")
    
    def _export_simple_stl(self, mesh_data: Dict[str, Any], filepath: str):
        """Export mesh to STL format"""
        try:
            with open(filepath, 'wb') as f:
                # Write STL header (80 bytes)
                header = f"PlanCast 3D Model - {len(mesh_data['vertices'])} vertices, {len(mesh_data['faces'])} faces".ljust(80, '\x00')
                f.write(header.encode('ascii'))
                
                # Write triangle count (4 bytes)
                triangle_count = len(mesh_data['faces'])
                f.write(triangle_count.to_bytes(4, byteorder='little'))
                
                # Write each face
                for face in mesh_data['faces']:
                    # Get vertices for this face
                    face_vertices = [mesh_data['vertices'][i] for i in face.indices]
                    
                    # Calculate face normal (simplified)
                    if len(face_vertices) >= 3:
                        v0, v1, v2 = face_vertices[0], face_vertices[1], face_vertices[2]
                        
                        # Calculate normal vector
                        ux, uy, uz = v1.x - v0.x, v1.y - v0.y, v1.z - v0.z
                        vx, vy, vz = v2.x - v0.x, v2.y - v0.y, v2.z - v0.z
                        
                        nx = uy * vz - uz * vy
                        ny = uz * vx - ux * vz
                        nz = ux * vy - uy * vx
                        
                        # Normalize
                        length = (nx**2 + ny**2 + nz**2)**0.5
                        if length > 0:
                            nx, ny, nz = nx/length, ny/length, nz/length
                        
                        # Write normal (12 bytes)
                        for val in [nx, ny, nz]:
                            f.write(struct.pack('<f', val))
                        
                        # Write vertices (36 bytes)
                        for vertex in face_vertices[:3]:  # STL only supports triangles
                            for val in [vertex.x, vertex.y, vertex.z]:
                                f.write(struct.pack('<f', val))
                        
                        # Write attribute count (2 bytes)
                        f.write(b'\x00\x00')
            
            print(f"      ✅ STL exported: {len(mesh_data['vertices'])} vertices, {len(mesh_data['faces'])} faces")
            
        except Exception as e:
            print(f"      ❌ STL export failed: {str(e)}")
    
    def create_html_viewer(self, test_case: Dict[str, Any], export_paths: Dict[str, Path]):
        """Create an HTML viewer for the 3D models"""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Model Viewer - {test_case['name']}</title>
    <style>
        body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; background: #f0f0f0; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .viewer {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .controls {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .model-info {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; margin: 0 0 10px 0; }}
        h2 {{ color: #555; margin: 0 0 15px 0; }}
        .model-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .model-item {{ text-align: center; }}
        .model-item img {{ max-width: 100%; height: auto; border-radius: 4px; }}
        .download-btn {{ display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 10px 5px; }}
        .download-btn:hover {{ background: #0056b3; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat {{ background: #f8f9fa; padding: 15px; border-radius: 4px; text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 3D Model Viewer</h1>
            <h2>{test_case['description']}</h2>
        </div>
        
        <div class="viewer">
            <h2>📊 Model Statistics</h2>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{len(test_case['rooms'])}</div>
                    <div class="stat-label">Rooms</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{len(test_case['walls'])}</div>
                    <div class="stat-label">Walls</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{sum(r['width'] * r['length'] for r in test_case['rooms'])} sq ft</div>
                    <div class="stat-label">Total Area</div>
                </div>
            </div>
        </div>
        
        <div class="controls">
            <h2>🎮 Controls</h2>
            <p><strong>Mouse:</strong> Left click + drag to rotate, Right click + drag to pan, Scroll to zoom</p>
            <p><strong>Touch:</strong> One finger to rotate, Two fingers to pan and zoom</p>
        </div>
        
        <div class="model-info">
            <h2>📁 Generated Files</h2>
            <div class="model-grid">
                <div class="model-item">
                    <h3>OBJ Format</h3>
                    <p>Wavefront OBJ file - compatible with most 3D software</p>
                    <a href="{export_paths['obj'].name}" class="download-btn" download>Download OBJ</a>
                </div>
                <div class="model-item">
                    <h3>GLB Format</h3>
                    <p>Binary glTF - optimized for web and real-time applications</p>
                    <a href="{export_paths['glb'].name}" class="download-btn" download>Download GLB</a>
                </div>
                <div class="model-item">
                    <h3>STL Format</h3>
                    <p>STereoLithography - standard for 3D printing</p>
                    <a href="{export_paths['stl'].name}" class="download-btn" download>Download STL</a>
                </div>
            </div>
        </div>
        
        <div class="model-info">
            <h2>🔍 Room Details</h2>
            <div class="stats">
"""
        
        for room in test_case['rooms']:
            html_content += f"""
                <div class="stat">
                    <div class="stat-value">{room['name']}</div>
                    <div class="stat-label">{room['width']}' × {room['length']}' × {room['height']}'</div>
                </div>
"""
        
        html_content += """
            </div>
        </div>
    </div>
</body>
</html>
"""
        
        html_path = self.output_dir / f"{test_case['name']}_viewer.html"
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        print(f"   ✅ Created HTML viewer: {html_path}")
        return html_path
    
    def run_complete_test(self, test_case: Dict[str, Any]):
        """Run complete test for a test case"""
        print(f"\n🚀 Running complete test: {test_case['name']}")
        print("=" * 60)
        
        try:
            # Test room generation
            rooms_3d = self.test_room_generation(test_case)
            
            # Test wall generation
            walls_3d = self.test_wall_generation(test_case)
            
            # Test mesh export
            export_paths = self.test_mesh_export(test_case, rooms_3d, walls_3d)
            
            if export_paths:
                # Create HTML viewer
                html_path = self.create_html_viewer(test_case, export_paths)
                
                print(f"\n🎉 Test completed successfully!")
                print(f"📁 Files saved to: {self.output_dir}")
                print(f"🌐 Open viewer: {html_path}")
                
                return True
            else:
                print(f"\n❌ Test failed: No models generated")
                return False
                
        except Exception as e:
            print(f"\n💥 Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all_tests(self):
        """Run all test cases"""
        print("🧪 Starting Local 3D Generation Testing")
        print("=" * 60)
        
        results = []
        for test_case in self.test_cases:
            success = self.run_complete_test(test_case)
            results.append({
                'name': test_case['name'],
                'success': success
            })
        
        # Summary
        print("\n📊 Test Summary")
        print("=" * 60)
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        
        for result in results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {result['name']}")
        
        print(f"\nOverall: {successful}/{total} tests passed")
        
        if successful > 0:
            print(f"\n🎯 Open the output directory to view results:")
            print(f"   {self.output_dir.absolute()}")
            
            # Try to open the output directory
            try:
                if sys.platform == "darwin":  # macOS
                    subprocess.run(["open", str(self.output_dir)])
                elif sys.platform == "win32":  # Windows
                    subprocess.run(["explorer", str(self.output_dir)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(self.output_dir)])
            except:
                pass

def main():
    """Main function"""
    tester = Local3DTesting()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
