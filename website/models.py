from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime

product_payment = db.Table('product_payment',
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True),
    db.Column('payment_id', db.Integer, db.ForeignKey('transactions.id'), primary_key=True),
    db.Column('quantity', db.Integer, nullable=False, default=1)  # Add quantity column
)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(1000), nullable=True)  # Store image as binary data

    def __repr__(self):
        return f'<Product {self.name}>'
    
class PaymentTransaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    checkout_request_id = db.Column(db.String(50), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')  # e.g., 'pending', 'completed', 'failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define many-to-many relationship
    products = db.relationship('Product', secondary=product_payment, backref=db.backref('transactions', lazy='dynamic'))

    def __repr__(self):
        return f'<PaymentTransaction {self.checkout_request_id}>'

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    notes = db.relationship('Note', lazy=True)

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
    
      
    def get_pending_balance(self):
        refunds = Refund.query.filter_by(LoanID=self.LoanrecordID).all()
        total_refunded = sum(refund.RefundAmount for refund in refunds)
        return self.Amount_Due - total_refunded


class Refund(db.Model):
    __tablename__ = 'refunds'
    RefundID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    LoanID = db.Column(db.Integer, db.ForeignKey('loanrecords.LoanrecordID'), nullable=False)
    RefundAmount = db.Column(db.Float, nullable=False)
    RefundDate = db.Column(db.DateTime(timezone=True), default=func.now())
    Status = db.Column(db.String(50), default='Pending')
    Reason = db.Column(db.Text, nullable=True)


