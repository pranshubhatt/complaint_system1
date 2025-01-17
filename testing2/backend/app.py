import datetime
from flask import Flask, render_template, request, redirect, url_for, session , flash
from flask_sqlalchemy import SQLAlchemy
from nlp import preprocess_text, categorize_complaint, assign_priority,  analyze_sentiment
from datetime import datetime, timedelta
from functools import wraps

import nltk

# Download necessary NLTK resources
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('vader_lexicon')

app = Flask(__name__)

# Set up the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1234@localhost/complaint_system'  # Replace with actual credentials
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Update with a secure secret key
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
db = SQLAlchemy(app)

# Define models for the database
class Citizen(db.Model):
    __tablename__ = 'citizens'

    citizen_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    address = db.Column(db.String(200), nullable=True)
    gender = db.Column(db.String(10), nullable=True)

class Complaint(db.Model):
    __tablename__ = 'complaints'

    complaint_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    citizen_id = db.Column(db.Integer, db.ForeignKey('citizens.citizen_id'), nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.Text, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.department_id'), nullable=False)
    priority = db.Column(db.Enum('LOW', 'MEDIUM', 'HIGH'), nullable=False)
    date_submitted = db.Column(db.Date, nullable=True)

    # Define relationships properly
    citizen = db.relationship('Citizen', backref=db.backref('complaints', lazy=True))
    department = db.relationship('Department', backref=db.backref('complaints', lazy=True))

class Department(db.Model):
    __tablename__ = 'departments'

    department_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    contact_person = db.Column(db.String(50))
    contact_number = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    address = db.Column(db.String(100))

class ComplaintLog(db.Model):
    __tablename__ = 'complaint_log'

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.complaint_id'), nullable=False)
    status = db.Column(db.Enum('In-progress', 'Resolved', 'Not resolved'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    remarks = db.Column(db.Text)

    # Relationship to link logs to the complaint
    complaint = db.relationship('Complaint', backref=db.backref('logs', cascade='all, delete-orphan'))

class Feedback(db.Model):
    __tablename__ = 'feedback'

    feedback_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.complaint_id'), nullable=False)
    rating = db.Column(db.Integer, db.CheckConstraint('rating BETWEEN 1 AND 5'))
    comments = db.Column(db.Text)
    date_provided = db.Column(db.Date)

    # Relationship to link feedback to complaint
    complaint = db.relationship('Complaint', backref=db.backref('feedback', cascade='all, delete-orphan'))

# Add these validation functions at the top if not already present
def validate_email(email):
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    import re
    pattern = r'^\d{10}$'
    return re.match(pattern, phone) is not None

# Add these helper functions for navigation protection
def citizen_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'citizen_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('citizen_login'))
        return f(*args, **kwargs)
    return decorated_function

def department_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'department_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('department_login'))
        return f(*args, **kwargs)
    return decorated_function

# Home route
@app.route('/')
def index():
    # Only redirect to dashboards for direct access to root URL
    if 'citizen_id' in session and request.path == '/':
        return redirect(url_for('citizen_dashboard'))
    if 'department_id' in session and request.path == '/':
        return redirect(url_for('department_dashboard'))
    return render_template('index.html')

# New Home route
@app.route('/home')
def home():
    # Clear any existing session
    session.clear()
    # Always render index.html without redirecting to dashboard
    return render_template('index.html')

# Citizen Registration Route
@app.route('/citizen-register', methods=['GET', 'POST'])
def citizen_register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        contact_number = request.form.get('contact_number', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        gender = request.form.get('gender')

        # Validation
        if not all([name, contact_number, email, address, gender]):
            flash('All fields are required', 'error')
            return redirect(url_for('citizen_register'))

        if not validate_email(email):
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('citizen_register'))

        if not validate_phone(contact_number):
            flash('Please enter a valid 10-digit phone number', 'error')
            return redirect(url_for('citizen_register'))

        # Check if email already exists
        existing_user = Citizen.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'error')
            return redirect(url_for('citizen_register'))

        try:
            new_citizen = Citizen(
                name=name,
                contact_number=contact_number,
                email=email,
                address=address,
                gender=gender
            )
            db.session.add(new_citizen)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('citizen_login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
            return redirect(url_for('citizen_register'))

    return render_template('register.html')

# Citizen Login Route
@app.route('/citizen-login', methods=['GET', 'POST'])
def citizen_login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        contact_number = request.form['contact_number']
        
        citizen = Citizen.query.filter_by(email=email, contact_number=contact_number).first()
        if citizen:
            session['citizen_id'] = citizen.citizen_id  # Store citizen ID in session
            return redirect(url_for('citizen_dashboard'))
        else:
            error = 'Invalid login credentials. Please try again.'

    return render_template('login.html', error=error)

# Add this decorator for database error handling
def handle_db_error(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            db.session.rollback()
            flash(f'Database error occurred: {str(e)}', 'error')
            return redirect(url_for('index'))
    return decorated_function

def validate_complaint(description):
    if not description or len(description.strip()) < 10:
        return False, "Complaint description must be at least 10 characters long"
    if len(description) > 1000:
        return False, "Complaint description cannot exceed 1000 characters"
    return True, ""

# Use it on routes that interact with database
@app.route('/register-complaint', methods=['GET', 'POST'])
def register_complaint():
    if 'citizen_id' not in session:
        return redirect(url_for('citizen_login'))
    
    # Get citizen data
    citizen = Citizen.query.get(session['citizen_id'])
    if not citizen:
        flash('Citizen not found', 'error')
        return redirect(url_for('citizen_login'))

    if request.method == 'POST':
        description = request.form.get('description')
        is_valid, message = validate_complaint(description)
        
        if not is_valid:
            flash(message, 'error')
            return redirect(url_for('register_complaint'))

        try:
            # Process complaint with NLP
            processed_text = preprocess_text(description)
            category, department_id = categorize_complaint(processed_text)
            priority = assign_priority(processed_text)

            # Create complaint
            new_complaint = Complaint(
                citizen_id=session['citizen_id'],
                category=category,
                description=description,
                department_id=department_id,
                priority=priority,
                date_submitted=datetime.now().date()
            )
            
            db.session.add(new_complaint)
            db.session.commit()

            flash('Complaint registered successfully!', 'success')
            return redirect(url_for('citizen_dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error registering complaint: {str(e)}', 'error')
            return redirect(url_for('register_complaint'))

    # Pass the citizen object to the template
    return render_template('register_complaint.html', citizen=citizen)


# Logout Route
@app.route('/logout')
def logout():
    session.pop('citizen_id', None)
    session.pop('department_id', None)
    return redirect(url_for('index'))

# Department Registration Route
@app.route('/department-register', methods=['GET', 'POST'])
def department_register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        contact_person = request.form.get('contact_person', '').strip()
        contact_number = request.form.get('contact_number', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()

        # Validation
        if not all([name, contact_person, contact_number, email, address]):
            flash('All fields are required', 'error')
            return redirect(url_for('department_register'))

        if not validate_email(email):
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('department_register'))

        if not validate_phone(contact_number):
            flash('Please enter a valid 10-digit phone number', 'error')
            return redirect(url_for('department_register'))

        # Check if department already exists
        existing_dept = Department.query.filter_by(email=email).first()
        if existing_dept:
            flash('Department already registered with this email', 'error')
            return redirect(url_for('department_register'))

        try:
            new_department = Department(
                name=name,
                contact_person=contact_person,
                contact_number=contact_number,
                email=email,
                address=address
            )
            db.session.add(new_department)
            db.session.commit()
            flash('Department registration successful! Please login.', 'success')
            return redirect(url_for('department_login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
            return redirect(url_for('department_register'))

    return render_template('department_register.html')

# Department Login Route
@app.route('/department-login', methods=['GET', 'POST'])
def department_login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        contact_number = request.form['contact_number']
        
        department = Department.query.filter_by(email=email, contact_number=contact_number).first()
        if department:
            session['department_id'] = department.department_id  # Store department_id in session
            return redirect(url_for('department_dashboard'))
        else:
            error = 'Invalid login credentials. Please try again.'

    return render_template('department_login.html', error=error)



# Citizen Dashboard Route
@app.route('/citizen-dashboard')
@citizen_login_required
def citizen_dashboard():
    citizen = Citizen.query.get(session['citizen_id'])
    if not citizen:
        session.clear()
        flash('Account not found', 'error')
        return redirect(url_for('citizen_login'))
    
    complaints = Complaint.query.filter_by(citizen_id=citizen.citizen_id).all()
    return render_template('citizen_dashboard.html', citizen=citizen, complaints=complaints)

# Department Dashboard Route

@app.route('/department-dashboard', methods=['GET', 'POST'])
@department_login_required
def department_dashboard():
    department = Department.query.get(session['department_id'])
    if not department:
        session.clear()
        flash('Department not found', 'error')
        return redirect(url_for('department_login'))
    
    selected_status = request.args.get('status', 'all')
    # Mapping of department ID to name
    department_names = {
        1: "Sanitation",
        2: "Water",
        3: "Infrastructure",
        4: "Public Safety",
        5: "General"
    }

    department_name = department_names.get(department.department_id, "Unknown Department")

    # Query complaints for the department, sorting by priority
    query = Complaint.query.filter_by(department_id=department.department_id)

    if selected_status != 'all':
        query = query.join(ComplaintLog).filter(ComplaintLog.status == selected_status)

    # Sort complaints by priority (assuming priority is an integer or comparable field)
    complaints = query.order_by(Complaint.priority.asc()).all()  # Sort by priority in ascending order

    # Add latest status and remarks for each complaint
    for complaint in complaints:
        latest_log = ComplaintLog.query.filter_by(complaint_id=complaint.complaint_id).order_by(ComplaintLog.timestamp.desc()).first()
        complaint.latest_status = latest_log.status if latest_log else "Pending"
        complaint.latest_remarks = latest_log.remarks if latest_log else "No remarks yet"

    if request.method == 'POST':
        for complaint in complaints:
            complaint_id = request.form.get(f'complaint_id_{complaint.complaint_id}')
            status = request.form.get(f'status_{complaint.complaint_id}')
            remarks = request.form.get(f'remarks_{complaint.complaint_id}')

            if complaint_id:
                # Create a new entry in ComplaintLog for status and remarks
                log_entry = ComplaintLog(
                    complaint_id=complaint_id,
                    status=status,
                    remarks=remarks,
                    timestamp=datetime.now()
                )
                db.session.add(log_entry)
                db.session.commit()

                # Fetch the updated complaint and its latest log entry again after the update
                complaint = Complaint.query.get(complaint_id)
                latest_log = ComplaintLog.query.filter_by(complaint_id=complaint.complaint_id).order_by(ComplaintLog.timestamp.desc()).first()

                # Update the status and remarks to the complaint object for frontend rendering
                complaint.latest_status = latest_log.status if latest_log else "Pending"
                complaint.latest_remarks = latest_log.remarks if latest_log else "No remarks yet"

    return render_template('department_dashboard.html', complaints=complaints, selected_status=selected_status, department_name=department_name)

# View Complaints Route
@app.route('/view-complaint/<int:complaint_id>', methods=['GET'])
@citizen_login_required
def view_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    
    if complaint.citizen_id != session['citizen_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('citizen_dashboard'))
    
    # Get department name from the department_id
    department_names = {
        1: "Sanitation",
        2: "Water",
        3: "Infrastructure",
        4: "Public Safety",
        5: "General"
    }
    
    department_name = department_names.get(complaint.department_id, "Unknown Department")
    
    return render_template('view_complaint.html', 
                         complaint=complaint,
                         department_name=department_name)


# Update Complaint Status Route
@app.route('/update-complaint-status/<int:complaint_id>', methods=['POST'])
def update_complaint_status(complaint_id):
    if 'department_id' not in session:
        return redirect(url_for('department_login'))

    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        
        # Security check
        if complaint.department_id != session['department_id']:
            flash('Unauthorized access', 'error')
            return redirect(url_for('department_dashboard'))

        status = request.form.get('status')
        remarks = request.form.get('remarks')

        # Validate status
        valid_statuses = ['In-progress', 'Resolved', 'Not resolved']
        if status not in valid_statuses:
            flash('Invalid status value', 'error')
            return redirect(url_for('department_dashboard'))

        # Validate remarks
        if not remarks or len(remarks.strip()) < 5:
            flash('Please provide meaningful remarks', 'error')
            return redirect(url_for('department_dashboard'))

        # Create log entry
        log = ComplaintLog(
            complaint_id=complaint_id,
            status=status,
            remarks=remarks,
            timestamp=datetime.now()
        )
        
        db.session.add(log)
        db.session.commit()

        flash('Status updated successfully', 'success')
        return redirect(url_for('department_dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating status: {str(e)}', 'error')
        return redirect(url_for('department_dashboard'))

# Add these routes after your existing routes

@app.route('/feedback-form/<int:complaint_id>')
def feedback_form(complaint_id):
    if 'citizen_id' not in session:
        return redirect(url_for('citizen_login'))
    
    complaint = Complaint.query.get_or_404(complaint_id)
    
    # Check if this complaint belongs to the logged-in citizen
    if complaint.citizen_id != session['citizen_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('citizen_dashboard'))
    
    return render_template('feedback_form.html', complaint=complaint)

@app.route('/submit-feedback/<int:complaint_id>', methods=['POST'])
def submit_feedback(complaint_id):
    if 'citizen_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('citizen_login'))
    
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        
        # Check if this complaint belongs to the logged-in citizen
        if complaint.citizen_id != session['citizen_id']:
            flash('Unauthorized access', 'error')
            return redirect(url_for('citizen_dashboard'))
        
        # Check if feedback already exists
        existing_feedback = Feedback.query.filter_by(complaint_id=complaint_id).first()
        if existing_feedback:
            flash('Feedback has already been submitted for this complaint', 'warning')
            return redirect(url_for('citizen_dashboard'))
        
        rating = request.form.get('rating')
        comments = request.form.get('comments')
        
        if not rating or not comments:
            flash('Please provide both rating and comments', 'error')
            return redirect(url_for('feedback_form', complaint_id=complaint_id))
        
        # Create new feedback entry
        feedback = Feedback(
            complaint_id=complaint_id,
            rating=int(rating),
            comments=comments,
            date_provided=datetime.now().date()
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('citizen_dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('citizen_dashboard'))

# Add session protection
@app.before_request
def before_request():
    if 'last_activity' in session:
        # Session timeout after 30 minutes of inactivity
        last_activity = datetime.fromtimestamp(session['last_activity'])
        if datetime.now() - last_activity > timedelta(minutes=30):
            session.clear()
            flash('Session expired. Please login again.', 'warning')
            return redirect(url_for('index'))
    session['last_activity'] = datetime.now().timestamp()

# Add error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Add error handling for common navigation issues
@app.errorhandler(401)
def unauthorized_error(error):
    flash('Please login to access this page', 'error')
    return redirect(url_for('index'))

@app.errorhandler(403)
def forbidden_error(error):
    flash('You do not have permission to access this page', 'error')
    return redirect(url_for('index'))

# Run the application
if __name__ == "__main__":
    app.run(debug=True, port=5001)  # Change the port number to 5001 or any other port

