import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///cloud.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    BLOCK_SIZE = 64 * 1024
    REPLICATION = 2
    TOTAL_STORAGE = 5 * 250 * 1024 * 1024  # 1.25 GB