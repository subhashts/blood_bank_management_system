from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file,current_app
from flask_login import login_required, current_user
from app.models import BloodInventory, BloodRequest, BloodDonation, Activity, db
from app.utils.certificate_generator import generate_donation_certificate
from app.utils.report_generator import generate_donation_report, generate_request_report
from datetime import datetime, date
import os

hospital_bp = Blueprint('hospital', __name__)

@hospital_bp.before_request
@login_required
def require_hospital():
    """Ensure only hospitals can access these routes"""
    if current_user.role != 'hospital' or not current_user.is_approved:
        flash('Access denied', 'error')
        return redirect(url_for('main.home'))

@hospital_bp.route('/dashboard')
def dashboard():
    """Hospital dashboard"""
    # Get inventory summary
    inventory = BloodInventory.query.filter_by(hospital_id=current_user.id).all()
    total_units = sum(inv.units_available for inv in inventory)
    
    # Get pending requests and donations
    pending_requests = BloodRequest.query.filter_by(hospital_id=current_user.id, status='pending').count()
    pending_donations = BloodDonation.query.filter_by(hospital_id=current_user.id, status='pending').count()
    
    # Get recent activities
    recent_requests = BloodRequest.query.filter_by(hospital_id=current_user.id)\
                                       .order_by(BloodRequest.request_date.desc())\
                                       .limit(5).all()
    
    return render_template('hospital/dashboard.html',
                         inventory=inventory,
                         total_units=total_units,
                         pending_requests=pending_requests,
                         pending_donations=pending_donations,
                         recent_requests=recent_requests)

@hospital_bp.route('/inventory', methods=['GET', 'POST'])
def manage_inventory():
    """Manage blood inventory"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            blood_group = request.form.get('blood_group')
            units = int(request.form.get('units'))
            
            # Check if inventory exists for this blood group
            inventory = BloodInventory.query.filter_by(
                hospital_id=current_user.id,
                blood_group=blood_group
            ).first()
            
            if inventory:
                inventory.units_available += units
                inventory.last_updated = datetime.utcnow()
            else:
                inventory = BloodInventory(
                    hospital_id=current_user.id,
                    blood_group=blood_group,
                    units_available=units
                )
                db.session.add(inventory)
            
            db.session.commit()
            flash(f'Added {units} units of {blood_group} blood to inventory', 'success')
        
        elif action == 'update':
            inventory_id = int(request.form.get('inventory_id'))
            new_units = int(request.form.get('new_units'))
            
            inventory = BloodInventory.query.filter_by(
                id=inventory_id,
                hospital_id=current_user.id
            ).first_or_404()
            
            inventory.units_available = new_units
            inventory.last_updated = datetime.utcnow()
            db.session.commit()
            
            flash(f'Updated {inventory.blood_group} inventory to {new_units} units', 'success')
        
        elif action == 'delete':
            inventory_id = int(request.form.get('inventory_id'))
            
            inventory = BloodInventory.query.filter_by(
                id=inventory_id,
                hospital_id=current_user.id
            ).first_or_404()
            
            db.session.delete(inventory)
            db.session.commit()
            
            flash(f'Removed {inventory.blood_group} from inventory', 'success')
        
        return redirect(url_for('hospital.manage_inventory'))
    
    inventory = BloodInventory.query.filter_by(hospital_id=current_user.id).all()
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    
    return render_template('hospital/inventory.html', 
                         inventory=inventory, 
                         blood_groups=blood_groups)

@hospital_bp.route('/donors')
def view_donors():
    """View and approve donors"""
    donations = BloodDonation.query.filter_by(hospital_id=current_user.id)\
                                  .order_by(BloodDonation.created_at.desc()).all()
    
    return render_template('hospital/donors.html', donations=donations)

@hospital_bp.route('/approve-donation/<int:donation_id>')
def approve_donation(donation_id):
    """Approve a blood donation"""
    donation = BloodDonation.query.filter_by(
        id=donation_id,
        hospital_id=current_user.id,
        status='pending'
    ).first_or_404()
    
    # Update donation status
    donation.status = 'approved'
    donation.certificate_generated = True
    
    # Update inventory
    inventory = BloodInventory.query.filter_by(
        hospital_id=current_user.id,
        blood_group=donation.blood_group
    ).first()
    
    if inventory:
        inventory.units_available += donation.units_donated
        inventory.last_updated = datetime.utcnow()
    else:
        inventory = BloodInventory(
            hospital_id=current_user.id,
            blood_group=donation.blood_group,
            units_available=donation.units_donated
        )
        db.session.add(inventory)
    
    db.session.commit()
    
    flash('Donation approved and added to inventory', 'success')
    return redirect(url_for('hospital.view_donors'))

@hospital_bp.route('/reject-donation/<int:donation_id>')
def reject_donation(donation_id):
    """Reject a blood donation"""
    donation = BloodDonation.query.filter_by(
        id=donation_id,
        hospital_id=current_user.id,
        status='pending'
    ).first_or_404()
    
    donation.status = 'rejected'
    db.session.commit()
    
    flash('Donation rejected', 'info')
    return redirect(url_for('hospital.view_donors'))

@hospital_bp.route('/requests')
def view_requests():
    """View blood requests"""
    requests = BloodRequest.query.filter_by(hospital_id=current_user.id)\
                                .order_by(BloodRequest.request_date.desc()).all()
    
    return render_template('hospital/requests.html', requests=requests)

@hospital_bp.route('/approve-request/<int:request_id>')
def approve_request(request_id):
    """Approve a blood request"""
    blood_request = BloodRequest.query.filter_by(
        id=request_id,
        hospital_id=current_user.id,
        status='pending'
    ).first_or_404()
    
    # Check inventory
    inventory = BloodInventory.query.filter_by(
        hospital_id=current_user.id,
        blood_group=blood_request.blood_group
    ).first()
    
    if not inventory or inventory.units_available < blood_request.units_requested:
        flash('Insufficient blood units in inventory', 'error')
        return redirect(url_for('hospital.view_requests'))
    
    # Update request status
    blood_request.status = 'approved'
    blood_request.response_date = datetime.utcnow()
    
    # Update inventory
    inventory.units_available -= blood_request.units_requested
    inventory.last_updated = datetime.utcnow()
    
    db.session.commit()
    
    flash('Blood request approved', 'success')
    return redirect(url_for('hospital.view_requests'))

@hospital_bp.route('/reject-request/<int:request_id>', methods=['POST'])
def reject_request(request_id):
    """Reject a blood request"""
    blood_request = BloodRequest.query.filter_by(
        id=request_id,
        hospital_id=current_user.id,
        status='pending'
    ).first_or_404()
    
    blood_request.status = 'rejected'
    blood_request.response_date = datetime.utcnow()
    blood_request.notes = request.form.get('rejection_reason', '')
    
    db.session.commit()
    
    flash('Blood request rejected', 'info')
    return redirect(url_for('hospital.view_requests'))

@hospital_bp.route('/reports')
def reports():
    """Generate and download reports"""
    return render_template('hospital/reports.html')

@hospital_bp.route('/download-report/<report_type>')
def download_report(report_type):
    """Download CSV reports"""
    if report_type == 'donations_monthly':
        filename = generate_donation_report(current_user.id, report_type='monthly')
    elif report_type == 'donations_yearly':
        filename = generate_donation_report(current_user.id, report_type='yearly')
    elif report_type == 'requests_monthly':
        filename = generate_request_report(current_user.id, report_type='monthly')
    elif report_type == 'requests_yearly':
        filename = generate_request_report(current_user.id, report_type='yearly')
    else:
        flash('Invalid report type', 'error')
        return redirect(url_for('hospital.reports'))
    
    # Build absolute reports directory using the app root
    reports_dir = os.path.join(current_app.root_path, 'static', 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    filepath = os.path.join(reports_dir, filename)
    return send_file(filepath, as_attachment=True, download_name=filename)
