from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    file_type = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    storage_nodes = db.Column(db.String(255))  # Comma-separated node IDs
    is_encrypted = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship('User', backref='files')

class StorageNode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    node_name = db.Column(db.String(50), nullable=False)
    node_path = db.Column(db.String(255), nullable=False)
    total_space = db.Column(db.Integer, default=250*1024*1024)  # 250MB
    used_space = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    last_checked = db.Column(db.DateTime, default=datetime.utcnow)