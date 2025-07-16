from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helper to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Dummy admin login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == os.getenv("ADMIN_USERNAME") and password == os.getenv("ADMIN_PASSWORD"):
            session["admin"] = True
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect(url_for("login"))
    
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    files.sort(reverse=True)
    return render_template("dashboard.html", files=files)

@app.route("/upload-form", methods=["GET"])
def upload_form():
    if "admin" not in session:
        return redirect(url_for("login"))
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "admin" not in session:
        return redirect(url_for("login"))

    if 'payroll_file' not in request.files:
        flash('No file part')
        return redirect(url_for("upload_form"))
    
    file = request.files['payroll_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for("upload_form"))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        file.save(file_path)

        # Optional PDF encryption if password is provided (placeholder)
        password = request.form.get("pdf_password")
        if password and new_filename.endswith(".pdf"):
            # Add your PDF encryption logic here
            pass

        # Send email with attachment (placeholder)
        subject = request.form.get("email_subject", "Payroll Report")
        body = request.form.get("email_body", "Please find the payroll report attached.")
        # Add your email-sending function here, using subject, body, and file_path

        flash('Payroll report uploaded and email sent.')
        return redirect(url_for('dashboard'))

    flash('Invalid file format. Only PDF and XLSX allowed.')
    return redirect(url_for("upload_form"))

@app.route("/uploads/<filename>")
def download_file(filename):
    if "admin" not in session:
        return redirect(url_for("login"))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))

# Main entry point for Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)