from flask import Flask, request, jsonify, send_file, render_template
import os, hashlib, json, random, time, io
from config import Config

app = Flask(__name__)
USER_ID = 1

# Fallbacks for configuration values that may not exist in Config
BLOCK_SIZE = getattr(Config, 'BLOCK_SIZE', 64 * 1024)
REPLICATION = getattr(Config, 'REPLICATION', getattr(Config, 'MIN_REPLICATION_FACTOR', 2))

def get_nodes():
    return [f"node_storage/node_{i}" for i in range(1, 6)]

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/upload', methods=['POST'])
def upload():
    file = request.files['file']
    data = file.read()
    name = file.filename
    size = len(data)
    file_id = hashlib.md5(data + str(time.time()).encode()).hexdigest()

    # Split into blocks
    blocks = []
    for i in range(0, size, Config.BLOCK_SIZE):
        block = data[i:i+Config.BLOCK_SIZE]
        block_id = f"{file_id}_{i//Config.BLOCK_SIZE}"
        blocks.append((block_id, block))

    # Save blocks with replication
    nodes = get_nodes()
    for block_id, block_data in blocks:
        chosen = random.sample(nodes, REPLICATION)
        for node_path in chosen:
            # ensure node directory exists
            os.makedirs(node_path, exist_ok=True)
            path = os.path.join(node_path, f"{block_id}.blk")
            with open(path, 'wb') as fh:
                fh.write(block_data)

    # Save manifest
    manifest = {
        "id": file_id,
        "name": name,
        "size": size,
        "blocks": len(blocks),
        "uploaded": time.time()
    }
    for node in nodes:
        os.makedirs(node, exist_ok=True)
        with open(os.path.join(node, f"{file_id}.json"), 'w') as fh:
            json.dump(manifest, fh)

    return jsonify({"success": True})

@app.route('/api/files')
def files():
    files = []
    seen = set()
    for node in get_nodes():
        if not os.path.exists(node):
            continue
        for fname in os.listdir(node):
            if not fname.endswith('.json'):
                continue
            try:
                with open(os.path.join(node, fname), 'r') as fh:
                    data = json.load(fh)
            except Exception:
                continue
            if data.get('id') not in seen:
                seen.add(data.get('id'))
                files.append({
                    "id": data.get('id'),
                    "name": data.get('name'),
                    "size": data.get('size'),
                    "uploaded": data.get('uploaded') * 1000
                })
    return jsonify({"files": files})

@app.route('/api/download/<file_id>')
def download(file_id):
    # Find manifest
    manifest = None
    for node in get_nodes():
        path = f"{node}/{file_id}.json"
        if os.path.exists(path):
            manifest = json.load(open(path))
            break
    if not manifest: return "Not found", 404

    # Rebuild file
    content = bytearray()
    for i in range(manifest.get('blocks', 0)):
        block_id = f"{file_id}_{i}"
        found = False
        for node in get_nodes():
            path = os.path.join(node, f"{block_id}.blk")
            if os.path.exists(path):
                with open(path, 'rb') as fh:
                    content.extend(fh.read())
                found = True
                break
        if not found:
            return jsonify({'error': f'Missing block {i}'}), 500

    return send_file(
        io.BytesIO(bytes(content)),
        as_attachment=True,
        download_name=manifest.get('name', 'download')
    )

@app.route('/api/delete/<file_id>', methods=['DELETE'])
def delete(file_id):
    for node in get_nodes():
        if not os.path.exists(node):
            continue
        for fname in os.listdir(node):
            if fname.startswith(file_id):
                try:
                    os.remove(os.path.join(node, fname))
                except Exception:
                    pass
    return jsonify({"success": True})
@app.route('/api/stats')
def stats():
    total = 0
    for node in get_nodes():
        for f in os.listdir(node):
            if f.endswith('.json'):
                try:
                    data = json.load(open(f"{node}/{f}"))
                    total += data['size']
                except:
                    pass
    percent = (total / Config.TOTAL_STORAGE) * 100
    return jsonify({
        "used": total,
        "total": Config.TOTAL_STORAGE,
        "percent": round(percent, 1)
    })

if __name__ == '__main__':
    os.makedirs("node_storage", exist_ok=True)
    print("MyCloud Ready → http://127.0.0.1:5000")
    app.run(debug=True)