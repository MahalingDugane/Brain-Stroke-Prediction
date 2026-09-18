from flask import Flask, render_template, Response, request, flash,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, UserMixin, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import numpy as np
import pandas as pd
from flask import send_from_directory
import os

app = Flask(__name__)

model = pickle.load(open('brainstroke_model.pkl', 'rb'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydb.db'
app.config['SECRET_KEY'] = 'thisissecret'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    fname = db.Column(db.String(80), nullable=False)
    lname = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    def __repr__(self):
        return '<User %r>' % self.username 
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        username = request.form.get('uname', '').strip()
        fname = request.form.get('fname', '').strip()
        lname = request.form.get('lname', '').strip()

        # Check empty fields
        if not email or not password or not username or not fname or not lname:
            flash('Please fill in all fields.', 'warning')
            return redirect('/register')

        # Check password length
        if len(password) < 6:
            flash('Password must contain at least 6 characters.', 'warning')
            return redirect('/register')

        # Check existing username
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'warning')
            return redirect('/register')

        # Check existing email
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'warning')
            return redirect('/register')

        # Securely hash the password
        hashed_password = generate_password_hash(password)

        user = User(
            email=email,
            password=hashed_password,
            username=username,
            fname=fname,
            lname=lname
        )

        db.session.add(user)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login1():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please enter username and password.', 'warning')
            return redirect('/login')

        user = User.query.filter_by(username=username).first()

        if user:
            valid_password = False

            # Check securely hashed passwords
            try:
                valid_password = check_password_hash(
                    user.password,
                    password
                )
            except (ValueError, TypeError):
                valid_password = False

            # Support old plain-text passwords temporarily
            if not valid_password and user.password == password:
                valid_password = True

                # Convert old password to a secure hash
                user.password = generate_password_hash(password)
                db.session.commit()

            if valid_password:
                login_user(user)
                return redirect('/stroke')

        flash('Invalid username or password.', 'warning')
        return redirect('/login')

    return render_template('login.html')

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/aboutus')
def About():
    return render_template("aboutus.html")

@app.route('/abstract')
def abstract():
    return render_template("abstract.html")

@app.route('/contactus')
def contactus():
    return render_template("contactus.html")

@app.route('/Model')
def Model():
    return render_template("Model.html")

@app.route('/stroke')
@login_required
def Stroke():
    return render_template('stroke.html')

@app.route('/predict1')
def Predict1():
    return render_template('predict1.html')

@app.route('/predict2')
def Predict2():
    return render_template('predict2.html')

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        try:
            gender = int(request.form.get('Gender'))
            age = float(request.form.get('SCORE'))
            hypertension = int(request.form.get('Hypertension'))
            heart_disease = int(request.form.get('Heart_Disease'))
            marriage_status = int(request.form.get('Marriage_Status'))
            work_type = int(request.form.get('Work_Type'))
            residence = int(request.form.get('Residence'))
            glucose = float(request.form.get('Depression'))
            bmi = float(request.form.get('intellectual_disability'))
            smoking_status = int(request.form.get('Smoking_Status'))

            if age < 0 or age > 120:
                return render_template(
                    'stroke.html',
                    error='Please enter a valid age.'
                )

            if glucose <= 0 or bmi <= 0:
                return render_template(
                    'stroke.html',
                    error='Please enter valid glucose and BMI values.'
                )

            final_features = [[
                gender,
                age,
                hypertension,
                heart_disease,
                marriage_status,
                work_type,
                residence,
                glucose,
                bmi,
                smoking_status
            ]]

            prediction = model.predict(final_features)
            output = prediction[0]

            if output == 0:
                return render_template(
                    'predict1.html',
                    prediction_text='You are not suffering from Brain Stroke'
                )
            else:
                return render_template(
                    'predict2.html',
                    prediction_text='Warning! Brain Stroke risk detected'
                )

        except (ValueError, TypeError):
            return render_template(
                'stroke.html',
                error='Please enter valid numbers.'
            )

    return render_template('stroke.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8081, debug=True)
