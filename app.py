from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure random key

# Load email credentials from .env
load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------- Helpers -------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_payroll_email():
    admin_emails = [
        "earlnimley@gmail.com",
        "coleaudreytonia@gmail.com",
        "nimleye0403@students.bowiestate.edu"
    ]

    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(admin_emails)
    msg["Subject"] = "Weekly Payroll Report"

    msg.attach(MIMEText("Hello Admin,\n\nPlease find attached the encrypted payroll report.\n\nRegards,\nPayroll System", "plain"))

    filepath = os.path.join("uploads", "encrypted_payroll_report.pdf")
    with open(filepath, "rb") as f:
        part = MIMEApplication(f.read(), _subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename="encrypted_payroll_report.pdf")
        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, admin_emails, msg.as_string())

# ------------------- Routes -------------------

@app.route('/')
def home():
    return redirect('/add_employee')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'admin' and password == 'password123':
            session['logged_in'] = True
            flash('Login successful.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if not session.get('logged_in'):
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            # You can expand this to save to a DB or file
            flash('Employee added successfully!', 'success')
            return redirect('/add_employee')
        except Exception as e:
            flash(f'❌ Error: {e}', 'danger')
            return redirect('/add_employee')

    return render_template('add_employee.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if not session.get('logged_in'):
        flash("Please log in to upload files.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files.get('file')

        if not file or file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                send_payroll_email()
                flash('File uploaded and email sent.', 'success')
            except Exception as e:
                flash(f'Upload succeeded, but email failed: {str(e)}', 'warning')

            return redirect('/dashboard')

        flash('Invalid file type.', 'danger')

    return render_template("upload.html")

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        flash("Please log in to access the dashboard.", "danger")
        return redirect(url_for('login'))

    payroll_files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.endswith('.pdf'):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            timestamp = os.path.getmtime(file_path)
            formatted_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            payroll_files.append((filename, formatted_time))

    return render_template('dashboard.html', payroll_files=payroll_files)

@app.route('/download/<filename>')
def download_file(filename):
    if not session.get('logged_in'):
        flash("Please log in to download files.", "danger")
        return redirect(url_for('login'))

    # Log the download
    log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {filename} downloaded by admin\n"
    with open("download_logs.txt", "a") as log_file:
        log_file.write(log_entry)

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/logs')
def view_logs():
    if not session.get('logged_in'):
        flash("Please log in to view logs.", "danger")
        return redirect(url_for('login'))

    try:
        with open("download_logs.txt", "r") as f:
            logs = f.readlines()
    except FileNotFoundError:
        logs = ["No logs found."]

    return render_template("logs.html", logs=logs)

# ------------------- Run -------------------
if __name__ == '__main__':
    app.run(debug=True)