import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "defaultsecret")
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'payroll.db'

# Ensure uploads folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ---------------------- Database Connection ----------------------
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------- PDF Encryption ----------------------
def encrypt_pdf(input_path, output_path, password):
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    with open(output_path, "wb") as f:
        writer.write(f)

# ---------------------- Email Sender ----------------------
def send_email_with_attachment(subject, body, to, attachment_path):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.getenv("EMAIL_SENDER")
    msg["To"] = to if isinstance(to, str) else ", ".join(to)
    msg.set_content(body)

    with open(attachment_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(attachment_path)
    msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.getenv("EMAIL_SENDER"), os.getenv("EMAIL_PASSWORD"))
        smtp.send_message(msg)

# ---------------------- Routes ----------------------

@app.route('/')
def index():
    return redirect('/dashboard')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        admin_user = request.form['username']
        admin_pass = request.form['password']
        # You can expand this with real credential checking
        if admin_user == os.getenv("ADMIN_USERNAME") and admin_pass == os.getenv("ADMIN_PASSWORD"):
            session['admin'] = admin_user
            flash('Login successful.', 'success')
            return redirect('/dashboard')
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Logged out.', 'info')
    return redirect('/login')

@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect('/login')
    conn = get_db_connection()
    files = conn.execute('SELECT * FROM payroll_files ORDER BY uploaded_at DESC').fetchall()
    conn.close()
    return render_template('dashboard.html', files=files)

@app.route('/upload', methods=['POST'])
def upload():
    if 'admin' not in session:
        return redirect('/login')

    payroll_file = request.files['payroll_file']
    email_subject = request.form.get('email_subject', 'Payroll Report')
    email_body = request.form.get('email_body', 'Please find attached the payroll report.')
    pdf_password = request.form.get('pdf_password')

    if payroll_file:
        filename = secure_filename(payroll_file.filename)
        timestamped_filename = datetime.now().strftime("%Y%m%d_%H%M%S_") + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], timestamped_filename)
        payroll_file.save(file_path)

        # Encrypt if PDF and password provided
        if filename.lower().endswith('.pdf') and pdf_password:
            encrypted_path = os.path.join(app.config['UPLOAD_FOLDER'], "encrypted_" + timestamped_filename)
            encrypt_pdf(file_path, encrypted_path, pdf_password)
            os.remove(file_path)
            os.rename(encrypted_path, file_path)

        # Save to DB
        conn = get_db_connection()
        conn.execute('INSERT INTO payroll_files (filename, uploaded_at) VALUES (?, ?)',
                     (timestamped_filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        # Email it
        recipients = [os.getenv("ADMIN_EMAIL")]  # Add more if needed
        send_email_with_attachment(
            subject=email_subject,
            body=email_body,
            to=recipients,
            attachment_path=file_path
        )

        flash('Payroll uploaded and emailed successfully!', 'success')
    else:
        flash('No file selected.', 'danger')

    return redirect('/dashboard')

@app.route('/download/<filename>')
def download(filename):
    if 'admin' not in session:
        return redirect('/login')
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# ---------------------- Main Entry ----------------------
if __name__ == '__main__':
    app.run(debug=True)