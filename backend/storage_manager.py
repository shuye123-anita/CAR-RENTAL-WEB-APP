import os
import hashlib
import json
from datetime import datetime
from backend.node_registry import NodeRegistry

class StorageManager:
    def __init__(self):
        self.node_registry = NodeRegistry()
        self.replication_factor = 2  # Store 2 copies of each block
        self.block_size = 64 * 1024  # 64KB blocks
        self.metadata_file = 'file_metadata.json'
        self.load_metadata()
    
    def load_metadata(self):
        """Load file metadata from disk"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except:
                self.metadata = {'files': {}, 'users': {}}
        else:
            self.metadata = {'files': {}, 'users': {}}
    
    def save_metadata(self):
        """Save file metadata to disk"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def store_file(self, file_data, user_id):
        """Split file into blocks and distribute across nodes"""
        original_filename = file_data['filename']
        file_content = file_data['content']
        file_size = len(file_content)
        file_id = file_data.get('file_id', f"file_{hashlib.md5(file_content).hexdigest()[:16]}")
        
        print(f"Storing file {original_filename} ({file_size} bytes) with ID: {file_id}")
        
        # Check available space
        available_space = self.get_available_space()
        if file_size > available_space:
            return {
                'success': False,
                'message': f'Insufficient space. Available: {self.format_size(available_space)}, Needed: {self.format_size(file_size)}'
            }
        
        # Split file into blocks
        blocks = []
        for i in range(0, file_size, self.block_size):
            block_content = file_content[i:i + self.block_size]
            block_hash = hashlib.sha256(block_content).hexdigest()
            block_id = f"{file_id}_block_{i//self.block_size}"
            blocks.append({
                'id': block_id,
                'content': block_content,
                'size': len(block_content),
                'hash': block_hash
            })
        
        print(f"Split into {len(blocks)} blocks")
        
        # Distribute blocks across nodes
        block_placements = []
        successful_blocks = 0
        
        for block in blocks:
            placed = self._store_block(block, user_id)
            if placed:
                block_placements.append({
                    'block_id': block['id'],
                    'nodes': placed['nodes']
                })
                successful_blocks += 1
            else:
                print(f"Failed to store block {block['id']}")
        
        # If all blocks stored successfully, save metadata
        if successful_blocks == len(blocks):
            # Save file metadata
            if 'files' not in self.metadata:
                self.metadata['files'] = {}
            
            self.metadata['files'][file_id] = {
                'original_filename': original_filename,
                'size': file_size,
                'blocks': len(blocks),
                'block_ids': [b['id'] for b in blocks],
                'user_id': user_id,
                'uploaded_at': datetime.utcnow().isoformat(),
                'mime_type': file_data.get('mime_type', 'application/octet-stream'),
                'hash': hashlib.sha256(file_content).hexdigest()
            }
            
            # Update user storage
            if str(user_id) not in self.metadata['users']:
                self.metadata['users'][str(user_id)] = {'used': 0, 'files': []}
            
            self.metadata['users'][str(user_id)]['used'] += file_size
            self.metadata['users'][str(user_id)]['files'].append(file_id)
            
            self.save_metadata()
            
            return {
                'success': True,
                'file_id': file_id,
                'blocks': len(blocks),
                'replication': self.replication_factor,
                'message': f'File stored successfully across {successful_blocks} blocks'
            }
        else:
            # Clean up any stored blocks
            for block in blocks:
                self._delete_block(block['id'], user_id)
            
            return {
                'success': False,
                'message': f'Failed to store all blocks. Stored {successful_blocks}/{len(blocks)}'
            }
    
    def _store_block(self, block, user_id):
        """Store a single block with replication"""
        block_id = block['id']
        block_content = block['content']
        block_size = block['size']
        
        # Get available nodes
        nodes = self.node_registry.get_active_nodes()
        suitable_nodes = []
        
        for node in nodes:
            if node.is_active and node.get_available_space() >= block_size:
                suitable_nodes.append(node)
        
        if len(suitable_nodes) < self.replication_factor:
            print(f"Not enough nodes for block {block_id}. Need {self.replication_factor}, have {len(suitable_nodes)}")
            return None
        
        # Sort by available space
        suitable_nodes.sort(key=lambda x: x.get_available_space(), reverse=True)
        
        # Select nodes for replication
        selected_nodes = suitable_nodes[:self.replication_factor]
        stored_nodes = []
        
        for node in selected_nodes:
            # Create block filename
            block_filename = f"{block_id}.block"
            
            # Store on node
            success, result = node.store_file({
                'filename': block_filename,
                'content': block_content,
                'size': block_size
            }, user_id)
            
            if success:
                stored_nodes.append(node.node_id)
            else:
                print(f"Failed to store block {block_id} on node {node.node_id}: {result}")
        
        if len(stored_nodes) >= 1:  # At least one copy
            return {
                'block_id': block_id,
                'nodes': stored_nodes,
                'replication': len(stored_nodes)
            }
        
        return None
    
    def _delete_block(self, block_id, user_id):
        """Delete a block from all nodes"""
        nodes = self.node_registry.get_active_nodes()
        deleted_count = 0
        
        for node in nodes:
            if node.is_active:
                if node.delete_file(f"{block_id}.block", user_id):
                    deleted_count += 1
        
        return deleted_count > 0
    
    def retrieve_file(self, file_id, user_id):
        """Retrieve file by reconstructing from blocks"""
        # Get file metadata
        if file_id not in self.metadata.get('files', {}):
            return None
        
        file_info = self.metadata['files'][file_id]
        if file_info['user_id'] != user_id:
            return None
        
        # Retrieve all blocks
        blocks_content = []
        for block_id in file_info['block_ids']:
            block_data = self._retrieve_block(block_id, user_id)
            if block_data:
                blocks_content.append(block_data['content'])
            else:
                print(f"Warning: Block {block_id} not found")
                return None
        
        # Reconstruct file
        file_content = b''.join(blocks_content)
        
        # Verify file hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        if file_hash != file_info.get('hash', ''):
            print(f"Warning: File hash mismatch for {file_id}")
        
        return {
            'content': file_content,
            'original_filename': file_info['original_filename'],
            'size': file_info['size'],
            'mime_type': file_info.get('mime_type', 'application/octet-stream')
        }
    
    def _retrieve_block(self, block_id, user_id):
        """Retrieve a block from any node"""
        nodes = self.node_registry.get_active_nodes()
        
        for node in nodes:
            if node.is_active:
                block_data = node.retrieve_file(f"{block_id}.block", user_id)
                if block_data:
                    return block_data
        
        return None
    
    def delete_file(self, file_id, user_id):
        """Delete file by removing all its blocks"""
        if file_id not in self.metadata.get('files', {}):
            return False
        
        file_info = self.metadata['files'][file_id]
        if file_info['user_id'] != user_id:
            return False
        
        # Delete all blocks
        success_count = 0
        for block_id in file_info['block_ids']:
            if self._delete_block(block_id, user_id):
                success_count += 1
        
        # Update metadata
        if success_count > 0:
            # Update user storage
            user_key = str(user_id)
            if user_key in self.metadata['users']:
                self.metadata['users'][user_key]['used'] -= file_info['size']
                if file_id in self.metadata['users'][user_key]['files']:
                    self.metadata['users'][user_key]['files'].remove(file_id)
            
            # Remove file metadata
            del self.metadata['files'][file_id]
            self.save_metadata()
            
            return True
        
        return False
    
    def get_user_files(self, user_id):
        """Get all files for a user"""
        files = []
        
        for file_id, file_info in self.metadata.get('files', {}).items():
            if file_info['user_id'] == user_id:
                files.append({
                    'id': file_id,
                    'filename': file_info['original_filename'],
                    'size': file_info['size'],
                    'uploaded_at': file_info['uploaded_at'],
                    'blocks': file_info['blocks'],
                    'mime_type': file_info.get('mime_type', 'application/octet-stream')
                })
        
        return files
    
    def get_storage_stats(self, user_id):
        """Get storage statistics for user"""
        nodes = self.node_registry.get_active_nodes()
        
        total_capacity = sum(node.capacity for node in nodes)
        total_used = sum(node.used_space for node in nodes)
        total_available = total_capacity - total_used
        
        # Get user's used space
        user_used = 0
        user_key = str(user_id)
        if user_key in self.metadata.get('users', {}):
            user_used = self.metadata['users'][user_key].get('used', 0)
        
        # Calculate user's available space (can use all available space)
        user_available = total_available
        
        return {
            'total': total_capacity,
            'used': total_used,
            'available': total_available,
            'user_used': user_used,
            'user_available': user_available,
            'files_count': len(self.metadata.get('files', {})),
            'nodes_count': len(nodes),
            'block_size_kb': self.block_size / 1024,
            'replication': self.replication_factor,
            'total_gb': f"{total_capacity / (1024**3):.2f} GB",
            'used_gb': f"{total_used / (1024**3):.2f} GB",
            'available_gb': f"{total_available / (1024**3):.2f} GB",
            'user_used_gb': f"{user_used / (1024**3):.2f} GB",
            'user_available_gb': f"{user_available / (1024**3):.2f} GB",
            'usage_percent': (total_used / total_capacity * 100) if total_capacity > 0 else 0,
            'user_usage_percent': (user_used / (user_used + user_available) * 100) if (user_used + user_available) > 0 else 0
        }
    
    def get_available_space(self):
        """Get total available space across all nodes"""
        nodes = self.node_registry.get_active_nodes()
        return sum(node.get_available_space() for node in nodes)
    
    def format_size(self, bytes):
        """Format bytes to human readable string"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"
    
    def check_system_health(self):
        """Check system health and rebalance if needed"""
        nodes = self.node_registry.get_active_nodes()
        
        # Check if any node is almost full
        for node in nodes:
            usage = (node.used_space / node.capacity * 100) if node.capacity > 0 else 0
            if usage > 90:
                print(f"Warning: Node {node.node_id} is {usage:.1f}% full")
                # In production, you'd trigger rebalancing here
        
        return {
            'healthy_nodes': len([n for n in nodes if n.is_active]),
            'total_nodes': len(nodes),
            'total_space': self.get_available_space()
        }