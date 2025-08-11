from datetime import date
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

# Setup Flask app
app = create_app()
app.app_context().push()

# Check if admin already exists
admin = User.query.filter_by(email='admin@demo.com').first()

if admin:
    print("⚠️ Admin user already exists.")
else:
    # Create admin user with required dob
    admin = User(
        name='Admin User',
        email='admin@demo.com',
        password_hash=generate_password_hash('password'),
        role='admin',
        dob=date(1990, 1, 1),  # ✅ Added dob
        age=30,
        address='Head Office',
        blood_group='O+',
        state_id=1,  # Make sure state_id=1 exists in DB
        city_id=1,   # Make sure city_id=1 exists in DB
        is_approved=True
    )

    db.session.add(admin)
    db.session.commit()
    print("✅ Admin user created: admin@demo.com / password")
