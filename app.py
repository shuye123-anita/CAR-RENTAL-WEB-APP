from flask import Flask, render_template, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
import os
import json
import hashlib
from datetime import datetime
from backend.storage_manager import StorageManager
from backend.node_registry import NodeRegistry
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize storage components
storage_manager = StorageManager()
node_registry = NodeRegistry()

# Simple user ID (since no auth, we'll use a default user)
DEFAULT_USER_ID = 1

def initialize_storage_system():
    """Initialize all 5 nodes with actual disk storage"""
    print("Initializing storage nodes...")
    
    # Create base directories
    os.makedirs('node_storage', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    
    # Register all nodes
    for node_config in Config.NODES_CONFIG:
        # Create node storage directory
        os.makedirs(node_config['storage_path'], exist_ok=True)
        
        # Register node
        node_registry.register_node(
            node_id=node_config['id'],
            address=node_config['address'],
            port=node_config['port'],
            storage_path=node_config['storage_path'],
            capacity=Config.NODE_STORAGE_LIMIT
        )
        print(f"Node {node_config['id']} initialized at {node_config['storage_path']}")
    
    print(f"Storage system initialized with {len(Config.NODES_CONFIG)} nodes")
    print(f"Total storage capacity: {Config.TOTAL_STORAGE / (1024*1024*1024):.2f} GB")

# Routes
@app.route('/')
def index():
    """Main page with file manager"""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload file to distributed storage - split into blocks"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read file content
        file_content = file.read()
        file_size = len(file_content)
        
        # Generate unique file ID
        file_hash = hashlib.sha256(file_content).hexdigest()
        file_id = f"file_{file_hash[:16]}_{int(datetime.utcnow().timestamp())}"
        
        print(f"Uploading file: {file.filename} ({file_size} bytes)")
        
        # Store file in distributed storage (split into blocks)
        file_data = {
            'filename': file.filename,
            'content': file_content,
            'size': file_size,
            'mime_type': file.mimetype,
            'file_id': file_id
        }
        
        storage_result = storage_manager.store_file(file_data, DEFAULT_USER_ID)
        
        if not storage_result['success']:
            print(f"Storage failed: {storage_result.get('message')}")
            return jsonify({'error': storage_result.get('message', 'Storage failed')}), 500
        
        print(f"File stored successfully: {storage_result}")
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'filename': file.filename,
            'size': file_size,
            'file_id': file_id,
            'blocks': storage_result.get('blocks', 0),
            'replication': storage_result.get('replication', 1)
        }), 201
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files')
def list_files():
    """List all uploaded files"""
    try:
        # In production, you'd have a database
        # For now, we'll get files from storage manager
        files = storage_manager.get_user_files(DEFAULT_USER_ID)
        
        return jsonify({'files': files})
    except Exception as e:
        print(f"Error listing files: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<file_id>')
def download_file(file_id):
    """Download a file by its ID"""
    try:
        print(f"Downloading file: {file_id}")
        
        file_data = storage_manager.retrieve_file(file_id, DEFAULT_USER_ID)
        
        if not file_data:
            print(f"File not found: {file_id}")
            return jsonify({'error': 'File not found'}), 404
        
        # Get original filename from metadata
        original_name = file_data.get('original_filename', file_id)
        
        # Create temporary file for download
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_name)[1])
        temp_file.write(file_data['content'])
        temp_file.close()
        
        response = send_file(
            temp_file.name,
            as_attachment=True,
            download_name=original_name,
            mimetype=file_data.get('mime_type', 'application/octet-stream')
        )
        
        # Clean up temp file after sending
        import atexit
        def cleanup():
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)
        atexit.register(cleanup)
        
        return response
        
    except Exception as e:
        print(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete a file by its ID"""
    try:
        print(f"Deleting file: {file_id}")
        
        deleted = storage_manager.delete_file(file_id, DEFAULT_USER_ID)
        
        if deleted:
            return jsonify({
                'success': True,
                'message': 'File deleted successfully'
            }), 200
        else:
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        print(f"Delete error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/storage/stats')
def storage_stats():
    """Get storage statistics - shows total available to user"""
    try:
        stats = storage_manager.get_storage_stats(DEFAULT_USER_ID)
        return jsonify(stats)
    except Exception as e:
        print(f"Stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Initialize storage system
initialize_storage_system()

if __name__ == '__main__':
    print("=" * 60)
    print("CLOUD STORAGE SYSTEM")
    print("=" * 60)
    print(f"Total Storage: {Config.TOTAL_STORAGE / (1024**3):.2f} GB")
    print(f"Storage Nodes: {len(Config.NODES_CONFIG)} x {Config.NODE_STORAGE_LIMIT / (1024**2):.0f} MB")
    print(f"Block Size: {storage_manager.block_size / 1024} KB")
    print(f"Replication: {storage_manager.replication_factor}x")
    print("=" * 60)
    print(f"Access URL: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, port=5000, host='0.0.0.0')