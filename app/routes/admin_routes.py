from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, BloodRequest, BloodDonation, BloodCamp, Activity, db
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def require_admin():
    """Ensure only admins can access these routes"""
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('main.home'))

@admin_bp.route('/dashboard')
def dashboard():
    """Admin dashboard"""
    # Get pending approvals
    pending_hospitals = User.query.filter_by(role='hospital', is_approved=False).count()
    pending_hosts = User.query.filter_by(role='host', is_approved=False).count()
    
    # Get system statistics
    total_users = User.query.count()
    total_donations = BloodDonation.query.filter_by(status='approved').count()
    total_requests = BloodRequest.query.count()
    active_camps = BloodCamp.query.filter_by(is_active=True).count()
    
    # Get recent activities
    recent_activities = Activity.query.order_by(Activity.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         pending_hospitals=pending_hospitals,
                         pending_hosts=pending_hosts,
                         total_users=total_users,
                         total_donations=total_donations,
                         total_requests=total_requests,
                         active_camps=active_camps,
                         recent_activities=recent_activities)

@admin_bp.route('/approvals')
def approvals():
    """View pending approvals"""
    pending_hospitals = User.query.filter_by(role='hospital', is_approved=False).all()
    pending_hosts = User.query.filter_by(role='host', is_approved=False).all()
    
    return render_template('admin/approvals.html',
                         pending_hospitals=pending_hospitals,
                         pending_hosts=pending_hosts)

@admin_bp.route('/approve-user/<int:user_id>')
def approve_user(user_id):
    """Approve a hospital or host"""
    user = User.query.filter(
        User.id == user_id,
        User.role.in_(['hospital', 'host']),
        User.is_approved == False
    ).first_or_404()
    
    user.is_approved = True
    db.session.commit()
    
    flash(f'{user.role.title()} "{user.hospital_name or user.camp_name}" approved successfully', 'success')
    return redirect(url_for('admin.approvals'))

@admin_bp.route('/reject-user/<int:user_id>')
def reject_user(user_id):
    """Reject a hospital or host application"""
    user = User.query.filter(
        User.id == user_id,
        User.role.in_(['hospital', 'host']),
        User.is_approved == False
    ).first_or_404()
    
    # Delete the user record
    db.session.delete(user)
    db.session.commit()
    
    flash(f'{user.role.title()} application rejected and removed', 'info')
    return redirect(url_for('admin.approvals'))

@admin_bp.route('/users')
def manage_users():
    """Manage all users"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/deactivate-user/<int:user_id>')
def deactivate_user(user_id):
    """Deactivate a user (for hospitals/hosts)"""
    user = User.query.filter(
        User.id == user_id,
        User.role.in_(['hospital', 'host'])
    ).first_or_404()
    
    user.is_approved = False
    db.session.commit()
    
    flash(f'{user.role.title()} deactivated', 'info')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/activate-user/<int:user_id>')
def activate_user(user_id):
    """Activate a user (for hospitals/hosts)"""
    user = User.query.filter(
        User.id == user_id,
        User.role.in_(['hospital', 'host'])
    ).first_or_404()
    
    user.is_approved = True
    db.session.commit()
    
    flash(f'{user.role.title()} activated', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/system-stats')
def system_stats():
    """View system statistics"""
    # User statistics
    user_stats = {
        'patients': User.query.filter_by(role='patient').count(),
        'hospitals': User.query.filter_by(role='hospital', is_approved=True).count(),
        'hosts': User.query.filter_by(role='host', is_approved=True).count(),
        'admins': User.query.filter_by(role='admin').count()
    }
    
    # Blood statistics
    blood_stats = {
        'total_donations': BloodDonation.query.filter_by(status='approved').count(),
        'pending_donations': BloodDonation.query.filter_by(status='pending').count(),
        'total_requests': BloodRequest.query.count(),
        'approved_requests': BloodRequest.query.filter_by(status='approved').count(),
        'pending_requests': BloodRequest.query.filter_by(status='pending').count()
    }
    
    # Camp statistics
    camp_stats = {
        'active_camps': BloodCamp.query.filter_by(is_active=True).count(),
        'total_camps': BloodCamp.query.count()
    }
    
    return render_template('admin/stats.html',
                         user_stats=user_stats,
                         blood_stats=blood_stats,
                         camp_stats=camp_stats)

# Admin can perform patient actions
@admin_bp.route('/patient-actions')
def patient_actions():
    """Access patient functionality as admin"""
    from app.utils.location_data import get_states
    states = get_states()
    return render_template('admin/patient_actions.html', states=states)

# Import patient routes for admin use
from app.routes.patient_routes import search_blood as patient_search_blood
from app.routes.patient_routes import request_blood as patient_request_blood
from app.routes.patient_routes import donate_blood as patient_donate_blood
from app.routes.patient_routes import register_camp as patient_register_camp

# Register patient routes for admin (with different URL prefix)
admin_bp.add_url_rule('/search-blood', 'search_blood', patient_search_blood, methods=['GET', 'POST'])
admin_bp.add_url_rule('/request-blood/<int:hospital_id>', 'request_blood', patient_request_blood, methods=['GET', 'POST'])
admin_bp.add_url_rule('/donate-blood', 'donate_blood', patient_donate_blood, methods=['GET', 'POST'])
admin_bp.add_url_rule('/register-camp', 'register_camp', patient_register_camp, methods=['GET', 'POST'])