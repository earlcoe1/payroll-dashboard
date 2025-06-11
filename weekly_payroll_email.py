
import pandas as pd
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from datetime import datetime
import os
import PyPDF2
import schedule
import time
import threading

from dotenv import load_dotenv
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# 🔽 Add this line to test loading:
print("Email loaded:", EMAIL_ADDRESS)


# Step 1: Generate Mock Payroll Data
data = {
    "Employee": ["Alice Johnson", "Bob Smith", "Charlie Lee"],
    "Hours Worked": [40, 38, 42],
    "Hourly Rate": [25, 30, 28],
}
df = pd.DataFrame(data)
df["Gross Pay"] = df["Hours Worked"] * df["Hourly Rate"]

# Step 2: Create a PDF Report
pdf_filename = "payroll_report.pdf"
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="Weekly Payroll Report", ln=True, align="C")

for i in range(len(df)):
    row = df.iloc[i]
    line = f"{row['Employee']} | Hours: {row['Hours Worked']} | Rate: ${row['Hourly Rate']} | Gross Pay: ${row['Gross Pay']}"
    pdf.cell(200, 10, txt=line, ln=True)

pdf.output(pdf_filename)

# Step 3: Encrypt the PDF
password = f"tutu123-{datetime.now().strftime('%Y%m%d')}"
encrypted_pdf_filename = "encrypted_payroll_report.pdf"

with open(pdf_filename, "rb") as infile, open(encrypted_pdf_filename, "wb") as outfile:
    reader = PyPDF2.PdfReader(infile)
    writer = PyPDF2.PdfWriter()

    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    writer.write(outfile)

# Step 4: Email Setup
admin_emails = [
    "earlnimley@gmail.com",
    "coleaudreytonia@gmail.com",
    "nimleye0403@students.bowiestate.edu"
]

EMAIL_ADDRESS = "earlnimley@gmail.com"       # Replace with your Gmail
EMAIL_PASSWORD = "grwfhgkhmptdfche"         # Replace with your app password

def send_weekly_email():
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(admin_emails)
    msg["Subject"] = "Weekly Payroll Report"

    body = """Hello Admin,

Please find attached the encrypted PDF payroll report for this week.

Regards,  
Payroll System
"""
    msg.attach(MIMEText(body, "plain"))

    with open(encrypted_pdf_filename, "rb") as f:
        part = MIMEApplication(f.read(), _subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename="encrypted_payroll_report.pdf")
        msg.attach(part)

    # Send email (Uncomment to enable)
    """
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, admin_emails, msg.as_string())
    """

# Schedule to run every Monday at 08:00
schedule.every().monday.at("08:00").do(send_weekly_email)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

# Start the scheduler thread (Uncomment to enable)
# threading.Thread(target=run_scheduler, daemon=True).start()
