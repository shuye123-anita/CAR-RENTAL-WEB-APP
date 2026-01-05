import os
import shutil

print("Setting up 5 storage nodes (500 MB each)...")
print("=" * 60)

for i in range(1, 6):
    path = f"node_storage/node_{i}"
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)
    print(f"Node {i} ready → {path}")

print("\n" + "=" * 60)
print("All 5 nodes ready! Total simulated storage: 2.5 GB")
print("Now run: python app.py")