from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime
from website import db

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)  # Quantity in stock
    details = db.Column(db.Text, nullable=True)  # New details column

    # New columns
    type = db.Column(db.String(100), nullable=True)  # Type of the product (e.g., smartphone, laptop, etc.)
    ram = db.Column(db.String(50), nullable=True)  # RAM size (e.g., 4GB, 8GB, etc.)
    storage = db.Column(db.String(50), nullable=True)  # Storage size (e.g., 64GB, 128GB, etc.)
    size = db.Column(db.String(50), nullable=True)  # Size of the product (e.g., screen size in inches)
    brand = db.Column(db.String(100), nullable=True)  # Brand of the product (e.g., Apple, Samsung, etc.)

    # New 'section' column to specify the category of the product (e.g., Electronics, Household)

    # Relationships
    order_items = db.relationship('OrderItem', back_populates='product', cascade="all, delete-orphan")
    transaction_products = db.relationship('TransactionProduct', back_populates='product', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Product {self.name}>'


# TransactionProduct Model
class TransactionProduct(db.Model):
    __tablename__ = 'transaction_products'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    particular = db.Column(db.String(100), nullable=True)

    # Relationships
    transaction = db.relationship('PaymentTransaction', back_populates='products')
    product = db.relationship('Product', back_populates='transaction_products')

    def __repr__(self):
        return (f'<TransactionProduct transaction_id={self.transaction_id} '
                f'product_id={self.product_id} quantity={self.quantity} particular={self.particular}>')

# OrderItem Model
class OrderItem(db.Model):
    __tablename__ = 'order_item'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    # Relationships
    transaction = db.relationship('PaymentTransaction', back_populates='order_items')
    product = db.relationship('Product', back_populates='order_items')

    def __repr__(self):
        return f'<OrderItem product_id={self.product_id} quantity={self.quantity} price={self.price}>'

# PaymentTransaction Model
class PaymentTransaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    checkout_request_id = db.Column(db.String(50), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # Use Numeric for better currency handling
    status = db.Column(db.String(20), default='pending')  # Default status is 'pending'
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    response_code = db.Column(db.String(10))
    response_description = db.Column(db.Text)
    mpesa_code = db.Column(db.String(50))
    pin_entered = db.Column(db.Boolean, default=False)  # Track whether the PIN was entered

    # Relationships
    order_items = db.relationship('OrderItem', back_populates='transaction', cascade="all, delete-orphan")
    products = db.relationship('TransactionProduct', back_populates='transaction', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<PaymentTransaction {self.checkout_request_id}>'

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    notes = db.relationship('Note', lazy=True)

# Note Model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# LoanRecord Model
class LoanRecord(db.Model):
    __tablename__ = 'loanrecords'
    LoanrecordID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Item = db.Column(db.String(100), nullable=False)
    Phone = db.Column(db.String(20), nullable=False)
    Address = db.Column(db.String(255), nullable=False)
    Amount_Borrowed = db.Column(db.Float, nullable=False)
    Amount_Due = db.Column(db.Float, nullable=False)
    Date_Borrowed = db.Column(db.DateTime(timezone=True), default=func.now())
    Date_Due = db.Column(db.DateTime, nullable=False)

    # Define relationship with Refund
    refunds = db.relationship('Refund', backref='loan_record', lazy=True)

    def get_pending_balance(self):
        total_refunded = sum(refund.RefundAmount for refund in self.refunds)
        return self.Amount_Due - total_refunded

# Refund Model
class Refund(db.Model):
    __tablename__ = 'refunds'
    RefundID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    LoanID = db.Column(db.Integer, db.ForeignKey('loanrecords.LoanrecordID'), nullable=False)
    RefundAmount = db.Column(db.Float, nullable=False)
    RefundDate = db.Column(db.DateTime(timezone=True), default=func.now())
    Status = db.Column(db.String(50), default='Pending')
    Reason = db.Column(db.Text, nullable=True)
<<<<<<< HEAD
=======

class CatalogueRequest(db.Model):
    __tablename__ = 'catalogue_requests'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    institution = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CatalogueRequest name={self.name} institution={self.institution} email={self.email}>'
>>>>>>> 7ede7b1b3e108efa3571a01923e2b7bec95b4ea4
