#!/usr/bin/env python3
"""
Real Pipeline Local Testing
This script tests the actual CubiCasa integration with real floor plan images.
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import traceback

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.cubicasa_service import CubiCasaService
from services.coordinate_scaler import CoordinateScaler
from services.test_room_generator import TestRoomGenerator
from services.test_wall_generator import TestWallGenerator
from services.mesh_exporter import MeshExporter
from models.data_structures import CubiCasaOutput, ScaledCoordinates, Room3D, Wall3D, Face
from PIL import Image
import numpy as np

class RealPipelineLocalTester:
    def __init__(self):
        self.output_dir = Path("output/real_pipeline_testing")
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize services
        self.cubicasa_service = CubiCasaService()
        self.coordinate_scaler = CoordinateScaler()
        self.room_generator = TestRoomGenerator()
        self.wall_generator = TestWallGenerator()
        self.mesh_exporter = MeshExporter()
        
        # Test images
        self.test_images = [
            {
                "name": "test_floorplan",
                "path": "test_floorplan.jpg",
                "description": "Test floor plan image"
            },
            {
                "name": "test_image",
                "path": "test_image.jpg", 
                "description": "Another test image"
            }
        ]
    
    def test_cubicasa_integration(self, image_path: str) -> Optional[CubiCasaOutput]:
        """Test CubiCasa integration with a real image"""
        print(f"🔍 Testing CubiCasa integration with: {image_path}")
        
        try:
            # Check if image exists
            if not os.path.exists(image_path):
                print(f"   ❌ Image not found: {image_path}")
                return None
            
            # Load and process image
            with Image.open(image_path) as img:
                print(f"   📸 Image loaded: {img.size[0]}x{img.size[1]} pixels")
                
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Process with CubiCasa
                print("   🤖 Processing with CubiCasa model...")
                start_time = time.time()
                
                # Convert PIL image to bytes for CubiCasa service
                import io
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='JPEG')
                img_bytes = img_bytes.getvalue()
                
                # Process with CubiCasa
                cubicasa_output = self.cubicasa_service.process_floorplan(img_bytes)
                
                processing_time = time.time() - start_time
                print(f"   ✅ CubiCasa processing completed in {processing_time:.2f}s")
                
                # Print results
                print(f"   📊 Detected {len(cubicasa_output.rooms)} rooms")
                print(f"   🧱 Detected {len(cubicasa_output.walls)} walls")
                print(f"   🚪 Detected {len(cubicasa_output.doors)} doors")
                print(f"   🪟 Detected {len(cubicasa_output.windows)} windows")
                
                return cubicasa_output
                
        except Exception as e:
            print(f"   💥 CubiCasa integration failed: {str(e)}")
            traceback.print_exc()
            return None
    
    def test_coordinate_scaling(self, cubicasa_output: CubiCasaOutput, test_dimensions: List[Dict[str, Any]]) -> Optional[ScaledCoordinates]:
        """Test coordinate scaling with user-provided dimensions"""
        print(f"📏 Testing coordinate scaling...")
        
        try:
            # Get room suggestions
            suggestions = self.coordinate_scaler.get_smart_room_suggestions(cubicasa_output)
            print(f"   💡 Room suggestions:")
            for suggestion in suggestions:
                print(f"      - {suggestion.name}: {suggestion.description} (Priority: {suggestion.priority})")
            
            # Test with first suggestion
            if suggestions:
                test_room = suggestions[0]
                test_dimension = test_dimensions[0] if test_dimensions else {"width": 20, "length": 15}
                
                print(f"   🎯 Testing with room: {test_room.name}")
                print(f"   📐 User input: {test_dimension['width']}' x {test_dimension['length']}'")
                
                # Scale coordinates
                scaled_coords = self.coordinate_scaler.convert_coordinates_to_feet(
                    cubicasa_output,
                    test_room.id,
                    test_dimension['width']
                )
                
                print(f"   ✅ Scaling completed with factor: {scaled_coords.scale_factor:.4f}")
                print(f"   📊 Scaled {len(scaled_coords.rooms_feet)} rooms")
                print(f"   🧱 Scaled {len(scaled_coords.walls_feet)} walls")
                
                return scaled_coords
            else:
                print("   ⚠️  No room suggestions available")
                return None
                
        except Exception as e:
            print(f"   💥 Coordinate scaling failed: {str(e)}")
            traceback.print_exc()
            return None
    
    def test_3d_generation(self, scaled_coords: ScaledCoordinates) -> Dict[str, Any]:
        """Test 3D model generation"""
        print(f"🏗️  Testing 3D model generation...")
        
        try:
            # Generate room meshes
            print("   🔨 Generating room meshes...")
            rooms_3d = self.room_generator.generate_room_meshes(scaled_coords)
            print(f"   ✅ Generated {len(rooms_3d)} room meshes")
            
            # Generate wall meshes
            print("   🧱 Generating wall meshes...")
            walls_3d = self.wall_generator.generate_wall_meshes(scaled_coords)
            print(f"   ✅ Generated {len(walls_3d)} wall meshes")
            
            # Combine meshes
            print("   🔗 Combining meshes...")
            combined_mesh = self.combine_meshes(rooms_3d, walls_3d)
            
            if combined_mesh:
                print(f"   ✅ Combined mesh: {len(combined_mesh['vertices'])} vertices, {len(combined_mesh['faces'])} faces")
                return {
                    'rooms': rooms_3d,
                    'walls': walls_3d,
                    'combined_mesh': combined_mesh
                }
            else:
                print("   ⚠️  No mesh to combine")
                return None
                
        except Exception as e:
            print(f"   💥 3D generation failed: {str(e)}")
            traceback.print_exc()
            return None
    
    def combine_meshes(self, rooms_3d: List[Room3D], walls_3d: List[Wall3D]) -> Optional[Dict[str, Any]]:
        """Combine room and wall meshes into a single mesh"""
        all_vertices = []
        all_faces = []
        vertex_offset = 0
        
        # Add room meshes
        for room in rooms_3d:
            if hasattr(room, 'mesh') and room.mesh:
                all_vertices.extend(room.mesh.vertices)
                for face in room.mesh.faces:
                    adjusted_face = Face(
                        indices=[i + vertex_offset for i in face.indices],
                        material="room_material"
                    )
                    all_faces.append(adjusted_face)
                vertex_offset += len(room.mesh.vertices)
        
        # Add wall meshes
        for wall in walls_3d:
            if hasattr(wall, 'mesh') and wall.mesh:
                all_vertices.extend(wall.mesh.vertices)
                for face in wall.mesh.faces:
                    adjusted_face = Face(
                        indices=[i + vertex_offset for i in face.indices],
                        material="wall_material"
                    )
                    all_faces.append(adjusted_face)
                vertex_offset += len(wall.mesh.vertices)
        
        if not all_vertices:
            return None
        
        return {
            'vertices': all_vertices,
            'faces': all_faces
        }
    
    def export_models(self, combined_mesh: Dict[str, Any], test_name: str) -> Dict[str, Path]:
        """Export 3D models to various formats"""
        print(f"📦 Exporting 3D models...")
        
        try:
            # Create export directory
            export_dir = self.output_dir / test_name
            export_dir.mkdir(exist_ok=True)
            
            # Create mesh object
            mesh_obj = type('Mesh', (), {
                'vertices': combined_mesh['vertices'],
                'faces': combined_mesh['faces']
            })()
            
            # Export to different formats
            timestamp = int(time.time())
            base_filename = f"{test_name}_{timestamp}"
            
            # Export OBJ
            obj_path = export_dir / f"{base_filename}.obj"
            self.mesh_exporter.export_obj(mesh_obj, str(obj_path))
            print(f"   ✅ Exported OBJ: {obj_path}")
            
            # Export GLB
            glb_path = export_dir / f"{base_filename}.glb"
            self.mesh_exporter.export_glb(mesh_obj, str(glb_path))
            print(f"   ✅ Exported GLB: {glb_path}")
            
            # Export STL
            stl_path = export_dir / f"{base_filename}.stl"
            self.mesh_exporter.export_stl(mesh_obj, str(stl_path))
            print(f"   ✅ Exported STL: {stl_path}")
            
            return {
                'obj': obj_path,
                'glb': glb_path,
                'stl': stl_path
            }
            
        except Exception as e:
            print(f"   💥 Model export failed: {str(e)}")
            traceback.print_exc()
            return {}
    
    def create_test_report(self, test_name: str, results: Dict[str, Any]) -> Path:
        """Create a test report"""
        print(f"📝 Creating test report...")
        
        try:
            report_path = self.output_dir / f"{test_name}_report.txt"
            
            with open(report_path, 'w') as f:
                f.write(f"3D Model Generation Test Report\n")
                f.write(f"Test: {test_name}\n")
                f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                
                # CubiCasa results
                if 'cubicasa_output' in results:
                    f.write("CUBICASA DETECTION RESULTS:\n")
                    f.write(f"- Rooms detected: {len(results['cubicasa_output'].rooms)}\n")
                    f.write(f"- Walls detected: {len(results['cubicasa_output'].walls)}\n")
                    f.write(f"- Doors detected: {len(results['cubicasa_output'].doors)}\n")
                    f.write(f"- Windows detected: {len(results['cubicasa_output'].windows)}\n\n")
                
                # Scaling results
                if 'scaled_coords' in results:
                    f.write("COORDINATE SCALING RESULTS:\n")
                    f.write(f"- Scale factor: {results['scaled_coords'].scale_factor:.4f}\n")
                    f.write(f"- Rooms scaled: {len(results['scaled_coords'].rooms_feet)}\n")
                    f.write(f"- Walls scaled: {len(results['scaled_coords'].walls_feet)}\n\n")
                
                # 3D generation results
                if 'generation_results' in results:
                    f.write("3D GENERATION RESULTS:\n")
                    f.write(f"- Rooms generated: {len(results['generation_results']['rooms'])}\n")
                    f.write(f"- Walls generated: {len(results['generation_results']['walls'])}\n")
                    if results['generation_results']['combined_mesh']:
                        mesh = results['generation_results']['combined_mesh']
                        f.write(f"- Total vertices: {len(mesh['vertices'])}\n")
                        f.write(f"- Total faces: {len(mesh['faces'])}\n\n")
                
                # Export results
                if 'export_paths' in results:
                    f.write("EXPORT RESULTS:\n")
                    for format_name, path in results['export_paths'].items():
                        f.write(f"- {format_name.upper()}: {path}\n")
                    f.write("\n")
                
                # Summary
                f.write("TEST SUMMARY:\n")
                success_count = sum(1 for key in ['cubicasa_output', 'scaled_coords', 'generation_results', 'export_paths'] 
                                 if key in results)
                f.write(f"- Pipeline stages completed: {success_count}/4\n")
                
                if success_count == 4:
                    f.write("- Status: ✅ FULLY SUCCESSFUL\n")
                elif success_count >= 2:
                    f.write("- Status: ⚠️  PARTIALLY SUCCESSFUL\n")
                else:
                    f.write("- Status: ❌ FAILED\n")
            
            print(f"   ✅ Created report: {report_path}")
            return report_path
            
        except Exception as e:
            print(f"   💥 Report creation failed: {str(e)}")
            return None
    
    def run_complete_test(self, test_image: Dict[str, str]) -> bool:
        """Run complete test for a test image"""
        print(f"\n🚀 Running complete test: {test_image['name']}")
        print("=" * 60)
        
        results = {}
        
        try:
            # Test CubiCasa integration
            cubicasa_output = self.test_cubicasa_integration(test_image['path'])
            if cubicasa_output:
                results['cubicasa_output'] = cubicasa_output
                
                # Test coordinate scaling
                test_dimensions = [{"width": 20, "length": 15}]  # Mock user input
                scaled_coords = self.test_coordinate_scaling(cubicasa_output, test_dimensions)
                if scaled_coords:
                    results['scaled_coords'] = scaled_coords
                    
                    # Test 3D generation
                    generation_results = self.test_3d_generation(scaled_coords)
                    if generation_results:
                        results['generation_results'] = generation_results
                        
                        # Export models
                        export_paths = self.export_models(generation_results['combined_mesh'], test_image['name'])
                        if export_paths:
                            results['export_paths'] = export_paths
                            
                            # Create report
                            report_path = self.create_test_report(test_image['name'], results)
                            if report_path:
                                results['report_path'] = report_path
                
                # Print summary
                success_count = len(results)
                print(f"\n📊 Test Results Summary:")
                print(f"   ✅ CubiCasa: {'✓' if 'cubicasa_output' in results else '✗'}")
                print(f"   ✅ Scaling: {'✓' if 'scaled_coords' in results else '✗'}")
                print(f"   ✅ 3D Generation: {'✓' if 'generation_results' in results else '✗'}")
                print(f"   ✅ Export: {'✓' if 'export_paths' in results else '✗'}")
                print(f"   ✅ Report: {'✓' if 'report_path' in results else '✗'}")
                
                if success_count >= 3:
                    print(f"\n🎉 Test completed successfully! ({success_count}/5 stages passed)")
                    return True
                else:
                    print(f"\n⚠️  Test partially completed ({success_count}/5 stages passed)")
                    return False
            else:
                print(f"\n❌ Test failed at CubiCasa stage")
                return False
                
        except Exception as e:
            print(f"\n💥 Test failed with error: {str(e)}")
            traceback.print_exc()
            return False
    
    def run_all_tests(self):
        """Run all test cases"""
        print("🧪 Starting Real Pipeline Local Testing")
        print("=" * 60)
        
        results = []
        for test_image in self.test_images:
            success = self.run_complete_test(test_image)
            results.append({
                'name': test_image['name'],
                'success': success
            })
        
        # Summary
        print("\n📊 Overall Test Summary")
        print("=" * 60)
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        
        for result in results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {result['name']}")
        
        print(f"\nOverall: {successful}/{total} tests passed")
        
        if successful > 0:
            print(f"\n🎯 Check the output directory for results:")
            print(f"   {self.output_dir.absolute()}")

def main():
    """Main function"""
    tester = RealPipelineLocalTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
