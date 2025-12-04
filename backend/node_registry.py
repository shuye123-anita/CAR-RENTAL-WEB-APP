import threading
import time
from datetime import datetime, timedelta
from backend.node import StorageNode

class NodeRegistry:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.nodes = {}
                cls._instance.heartbeat_timeout = 60  # seconds
                cls._instance._start_health_check()
            return cls._instance
    
    def register_node(self, node_id, address, port, storage_path, capacity):
        """Register a new storage node"""
        node = StorageNode(node_id, address, port, storage_path, capacity)
        self.nodes[node_id] = node
        return node
    
    def get_node(self, node_id):
        """Get a specific node by ID"""
        return self.nodes.get(node_id)
    
    def get_active_nodes(self):
        """Get all active nodes"""
        return [node for node in self.nodes.values() if node.is_active]
    
    def get_available_nodes(self):
        """Get nodes that are active and have available space"""
        return [node for node in self.get_active_nodes() if node.get_available_space() > 0]
    
    def update_heartbeat(self, node_id):
        """Update heartbeat for a node"""
        node = self.get_node(node_id)
        if node:
            node.update_heartbeat()
    
    def check_node_health(self, node_id):
        """Check health of a specific node"""
        node = self.get_node(node_id)
        if not node:
            return False
        
        # Check heartbeat
        time_since_heartbeat = datetime.utcnow() - node.last_heartbeat
        if time_since_heartbeat.total_seconds() > self.heartbeat_timeout:
            node.is_active = False
            return False
        
        # Check storage health
        if not node.check_health():
            node.is_active = False
            return False
        
        return True
    
    def _start_health_check(self):
        """Start background health check thread"""
        def health_check_worker():
            while True:
                time.sleep(30)
                self._perform_health_check()
        
        thread = threading.Thread(target=health_check_worker, daemon=True)
        thread.start()
    
    def _perform_health_check(self):
        """Perform health check on all nodes"""
        for node_id in list(self.nodes.keys()):
            try:
                self.check_node_health(node_id)
            except Exception as e:
                print(f"Error checking health of node {node_id}: {e}")