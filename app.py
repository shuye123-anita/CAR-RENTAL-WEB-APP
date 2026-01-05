# app.py - Flask Web Application with SQLite
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User
from config import Config
import os
import time
import threading
from dotenv import load_dotenv
import grpc
import auth_pb2
import auth_pb2_grpc
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

print("=" * 60)
print("🌐 Starting Flask Web Application...")
print("=" * 60)
print(f"📊 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Auth Service Manager
class AuthServiceManager:
    def __init__(self):
        self.stub = None
        self.port = None
        self.connected = False
        self.last_check = time.time()
        
    def get_stub(self):
        # Check if we need to reconnect
        if not self.connected or time.time() - self.last_check > 30:
            self.try_connect()
        return self.stub if self.connected else None
    
    def is_connected(self):
        return self.connected
    
    def try_connect(self):
        """Try to connect to auth server on various ports"""
        ports = [50051, 50052, 50053, 50054]
        
        for port in ports:
            try:
                print(f"🔌 Trying to connect to auth server on port {port}...")
                channel = grpc.insecure_channel(f'127.0.0.1:{port}', options=[
                    ('grpc.max_receive_message_length', 100 * 1024 * 1024),
                    ('grpc.max_send_message_length', 100 * 1024 * 1024),
                ])
                
                # Try to establish connection
                try:
                    stub = auth_pb2_grpc.AuthServiceStub(channel)
                    # Test with a quick call
                    future = grpc.channel_ready_future(channel)
                    future.result(timeout=2)
                    
                    self.stub = stub
                    self.port = port
                    self.connected = True
                    self.last_check = time.time()
                    
                    print(f"✅ Connected to auth server on port {port}")
                    return True
                    
                except grpc.FutureTimeoutError:
                    print(f"⏱️  Timeout connecting to port {port}")
                    continue
                except Exception as e:
                    print(f"⚠️  Connection test failed on port {port}: {str(e)[:50]}")
                    continue
                    
            except Exception as e:
                print(f"❌ Error on port {port}: {str(e)[:50]}")
                continue
        
        print("❌ Could not connect to auth server")
        self.connected = False
        return False

# Initialize auth manager
auth_manager = AuthServiceManager()
auth_manager.try_connect()

if not auth_manager.is_connected():
    print("⚠️ Auth server not found. Login/Signup will not work.")
    print("💡 Start auth_server.py in another terminal")

# Initialize database and storage
with app.app_context():
    # Create all database tables
    db.create_all()
    print("✅ SQLite database initialized (car_rental.db)")
    
    # Check if we have any users
    user_count = User.query.count()
    print(f"📊 Total users in database: {user_count}")
    
    # Create storage directories
    os.makedirs("node_storage", exist_ok=True)
    for i in range(1, 6):
        os.makedirs(f"node_storage/node_{i}", exist_ok=True)
    print("✅ Storage nodes created")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        stub = auth_manager.get_stub()
        if not stub:
            flash("Auth server not available. Please start auth_server.py", "error")
            return render_template('signup.html')
        
        try:
            req = auth_pb2.SignupRequest(
                name=request.form['name'],
                username=request.form['username'],
                email=request.form['email'],
                password=request.form['password']
            )
            resp = stub.Signup(req, timeout=10)
            
            if resp.success:
                # Create user in SQLite database
                try:
                    user = User(
                        name=request.form['name'],
                        username=request.form['username'],
                        email=request.form['email'],
                        password_hash=request.form['password']  # In production, hash this!
                    )
                    db.session.add(user)
                    db.session.commit()
                    print(f"✅ User {request.form['username']} saved to SQLite database")
                except Exception as db_error:
                    print(f"⚠️ Could not save user to database: {db_error}")
                
                flash(resp.message, "success")
                return redirect(url_for('login'))
            else:
                flash(resp.message, "error")
                
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                auth_manager.try_connect()
                flash("Authentication service unavailable. Please try again.", "error")
            else:
                flash(f"Auth error: {e.details()}", "error")
        except Exception as e:
            flash(f"Cannot reach auth server: {str(e)[:100]}", "error")
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        stub = auth_manager.get_stub()
        if not stub:
            flash("Auth server not available. Please start auth_server.py", "error")
            return render_template('login.html')
        
        try:
            req = auth_pb2.LoginRequest(
                username=request.form['username'],
                password=request.form['password']
            )
            resp = stub.Login(req, timeout=10)
            
            if resp.success:
                flash("OTP sent! Check the auth server console.", "success")
                return redirect(url_for('verify_otp', user_id=resp.user_id))
            else:
                flash(resp.message, "error")
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                auth_manager.try_connect()
                flash("Authentication service unavailable. Please try again.", "error")
            else:
                flash(f"Auth error: {e.details()}", "error")
        except Exception as e:
            flash(f"Auth service error: {str(e)[:100]}", "error")
    
    return render_template('login.html')

@app.route('/verify-otp/<int:user_id>', methods=['GET', 'POST'])
def verify_otp(user_id):
    if request.method == 'POST':
        stub = auth_manager.get_stub()
        if not stub:
            flash("Auth server not available", "error")
            return render_template('verify_otp.html', name=f"User {user_id}")
        
        try:
            req = auth_pb2.VerifyOTPRequest(
                user_id=user_id,
                otp=request.form['otp']
            )
            resp = stub.VerifyOTP(req, timeout=10)
            
            if resp.success:
                # Get user from SQLite database
                user = User.query.filter_by(id=user_id).first()
                if not user:
                    # Create a temporary user if not found in database
                    user = User.query.filter_by(username=f"user{user_id}").first()
                    if not user:
                        # Create demo user
                        user = User(
                            name=f"User {user_id}",
                            username=f"user{user_id}",
                            email=f"user{user_id}@example.com",
                            password_hash="demo"
                        )
                        db.session.add(user)
                        db.session.commit()
                
                login_user(user)
                flash("Login successful!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash(resp.message, "error")
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                auth_manager.try_connect()
                flash("Authentication service unavailable. Please try again.", "error")
            else:
                flash(f"Verification error: {e.details()}", "error")
        except Exception as e:
            flash(f"Verification failed: {str(e)[:100]}", "error")
    
    return render_template('verify_otp.html', name=f"User {user_id}")

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "success")
    return redirect(url_for('login'))

@app.route('/db-info')
@login_required
def db_info():
    """Debug endpoint to show database info"""
    users = User.query.all()
    info = {
        'total_users': len(users),
        'users': [{'id': u.id, 'username': u.username, 'email': u.email} for u in users],
        'current_user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email
        }
    }
    return info

if __name__ == '__main__':
    print("✅ Car Rental Cloud Storage System - LAUNCHED")
    print(f"🌐 Web App: http://127.0.0.1:5000")
    print(f"📊 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    if auth_manager.is_connected():
        print(f"🔌 Connected to Auth Server on port {auth_manager.port}")
    else:
        print("⚠️ Auth Server: NOT CONNECTED")
    print("=" * 60)
    app.run(debug=True, port=5000)