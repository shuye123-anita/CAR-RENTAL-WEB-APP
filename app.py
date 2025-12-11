# app.py - FINAL WORKING VERSION WITH CONNECTION RETRY
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

# ROBUST gRPC CONNECTION WITH RETRY
def get_stub():
    print("Connecting to gRPC server at 127.0.0.1:50051...")
    for i in range(20):
        try:
            channel = grpc.insecure_channel('127.0.0.1:50051')
            grpc.channel_ready_future(channel).result(timeout=3)
            print("SUCCESS: Connected to Auth Server!")
            return auth_pb2_grpc.AuthServiceStub(channel)
        except:
            print(f"Attempt {i+1}/20 - Auth server not ready soon...")
            time.sleep(1)
    return None

stub = get_stub()
if not stub:
    print("FATAL: Could not connect to auth server. Is python auth_server.py running?")
    exit()

# Rest of your setup
with app.app_context():
    db.create_all()
    os.makedirs("node_storage", exist_ok=True)
    for i in range(1, 6):
        os.makedirs(f"node_storage/node_{i}", exist_ok=True)

BLOCK_SIZE = 64 * 1024
REPLICATION = 2

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
        req = auth_pb2.SignupRequest(name=request.form['name'], username=request.form['username'],
                                    email=request.form['email'], password=request.form['password'])
        try:
            resp = stub.Signup(req, timeout=10)
            flash(resp.message, "success" if resp.success else "error")
            if resp.success:
                return redirect(url_for('login'))
        except:
            flash("Cannot reach auth server", "error")
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        req = auth_pb2.LoginRequest(username=request.form['username'], password=request.form['password'])
        try:
            resp = stub.Login(req, timeout=10)
            if resp.success:
                flash("Check your email! OTP sent.", "success")
                return redirect(url_for('verify_otp', user_id=resp.user_id))
            else:
                flash(resp.message, "error")
        except Exception as e:
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
                login_user(user)
                flash("Welcome back!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash(resp.message, "error")
        except:
            flash("Verification failed", "error")
    user = User.query.get(user_id)
    return render_template('verify_otp.html', name=user.name if user else "User")

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Keep all your /api routes exactly as they are (upload, files, download, delete, stats)

if __name__ == '__main__':
    print("Car Rental Cloud Storage System - LAUNCHED")
    app.run(debug=True, port=5000)