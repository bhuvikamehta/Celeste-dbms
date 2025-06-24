from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')

# Database configuration using environment variables
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'CELESTE'),
            port=int(os.getenv('DB_PORT', '3306'))
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Database connection failed: {err}")
        return None

@app.route('/')
def landing():
    return render_template("landing.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = get_db_connection()
        if connection is None:
            flash('Database connection failed. Please try again later.', 'error')
            return render_template('login.html')
        
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            
            if user:
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')
        except mysql.connector.Error as err:
            flash(f'Database error: {err}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        connection = get_db_connection()
        if connection is None:
            flash('Database connection failed. Please try again later.', 'error')
            return render_template('register.html')
        
        try:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", 
                         (username, password, email))
            connection.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f'Registration failed: {err}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('landing'))

# Health check endpoint for Render
@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    # For local development
    app.run(debug=True)
    # For production, this won't be used as gunicorn will run the app
