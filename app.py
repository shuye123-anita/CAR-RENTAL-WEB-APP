# app.py - Full fixed version (correct file size + no per-file limit + OTP fix)

from flask import Flask, request, render_template, redirect, url_for, flash, send_file, abort
import io
import os
import time
import grpc
import auth_pb2
import auth_pb2_grpc
from datetime import datetime
from dotenv import load_dotenv
import shutil
import hashlib
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, File
from config import Config

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class AuthServiceManager:
    def __init__(self):
        self.stub = None
        self.port = None
        self.connected = False
        self.last_check = time.time()
        
    def get_stub(self):
        if not self.connected or time.time() - self.last_check > 30:
            self.try_connect()
        return self.stub if self.connected else None
    
    def is_connected(self):
        return self.connected
    
    def try_connect(self):
        ports = [50051, 50052, 50053, 50054]
        for port in ports:
            try:
                print(f"🔌 Trying auth server on port {port}...")
                channel = grpc.insecure_channel(f'127.0.0.1:{port}')
                stub = auth_pb2_grpc.AuthServiceStub(channel)
                grpc.channel_ready_future(channel).result(timeout=2)
                self.stub = stub
                self.port = port
                self.connected = True
                self.last_check = time.time()
                print(f"✅ Connected to auth server on port {port}")
                return True
            except Exception:
                continue
        print("❌ Could not connect to auth server")
        self.connected = False
        return False

auth_manager = AuthServiceManager()
auth_manager.try_connect()

if not auth_manager.is_connected():
    print("⚠️ Start auth_server.py in another terminal")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_node_paths():
    return [os.path.join(app.config['UPLOAD_FOLDER'], f'node_{i}') for i in range(1, app.config['NODE_COUNT'] + 1)]

def get_total_storage_usage():
    total = 0
    for path in get_node_paths():
        if os.path.exists(path):
            for root, _, files in os.walk(path):
                for f in files:
                    fp = os.path.join(root, f)
                    total += os.path.getsize(fp)
    return total

def get_total_capacity():
    return app.config['TOTAL_STORAGE']

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        stub = auth_manager.get_stub()
        if not stub:
            flash("Auth server not running", "error")
            return redirect(url_for('signup'))
        
        try:
            req = auth_pb2.SignupRequest(
                name=request.form['name'],
                username=request.form['username'],
                email=request.form['email'],
                password=request.form['password']
            )
            resp = stub.Signup(req, timeout=10)
            if resp.success:
                flash(resp.message, "success")
                return redirect(url_for('login'))
            else:
                flash(resp.message, "error")
        except Exception:
            flash("Signup failed", "error")
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        stub = auth_manager.get_stub()
        if not stub:
            flash("Auth server not available. Please start auth_server.py", "error")
            return render_template('login.html')
        
        username = request.form['username']
        password = request.form['password']
        
        try:
            req = auth_pb2.LoginRequest(username=username, password=password)
            resp = stub.Login(req, timeout=10)
            
            if resp.success:
                user = User.query.filter_by(username=username).first()
                if not user:
                    user = User(
                        username=username,
                        name=username,
                        email="temp@example.com",
                        password_hash="from_grpc"
                    )
                    db.session.add(user)
                    db.session.commit()
                
                login_user(user)
                flash(resp.message, "success")
                return redirect(url_for('verify_otp', user_id=user.id))
            else:
                flash(resp.message, "error")
        except grpc.RpcError as e:
            flash("Connection to auth server failed. Is auth_server.py running?", "error")
        except Exception as e:
            flash("Login error. Try again.", "error")
    
    return render_template('login.html')

@app.route('/verify-otp/<int:user_id>', methods=['GET', 'POST'])
def verify_otp(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("Session expired. Please login again.", "error")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        stub = auth_manager.get_stub()
        if not stub:
            flash("Auth server not available", "error")
            return render_template('verify_otp.html')
        
        try:
            req = auth_pb2.VerifyOTPRequest(user_id=user_id, otp=request.form['otp'])
            resp = stub.VerifyOTP(req, timeout=10)
            
            if resp.success:
                login_user(user)
                flash("Login successful!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash(resp.message, "error")
        except Exception:
            flash("OTP verification failed. Try again.", "error")
    
    return render_template('verify_otp.html')

@app.route('/dashboard')
@login_required
def dashboard():
    files = File.query.filter_by(user_id=current_user.id).all()
    
    used_bytes = get_total_storage_usage()
    total_bytes = get_total_capacity()
    used_mb = round(used_bytes / (1024 * 1024), 2)
    total_gb = round(total_bytes / (1024 * 1024 * 1024), 1)
    used_percent = int((used_bytes / total_bytes) * 100) if total_bytes else 0
    
    return render_template('dashboard.html',
                           username=current_user.username,
                           files=files,
                           used_bytes=f"{used_mb} MB",
                           total_bytes=f"{total_gb} GB",
                           used_percent=used_percent)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('dashboard'))

    files = request.files.getlist('file')
    if not files or all(f.filename == '' for f in files):
        flash('No file selected', 'error')
        return redirect(url_for('dashboard'))

    total_new_size = 0
    file_data_list = []

    # First pass: read all files and calculate total size
    for file in files:
        if file.filename == '':
            continue
        try:
            data = file.stream.read()
            file_size = len(data)
            total_new_size += file_size
            file_data_list.append((file.filename, data, file_size))
        except Exception:
            flash(f'Failed to read {file.filename}', 'error')

    # Check remaining space
    used_bytes = get_total_storage_usage()
    remaining = get_total_capacity() - used_bytes
    if total_new_size > remaining:
        flash(f'Not enough space. Need {total_new_size/(1024*1024):.1f} MB, only {remaining/(1024*1024):.1f} MB left', 'error')
        return redirect(url_for('dashboard'))

    # Second pass: process and save each file
    uploaded = 0
    for filename, data, file_size in file_data_list:
        chunks = [data[i:i + app.config['BLOCK_SIZE']] for i in range(0, file_size, app.config['BLOCK_SIZE'])]
        node_paths = get_node_paths()
        used_nodes = set()

        for idx, chunk in enumerate(chunks):
            primary = idx % app.config['NODE_COUNT']
            replica = (idx + 1) % app.config['NODE_COUNT']
            chunk_name = f"{hashlib.md5(chunk).hexdigest()}_{idx}"

            for node_idx in [primary, replica]:
                node_path = node_paths[node_idx]
                chunk_path = os.path.join(node_path, chunk_name)
                with open(chunk_path, 'wb') as f:
                    f.write(chunk)
                used_nodes.add(node_idx + 1)

        db_file = File(
            filename=hashlib.sha256(data).hexdigest(),
            original_name=filename,
            file_size=file_size,  # Correct size in bytes
            file_type=filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown',
            user_id=current_user.id,
            chunks=len(chunks),
            storage_nodes=','.join(map(str, sorted(used_nodes)))
        )
        db.session.add(db_file)
        uploaded += 1

    db.session.commit()
    flash(f'{uploaded} file(s) uploaded successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    file_meta = File.query.get_or_404(file_id)
    if file_meta.user_id != current_user.id:
        abort(403)
    
    node_paths = get_node_paths()
    reconstructed = []
    
    for idx in range(file_meta.chunks):
        chunk_data = None
        for node_idx in range(app.config['NODE_COUNT']):
            files_in_node = [f for f in os.listdir(node_paths[node_idx]) if f.endswith(f"_{idx}")]
            if files_in_node:
                with open(os.path.join(node_paths[node_idx], files_in_node[0]), 'rb') as f:
                    chunk_data = f.read()
                break
        if not chunk_data:
            flash('File corrupted', 'error')
            return redirect(url_for('dashboard'))
        reconstructed.append(chunk_data)
    
    return send_file(io.BytesIO(b''.join(reconstructed)),
                     as_attachment=True,
                     download_name=file_meta.original_name)

@app.route('/delete/<int:file_id>')
@login_required
def delete_file(file_id):
    file_meta = File.query.get_or_404(file_id)
    if file_meta.user_id != current_user.id:
        abort(403)
    db.session.delete(file_meta)
    db.session.commit()
    flash('File deleted', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db_path = 'car_rental.db'
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print("🗑️ Old database deleted for fresh start")
            except PermissionError:
                print("⚠️ Database in use - starting with existing one")
        
        db.create_all()
        print("✅ Database ready")
        os.makedirs("node_storage", exist_ok=True)
    
    print("🚀 Car Rental Cloud Storage Launched")
    app.run(debug=True, port=5000)