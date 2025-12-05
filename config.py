class Config:
    SECRET_KEY = 'super-secret-key'
    NODE_COUNT = 5
    STORAGE_PER_NODE = 250 * 1024 * 1024  # 250 MB
    TOTAL_STORAGE = NODE_COUNT * STORAGE_PER_NODE
    REPLICATION = 2          # Each block saved on 2 nodes
    BLOCK_SIZE = 64 * 1024    # 64 KB blocks