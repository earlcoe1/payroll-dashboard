
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with your actual secret key

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf'}

# Load environment variables
load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

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

    body = """Hello Admin,

Please find attached the encrypted payroll report for this week.

Regards,  
Payroll System
"""
    msg.attach(MIMEText(body, "plain"))

    encrypted_file = os.path.join("uploads", "encrypted_payroll_report.pdf")

    with open(encrypted_file, "rb") as f:
        part = MIMEApplication(f.read(), _subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename="encrypted_payroll_report.pdf")
        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, admin_emails, msg.as_string())

@app.route('/')
def index():
    return render_template('index.html')  # Assumes you have index.html template

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            try:
                send_payroll_email()
                flash('File uploaded and email sent successfully!')
            except Exception as e:
                flash(f'File uploaded but email failed: {str(e)}')

            return redirect(url_for('index'))

        flash('Invalid file type.')
        return redirect(request.url)
    return render_template("upload.html")  # Assumes you have upload.html template

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, flash
import os

@app.route('/dashboard')
def dashboard():
    upload_folder = 'uploads'
    payroll_files = []

    for filename in os.listdir(upload_folder):
        if filename.endswith('.pdf'):
            file_path = os.path.join(upload_folder, filename)
            timestamp = os.path.getmtime(file_path)
            formatted_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            payroll_files.append((filename, formatted_time))

    return render_template('dashboard.html', payroll_files=payroll_files)