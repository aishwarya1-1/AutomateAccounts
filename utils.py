import os
import uuid
import PyPDF2
import logging
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Check if the file is a PDF."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

def save_file(file):
    """Save the uploaded file to the upload folder."""
    try:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Generate a unique filename to prevent overwriting
            unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:8]}_{filename}"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            return {"success": True, "filename": unique_filename, "file_path": file_path}
        else:
            return {"success": False, "error": "Invalid file type. Only PDF files are allowed."}
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        return {"success": False, "error": str(e)}

def validate_pdf(file_path):
    """Validate if the file is a valid PDF."""
    try:
        # Try to open and read the PDF
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            # Check if we can get the number of pages (basic validation)
            num_pages = len(reader.pages)
            return {"valid": True, "pages": num_pages}
    except Exception as e:
        logger.error(f"PDF validation error: {str(e)}")
        return {"valid": False, "error": str(e)}

def parse_date(date_str):
    """Parse various date formats into a datetime object."""
    date_formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%B %d, %Y",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%d %B %Y",
        "%Y/%m/%d"
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    # If all formats fail, return None
    return None

def parse_amount(amount_str):
    """Parse various amount formats into a float."""
    try:
        # Remove currency symbols and commas
        cleaned = amount_str.replace('$', '').replace('€', '').replace('£', '').replace(',', '').strip()
        return float(cleaned)
    except ValueError:
        return None