import os
from dotenv import load_dotenv
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

load_dotenv()

class Config:
    # Secret key for session management
    SECRET_KEY = os.getenv('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # SQLite Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or f'sqlite:///{BASE_DIR}/car_rental.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Storage Configuration
    BLOCK_SIZE = 64 * 1024  # 64KB blocks
    REPLICATION = 2  # Each block stored on 2 nodes
    TOTAL_STORAGE = 5 * 250 * 1024 * 1024  # 1.25 GB (5 nodes × 250MB each)
    
    # File upload settings
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    UPLOAD_FOLDER = 'node_storage'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}