import os
import json
import logging
import sqlite3
from datetime import datetime
from flask import request, jsonify, render_template, url_for, redirect, flash, send_from_directory
from werkzeug.utils import secure_filename
from app import app, db
from models import ReceiptFile, Receipt, ReceiptItem
from utils import save_file, validate_pdf, parse_date, parse_amount
from ocr_helper import process_receipt

logger = logging.getLogger(__name__)

# Web routes
@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve the uploaded file."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# API Routes
@app.route('/api/upload', methods=['POST'])
def upload_receipt():
    """API to upload a receipt file."""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
    
    # Save the file
    result = save_file(file)
    if not result["success"]:
        return jsonify(result), 400
    
    # Create record in database
    try:
        # Create database record
        receipt_file = ReceiptFile()
        receipt_file.file_name = result["filename"]
        receipt_file.file_path = result["file_path"]
        receipt_file.is_valid = False
        receipt_file.is_processed = False
        
        # Add to database and get ID
        db.session.add(receipt_file)
        db.session.commit()
        file_id = receipt_file.id
        
        return jsonify({
            "success": True, 
            "message": "File uploaded successfully",
            "file_id": file_id,
            "file_name": receipt_file.file_name
        }), 201
    
    except Exception as e:
        db.session.rollback()  # Roll back on error
        logger.error(f"Database error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/validate', methods=['POST'])
def validate_receipt():
    """API to validate if the uploaded file is a valid PDF."""
    data = request.get_json()
    if not data or 'file_id' not in data:
        return jsonify({"success": False, "error": "Missing file_id parameter"}), 400
    
    file_id = data['file_id']
    receipt_file = ReceiptFile.query.get(file_id)
    
    if not receipt_file:
        return jsonify({"success": False, "error": "File not found"}), 404
    
    # Validate the PDF
    validation = validate_pdf(receipt_file.file_path)
    
    try:
        if validation["valid"]:
            receipt_file.is_valid = True
            receipt_file.invalid_reason = None
        else:
            receipt_file.is_valid = False
            receipt_file.invalid_reason = validation.get("error", "Invalid PDF file")
        
        receipt_file.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "is_valid": receipt_file.is_valid,
            "pages": validation.get("pages", 0) if receipt_file.is_valid else 0,
            "error": receipt_file.invalid_reason
        }), 200
    
    except Exception as e:
        logger.error(f"Database error during validation: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/process', methods=['POST'])
def process_receipt_api():
    """API to process a receipt and extract data."""
    data = request.get_json()
    if not data or 'file_id' not in data:
        return jsonify({"success": False, "error": "Missing file_id parameter"}), 400
    
    file_id = data['file_id']
    receipt_file = ReceiptFile.query.get(file_id)
    
    if not receipt_file:
        return jsonify({"success": False, "error": "File not found"}), 404
    
    if not receipt_file.is_valid:
        return jsonify({"success": False, "error": "Cannot process invalid file"}), 400
    
    # Process the receipt
    result = process_receipt(receipt_file.file_path)
    
    if not result.get("success"):
        return jsonify(result), 500
    
    try:
        # Create receipt record
        purchased_at = None
        if result.get("purchased_at"):
            purchased_at = parse_date(result["purchased_at"])
        
        total_amount = None
        if result.get("total_amount"):
            if isinstance(result["total_amount"], str):
                total_amount = parse_amount(result["total_amount"])
            else:
                total_amount = float(result["total_amount"])
        
        receipt = Receipt(
            receipt_file_id=receipt_file.id,
            file_path=receipt_file.file_path,
            merchant_name=result.get("merchant_name"),
            total_amount=total_amount,
            purchased_at=purchased_at,
            receipt_number=result.get("receipt_number"),
            payment_method=result.get("payment_method"),
            tax_amount=result.get("tax_amount"),
            currency=result.get("currency")
        )
        
        db.session.add(receipt)
        
        # Add receipt items if any
        if result.get("items") and isinstance(result["items"], list):
            for item_data in result["items"]:
                item = ReceiptItem(
                    description=item_data.get("description"),
                    quantity=item_data.get("quantity"),
                    unit_price=item_data.get("unit_price"),
                    total_price=item_data.get("total_price")
                )
                receipt.items.append(item)
        
        # Update receipt file status
        receipt_file.is_processed = True
        receipt_file.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Receipt processed successfully",
            "receipt_id": receipt.id,
            "receipt_data": receipt.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f"Database error during processing: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Resource not found"}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"success": False, "error": "Bad request"}), 400

@app.errorhandler(500)
def server_error(error):
    return jsonify({"success": False, "error": "Internal server error"}), 500