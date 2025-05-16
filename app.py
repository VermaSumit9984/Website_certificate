import os
from dotenv import load_dotenv
from datetime import datetime
from flask import (Flask, render_template, request,
                   redirect, url_for, session, send_from_directory, flash)
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.pdfgen import canvas

from models import db, User

app = Flask(__name__)

# ── Flask Configuration ─────────────────────────────────────────────
load_dotenv()  # reads .env
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_only_fallback_key')  # Needed for session security / 017ed2fa452cdf6eb17f3f5d12a005c0
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ── Initialize Database with App ────────────────────────────────────
db.init_app(app)

@app.before_first_request
def create_tables():
    """Create database tables on first request."""
    db.create_all()
    # Ensure certificates folder exists
    cert_folder = os.path.join(app.root_path, 'static', 'certificates')
    os.makedirs(cert_folder, exist_ok=True)

# ── Certificate Generation ────────────────────────────────────────────
def generate_certificate(user):
    """
    Creates a PDF certificate for `user` and saves it under
    static/certificates/<filename>. Returns the filename.
    """
    # Filename: certificate_<user.id>.pdf
    filename = f"certificate_{user.id}.pdf"
    filepath = os.path.join(app.root_path, 'static', 'certificates', filename)
    
    # Create a PDF with ReportLab
    c = canvas.Canvas(filepath, pagesize=(600, 400))
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(300, 350, "Certificate of Achievement")
    # User name
    c.setFont("Helvetica", 18)
    c.drawCentredString(300, 300, f"Awarded to: {user.full_name}")
    # Date
    date_str = datetime.now().strftime("%B %d, %Y")
    c.setFont("Helvetica-Oblique", 14)
    c.drawCentredString(300, 250, f"Date: {date_str}")
    c.showPage()
    c.save()
    
    return filename

# ── Routes ─────────────────────────────────────────────────────────────

@app.route('/')
def home():
    """Redirect to login page."""
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    GET: show form.
    POST: create user, generate certificate, then redirect to login.
    """
    if request.method == 'POST':
        # 1. Collect form data
        full_name = request.form['full_name']
        email     = request.form['email']
        phone     = request.form['phone']
        password  = request.form['password']

        # 2. Prevent duplicate emails
        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "error")
            return render_template('register.html')

        # 3. Hash password & create user
        hashed_pw = generate_password_hash(password)
        user = User(full_name=full_name,
                    email=email,
                    phone=phone,
                    password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()  # user.id is now set

        # 4. Generate and save certificate
        cert_file = generate_certificate(user)
        user.certificate_filename = cert_file
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET: show form.
    POST: validate credentials, store user_id in session.
    """
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        # Check if user exists & password matches
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        flash("Invalid credentials!", "error")

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    """
    Shows user details and embeds their personal certificate.
    """
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    return render_template('dashboard.html', user=user)


@app.route('/download_certificate/<filename>')
def download_certificate(filename):
    """
    Sends the generated certificate file as an attachment.
    """
    cert_dir = os.path.join(app.root_path, 'static', 'certificates')
    return send_from_directory(cert_dir, filename, as_attachment=True)


if __name__ == '__main__':
    # Run in debug mode so you see errors if they happen
    app.run(debug=True)
