#!/usr/bin/env python3
"""
Create an Interactive 3D Viewer with Three.js
This creates a proper web-based 3D viewer and starts a local server
"""

import os
import sys
import json
import shutil
from pathlib import Path
import http.server
import socketserver
import threading
import webbrowser
import time

def create_interactive_viewer(model_dir: Path, model_name: str, original_image_path: str):
    """Create an interactive 3D viewer with Three.js"""
    
    # Read the OBJ file content
    obj_file = None
    for file in model_dir.glob("*.obj"):
        obj_file = file
        break
    
    if not obj_file:
        print("❌ No OBJ file found!")
        return None
    
    # Read OBJ content
    with open(obj_file, 'r') as f:
        obj_content = f.read()
    
    # Escape special characters for JavaScript
    obj_content_escaped = obj_content.replace('`', '\\`').replace('$', '\\$')
    
    # Create viewer HTML
    html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Floor Plan Viewer - {model_name}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: #1a1a1a;
            color: white;
            overflow: hidden;
        }}
        
        .container {{
            display: flex;
            height: 100vh;
        }}
        
        .sidebar {{
            width: 300px;
            background: #2a2a2a;
            padding: 20px;
            overflow-y: auto;
            box-shadow: 2px 0 5px rgba(0,0,0,0.3);
        }}
        
        .viewer {{
            flex: 1;
            position: relative;
        }}
        
        .controls {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(42, 42, 42, 0.9);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }}
        
        .control-group {{
            margin-bottom: 15px;
        }}
        
        .control-group label {{
            display: block;
            margin-bottom: 5px;
            font-size: 12px;
            color: #ccc;
        }}
        
        input[type="range"] {{
            width: 100%;
        }}
        
        button {{
            background: #007bff;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            margin: 2px;
        }}
        
        button:hover {{
            background: #0056b3;
        }}
        
        .download-section {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #444;
        }}
        
        .download-btn {{
            display: block;
            width: 100%;
            margin-bottom: 10px;
            background: #28a745;
            text-decoration: none;
            text-align: center;
            padding: 10px;
            border-radius: 4px;
        }}
        
        .download-btn:hover {{
            background: #1e7e34;
        }}
        
        .stats {{
            background: #333;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        
        .stat-item {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }}
        
        .original-image {{
            max-width: 100%;
            border-radius: 8px;
            margin-bottom: 15px;
        }}
        
        #loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 18px;
            color: #ccc;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h2>🏠 3D Floor Plan</h2>
            <h3>{model_name}</h3>
            
            <div class="stats">
                <h4>📊 Model Statistics</h4>
                <div class="stat-item">
                    <span>Vertices:</span>
                    <span id="vertex-count">Loading...</span>
                </div>
                <div class="stat-item">
                    <span>Faces:</span>
                    <span id="face-count">Loading...</span>
                </div>
                <div class="stat-item">
                    <span>Rooms:</span>
                    <span>2</span>
                </div>
                <div class="stat-item">
                    <span>Walls:</span>
                    <span>8</span>
                </div>
            </div>
            
            <h4>📸 Original Floor Plan</h4>
            <img src="{original_image_path}" alt="Original Floor Plan" class="original-image">
            
            <div class="download-section">
                <h4>📁 Download 3D Models</h4>
                <a href="{obj_file.name}" download class="download-btn">
                    📄 Download OBJ (Most Compatible)
                </a>
                <a href="{model_dir.glob('*.stl').__next__().name}" download class="download-btn">
                    🖨️ Download STL (3D Printing)
                </a>
                <a href="{model_dir.glob('*.glb').__next__().name}" download class="download-btn">
                    🌐 Download GLB (Web Optimized)
                </a>
            </div>
        </div>
        
        <div class="viewer">
            <div id="loading">Loading 3D Model...</div>
            <div id="threejs-container"></div>
            
            <div class="controls">
                <h4>🎮 Controls</h4>
                
                <div class="control-group">
                    <button onclick="resetCamera()">🏠 Reset View</button>
                    <button onclick="toggleWireframe()">🔲 Wireframe</button>
                </div>
                
                <div class="control-group">
                    <label>Room Color</label>
                    <input type="color" id="room-color" value="#4a90e2" onchange="updateRoomColor()">
                </div>
                
                <div class="control-group">
                    <label>Wall Color</label>
                    <input type="color" id="wall-color" value="#8b4513" onchange="updateWallColor()">
                </div>
                
                <div class="control-group">
                    <label>Lighting Intensity</label>
                    <input type="range" id="light-intensity" min="0" max="2" step="0.1" value="1" onchange="updateLighting()">
                </div>
                
                <div class="control-group">
                    <button onclick="exportScreenshot()">📸 Screenshot</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/OBJLoader.js"></script>
    
    <script>
        let scene, camera, renderer, controls;
        let roomMaterial, wallMaterial;
        let ambientLight, directionalLight;
        let model;
        
        // OBJ file content embedded
        const objContent = `{obj_content_escaped}`;
        
        function init() {{
            // Create scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x222222);
            
            // Create camera
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(20, 15, 20);
            
            // Create renderer
            renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth - 300, window.innerHeight);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            
            document.getElementById('threejs-container').appendChild(renderer.domElement);
            
            // Create controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            // Create lights
            ambientLight = new THREE.AmbientLight(0x404040, 0.6);
            scene.add(ambientLight);
            
            directionalLight = new THREE.DirectionalLight(0xffffff, 1);
            directionalLight.position.set(10, 10, 5);
            directionalLight.castShadow = true;
            scene.add(directionalLight);
            
            // Create materials
            roomMaterial = new THREE.MeshLambertMaterial({{ color: 0x4a90e2 }});
            wallMaterial = new THREE.MeshLambertMaterial({{ color: 0x8b4513 }});
            
            // Load and parse OBJ
            loadOBJFromContent(objContent);
            
            // Start animation loop
            animate();
            
            // Hide loading
            document.getElementById('loading').style.display = 'none';
        }}
        
        function loadOBJFromContent(content) {{
            const loader = new THREE.OBJLoader();
            model = loader.parse(content);
            
            // Apply materials and calculate stats
            let vertexCount = 0;
            let faceCount = 0;
            
            model.traverse(function(child) {{
                if (child.isMesh) {{
                    // Assign material based on naming convention
                    if (child.name.includes('room') || child.name.includes('floor')) {{
                        child.material = roomMaterial;
                    }} else {{
                        child.material = wallMaterial;
                    }}
                    
                    child.castShadow = true;
                    child.receiveShadow = true;
                    
                    // Count vertices and faces
                    if (child.geometry) {{
                        vertexCount += child.geometry.attributes.position.count;
                        faceCount += child.geometry.index ? child.geometry.index.count / 3 : child.geometry.attributes.position.count / 3;
                    }}
                }}
            }});
            
            // Center and scale the model
            const box = new THREE.Box3().setFromObject(model);
            const center = box.getCenter(new THREE.Vector3());
            model.position.x = -center.x;
            model.position.z = -center.z;
            model.position.y = 0; // Keep on ground
            
            scene.add(model);
            
            // Update stats
            document.getElementById('vertex-count').textContent = vertexCount;
            document.getElementById('face-count').textContent = Math.floor(faceCount);
            
            console.log('Model loaded:', vertexCount, 'vertices,', Math.floor(faceCount), 'faces');
        }}
        
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        
        function resetCamera() {{
            camera.position.set(20, 15, 20);
            controls.reset();
        }}
        
        function toggleWireframe() {{
            if (model) {{
                model.traverse(function(child) {{
                    if (child.isMesh) {{
                        child.material.wireframe = !child.material.wireframe;
                    }}
                }});
            }}
        }}
        
        function updateRoomColor() {{
            const color = document.getElementById('room-color').value;
            roomMaterial.color.setHex(parseInt(color.substring(1), 16));
        }}
        
        function updateWallColor() {{
            const color = document.getElementById('wall-color').value;
            wallMaterial.color.setHex(parseInt(color.substring(1), 16));
        }}
        
        function updateLighting() {{
            const intensity = document.getElementById('light-intensity').value;
            directionalLight.intensity = intensity;
        }}
        
        function exportScreenshot() {{
            const link = document.createElement('a');
            link.download = '{model_name}_screenshot.png';
            link.href = renderer.domElement.toDataURL();
            link.click();
        }}
        
        // Handle window resize
        window.addEventListener('resize', function() {{
            camera.aspect = (window.innerWidth - 300) / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth - 300, window.innerHeight);
        }});
        
        // Initialize when page loads
        window.addEventListener('load', init);
    </script>
</body>
</html>
'''
    
    # Save the viewer
    viewer_path = model_dir.parent / f"{model_name}_interactive_viewer.html"
    with open(viewer_path, 'w') as f:
        f.write(html_content)
    
    return viewer_path

def start_local_server(directory: Path, port: int = 8000):
    """Start a local HTTP server to serve files"""
    os.chdir(directory)
    
    class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET')
            self.send_header('Access-Control-Allow-Headers', '*')
            super().end_headers()
    
    with socketserver.TCPServer(("", port), MyHTTPRequestHandler) as httpd:
        print(f"🌐 Starting server at http://localhost:{port}")
        print(f"📁 Serving directory: {directory}")
        print("Press Ctrl+C to stop the server")
        httpd.serve_forever()

def main():
    """Main function to create viewer and start server"""
    print("🎨 Creating Interactive 3D Viewer...")
    
    # Find the latest model
    output_dir = Path("output/custom_image_testing")
    if not output_dir.exists():
        print("❌ No output directory found. Run the 3D generation first!")
        return
    
    model_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
    if not model_dirs:
        print("❌ No model directories found!")
        return
    
    # Use the first model directory
    model_dir = model_dirs[0]
    model_name = model_dir.name
    
    print(f"📁 Using model: {model_name}")
    
    # Create the interactive viewer
    viewer_path = create_interactive_viewer(
        model_dir, 
        model_name, 
        "../../test_image.jpg"  # Relative path to image
    )
    
    if viewer_path:
        print(f"✅ Interactive viewer created: {viewer_path}")
        
        # Start server in a separate thread
        server_thread = threading.Thread(
            target=start_local_server, 
            args=(output_dir,), 
            daemon=True
        )
        server_thread.start()
        
        # Wait a moment for server to start
        time.sleep(1)
        
        # Open browser
        viewer_url = f"http://localhost:8000/{viewer_path.name}"
        print(f"🚀 Opening viewer: {viewer_url}")
        webbrowser.open(viewer_url)
        
        try:
            # Keep server running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Server stopped.")
    else:
        print("❌ Failed to create viewer")

if __name__ == "__main__":
    main()
