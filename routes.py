import os
import json
import logging
import sqlite3
from datetime import datetime
from flask import request, jsonify, render_template, url_for, redirect, flash, send_from_directory
from werkzeug.utils import secure_filename
from app import app


logger = logging.getLogger(__name__)

# Web routes
@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html')