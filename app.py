from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User
from config import Config
import os, hashlib, json, random, time, io, smtplib, ssl
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Safe defaults in case Config lacks these
BLOCK_SIZE = getattr(Config, 'BLOCK_SIZE', 64 * 1024)
REPLICATION = getattr(Config, 'REPLICATION', getattr(Config, 'MIN_REPLICATION_FACTOR', 2))

# Create DB and nodes
with app.app_context():
    db.create_all()
    os.makedirs("node_storage", exist_ok=True)
    for i in range(1, 6):
        os.makedirs(f"node_storage/node_{i}", exist_ok=True)

def get_nodes():
    return [f"node_storage/node_{i}" for i in range(1, 6)]

def send_otp_email(email, otp):
    msg = EmailMessage()
    msg['Subject'] = "Your Car Rental Cloud Login Code"
    msg['From'] = os.getenv("MAIL_USERNAME")
    msg['To'] = email
    msg.set_content(f"""
    <div style="font-family:Arial;text-align:center;padding:50px;background:#f0f0f0">
        <div style="background:white;padding:40px;border-radius:20px;display:inline-block;box-shadow:0 10px 30px rgba(0,0,0,0.2)">
            <h2 style="color:#1e3c72">Car Rental Cloud Storage</h2>
            <p style="font-size:18px">Your secure login code:</p>
            <h1 style="font-size:60px;color:#00d4ff;letter-spacing:20px;margin:30px 0">{otp}</h1>
            <p>Valid for 5 minutes</p>
        </div>
    </div>
    """, subtype='html')

    context = ssl.create_default_context()
    with smtplib.SMTP(os.getenv("MAIL_SERVER"), int(os.getenv("MAIL_PORT"))) as server:
        server.starttls(context=context)
        server.login(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD"))
        server.send_message(msg)

otp_store = {}

@login_manager.user_loader
def load_user(user_id):
    # Flask-Login passes the user id (usually a string). Try numeric primary key first,
    # fall back to email lookup for older sessions that stored email.
    try:
        return User.query.get(int(user_id))
    except Exception:
        return User.query.filter_by(email=user_id).first()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower()
        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "error")
        else:
            otp = str(random.randint(100000, 999999))
            otp_store[email] = {"otp": otp, "time": time.time(), "name": name}
            send_otp_email(email, otp)
            flash("Check your email for OTP!", "success")
            return redirect(url_for('verify_signup', email=email))
    return render_template('signup.html')

@app.route('/verify-signup/<email>', methods=['GET', 'POST'])
def verify_signup(email):
    if request.method == 'POST':
        otp = request.form['otp']
        data = otp_store.get(email)
        if data and (time.time() - data["time"] < 300) and otp == data["otp"]:
            user = User(email=email, name=data["name"])
            db.session.add(user)
            db.session.commit()
            del otp_store[email]
            flash("Account created! Now login.", "success")
            return redirect(url_for('login'))
        flash("Invalid or expired OTP", "error")
    return render_template('verify_otp.html', email=email, title="Complete Sign Up")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Email not registered", "error")
        else:
            otp = str(random.randint(100000, 999999))
            otp_store[email] = {"otp": otp, "time": time.time()}
            send_otp_email(email, otp)
            flash("OTP sent to your email!", "success")
            return redirect(url_for('verify_login', email=email))
    return render_template('login.html')

@app.route('/verify-login/<email>', methods=['GET', 'POST'])
def verify_login(email):
    if request.method == 'POST':
        otp = request.form['otp']
        data = otp_store.get(email)
        if data and (time.time() - data["time"] < 300) and otp == data["otp"]:
            user = User.query.filter_by(email=email).first()
            login_user(user)
            del otp_store[email]
            return redirect(url_for('dashboard'))
        flash("Wrong OTP", "error")
    return render_template('verify_otp.html', email=email, title="Login with OTP")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out!", "success")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.name)

# === STORAGE APIs ===
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
        return "Access denied", 403

    content = bytearray()
    for i in range(manifest['blocks']):
        block_id = f"{file_id}_{i}"
        for node in get_nodes():
            path = os.path.join(node, f"{block_id}.blk")
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    content.extend(f.read())
                break

    return send_file(io.BytesIO(bytes(content)), download_name=manifest['name'], as_attachment=True)

@app.route('/api/delete/<file_id>', methods=['DELETE'])
@login_required
def delete(file_id):
    for node in get_nodes():
        if not os.path.exists(node):
            continue
        for fname in os.listdir(node):
            if fname.startswith(file_id):
                try:
                    os.remove(os.path.join(node, fname))
                except Exception:
                    pass
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
    percent = (total / Config.TOTAL_STORAGE) * 100
    return jsonify({"used": total, "total": Config.TOTAL_STORAGE, "percent": round(percent, 1)})

if __name__ == '__main__':
    print("Car Rental Cloud Storage - LIVE at http://127.0.0.1:5000")
    app.run(debug=True)