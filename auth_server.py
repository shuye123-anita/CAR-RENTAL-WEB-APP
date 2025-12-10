# auth_server.py - Modified to use '127.0.0.1' for gRPC binding
import grpc
from concurrent import futures
import time
import os
import random
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv
import auth_pb2
import auth_pb2_grpc
import bcrypt

load_dotenv()

MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_PORT = int(os.getenv("MAIL_PORT"))
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

from models import db, User

otp_store = {}
active_sessions = {}

def send_otp_email(email, otp, name="User"):
    msg = EmailMessage()
    msg['Subject'] = "Car Rental Cloud - Your Login Code"
    msg['From'] = MAIL_USERNAME
    msg['To'] = email
    msg.set_content(f"""
    <div style="font-family:Arial;text-align:center;padding:50px;background:#0a0a1a;color:white">
        <div style="background:#1a1a2e;padding:50px;border-radius:20px;display:inline-block;border:2px solid #00d4ff">
            <h1 style="color:#00d4ff">Car Rental Cloud</h1>
            <p style="font-size:20px">Hello <strong>{name}</strong>!</p>
            <p style="font-size:18px">Your secure login code:</p>
            <h2 style="font-size:60px;letter-spacing:20px;color:#00ffcc;background:#000;padding:20px;border-radius:15px">{otp}</h2>
            <p style="color:#aaa">Valid for 5 minutes</p>
        </div>
    </div>
    """, subtype='html')

    context = ssl.create_default_context()
    with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
        server.starttls(context=context)
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)

class AuthServiceServicer(auth_pb2_grpc.AuthServiceServicer):
    def Signup(self, request, context):
        if User.query.filter_by(username=request.username.lower()).first():
            return auth_pb2.SignupResponse(success=False, message="Username already taken!")
        if User.query.filter_by(email=request.email.lower()).first():
            return auth_pb2.SignupResponse(success=False, message="Email already registered!")

        new_user = User(
            name=request.name,
            username=request.username.lower(),
            email=request.email.lower()
        )
        new_user.set_password(request.password)
        db.session.add(new_user)
        db.session.commit()

        return auth_pb2.SignupResponse(success=True, message="Account created successfully!")

    def Login(self, request, context):
        user = User.query.filter_by(username=request.username.lower()).first()
        if not user or not user.check_password(request.password):
            return auth_pb2.LoginResponse(success=False, message="Invalid username or password")

        otp = ''.join(str(random.randint(0,9)) for _ in range(6))
        otp_store[user.id] = {"otp": otp, "time": time.time()}
        send_otp_email(user.email, otp, user.name)

        return auth_pb2.LoginResponse(success=True, message="OTP sent!", user_id=user.id)

    def VerifyOTP(self, request, context):
        data = otp_store.get(request.user_id)
        if not data or time.time() - data["time"] > 300:
            return auth_pb2.VerifyOTPResponse(success=False, message="OTP expired or invalid")

        if request.otp != data["otp"]:
            return auth_pb2.VerifyOTPResponse(success=False, message="Wrong OTP")

        del otp_store[request.user_id]
        session_token = os.urandom(32).hex()
        active_sessions[session_token] = request.user_id

        return auth_pb2.VerifyOTPResponse(
            success=True,
            message="Login successful",
            session_token=session_token
        )

def serve():
    # Initialize DB
    from app import app
    with app.app_context():
        db.create_all()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServiceServicer(), server)
    server.add_insecure_port('127.0.0.1:50051')  # Modified for IPv4 binding
    print("gRPC Auth Server running on port 50051")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()