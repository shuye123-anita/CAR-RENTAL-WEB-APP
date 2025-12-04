import hashlib
import os
from datetime import datetime

class FileManager:
    @staticmethod
    def calculate_file_hash(file_content):
        """Calculate SHA256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    def get_file_info(file_path):
        """Get file information"""
        if not os.path.exists(file_path):
            return None
        
        stats = os.stat(file_path)
        return {
            'size': stats.st_size,
            'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
            'is_file': os.path.isfile(file_path),
            'is_dir': os.path.isdir(file_path)
        }
    
    @staticmethod
    def format_file_size(size_bytes):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"