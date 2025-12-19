from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'hackathon_secret_key' # Security key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///karigar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'customer' or 'provider'
    category = db.Column(db.String(50), nullable=True) # Only for providers (e.g., Plumber)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, nullable=False)
    provider_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Accepted

# --- Routes ---

@app.route('/')
def home():
    # Show all providers on home page for simplicity
    providers = User.query.filter_by(role='provider').all()
    return render_template('index.html', providers=providers)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        role = request.form['role'] # customer or provider
        
        # Simple Login/Register (Hackathon style: if user doesn't exist, create them)
        user = User.query.filter_by(username=username).first()
        if not user:
            category = request.form.get('category') if role == 'provider' else None
            user = User(username=username, role=role, category=category)
            db.session.add(user)
            db.session.commit()
        
        session['user_id'] = user.id
        session['role'] = user.role
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if user.role == 'customer':
        # Show my bookings
        my_bookings = Booking.query.filter_by(customer_id=user.id).all()
        # Helper to get provider names (simple logic for hackathon)
        bookings_data = []
        for b in my_bookings:
            prov = User.query.get(b.provider_id)
            bookings_data.append({'id': b.id, 'provider': prov.username, 'status': b.status})
        return render_template('dashboard.html', user=user, bookings=bookings_data)
    
    else: # Provider
        # Show requests coming to me
        requests = Booking.query.filter_by(provider_id=user.id).all()
        req_data = []
        for r in requests:
            cust = User.query.get(r.customer_id)
            req_data.append({'id': r.id, 'customer': cust.username, 'status': r.status})
        return render_template('dashboard.html', user=user, requests=req_data)

@app.route('/book/<int:provider_id>')
def book(provider_id):
    if 'user_id' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
    
    new_booking = Booking(customer_id=session['user_id'], provider_id=provider_id)
    db.session.add(new_booking)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/accept/<int:booking_id>')
def accept(booking_id):
    # Provider accepts booking
    booking = Booking.query.get(booking_id)
    booking.status = 'Accepted'
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Initialize DB
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)