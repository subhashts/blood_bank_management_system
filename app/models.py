from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    address = db.Column(db.Text, nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey('state.id'), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # patient, hospital, host, admin
    is_approved = db.Column(db.Boolean, default=True)  # False for hospital/host initially
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Additional fields for hospital
    hospital_name = db.Column(db.String(200))
    license_number = db.Column(db.String(100))
    hospital_address = db.Column(db.Text)
    hospital_contact = db.Column(db.String(20))
    
    # Additional fields for camp host
    camp_name = db.Column(db.String(200))
    camp_address = db.Column(db.Text)
    camp_contact = db.Column(db.String(20))
    
    # Relationships
    state = db.relationship('State', backref='users')
    city = db.relationship('City', backref='users')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'

class State(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    cities = db.relationship('City', backref='state', lazy='dynamic')

class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey('state.id'), nullable=False)

class BloodInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    units_available = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    hospital = db.relationship('User', backref='blood_inventory')

class BloodRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    units_requested = db.Column(db.Integer, nullable=False)
    request_type = db.Column(db.String(20), nullable=False)  # normal, critical
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    response_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    patient = db.relationship('User', foreign_keys=[patient_id], backref='blood_requests')
    hospital = db.relationship('User', foreign_keys=[hospital_id], backref='received_requests')

class BloodDonation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    camp_id = db.Column(db.Integer, db.ForeignKey('blood_camp.id'))
    blood_group = db.Column(db.String(5), nullable=False)
    units_donated = db.Column(db.Integer, default=1)
    donation_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    certificate_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    donor = db.relationship('User', foreign_keys=[donor_id], backref='donations')
    hospital = db.relationship('User', foreign_keys=[hospital_id], backref='received_donations')

class BloodCamp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey('state.id'), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    host = db.relationship('User', backref='hosted_camps')
    state = db.relationship('State', backref='camps')
    city = db.relationship('City', backref='camps')
    donations = db.relationship('BloodDonation', backref='camp')

class CampInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    camp_id = db.Column(db.Integer, db.ForeignKey('blood_camp.id'), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    units_available = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    camp = db.relationship('BloodCamp', backref='inventory')

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # donation, request, camp_registration
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='activities')