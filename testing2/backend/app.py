from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from nlp import preprocess_text, categorize_complaint, assign_priority,  analyze_sentiment


import nltk

# Download necessary NLTK resources
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('vader_lexicon')

app = Flask(__name__)

# Set up the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/complaint_system'  # Replace with actual credentials
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Update with a secure secret key , Optional
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

class Department(db.Model):
    __tablename__ = 'departments'

    department_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    contact_person = db.Column(db.String(50))
    contact_number = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    address = db.Column(db.String(100))


# Home route
@app.route('/')
def index():
    return render_template('index.html')


# Citizen Registration Route
@app.route('/citizen-register', methods=['GET', 'POST'])
def citizen_register():
    if request.method == 'POST':
        name = request.form['name']
        contact_number = request.form['contact_number']
        email = request.form['email']
        address = request.form['address']
        gender = request.form['gender']

        new_citizen = Citizen(name=name, contact_number=contact_number, email=email, address=address, gender=gender)
        db.session.add(new_citizen)
        db.session.commit()

        return redirect(url_for('citizen_login'))

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

# Complaint Submission Route
@app.route('/register-complaint', methods=['GET', 'POST'])
def register_complaint():
    if 'citizen_id' not in session:
        return redirect(url_for('citizen_login'))

    citizen_id = session['citizen_id']
    citizen = Citizen.query.get(citizen_id)  # Get the logged-in citizen's data

    if request.method == 'POST':
        description = request.form['description']
        
        # NLP processing
        processed_text = preprocess_text(description)
        category, department_id = categorize_complaint(processed_text)  # Adjust to return both category and department_id
        priority = assign_priority(processed_text)

        # Map category to department_id (already handled in categorize_complaint)
        # department_id is already returned by categorize_complaint, so no need to use the category_to_department dict here

        # Create the new complaint record
        new_complaint = Complaint(
            citizen_id=citizen_id,
            category=category,
            description=description,
            department_id=department_id,
            priority=priority,
            date_submitted=db.func.current_date(),
        )
        
        db.session.add(new_complaint)
        db.session.commit()

        return redirect(url_for('citizen_dashboard'))

    return render_template('register_complaint.html', citizen=citizen)




# Logout Route
@app.route('/logout')
def logout():
    session.pop('citizen_id', None)
    return redirect(url_for('index'))

# Department Registration Route
@app.route('/department-register', methods=['GET', 'POST'])
def department_register():
    if request.method == 'POST':
        name = request.form['name']
        contact_person = request.form['contact_person']
        contact_number = request.form['contact_number']
        email = request.form['email']
        address = request.form['address']

        new_department = Department(name=name, contact_person=contact_person, contact_number=contact_number, email=email, address=address)
        db.session.add(new_department)
        db.session.commit()

        return redirect(url_for('department_login'))

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
            return redirect(url_for('index'))
        else:
            error = 'Invalid login credentials. Please try again.'

    return render_template('department_login.html', error=error)

# Citizen Dashboard Route
@app.route('/citizen-dashboard')
def citizen_dashboard():
    if 'citizen_id' not in session:
        return redirect(url_for('citizen_login'))

    citizen_id = session['citizen_id']
    citizen = Citizen.query.get(citizen_id)
    complaints = Complaint.query.filter_by(citizen_id=citizen_id).all()
    return render_template('citizen_dashboard.html', citizen=citizen, complaints=complaints)


# Run the application
if __name__ == "__main__":
    app.run(debug=True)
