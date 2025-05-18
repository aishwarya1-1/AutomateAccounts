import os
from dotenv import load_dotenv
import json
import logging
import base64
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)
load_dotenv()
# Initialize Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Log status of API key
if GEMINI_API_KEY:
    logger.info("Gemini API key is available")
else:
    logger.warning("Gemini API key is not set")

def extract_receipt_data_from_text(text):
    """
    Extract structured receipt data from OCR text using Gemini.
    """
    try:
        if not GEMINI_API_KEY:
            logger.warning("Gemini API key not provided, using basic extraction")
            # Provide basic extraction without Gemini
            return {
                "success": True,
                "merchant_name": "Unknown",
                "total_amount": None,
                "purchased_at": None,
                "receipt_number": None,
                "payment_method": None,
                "items": []
            }
        
        prompt = f"""
        Extract the following information from this receipt OCR text. 
        If you cannot find specific information, return null for that field.
        
        Return a JSON object with the following fields:
        - merchant_name: the store or vendor name
        - total_amount: the total amount paid (numeric value only)
        - purchased_at: the purchase date in YYYY-MM-DD format
        - receipt_number: receipt or transaction number
        - payment_method: method of payment (credit card, cash, etc.)
        - tax_amount: tax amount if available
        - currency: currency code or symbol
        - items: an array of purchased items, each with:
          - description: item name/description
          - quantity: number of items (if available)
          - unit_price: price per unit (if available)
          - total_price: total price for this item
        
        Receipt text:
        {text}
        
        Only respond with a JSON object, nothing else.
        """
        
        # Use direct REST API call to Gemini
        try:
            url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY
            }
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "topP": 0.95,
                    "topK": 0,
                    "maxOutputTokens": 2048
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()
            
            if response.status_code != 200:
                logger.error(f"Gemini API error: {response.status_code}")
                logger.error(f"Response: {response_data}")
                return {"success": False, "error": f"API error: {response.status_code}"}
            
            # Extract the text from the response
            try:
                content_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
                
                # Find the JSON object in the response if it's surrounded by backticks or not direct JSON
                if "```json" in content_text:
                    content_text = content_text.split("```json")[1].split("```")[0].strip()
                elif "```" in content_text:
                    content_text = content_text.split("```")[1].split("```")[0].strip()
                
                result = json.loads(content_text)
                return {"success": True, **result}
            except Exception as parse_error:
                logger.error(f"Failed to parse Gemini response: {str(parse_error)}")
                logger.debug(f"Raw response: {response_data}")
                return {"success": False, "error": f"Response parsing error: {str(parse_error)}"}
                
        except Exception as api_error:
            logger.error(f"Gemini API request error: {str(api_error)}")
            return {"success": False, "error": f"API request error: {str(api_error)}"}
    
    except Exception as e:
        logger.error(f"Gemini extraction error: {str(e)}")
        return {"success": False, "error": str(e)}

def extract_receipt_data_from_image(image_path):
    """
    Extract receipt data directly from an image using Gemini's vision capabilities.
    """
    try:
        if not GEMINI_API_KEY:
            logger.warning("Gemini API key not provided, cannot process image")
            return {"success": False, "error": "Gemini API key not provided"}
        
        # Read the image file as bytes
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
        
        # Convert to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        prompt = """
        This is a scanned receipt. Extract the following information:
        - merchant_name: the store or vendor name
        - total_amount: the total amount paid (numeric value only)
        - purchased_at: the purchase date in YYYY-MM-DD format
        - receipt_number: receipt or transaction number
        - payment_method: method of payment (credit card, cash, etc.)
        - tax_amount: tax amount if available
        - currency: currency code or symbol
        - items: an array of purchased items, each with:
          - description: item name/description
          - quantity: number of items (if available)
          - unit_price: price per unit (if available)
          - total_price: total price for this item
          
        Respond only with JSON.
        """
        
        # Use direct REST API call to Gemini
        try:
            url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY
            }
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            },
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": image_base64
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "topP": 0.95,
                    "topK": 0,
                    "maxOutputTokens": 2048
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()
            
            if response.status_code != 200:
                logger.error(f"Gemini API error: {response.status_code}")
                logger.error(f"Response: {response_data}")
                return {"success": False, "error": f"API error: {response.status_code}"}
            
            # Extract the text from the response
            try:
                content_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
                
                # Find the JSON object in the response if it's surrounded by backticks or not direct JSON
                if "```json" in content_text:
                    content_text = content_text.split("```json")[1].split("```")[0].strip()
                elif "```" in content_text:
                    content_text = content_text.split("```")[1].split("```")[0].strip()
                
                result = json.loads(content_text)
                return {"success": True, **result}
            except Exception as parse_error:
                logger.error(f"Failed to parse Gemini response: {str(parse_error)}")
                logger.debug(f"Raw response: {response_data}")
                return {"success": False, "error": f"Response parsing error: {str(parse_error)}"}
                
        except Exception as api_error:
            logger.error(f"Gemini API request error: {str(api_error)}")
            return {"success": False, "error": f"API request error: {str(api_error)}"}
    
    except Exception as e:
        logger.error(f"Gemini image extraction error: {str(e)}")
        return {"success": False, "error": str(e)}