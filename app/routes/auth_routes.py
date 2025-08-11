from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app.models import User, db
from app.utils.location_data import get_states, get_cities_by_state
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_approved and user.role in ['hospital', 'host']:
                flash('Your account is pending approval. Please contact admin.', 'warning')
                return render_template('auth/login.html')
            
            login_user(user)
            
            # Redirect based on role
            if user.role == 'patient':
                return redirect(url_for('patient.dashboard'))
            elif user.role == 'hospital':
                return redirect(url_for('hospital.dashboard'))
            elif user.role == 'host':
                return redirect(url_for('host.dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    states = get_states()
    
    if request.method == 'POST':
        # Common fields
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        dob = datetime.strptime(request.form.get('dob'), '%Y-%m-%d').date()
        age = int(request.form.get('age'))
        blood_group = request.form.get('blood_group')
        address = request.form.get('address')
        state_id = int(request.form.get('state_id'))
        city_id = int(request.form.get('city_id'))
        role = request.form.get('role')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html', states=states)
        
        # Create user
        user = User(
            name=name,
            email=email,
            dob=dob,
            age=age,
            blood_group=blood_group,
            address=address,
            state_id=state_id,
            city_id=city_id,
            role=role
        )
        user.set_password(password)
        
        # Role-specific fields
        if role == 'hospital':
            user.hospital_name = request.form.get('hospital_name')
            user.license_number = request.form.get('license_number')
            user.hospital_address = request.form.get('hospital_address')
            user.hospital_contact = request.form.get('hospital_contact')
            user.is_approved = False  # Requires admin approval
        elif role == 'host':
            user.camp_name = request.form.get('camp_name')
            user.camp_address = request.form.get('camp_address')
            user.camp_contact = request.form.get('camp_contact')
            user.is_approved = False  # Requires admin approval
        
        db.session.add(user)
        db.session.commit()
        
        if role in ['hospital', 'host']:
            flash('Registration successful! Your account is pending approval. Admin will contact you soon.', 'info')
        else:
            flash('Registration successful! You can now login.', 'success')
            
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', states=states)

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('main.home'))