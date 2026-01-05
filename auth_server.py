# auth_server.py - gRPC Auth Server
import grpc
from concurrent import futures
import time
import os
import random
import sys
import socket
import auth_pb2
import auth_pb2_grpc

print("=" * 60)
print("🚀 Starting gRPC Auth Server...")
print("=" * 60)

# Simple in-memory storage
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
        
        # Store user in memory
        user_id = len(users_db) + 1
        users_db[request.username] = {
            'id': user_id,
            'name': request.name,
            'email': request.email,
            'password': request.password
        }
        
        print(f"✅ User created: {request.username} (ID: {user_id})")
        print(f"   Name: {request.name}")
        print(f"   Email: {request.email}")
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
        
        # Simple password check
        if request.password != user['password']:
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
        
        return auth_pb2.LoginResponse(
            success=True, 
            message="OTP sent! (Check console)",
            user_id=user['id']
        )
    
    def VerifyOTP(self, request, context):
        print(f"🔢 OTP verification for user_id: {request.user_id}")
        
        if request.user_id not in otp_store:
            return auth_pb2.VerifyOTPResponse(
                success=False, 
                message="OTP expired or invalid"
            )
        
        stored = otp_store[request.user_id]
        
        # Check if OTP expired (5 minutes)
        if time.time() - stored["time"] > 300:
            del otp_store[request.user_id]
            return auth_pb2.VerifyOTPResponse(
                success=False, 
                message="OTP expired"
            )
        
        # Check OTP
        if request.otp != stored["otp"]:
            return auth_pb2.VerifyOTPResponse(
                success=False, 
                message="Wrong OTP"
            )
        
        # OTP is correct
        del otp_store[request.user_id]
        
        print(f"✅ OTP verified for user_id: {request.user_id}")
        print(f"   Username: {stored['username']}")
        return auth_pb2.VerifyOTPResponse(
            success=True,
            message="Login successful!",
            session_token=f"session-{request.user_id}"
        )

def is_port_available(port):
    """Check if a port is available"""
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
                print(f"⚠️ Port {port} is busy, trying next port...")
                continue
            
            server = grpc.server(
                futures.ThreadPoolExecutor(max_workers=10)
            )
            auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServiceServicer(), server)
            server.add_insecure_port(f'127.0.0.1:{port}')
            server.start()
            
            print(f"✅ Auth Server is RUNNING on 127.0.0.1:{port}")
            print("=" * 60)
            print("📋 Active Users:", len(users_db))
            print("📋 Pending OTPs:", len(otp_store))
            print("=" * 60)
            print("Server is ready! Keep this window open.")
            print("=" * 60)
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Server stopped by user")
                server.stop(0)
                return
                
        except Exception as e:
            print(f"❌ Error starting server on port {port}: {str(e)[:100]}")
            continue
    
    print("❌ Could not start server on any port")
    print("💡 Try running: python cleanup.py")
    print("💡 Then restart auth_server.py")

if __name__ == '__main__':
    serve()