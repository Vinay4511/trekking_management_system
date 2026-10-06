from app import app
from extensions import db
from models import User,StaffProfile,Booking,Trek,Review,TrekItinerary

with app.app_context():
    db.create_all()
    existing_admin = User.query.filter_by(role='admin').first()
    if not existing_admin:
        admin_user = User(
            username='admin',
            email='admin@trekking.com',
            role='admin',
            is_active=True
        )
        admin_user.set_pass('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print("Admin created successfully")
        print("email: admin@trekking.com")
        print("password:admin123")
    else:
        print("Admin already exists")

