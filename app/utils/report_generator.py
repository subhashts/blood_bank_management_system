import csv
import os
from datetime import datetime
from flask import current_app
from app.models import BloodDonation, BloodRequest, User

def generate_donation_report(hospital_id, start_date=None, end_date=None, report_type='monthly'):
    """Generate CSV report for donations"""
    
    # Create reports directory if it doesn't exist
    reports_dir = os.path.join(current_app.root_path, 'static', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Build query
    query = BloodDonation.query.filter_by(hospital_id=hospital_id, status='approved')
    
    if start_date and end_date:
        query = query.filter(BloodDonation.donation_date.between(start_date, end_date))
    
    donations = query.join(User, BloodDonation.donor_id == User.id).all()
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"donations_report_{report_type}_{timestamp}.csv"
    filepath = os.path.join(reports_dir, filename)
    
    # Write CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Donation ID', 'Donor Name', 'Donor Email', 'Blood Group', 
            'Units Donated', 'Donation Date', 'Status', 'Certificate Generated'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for donation in donations:
            writer.writerow({
                'Donation ID': donation.id,
                'Donor Name': donation.donor.name,
                'Donor Email': donation.donor.email,
                'Blood Group': donation.blood_group,
                'Units Donated': donation.units_donated,
                'Donation Date': donation.donation_date.strftime('%Y-%m-%d'),
                'Status': donation.status.title(),
                'Certificate Generated': 'Yes' if donation.certificate_generated else 'No'
            })
    
    return filename

def generate_request_report(hospital_id, start_date=None, end_date=None, report_type='monthly'):
    """Generate CSV report for blood requests"""
    
    # Create reports directory if it doesn't exist
    reports_dir = os.path.join(current_app.root_path, 'static', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Build query
    query = BloodRequest.query.filter_by(hospital_id=hospital_id)
    
    if start_date and end_date:
        query = query.filter(BloodRequest.request_date.between(start_date, end_date))
    
    requests = query.join(User, BloodRequest.patient_id == User.id).all()
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"requests_report_{report_type}_{timestamp}.csv"
    filepath = os.path.join(reports_dir, filename)
    
    # Write CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Request ID', 'Patient Name', 'Patient Email', 'Blood Group', 
            'Units Requested', 'Request Type', 'Request Date', 'Status', 'Response Date', 'Notes'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for request in requests:
            writer.writerow({
                'Request ID': request.id,
                'Patient Name': request.patient.name,
                'Patient Email': request.patient.email,
                'Blood Group': request.blood_group,
                'Units Requested': request.units_requested,
                'Request Type': request.request_type.title(),
                'Request Date': request.request_date.strftime('%Y-%m-%d %H:%M'),
                'Status': request.status.title(),
                'Response Date': request.response_date.strftime('%Y-%m-%d %H:%M') if request.response_date else '',
                'Notes': request.notes or ''
            })
    
    return filename

def generate_camp_donor_report(camp_id, start_date=None, end_date=None):
    """Generate CSV report for camp donors"""
    
    # Create reports directory if it doesn't exist
    reports_dir = os.path.join(current_app.root_path, 'static', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Build query
    query = BloodDonation.query.filter_by(camp_id=camp_id, status='approved')
    
    if start_date and end_date:
        query = query.filter(BloodDonation.donation_date.between(start_date, end_date))
    
    donations = query.join(User, BloodDonation.donor_id == User.id).all()
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"camp_donors_report_{timestamp}.csv"
    filepath = os.path.join(reports_dir, filename)
    
    # Write CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Donation ID', 'Donor Name', 'Donor Email', 'Blood Group', 
            'Units Donated', 'Donation Date', 'Certificate Generated'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for donation in donations:
            writer.writerow({
                'Donation ID': donation.id,
                'Donor Name': donation.donor.name,
                'Donor Email': donation.donor.email,
                'Blood Group': donation.blood_group,
                'Units Donated': donation.units_donated,
                'Donation Date': donation.donation_date.strftime('%Y-%m-%d'),
                'Certificate Generated': 'Yes' if donation.certificate_generated else 'No'
            })
    
    return filename