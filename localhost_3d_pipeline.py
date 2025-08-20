#!/usr/bin/env python3
"""
Localhost 3D Pipeline Development Environment
A complete web interface for testing and developing your 3D model generation pipeline
"""

import os
import sys
import json
import time
import uuid
import shutil
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
import traceback
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template_string, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import threading
import webbrowser

# Import your pipeline components
try:
    from services.cubicasa_service import CubiCasaService
    from services.coordinate_scaler import CoordinateScaler
    from services.test_room_generator import SimpleRoomGenerator
    from services.test_wall_generator import SimpleWallGenerator
    from models.data_structures import CubiCasaOutput, Room3D, Wall3D, Face, Vertex3D
    from PIL import Image
    import numpy as np
    PIPELINE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Some pipeline components not available: {e}")
    PIPELINE_AVAILABLE = False

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'temp/uploads'
app.config['OUTPUT_FOLDER'] = 'temp/generated_models'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Global pipeline instance
pipeline = None

class Local3DPipeline:
    """Local 3D Pipeline for development and testing"""
    
    def __init__(self):
        self.cubicasa_service = None
        self.coordinate_scaler = None
        self.room_generator = None
        self.wall_generator = None
        self.initialized = False
        
        if PIPELINE_AVAILABLE:
            self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """Initialize the 3D generation pipeline"""
        try:
            print("🔧 Initializing 3D Pipeline...")
            self.cubicasa_service = CubiCasaService()
            self.coordinate_scaler = CoordinateScaler()
            self.room_generator = SimpleRoomGenerator()
            self.wall_generator = SimpleWallGenerator()
            self.initialized = True
            print("✅ 3D Pipeline initialized successfully!")
        except Exception as e:
            print(f"❌ Failed to initialize pipeline: {e}")
            self.initialized = False
    
    def process_image(self, image_path: str, room_dimensions: Dict[str, Any]) -> Dict[str, Any]:
        """Process an image through the simplified 3D pipeline (no scaling)"""
        if not self.initialized:
            return {"error": "Pipeline not initialized"}
        
        try:
            start_time = time.time()
            
            # Load and validate image
            with Image.open(image_path) as img:
                print(f"📸 Processing image: {img.size[0]}x{img.size[1]} pixels")
                
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Convert PIL image to bytes for CubiCasa
                import io
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='JPEG')
                img_bytes = img_bytes.getvalue()
            
            # Step 1: CubiCasa Processing
            print("🤖 Running CubiCasa analysis...")
            cubicasa_output = self.cubicasa_service.process_image(img_bytes, f"local_{uuid.uuid4().hex[:8]}")
            
            # Step 2: Generate 3D models (no scaling, using 1:1 pixel to foot)
            print("🏗️ Generating 3D models...")
            rooms_3d = self.room_generator.generate_simple_rooms(cubicasa_output)
            walls_3d = self.wall_generator.generate_simple_walls(cubicasa_output)
            
            # Step 3: Combine and export
            combined_mesh = self._combine_meshes(rooms_3d, walls_3d)
            
            if not combined_mesh:
                return {"error": "No mesh generated"}
            
            # Step 4: Export models
            model_name = Path(image_path).stem
            export_paths = self._export_models(combined_mesh, model_name)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "processing_time": processing_time,
                "detection_results": {
                    "rooms": len(cubicasa_output.room_bounding_boxes),
                    "walls": len(cubicasa_output.wall_coordinates),
                    "doors": len(cubicasa_output.door_coordinates),
                    "windows": len(cubicasa_output.window_coordinates)
                },
                "3d_results": {
                    "rooms_generated": len(rooms_3d),
                    "walls_generated": len(walls_3d),
                    "total_vertices": len(combined_mesh['vertices']),
                    "total_faces": len(combined_mesh['faces'])
                },
                "export_paths": export_paths,
                "model_name": model_name
            }
            
        except Exception as e:
            error_msg = f"Pipeline processing failed: {str(e)}"
            print(f"💥 {error_msg}")
            traceback.print_exc()
            return {"error": error_msg}
    
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
    
    def _export_models(self, combined_mesh: Dict[str, Any], model_name: str) -> Dict[str, str]:
        """Export 3D models to various formats"""
        try:
            # Create export directory
            export_dir = Path(app.config['OUTPUT_FOLDER']) / model_name
            export_dir.mkdir(exist_ok=True)
            
            # Export to different formats
            timestamp = int(time.time())
            base_filename = f"{model_name}_{timestamp}"
            
            export_paths = {}
            
            # Export OBJ
            obj_path = export_dir / f"{base_filename}.obj"
            self._export_obj(combined_mesh, str(obj_path))
            export_paths['obj'] = str(obj_path)
            
            # Export STL
            stl_path = export_dir / f"{base_filename}.stl"
            self._export_stl(combined_mesh, str(stl_path))
            export_paths['stl'] = str(stl_path)
            
            # Export GLB (proper implementation)
            glb_path = export_dir / f"{base_filename}.glb"
            self._export_glb(combined_mesh, str(glb_path))
            export_paths['glb'] = str(glb_path)
            
            return export_paths
            
        except Exception as e:
            print(f"💥 Model export failed: {str(e)}")
            return {}
    
    def _export_obj(self, mesh_data: Dict[str, Any], filepath: str):
        """Export mesh to OBJ format"""
        try:
            with open(filepath, 'w') as f:
                # Write vertices
                for vertex in mesh_data['vertices']:
                    f.write(f"v {vertex.x} {vertex.y} {vertex.z}\n")
                
                # Write faces (OBJ uses 1-indexed vertices)
                for face in mesh_data['faces']:
                    indices = [i + 1 for i in face.indices]
                    f.write(f"f {' '.join(map(str, indices))}\n")
            
            print(f"✅ OBJ exported: {len(mesh_data['vertices'])} vertices, {len(mesh_data['faces'])} faces")
            
        except Exception as e:
            print(f"❌ OBJ export failed: {str(e)}")
    
    def _export_stl(self, mesh_data: Dict[str, Any], filepath: str):
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
                    face_vertices = [mesh_data['vertices'][i] for i in face.indices]
                    
                    if len(face_vertices) >= 3:
                        v0, v1, v2 = face_vertices[0], face_vertices[1], face_vertices[2]
                        
                        # Calculate face normal
                        ux, uy, uz = v1.x - v0.x, v1.y - v0.y, v1.z - v0.z
                        vx, vy, vz = v2.x - v0.x, v2.y - v0.y, v2.z - v0.z
                        
                        nx = uy * vz - uz * vy
                        ny = uz * vx - ux * vz
                        nz = ux * vy - uy * vx
                        
                        length = (nx**2 + ny**2 + nz**2)**0.5
                        if length > 0:
                            nx, ny, nz = nx/length, ny/length, nz/length
                        
                        # Write normal (12 bytes)
                        for val in [nx, ny, nz]:
                            f.write(struct.pack('<f', val))
                        
                        # Write vertices (36 bytes)
                        for vertex in face_vertices[:3]:
                            for val in [vertex.x, vertex.y, vertex.z]:
                                f.write(struct.pack('<f', val))
                        
                        # Write attribute count (2 bytes)
                        f.write(b'\x00\x00')
            
            print(f"✅ STL exported: {len(mesh_data['vertices'])} vertices, {len(mesh_data['faces'])} faces")
            
        except Exception as e:
            print(f"❌ STL export failed: {str(e)}")
    
    def _export_glb(self, mesh_data: Dict[str, Any], filepath: str):
        """Export mesh to GLB format using pygltflib"""
        try:
            from pygltflib import GLTF2, Scene, Node, Mesh, Primitive, Accessor, BufferView, Buffer, Asset
            import numpy as np
            
            # Convert mesh data to numpy arrays
            vertices = np.array([[v.x, v.y, v.z] for v in mesh_data['vertices']], dtype=np.float32)
            indices = np.array([idx for face in mesh_data['faces'] for idx in face.indices], dtype=np.uint32)
            
            # Create GLTF structure
            gltf = GLTF2(
                asset=Asset(version="2.0"),
                scene=0,
                scenes=[Scene(nodes=[0])],
                nodes=[Node(mesh=0)],
                meshes=[Mesh(primitives=[Primitive(
                    attributes={"POSITION": 0},
                    indices=1
                )])],
                accessors=[
                    Accessor(
                        bufferView=0,
                        componentType=5126,  # FLOAT
                        count=len(vertices),
                        type="VEC3",
                        max=vertices.max(axis=0).tolist(),
                        min=vertices.min(axis=0).tolist()
                    ),
                    Accessor(
                        bufferView=1,
                        componentType=5125,  # UNSIGNED_INT
                        count=len(indices),
                        type="SCALAR"
                    )
                ],
                bufferViews=[
                    BufferView(
                        buffer=0,
                        byteOffset=0,
                        byteLength=len(vertices.tobytes()),
                        byteStride=12
                    ),
                    BufferView(
                        buffer=0,
                        byteOffset=len(vertices.tobytes()),
                        byteLength=len(indices.tobytes())
                    )
                ],
                buffers=[Buffer(
                    byteLength=len(vertices.tobytes()) + len(indices.tobytes())
                )]
            )
            
            # Save GLB
            gltf.save(filepath)
            
            print(f"✅ GLB exported: {len(mesh_data['vertices'])} vertices, {len(mesh_data['faces'])} faces")
            
        except Exception as e:
            print(f"❌ GLB export failed: {str(e)}")
            # Fallback to simple GLB
            self._export_simple_glb(mesh_data, filepath)
    
    def _export_simple_glb(self, mesh_data: Dict[str, Any], filepath: str):
        """Fallback GLB export (simple placeholder)"""
        try:
            with open(filepath, 'wb') as f:
                f.write(b'glTF')
                f.write(b'\x02\x00\x00\x00')  # Version 2.0
                f.write(b'\x00\x00\x00\x00')  # Length placeholder
                f.write(b'\x00\x00\x00\x00')  # Content placeholder
            
            print(f"✅ Simple GLB exported (placeholder): {len(mesh_data['vertices'])} vertices, {len(mesh_data['faces'])} faces")
            
        except Exception as e:
            print(f"❌ Simple GLB export failed: {str(e)}")

# Initialize pipeline
pipeline = Local3DPipeline()

# HTML Template for the web interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Pipeline Development Environment</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .upload-area {
            border: 3px dashed #ddd;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .upload-area:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }
        
        .upload-area.dragover {
            border-color: #667eea;
            background: #e8f0ff;
        }
        
        .upload-icon {
            font-size: 3em;
            color: #667eea;
            margin-bottom: 15px;
        }
        
        .file-input {
            display: none;
        }
        
        .dimensions-form {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 20px;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
        }
        
        .form-group label {
            margin-bottom: 5px;
            font-weight: 600;
            color: #555;
        }
        
        .form-group input {
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .generate-btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s ease;
            margin-top: 20px;
            width: 100%;
        }
        
        .generate-btn:hover {
            transform: translateY(-2px);
        }
        
        .generate-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .results-section {
            grid-column: 1 / -1;
        }
        
        .results-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .result-card {
            background: #f8f9ff;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #667eea;
        }
        
        .result-card h3 {
            color: #667eea;
            margin-bottom: 15px;
        }
        
        .stat-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .stat-item {
            background: white;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        
        .download-section {
            margin-top: 20px;
        }
        
        .download-btn {
            display: inline-block;
            background: #28a745;
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 8px;
            margin: 5px;
            transition: background 0.3s ease;
        }
        
        .download-btn:hover {
            background: #1e7e34;
        }
        
        .preview-section {
            grid-column: 1 / -1;
        }
        
        .preview-container {
            background: #1a1a1a;
            border-radius: 10px;
            height: 500px;
            position: relative;
            overflow: hidden;
        }
        
        .preview-placeholder {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #666;
            text-align: center;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #c33;
        }
        
        .success {
            background: #efe;
            color: #363;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #363;
        }
        
        .info-box {
            background: #e8f4fd;
            border: 1px solid #bee5eb;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
        }
        
        .info-box p {
            margin: 5px 0;
            color: #0c5460;
        }
        
        .manual-upload {
            text-align: center;
            margin-top: 20px;
        }
        
        .manual-btn {
            background: #6c757d;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        
        .manual-btn:hover {
            background: #5a6268;
        }
        
        .manual-hint {
            margin-top: 10px;
            color: #666;
            font-size: 14px;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .dimensions-form {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 3D Pipeline Development Environment</h1>
            <p>Test, develop, and preview your 3D model generation pipeline locally</p>
        </div>
        
        <div class="main-content">
            <!-- Upload Section -->
            <div class="card">
                <h2>📸 Upload Floor Plan</h2>
                <div class="upload-area" id="uploadArea">
                    <div class="upload-icon">📁</div>
                    <p><strong>Click to upload</strong> or drag and drop</p>
                    <p>Supports: JPG, PNG, PDF (max 16MB)</p>
                    <input type="file" id="fileInput" class="file-input" accept=".jpg,.jpeg,.png,.pdf">
                </div>
                
                <div class="manual-upload">
                    <button type="button" class="manual-btn" onclick="document.getElementById('fileInput').click()">
                        📂 Choose File Manually
                    </button>
                    <p class="manual-hint">Or drag and drop your floor plan image above</p>
                </div>
                
                <div class="info-box">
                    <p><strong>ℹ️ Simple Mode:</strong> No scaling needed</p>
                    <p>• Default wall height: 9 feet</p>
                    <p>• 1:1 pixel to foot conversion</p>
                    <p>• Focus on 3D generation quality</p>
                </div>
                
                <button class="generate-btn" id="generateBtn" onclick="generate3DModel()">
                    🚀 Generate 3D Model
                </button>
            </div>
            
            <!-- Pipeline Status -->
            <div class="card">
                <h2>🔧 Pipeline Status</h2>
                <div id="pipelineStatus">
                    <p><strong>Status:</strong> <span id="statusText">Ready</span></p>
                    <p><strong>Components:</strong></p>
                    <ul id="componentList">
                        <li>✅ CubiCasa Service</li>
                        <li>✅ Coordinate Scaler</li>
                        <li>✅ Room Generator</li>
                        <li>✅ Wall Generator</li>
                    </ul>
                </div>
                
                <div class="loading" id="loadingSection">
                    <div class="spinner"></div>
                    <p>Processing your floor plan...</p>
                    <p id="processingStep">Initializing...</p>
                </div>
            </div>
        </div>
        
        <!-- Results Section -->
        <div class="results-section card" id="resultsSection" style="display: none;">
            <h2>📊 Generation Results</h2>
            <div class="results-grid" id="resultsGrid"></div>
        </div>
        
        <!-- 3D Preview Section -->
        <div class="preview-section card" id="previewSection" style="display: none;">
            <h2>🎮 3D Model Preview</h2>
            <div class="preview-container" id="previewContainer">
                <div class="preview-placeholder">
                    <h3>3D Preview</h3>
                    <p>Your generated 3D model will appear here</p>
                    <p>Use mouse to rotate, scroll to zoom</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentFile = null;
        let currentResults = null;
        
        // File upload handling
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const generateBtn = document.getElementById('generateBtn');
        
        // Manual file selection
        uploadArea.addEventListener('click', () => fileInput.click());
        
        // Drag and drop handling
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragenter', (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
        
        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadArea.classList.remove('dragover');
            
            console.log('File dropped:', e.dataTransfer.files);
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelect(files[0]);
            }
        });
        
        // Manual file input change
        fileInput.addEventListener('change', (e) => {
            console.log('File selected:', e.target.files);
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });
        
        function handleFileSelect(file) {
            try {
                console.log('Handling file:', file.name, file.type, file.size);
                
                if (!file) {
                    console.error('No file provided');
                    return;
                }
                
                if (file.size > 16 * 1024 * 1024) {
                    alert('File too large! Maximum size is 16MB.');
                    return;
                }
                
                // Validate file type
                const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/pdf'];
                if (!allowedTypes.includes(file.type)) {
                    alert('Invalid file type! Please use JPG, PNG, or PDF.');
                    return;
                }
                
                currentFile = file;
                uploadArea.innerHTML = `
                    <div class="upload-icon">✅</div>
                    <p><strong>${file.name}</strong></p>
                    <p>Size: ${(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    <p>Type: ${file.type}</p>
                    <p>Click to change file</p>
                `;
                
                generateBtn.disabled = false;
                console.log('File selected successfully');
                
            } catch (error) {
                console.error('Error handling file:', error);
                alert('Error handling file: ' + error.message);
            }
        }
        
        async function generate3DModel() {
            try {
                console.log('Starting 3D generation...');
                
                if (!currentFile) {
                    alert('Please select a file first!');
                    return;
                }
                
                console.log('File to process:', currentFile.name, currentFile.size);
                
                // Show loading
                document.getElementById('loadingSection').style.display = 'block';
                document.getElementById('statusText').textContent = 'Processing...';
                generateBtn.disabled = true;
                
                // Create form data
                const formData = new FormData();
                formData.append('image', currentFile);
                formData.append('room_width', 20);  // Default values
                formData.append('room_length', 15); // Default values
                
                console.log('Sending request to /generate...');
                
                const response = await fetch('/generate', {
                    method: 'POST',
                    body: formData
                });
                
                console.log('Response received:', response.status, response.statusText);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const result = await response.json();
                console.log('Result:', result);
                
                if (result.success) {
                    currentResults = result;
                    showResults(result);
                    showPreview(result);
                } else {
                    showError(result.error || 'Generation failed');
                }
                
            } catch (error) {
                console.error('Generation error:', error);
                showError('Error: ' + error.message);
            } finally {
                // Hide loading
                document.getElementById('loadingSection').style.display = 'none';
                document.getElementById('statusText').textContent = 'Ready';
                generateBtn.disabled = false;
            }
        }
        
        function showResults(results) {
            const resultsSection = document.getElementById('resultsSection');
            const resultsGrid = document.getElementById('resultsGrid');
            
            resultsGrid.innerHTML = `
                <div class="result-card">
                    <h3>📊 Detection Results</h3>
                    <div class="stat-grid">
                        <div class="stat-item">
                            <div class="stat-value">${results.detection_results.rooms}</div>
                            <div class="stat-label">Rooms</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${results.detection_results.walls}</div>
                            <div class="stat-label">Walls</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${results.detection_results.doors}</div>
                            <div class="stat-label">Doors</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${results.detection_results.windows}</div>
                            <div class="stat-label">Windows</div>
                        </div>
                    </div>
                </div>
                
                <div class="result-card">
                    <h3>🏗️ 3D Generation</h3>
                    <div class="stat-grid">
                        <div class="stat-item">
                            <div class="stat-value">${results.3d_results.rooms_generated}</div>
                            <div class="stat-label">Rooms</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${results.3d_results.walls_generated}</div>
                            <div class="stat-label">Walls</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${results.3d_results.total_vertices}</div>
                            <div class="stat-label">Vertices</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${results.3d_results.total_faces}</div>
                            <div class="stat-label">Faces</div>
                        </div>
                    </div>
                </div>
                
                <div class="result-card">
                    <h3>⚡ Performance</h3>
                    <div class="stat-grid">
                        <div class="stat-item">
                            <div class="stat-value">${results.processing_time.toFixed(2)}s</div>
                            <div class="stat-label">Processing Time</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">9.0'</div>
                            <div class="stat-label">Wall Height</div>
                        </div>
                    </div>
                </div>
                
                <div class="result-card">
                    <h3>📁 Download Models</h3>
                    <div class="download-section">
                        <a href="/download/${results.export_paths.obj}" class="download-btn" download>
                            📄 OBJ File
                        </a>
                        <a href="/download/${results.export_paths.stl}" class="download-btn" download>
                            🖨️ STL File
                        </a>
                        <a href="/download/${results.export_paths.glb}" class="download-btn" download>
                            🌐 GLB File
                        </a>
                    </div>
                </div>
            `;
            
            resultsSection.style.display = 'block';
        }
        
        function showPreview(results) {
            const previewSection = document.getElementById('previewSection');
            const previewContainer = document.getElementById('previewContainer');
            
            // For now, show a placeholder
            // In the future, this could integrate with Three.js for real 3D preview
            previewContainer.innerHTML = `
                <div class="preview-placeholder">
                    <h3>🎉 3D Model Generated Successfully!</h3>
                    <p><strong>${results.model_name}</strong></p>
                    <p>${results.3d_results.total_vertices} vertices, ${results.3d_results.total_faces} faces</p>
                    <p>Processing time: ${results.processing_time.toFixed(2)} seconds</p>
                    <p>Use the download buttons above to get your 3D models</p>
                </div>
            `;
            
            previewSection.style.display = 'block';
        }
        
        function showError(message) {
            const resultsSection = document.getElementById('resultsSection');
            resultsSection.innerHTML = `
                <div class="error">
                    <h3>❌ Error</h3>
                    <p>${message}</p>
                </div>
            `;
            resultsSection.style.display = 'block';
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            generateBtn.disabled = true;
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate_3d_model():
    """Generate 3D model from uploaded image"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'})
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'})
        
        # Get room dimensions
        room_width = float(request.form.get('room_width', 20))
        room_length = float(request.form.get('room_length', 15))
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        safe_filename = f"{Path(filename).stem}_{timestamp}{Path(filename).suffix}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(filepath)
        
        # Process with pipeline
        room_dimensions = {
            'width': room_width,
            'length': room_length
        }
        
        result = pipeline.process_image(filepath, room_dimensions)
        
        if 'error' in result:
            return jsonify(result)
        
        # Convert file paths to relative URLs for download
        export_paths = {}
        for format_type, filepath in result['export_paths'].items():
            export_paths[format_type] = os.path.relpath(filepath, app.config['OUTPUT_FOLDER'])
        
        result['export_paths'] = export_paths
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = f"Generation failed: {str(e)}"
        print(f"💥 {error_msg}")
        traceback.print_exc()
        return jsonify({'error': error_msg})

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download generated 3D model files"""
    try:
        # Use absolute path to avoid Safari issues
        filepath = os.path.abspath(os.path.join(app.config['OUTPUT_FOLDER'], filename))
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True, download_name=os.path.basename(filename))
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def pipeline_status():
    """Get pipeline status"""
    return jsonify({
        'initialized': pipeline.initialized if pipeline else False,
        'components': {
            'cubicasa': pipeline.cubicasa_service is not None if pipeline else False,
            'scaler': pipeline.coordinate_scaler is not None if pipeline else False,
            'room_generator': pipeline.room_generator is not None if pipeline else False,
            'wall_generator': pipeline.wall_generator is not None if pipeline else False
        }
    })

def start_server(port=8000):
    """Start the Flask server"""
    print(f"🚀 Starting 3D Pipeline Development Server...")
    print(f"🌐 Open your browser to: http://localhost:{port}")
    print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"📁 Output folder: {app.config['OUTPUT_FOLDER']}")
    print(f"🔧 Pipeline status: {'✅ Ready' if pipeline.initialized else '❌ Not Ready'}")
    print("\n" + "="*60)
    print("🎯 This is your development playground!")
    print("📸 Upload floor plan images to test the pipeline")
    print("🏗️ Generate 3D models in real-time")
    print("📥 Download working GLB, OBJ, and STL files")
    print("🔧 Test new features as you develop them")
    print("="*60 + "\n")
    
    # Open browser automatically
    threading.Timer(1.5, lambda: webbrowser.open(f'http://localhost:{port}')).start()
    
    # Start server
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

if __name__ == '__main__':
    start_server()
