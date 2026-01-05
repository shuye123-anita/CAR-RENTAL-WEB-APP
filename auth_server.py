# auth_server.py - gRPC Auth Server
import grpc
from concurrent import futures
import time
import os
import random
import sys
import auth_pb2
import auth_pb2_grpc
import bcrypt

print("=" * 60)
print("🚀 Starting gRPC Auth Server...")
print("=" * 60)

# Simple in-memory storage (no database needed for now)
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
            'password': request.password  # In real app, hash this
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
        return auth_pb2.VerifyOTPResponse(
            success=True,
            message="Login successful!",
            session_token=f"session-{request.user_id}"
        )

def serve():
    # Try multiple ports if 50051 is busy
    ports = [50051, 50052, 50053, 50054]
    
    for port in ports:
        try:
            server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServiceServicer(), server)
            server.add_insecure_port(f'127.0.0.1:{port}')
            server.start()
            
            print(f"✅ Auth Server is RUNNING on 127.0.0.1:{port}")
            print("=" * 60)
            print("Server is ready! Keep this window open.")
            print("=" * 60)
            
            # Keep server running
            try:
                while True:
                    time.sleep(3600)
            except KeyboardInterrupt:
                print("\n👋 Server stopped by user")
                server.stop(0)
                
        except Exception as e:
            if "Address already in use" in str(e):
                print(f"⚠️ Port {port} is busy, trying next port...")
                continue
            else:
                raise e
    
    print("❌ Could not start server on any port")

if __name__ == '__main__':
    serve()