import os
import random
import string
import cv2
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from skimage.metrics import structural_similarity as ssim
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configuring Flask Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'vocloteam@gmail.com'
app.config['MAIL_PASSWORD'] = 'kdum hcbv mjxb khix'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'wav', 'mp3'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

mail = Mail(app)

# Mock database for users (simulating a simple in-memory database)
users_db = {}
otp_db = {}

# Ensure the uploads directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def send_otp(email):
    otp = ''.join(random.choices(string.digits, k=6))
    msg = Message('Your OTP for VoClo Email Verification', 
                 sender='vocloteam@gmail.com',
                 recipients=[email])
    msg.body = f'''Welcome to VoClo!
    
Your verification OTP is: {otp}
    
This OTP will expire in 10 minutes.
    
Best regards,
The VoClo Team'''
    
    try:
        mail.send(msg)
        return otp
    except Exception as e:
        flash(f"Error sending OTP: {e}", 'danger')
        return None

# Route for the home page
@app.route('/')
def home():
    return render_template('index.html')

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        uploaded_face_image = request.files.get('face_image')

        if email in users_db and check_password_hash(users_db[email]['password'], password):
            if not users_db[email]['verified']:
                flash('Please verify your email first.', 'warning')
                return redirect(url_for('verify_otp', email=email))
                
            if uploaded_face_image and allowed_file(uploaded_face_image.filename):
                uploaded_face_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                                                'temp_' + secure_filename(uploaded_face_image.filename))
                uploaded_face_image.save(uploaded_face_path)

                if authenticate_face(email, uploaded_face_path):
                    session['user_email'] = email
                    session['user_name'] = users_db[email]['name']
                    session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    flash('Login successful!', 'success')
                    return redirect(url_for('voice_auth'))
                else:
                    flash('Face authentication failed', 'danger')
                    os.remove(uploaded_face_path)  # Clean up temporary file
            else:
                flash('Invalid face image or no image uploaded', 'danger')
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

def authenticate_face(email, uploaded_face_path):
    try:
        stored_face_image_path = users_db[email]['image']
        stored_face = cv2.imread(stored_face_image_path, cv2.IMREAD_GRAYSCALE)
        uploaded_face = cv2.imread(uploaded_face_path, cv2.IMREAD_GRAYSCALE)
        
        if stored_face is None or uploaded_face is None:
            return False
            
        return compare_images(stored_face, uploaded_face)
    except Exception as e:
        print(f"Face authentication error: {e}")
        return False

def compare_images(image1, image2):
    try:
        image1_resized = cv2.resize(image1, (image2.shape[1], image2.shape[0]))
        mse_value = mean_squared_error(image1_resized, image2)
        ssim_value = compute_ssim(image1_resized, image2)
        
        print(f"MSE: {mse_value}, SSIM: {ssim_value}")
        return mse_value < 1000 and ssim_value > 0.7
    except Exception as e:
        print(f"Image comparison error: {e}")
        return False

def mean_squared_error(image1, image2):
    err = np.sum((image1.astype("float") - image2.astype("float")) ** 2)
    err /= float(image1.shape[0] * image1.shape[1])
    return err

def compute_ssim(image1, image2):
    return ssim(image1, image2)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        
        if len(password) < 8:
            flash("Password must be at least 8 characters long!", "danger")
        elif password != password_confirm:
            flash("Passwords do not match!", "danger")
        elif email in users_db:
            flash("Email already exists!", "danger")
        else:
            if 'image' not in request.files:
                flash("No file part", "danger")
                return redirect(request.url)
            
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(f"{email}_{image.filename}")
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)

                hashed_password = generate_password_hash(password)
                
                users_db[email] = {
                    'name': name,
                    'email': email,
                    'password': hashed_password,
                    'image': image_path,
                    'verified': False,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                otp = send_otp(email)
                if otp:
                    otp_db[email] = {
                        'otp': otp,
                        'created_at': datetime.now()
                    }
                    flash('Registration successful! Please verify your email.', 'success')
                    return redirect(url_for('verify_otp', email=email))
            else:
                flash("Invalid file type. Only PNG, JPG, JPEG are allowed.", "danger")
    
    return render_template('register.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    email = request.args.get('email')
    if email not in otp_db:
        flash('OTP expired or invalid. Please request a new one.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        otp_entered = request.form['otp']
        if otp_entered == otp_db[email]['otp']:
            users_db[email]['verified'] = True
            del otp_db[email]
            flash('Email verified successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('verify_otp.html', email=email)

@app.route('/voice_auth')
def voice_auth():
    if 'user_email' not in session:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))
        
    user = users_db.get(session['user_email'])
    return render_template('voice_auth.html', user=user)

@app.route('/start_voice_authentication', methods=['POST'])
def start_voice_authentication():
    if 'user_email' not in session:
        return jsonify({"error": "Not authenticated"}), 401
        
    # Here you would implement actual voice recognition
    is_match = random.choice([True, False])
    return jsonify({"success": is_match})

@app.route('/start_voice_clone_training', methods=['POST'])
def start_voice_clone_training():
    if 'user_email' not in session:
        return jsonify({"error": "Not authenticated"}), 401
        
    return jsonify({"message": "Voice clone training completed successfully!"})

@app.route('/detect_voice_type', methods=['POST'])
def detect_voice_type():
    if 'user_email' not in session:
        return jsonify({"error": "Not authenticated"}), 401
        
    audio_file = request.files.get('audio_file')
    if not audio_file or not allowed_file(audio_file.filename):
        return jsonify({"error": "Invalid or no audio file provided"}), 400
    
    is_human_voice = random.choice([True, False])
    return jsonify({
        "is_human_voice": is_human_voice,
        "confidence_score": random.uniform(0.7, 0.99)
    })

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)