from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file,current_app
from flask_login import login_required, current_user
from app.models import BloodCamp, CampInventory, BloodDonation, db
from app.utils.location_data import get_states, get_cities_by_state
from app.utils.report_generator import generate_camp_donor_report
from datetime import datetime, date
import os

host_bp = Blueprint('host', __name__)

@host_bp.before_request
@login_required
def require_host():
    """Ensure only approved hosts can access these routes"""
    if current_user.role != 'host' or not current_user.is_approved:
        flash('Access denied', 'error')
        return redirect(url_for('main.home'))

@host_bp.route('/dashboard')
def dashboard():
    """Host dashboard"""
    # Get active camps
    active_camps = BloodCamp.query.filter_by(host_id=current_user.id, is_active=True).count()
    
    # Get pending donations across 
    pending_donations = BloodDonation.query.join(BloodCamp)\
                                          .filter(BloodCamp.host_id == current_user.id,
                                                 BloodDonation.status == 'pending').count()
    
    # Get recent camps
    recent_camps = BloodCamp.query.filter_by(host_id=current_user.id)\
                                 .order_by(BloodCamp.created_at.desc())\
                                 .limit(5).all()
    
    # add today's date as a Python date (so it can be compared to camp.start_date/end_date which are db.Date)
    today = date.today()
    
    return render_template('host/dashboard.html',
                         today=today,
                         active_camps=active_camps,
                         pending_donations=pending_donations,
                         recent_camps=recent_camps)

@host_bp.route('/camps', methods=['GET', 'POST'])
def manage_camps():
    """Manage blood camps"""
    states = get_states()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            name = request.form.get('name')
            address = request.form.get('address')
            state_id = int(request.form.get('state_id'))
            city_id = int(request.form.get('city_id'))
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            contact_number = request.form.get('contact_number')
            
            if start_date >= end_date:
                flash('End date must be after start date', 'error')
                return redirect(url_for('host.manage_camps'))
            
            camp = BloodCamp(
                host_id=current_user.id,
                name=name,
                address=address,
                state_id=state_id,
                city_id=city_id,
                start_date=start_date,
                end_date=end_date,
                contact_number=contact_number
            )
            
            db.session.add(camp)
            db.session.commit()
            
            flash('Blood camp created successfully', 'success')
        
        elif action == 'update':
            camp_id = int(request.form.get('camp_id'))
            camp = BloodCamp.query.filter_by(id=camp_id, host_id=current_user.id).first_or_404()
            
            camp.name = request.form.get('name')
            camp.address = request.form.get('address')
            camp.state_id = int(request.form.get('state_id'))
            camp.city_id = int(request.form.get('city_id'))
            camp.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            camp.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            camp.contact_number = request.form.get('contact_number')
            
            db.session.commit()
            flash('Camp updated successfully', 'success')
        
        elif action == 'deactivate':
            camp_id = int(request.form.get('camp_id'))
            camp = BloodCamp.query.filter_by(id=camp_id, host_id=current_user.id).first_or_404()
            
            camp.is_active = False
            db.session.commit()
            
            flash('Camp deactivated', 'info')
        
        return redirect(url_for('host.manage_camps'))
    
    camps = BloodCamp.query.filter_by(host_id=current_user.id)\
                          .order_by(BloodCamp.created_at.desc()).all()
    today = date.today()
    return render_template('host/camps.html', camps=camps, states=states, today=today)

@host_bp.route('/inventory/<int:camp_id>', methods=['GET', 'POST'])
def manage_inventory(camp_id):
    """Manage camp inventory"""
    camp = BloodCamp.query.filter_by(id=camp_id, host_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            blood_group = request.form.get('blood_group')
            units = int(request.form.get('units'))
            
            inventory = CampInventory.query.filter_by(
                camp_id=camp_id,
                blood_group=blood_group
            ).first()
            
            if inventory:
                inventory.units_available += units
                inventory.last_updated = datetime.utcnow()
            else:
                inventory = CampInventory(
                    camp_id=camp_id,
                    blood_group=blood_group,
                    units_available=units
                )
                db.session.add(inventory)
            
            db.session.commit()
            flash(f'Added {units} units of {blood_group} blood to inventory', 'success')
        
        elif action == 'update':
            inventory_id = int(request.form.get('inventory_id'))
            new_units = int(request.form.get('new_units'))
            
            inventory = CampInventory.query.filter_by(id=inventory_id).first_or_404()
            inventory.units_available = new_units
            inventory.last_updated = datetime.utcnow()
            
            db.session.commit()
            flash('Inventory updated successfully', 'success')
        
        return redirect(url_for('host.manage_inventory', camp_id=camp_id))
    
    inventory = CampInventory.query.filter_by(camp_id=camp_id).all()
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    
    return render_template('host/inventory.html', 
                         camp=camp, 
                         inventory=inventory, 
                         blood_groups=blood_groups)

@host_bp.route('/donors')
def view_donors():
    """View donors across all camps"""
    donations = BloodDonation.query.join(BloodCamp)\
                                  .filter(BloodCamp.host_id == current_user.id)\
                                  .order_by(BloodDonation.created_at.desc()).all()
    
    return render_template('host/donors.html', donations=donations)

@host_bp.route('/approve-donation/<int:donation_id>')
def approve_donation(donation_id):
    """Approve a camp donation"""
    donation = BloodDonation.query.join(BloodCamp)\
                                  .filter(BloodDonation.id == donation_id,
                                         BloodCamp.host_id == current_user.id,
                                         BloodDonation.status == 'pending').first_or_404()
    
    # Update donation status
    donation.status = 'approved'
    donation.certificate_generated = True
    
    # Update camp inventory
    inventory = CampInventory.query.filter_by(
        camp_id=donation.camp_id,
        blood_group=donation.blood_group
    ).first()
    
    if inventory:
        inventory.units_available += donation.units_donated
        inventory.last_updated = datetime.utcnow()
    else:
        inventory = CampInventory(
            camp_id=donation.camp_id,
            blood_group=donation.blood_group,
            units_available=donation.units_donated
        )
        db.session.add(inventory)
    
    db.session.commit()
    
    flash('Donation approved and added to inventory', 'success')
    return redirect(url_for('host.view_donors'))

@host_bp.route('/reject-donation/<int:donation_id>')
def reject_donation(donation_id):
    """Reject a camp donation"""
    donation = BloodDonation.query.join(BloodCamp)\
                                  .filter(BloodDonation.id == donation_id,
                                         BloodCamp.host_id == current_user.id,
                                         BloodDonation.status == 'pending').first_or_404()
    
    donation.status = 'rejected'
    db.session.commit()
    
    flash('Donation rejected', 'info')
    return redirect(url_for('host.view_donors'))

@host_bp.route('/reports')
def reports():
    """View reports page"""
    camps = BloodCamp.query.filter_by(host_id=current_user.id).all()
    return render_template('host/reports.html', camps=camps)
@host_bp.route('/download-report/<int:camp_id>')
def download_report(camp_id):
    """Download camp donor report"""
    camp = BloodCamp.query.filter_by(id=camp_id, host_id=current_user.id).first_or_404()

    filename = generate_camp_donor_report(camp_id)

    # Build absolute reports directory using the app root (avoids duplicated 'app\\app')
    reports_dir = os.path.join(current_app.root_path, 'static', 'reports')

    # Ensure directory exists (safe even if generator already created it)
    os.makedirs(reports_dir, exist_ok=True)

    filepath = os.path.join(reports_dir, filename)

    return send_file(filepath, as_attachment=True, download_name=f'{camp.name}_donors_report.csv')
