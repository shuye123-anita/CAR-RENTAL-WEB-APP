
"""
Initialize the storage nodes with proper disk space allocation
"""

import os
import sys
import shutil

# Add the project root to the path
sys.path.append('.')

from config import Config

def initialize_nodes():
    """Initialize all storage nodes"""
    print("Initializing Distributed Storage Nodes")
    print("="*50)
    
    # Clean up any existing storage
    for node_config in Config.NODES_CONFIG:
        storage_path = node_config['storage_path']
        
        # Remove if exists
        if os.path.exists(storage_path):
            shutil.rmtree(storage_path)
            print(f"Cleaned up existing node storage: {storage_path}")
        
        # Create fresh directory
        os.makedirs(storage_path, exist_ok=True)
        
        # Create subdirectories
        for user_id in ['1', '2', '3']:
            user_dir = os.path.join(storage_path, user_id)
            os.makedirs(user_dir, exist_ok=True)
        
        print(f"✓ Node {node_config['id']} initialized at {storage_path}")
    
    # Calculate total storage
    total_storage = Config.TOTAL_STORAGE
    per_node = Config.NODE_STORAGE_LIMIT
    
    print(f"\nStorage Configuration:")
    print(f"  Number of nodes: {Config.NODE_COUNT}")
    print(f"  Storage per node: {per_node/(1024*1024):.0f} MB")
    print(f"  Total storage: {total_storage/(1024*1024*1024):.2f} GB")
    print(f"  Replication factor: 2x (each block stored on 2 nodes)")
    
    # Create a test file to show it's working
    test_file = os.path.join('node_storage', 'README.txt')
    with open(test_file, 'w') as f:
        f.write("Distributed Cloud Storage System\n")
        f.write("="*40 + "\n\n")
        f.write(f"Total Nodes: {Config.NODE_COUNT}\n")
        f.write(f"Total Storage: {total_storage/(1024*1024*1024):.2f} GB\n")
        f.write(f"Block Size: 64 KB\n")
        f.write(f"Replication: 2x\n\n")
        f.write("Files are automatically split into blocks and distributed\n")
        f.write("across all available nodes for high availability.\n")
    
    print(f"\n✓ Storage system initialized successfully!")
    print(f"\nTo start the system:")
    print(f"  1. Run: python app.py")
    print(f"  2. Open: http://localhost:5000")
    print(f"  3. Upload files up to 100MB")

if __name__ == "__main__":
    initialize_nodes()
