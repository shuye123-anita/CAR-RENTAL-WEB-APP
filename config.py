import os
from datetime import timedelta

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///cloud_storage.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Storage Configuration
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip'}
    
    # Node Configuration - 5 nodes x 250MB = 1.25GB total
    NODE_COUNT = 5
    NODE_STORAGE_LIMIT = 250 * 1024 * 1024  # 250MB per node
    TOTAL_STORAGE = NODE_COUNT * NODE_STORAGE_LIMIT  # 1.25GB total
    MIN_REPLICATION_FACTOR = 2
    HEARTBEAT_INTERVAL = 30  # seconds
    
    # Node IPs and Ports
    NODES_CONFIG = [
        {'id': 'node_1', 'address': '127.0.0.1', 'port': 5001, 'storage_path': 'node_storage/node_1'},
        {'id': 'node_2', 'address': '127.0.0.1', 'port': 5002, 'storage_path': 'node_storage/node_2'},
        {'id': 'node_3', 'address': '127.0.0.1', 'port': 5003, 'storage_path': 'node_storage/node_3'},
        {'id': 'node_4', 'address': '127.0.0.1', 'port': 5004, 'storage_path': 'node_storage/node_4'},
        {'id': 'node_5', 'address': '127.0.0.1', 'port': 5005, 'storage_path': 'node_storage/node_5'}
    ]
    
    # Security
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    # CORS
    CORS_HEADERS = 'Content-Type'