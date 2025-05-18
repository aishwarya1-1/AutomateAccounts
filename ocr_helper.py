import os
import io
import logging
import pytesseract
from PIL import Image
import pdf2image
import tempfile

from gemini_helper import extract_receipt_data_from_text, extract_receipt_data_from_image

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file using pytesseract OCR.
    """
    try:
        # Convert PDF to images
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert PDF pages to images
            images = pdf2image.convert_from_path(pdf_path)
            
            # Extract text from each image
            text = []
            for i, image in enumerate(images):
                # Save the image to a temporary file
                image_path = f"{temp_dir}/page_{i}.png"
                image.save(image_path, "PNG")
                
                # Extract text using pytesseract
                img_text = pytesseract.image_to_string(Image.open(image_path))
                text.append(img_text)
            
            # Combine text from all pages
            full_text = "\n\n".join(text)
            return {"success": True, "text": full_text}
    
    except Exception as e:
        logger.error(f"OCR extraction error: {str(e)}")
        return {"success": False, "error": str(e)}

def process_receipt(pdf_path):
    """
    Process a receipt PDF to extract structured data.
    Uses OCR to extract text and then performs simple parsing.
    """
    try:
        # Extract text with OCR
        ocr_result = extract_text_from_pdf(pdf_path)
        if not ocr_result.get("success"):
            return ocr_result
        
        # Get the extracted text
        text = ocr_result.get("text", "")
        
        # Simple fallback extraction in case Gemini API has issues
        try:
            # Try using Gemini first
            data_result = extract_receipt_data_from_text(text)
            if data_result.get("success"):
                return data_result
        except Exception as e:
            logger.warning(f"Gemini extraction failed, using simple extraction: {str(e)}")
        
        # Fallback to simple extraction
        logger.info("Using simple extraction fallback")
        
        # Simple extraction logic - find common receipt patterns
        lines = text.split('\n')
        
        # Initialize data
        data = {
            "success": True,
            "merchant_name": "Unknown",
            "total_amount": None,
            "purchased_at": None,
            "receipt_number": None,
            "payment_method": None,
            "items": []
        }
        
        # Simple parsing logic
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for merchant name (usually at the top)
            if i < 5 and len(line) > 3 and data["merchant_name"] == "Unknown":
                if not any(word in line.lower() for word in ["receipt", "invoice", "tel", "fax", "phone", "date", "time"]):
                    data["merchant_name"] = line
            
            # Look for total amount
            if "total" in line.lower() and data["total_amount"] is None:
                # Extract numbers from the line
                import re
                amounts = re.findall(r'\d+\.\d+', line)
                if amounts:
                    data["total_amount"] = float(amounts[-1])  # Take the last number as total
            
            # Look for date
            date_patterns = [
                r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY or DD/MM/YYYY
                r'\d{1,2}-\d{1,2}-\d{2,4}',  # MM-DD-YYYY or DD-MM-YYYY
                r'\d{4}-\d{2}-\d{2}'         # YYYY-MM-DD
            ]
            if data["purchased_at"] is None:
                for pattern in date_patterns:
                    matches = re.findall(pattern, line)
                    if matches:
                        data["purchased_at"] = matches[0]
                        break
        
        return data
    
    except Exception as e:
        logger.error(f"Receipt processing error: {str(e)}")
        return {"success": False, "error": str(e)}