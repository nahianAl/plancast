"""
Mesh Exporter Service for PlanCast.

Task 5: Export 3D building models in multiple formats.
Combines Room3D and Wall3D meshes into exportable 3D model files.
"""

import time
import os
import math
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import logging

try:
    import trimesh
    import numpy as np
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False
    trimesh = None
    np = None

from models.data_structures import (
    Building3D, 
    Room3D, 
    Wall3D, 
    Vertex3D, 
    Face,
    MeshExportResult,
    WebPreviewData,
    ExportFormat
)
from utils.logger import get_logger, log_job_start, log_job_complete, log_job_error
from config.settings import (
    GENERATED_MODELS_DIR,
    USE_Y_UP_FOR_WEB,
    DEFAULT_UNITS,
    WEB_OPTIMIZED_GLB
)

logger = get_logger("mesh_exporter")


class MeshExportError(Exception):
    """Custom exception for mesh export errors."""
    pass


class DependencyError(Exception):
    """Custom exception for missing dependencies."""
    pass


class MeshExporter:
    """
    Production mesh exporter service.
    
    Combines Room3D and Wall3D meshes into exportable 3D model files
    in multiple formats (GLB, OBJ, STL, etc.).
    """
    
    def __init__(self):
        """Initialize mesh exporter."""
        if not TRIMESH_AVAILABLE:
            raise DependencyError(
                "trimesh library not available. Install with: pip install trimesh"
            )
        
        self.supported_formats = ["glb", "obj", "stl", "fbx", "skp"]
        self.web_optimized_formats = ["glb"]
        self.placeholder_formats = ["fbx"]  # Only FBX is still a placeholder
        
    def check_skp_export_support(self) -> str:
        """
        Check SKP export support and return the best available method.
        
        Returns:
            'trimesh' if SKP export is directly supported
            'collada_fallback' if SKP not supported but Collada is available
            'obj_fallback' if neither SKP nor Collada is available
        """
        try:
            # Check if trimesh supports SKP directly
            if 'skp' in trimesh.available_formats():
                logger.info("✅ SKP export directly supported by trimesh")
                return 'trimesh'
            
            # Check if Collada (DAE) is available as fallback
            if 'dae' in trimesh.available_formats():
                logger.info("✅ SKP not supported, but Collada (DAE) fallback available")
                return 'collada_fallback'
            
            # Last resort: OBJ fallback
            logger.warning("⚠️ SKP and Collada not supported, using OBJ fallback")
            return 'obj_fallback'
            
        except Exception as e:
            logger.error(f"❌ Error checking SKP export support: {str(e)}")
            return 'obj_fallback'
    
    def _optimize_for_sketchup(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """
        Optimize mesh for SketchUp import.
        
        Args:
            mesh: Input trimesh
            
        Returns:
            Optimized trimesh for SketchUp
        """
        logger.info("Optimizing mesh for SketchUp...")
        
        try:
            # Make a copy to avoid modifying original
            optimized_mesh = mesh.copy()
            
            # Fix face normals (SketchUp is sensitive to face winding)
            if not optimized_mesh.is_winding_consistent:
                logger.info("Fixing face winding for SketchUp compatibility")
                optimized_mesh.fix_normals()
            
            # Merge duplicate vertices
            if len(optimized_mesh.vertices) > 0:
                logger.info("Merging duplicate vertices")
                merged_mesh = optimized_mesh.merge_vertices()
                if merged_mesh is not None:
                    optimized_mesh = merged_mesh
            
            # Remove degenerate faces
            if len(optimized_mesh.faces) > 0:
                logger.info("Removing degenerate faces")
                cleaned_mesh = optimized_mesh.remove_degenerate_faces()
                if cleaned_mesh is not None:
                    optimized_mesh = cleaned_mesh
            
            # Convert from feet to inches (SketchUp's internal units)
            # Scale by 12 (1 foot = 12 inches)
            logger.info("Converting units from feet to inches for SketchUp")
            scale_matrix = np.array([
                [12.0, 0, 0, 0],
                [0, 12.0, 0, 0],
                [0, 0, 12.0, 0],
                [0, 0, 0, 1]
            ])
            optimized_mesh.apply_transform(scale_matrix)
            
            logger.info(f"✅ SketchUp optimization completed: {len(optimized_mesh.vertices)} vertices, {len(optimized_mesh.faces)} faces")
            return optimized_mesh
            
        except Exception as e:
            logger.warning(f"⚠️ SketchUp optimization failed, using original mesh: {str(e)}")
            return mesh
    
    def _create_sketchup_import_instructions(self, 
                                           building: Building3D,
                                           export_path: str,
                                           export_method: str) -> str:
        """
        Create import instructions file for SketchUp.
        
        Args:
            building: Building3D object
            export_path: Path to exported file
            export_method: Export method used ('collada_fallback' or 'obj_fallback')
            
        Returns:
            Path to instructions file
        """
        instructions_path = export_path.replace('.dae', '_import_instructions.txt').replace('.obj', '_import_instructions.txt')
        
        instructions = f"""SKETCHUP IMPORT INSTRUCTIONS
===============================

Model Information:
- Rooms: {len(building.rooms)}
- Walls: {len(building.walls)}
- Total Vertices: {building.total_vertices}
- Total Faces: {building.total_faces}
- Export Method: {export_method.upper()}

Import Steps:
"""

        if export_method == 'collada_fallback':
            instructions += """
1. Open SketchUp
2. Go to File > Import
3. Select the .dae file: {export_path}
4. In Import Options:
   - Units: Inches
   - Merge Coplanar Faces: Yes
   - Orient Faces Consistently: Yes
5. Click Import
6. The model will be imported at 1:1 scale in inches

Note: This model was exported as Collada (.dae) format, which SketchUp imports natively.
The geometry has been optimized for SketchUp compatibility.
"""
        else:  # obj_fallback
            instructions += """
1. Open SketchUp
2. Go to File > Import
3. Select the .obj file: {export_path}
4. In Import Options:
   - Units: Inches
   - Merge Coplanar Faces: Yes
   - Orient Faces Consistently: Yes
5. Click Import
6. The model will be imported at 1:1 scale in inches

Note: This model was exported as OBJ format as a fallback option.
For best results, consider using the Collada (.dae) format if available.
"""

        instructions += f"""

Model Statistics:
- Building Dimensions: {building.bounding_box.get('max_x', 0) - building.bounding_box.get('min_x', 0):.1f}' × {building.bounding_box.get('max_y', 0) - building.bounding_box.get('min_y', 0):.1f}' × {building.bounding_box.get('max_z', 0) - building.bounding_box.get('min_z', 0):.1f}'
- Total Area: {building.bounding_box.get('max_x', 0) - building.bounding_box.get('min_x', 0) * (building.bounding_box.get('max_y', 0) - building.bounding_box.get('min_y', 0)):.1f} sq ft

Generated by PlanCast - AI Floor Plan to 3D Converter
"""

        try:
            with open(instructions_path, 'w') as f:
                f.write(instructions)
            logger.info(f"✅ Created SketchUp import instructions: {instructions_path}")
            return instructions_path
        except Exception as e:
            logger.error(f"❌ Failed to create import instructions: {str(e)}")
            return ""
        
    def export_building(self, 
                       building: Building3D,
                       formats: List[str],
                       out_dir: str = "output/generated_models") -> MeshExportResult:
        """
        Export building model in multiple formats.
        
        Args:
            building: Building3D object with rooms and walls
            formats: List of export formats (glb, obj, stl, etc.)
            out_dir: Output directory for exported files
            
        Returns:
            MeshExportResult with file paths and metadata
            
        Raises:
            MeshExportError: If export fails
            DependencyError: If required libraries missing
        """
        start_time = time.time()
        
        logger.info(f"Exporting building model in formats: {formats}")
        logger.info(f"Building has {len(building.rooms)} rooms and {len(building.walls)} walls")
        logger.info(f"Total geometry: {building.total_vertices} vertices, {building.total_faces} faces")
        
        try:
            # Validate input
            self._validate_building(building)
            self._validate_formats(formats)
            
            # Create output directory
            output_path = Path(out_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename base
            timestamp = int(time.time())
            filename_base = f"building_{timestamp}"
            
            # Export in each requested format
            exported_files = {}
            file_sizes = {}
            
            for format_name in formats:
                try:
                    format_name = format_name.lower()
                    if format_name not in self.supported_formats:
                        logger.warning(f"Unsupported format '{format_name}', skipping")
                        continue
                    
                    # Generate output file path
                    out_path = output_path / f"{filename_base}.{format_name}"
                    
                    # Export based on format
                    if format_name == "glb":
                        file_path = self.export_glb(building, str(out_path), web_optimized=True)
                    elif format_name == "obj":
                        file_path = self.export_obj(building, str(out_path))
                    elif format_name == "stl":
                        file_path = self.export_stl(building, str(out_path))
                    elif format_name == "fbx":
                        file_path = self.export_fbx(building, str(out_path))
                    elif format_name == "skp":
                        file_path = self.export_skp(building, str(out_path))
                    else:
                        logger.warning(f"Format '{format_name}' not implemented, skipping")
                        continue
                    
                    # Get file size and store results
                    file_size = os.path.getsize(file_path)
                    
                    # Handle placeholder formats (FBX exports as OBJ)
                    if format_name in self.placeholder_formats:
                        logger.info(f"📝 Note: {format_name.upper()} exported as OBJ (placeholder implementation)")
                        # Store as OBJ format in results
                        exported_files["obj"] = file_path
                        file_sizes["obj"] = file_size
                    # Handle SKP format (may return .skp, .dae, or .obj)
                    elif format_name == "skp":
                        # Determine actual format from file extension
                        actual_format = os.path.splitext(file_path)[1][1:].lower()
                        if actual_format in ["skp", "dae", "obj"]:
                            exported_files[actual_format] = file_path
                            file_sizes[actual_format] = file_size
                            logger.info(f"📝 Note: SKP exported as {actual_format.upper()}")
                        else:
                            # Fallback to storing as requested format
                            exported_files[format_name] = file_path
                            file_sizes[format_name] = file_size
                    else:
                        exported_files[format_name] = file_path
                        file_sizes[format_name] = file_size
                    
                    logger.info(f"✅ Exported {format_name.upper()}: {file_path} ({file_size} bytes)")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to export {format_name}: {str(e)}")
                    raise MeshExportError(f"Export failed for format '{format_name}': {str(e)}")
            
            # Generate web preview data
            preview_data = self._generate_web_preview_data(building, exported_files, filename_base)
            
            # Create export summary
            export_time = time.time() - start_time
            summary = {
                "export_time_seconds": export_time,
                "formats_exported": list(exported_files.keys()),
                "total_files": len(exported_files),
                "file_sizes": file_sizes,
                "total_size_bytes": sum(file_sizes.values()),
                "building_stats": {
                    "rooms": len(building.rooms),
                    "walls": len(building.walls),
                    "total_vertices": building.total_vertices,
                    "total_faces": building.total_faces
                }
            }
            
            # Create result
            result = MeshExportResult(
                files=exported_files,
                preview_data=preview_data,
                summary=summary
            )
            
            logger.info(f"✅ Building export completed: {len(exported_files)} formats in {export_time:.3f}s")
            
            return result
            
        except Exception as e:
            export_time = time.time() - start_time
            logger.error(f"❌ Building export failed after {export_time:.3f}s: {str(e)}")
            raise MeshExportError(f"Building export failed: {str(e)}")
    
    def export_glb(self, building: Building3D, out_path: str, web_optimized: bool = True) -> str:
        """
        Export building as GLB format (web-optimized).
        
        Args:
            building: Building3D object
            out_path: Output file path
            web_optimized: Optimize for web viewing
            
        Returns:
            Path to exported GLB file
        """
        logger.info(f"Exporting GLB: {out_path} (web_optimized={web_optimized})")
        
        try:
            # Combine all meshes
            combined_mesh = self._combine_building_meshes(building)
            
            # Convert to Y-up for web compatibility if needed
            if USE_Y_UP_FOR_WEB and web_optimized:
                combined_mesh = self._convert_to_y_up(combined_mesh)
            
            # Optimize for web if requested
            if web_optimized:
                combined_mesh = self._optimize_for_web(combined_mesh)
            
            # Export as GLB
            combined_mesh.export(out_path, file_type="glb")
            
            logger.info(f"✅ GLB export successful: {out_path}")
            return out_path
            
        except Exception as e:
            logger.error(f"❌ GLB export failed: {str(e)}")
            raise MeshExportError(f"GLB export failed: {str(e)}")
    
    def export_obj(self, building: Building3D, out_path: str) -> str:
        """
        Export building as OBJ format.
        
        Args:
            building: Building3D object
            out_path: Output file path
            
        Returns:
            Path to exported OBJ file
        """
        logger.info(f"Exporting OBJ: {out_path}")
        
        try:
            # Combine all meshes
            combined_mesh = self._combine_building_meshes(building)
            
            # Export as OBJ
            combined_mesh.export(out_path, file_type="obj")
            
            logger.info(f"✅ OBJ export successful: {out_path}")
            return out_path
            
        except Exception as e:
            logger.error(f"❌ OBJ export failed: {str(e)}")
            raise MeshExportError(f"OBJ export failed: {str(e)}")
    
    def export_stl(self, building: Building3D, out_path: str) -> str:
        """
        Export building as STL format.
        
        Args:
            building: Building3D object
            out_path: Output file path
            
        Returns:
            Path to exported STL file
        """
        logger.info(f"Exporting STL: {out_path}")
        
        try:
            # Combine all meshes
            combined_mesh = self._combine_building_meshes(building)
            
            # Export as STL
            combined_mesh.export(out_path, file_type="stl")
            
            logger.info(f"✅ STL export successful: {out_path}")
            return out_path
            
        except Exception as e:
            logger.error(f"❌ STL export failed: {str(e)}")
            raise MeshExportError(f"STL export failed: {str(e)}")
    
    def export_fbx(self, building: Building3D, out_path: str) -> str:
        """
        Export building as FBX format (placeholder - exports OBJ for now).
        
        Args:
            building: Building3D object
            out_path: Output file path
            
        Returns:
            Path to exported OBJ file (converted from FBX request)
        """
        logger.info(f"Exporting FBX: {out_path}")
        logger.warning("FBX export not yet implemented, exporting OBJ instead")
        
        try:
            # Export as OBJ instead (placeholder implementation)
            obj_path = out_path.replace('.fbx', '.obj')
            result = self.export_obj(building, obj_path)
            
            logger.info(f"✅ FBX placeholder: exported OBJ instead: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ FBX placeholder export failed: {str(e)}")
            raise MeshExportError(f"FBX placeholder export failed: {str(e)}")
    
    def export_skp(self, building: Building3D, out_path: str) -> str:
        """
        Export building as SKP format using hybrid approach.
        
        Args:
            building: Building3D object
            out_path: Output file path
            
        Returns:
            Path to exported file (.skp, .dae, or .obj)
        """
        logger.info(f"Exporting SKP: {out_path}")
        
        try:
            # Check available export methods
            export_method = self.check_skp_export_support()
            
            # Combine building meshes
            combined_mesh = self._combine_building_meshes(building)
            
            if export_method == 'trimesh':
                # Try direct SKP export
                logger.info("Attempting direct SKP export via trimesh")
                try:
                    combined_mesh.export(out_path, file_type="skp")
                    logger.info(f"✅ SKP export successful: {out_path}")
                    return out_path
                except Exception as e:
                    logger.warning(f"Direct SKP export failed: {str(e)}, falling back to Collada")
                    export_method = 'collada_fallback'
            
            if export_method == 'collada_fallback':
                # Export as Collada (.dae)
                logger.info("Using Collada (.dae) fallback for SketchUp compatibility")
                dae_path = out_path.replace('.skp', '.dae')
                
                # Optimize mesh for SketchUp
                optimized_mesh = self._optimize_for_sketchup(combined_mesh)
                
                # Export as Collada
                optimized_mesh.export(dae_path, file_type="dae")
                
                # Create import instructions
                self._create_sketchup_import_instructions(building, dae_path, export_method)
                
                logger.info(f"✅ Collada export successful: {dae_path}")
                return dae_path
            
            else:  # obj_fallback
                # Export as OBJ as last resort
                logger.warning("Using OBJ fallback for SketchUp compatibility")
                obj_path = out_path.replace('.skp', '.obj')
                
                # Optimize mesh for SketchUp
                optimized_mesh = self._optimize_for_sketchup(combined_mesh)
                
                # Export as OBJ
                optimized_mesh.export(obj_path, file_type="obj")
                
                # Create import instructions
                self._create_sketchup_import_instructions(building, obj_path, export_method)
                
                logger.info(f"✅ OBJ fallback export successful: {obj_path}")
                return obj_path
            
        except Exception as e:
            logger.error(f"❌ SKP export failed: {str(e)}")
            raise MeshExportError(f"SKP export failed: {str(e)}")
    
    def _validate_building(self, building: Building3D) -> None:
        """
        Validate building data for export.
        
        Args:
            building: Building3D object to validate
            
        Raises:
            MeshExportError: If validation fails
        """
        if not building.rooms and not building.walls:
            raise MeshExportError("Building has no rooms or walls to export")
        
        if building.total_vertices <= 0:
            raise MeshExportError("Building has no vertices")
        
        if building.total_faces <= 0:
            raise MeshExportError("Building has no faces")
        
        logger.info(f"✅ Building validation passed: {building.total_vertices} vertices, {building.total_faces} faces")
    
    def _validate_formats(self, formats: List[str]) -> None:
        """
        Validate export formats.
        
        Args:
            formats: List of format names to validate
            
        Raises:
            MeshExportError: If validation fails
        """
        if not formats:
            raise MeshExportError("No export formats specified")
        
        for format_name in formats:
            if format_name.lower() not in self.supported_formats:
                logger.warning(f"Unsupported format: {format_name}")
        
        logger.info(f"✅ Format validation passed: {formats}")
    
    def _combine_building_meshes(self, building: Building3D) -> trimesh.Trimesh:
        """
        Combine all room and wall meshes into a single trimesh.
        
        Args:
            building: Building3D object
            
        Returns:
            Combined trimesh object
        """
        logger.info("Combining building meshes...")
        
        all_meshes = []
        
        # Convert room meshes
        for room in building.rooms:
            room_mesh = self._room_to_trimesh(room)
            all_meshes.append(room_mesh)
            logger.debug(f"Added room '{room.name}': {len(room_mesh.vertices)} vertices")
        
        # Convert wall meshes
        for wall in building.walls:
            wall_mesh = self._wall_to_trimesh(wall)
            all_meshes.append(wall_mesh)
            logger.debug(f"Added wall '{wall.id}': {len(wall_mesh.vertices)} vertices")
        
        # Combine all meshes
        if len(all_meshes) == 1:
            combined_mesh = all_meshes[0]
        else:
            combined_mesh = trimesh.util.concatenate(all_meshes)
        
        logger.info(f"✅ Combined {len(all_meshes)} meshes into single mesh: "
                   f"{len(combined_mesh.vertices)} vertices, {len(combined_mesh.faces)} faces")
        
        return combined_mesh
    
    def _room_to_trimesh(self, room: Room3D) -> trimesh.Trimesh:
        """
        Convert Room3D to trimesh.
        
        Args:
            room: Room3D object
            
        Returns:
            Trimesh object
        """
        # Extract vertices and faces
        vertices = np.array([[v.x, v.y, v.z] for v in room.vertices])
        faces = np.array([f.indices for f in room.faces])
        
        # Create trimesh
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Debug logging
        logger.debug(f"Room '{room.name}' mesh: {len(vertices)} vertices, {len(faces)} faces")
        logger.debug(f"Mesh bounds: {mesh.bounds}")
        logger.debug(f"Mesh volume: {mesh.volume}")
        logger.debug(f"Mesh is watertight: {mesh.is_watertight}")
        logger.debug(f"Mesh is winding consistent: {mesh.is_winding_consistent}")
        
        return mesh
    
    def _wall_to_trimesh(self, wall: Wall3D) -> trimesh.Trimesh:
        """
        Convert Wall3D to trimesh.
        
        Args:
            wall: Wall3D object
            
        Returns:
            Trimesh object
        """
        # Extract vertices and faces
        vertices = np.array([[v.x, v.y, v.z] for v in wall.vertices])
        faces = np.array([f.indices for f in wall.faces])
        
        # Create trimesh
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Debug logging
        logger.debug(f"Wall '{wall.id}' mesh: {len(vertices)} vertices, {len(faces)} faces")
        logger.debug(f"Mesh bounds: {mesh.bounds}")
        logger.debug(f"Mesh volume: {mesh.volume}")
        logger.debug(f"Mesh is watertight: {mesh.is_watertight}")
        logger.debug(f"Mesh is winding consistent: {mesh.is_winding_consistent}")
        
        return mesh
    
    def _convert_to_y_up(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """
        Convert mesh from Z-up to Y-up coordinate system for web compatibility.
        
        Args:
            mesh: Input trimesh
            
        Returns:
            Converted trimesh
        """
        # Create 4x4 transformation matrix: swap Y and Z axes
        transform = np.array([
            [1, 0, 0, 0],    # X stays the same
            [0, 0, 1, 0],    # Y becomes Z
            [0, -1, 0, 0],   # Z becomes -Y
            [0, 0, 0, 1]     # Homogeneous coordinate
        ])
        
        # Apply transformation
        mesh.apply_transform(transform)
        
        logger.debug("Converted mesh to Y-up coordinate system")
        return mesh
    
    def _optimize_for_web(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """
        Optimize mesh for web viewing.
        
        Args:
            mesh: Input trimesh
            
        Returns:
            Optimized trimesh
        """
        # For now, just return the mesh as-is
        # TODO: Implement proper optimization when trimesh methods are confirmed
        logger.debug(f"Mesh optimization skipped: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
        return mesh
    
    def _generate_web_preview_data(self, 
                                 building: Building3D,
                                 exported_files: Dict[str, str],
                                 filename_base: str) -> WebPreviewData:
        """
        Generate web preview data for browser visualization.
        
        Args:
            building: Building3D object
            exported_files: Dictionary of exported file paths
            filename_base: Base filename for assets
            
        Returns:
            WebPreviewData object
        """
        # Find GLB file for web preview
        glb_path = exported_files.get("glb", "")
        glb_url = f"/models/{filename_base}.glb" if glb_path else ""
        
        # Generate thumbnail URL (placeholder for now)
        thumbnail_url = f"/thumbnails/{filename_base}.jpg"
        
        # Calculate scene metadata
        scene_metadata = self._calculate_scene_metadata(building)
        
        preview_data = WebPreviewData(
            glb_url=glb_url,
            thumbnail_url=thumbnail_url,
            scene_metadata=scene_metadata
        )
        
        logger.info(f"Generated web preview data: GLB={glb_url}, thumbnail={thumbnail_url}")
        return preview_data
    
    def _calculate_scene_metadata(self, building: Building3D) -> Dict[str, Any]:
        """
        Calculate scene metadata for Three.js.
        
        Args:
            building: Building3D object
            
        Returns:
            Scene metadata dictionary
        """
        bbox = building.bounding_box
        
        # Calculate building center
        center_x = (bbox["min_x"] + bbox["max_x"]) / 2
        center_y = (bbox["min_y"] + bbox["max_y"]) / 2
        center_z = (bbox["min_z"] + bbox["max_z"]) / 2
        
        # Calculate building dimensions
        width = bbox["max_x"] - bbox["min_x"]
        height = bbox["max_z"] - bbox["min_z"]
        depth = bbox["max_y"] - bbox["min_y"]
        
        # Calculate optimal camera distance
        max_dim = max(width, height, depth)
        camera_distance = max_dim * 2.0
        
        metadata = {
            "building_center": [center_x, center_y, center_z],
            "building_dimensions": [width, height, depth],
            "bounding_box": bbox,
            "camera_positions": {
                "isometric": [camera_distance, camera_distance, camera_distance],
                "top": [center_x, center_y, camera_distance],
                "front": [center_x, camera_distance, center_z],
                "side": [camera_distance, center_y, center_z]
            },
            "units": DEFAULT_UNITS,
            "total_vertices": building.total_vertices,
            "total_faces": building.total_faces
        }
        
        return metadata
    
    def validate_export_result(self, result: MeshExportResult) -> Dict[str, Any]:
        """
        Validate export result.
        
        Args:
            result: MeshExportResult to validate
            
        Returns:
            Validation result dictionary
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "files_exported": len(result.files),
            "total_size_bytes": result.summary.get("total_size_bytes", 0)
        }
        
        # Check if files were exported
        if not result.files:
            validation_result["is_valid"] = False
            validation_result["errors"].append("No files were exported")
        
        # Check file existence
        for format_name, file_path in result.files.items():
            if not os.path.exists(file_path):
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"Exported file not found: {file_path}")
            
            # Check file size
            try:
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    validation_result["warnings"].append(f"Empty file: {file_path}")
            except OSError:
                validation_result["errors"].append(f"Cannot access file: {file_path}")
        
        # Check web preview data
        if not result.preview_data.glb_url:
            validation_result["warnings"].append("No GLB URL for web preview")
        
        return validation_result


# Global service instance
_mesh_exporter = None


def get_mesh_exporter() -> MeshExporter:
    """
    Get or create global mesh exporter service instance.
    
    Returns:
        MeshExporter instance
    """
    global _mesh_exporter
    if _mesh_exporter is None:
        _mesh_exporter = MeshExporter()
        logger.info("✅ Mesh exporter service initialized")
    return _mesh_exporter
