from datetime import datetime
from app import db

class ReceiptFile(db.Model):
    __tablename__ = 'receipt_file'

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    is_valid = db.Column(db.Boolean, default=False)
    invalid_reason = db.Column(db.String(255), nullable=True)
    is_processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    receipts = db.relationship('Receipt', backref='file', lazy=True)
    
    def __init__(self, **kwargs):
        super(ReceiptFile, self).__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'is_valid': self.is_valid,
            'invalid_reason': self.invalid_reason,
            'is_processed': self.is_processed,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Receipt(db.Model):
    __tablename__ = 'receipt'

    id = db.Column(db.Integer, primary_key=True)
    purchased_at = db.Column(db.DateTime, nullable=True)
    merchant_name = db.Column(db.String(255), nullable=True)
    total_amount = db.Column(db.Float, nullable=True)
    file_path = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional fields for more detailed information
    receipt_number = db.Column(db.String(100), nullable=True)
    payment_method = db.Column(db.String(100), nullable=True)
    tax_amount = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(10), nullable=True)
    
    # Foreign key relationship
    receipt_file_id = db.Column(db.Integer, db.ForeignKey('receipt_file.id'), nullable=False)
    
    # Items relationship
    items = db.relationship('ReceiptItem', backref='receipt', lazy=True, cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super(Receipt, self).__init__(**kwargs)

    def to_dict(self):
        items_data = []
        if self.items:
            items_data = [item.to_dict() for item in self.items]
        
        return {
            'id': self.id,
            'purchased_at': self.purchased_at.isoformat() if self.purchased_at else None,
            'merchant_name': self.merchant_name,
            'total_amount': self.total_amount,
            'file_path': self.file_path,
            'receipt_number': self.receipt_number,
            'payment_method': self.payment_method,
            'tax_amount': self.tax_amount,
            'currency': self.currency,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'items': items_data
        }

class ReceiptItem(db.Model):
    __tablename__ = 'receipt_item'
    
    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipt.id'), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    quantity = db.Column(db.Float, nullable=True)
    unit_price = db.Column(db.Float, nullable=True)
    total_price = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(ReceiptItem, self).__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price,
            'created_at': self.created_at.isoformat()
        }