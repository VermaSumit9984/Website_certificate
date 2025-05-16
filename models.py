from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy (no app bound yet)
db = SQLAlchemy()

class User(db.Model):
    """
    Represents a registered user.
    """
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    certificate_filename = db.Column(db.String(200), nullable=True)
