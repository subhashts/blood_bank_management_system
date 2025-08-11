import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.colors import HexColor
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics import renderPDF
from flask import current_app

def generate_donation_certificate(donation, donor_name, hospital_name=None, camp_name=None):
    """Generate a PDF certificate for blood donation"""
    
    # Create certificates directory if it doesn't exist
    cert_dir = os.path.join(current_app.root_path, 'static', 'certificates')
    os.makedirs(cert_dir, exist_ok=True)
    
    # Generate filename
    filename = f"donation_certificate_{donation.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(cert_dir, filename)
    
    # Create PDF document
    doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=HexColor('#8B0000')
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=HexColor('#DC143C')
    )
    
    content_style = ParagraphStyle(
        'CustomContent',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12,
        alignment=TA_CENTER,
        leading=18
    )
    
    # Build content
    content = []
    
    # Title
    content.append(Paragraph("CERTIFICATE OF APPRECIATION", title_style))
    content.append(Spacer(1, 20))
    
    # Subtitle
    content.append(Paragraph("Blood Donation Certificate", subtitle_style))
    content.append(Spacer(1, 30))
    
    # Main content
    content.append(Paragraph("This is to certify that", content_style))
    content.append(Spacer(1, 10))
    
    # Donor name (highlighted)
    donor_style = ParagraphStyle(
        'DonorName',
        parent=styles['Normal'],
        fontSize=16,
        spaceAfter=15,
        alignment=TA_CENTER,
        textColor=HexColor('#8B0000'),
        fontName='Helvetica-Bold'
    )
    content.append(Paragraph(f"<u>{donor_name}</u>", donor_style))
    
    # Donation details
    location = hospital_name if hospital_name else camp_name
    location_type = "Hospital" if hospital_name else "Blood Camp"
    
    content.append(Paragraph(f"has generously donated <b>{donation.units_donated} unit(s)</b> of <b>{donation.blood_group}</b> blood", content_style))
    content.append(Paragraph(f"at <b>{location}</b> ({location_type})", content_style))
    content.append(Paragraph(f"on <b>{donation.donation_date.strftime('%B %d, %Y')}</b>", content_style))
    
    content.append(Spacer(1, 30))
    
    # Appreciation message
    content.append(Paragraph("Your noble act of blood donation is a gift of life to someone in need.", content_style))
    content.append(Paragraph("Thank you for your selfless contribution to society.", content_style))
    
    content.append(Spacer(1, 40))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=HexColor('#666666')
    )
    
    content.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", footer_style))
    content.append(Paragraph("Blood Management System", footer_style))
    
    # Build PDF
    doc.build(content)
    
    return filename

def generate_camp_registration_certificate(donation, donor_name, camp_name):
    """Generate certificate for camp registration"""
    return generate_donation_certificate(donation, donor_name, camp_name=camp_name)