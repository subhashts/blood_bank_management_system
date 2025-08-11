from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from app.models import User, BloodInventory, BloodRequest, BloodDonation, BloodCamp, Activity, db
from app.utils.location_data import get_states, get_cities_by_state
from app.utils.certificate_generator import generate_donation_certificate
from datetime import datetime, date
import os
# from app.models import Hospital


patient_bp = Blueprint('patient', __name__)

@patient_bp.before_request
@login_required
def require_patient():
    """Ensure only patients can access these routes"""
    if current_user.role != 'patient':
        flash('Access denied', 'error')
        return redirect(url_for('main.home'))


@patient_bp.route("/search/blood", methods=["GET", "POST"])
@login_required
def search_blood():
    hospitals = []
    cities = db.session.query(Hospital.hospital_city).distinct().all()
    cities = [c[0] for c in cities]  # Flatten tuples to list of city names
    selected_city = None

    if request.method == "POST":
        selected_city = request.form.get("city")
        if selected_city:
            hospitals = Hospital.query.filter_by(hospital_city=selected_city).all()

    return render_template(
        "search_blood.html",
        cities=cities,
        hospitals=hospitals,
        selected_city=selected_city
    )
# app/patient_routes.py
# 
# app/routes/patient_routes.py
from app.models import User, BloodInventory  # Import User model instead of Hospital

@patient_bp.route('/list-hospitals')
@login_required
def list_hospitals():
    user_city = current_user.city_id  # We use the city_id from the logged-in patient.

    # Get all hospitals in the patient's city
    hospitals = User.query.filter_by(
        role='hospital',
        city_id=user_city
    ).all()

    # Now get their blood inventory
    hospital_data = []
    for hospital in hospitals:
        inventory = BloodInventory.query.filter_by(hospital_id=hospital.id).all()
        hospital_data.append({
            'hospital': hospital,
            'inventory': inventory
        })

    return render_template('list_hosp.html', hospitals=hospital_data)

@patient_bp.route('/dashboard')
@login_required
def dashboard():
    """Patient dashboard with recent activities and certificate download link"""
    # Quick stats
    pending_requests = BloodRequest.query.filter_by(
        patient_id=current_user.id, status='pending'
    ).count()

    pending_donations = BloodDonation.query.filter_by(
        donor_id=current_user.id, status='pending'
    ).count()

    # Recent activities (you might already have a query like this)
    recent_activities = Activity.query.filter_by(
        user_id=current_user.id
    ).order_by(Activity.created_at.desc()).limit(10).all()

    # Attach donation_id and certificate_generated to activities for template
    for act in recent_activities:
        if act.activity_type == 'donation':
            donation = BloodDonation.query.filter_by(
                donor_id=current_user.id
            ).order_by(BloodDonation.created_at.desc()).first()

            if donation:
                act.donation_id = donation.id
                act.certificate_generated = donation.certificate_generated
                act.status = donation.status
            else:
                act.donation_id = None
                act.certificate_generated = False
                act.status = None
        else:
            act.donation_id = None
            act.certificate_generated = False
            act.status = None

    return render_template(
        'patient/dashboard.html',
        pending_requests=pending_requests,
        pending_donations=pending_donations,
        recent_activities=recent_activities
    )

@patient_bp.route('/request-blood', defaults={'hospital_id': None}, methods=['GET', 'POST'])
@patient_bp.route('/request-blood/<int:hospital_id>', methods=['GET', 'POST'])
@login_required
def request_blood(hospital_id):
    """Request blood — works for both direct hospital requests and general requests"""

    # If a hospital is pre-selected
    if hospital_id:
        hospital = User.query.get_or_404(hospital_id)
        hospitals = None  # dropdown not needed
        inventory = BloodInventory.query.filter_by(hospital_id=hospital_id)\
                                        .filter(BloodInventory.units_available > 0).all()
    else:
        # Get all hospitals for dropdown
        hospitals = User.query.filter_by(role='hospital').all()
        hospital = None
        inventory = None  # inventory shown only when hospital is fixed

    if request.method == 'POST':
        # If hospital not fixed in URL, get from form
        if not hospital_id:
            hospital_id = int(request.form.get('hospital_id'))
            hospital = User.query.get_or_404(hospital_id)

        blood_group = request.form.get('blood_group')
        units_requested = int(request.form.get('units_requested'))
        request_type = request.form.get('request_type')
        notes = request.form.get('notes', '')

        # Optional: Check hospital inventory
        inventory_check = BloodInventory.query.filter_by(
            hospital_id=hospital_id,
            blood_group=blood_group
        ).first()

        if not inventory_check or inventory_check.units_available < units_requested:
            flash('Insufficient blood units available', 'error')
            return redirect(url_for('main.search_blood'))

        # Create the request
        blood_request = BloodRequest(
            patient_id=current_user.id,
            hospital_id=hospital_id,
            blood_group=blood_group,
            units_requested=units_requested,
            request_type=request_type,
            notes=notes
        )
        db.session.add(blood_request)

        # Log activity
        activity = Activity(
            user_id=current_user.id,
            activity_type='request',
            description=f'Requested {units_requested} units of {blood_group} blood from {hospital.hospital_name}'
        )
        db.session.add(activity)

        db.session.commit()
        flash('Blood request submitted successfully', 'success')
        return redirect(url_for('patient.dashboard'))

    return render_template(
        'patient/request_blood.html',
        hospital=hospital,
        hospitals=hospitals,
        inventory=inventory
    )


@patient_bp.route('/donate-blood', methods=['GET', 'POST'])
def donate_blood():
    """Donate blood to a hospital"""
    states = get_states()
    
    if request.method == 'POST':
        state_id = int(request.form.get('state_id'))
        city_id = int(request.form.get('city_id'))
        hospital_id = int(request.form.get('hospital_id'))
        donation_date = datetime.strptime(request.form.get('donation_date'), '%Y-%m-%d').date()
        
        # Create donation record
        donation = BloodDonation(
            donor_id=current_user.id,
            hospital_id=hospital_id,
            blood_group=current_user.blood_group,
            donation_date=donation_date
        )
        
        db.session.add(donation)
        
        # Add activity
        hospital = User.query.get(hospital_id)
        activity = Activity(
            user_id=current_user.id,
            activity_type='donation',
            description=f'Scheduled blood donation at {hospital.hospital_name} on {donation_date.strftime("%B %d, %Y")}'
        )
        db.session.add(activity)
        
        db.session.commit()
        
        flash('Blood donation scheduled successfully. Awaiting hospital approval.', 'success')
        return redirect(url_for('patient.dashboard'))
    
    return render_template('patient/donate_blood.html', states=states)

@patient_bp.route('/register-camp', methods=['GET', 'POST'])
def register_camp():
    """Register for a blood camp"""
    states = get_states()
    
    if request.method == 'POST':
        state_id = int(request.form.get('state_id'))
        city_id = int(request.form.get('city_id'))
        camp_id = int(request.form.get('camp_id'))
        donation_date = datetime.strptime(request.form.get('donation_date'), '%Y-%m-%d').date()
        
        # Create camp donation record
        donation = BloodDonation(
            donor_id=current_user.id,
            camp_id=camp_id,
            blood_group=current_user.blood_group,
            donation_date=donation_date
        )
        
        db.session.add(donation)
        
        # Add activity
        camp = BloodCamp.query.get(camp_id)
        activity = Activity(
            user_id=current_user.id,
            activity_type='camp_registration',
            description=f'Registered for blood camp: {camp.name} on {donation_date.strftime("%B %d, %Y")}'
        )
        db.session.add(activity)
        
        db.session.commit()
        
        flash('Camp registration successful. Awaiting approval.', 'success')
        return redirect(url_for('patient.dashboard'))
    
    return render_template('patient/register_camp.html', states=states)

@patient_bp.route('/api/hospitals/<int:state_id>/<int:city_id>')
def get_hospitals(state_id, city_id):
    """Get hospitals for a state and city"""
    hospitals = User.query.filter_by(
        role='hospital',
        is_approved=True,
        state_id=state_id,
        city_id=city_id
    ).all()
    
    return {'hospitals': [{'id': h.id, 'name': h.hospital_name} for h in hospitals]}

@patient_bp.route('/api/camps/<int:state_id>/<int:city_id>')
def get_camps(state_id, city_id):
    """Get active camps for a state and city"""
    today = date.today()
    camps = BloodCamp.query.filter_by(
        state_id=state_id,
        city_id=city_id,
        is_active=True
    ).filter(
        BloodCamp.start_date <= today,
        BloodCamp.end_date >= today
    ).all()
    
    return {'camps': [{'id': c.id, 'name': c.name} for c in camps]}


@patient_bp.route('/my-requests')
@login_required
def my_requests():
    """View patient's blood requests"""
    # Query the BloodRequest model for the logged-in patient's requests
    requests = BloodRequest.query.filter_by(patient_id=current_user.id)\
                                .order_by(BloodRequest.request_date.desc()).all()
    
    # Pass the requests to the template
    return render_template('patient/my_requests.html', requests=requests)



@patient_bp.route('/my-donations')
def my_donations():
    """View patient's blood donations"""
    donations = BloodDonation.query.filter_by(donor_id=current_user.id)\
                                  .order_by(BloodDonation.created_at.desc()).all()
    
    return render_template('patient/my_donations.html', donations=donations)

from flask import current_app  # make sure this import is at the top with the others

@patient_bp.route('/download-certificate/<int:donation_id>')
def download_certificate(donation_id):
    """Download donation certificate"""
    donation = BloodDonation.query.filter_by(
        id=donation_id, 
        donor_id=current_user.id,
        status='approved',
        certificate_generated=True
    ).first_or_404()
    
    # Generate certificate if not exists
    hospital_name = donation.hospital.hospital_name if donation.hospital else None
    camp_name = donation.camp.name if donation.camp else None
    
    filename = generate_donation_certificate(
        donation, 
        current_user.name, 
        hospital_name=hospital_name,
        camp_name=camp_name
    )
    
    # Use absolute path to avoid file not found errors
    filepath = os.path.join(current_app.root_path, 'static', 'certificates', filename)
    
    return send_file(filepath, as_attachment=True, download_name=f'donation_certificate_{donation_id}.pdf')
