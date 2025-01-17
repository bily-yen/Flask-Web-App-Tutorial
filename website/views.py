import os
import re
import json
import time
import logging
import base64
from datetime import datetime, timedelta, timezone
from threading import Timer
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
from flask_socketio import emit

# Import models and database setup
from .models import Note, LoanRecord, Refund, Product, PaymentTransaction, OrderItem, TransactionProduct,CatalogueRequest, db

# Initialize dotenv for environment variables
from dotenv import load_dotenv
load_dotenv()  # Make sure to load environment variables from .env file

# Import socketio object from your app package (already initialized in __init__.py)
from . import socketio

# Import mail from your app package where it's initialized (usually in __init__.py)
from website import mail
# Load environment variables from .env file

from flask_mail import Message
import logging

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

# Route to handle form submission
from flask import render_template, request, redirect, url_for, flash
from datetime import datetime
from flask_mail import Message
from . import mail  # Assuming you have configured mail in your app

@views.route('/submit-email', methods=['POST'])
def submit_catalogue_request():
    # Get form data
    name = request.form['name']
    institution = request.form['institution']
    email = request.form['email']

    # Check if the email already exists in the database
    existing_request = CatalogueRequest.query.filter_by(email=email).first()
    if existing_request:
        flash('This email has already been used to request a catalogue.', 'warning')
        return redirect(url_for('views.index'))  # Correctly redirect to the index route

    # Create a new CatalogueRequest object and store it in the database
    catalogue_request = CatalogueRequest(
        name=name,
        institution=institution,
        email=email,
        submitted_at=datetime.utcnow()
    )

    try:
        db.session.add(catalogue_request)
        db.session.commit()
        flash('Thank you! Your catalogue request has been received.', 'success')

        # Send email to the user
        try:
            subject_user = "Catalogue Request Confirmation"
            body_user = f"""
            Hello {name},

            Thank you for requesting our catalogue. We have received your request.

            Name: {name}
            Institution: {institution}
            Email: {email}

            We will send the catalogue to your email shortly.

            Best regards,
            Your TechMart Team
            """

            msg_user = Message(
                subject=subject_user,
                recipients=[email],  # Send to the user's email
                body=body_user
            )
            mail.send(msg_user)
            logging.info(f"Catalogue request confirmation email sent to {email}")

        except Exception as e:
            logging.error(f"Error sending email to user: {e}")
            flash('Request was successful, but there was an error sending the confirmation email.', 'danger')

        # Send email to the admin about the new request
        try:
            admin_email = "bilyokwaro95@gmail.com"  # Admin email

            subject_admin = "New Catalogue Request"
            body_admin = f"""
            New Catalogue Request:

            Name: {name}
            Institution: {institution}
            Email: {email}

            Please process this request.

            Best regards,
            Your TechMart Team
            """

            msg_admin = Message(
                subject=subject_admin,
                recipients=[admin_email],  # Send to admin's email
                body=body_admin
            )
            mail.send(msg_admin)
            logging.info(f"New catalogue request notification sent to admin at {admin_email}")

        except Exception as e:
            logging.error(f"Error sending email to admin: {e}")
            flash('Catalogue request was received, but there was an error notifying the admin.', 'danger')

    except Exception as e:
        db.session.rollback()  # Rollback in case of an error
        flash(f'An error occurred: {str(e)}', 'danger')

    return redirect(url_for('views.index'))  # Correctly redirect to the index route after submission



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

# Route for Furniture products
@views.route('/api/furniture', methods=['GET'])
def get_furniture_products_route():
    products = Product.query.filter(Product.type == 'Furniture').all()  # Filter by Furniture type
    furniture_product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]
    return jsonify(furniture_product_list)  # Return as JSON


# Route for Clothing products
@views.route('/api/clothing', methods=['GET'])
def get_clothing_products_route():
    clothing_products = Product.query.filter(Product.type == 'Clothing').all()  # Filter by Clothing type
    clothing_product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in clothing_products]
    return jsonify(clothing_product_list)  # Return as JSON

# Route for Phones products
@views.route('/api/phones', methods=['GET'])
def get_phones_products_route():
    phones_products = Product.query.filter(Product.type == 'Phones').all()  # Filter by Phones type
    phones_product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in phones_products]
    return jsonify(phones_product_list)  # Return as JSON


# Route for Accessories products
@views.route('/api/accessories', methods=['GET'])
def get_accessories_products_route():
    accessories_products = Product.query.filter(Product.type == 'Tools & Accessories').all()  # Filter by Accessories type
    accessories_product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in accessories_products]
    return jsonify(accessories_product_list)  # Return as JSON

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

def format_product_list(products):
    product_list = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'image': product.image,
        'quantity': product.quantity
    } for product in products]
    return jsonify(product_list), 200


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

@views.route('/api/update_quantity', methods=['POST'])
def update_quantity_route():
    # Parse the incoming request
    data = request.get_json()  # Expecting {"id": <product_id>, "quantity": <new_quantity>}
    product_id = data.get('id')
    new_quantity = data.get('quantity')

    if product_id is None or new_quantity is None:
        return jsonify({'error': 'Product ID and quantity are required'}), 400

    product = Product.query.get_or_404(product_id)
    
    # Update the quantity of the product
    product.quantity = new_quantity
    
    # Commit the changes to the database
    db.session.commit()

    return jsonify({
        'message': 'Product quantity updated successfully',
        'id': product.id,
        'name': product.name,
        'new_quantity': product.quantity
    })

@views.route('/myshops', methods=['GET'])
@login_required
def myshops():
    """
    Return to the admin page.
    """
    return render_template('myshops.html', user=current_user)
    


@views.route('/consumer', methods=['GET'])
def consumer ():
    """
    Return to the admin page.
    """
    return render_template('consumer.html', user=current_user)
    

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

        # Access token for MPESA API
        access_token = get_access_token()
        if not access_token:
            logging.error('Failed to retrieve access token')
            return jsonify({'error': 'Failed to retrieve access token'}), 500

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Prepare MPESA request data
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

        # Send the request to MPESA API
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

            # Send email to the user with order details
            try:
                # Prepare the email content for the user
                subject_user = "Your Payment Order Confirmation"
                body_user = f"""
                Hello {current_user.first_name},

                Thank you for your purchase. Your payment was successfully processed.

                Order ID: {transaction.id}
                Amount: {amount}
                Phone: {phone}
                Products:
                """

                # Add products details for the user
                for item in products:
                    product = Product.query.get(item[0])
                    body_user += f"\n- {product.name} x {item[1]}"

                body_user += f"""

                If you have any questions, feel free to reach out to our support team.

                Best regards,
                Your TechMart Team
                """

                # Send the email to the user
                msg_user = Message(
                    subject=subject_user,
                    recipients=[current_user.email],  # Send to the logged-in user's email
                    body=body_user
                )
                mail.send(msg_user)
                logging.info(f"Payment confirmation email sent to {current_user.email}")

            except Exception as e:
                logging.error(f"Error sending email to user: {e}")
                return jsonify({'error': 'Payment processed, but failed to send confirmation email to user'}), 500

            # Send email to the admin (new incoming order)
            try:
                admin_email = "bilyokwaro95@gmail.com"  # Admin email (directly set)

                # Prepare the email content for the admin
                subject_admin = "New Incoming Order"
                body_admin = f"""
                New Order Received:

                Order ID: {transaction.id}
                Amount: {amount}
                Phone: {phone}
                Products:
                """

                # Add products details for the admin
                for item in products:
                    product = Product.query.get(item[0])
                    body_admin += f"\n- {product.name} x {item[1]}"

                body_admin += f"""

                Please process this order as soon as possible.

                Best regards,
                Your TechMart Team
                """

                # Send the email to the admin
                msg_admin = Message(
                    subject=subject_admin,
                    recipients=[admin_email],  # Send to admin's email
                    body=body_admin
                )
                mail.send(msg_admin)
                logging.info(f"New order notification sent to admin at {admin_email}")

            except Exception as e:
                logging.error(f"Error sending email to admin: {e}")
                return jsonify({'error': 'Payment processed, but failed to send admin notification'}), 500

            return jsonify({'success': True, 'message': 'Payment initiated, confirmation email sent to user, and admin notified'}), 200

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


@views.route('/cart')
def my_cart():
    return render_template('mycart.html')

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



@views.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    # Fetch products to display on page load
    products = Product.query.all()  # Fetch products to display

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
    return render_template('add_product.html', products=products)

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

