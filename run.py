from app import create_app
from flask_migrate import upgrade

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        from app.models import db
        db.create_all()
        
        # Load initial data
        from app.utils.location_data import load_initial_data
        load_initial_data()
    
    app.run(debug=True)