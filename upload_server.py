#!/usr/bin/env python3
"""
Simple HTTP Upload Server for mobile image uploads via QR code
"""

import os
import json
import base64
import logging
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
import tempfile
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path("/home/pi/Desktop/v2_Tripple S")
IMAGE_DIR = BASE_DIR / "BilderVertex"
TRANSCRIPT_JSON = BASE_DIR / "transkript.json"
UPLOAD_PORT = 8000

class UploadHandler(BaseHTTPRequestHandler):
    """HTTP request handler for file uploads"""
    
    def do_GET(self):
        """Handle GET requests - serve upload form"""
        if self.path == '/upload' or self.path == '/':
            self.send_upload_form()
        elif self.path == '/status':
            self.send_status()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests - process uploads"""
        if self.path == '/upload':
            self.handle_upload()
        else:
            self.send_error(404, "Not Found")
    
    def send_upload_form(self):
        """Send HTML upload form"""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Image Upload - ImakeMoney</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        .container { max-width: 500px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .upload-area { border: 2px dashed #ccc; padding: 20px; text-align: center; margin: 20px 0; border-radius: 10px; }
        .upload-area.dragover { border-color: #007cba; background: #f0f8ff; }
        input[type="file"] { margin: 10px 0; }
        button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        button:hover { background: #005a8b; }
        .status { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Image Upload</h1>
        <p>Upload images to be processed with voice recordings</p>
        
        <div class="upload-area" id="uploadArea">
            <p>📁 Drag & drop images here or click to select</p>
            <input type="file" id="fileInput" accept="image/*" multiple style="display: none;">
            <button onclick="document.getElementById('fileInput').click()">Select Images</button>
        </div>
        
        <div id="status"></div>
        
        <form id="uploadForm" style="display: none;">
            <input type="file" id="imageFile" name="image" accept="image/*" multiple>
        </form>
    </div>

    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const status = document.getElementById('status');
        
        // Drag and drop handlers
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            handleFiles(files);
        });
        
        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });
        
        function handleFiles(files) {
            for (let file of files) {
                if (file.type.startsWith('image/')) {
                    uploadFile(file);
                } else {
                    showStatus('Error: Only image files are allowed', 'error');
                }
            }
        }
        
        function uploadFile(file) {
            const formData = new FormData();
            formData.append('image', file);
            
            showStatus(`Uploading ${file.name}...`, 'info');
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus(`✓ ${file.name} uploaded successfully`, 'success');
                } else {
                    showStatus(`✗ Upload failed: ${data.error}`, 'error');
                }
            })
            .catch(error => {
                showStatus(`✗ Upload error: ${error}`, 'error');
            });
        }
        
        function showStatus(message, type) {
            const statusDiv = document.createElement('div');
            statusDiv.className = `status ${type}`;
            statusDiv.textContent = message;
            status.appendChild(statusDiv);
            
            // Remove after 5 seconds
            setTimeout(() => {
                if (statusDiv.parentNode) {
                    statusDiv.parentNode.removeChild(statusDiv);
                }
            }, 5000);
        }
    </script>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_status(self):
        """Send server status"""
        status = {
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "upload_dir": str(IMAGE_DIR),
            "server": "ImakeMoney Upload Server"
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(status).encode())
    
    def handle_upload(self):
        """Handle file upload"""
        try:
            # Parse content length
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_json_response({"success": False, "error": "No content"}, 400)
                return
            
            # Read post data
            post_data = self.rfile.read(content_length)
            
            # Use cgi module for multipart parsing
            import cgi
            import io
            
            # Create environment for cgi parsing
            environ = {
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': self.headers.get('Content-Type', ''),
                'CONTENT_LENGTH': str(content_length),
            }
            
            # Create file-like object for post data
            fp = io.BytesIO(post_data)
            
            # Parse multipart data
            form = cgi.FieldStorage(
                fp=fp,
                environ=environ,
                headers=self.headers
            )
            
            # Look for image field
            if 'image' in form:
                file_item = form['image']
                if file_item.filename:
                    # Get image data and filename
                    filename = file_item.filename
                    image_data = file_item.file.read()
                    
                    # Save uploaded file
                    success = self.save_uploaded_image(filename, image_data)
                    if success:
                        self.send_json_response({"success": True, "filename": filename})
                        return
                    else:
                        self.send_json_response({"success": False, "error": "Failed to save image"}, 500)
                        return
            
            self.send_json_response({"success": False, "error": "No valid image found"}, 400)
            
        except Exception as e:
            logger.error(f"Upload error: {e}")
            self.send_json_response({"success": False, "error": str(e)}, 500)
    
    def save_uploaded_image(self, filename, image_data):
        """Save uploaded image and add to transcript.json"""
        try:
            # Ensure directories exist
            IMAGE_DIR.mkdir(parents=True, exist_ok=True)
            BASE_DIR.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_part, ext = os.path.splitext(filename)
            safe_filename = f"upload_{timestamp}_{name_part}{ext}"
            file_path = IMAGE_DIR / safe_filename
            
            # Write image file
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"Saved uploaded image: {file_path}")
            
            # Convert to base64 for transcript.json
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Update or create transcript.json
            transcript_data = {
                "transcript": "Image uploaded via mobile device",
                "timestamp": datetime.now().timestamp(),
                "iso_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "processing_method": "mobile_upload",
                "workflow_step": "image_upload_complete",
                "image_base64": image_base64,
                "image_filename": safe_filename,
                "image_timestamp": timestamp
            }
            
            # Load existing transcript if available
            if TRANSCRIPT_JSON.exists():
                try:
                    with open(TRANSCRIPT_JSON, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    # Merge with existing data, prioritizing new image
                    transcript_data.update(existing_data)
                    transcript_data["image_base64"] = image_base64
                    transcript_data["image_filename"] = safe_filename
                    transcript_data["image_timestamp"] = timestamp
                except Exception as e:
                    logger.warning(f"Could not load existing transcript: {e}")
            
            # Save updated transcript
            with open(TRANSCRIPT_JSON, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Updated transcript.json with uploaded image: {safe_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving uploaded image: {e}")
            return False
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.client_address[0]} - {format % args}")

def start_upload_server(port=UPLOAD_PORT):
    """Start the upload server"""
    try:
        server = HTTPServer(('0.0.0.0', port), UploadHandler)
        logger.info(f"Upload server starting on port {port}")
        logger.info(f"Upload URL: http://localhost:{port}/upload")
        logger.info(f"Image directory: {IMAGE_DIR}")
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

def start_server_thread(port=UPLOAD_PORT):
    """Start server in background thread"""
    server_thread = threading.Thread(target=start_upload_server, args=(port,))
    server_thread.daemon = True
    server_thread.start()
    return server_thread

if __name__ == "__main__":
    start_upload_server()