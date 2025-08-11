from flask import Blueprint, render_template, request, jsonify
from app.models import User, BloodInventory, BloodCamp, State, City
from app.utils.location_data import get_states, get_cities_by_state
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Home page with blood compatibility chart and search options"""
    states = get_states()
    return render_template('home.html', states=states)

@main_bp.route('/api/cities/<int:state_id>')
def get_cities(state_id):
    """API endpoint to get cities for a state"""
    cities = get_cities_by_state(state_id)
    return jsonify([{'id': city.id, 'name': city.name} for city in cities])

@main_bp.route('/search/blood')
def search_blood():
    """Search for blood availability in hospitals"""
    state_id = request.args.get('state_id', type=int)
    city_id = request.args.get('city_id', type=int)
    blood_group = request.args.get('blood_group', '')
    
    if not all([state_id, city_id]):
        return render_template('search_results.html', hospitals=[], search_type='blood')
    
    # Find hospitals in the selected city with blood inventory
    hospitals_query = User.query.filter_by(
        role='hospital', 
        is_approved=True,
        state_id=state_id,
        city_id=city_id
    )
    
    hospitals = []
    for hospital in hospitals_query.all():
        inventory_query = BloodInventory.query.filter_by(hospital_id=hospital.id)
        
        if blood_group:
            inventory_query = inventory_query.filter_by(blood_group=blood_group)
            inventory = inventory_query.filter(BloodInventory.units_available > 0).all()
        else:
            inventory = inventory_query.filter(BloodInventory.units_available > 0).all()
        
        if inventory:
            hospital_data = {
                'hospital': hospital,
                'inventory': inventory,
                'state': hospital.state.name,
                'city': hospital.city.name
            }
            hospitals.append(hospital_data)
    
    return render_template('search_results.html', 
                         hospitals=hospitals, 
                         search_type='blood',
                         selected_blood_group=blood_group)

@main_bp.route('/search/camps')
def search_camps():
    """Search for active blood camps"""
    state_id = request.args.get('state_id', type=int)
    city_id = request.args.get('city_id', type=int)
    
    if not all([state_id, city_id]):
        return render_template('search_results.html', camps=[], search_type='camps')
    
    # Find active camps in the selected city
    today = datetime.now().date()
    camps = BloodCamp.query.filter_by(
        state_id=state_id,
        city_id=city_id,
        is_active=True
    ).filter(
        BloodCamp.start_date <= today,
        BloodCamp.end_date >= today
    ).all()
    
    return render_template('search_results.html', 
                         camps=camps, 
                         search_type='camps')

@main_bp.route('/compatibility')
def blood_compatibility():
    """Blood compatibility information page"""
    compatibility_data = {
        'A+': {'can_donate_to': ['A+', 'AB+'], 'can_receive_from': ['A+', 'A-', 'O+', 'O-']},
        'A-': {'can_donate_to': ['A+', 'A-', 'AB+', 'AB-'], 'can_receive_from': ['A-', 'O-']},
        'B+': {'can_donate_to': ['B+', 'AB+'], 'can_receive_from': ['B+', 'B-', 'O+', 'O-']},
        'B-': {'can_donate_to': ['B+', 'B-', 'AB+', 'AB-'], 'can_receive_from': ['B-', 'O-']},
        'AB+': {'can_donate_to': ['AB+'], 'can_receive_from': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']},
        'AB-': {'can_donate_to': ['AB+', 'AB-'], 'can_receive_from': ['A-', 'B-', 'AB-', 'O-']},
        'O+': {'can_donate_to': ['A+', 'B+', 'AB+', 'O+'], 'can_receive_from': ['O+', 'O-']},
        'O-': {'can_donate_to': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'], 'can_receive_from': ['O-']},
    }
    
    return render_template('compatibility.html', compatibility_data=compatibility_data)