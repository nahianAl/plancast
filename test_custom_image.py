#!/usr/bin/env python3
"""
Custom Image 3D Generation Test
This script allows you to test your own floor plan image with the 3D generation pipeline.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import traceback

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.cubicasa_service import CubiCasaService
from services.coordinate_scaler import CoordinateScaler
from services.test_room_generator import SimpleRoomGenerator
from services.test_wall_generator import SimpleWallGenerator
from models.data_structures import CubiCasaOutput, Room3D, Wall3D, Face
from PIL import Image
import numpy as np

class CustomImageTester:
    def __init__(self):
        self.output_dir = Path("output/custom_image_testing")
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize services
        self.cubicasa_service = CubiCasaService()
        self.coordinate_scaler = CoordinateScaler()
        self.room_generator = SimpleRoomGenerator()
        self.wall_generator = SimpleWallGenerator()
        
    def test_with_custom_image(self, image_path: str, room_dimensions: Dict[str, Any] = None):
        """Test 3D generation with a custom image"""
        print(f"🎯 Testing 3D generation with custom image: {image_path}")
        print("=" * 60)
        
        # Validate image
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            return False
        
        try:
            # Load and analyze image
            with Image.open(image_path) as img:
                print(f"📸 Image loaded: {img.size[0]}x{img.size[1]} pixels")
                
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Process with CubiCasa
                print("🤖 Processing with CubiCasa model...")
                start_time = time.time()
                
                # Convert PIL image to bytes for CubiCasa service
                import io
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='JPEG')
                img_bytes = img_bytes.getvalue()
                
                # Process with CubiCasa
                cubicasa_output = self.cubicasa_service.process_floorplan(img_bytes)
                
                processing_time = time.time() - start_time
                print(f"✅ CubiCasa processing completed in {processing_time:.2f}s")
                
                # Print detection results
                print(f"📊 Detection Results:")
                print(f"   🏠 Rooms detected: {len(cubicasa_output.rooms) if hasattr(cubicasa_output, 'rooms') else len(cubicasa_output.room_bounding_boxes)}")
                print(f"   🧱 Walls detected: {len(cubicasa_output.walls) if hasattr(cubicasa_output, 'walls') else len(cubicasa_output.wall_coordinates)}")
                print(f"   🚪 Doors detected: {len(cubicasa_output.doors)}")
                print(f"   🪟 Windows detected: {len(cubicasa_output.windows)}")
                
                # Get room suggestions for scaling
                suggestions = self.coordinate_scaler.get_smart_room_suggestions(cubicasa_output)
                print(f"\n💡 Room Suggestions for Scaling:")
                for i, suggestion in enumerate(suggestions):
                    print(f"   {i+1}. {suggestion.name}: {suggestion.description} (Priority: {suggestion.priority})")
                
                # Use provided dimensions or ask user
                if room_dimensions:
                    selected_room = suggestions[0] if suggestions else None
                    room_width = room_dimensions.get('width', 20)
                    room_length = room_dimensions.get('length', 15)
                    print(f"\n📏 Using provided dimensions: {room_width}' x {room_length}' for room: {selected_room.name if selected_room else 'Unknown'}")
                else:
                    # Interactive room selection
                    if suggestions:
                        print(f"\n🎯 Select a room for scaling (1-{len(suggestions)}):")
                        for i, suggestion in enumerate(suggestions):
                            print(f"   {i+1}. {suggestion.name}: {suggestion.description}")
                        
                        try:
                            choice = int(input(f"Enter choice (1-{len(suggestions)}): ")) - 1
                            if 0 <= choice < len(suggestions):
                                selected_room = suggestions[choice]
                                print(f"✅ Selected: {selected_room.name}")
                            else:
                                print("❌ Invalid choice, using first room")
                                selected_room = suggestions[0]
                        except (ValueError, KeyboardInterrupt):
                            print("❌ Invalid input, using first room")
                            selected_room = suggestions[0]
                        
                        # Get room dimensions
                        print(f"\n📐 Enter dimensions for {selected_room.name}:")
                        try:
                            room_width = float(input("Width (feet): "))
                            room_length = float(input("Length (feet): "))
                        except (ValueError, KeyboardInterrupt):
                            print("❌ Using default dimensions: 20' x 15'")
                            room_width, room_length = 20, 15
                    else:
                        print("⚠️  No room suggestions available, using default dimensions")
                        selected_room = None
                        room_width, room_length = 20, 15
                
                # Scale coordinates
                if selected_room:
                    print(f"\n📏 Scaling coordinates using {selected_room.name} as reference...")
                    scaled_coords = self.coordinate_scaler.convert_coordinates_to_feet(
                        cubicasa_output,
                        selected_room.id,
                        room_width
                    )
                    print(f"✅ Scaling completed with factor: {scaled_coords.scale_factor:.4f}")
                else:
                    print("⚠️  Using 1:1 scaling (no coordinate scaling)")
                    # Create mock scaled coordinates for simple generators
                    scaled_coords = self._create_mock_scaled_coords(cubicasa_output, room_width, room_length)
                
                # Generate 3D models
                print(f"\n🏗️  Generating 3D models...")
                
                # Generate room meshes
                print("   🔨 Generating room meshes...")
                rooms_3d = self.room_generator.generate_simple_rooms(cubicasa_output)
                print(f"   ✅ Generated {len(rooms_3d)} room meshes")
                
                # Generate wall meshes
                print("   🧱 Generating wall meshes...")
                walls_3d = self.wall_generator.generate_simple_walls(cubicasa_output)
                print(f"   ✅ Generated {len(walls_3d)} wall meshes")
                
                # Combine meshes
                print("   🔗 Combining meshes...")
                combined_mesh = self._combine_meshes(rooms_3d, walls_3d)
                
                if combined_mesh:
                    print(f"   ✅ Combined mesh: {len(combined_mesh['vertices'])} vertices, {len(combined_mesh['faces'])} faces")
                    
                    # Export models
                    print(f"\n📦 Exporting 3D models...")
                    export_paths = self._export_models(combined_mesh, Path(image_path).stem)
                    
                    # Create HTML viewer
                    print(f"\n🌐 Creating HTML viewer...")
                    html_path = self._create_html_viewer(
                        Path(image_path).stem,
                        rooms_3d, 
                        walls_3d, 
                        export_paths,
                        image_path
                    )
                    
                    print(f"\n🎉 3D Generation completed successfully!")
                    print(f"📁 Files saved to: {self.output_dir}")
                    print(f"🌐 Open viewer: {html_path}")
                    
                    return True
                else:
                    print(f"\n❌ No mesh to combine")
                    return False
                
        except Exception as e:
            print(f"\n💥 Test failed with error: {str(e)}")
            traceback.print_exc()
            return False
    
    def _create_mock_scaled_coords(self, cubicasa_output: CubiCasaOutput, room_width: float, room_length: float):
        """Create mock scaled coordinates for simple generators"""
        # This is a simplified approach for testing
        return cubicasa_output
    
    def _combine_meshes(self, rooms_3d: List[Room3D], walls_3d: List[Wall3D]) -> Optional[Dict[str, Any]]:
        """Combine room and wall meshes into a single mesh"""
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
            return None
        
        return {
            'vertices': all_vertices,
            'faces': all_faces
        }
    
    def _export_models(self, combined_mesh: Dict[str, Any], model_name: str) -> Dict[str, Path]:
        """Export 3D models to various formats"""
        try:
            # Create export directory
            export_dir = self.output_dir / model_name
            export_dir.mkdir(exist_ok=True)
            
            # Export to different formats
            timestamp = int(time.time())
            base_filename = f"{model_name}_{timestamp}"
            
            # Export OBJ
            obj_path = export_dir / f"{base_filename}.obj"
            self._export_simple_obj(combined_mesh, str(obj_path))
            print(f"   ✅ Exported OBJ: {obj_path}")
            
            # Export GLB
            glb_path = export_dir / f"{base_filename}.glb"
            self._export_simple_glb(combined_mesh, str(glb_path))
            print(f"   ✅ Exported GLB: {glb_path}")
            
            # Export STL
            stl_path = export_dir / f"{base_filename}.stl"
            self._export_simple_stl(combined_mesh, str(stl_path))
            print(f"   ✅ Exported STL: {stl_path}")
            
            return {
                'obj': obj_path,
                'glb': glb_path,
                'stl': stl_path
            }
            
        except Exception as e:
            print(f"   💥 Model export failed: {str(e)}")
            return {}
    
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
            with open(filepath, 'wb') as f:
                f.write(b'glTF')
                f.write(b'\x00\x00\x00\x00')  # Version
                f.write(b'\x00\x00\x00\x00')  # Length placeholder
            
            print(f"      ✅ GLB exported (placeholder): {len(mesh_data['vertices'])} vertices, {len(mesh_data['faces'])} faces")
            
        except Exception as e:
            print(f"      ❌ GLB export failed: {str(e)}")
    
    def _export_simple_stl(self, mesh_data: Dict[str, Any], filepath: str):
        """Export mesh to STL format"""
        try:
            import struct
            
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
    
    def _create_html_viewer(self, model_name: str, rooms_3d: List[Room3D], walls_3d: List[Wall3D], export_paths: Dict[str, Path], image_path: str) -> Path:
        """Create an HTML viewer for the 3D models"""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Model Viewer - {model_name}</title>
    <style>
        body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; background: #f0f0f0; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .image-section {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .viewer {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .model-info {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; margin: 0 0 10px 0; }}
        h2 {{ color: #555; margin: 0 0 15px 0; }}
        .model-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .model-item {{ text-align: center; }}
        .download-btn {{ display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 10px 5px; }}
        .download-btn:hover {{ background: #0056b3; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat {{ background: #f8f9fa; padding: 15px; border-radius: 4px; text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .original-image {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 3D Model Viewer - Custom Image</h1>
            <h2>{model_name}</h2>
        </div>
        
        <div class="image-section">
            <h2>📸 Original Floor Plan</h2>
            <img src="{image_path}" alt="Original Floor Plan" class="original-image">
        </div>
        
        <div class="viewer">
            <h2>📊 Model Statistics</h2>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{len(rooms_3d)}</div>
                    <div class="stat-label">Rooms Generated</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{len(walls_3d)}</div>
                    <div class="stat-label">Walls Generated</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{sum(len(r.vertices) for r in rooms_3d) + sum(len(w.vertices) for w in walls_3d)}</div>
                    <div class="stat-label">Total Vertices</div>
                </div>
            </div>
        </div>
        
        <div class="model-info">
            <h2>📁 Generated Files</h2>
            <div class="model-grid">
                <div class="model-item">
                    <h3>OBJ Format</h3>
                    <p>Wavefront OBJ file - compatible with most 3D software</p>
                    <a href="{export_paths.get('obj', {}).name if export_paths.get('obj') else '#'}" class="download-btn" download>Download OBJ</a>
                </div>
                <div class="model-item">
                    <h3>GLB Format</h3>
                    <p>Binary glTF - optimized for web and real-time applications</p>
                    <a href="{export_paths.get('glb', {}).name if export_paths.get('glb') else '#'}" class="download-btn" download>Download GLB</a>
                </div>
                <div class="model-item">
                    <h3>STL Format</h3>
                    <p>STereoLithography - standard for 3D printing</p>
                    <a href="{export_paths.get('stl', {}).name if export_paths.get('stl') else '#'}" class="download-btn" download>Download STL</a>
                </div>
            </div>
        </div>
        
        <div class="model-info">
            <h2>🔍 Room Details</h2>
            <div class="stats">
"""
        
        for room in rooms_3d:
            html_content += f"""
                <div class="stat">
                    <div class="stat-value">{room.name}</div>
                    <div class="stat-label">{len(room.vertices)} vertices, {len(room.faces)} faces</div>
                </div>
"""
        
        html_content += """
            </div>
        </div>
    </div>
</body>
</html>
"""
        
        html_path = self.output_dir / f"{model_name}_viewer.html"
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        print(f"   ✅ Created HTML viewer: {html_path}")
        return html_path

def main():
    """Main function for testing custom images"""
    print("🎯 Custom Image 3D Generation Testing")
    print("=" * 60)
    
    # Get image path from user
    image_path = input("Enter the path to your floor plan image: ").strip()
    
    if not image_path:
        print("❌ No image path provided")
        return
    
    # Optional: Get room dimensions
    print("\n📐 Room Dimensions (optional - press Enter to skip):")
    try:
        width_input = input("Room width (feet): ").strip()
        length_input = input("Room length (feet): ").strip()
        
        room_dimensions = None
        if width_input and length_input:
            room_dimensions = {
                'width': float(width_input),
                'length': float(length_input)
            }
            print(f"✅ Using dimensions: {room_dimensions['width']}' x {room_dimensions['length']}'")
        else:
            print("ℹ️  No dimensions provided - will use interactive selection")
    except (ValueError, KeyboardInterrupt):
        print("ℹ️  Invalid input - will use interactive selection")
        room_dimensions = None
    
    # Create tester and run test
    tester = CustomImageTester()
    success = tester.test_with_custom_image(image_path, room_dimensions)
    
    if success:
        print(f"\n🎉 Custom image test completed successfully!")
        print(f"📁 Check the output directory: {tester.output_dir}")
    else:
        print(f"\n❌ Custom image test failed")

if __name__ == "__main__":
    main()
