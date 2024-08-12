from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from .models import Note, LoanRecord, Refund
from . import db
import re
import json

# Initialize Flask-Limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri='redis://localhost:6379/0'  # Redis URL for rate limiter storage
)

views = Blueprint('views', __name__)

def sanitize_input(input_data):
    if input_data:
        return re.sub(r'<.*?>', '', input_data)
    return input_data

@views.route('/newrefund', methods=['POST'])
@limiter.limit("5 per minute")  # Apply rate limit to this endpoint
@login_required
def newrefund():
    if request.method == "POST":
        try:
            LoanID = int(request.form['LoanID'])
            RefundAmount = float(request.form['RefundAmount'])
            RefundDate_str = request.form.get('RefundDate')
            Status = sanitize_input(request.form.get('Status', 'Pending'))
            Reason = sanitize_input(request.form.get('Reason', ''))

            RefundDate = datetime.utcnow() if not RefundDate_str else datetime.strptime(RefundDate_str, '%Y-%m-%dT%H:%M')

            new_refund = Refund(
                LoanID=LoanID,
                RefundAmount=RefundAmount,
                RefundDate=RefundDate,
                Status=Status,
                Reason=Reason
            )

            db.session.add(new_refund)
            db.session.commit()

            flash("Refund Added Successfully", 'success')
        except Exception as e:
            flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('views.loanrecordbook'))

@views.route('/loandata')
@limiter.limit("10 per minute")  # Apply rate limit to this endpoint
@login_required
def loanrecordbook():
    loan_records = LoanRecord.query.order_by(LoanRecord.LoanrecordID.asc()).all()
    refunds = Refund.query.order_by(Refund.RefundID.asc()).all()
    for loan in loan_records:
        loan.pending_balance = loan.get_pending_balance()
    return render_template('loans.html', loanrecords=loan_records, refunds=refunds, user=current_user)

@views.route('/newloanrecord', methods=['POST'])
@limiter.limit("10 per minute")  # Apply rate limit to this endpoint
@login_required
def newloanrecord():
    if request.method == "POST":
        try:
            Name = sanitize_input(request.form['Name'])
            Item = sanitize_input(request.form['Item'])
            Phone = sanitize_input(request.form['Phone'])
            Address = sanitize_input(request.form['Address'])
            Amount_Borrowed = float(request.form['Amount_Borrowed'])
            Amount_Due = float(request.form['Amount_Due'])

            Date_Borrowed_str = request.form.get('Date_Borrowed')
            Date_Due_str = request.form.get('Date_Due')

            Date_Borrowed = datetime.utcnow() if not Date_Borrowed_str else datetime.strptime(Date_Borrowed_str, '%Y-%m-%dT%H:%M')
            Date_Due = Date_Borrowed + timedelta(weeks=1) if not Date_Due_str else datetime.strptime(Date_Due_str, '%Y-%m-%dT%H:%M')

            new_record = LoanRecord(
                Name=Name,
                Item=Item,
                Phone=Phone,
                Address=Address,
                Amount_Borrowed=Amount_Borrowed,
                Amount_Due=Amount_Due,
                Date_Borrowed=Date_Borrowed,
                Date_Due=Date_Due
            )

            db.session.add(new_record)
            db.session.commit()

            flash("Data Inserted Successfully", 'success')
        except Exception as e:
            flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('views.loanrecordbook'))

@views.route('/index', methods=['GET'])
def index():
    return render_template('index.html')

@views.route('/products', methods=['GET'])
def products():
    return render_template('products.html')

@views.route('/add-note', methods=['POST'])
@login_required
def add_note():
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

@views.route('/btadmin', methods=['GET'])
@login_required
def backtoadmin():
    return render_template('home.html', user=current_user)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
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

@views.route('/delete-note', methods=['POST'])
@limiter.limit("10 per minute")  # Apply rate limit to this endpoint
@login_required
def delete_note():
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