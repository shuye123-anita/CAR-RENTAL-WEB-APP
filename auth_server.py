# auth_server.py - FINAL FIXED VERSION: Works with BOTH old plain-text accounts AND new hashed ones

import grpc
from concurrent import futures
import time
import os
import random
import sys
import socket
import auth_pb2
import auth_pb2_grpc
import bcrypt

from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

print("=" * 60)
print("🚀 Starting gRPC Auth Server...")
print("=" * 60)

load_dotenv()

MAIL_SERVER = os.getenv('MAIL_SERVER')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'

users_db = {}
otp_store = {}

class AuthServiceServicer(auth_pb2_grpc.AuthServiceServicer):
    def Signup(self, request, context):
        print(f"📝 Signup request: {request.username}")
        if request.username in users_db:
            return auth_pb2.SignupResponse(
                success=False, 
                message="Username already exists"
            )
        
        # Always hash new passwords
        hashed = bcrypt.hashpw(request.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user_id = len(users_db) + 1
        users_db[request.username] = {
            'id': user_id,
            'name': request.name,
            'email': request.email,
            'password_hash': hashed  # New accounts always hashed
        }
        
        print(f"✅ User created: {request.username} (ID: {user_id})")
        return auth_pb2.SignupResponse(
            success=True, 
            message="Account created successfully!"
        )
    
    def Login(self, request, context):
        print(f"🔐 Login attempt: {request.username}")
        
        if request.username not in users_db:
            return auth_pb2.LoginResponse(
                success=False, 
                message="Invalid username or password"
            )
        
        user = users_db[request.username]
        
        # Get stored password (hashed or plain)
        stored_password = user.get('password_hash') or user.get('password')  # fallback to old plain
        
        if stored_password is None:
            return auth_pb2.LoginResponse(success=False, message="Invalid username or password")
        
        password_match = False
        
        # If it looks like a bcrypt hash (starts with $2b$), use bcrypt check
        if stored_password.startswith('$2b$'):
            try:
                password_match = bcrypt.checkpw(request.password.encode('utf-8'), stored_password.encode('utf-8'))
            except:
                password_match = False
        else:
            # Old plain text password
            password_match = (request.password == stored_password)
        
        if not password_match:
            return auth_pb2.LoginResponse(
                success=False, 
                message="Invalid username or password"
            )
        
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        otp_store[user['id']] = {
            "otp": otp, 
            "time": time.time(),
            "username": request.username
        }
        
        print(f"✅ Generated OTP for {request.username}: {otp}")
        print(f"   User ID: {user['id']}")
        print(f"   OTP valid for 5 minutes")

        # Send email
        email_sent = False
        if MAIL_USERNAME and MAIL_PASSWORD and user.get('email'):
            try:
                msg = MIMEMultipart()
                msg['From'] = MAIL_USERNAME
                msg['To'] = user['email']
                msg['Subject'] = "Your Car Rental Cloud OTP"

                body = f"""Hello {user['name']},

Your OTP is: {otp}

Valid for 5 minutes.

Best,
Car Rental Cloud Team
"""
                msg.attach(MIMEText(body, 'plain'))

                server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
                if MAIL_USE_TLS:
                    server.starttls()
                server.login(MAIL_USERNAME, MAIL_PASSWORD)
                server.sendmail(MAIL_USERNAME, user['email'], msg.as_string())
                server.quit()

                print(f"✅ OTP sent to {user['email']}")
                email_sent = True
            except Exception as e:
                print(f"❌ Email failed: {str(e)}")
        
        message = "OTP sent to email + terminal!" if email_sent else "OTP in terminal (email failed)"
        return auth_pb2.LoginResponse(
            success=True,
            message=message,
            user_id=user['id']
        )
    
    def VerifyOTP(self, request, context):
        if request.user_id not in otp_store:
            return auth_pb2.VerifyOTPResponse(success=False, message="Invalid or expired OTP")
        
        stored = otp_store[request.user_id]
        if time.time() - stored["time"] > 300:
            del otp_store[request.user_id]
            return auth_pb2.VerifyOTPResponse(success=False, message="OTP expired")
        
        if request.otp != stored["otp"]:
            return auth_pb2.VerifyOTPResponse(success=False, message="Wrong OTP")
        
        del otp_store[request.user_id]
        return auth_pb2.VerifyOTPResponse(success=True, message="Login successful!", session_token=f"session-{request.user_id}")

def is_port_available(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except socket.error:
            return False

def serve():
    ports = [50051, 50052, 50053, 50054]
    
    for port in ports:
        try:
            if not is_port_available(port):
                print(f"⚠️ Port {port} busy")
                continue
            
            server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServiceServicer(), server)
            server.add_insecure_port(f'127.0.0.1:{port}')
            server.start()
            
            print(f"✅ Auth Server running on port {port}")
            print("=" * 60)
            print("Server ready!")
            print("=" * 60)
            
            while True:
                time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
    
    print("No port available")

if __name__ == '__main__':
    serve()