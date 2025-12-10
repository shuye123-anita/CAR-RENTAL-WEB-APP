# app.py - Modified to use '127.0.0.1' for gRPC connection
from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User
from config import Config
import os, hashlib, json, random, time, io
from dotenv import load_dotenv
import grpc
import auth_pb2
import auth_pb2_grpc

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# gRPC Client - Changed to '127.0.0.1'
channel = grpc.insecure_channel('127.0.0.1:50051')
stub = auth_pb2_grpc.AuthServiceStub(channel)

# Create DB & nodes
with app.app_context():
    db.create_all()
    os.makedirs("node_storage", exist_ok=True)
    for i in range(1, 6):
        os.makedirs(f"node_storage/node_{i}", exist_ok=True)

BLOCK_SIZE = getattr(Config, 'BLOCK_SIZE', 64 * 1024)
REPLICATION = getattr(Config, 'REPLICATION', 2)

def get_nodes():
    return [f"node_storage/node_{i}" for i in range(1, 6)]

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('login')) if not current_user.is_authenticated else redirect(url_for('dashboard'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        req = auth_pb2.SignupRequest(
            name=request.form['name'],
            username=request.form['username'],
            email=request.form['email'],
            password=request.form['password']
        )
        try:
            resp = stub.Signup(req, timeout=10)
            if resp.success:
                flash("Account created! Please login.", "success")
                return redirect(url_for('login'))
            else:
                flash(resp.message, "error")
        except grpc.RpcError:
            flash("Authentication service unavailable", "error")
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        req = auth_pb2.LoginRequest(
            username=request.form['username'],
            password=request.form['password']
        )
        try:
            resp = stub.Login(req, timeout=10)
            if resp.success:
                flash("OTP sent to your email!", "success")
                return redirect(url_for('verify_otp', user_id=resp.user_id))
            else:
                flash(resp.message, "error")
        except grpc.RpcError:
            flash("Auth service down. Try again later.", "error")
    return render_template('login.html')

@app.route('/verify-otp/<int:user_id>', methods=['GET', 'POST'])
def verify_otp(user_id):
    if request.method == 'POST':
        req = auth_pb2.VerifyOTPRequest(user_id=user_id, otp=request.form['otp'])
        try:
            resp = stub.VerifyOTP(req, timeout=10)
            if resp.success:
                user = User.query.get(user_id)
                if user:
                    login_user(user)
                    session['grpc_token'] = resp.session_token
                    return redirect(url_for('dashboard'))
                else:
                    flash("User not found", "error")
            else:
                flash(resp.message, "error")
        except grpc.RpcError:
            flash("Auth service error", "error")

    user = User.query.get(user_id)
    return render_template('verify_otp.html', name=user.name if user else "User")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

# === STORAGE APIs (UNCHANGED) ===
@app.route('/api/upload', methods=['POST'])
@login_required
def upload():
    file = request.files['file']
    data = file.read()
    name = file.filename
    size = len(data)
    file_id = hashlib.sha256(data + str(time.time()).encode()).hexdigest()[:16]

    blocks = []
    for i in range(0, size, BLOCK_SIZE):
        block = data[i:i+BLOCK_SIZE]
        block_id = f"{file_id}_{i//BLOCK_SIZE}"
        blocks.append((block_id, block))

    nodes = get_nodes()
    for block_id, block_data in blocks:
        chosen = random.sample(nodes, REPLICATION)
        for node_path in chosen:
            os.makedirs(node_path, exist_ok=True)
            with open(os.path.join(node_path, f"{block_id}.blk"), 'wb') as f:
                f.write(block_data)

    manifest = {
        "id": file_id, "name": name, "size": size,
        "blocks": len(blocks), "uploaded": time.time(),
        "user": current_user.id
    }
    for node in nodes:
        with open(os.path.join(node, f"{file_id}.json"), 'w') as f:
            json.dump(manifest, f)

    return jsonify({"success": True})

@app.route('/api/files')
@login_required
def files():
    files = []
    seen = set()
    for node in get_nodes():
        if not os.path.exists(node): continue
        for f in os.listdir(node):
            if f.endswith('.json'):
                try:
                    with open(os.path.join(node, f)) as fh:
                        data = json.load(fh)
                    if data.get('user') == current_user.id and data.get('id') not in seen:
                        seen.add(data['id'])
                        files.append({
                            "id": data['id'],
                            "name": data['name'],
                            "size": data['size'],
                            "uploaded": data['uploaded'] * 1000
                        })
                except: continue
    return jsonify({"files": files})

@app.route('/api/download/<file_id>')
@login_required
def download(file_id):
    manifest = None
    for node in get_nodes():
        path = os.path.join(node, f"{file_id}.json")
        if os.path.exists(path):
            with open(path) as f:
                manifest = json.load(f)
            break
    if not manifest or manifest.get('user') != current_user.id:
        return "Forbidden", 403

    content = bytearray()
    for i in range(manifest['blocks']):
        block_id = f"{file_id}_{i}"
        found = False
        for node in get_nodes():
            path = os.path.join(node, f"{block_id}.blk")
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    content.extend(f.read())
                found = True
                break
        if not found:
            return "File corrupted", 500

    return send_file(
        io.BytesIO(bytes(content)),
        as_attachment=True,
        download_name=manifest['name']
    )

@app.route('/api/delete/<file_id>', methods=['DELETE'])
@login_required
def delete(file_id):
    for node in get_nodes():
        for fname in os.listdir(node):
            if fname.startswith(file_id):
                try:
                    os.remove(os.path.join(node, fname))
                except: pass
    return jsonify({"success": True})

@app.route('/api/stats')
@login_required
def stats():
    total = 0
    for node in get_nodes():
        if not os.path.exists(node): continue
        for f in os.listdir(node):
            if f.endswith('.json'):
                try:
                    data = json.load(open(os.path.join(node, f)))
                    if data.get('user') == current_user.id:
                        total += data['size']
                except: pass
    percent = round((total / Config.TOTAL_STORAGE) * 100, 1)
    return jsonify({
        "used": total,
        "total": Config.TOTAL_STORAGE,
        "percent": percent
    })

if __name__ == '__main__':
    print("Car Rental Cloud Storage System - LAUNCHED")
    app.run(debug=True, port=5000)