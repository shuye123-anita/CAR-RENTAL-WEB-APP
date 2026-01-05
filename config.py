# config.py - Full modified version

import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or f'sqlite:///{BASE_DIR}/car_rental.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    BLOCK_SIZE = 64 * 1024  # 64KB blocks
    REPLICATION = 2
    NODE_COUNT = 5
    NODE_CAPACITY = 500 * 1024 * 1024  # 500 MB per node
    TOTAL_STORAGE = NODE_COUNT * NODE_CAPACITY  # 2.5 GB total
    
    # Very high per-file limit (2 GB) - we will check total remaining space instead
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2 GB
    
    UPLOAD_FOLDER = 'node_storage'
    
    # Allow ALL file types
    ALLOWED_EXTENSIONS = set()  # Empty set = no restriction