import os
import json
import hashlib
from datetime import datetime

class StorageNode:
    def __init__(self, node_id, address, port, storage_path, capacity):
        self.node_id = node_id
        self.address = address
        self.port = port
        self.storage_path = storage_path
        self.capacity = capacity
        self.used_space = 0
        self.is_active = True
        self.last_heartbeat = datetime.utcnow()
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing files metadata
        self.metadata_file = os.path.join(storage_path, 'metadata.json')
        self.files_metadata = self._load_metadata()
        self._calculate_used_space()
    
    def _load_metadata(self):
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_metadata(self):
        with open(self.metadata_file, 'w') as f:
            json.dump(self.files_metadata, f, indent=2)
    
    def _calculate_used_space(self):
        """Calculate actual disk usage by scanning directory"""
        total = 0
        if os.path.exists(self.storage_path):
            for dirpath, dirnames, filenames in os.walk(self.storage_path):
                for f in filenames:
                    if f == 'metadata.json':
                        continue
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        try:
                            total += os.path.getsize(fp)
                        except:
                            pass
        self.used_space = total
        return total
    
    def get_available_space(self):
        """Get available space"""
        return max(0, self.capacity - self.used_space)
    
    def store_file(self, file_data, user_id):
        """Store a file on this node"""
        filename = file_data.get('filename')
        content = file_data.get('content')
        size = file_data.get('size')
        
        # Check if we have enough space
        if size > self.get_available_space():
            return False, "Insufficient storage space"
        
        # Create user directory
        user_dir = os.path.join(self.storage_path, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(user_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Update metadata
        self.files_metadata[filename] = {
            'user_id': user_id,
            'size': size,
            'stored_at': datetime.utcnow().isoformat(),
            'path': file_path,
            'checksum': self._calculate_checksum(content)
        }
        
        self.used_space += size
        self._save_metadata()
        
        return True, file_path
    
    def _calculate_checksum(self, content):
        """Calculate SHA256 checksum"""
        return hashlib.sha256(content).hexdigest()
    
    def retrieve_file(self, filename, user_id):
        """Retrieve a file from this node"""
        if filename not in self.files_metadata:
            return None
        
        file_info = self.files_metadata[filename]
        if file_info['user_id'] != user_id:
            return None
        
        file_path = file_info.get('path')
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            return {
                'content': content,
                'size': len(content),
                'path': file_path,
                'node_id': self.node_id
            }
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
            return None
    
    def delete_file(self, filename, user_id):
        """Delete a file from this node"""
        if filename not in self.files_metadata:
            return False
        
        file_info = self.files_metadata[filename]
        if file_info['user_id'] != user_id:
            return False
        
        file_path = file_info.get('path')
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                # Remove empty user directory
                user_dir = os.path.dirname(file_path)
                if os.path.exists(user_dir) and not os.listdir(user_dir):
                    os.rmdir(user_dir)
            except Exception as e:
                print(f"Error deleting file {filename}: {e}")
        
        self.used_space -= file_info.get('size', 0)
        del self.files_metadata[filename]
        self._save_metadata()
        
        return True
    
    def check_health(self):
        """Check if node is healthy"""
        try:
            return os.path.exists(self.storage_path)
        except:
            return False
    
    def get_stats(self):
        """Get node statistics"""
        return {
            'node_id': self.node_id,
            'storage_path': self.storage_path,
            'capacity': self.capacity,
            'used_space': self.used_space,
            'available_space': self.get_available_space(),
            'file_count': len(self.files_metadata),
            'is_active': self.is_active,
            'last_heartbeat': self.last_heartbeat.isoformat()
        }
    
    def update_heartbeat(self):
        """Update heartbeat timestamp"""
        self.last_heartbeat = datetime.utcnow()
        self.is_active = True