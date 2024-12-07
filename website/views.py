import os
import re
import json
import time
import logging
import base64
from datetime import datetime, timedelta, timezone
from threading import Timer
from flask import jsonify
from flask_socketio import emit
from flask_socketio import SocketIO
from . import socketio


import requests
from requests.auth import HTTPBasicAuth
from werkzeug.utils import secure_filename
from flask import (
    Blueprint, render_template, request, flash, jsonify, redirect,
    url_for, send_file, send_from_directory, current_app
)
from flask_login import login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.orm import joinedload

# Import models and database setup
from .models import Note, LoanRecord, Refund, Product, PaymentTransaction, OrderItem, TransactionProduct, Computer, Printer, Scanner, Projector, Photocopier, Laminator, Whiteboard, Monitor, Laptop, db
from dotenv import load_dotenv
import os
socketio = SocketIO()


# Load environment variables from .env file
load_dotenv()

mpesa_endpoint = os.getenv('MPESA_ENDPOINT')
business_shortcode = os.getenv('BUSINESS_SHORTCODE')
passkey = os.getenv('PASSKEY')
callback_url = os.getenv('CALLBACK_URL')


    



# Define East Africa Time (EAT) offset (UTC+3)
EAT_OFFSET = timezone(timedelta(hours=3))

def convert_to_eat(dt):
    """
    Convert a datetime object to East Africa Time (EAT).
    Assumes the datetime is in UTC if naive.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(EAT_OFFSET)

# Initialize Flask-Limiter for rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri='redis://localhost:6379/0'  # Redis URL for rate limiter storage
)

# Define the blueprint for views
views = Blueprint('views', __name__)

def sanitize_input(input_data):
    """
    Sanitize input to prevent XSS by stripping out HTML tags.
    """
    if input_data:
        return re.sub(r'<.*?>', '', input_data)
    return input_data


# Route to handle adding a new refund
@views.route('/newrefund', methods=['POST'])
@limiter.limit("5 per minute")
@login_required
def newrefund():
    """
    Handle the addition of a new refund record.
    Converts dates to EAT before saving.
    """
    if request.method == "POST":
        try:
            LoanID = int(request.form['LoanID'])
            RefundAmount = float(request.form['RefundAmount'])
            RefundDate_str = request.form.get('RefundDate')
            Status = sanitize_input(request.form.get('Status', 'Pending'))
            Reason = sanitize_input(request.form.get('Reason', ''))

            # Check if LoanID exists in loan records
            loan_record = LoanRecord.query.get(LoanID)
            if not loan_record:
                flash(f"Error: LoanID {LoanID} does not exist.", 'error')
                return redirect(url_for('views.loanrecordbook'))

            # Handle RefundDate
            if RefundDate_str:
                RefundDate = datetime.strptime(RefundDate_str, '%Y-%m-%dT%H:%M')
            else:
                RefundDate = datetime.utcnow()  # Default to current UTC time

            # Convert RefundDate to East Africa Time (EAT)
            RefundDate_EAT = convert_to_eat(RefundDate)

            new_refund = Refund(
                LoanID=LoanID,
                RefundAmount=RefundAmount,
                RefundDate=RefundDate_EAT,
                Status=Status,
                Reason=Reason
            )

            db.session.add(new_refund)
            db.session.commit()

            flash("Refund Added Successfully", 'success')
        except Exception as e:
            flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('views.loanrecordbook'))

# Route to display daily transactions summary
@views.route('/transactions', methods=['GET'])
def daily_summary():
    """
    Display a summary of transactions (loans and refunds) for a given day.
    Converts transaction dates to EAT for display.
    """
    # Get the current date or a date from the query parameters
    date_str = request.args.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
    date = datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)

    # Define start and end of day in UTC
    start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    # Query for loans and refunds for the given date
    loans = LoanRecord.query.filter(LoanRecord.Date_Borrowed >= start_of_day,
                                    LoanRecord.Date_Borrowed < end_of_day).all()
    refunds = Refund.query.filter(Refund.RefundDate >= start_of_day,
                                  Refund.RefundDate < end_of_day).all()

    transactions = []
    total_loans = 0
    total_refunds = 0

    # Add loans to transactions list and calculate totals
    for loan in loans:
        transactions.append({
            'transaction_id': loan.LoanrecordID,
            'type': 'Loan',
            'date': loan.Date_Borrowed.astimezone(timezone(timedelta(hours=3))),  # Convert to EAT
            'amount': loan.Amount_Borrowed,
            'pending_balance': loan.get_pending_balance()
        })
        total_loans += loan.Amount_Borrowed

    # Add refunds to transactions list and calculate totals
    for refund in refunds:
        transactions.append({
            'transaction_id': refund.RefundID,
            'type': 'Refund',
            'date': refund.RefundDate.astimezone(timezone(timedelta(hours=3))),  # Convert to EAT
            'amount': refund.RefundAmount,
            'pending_balance': None
        })
        total_refunds += refund.RefundAmount

    # Sort transactions by date
    transactions.sort(key=lambda x: x['date'], reverse=True)

    # Calculate the difference
    difference = total_refunds - total_loans

    return render_template('transactions.html', transactions=transactions, date=date_str,
                           total_loans=total_loans, total_refunds=total_refunds, difference=difference)

# Route to display the loan record book
@views.route('/loandata')
@limiter.limit("10 per minute")
@login_required
def loanrecordbook():
    """
    Display loan records and refund records.
    Converts dates to EAT for display.
    """
    loan_records = LoanRecord.query.order_by(LoanRecord.LoanrecordID.asc()).all()
    refunds = Refund.query.order_by(Refund.RefundID.asc()).all()
    
    for loan in loan_records:
        # Convert to EAT for display
        loan.Date_Borrowed = loan.Date_Borrowed.astimezone(timezone(timedelta(hours=3)))
        loan.Date_Due = loan.Date_Due.astimezone(timezone(timedelta(hours=3)))
        loan.pending_balance = loan.get_pending_balance()
        
    return render_template('loans.html', loanrecords=loan_records, refunds=refunds, user=current_user)

# Route to handle adding a new loan record
@views.route('/newloanrecord', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
def newloanrecord():
    """
    Handle the addition of a new loan record.
    Converts dates to EAT before saving.
    """
    if request.method == "POST":
        try:
            # Sanitize and extract form data
            Name = sanitize_input(request.form['Name'])
            Item = sanitize_input(request.form['Item'])
            Phone = sanitize_input(request.form['Phone'])
            Address = sanitize_input(request.form['Address'])
            Amount_Borrowed = float(request.form['Amount_Borrowed'])
            Amount_Due = float(request.form['Amount_Due'])

            # Extract and convert Date_Borrowed and Date_Due
            Date_Borrowed_str = request.form.get('Date_Borrowed')
            if Date_Borrowed_str:
                Date_Borrowed = datetime.strptime(Date_Borrowed_str, '%Y-%m-%dT%H:%M')
            else:
                Date_Borrowed = datetime.utcnow()

            Date_Due_str = request.form.get('Date_Due')
            if Date_Due_str:
                Date_Due = datetime.strptime(Date_Due_str, '%Y-%m-%dT%H:%M')
            else:
                Date_Due = Date_Borrowed + timedelta(weeks=1)

            # Convert to East Africa Time for storage
            Date_Borrowed_EAT = convert_to_eat(Date_Borrowed)
            Date_Due_EAT = convert_to_eat(Date_Due)

            # Create new LoanRecord instance
            new_record = LoanRecord(
                Name=Name,
                Item=Item,
                Phone=Phone,
                Address=Address,
                Amount_Borrowed=Amount_Borrowed,
                Amount_Due=Amount_Due,
                Date_Borrowed=Date_Borrowed_EAT,
                Date_Due=Date_Due_EAT
            )

            db.session.add(new_record)
            db.session.commit()

            flash("Data Inserted Successfully", 'success')
        except Exception as e:
            flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('views.loanrecordbook'))

# Route to display the index page
@views.route('/index', methods=['GET'])
def index():
    """
    Display the index page.
    """
    return render_template('index.html')

@views.route('/services', methods=['GET'])
def services():
    """
    Display the index page.
    """
    return render_template('services.html')



# Route to handle adding a new note
@views.route('/add-note', methods=['POST'])
@login_required
def add_note():
    """
    Handle the addition of a new note.
    """
    try:
        data = request.get_json()
        note_content = sanitize_input(data.get('note'))

        if not note_content or len(note_content) < 1:
            return jsonify({'message': 'Note is too short!'}), 400
        
        new_note = Note(data=note_content, user_id=current_user.id)
        db.session.add(new_note)
        db.session.commit()
        return jsonify({'message': 'Note added!'}), 200
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# Route to return to admin page
@views.route('/btadmin', methods=['GET'])
@login_required
def backtoadmin():
    """
    Return to the admin page.
    """
    return render_template('home.html', user=current_user)




@views.route('/api/products', methods=['GET'])
def get_products_route():
    products = Product.query.all()  # Fetch all products from the database
    product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]  # Convert Product objects to dictionaries
    return jsonify(product_list)  # Return as JSON

@views.route('/product/<int:product_id>', methods=['GET'])
def product_detail(product_id):
    # Fetch the product by its ID
    product = Product.query.get_or_404(product_id)
    
    # Fetch top sellers: Products with quantity < 15
    top_selling_products = Product.query.filter(Product.quantity < 15).all()
    
    # No printer in this route, as it's a product detail page
    printer = None
    
    # Render the template, passing the top-selling products
    return render_template('productdetail.html', product=product, printer=printer, top_selling_products=top_selling_products)

@views.route('/printer/<int:printer_id>', methods=['GET'])
def printer_detail(printer_id):
    # Fetch the printer by its ID
    printer = Printer.query.get_or_404(printer_id)
    
    # Fetch top sellers: Printers with quantity < 15
    top_selling_printers = Printer.query.filter(Printer.quantity < 15).all()
    
    # No product in this route, as it's a printer detail page
    product = None
    
    # Render the template, passing the top-selling printers
    return render_template('productdetail.html', product=product, printer=printer, top_selling_printers=top_selling_printers)




@views.route('/api/additional', methods=['GET'])
def get_additional_products_route():
    products = Product.query.filter(Product.quantity < 10).all()  # Adjust the condition as needed
    additional_product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]  # Convert Product objects to dictionaries
    return jsonify(additional_product_list)  # Return as JSON

@views.route('/api/hp-printer', methods=['GET'])
def get_hp_printers():
    products = Printer.query.filter_by(brand='HP').all()
    product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]
    return jsonify(product_list)

# Fetch products for Epson
@views.route('/api/epson', methods=['GET'])
def get_epson_products():
    products = Printer.query.filter_by(brand='Epson').all()
    product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]
    return jsonify(product_list)

# Fetch products for Ricoh
@views.route('/api/ricoh', methods=['GET'])
def get_ricoh_products():
    products = Printer.query.filter_by(brand='Ricoh').all()
    product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]
    return jsonify(product_list)

# Fetch products for Canon
@views.route('/api/canon', methods=['GET'])
def get_canon_products():
    products = Printer.query.filter_by(brand='Canon').all()
    product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]
    return jsonify(product_list)

@views.route('/api/hp', methods=['GET'])
def get_hp_products():
    products = Computer.query.filter_by(brand='HP').all()  # Fetch HP products from the computers table
    product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]
    return jsonify(product_list)

# Fetch products for Dell
@views.route('/api/dell', methods=['GET'])
def get_dell_products():
    products = Computer.query.filter_by(brand='Dell').all()  # Fetch Dell products from the computers table
    product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]
    return jsonify(product_list)

# Fetch products for Lenovo
@views.route('/api/lenovo', methods=['GET'])
def get_lenovo_products():
    products = Computer.query.filter_by(brand='Lenovo').all()  # Fetch Lenovo products from the computers table
    product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]
    return jsonify(product_list)

# Fetch products for MacOS
@views.route('/api/macos', methods=['GET'])
def get_macos_products():
    products = Computer.query.filter_by(brand='MacOS').all()  # Fetch MacOS products from the computers table
    product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]
    return jsonify(product_list)

# Fetch HP scanners
@views.route('/api/hp-scanners', methods=['GET'])
def get_hp_scanners():
    products = Scanner.query.filter_by(brand='HP').all()
    return format_product_list(products)

# Fetch Epson scanners
@views.route('/api/epson-scanners', methods=['GET'])
def get_epson_scanners():
    products = Scanner.query.filter_by(brand='Epson').all()
    return format_product_list(products)

# Fetch Ricoh scanners
@views.route('/api/ricoh-scanners', methods=['GET'])
def get_ricoh_scanners():
    products = Scanner.query.filter_by(brand='Ricoh').all()
    return format_product_list(products)

# Fetch Canon scanners
@views.route('/api/canon-scanners', methods=['GET'])
def get_canon_scanners():
    products = Scanner.query.filter_by(brand='Canon').all()
    return format_product_list(products)

# Function to format product list for JSON response
def format_product_list(products):
    product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]
    return jsonify(product_list), 200

# Fetch HP projectors
@views.route('/api/hp-projectors', methods=['GET'])
def get_hp_projectors():
    products = Projector.query.filter_by(brand='HP').all()
    return format_product_list(products)

# Fetch Epson projectors
@views.route('/api/epson-projectors', methods=['GET'])
def get_epson_projectors():
    products = Projector.query.filter_by(brand='Epson').all()
    return format_product_list(products)

# Fetch BenQ projectors
@views.route('/api/benq-projectors', methods=['GET'])
def get_benq_projectors():
    products = Projector.query.filter_by(brand='BenQ').all()
    return format_product_list(products)

# Fetch ViewSonic projectors
@views.route('/api/viewsonic-projectors', methods=['GET'])
def get_viewsonic_projectors():
    products = Projector.query.filter_by(brand='ViewSonic').all()
    return format_product_list(products)

# Fetch Canon projectors
@views.route('/api/canon-projectors', methods=['GET'])
def get_canon_projectors():
    products = Projector.query.filter_by(brand='Canon').all()
    return format_product_list(products)

# Fetch Ricoh projectors
@views.route('/api/ricoh-projectors', methods=['GET'])
def get_ricoh_projectors():
    products = Projector.query.filter_by(brand='Ricoh').all()
    return format_product_list(products)

# Function to format product list for JSON response
def format_product_list(products):
    product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]
    return jsonify(product_list), 200

@views.route('/api/hp-photocopiers', methods=['GET'])
def get_hp_photocopiers():
    products = Photocopier.query.filter_by(brand='HP').all()
    return format_product_list(products)

# Fetch Epson photocopiers
@views.route('/api/epson-photocopiers', methods=['GET'])
def get_epson_photocopiers():
    products = Photocopier.query.filter_by(brand='Epson').all()
    return format_product_list(products)

# Fetch Ricoh photocopiers
@views.route('/api/ricoh-photocopiers', methods=['GET'])
def get_ricoh_photocopiers():
    products = Photocopier.query.filter_by(brand='Ricoh').all()
    return format_product_list(products)

# Fetch Canon photocopiers
@views.route('/api/canon-photocopiers', methods=['GET'])
def get_canon_photocopiers():
    products = Photocopier.query.filter_by(brand='Canon').all()
    return format_product_list(products)

# Fetch additional brands as needed
# Example: Fetch Xerox photocopiers
@views.route('/api/xerox-photocopiers', methods=['GET'])
def get_xerox_photocopiers():
    products = Photocopier.query.filter_by(brand='Xerox').all()
    return format_product_list(products)

# Function to format product list for JSON response
def format_product_list(products):
    product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]
    return jsonify(product_list), 200


@views.route('/api/epson-laminators', methods=['GET'])
def get_epson_laminators():
    products = Laminator.query.filter_by(brand='Epson').all()
    return format_product_list(products)

# Fetch Ricoh laminators
@views.route('/api/ricoh-laminators', methods=['GET'])
def get_ricoh_laminators():
    products = Laminator.query.filter_by(brand='Ricoh').all()
    return format_product_list(products)

# Fetch Canon laminators
@views.route('/api/canon-laminators', methods=['GET'])
def get_canon_laminators():
    products = Laminator.query.filter_by(brand='Canon').all()
    return format_product_list(products)

# Fetch Xerox laminators
@views.route('/api/xerox-laminators', methods=['GET'])
def get_xerox_laminators():
    products = Laminator.query.filter_by(brand='Xerox').all()
    return format_product_list(products)

# Fetch additional brands
@views.route('/api/brandA-laminators', methods=['GET'])
def get_brandA_laminators():
    products = Laminator.query.filter_by(brand='BrandA').all()
    return format_product_list(products)

@views.route('/api/brandB-laminators', methods=['GET'])
def get_brandB_laminators():
    products = Laminator.query.filter_by(brand='BrandB').all()
    return format_product_list(products)

@views.route('/api/brandC-laminators', methods=['GET'])
def get_brandC_laminators():
    products = Laminator.query.filter_by(brand='BrandC').all()
    return format_product_list(products)

@views.route('/api/brandD-laminators', methods=['GET'])
def get_brandD_laminators():
    products = Laminator.query.filter_by(brand='BrandD').all()
    return format_product_list(products)

# ... continue for additional brands up to BrandAT ...

@views.route('/api/brandAT-laminators', methods=['GET'])
def get_brandAT_laminators():
    products = Laminator.query.filter_by(brand='BrandAT').all()
    return format_product_list(products)

# Function to format product list for JSON response
def format_product_list(products):
    product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]
    return jsonify(product_list), 200



# Fetch Quartet whiteboards
@views.route('/api/whiteboard-quartet', methods=['GET'])
def get_quartet_products():
    products = Whiteboard.query.filter_by(brand='Quartet').all()
    return format_product_list(products)

# Fetch Expo whiteboards
@views.route('/api/whiteboard-expo', methods=['GET'])
def get_expo_products():
    products = Whiteboard.query.filter_by(brand='Expo').all()
    return format_product_list(products)

# Fetch Ghent whiteboards
@views.route('/api/whiteboard-ghent', methods=['GET'])
def get_ghent_products():
    products = Whiteboard.query.filter_by(brand='Ghent').all()
    return format_product_list(products)

# Fetch Lorell whiteboards
@views.route('/api/whiteboard-lorell', methods=['GET'])
def get_lorell_products():
    products = Whiteboard.query.filter_by(brand='Lorell').all()
    return format_product_list(products)

# Fetch MasterVision whiteboards
@views.route('/api/whiteboard-mastervision', methods=['GET'])
def get_mastervision_products():
    products = Whiteboard.query.filter_by(brand='Mastervision').all()
    return format_product_list(products)

# Fetch Officemate whiteboards
@views.route('/api/whiteboard-officemate', methods=['GET'])
def get_officemate_products():
    products = Whiteboard.query.filter_by(brand='Officemate').all()
    return format_product_list(products)

# Fetch Rubbermaid whiteboards
@views.route('/api/whiteboard-rubbermaid', methods=['GET'])
def get_rubbermaid_products():
    products = Whiteboard.query.filter_by(brand='Rubbermaid').all()
    return format_product_list(products)

# Fetch Zonon whiteboards
@views.route('/api/whiteboard-zonon', methods=['GET'])
def get_zonon_products():
    products = Whiteboard.query.filter_by(brand='Zonon').all()
    return format_product_list(products)

# Fetch Bi-Silque whiteboards
@views.route('/api/whiteboard-bi-silque', methods=['GET'])
def get_bi_silque_products():
    products = Whiteboard.query.filter_by(brand='Bi-silque').all()
    return format_product_list(products)

# Fetch 3M whiteboards
@views.route('/api/whiteboard-3m', methods=['GET'])
def get_three_m_products():
    products = Whiteboard.query.filter_by(brand='3M').all()
    return format_product_list(products)

# Function to format product list for JSON response
def format_product_list(products):
    product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]
    return jsonify(product_list), 200


@views.route('/api/epson-monitors', methods=['GET'])
def get_epson_monitors():
    products = Monitor.query.filter_by(brand='Epson').all()
    return format_product_list(products)



@views.route('/gwena', methods=['GET'])
def gwena_assignment():
    return render_template('gwena.html', user=current_user)



@views.route('/api/ricoh-monitors', methods=['GET'])
def get_ricoh_monitors():
    products = Monitor.query.filter_by(brand='Ricoh').all()
    return format_product_list(products)

@views.route('/api/canon-monitors', methods=['GET'])
def get_canon_monitors():
    products = Monitor.query.filter_by(brand='Canon').all()
    return format_product_list(products)

@views.route('/api/xerox-monitors', methods=['GET'])
def get_xerox_monitors():
    products = Monitor.query.filter_by(brand='Xerox').all()
    return format_product_list(products)

@views.route('/api/dell-laptops', methods=['GET'])
def get_dell_laptops():
    products = Laptop.query.filter_by(brand='Dell').all()
    return format_product_list(products)

@views.route('/api/hp-laptops', methods=['GET'])
def get_hp_laptops():
    products = Laptop.query.filter_by(brand='HP').all()
    return format_product_list(products)

@views.route('/api/lenovo-laptops', methods=['GET'])
def get_lenovo_laptops():
    products = Laptop.query.filter_by(brand='Lenovo').all()
    return format_product_list(products)

@views.route('/api/apple-laptops', methods=['GET'])
def get_apple_laptops():
    products = Laptop.query.filter_by(brand='Apple').all()
    return format_product_list(products)

@views.route('/api/asus-laptops', methods=['GET'])
def get_asus_laptops():
    products = Laptop.query.filter_by(brand='Asus').all()
    return format_product_list(products)




@views.route('/api/laptops', methods=['GET'])
def get_laptops():
    products = Laptop.query.all()
    return jsonify([{'id': p.id, 'name': p.name, 'price': p.price, 'image': p.image, 'quantity': p.quantity} for p in products])


@views.route('/myshops', methods=['GET'])
@login_required
def myshops():
    """
    Return to the admin page.
    """
    return render_template('myshops.html', user=current_user)
    

@views.route('/aboutus', methods=['GET'])
def aboutus():
    """
    Return to the admin page.
    """
    return render_template('aboutus.html', user=current_user)

@views.route('/claim', methods=['GET'])
def claim():
    """
    Return to the admin page.
    """
    return render_template('claim.html', user=current_user)

@views.route('/illustration', methods=['GET'])
def cover():
    """
    Return to the admin page.
    """
    return render_template('illustration.html', user=current_user)


@views.route('/equipment/printer')
def printer():
    return render_template('printer.html')  # Adjust the template as needed

@views.route('/equipment/computer')
def computer():
    return render_template('computer.html')  # Adjust the template as needed

@views.route('/equipment/scanner')
def scanner():
    return render_template('scanner.html')  # Adjust the template as needed

@views.route('/equipment/projector')
def projector():
    return render_template('projector.html')  # Adjust the template as needed

@views.route('/equipment/photocopier')
def photocopier():
    return render_template('photocopier.html')  # Adjust the template as needed

@views.route('/equipment/laminator')
def laminator():
    return render_template('laminator.html')  # Adjust the template as needed

@views.route('/equipment/whiteboard')
def whiteboard():
    return render_template('whiteboard.html')  # Adjust the template as needed

@views.route('/equipment/monitor')
def monitor():
    return render_template('monitor.html')  # Adjust the template as needed

@views.route('/equipment/laptop')
def laptop():
    return render_template('laptop.html')  # Adjust the template as needed




@views.route('/products', methods=['GET'])
def addtocart():
    """
    Return to the admin page.
    """
    return render_template('addtocart.html', user=current_user)


# Route to display the home page
@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    """
    Display the home page and handle note addition.
    """
    if request.method == 'POST':
        note = sanitize_input(request.form.get('note'))

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)

# Route to handle deleting a note
@views.route('/delete-note', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
def delete_note():
    """
    Handle the deletion of a note.
    """
    try:
        note = json.loads(request.data)
        noteId = note.get('noteId')
        note = Note.query.get(noteId)
        if note and note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
        return jsonify({}), 200
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500
    





# Dictionary to keep track of pending payments and their timestamps
pending_payments = {}

# Duration (in seconds) after which a payment is considered to have taken too long
TIMEOUT_DURATION = 15

logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)

@views.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json()
    logging.info(f"Callback data received: {data}")

    # Validate the presence of necessary keys
    if 'Body' not in data or 'stkCallback' not in data['Body']:
        logging.error("Invalid callback data structure")
        return jsonify({'error': 'Invalid callback data structure'}), 400

    checkout_request_id = data['Body']['stkCallback'].get('CheckoutRequestID')
    transaction = PaymentTransaction.query.filter_by(checkout_request_id=checkout_request_id).first()

    if not transaction:
        logging.error(f"PaymentTransaction with CheckoutRequestID {checkout_request_id} not found")
        return jsonify({'error': 'Transaction not found'}), 404

    # Update the transaction based on the callback response
    transaction.response_code = data['Body']['stkCallback'].get('ResultCode')
    transaction.response_description = data['Body']['stkCallback'].get('ResultDesc')

    if transaction.response_code == '0':  # Success
        transaction.status = 'completed'
        receipt_number = next(
            (item['Value'] for item in data['Body']['stkCallback'].get('CallbackMetadata', {}).get('Item', [])
             if item['Name'] == 'MpesaReceiptNumber'), None
        )
        transaction.mpesa_code = receipt_number
        logging.info(f"Transaction {checkout_request_id} completed successfully with receipt number {receipt_number}")
    else:  # Failure
        transaction.status = 'failed'
        logging.error(f"Transaction {checkout_request_id} failed with ResultCode: {transaction.response_code}")

    db.session.commit()

    # Notify frontend via WebSocket
    notify_frontend(transaction)

    return jsonify({'status': 'success'}), 200

def notify_frontend(transaction):
    frontend_message = {
        'transaction_id': transaction.id,
        'status': transaction.status,
        'amount': transaction.amount,
        'mpesa_code': transaction.mpesa_code,
        'response_description': transaction.response_description
    }
    
    # Emit message to connected clients
    socketio.emit('payment_status_update', frontend_message)
    print("Notification sent to frontend:", frontend_message)


@views.route('/pay', methods=['POST'])
@login_required
def mpesa_express():
    try:
        data = request.json
        amount = data.get('amount')
        phone = data.get('phone')
        product_ids = data.get('product_ids')

        if not amount or not phone or not product_ids:
            return jsonify({'error': 'Amount, phone number, and products are required'}), 400

        try:
            amount = int(round(float(amount)))
        except ValueError:
            return jsonify({'error': 'Invalid amount format'}), 400

        access_token = get_access_token()
        if not access_token:
            logging.error('Failed to retrieve access token')
            return jsonify({'error': 'Failed to retrieve access token'}), 500

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        endpoint = os.getenv('MPESA_ENDPOINT')
        business_shortcode = os.getenv('BUSINESS_SHORTCODE')
        passkey = os.getenv('PASSKEY')
        password = base64.b64encode((business_shortcode + passkey + timestamp).encode('utf-8')).decode('utf-8')

        request_data = {
            "BusinessShortCode": business_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "PartyA": phone,
            "PartyB": business_shortcode,
            "PhoneNumber": phone,
            "CallBackURL": os.getenv('CALLBACK_URL'),
            "AccountReference": "techmartin",
            "TransactionDesc": "Payment for products",
            "Amount": amount
        }

        response = requests.post(endpoint, json=request_data, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get('ResponseCode') == '0':
            # Create PaymentTransaction entry
            transaction = PaymentTransaction(
                checkout_request_id=response_data.get('CheckoutRequestID'),
                phone_number=phone,
                amount=amount,
                response_code=response_data.get('ResponseCode'),
                response_description=response_data.get('ResponseDescription'),
                mpesa_code=None  # Initialize as None
            )
            db.session.add(transaction)
            db.session.commit()

            # Process product_ids to store them in TransactionProduct
            products = []
            for item in product_ids.split(','):
                try:
                    product_id, quantity = item.split(':')
                    product_id = int(product_id)
                    quantity = int(quantity)
                    products.append((product_id, quantity))

                    product = Product.query.get(product_id)
                    particular_name = product.name if product else "Unknown"
                    
                    transaction_product = TransactionProduct(
                        transaction_id=transaction.id,
                        product_id=product_id,
                        quantity=quantity,
                        particular=particular_name
                    )
                    db.session.add(transaction_product)
                except ValueError:
                    return jsonify({'error': 'Invalid product format'}), 400

            db.session.commit()

            return jsonify({'success': True, 'message': 'Payment initiated successfully'}), 200
        else:
            description = response_data.get('ResponseDescription', 'No description provided')
            if 'insufficient funds' in description.lower():
                return jsonify({'error': 'Insufficient funds in your account.'}), 400
            
            logging.error(f"STK Push failed: {description}")
            return jsonify({'error': f'STK Push failed: {description}'}), 400

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    

def handle_timeout(checkout_request_id):
    time.sleep(TIMEOUT_DURATION)

    try:
        logging.warning(f"Payment with CheckoutRequestID {checkout_request_id} took too long to confirm")

        transaction = PaymentTransaction.query.filter_by(checkout_request_id=checkout_request_id).first()
        if transaction and transaction.status == 'pending':
            transaction.status = 'failed'
            db.session.commit()
            logging.info(f"Payment status for CheckoutRequestID {checkout_request_id} updated to 'failed'")
        else:
            logging.info(f"Payment status for CheckoutRequestID {checkout_request_id} is not 'pending', no update needed")
    except Exception as e:
        logging.error(f"An error occurred while handling the timeout: {e}")



def get_access_token():
    consumer_key = os.getenv('SAFARICOM_CONSUMER_KEY')
    consumer_secret = os.getenv('SAFARICOM_CONSUMER_SECRET')
    endpoint = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    if not consumer_key or not consumer_secret:
        logging.error("Consumer key or secret is not set.")
        return None

    try:
        response = requests.get(endpoint, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        response.raise_for_status()
        data = response.json()
        logging.info(f"Access token response: {data}")
        return data.get('access_token')
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None
    except ValueError as e:
        logging.error(f"Data processing error: {e}")
        return None


@views.route('/orders')
@login_required
def view_orders():
    try:
        orders = PaymentTransaction.query.all()
        logging.info(f"Fetched {len(orders)} orders.")
        return render_template('orders.html', orders=orders)
    except Exception as e:
        logging.error(f"Error fetching orders: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@views.route('/order/<int:transaction_id>')
@login_required
def order_details(transaction_id):
    try:
        transaction = PaymentTransaction.query.get_or_404(transaction_id)
        order_items = TransactionProduct.query.filter_by(transaction_id=transaction_id).all()

        for item in order_items:
            if not item.particular:
                product = Product.query.get(item.product_id)
                if product:
                    item.particular = product.name
                    db.session.add(item)
        
        db.session.commit()

        logging.info(f"Fetched details for order ID {transaction_id}.")
        return render_template('order_details.html', transaction=transaction, order_items=order_items)
    except Exception as e:
        logging.error(f"Error fetching order details: {e}")
        return jsonify({'error': 'Internal server error'}), 500



@views.route('/add_printer', methods=['GET', 'POST'])
@login_required
def add_printer_product():
    # Fetch computers to display on page load
    printers = Printer.query.all()  # Fetch computers to display

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        quantity = request.form.get('quantity', type=int)
        image = request.files.get('image')
        brand = request.form['brand']
        specifications = request.form.get('specifications')  # Optional field

        # Check if an image was provided
        if not image or image.filename == '':
            flash('No image selected for uploading', 'error')
            return redirect(request.url)

        # Validate the image file type
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            relative_image_path = os.path.join('SPAPHOTOS', filename)  # Adjust as necessary
            
            # Enumerate existing computers to assign a new ID
            new_id = len(printers) + 1  # Start new ID from existing count
            
            new_printer = Printer(
                id=new_id,  # Set the new ID
                name=name,
                price=float(price),
                quantity=quantity,
                image=str(relative_image_path),
                brand=brand,
                specifications=specifications
            )

            db.session.add(new_printer)
            db.session.commit()
            flash('Printer product added successfully!', 'success')
            return redirect(url_for('views.add_printer_product'))  # Redirect to the same page
        else:
            flash('Allowed image types are - png, jpg, jpeg', 'error')
            return redirect(request.url)

    # Render the template with computers data
    return render_template('add_product.html', printers=printers)

@views.route('/add_comp', methods=['GET', 'POST'])
@login_required
def add_computer_product():
    # Fetch computers to display on page load
    computers = Computer.query.all()  # Fetch computers to display

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        quantity = request.form.get('quantity', type=int)
        image = request.files.get('image')
        brand = request.form['brand']
        specifications = request.form.get('specifications')  # Optional field

        # Check if an image was provided
        if not image or image.filename == '':
            flash('No image selected for uploading', 'error')
            return redirect(request.url)

        # Validate the image file type
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            relative_image_path = os.path.join('SPAPHOTOS', filename)  # Adjust as necessary
            
            # Enumerate existing computers to assign a new ID
            new_id = len(computers) + 1  # Start new ID from existing count
            
            new_computer = Computer(
                id=new_id,  # Set the new ID
                name=name,
                price=float(price),
                quantity=quantity,
                image=str(relative_image_path),
                brand=brand,
                specifications=specifications
            )

            db.session.add(new_computer)
            db.session.commit()
            flash('Computer product added successfully!', 'success')
            return redirect(url_for('views.add_computer_product'))  # Redirect to the same page
        else:
            flash('Allowed image types are - png, jpg, jpeg', 'error')
            return redirect(request.url)

    # Render the template with computers data
    return render_template('add_product.html', computers=computers)

@views.route('/add_scanner', methods=['GET', 'POST'])
@login_required
def add_scanner_product():
    # Fetch scanners to display on page load
    scanners = Scanner.query.all()  # Fetch scanners to display

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        quantity = request.form.get('quantity', type=int)
        image = request.files.get('image')
        brand = request.form['brand']
        specifications = request.form.get('specifications')  # Optional field

        # Check if an image was provided
        if not image or image.filename == '':
            flash('No image selected for uploading', 'error')
            return redirect(request.url)

        # Validate the image file type
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            relative_image_path = os.path.join('SPAPHOTOS', filename)  # Adjust as necessary
            
            # Enumerate existing scanners to assign a new ID
            new_id = len(scanners) + 1  # Start new ID from existing count
            
            new_scanner = Scanner(
                id=new_id,  # Set the new ID
                name=name,
                price=float(price),
                quantity=quantity,
                image=str(relative_image_path),
                brand=brand,
                specifications=specifications
            )

            db.session.add(new_scanner)
            db.session.commit()
            flash('Scanner product added successfully!', 'success')
            return redirect(url_for('views.add_scanner_product'))  # Redirect to the same page
        else:
            flash('Allowed image types are - png, jpg, jpeg', 'error')
            return redirect(request.url)

    # Render the template with scanners data
    return render_template('add_product.html', scanners=scanners)


@views.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    # Fetch products to display on page load
    products = Product.query.all()  # Fetch products to display
    computers = Computer.query.all()
    printers = Printer.query.all()
    scanners = Scanner.query.all()

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        quantity = request.form.get('quantity', type=int)
        image = request.files.get('image')

        # Check if an image was provided
        if not image or image.filename == '':
            flash('No image selected for uploading', 'error')
            return redirect(request.url)
        
        # Validate the image file type
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            relative_image_path = os.path.join('SPAPHOTOS', filename)
            new_product = Product(name=name, price=price, quantity=quantity, image=str(relative_image_path))
    
            db.session.add(new_product)
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('views.add_product'))  # Redirect to the same page
        else:
            flash('Allowed image types are - png, jpg, jpeg', 'error')
            return redirect(request.url)

    # Render the template with products data
    return render_template('add_product.html', products=products , computers=computers, printers=printers, scanners =scanners)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_image(product_class, product_id):
    product = product_class.query.get_or_404(product_id)
    filename = os.path.basename(product.image)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@views.route('/product_image/<int:product_id>')
def product_image(product_id):
    return get_image(Product, product_id)

@views.route('/computer_image/<int:product_id>')
def computer_image(product_id):
    return get_image(Computer, product_id)

@views.route('/printer_image/<int:product_id>')
def printer_image(product_id):
    return get_image(Printer, product_id)


@views.route('scanner_image/<int:product_id>')
def scanner_image(product_id):
    return get_image(Scanner, product_id)

