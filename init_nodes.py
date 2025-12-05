import os
import shutil

print("Setting up 5 storage nodes...")

for i in range(1, 6):
    path = f"node_storage/node_{i}"
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)
    print(f"Node {i} ready → {path}")

print("\nAll nodes ready! Total storage: 1.25 GB")
print("Now run: python app.py")