from flask import Blueprint,jsonify,request
from flask_jwt_extended import get_jwt_identity,jwt_required
from backend.models import User,StaffProfile,Trek,Booking,TrekFAQ,Packing,Review,TrekItinerary
from backend.utils.decorators import role_required
from sqlalchemy import func
from backend.extensions import db
from datetime import datetime,date
from backend.utils.validators import check_valid_email,valid_phone_number,valid_password

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")
VALID_TREK_STATUS = {'Pending', 'Approved', 'Open', 'Closed', 'Completed'}

def get_current_staff():
    user_id = get_jwt_identity()
    return  StaffProfile.query.filter_by(user_id = int(user_id)).first()
@staff_bp.route('/dashboard',methods = ['GET'])
@role_required('staff')
def dashboard():
    staff = get_current_staff()

    if not staff:
        return jsonify({"message":"Staff not found","category":"danger"}),400

    treks = Trek.query.filter_by(staff_assigned_id = staff.id).all()

    total_treks = treks.query.count()
    pending_treks = treks.filter(Trek.status == 'Pending').count()
    approved_treks = treks.filter(Trek.status == 'Approved').count()
    open_treks = treks.filter(Trek.status == 'Open').count()
    closed_treks = treks.filter(Trek.status == 'Closed').count()
    Completed_treks = treks.filter(Trek.status == 'Completed').count()


