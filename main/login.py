from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import bcrypt
import pyotp
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Ensure the database is set up correctly
def create_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        password TEXT NOT NULL,
        otp_secret TEXT NOT NULL,
        face_image_path TEXT
    )
    """)
    conn.commit()
    conn.close()

# Route to the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        otp = request.form['otp']
        uploaded_face_image = request.files['face_image']

        # Get user from DB
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

        if not user:
            flash("User not found", 'danger')
            return redirect(url_for('login'))

        # Check password
        stored_password = user[2]
        if not bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            flash("Invalid password", 'danger')
            return redirect(url_for('login'))

        # Verify OTP
        otp_secret = user[3]
        if otp_secret is None:
            flash("OTP secret is missing. Please contact support.", 'danger')
            return redirect(url_for('login'))

        totp = pyotp.TOTP(otp_secret)
        if otp != totp.now():
            flash("Invalid OTP", 'danger')
            return redirect(url_for('login'))

        # Face Image Authentication
        if uploaded_face_image:
            face_image_filename = secure_filename(uploaded_face_image.filename)
            uploaded_face_image.save(os.path.join('user_faces', face_image_filename))

            # Compare face image path
            stored_face_image_path = user[4]
            if os.path.join('user_faces', face_image_filename) != stored_face_image_path:
                flash("Face image does not match", 'danger')
                return redirect(url_for('login'))

        # If everything is correct, log in the user
        session['email'] = email
        flash("Login successful!", 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')

# Route to the dashboard
@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

if __name__ == '__main__':
    create_db()
    app.run(debug=True)

