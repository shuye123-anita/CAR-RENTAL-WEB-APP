from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User
from config import Config
import os, hashlib, json, random, time, io, smtplib, ssl
from email.message import EmailMessage
from dotenv import load_dotenv
import bcrypt

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create database and storage nodes
with app.app_context():
    db.create_all()
    os.makedirs("node_storage", exist_ok=True)
    for i in range(1, 6):
        os.makedirs(f"node_storage/node_{i}", exist_ok=True)

# Safe config values
BLOCK_SIZE = getattr(Config, 'BLOCK_SIZE', 64 * 1024)
REPLICATION = getattr(Config, 'REPLICATION', 2)

def get_nodes():
    return [f"node_storage/node_{i}" for i in range(1, 6)]

def send_otp_email(email, otp, name="User"):
    msg = EmailMessage()
    msg['Subject'] = "Car Rental Cloud - Your Login Code"
    msg['From'] = os.getenv("MAIL_USERNAME")
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
    with smtplib.SMTP(os.getenv("MAIL_SERVER"), int(os.getenv("MAIL_PORT"))) as server:
        server.starttls(context=context)
        server.login(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD"))
        server.send_message(msg)

# Temporary OTP storage
otp_store = {}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# === ROUTES ===
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username'].lower()
        email = request.form['email'].lower()
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash("Username already taken!", "error")
        elif User.query.filter_by(email=email).first():
            flash("Email already registered!", "error")
        else:
            user = User(name=name, username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Account created successfully! Please login.", "success")
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Correct credentials → send OTP
            otp = ''.join([str(random.randint(0,9)) for _ in range(6)])
            otp_store[user.id] = {"otp": otp, "time": time.time()}
            send_otp_email(user.email, otp, user.name)
            flash("OTP sent to your email!", "success")
            return redirect(url_for('verify_otp', user_id=user.id))
        else:
            flash("Invalid username or password", "error")
    return render_template('login.html')

@app.route('/verify-otp/<int:user_id>', methods=['GET', 'POST'])
def verify_otp(user_id):
    if request.method == 'POST':
        entered_otp = request.form['otp']
        data = otp_store.get(user_id)

        if not data:
            flash("OTP expired. Please login again.", "error")
            return redirect(url_for('login'))

        if time.time() - data["time"] > 300:
            del otp_store[user_id]
            flash("OTP expired!", "error")
            return redirect(url_for('login'))

        if entered_otp == data["otp"]:
            user = User.query.get(user_id)
            login_user(user)
            del otp_store[user_id]
            return redirect(url_for('dashboard'))
        else:
            flash("Wrong OTP!", "error")

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

# === STORAGE APIs (Protected) ===
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
        "id": file_id,
        "name": name,
        "size": size,
        "blocks": len(blocks),
        "uploaded": time.time(),
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