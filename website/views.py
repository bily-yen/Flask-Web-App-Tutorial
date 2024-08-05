from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from .models import Note, LoanRecord, Refund
from . import db
import json

views = Blueprint('views', __name__)

@views.route('/newrefund', methods=['POST'])
@login_required
def newrefund():
    if request.method == "POST":
        LoanID = int(request.form['LoanID'])
        RefundAmount = float(request.form['RefundAmount'])
        RefundDate_str = request.form.get('RefundDate')
        Status = request.form.get('Status', 'Pending')
        Reason = request.form.get('Reason', '')
    

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

        flash("Refund Added Successfully")
        return redirect(url_for('views.loanrecordbook'))

@views.route('/loandata')
@login_required
def loanrecordbook():
    loan_records = LoanRecord.query.order_by(LoanRecord.LoanrecordID.asc()).all()
    refunds = Refund.query.order_by(Refund.RefundID.asc()).all()  # Fetch refund records
    for loan in loan_records:
        loan.pending_balance = loan.get_pending_balance()  # Ensure this method is defined in LoanRecord
    return render_template('loans.html', loanrecords=loan_records, refunds=refunds, user=current_user)

@views.route('/newloanrecord', methods=['POST'])
@login_required
def newloanrecord():
    if request.method == "POST":
        Name = request.form['Name']
        Item = request.form['Item']
        Phone = request.form['Phone']
        Address = request.form['Address']
        Amount_Borrowed = float(request.form['Amount_Borrowed'])
        Amount_Due = float(request.form['Amount_Due'])

        # Check if date values are provided and parse them
        Date_Borrowed_str = request.form.get('Date_Borrowed')
        Date_Due_str = request.form.get('Date_Due')

        # Set default values if dates are not provided
        Date_Borrowed = datetime.utcnow() if not Date_Borrowed_str else datetime.strptime(Date_Borrowed_str, '%Y-%m-%dT%H:%M')
        Date_Due = Date_Borrowed + timedelta(weeks=1) if not Date_Due_str else datetime.strptime(Date_Due_str, '%Y-%m-%dT%H:%M')

        # Create a new LoanRecord instance
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
        
        # Add the record to the session and commit
        db.session.add(new_record)
        db.session.commit()

        flash("Data Inserted Successfully")
        return redirect(url_for('views.loanrecordbook'))

@views.route('/index', methods=['GET'])
def index():
    return render_template('index.html')

@views.route('/add-note', methods=['POST'])
@login_required
def add_note():
    data = request.json
    note_content = data.get('note')
    if note_content:
        new_note = Note(data=note_content, user_id=current_user.id)
        db.session.add(new_note)
        db.session.commit()
        return jsonify({'message': 'Note added!'}), 200
    return jsonify({'message': 'No note content provided!'}), 400

@views.route('/btadmin', methods=['GET'])
@login_required
def backtoadmin():
    return render_template('home.html', user=current_user)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')  # Gets the note from the HTML

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)  # Providing the schema for the note
            db.session.add(new_note)  # Adding the note to the database
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)

@views.route('/delete-note', methods=['POST'])
@login_required
def delete_note():
    note = json.loads(request.data)  # This function expects a JSON from the frontend
    noteId = note.get('noteId')
    note = Note.query.get(noteId)
    if note and note.user_id == current_user.id:
        db.session.delete(note)
        db.session.commit()
    return jsonify({})