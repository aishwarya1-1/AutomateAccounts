import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Create the Flask app
app = Flask(__name__)

# Configure the app
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Database configuration - Use SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///receipts.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# File upload configuration
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static/uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Create the database instance
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Create database tables
with app.app_context():
    from models import ReceiptFile, Receipt, ReceiptItem
    db.create_all()
    logger.info("Database tables created")