# AutomateAccounts
A web application with REST APIs for processing scanned receipts, extracting information using OCR/AI techniques, and storing the data in a SQLite database.

# Features

* Upload scanned receipts in PDF format
* Validate uploaded files to ensure they are valid PDFs
* Converts PDF pages to images using pdf2image,Performs OCR (Optical Character Recognition) on each image page using pytesseract to extract raw text and then attempts structured data extraction from the raw text using Google Gemini AI
* Store extracted information in a structured SQLite database
* API endpoints for managing and retrieving receipts

## ⚙️ Setup & Installation Instructions

### 📥 1. Clone the repository

```bash
git clone https://github.com/your-username/AutomateAccounts.git
cd AutomateAccounts
```

---

### 🐍 Option A: Using Conda

#### 2A. Create and activate a Conda environment

```bash
conda create -n automate python=3.10 -y
conda activate automate
```

#### 3A. Install system dependencies (Tesseract + Poppler)

```bash
conda install -c conda-forge poppler tesseract
```

#### 4A. Install Python packages

```bash
pip install -r requirements.txt
```

---

### 🐍 Option B: Using Virtual Environment (venv)

#### 2B. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3B. Install system dependencies (outside virtual environment)

##### macOS (using Homebrew)

```bash
brew install poppler tesseract
```

##### Linux (Debian/Ubuntu)

```bash
sudo apt install poppler-utils tesseract-ocr
```

##### Windows

- [Tesseract OCR Binaries](https://github.com/tesseract-ocr/tesseract)
- [Poppler for Windows](http://blog.alivate.com.au/poppler-windows/)

#### 4B. Install Python packages

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file in the root directory with the Gemini api key:

```ini

GEMINI_API_KEY=your-gemini-api-key
```

---

## 🚀 Running the App

To run locally:

```bash
flask run --host=0.0.0.0 --port=5000
```

To run in production using Gunicorn:

```bash
gunicorn -w 4 main:app
```

---


## 📦 Requirements

All Python dependencies are listed in [`requirements.txt`](./requirements.txt).
System dependencies:
- `tesseract` (for OCR)
- `poppler` (for PDF to image conversion)

---

## API Endpoints

- API Endpoints
  - 1\. Upload Receipt (`/api/upload`)
  - 2\. Validate Receipt (`/api/validate`)
  - 3\. Process Receipt (`/api/process`)
  - 4\. Get All Receipts (`/api/receipts`)
  - 5\. Get Specific Receipt (`/api/receipts/<receipt_id>`)
- Error Handling



## API Endpoints

### 1. Upload Receipt (`/api/upload`)

**Description**: Uploads a PDF receipt file and saves it to the server, creating a `ReceiptFile` record in the database.

**Method**: `POST`

**URL**: `/api/upload`

**Content-Type**: `multipart/form-data`

**Request Parameters**:

- `file`: The PDF file to upload (required).

**Example Request (curl)**:

```bash
curl -X POST -F "file=@/path/to/receipt.pdf" http://localhost:5000/api/upload
```

**Example Request (Python** `requests`**)**:

```python
import requests

url = "http://localhost:5000/api/upload"
files = {"file": open("receipt.pdf", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

**Example Response (Success)**:

```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file_id": 1,
  "file_name": "receipt.pdf"
}
```

**Example Response (Error)**:

```json
{
  "success": false,
  "error": "No file part"
}
```

**Status Codes**:

- `201`: File uploaded successfully.
- `400`: Missing file or invalid request.
- `500`: Server error (e.g., database issue).

### 2. Validate Receipt (`/api/validate`)

**Description**: Validates that the uploaded file is a valid PDF and updates the `ReceiptFile` record.

**Method**: `POST`

**URL**: `/api/validate`

**Content-Type**: `application/json`

**Request Body**:

```json
{
  "file_id": <integer>
}
```

**Example Request (curl)**:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"file_id": 1}' http://localhost:5000/api/validate
```

**Example Request (Python** `requests`**)**:

```python
import requests

url = "http://localhost:5000/api/validate"
data = {"file_id": 1}
response = requests.post(url, json=data)
print(response.json())
```

**Example Response (Success)**:

```json
{
  "success": true,
  "is_valid": true,
  "pages": 1,
  "error": null
}
```

**Example Response (Error)**:

```json
{
  "success": true,
  "is_valid": false,
  "pages": 0,
  "error": "Invalid PDF file"
}
```

**Status Codes**:

- `200`: Validation completed.
- `400`: Missing `file_id`.
- `404`: File not found.
- `500`: Server error.

### 3. Process Receipt (`/api/process`)

**Description**: Processes the uploaded PDF to extract receipt data (e.g., merchant, total, items) using OCR (`pytesseract`) and AI (`google-generativeai`), storing results in `Receipt` and `ReceiptItem` records.

**Method**: `POST`

**URL**: `/api/process`

**Content-Type**: `application/json`

**Request Body**:

```json
{
  "file_id": <integer>
}
```

**Example Request (curl)**:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"file_id": 1}' http://localhost:5000/api/process
```

**Example Request (Python** `requests`**)**:

```python
import requests

url = "http://localhost:5000/api/process"
data = {"file_id": 1}
response = requests.post(url, json=data)
print(response.json())
```

**Example Response (Success)**:

```json
{
  "success": true,
  "message": "Receipt processed successfully",
  "receipt_id": 1,
  "receipt_data": {
    "id": 1,
    "receipt_file_id": 1,
    "file_path": "/path/to/uploads/receipt.pdf",
    "merchant_name": "Example Store",
    "total_amount": 25.99,
    "purchased_at": "2025-05-19T12:00:00",
    "receipt_number": "123456",
    "payment_method": "Credit Card",
    "tax_amount": 2.00,
    "currency": "USD",
    "items": [
      {
        "description": "Item 1",
        "quantity": 2,
        "unit_price": 10.00,
        "total_price": 20.00
      }
    ]
  }
}
```

**Example Response (Error)**:

```json
{
  "success": false,
  "error": "Cannot process invalid file"
}
```

**Status Codes**:

- `200`: Receipt processed successfully.
- `400`: Missing `file_id` or invalid file.
- `404`: File not found.
- `500`: Processing or database error.

### 4. Get All Receipts (`/api/receipts`)

**Description**: Retrieves a list of all processed receipts.

**Method**: `GET`

**URL**: `/api/receipts`

**Example Request (curl)**:

```bash
curl http://localhost:5000/api/receipts
```

**Example Request (Python** `requests`**)**:

```python
import requests

url = "http://localhost:5000/api/receipts"
response = requests.get(url)
print(response.json())
```

**Example Response (Success)**:

```json
{
  "success": true,
  "receipts": [
    {
      "id": 1,
      "receipt_file_id": 1,
      "file_path": "/path/to/uploads/receipt.pdf",
      "merchant_name": "Example Store",
      "total_amount": 25.99,
      "purchased_at": "2025-05-19T12:00:00",
      "receipt_number": "123456",
      "payment_method": "Credit Card",
      "tax_amount": 2.00,
      "currency": "USD",
      "items": [
        {
          "description": "Item 1",
          "quantity": 2,
          "unit_price": 10.00,
          "total_price": 20.00
        }
      ]
    }
  ]
}
```

**Example Response (Error)**:

```json
{
  "success": false,
  "error": "Internal server error"
}
```

**Status Codes**:

- `200`: Receipts retrieved successfully.
- `500`: Database error.

### 5. Get Specific Receipt (`/api/receipts/<receipt_id>`)

**Description**: Retrieves details of a specific receipt by ID.

**Method**: `GET`

**URL**: `/api/receipts/<receipt_id>`

**Example Request (curl)**:

```bash
curl http://localhost:5000/api/receipts/1
```

**Example Request (Python** `requests`**)**:

```python
import requests

url = "http://localhost:5000/api/receipts/1"
response = requests.get(url)
print(response.json())
```

**Example Response (Success)**:

```json
{
  "success": true,
  "receipt": {
    "id": 1,
    "receipt_file_id": 1,
    "file_path": "/path/to/uploads/receipt.pdf",
    "merchant_name": "Example Store",
    "total_amount": 25.99,
    "purchased_at": "2025-05-19T12:00:00",
    "receipt_number": "123456",
    "payment_method": "Credit Card",
    "tax_amount": 2.00,
    "currency": "USD",
    "items": [
      {
        "description": "Item 1",
        "quantity": 2,
        "unit_price": 10.00,
        "total_price": 20.00
      }
    ]
  }
}
```

**Example Response (Error)**:

```json
{
  "success": false,
  "error": "Receipt not found"
}
```

**Status Codes**:

- `200`: Receipt retrieved successfully.
- `404`: Receipt not found.
- `500`: Database error.

## Error Handling

The API returns standardized error responses:

```json
{
  "success": false,
  "error": "<error message>"
}
```

- **400**: Bad request (e.g., missing parameters).
- **404**: Resource not found (e.g., invalid `file_id`).
- **500**: Server error (e.g., database or processing failure).

## Screenshots

![image](https://github.com/user-attachments/assets/87ca70ac-1037-44c7-967d-01d173a06cc4)
![image](https://github.com/user-attachments/assets/342894e4-0279-4ac9-81ce-efb384dbff51)
![image](https://github.com/user-attachments/assets/90b4dbdc-3f7e-413d-b183-404f162ec066)
![image](https://github.com/user-attachments/assets/05f98198-aba0-4aca-9453-6f52a921829a)
![image](https://github.com/user-attachments/assets/02dbf325-048f-4b2e-a95c-1c55e07a96d3)


