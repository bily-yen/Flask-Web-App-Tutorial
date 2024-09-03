from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, Flask
from flask_login import login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta, timezone
import requests
from requests.auth import HTTPBasicAuth
import base64
from threading import Timer
import logging
# Import models and database setup
from .models import Note, LoanRecord, Refund, Product, PaymentTransaction
from . import db
import re
import json
import time
import os



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

# Route to display the products page
@views.route('/products', methods=['GET'])
def products():
    """
    Display the products page.
    """
    return render_template('products.html')

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

@views.route('/myproducts', methods=['GET'])
@login_required
def myproducts():
    """
    Return to the admin page.
    """
    products = Product.query.all()
    return render_template('myproducts.html', products=products, user=current_user)

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
    



import logging
import base64
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify, redirect, url_for
from threading import Timer
import time

# Dictionary to keep track of pending payments and their timestamps
pending_payments = {}

# Duration (in seconds) after which a payment is considered to have taken too long
TIMEOUT_DURATION = 15

logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)

@views.route('/pay', methods=['POST'])
def mpesa_express():
    try:
        # Retrieve form data
        amount = request.form.get('amount')
        phone = request.form.get('phone')

        if not amount or not phone:
            return jsonify({'error': 'Amount and phone number are required'}), 400

        try:
            amount = float(amount)
            amount = int(round(amount))  # Convert to integer (e.g., cents)
        except ValueError:
            return jsonify({'error': 'Invalid amount format'}), 400
        
        access_token = getAccesstoken()
        if not access_token:
            logging.error('Failed to retrieve access token')
            return jsonify({'error': 'Failed to retrieve access token'}), 500

        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        endpoint = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

        business_shortcode = '174379'
        passkey = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
        password = business_shortcode + passkey + timestamp
        password = base64.b64encode(password.encode('utf-8')).decode('utf-8')

        data = {
            "BusinessShortCode": business_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "PartyA": phone,
            "PartyB": business_shortcode,
            "PhoneNumber": phone,
            "CallBackURL": "https://618d-105-27-235-50.ngrok-free.app/myproduct",
            "AccountReference": "techmartin",
            "TransactionDesc": "Payment for testing",
            "Amount": amount
        }

        logging.debug(f'Request Headers: {headers}')
        logging.debug(f'Request Data: {data}')

        res = requests.post(endpoint, json=data, headers=headers)
        logging.debug(f'Response Status Code: {res.status_code}')
        logging.debug(f'Response Text: {res.text}')
        res.raise_for_status()

        response_data = res.json()
        logging.info(f"Payment request response: {response_data}")

        if response_data.get('ResponseCode') == '0':
            logging.info("STK Push initiated successfully.")
            
            # Save the transaction to the database
            transaction = PaymentTransaction(
                checkout_request_id=response_data.get('CheckoutRequestID'),
                phone_number=phone,
                amount=amount,
                response_code=response_data.get('ResponseCode'),
                response_description=response_data.get('ResponseDescription'),
                mpesa_code=response_data.get('MpesaReceiptNumber')  # Save MPESA code
            )
            db.session.add(transaction)
            db.session.commit()

            timer = Timer(TIMEOUT_DURATION, handle_timeout, args=[response_data.get('CheckoutRequestID')])
            timer.start()

            # Redirect to the 'myproducts' page
            return redirect(url_for('views.myproducts'))
        else:
            description = response_data.get('ResponseDescription', 'No description provided')
            logging.error(f"STK Push failed: {description}")
            return jsonify({'error': 'STK Push failed', 'description': description}), 400

    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        return jsonify({'error': 'Request failed', 'details': str(e)}), 500

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
    
def handle_timeout(checkout_request_id):
    # Wait for the timeout duration before handling timeout
    time.sleep(TIMEOUT_DURATION)

    try:
        # Log the timeout event
        logging.warning(f"Payment with CheckoutRequestID {checkout_request_id} took too long to confirm")

        # Update the payment status to 'failed' in the database
        transaction = PaymentTransaction.query.filter_by(checkout_request_id=checkout_request_id).first()
        if transaction:
            # Ensure the status is updated only if it's still 'pending'
            if transaction.status == 'pending':
                transaction.status = 'failed'
                db.session.commit()
                logging.info(f"Payment status for CheckoutRequestID {checkout_request_id} updated to 'failed'")
            else:
                logging.info(f"Payment status for CheckoutRequestID {checkout_request_id} is not 'pending', no update needed")
        else:
            logging.warning(f"No transaction found with CheckoutRequestID {checkout_request_id}")

    except Exception as e:
        logging.error(f"An error occurred while handling the timeout: {e}")


@views.route('/myproducts/confirmation', methods=['POST'])
def confirmation():
    try:
        data = request.get_json()
        logging.info(f"Confirmation callback data received: {data}")

        # Process the confirmation callback data
        # Update your records or notify users as necessary
        return "ok"
    except Exception as e:
        logging.error(f"Error processing confirmation callback: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@views.route('/myproducts/validation', methods=['POST'])
def validation():
    try:
        data = request.get_json()
        logging.info(f"Validation callback data received: {data}")

        # Process the validation callback data
        # Validate the payment request
        return "ok"
    except Exception as e:
        logging.error(f"Error processing validation callback: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    
def getAccesstoken():
    consumer_key = 'cneQGWZjJauEZm7MR2ARlAxCfGsoojXA5ljDhNY5Xbgh4DSI'
    consumer_secret = 'h8qnYYGo7sUE3qDcnMtYvRKSOotx1kdF5ZjcV0vId2qJvHPxu3CGYYcgRWWdhJBT'
    endpoint = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    try:
        r = requests.get(endpoint, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        r.raise_for_status()
        data = r.json()
        logging.info(f"Access token response: {data}")
        return data.get('access_token')
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None
    except ValueError as e:
        logging.error(f"Data processing error: {e}")
        return None
    
from sqlalchemy.orm import joinedload
    
def update_transaction_status(transaction_id, new_status):
    transaction = PaymentTransaction.query.get_or_404(transaction_id)
    if new_status in ['pending', 'completed', 'failed']:
        transaction.status = new_status
        db.session.commit()
    else:
        raise ValueError('Invalid status value')
    

    
    
from werkzeug.utils import secure_filename
    
from flask import current_app


import os
from flask import flash, redirect, render_template, request, url_for, current_app
from werkzeug.utils import secure_filename

@views.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        image = request.files.get('image')

        if not image:
            flash('No image selected for uploading', 'error')
            return redirect(request.url)

        if image.filename == '':
            flash('No image selected for uploading', 'error')
            return redirect(request.url)
        
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            relative_image_path = os.path.join('SPAPHOTOS', filename)
            new_product = Product(name=name, price=price, image=str(relative_image_path))  # Ensure this is a string
    
            db.session.add(new_product)
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('views.add_product'))
        else:
            flash('Allowed image types are - png, jpg, jpeg, gif', 'error')
            return redirect(request.url)

    return render_template('add_product.html')

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

from flask import send_file
import io
from flask import send_from_directory, current_app

@views.route('/product_image/<int:product_id>')
def product_image(product_id):
    product = Product.query.get_or_404(product_id)
    filename = os.path.basename(product.image)  # Extract the filename from the path
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

