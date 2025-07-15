from flask import Flask, render_template, request, redirect, flash
import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Connect to MySQL
try:
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = db.cursor()
    print("✅ MySQL connection successful")
except Exception as e:
    print(f"❌ MySQL connection failed: {e}")
    exit()

# Redirect / to /add_employee
@app.route('/')
def home():
    return redirect('/add_employee')

# Add Employee route
@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        emp_id = request.form['employee_id']
        name = request.form['name']
        position = request.form['position']
        email = request.form['email']
        salary = request.form['salary']

        sql = "INSERT INTO employees (employee_id, name, position, email, salary) VALUES (%s, %s, %s, %s, %s)"
        values = (emp_id, name, position, email, salary)

        try:
            cursor.execute(sql, values)
            db.commit()
            flash('✅ Employee added successfully!', 'success')
        except Exception as e:
            db.rollback()
            flash(f'❌ Error: {e}', 'danger')

        return redirect('/add_employee')

    return render_template('add_employee.html')

if __name__ == '__main__':
    app.run(debug=True)