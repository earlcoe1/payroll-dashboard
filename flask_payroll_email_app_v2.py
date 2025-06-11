from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, flash
import os
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from email.message import EmailMessage
import smtplib
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_RECIPIENTS = os.getenv('EMAIL_RECIPIENTS', '').split(',')

ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
ADMIN_PASS = os.getenv('ADMIN_PASS', 'password')
SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'temporary-secret-key')

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Upload folder
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Route: Dashboard
@app.route('/')
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('login'))
    files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(filepath):
            timestamp = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
            files.append({'filename': filename, 'timestamp': timestamp})
    files.sort(key=lambda x: x['timestamp'], reverse=True)
    return render_template("index.html", files=files)

# Route: Upload file
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if not session.get('admin'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['file']
        password = request.form.get('password')

        if file and file.filename.endswith('.pdf'):
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{os.path.splitext(file.filename)[0]}_{timestamp}.pdf"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Save temp file
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], "temp_unencrypted.pdf")
            file.save(temp_path)

            # Encrypt PDF
            reader = PdfReader(temp_path)
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            if password:
                writer.encrypt(password)

            with open(filepath, 'wb') as f:
                writer.write(f)

            os.remove(temp_path)

            # Send email
            try:
                msg = EmailMessage()
                msg['Subject'] = f"Encrypted Payroll Report: {filename}"
                msg['From'] = EMAIL_SENDER
                msg['To'] = ', '.join(EMAIL_RECIPIENTS)
                msg.set_content("The latest encrypted payroll report is attached. Use the upload password to open the file.")

                with open(filepath, 'rb') as f:
                    msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=filename)

                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
                    smtp.send_message(msg)

                print("✅ Email sent successfully.")
            except Exception as e:
                print(f"❌ Email sending failed: {e}")

            return redirect(url_for('dashboard'))
        else:
            return "Only PDF files are allowed.", 400

    return render_template("upload.html")

# Route: Serve file with protection
@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    if not session.get('admin'):
        return redirect(url_for('login'))
    log_path = os.path.join(app.root_path, 'download_logs.txt')
    with open(log_path, 'a') as log:
        log.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {filename} downloaded\n")
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Route: View download logs
@app.route('/admin/logs')
def view_logs():
    if not session.get('admin'):
        return redirect(url_for('login'))
    log_path = os.path.join(app.root_path, 'download_logs.txt')
    logs = []
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            logs = f.readlines()
    return render_template("logs.html", logs=logs)

# Route: Admin login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['admin'] = True
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template("login.html")

# Route: Logout
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

# Run app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)