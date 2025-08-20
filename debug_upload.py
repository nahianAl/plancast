#!/usr/bin/env python3
"""
Debug Upload - Minimal version to isolate upload issues
"""

import os
from flask import Flask, render_template_string, request, jsonify
from werkzeug.utils import secure_filename
import threading
import webbrowser

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'temp/debug_uploads'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Debug Upload Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f0f0f0;
        }
        
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .upload-area {
            border: 3px dashed #ccc;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            margin: 20px 0;
            transition: all 0.3s ease;
            cursor: pointer;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .upload-area:hover {
            border-color: #007bff;
            background: #f8f9ff;
        }
        
        .upload-area.dragover {
            border-color: #007bff;
            background: #e8f0ff;
        }
        
        .upload-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }
        
        .file-input {
            display: none;
        }
        
        .manual-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            margin: 10px;
        }
        
        .manual-btn:hover {
            background: #0056b3;
        }
        
        .status {
            margin: 20px 0;
            padding: 15px;
            border-radius: 8px;
            background: #f8f9fa;
            border-left: 4px solid #007bff;
        }
        
        .error {
            background: #f8d7da;
            border-left-color: #dc3545;
            color: #721c24;
        }
        
        .success {
            background: #d4edda;
            border-left-color: #28a745;
            color: #155724;
        }
        
        .debug-log {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            font-family: monospace;
            font-size: 12px;
            max-height: 200px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🐛 Debug Upload Test</h1>
        <p>Testing file upload functionality with extensive logging</p>
        
        <div class="upload-area" id="uploadArea">
            <div class="upload-icon">📁</div>
            <p><strong>Click here to upload</strong></p>
            <p>or drag and drop a file</p>
            <p><small>Supports: JPG, PNG, PDF (max 16MB)</small></p>
        </div>
        
        <input type="file" id="fileInput" class="file-input" accept=".jpg,.jpeg,.png,.pdf">
        
        <div style="text-align: center;">
            <button type="button" class="manual-btn" id="manualBtn">
                📂 Choose File Manually
            </button>
        </div>
        
        <div id="status" class="status">
            <strong>Status:</strong> <span id="statusText">Ready</span>
        </div>
        
        <div class="debug-log" id="debugLog">
            <strong>Debug Log:</strong><br>
            <div id="logContent">Waiting for events...</div>
        </div>
    </div>

    <script>
        // Debug logging function
        function log(message) {
            const logContent = document.getElementById('logContent');
            const timestamp = new Date().toLocaleTimeString();
            logContent.innerHTML += `[${timestamp}] ${message}<br>`;
            logContent.scrollTop = logContent.scrollHeight;
            console.log(`[${timestamp}] ${message}`);
        }
        
        log('Script loaded and initialized');
        
        // Get DOM elements
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const manualBtn = document.getElementById('manualBtn');
        const status = document.getElementById('status');
        const statusText = document.getElementById('statusText');
        
        let currentFile = null;
        
        // Show status
        function showStatus(message, type = 'info') {
            statusText.textContent = message;
            status.className = 'status';
            if (type === 'error') status.classList.add('error');
            if (type === 'success') status.classList.add('success');
            log(`Status: ${message} (${type})`);
        }
        
        // Prevent default drag behaviors on entire document
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            document.addEventListener(eventName, preventDefaults, false);
            log(`Document event listener added: ${eventName}`);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
            log(`Document event prevented: ${e.type}`);
        }
        
        // Upload area click
        uploadArea.addEventListener('click', (e) => {
            e.preventDefault();
            log('Upload area clicked - triggering file input');
            fileInput.click();
        });
        
        // Manual button click
        manualBtn.addEventListener('click', (e) => {
            e.preventDefault();
            log('Manual button clicked - triggering file input');
            fileInput.click();
        });
        
        // File input events
        fileInput.addEventListener('focus', (e) => {
            log('File input focused');
        });
        
        fileInput.addEventListener('click', (e) => {
            log('File input clicked');
        });
        
        fileInput.addEventListener('change', (e) => {
            log(`File input changed - files: ${e.target.files.length}`);
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });
        
        // Drag and drop for upload area
        uploadArea.addEventListener('dragenter', (e) => {
            log('Upload area dragenter');
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragover', (e) => {
            log('Upload area dragover');
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', (e) => {
            log('Upload area dragleave');
            if (!uploadArea.contains(e.relatedTarget)) {
                uploadArea.classList.remove('dragover');
            }
        });
        
        uploadArea.addEventListener('drop', (e) => {
            log('Upload area drop');
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            log(`Files dropped: ${files.length}`);
            
            if (files.length > 0) {
                handleFileSelect(files[0]);
            }
        });
        
        function handleFileSelect(file) {
            try {
                log(`Handling file: ${file.name} (${file.size} bytes, type: ${file.type})`);
                
                if (!file) {
                    showError('No file provided');
                    return;
                }
                
                if (file.size > 16 * 1024 * 1024) {
                    showError('File too large! Maximum size is 16MB.');
                    return;
                }
                
                // Validate file type
                const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
                const fileExtension = file.name.toLowerCase().split('.').pop();
                const allowedExtensions = ['jpg', 'jpeg', 'png', 'pdf'];
                
                log(`File validation - MIME type: ${file.type}, extension: ${fileExtension}`);
                
                if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
                    showError('Invalid file type! Please use JPG, PNG, or PDF files.');
                    return;
                }
                
                currentFile = file;
                
                // Update upload area
                uploadArea.innerHTML = `
                    <div class="upload-icon">✅</div>
                    <p><strong>${file.name}</strong></p>
                    <p>Size: ${(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    <p>Click to change file</p>
                `;
                
                showStatus('File ready for upload!', 'success');
                
                // Test upload
                testUpload(file);
                
            } catch (error) {
                log(`Error handling file: ${error.message}`);
                showError('Error handling file: ' + error.message);
            }
        }
        
        async function testUpload(file) {
            try {
                log('Starting upload test...');
                showStatus('Testing upload to server...', 'info');
                
                const formData = new FormData();
                formData.append('test_file', file);
                
                log('FormData created, sending request...');
                
                const response = await fetch('/test_upload', {
                    method: 'POST',
                    body: formData
                });
                
                log(`Response received: ${response.status} ${response.statusText}`);
                
                const result = await response.json();
                log(`Response JSON: ${JSON.stringify(result)}`);
                
                if (response.ok) {
                    showStatus(`Upload test successful! Server received: ${result.filename}`, 'success');
                } else {
                    showStatus(`Upload test failed: ${result.error}`, 'error');
                }
                
            } catch (error) {
                log(`Upload test error: ${error.message}`);
                showStatus(`Upload test failed: ${error.message}`, 'error');
            }
        }
        
        function showError(message) {
            showStatus(message, 'error');
        }
        
        // Initialize
        log('Initializing debug upload test...');
        showStatus('Ready - Click or drag to upload a file', 'info');
        log('Debug upload test ready');
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/test_upload', methods=['POST'])
def test_upload():
    """Test file upload"""
    try:
        print("📁 Upload test request received")
        print(f"📋 Request method: {request.method}")
        print(f"📋 Request headers: {dict(request.headers)}")
        print(f"📁 Files: {list(request.files.keys())}")
        print(f"📋 Form data: {list(request.form.keys())}")
        
        if 'test_file' not in request.files:
            print("❌ No test_file in request.files")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['test_file']
        print(f"📸 File object: {file}")
        print(f"📸 Filename: {file.filename}")
        print(f"📸 Content type: {file.content_type if hasattr(file, 'content_type') else 'unknown'}")
        
        if file.filename == '':
            print("❌ Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        print(f"💾 Saving file to: {filepath}")
        file.save(filepath)
        
        # Get file info
        file_size = os.path.getsize(filepath)
        
        print(f"✅ File saved: {filename} ({file_size} bytes)")
        print(f"✅ File path: {filepath}")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'size': file_size,
            'path': filepath
        })
        
    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def start_server(port=8003):
    """Start the debug server"""
    print(f"🐛 Starting Debug Upload Test Server...")
    print(f"🌐 Open your browser to: http://localhost:{port}")
    print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print("\n" + "="*50)
    print("🔍 This is a DEBUG version to isolate upload issues")
    print("📝 Check the debug log in the browser console")
    print("📝 Check the server console for detailed logs")
    print("="*50 + "\n")
    
    # Open browser automatically
    threading.Timer(1.5, lambda: webbrowser.open(f'http://localhost:{port}')).start()
    
    # Start server
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

if __name__ == '__main__':
    start_server()
