from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'  

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',   
    'database': 'real_estate'  
}

# login 
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('loggedin'):
            # Store the requested URL in session
            session['next'] = request.url
            flash('Please log in to access the property listings', 'info')
            return redirect(url_for('login_signup'))
        return f(*args, **kwargs)
    return decorated_function

# Database connection function
def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login_signup')
def login_signup():
    # if user is already logged in 
    if session.get('loggedin'):
        next_page = session.get('next')
        if next_page:
            session.pop('next', None)
            return redirect(next_page)
        return redirect(url_for('home'))
    return render_template('login_Signup.html')


@app.route('/property')
@login_required
def property():
    return render_template('property.html')


@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/about_us')
def about_us():
    return render_template('aboutUs.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Please fill all fields', 'field': 'email'}), 400
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            #  if email already exists
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            account = cursor.fetchone()
            
            if account:
                return jsonify({'error': 'This email is already registered', 'field': 'email'}), 400
            
            # insert new user data
            cursor.execute('INSERT INTO users (email, password) VALUES (%s, %s)', 
                         (email, password))  # Use the plain password directly
            conn.commit()
            
            # automatically log in if the user is already registered
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cursor.fetchone()
            
            session['loggedin'] = True
            session['id'] = user['id']
            session['email'] = user['email']
            
             
            next_page = session.get('next')
            if next_page:
                session.pop('next', None)
                return jsonify({'success': True, 'redirect': next_page}), 200
            return jsonify({'success': True, 'redirect': url_for('home')}), 200
            
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            return jsonify({'error': 'An error occurred during registration', 'field': 'email'}), 400
        finally:
            if 'conn' in locals():
                cursor.close()
                conn.close()


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # fetching user with email
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cursor.fetchone()
            
            # comparing password  
            if user and user['password'] == password:
                 
                session['loggedin'] = True
                session['id'] = user['id']
                session['email'] = user['email']
                
                
                next_page = session.get('next')
                if next_page:
                    session.pop('next', None)
                    return jsonify({'success': True, 'redirect': url_for('home')}), 200
                return jsonify({'success': True, 'redirect': url_for('home')}), 200
            else:
                return jsonify({'error': 'Invalid email or password', 'field': 'email'}), 400
                
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            return jsonify({'error': 'An error occurred', 'field': 'email'}), 400
        finally:
            if 'conn' in locals():
                cursor.close()
                conn.close()

# log out
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)