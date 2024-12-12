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

    # Relationships
    order_items = db.relationship('OrderItem', back_populates='product', cascade="all, delete-orphan")
    transaction_products = db.relationship('TransactionProduct', back_populates='product', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Product {self.name}>'

class Computer(db.Model):
    __tablename__ = 'computers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)  # Quantity in stock
    brand = db.Column(db.String(50), nullable=False)  # Brand of the computer
    specifications = db.Column(db.Text, nullable=True)  # Specifications/details about the computer
    details = db.Column(db.Text, nullable=True)  # New details column

    # Relationships
    order_items = db.relationship('OrderItem', back_populates='computer', cascade="all, delete-orphan")
    transaction_products = db.relationship('TransactionProduct', back_populates='computer', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Computer {self.name}>'

class Printer(db.Model):
    __tablename__ = 'printers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)  # Quantity in stock
    brand = db.Column(db.String(50), nullable=False)  # Brand of the printer
    specifications = db.Column(db.Text, nullable=True)  # Specifications/details about the printer
    details = db.Column(db.Text, nullable=True)  # General details about the printer
    
    # Special features for printers
    print_speed = db.Column(db.String(100), nullable=True)  # Print speed (e.g., "20 pages per minute")
    resolution = db.Column(db.String(100), nullable=True)  # Resolution (e.g., "1200x1200 dpi")
    connectivity = db.Column(db.String(100), nullable=True)  # Connectivity (e.g., "Wi-Fi, USB")
    color = db.Column(db.String(50), nullable=True)  # Color options (e.g., "Color", "Monochrome")
    type = db.Column(db.String(50), nullable=True)  # Type of printer (e.g., "Laser", "Inkjet")

    # Relationships
    order_items = db.relationship('OrderItem', back_populates='printer', cascade="all, delete-orphan")
    transaction_products = db.relationship('TransactionProduct', back_populates='printer', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Printer {self.name}>'

class Projector(db.Model):
    __tablename__ = 'projectors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)  # Quantity in stock
    brand = db.Column(db.String(50), nullable=False)  # Brand of the projector
    specifications = db.Column(db.Text, nullable=True)  # Specifications/details about the projector
    details = db.Column(db.Text, nullable=True)  # New details column

    # Relationships
    order_items = db.relationship('OrderItem', back_populates='projector', cascade="all, delete-orphan")
    transaction_products = db.relationship('TransactionProduct', back_populates='projector', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Projector {self.name}>'

class Photocopier(db.Model):
    __tablename__ = 'photocopiers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)  # Quantity in stock
    brand = db.Column(db.String(50), nullable=False)  # Brand of the photocopier
    specifications = db.Column(db.Text, nullable=True)  # Specifications/details about the photocopier
    details = db.Column(db.Text, nullable=True)  # New details column

    # Relationships
    order_items = db.relationship('OrderItem', back_populates='photocopier', cascade="all, delete-orphan")
    transaction_products = db.relationship('TransactionProduct', back_populates='photocopier', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Photocopier {self.name}>'

class Laminator(db.Model):
    __tablename__ = 'laminators'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)  # Quantity in stock
    brand = db.Column(db.String(50), nullable=False)  # Brand of the laminator
    specifications = db.Column(db.Text, nullable=True)  # Specifications/details about the laminator
    details = db.Column(db.Text, nullable=True)  # New details column

    # Relationships
    order_items = db.relationship('OrderItem', back_populates='laminator', cascade="all, delete-orphan")
    transaction_products = db.relationship('TransactionProduct', back_populates='laminator', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Laminator {self.name}>'

class Whiteboard(db.Model):
    __tablename__ = 'whiteboards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)  # Quantity in stock
    brand = db.Column(db.String(50), nullable=False)  # Brand of the whiteboard
    specifications = db.Column(db.Text, nullable=True)  # Specifications/details about the whiteboard
    details = db.Column(db.Text, nullable=True)  # New details column

    # Relationships
    order_items = db.relationship('OrderItem', back_populates='whiteboard', cascade="all, delete-orphan")
    transaction_products = db.relationship('TransactionProduct', back_populates='whiteboard', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Whiteboard {self.name}>'

class Monitor(db.Model):
    __tablename__ = 'monitors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)  # Quantity in stock
    brand = db.Column(db.String(50), nullable=False)  # Brand of the monitor
    specifications = db.Column(db.Text, nullable=True)  # Specifications/details about the monitor
    details = db.Column(db.Text, nullable=True)  # New details column

    # Relationships
    order_items = db.relationship('OrderItem', back_populates='monitor', cascade="all, delete-orphan")
    transaction_products = db.relationship('TransactionProduct', back_populates='monitor', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Monitor {self.name}>'

class Laptop(db.Model):
    __tablename__ = 'laptops'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)  # Quantity in stock
    brand = db.Column(db.String(50), nullable=False)  # Brand of the laptop
    specifications = db.Column(db.Text, nullable=True)  # Specifications/details about the laptop
    details = db.Column(db.Text, nullable=True)  # New details column

    # Relationships
    order_items = db.relationship('OrderItem', back_populates='laptop', cascade="all, delete-orphan")
    transaction_products = db.relationship('TransactionProduct', back_populates='laptop', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Laptop {self.name}>'

class Scanner(db.Model):
    __tablename__ = 'scanners'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)  # Quantity in stock
    brand = db.Column(db.String(50), nullable=False)  # Brand of the scanner
    specifications = db.Column(db.Text, nullable=True)  # Specifications/details about the scanner
    details = db.Column(db.Text, nullable=True)  # New details column

    # Relationships
    order_items = db.relationship('OrderItem', back_populates='scanner', cascade="all, delete-orphan")
    transaction_products = db.relationship('TransactionProduct', back_populates='scanner', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Scanner {self.name}>'
    
class TransactionProduct(db.Model):
    __tablename__ = 'transaction_products'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    computer_id = db.Column(db.Integer, db.ForeignKey('computers.id'), nullable=True)  # Optional link to computer
    printer_id = db.Column(db.Integer, db.ForeignKey('printers.id'), nullable=True)  # Optional link to printer
    scanner_id = db.Column(db.Integer, db.ForeignKey('scanners.id'), nullable=True)  # Optional link to scanner
    projector_id = db.Column(db.Integer, db.ForeignKey('projectors.id'), nullable=True)  # Optional link to projector
    photocopier_id = db.Column(db.Integer, db.ForeignKey('photocopiers.id'), nullable=True)  # Optional link to photocopier
    laminator_id = db.Column(db.Integer, db.ForeignKey('laminators.id'), nullable=True)  # Optional link to laminator
    whiteboard_id = db.Column(db.Integer, db.ForeignKey('whiteboards.id'), nullable=True)  # Optional link to whiteboard
    monitor_id = db.Column(db.Integer, db.ForeignKey('monitors.id'), nullable=True)  # Optional link to monitor
    laptop_id = db.Column(db.Integer, db.ForeignKey('laptops.id'), nullable=True)  # Optional link to laptop
    quantity = db.Column(db.Integer, nullable=False)
    particular = db.Column(db.String(100), nullable=True)

    # Relationships
    transaction = db.relationship('PaymentTransaction', back_populates='products')
    product = db.relationship('Product', back_populates='transaction_products')
    computer = db.relationship('Computer', back_populates='transaction_products')
    printer = db.relationship('Printer', back_populates='transaction_products')
    scanner = db.relationship('Scanner', back_populates='transaction_products')
    projector = db.relationship('Projector', back_populates='transaction_products')
    photocopier = db.relationship('Photocopier', back_populates='transaction_products')
    laminator = db.relationship('Laminator', back_populates='transaction_products')
    whiteboard = db.relationship('Whiteboard', back_populates='transaction_products')
    monitor = db.relationship('Monitor', back_populates='transaction_products')
    laptop = db.relationship('Laptop', back_populates='transaction_products')

    def __repr__(self):
        return (f'<TransactionProduct transaction_id={self.transaction_id} '
                f'product_id={self.product_id} computer_id={self.computer_id} '
                f'printer_id={self.printer_id} scanner_id={self.scanner_id} '
                f'projector_id={self.projector_id} photocopier_id={self.photocopier_id} '
                f'laminator_id={self.laminator_id} whiteboard_id={self.whiteboard_id} '
                f'monitor_id={self.monitor_id} laptop_id={self.laptop_id} '
                f'quantity={self.quantity} particular={self.particular}>')

class OrderItem(db.Model):
    __tablename__ = 'order_item'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    computer_id = db.Column(db.Integer, db.ForeignKey('computers.id'), nullable=True)
    printer_id = db.Column(db.Integer, db.ForeignKey('printers.id'), nullable=True)
    scanner_id = db.Column(db.Integer, db.ForeignKey('scanners.id'), nullable=True)
    projector_id = db.Column(db.Integer, db.ForeignKey('projectors.id'), nullable=True)
    photocopier_id = db.Column(db.Integer, db.ForeignKey('photocopiers.id'), nullable=True)
    laminator_id = db.Column(db.Integer, db.ForeignKey('laminators.id'), nullable=True)
    whiteboard_id = db.Column(db.Integer, db.ForeignKey('whiteboards.id'), nullable=True)
    monitor_id = db.Column(db.Integer, db.ForeignKey('monitors.id'), nullable=True)
    laptop_id = db.Column(db.Integer, db.ForeignKey('laptops.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    # Relationships
    transaction = db.relationship('PaymentTransaction', back_populates='order_items')
    product = db.relationship('Product', back_populates='order_items')
    computer = db.relationship('Computer', back_populates='order_items')
    printer = db.relationship('Printer', back_populates='order_items')
    scanner = db.relationship('Scanner', back_populates='order_items')
    projector = db.relationship('Projector', back_populates='order_items')
    photocopier = db.relationship('Photocopier', back_populates='order_items')
    laminator = db.relationship('Laminator', back_populates='order_items')
    whiteboard = db.relationship('Whiteboard', back_populates='order_items')
    monitor = db.relationship('Monitor', back_populates='order_items')
    laptop = db.relationship('Laptop', back_populates='order_items')

    def __repr__(self):
        return (f'<OrderItem product_id={self.product_id} '
                f'computer_id={self.computer_id} '
                f'printer_id={self.printer_id} '
                f'scanner_id={self.scanner_id} '
                f'projector_id={self.projector_id} '
                f'photocopier_id={self.photocopier_id} '
                f'laminator_id={self.laminator_id} '
                f'whiteboard_id={self.whiteboard_id} '
                f'monitor_id={self.monitor_id} '
                f'laptop_id={self.laptop_id} '
                f'quantity={self.quantity} price={self.price}>')
    

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


