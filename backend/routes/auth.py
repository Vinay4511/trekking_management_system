from backend.models import User,StaffProfile
from backend.extensions import jwt,db
from flask import Blueprint,jsonify,request
from flask_jwt_extended import create_access_token,jwt_required,get_jwt_identity
from backend.utils.validators import check_valid_email,valid_phone_number,valid_password,valid_entry_details
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login",methods = ["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email","").lower().strip()
    password = data.get("password",None)

    if not email or not password or not check_valid_email(email) :
        return jsonify({"message":"Invalid Data","category":"danger"}),400

    user = User.query.filter_by(email= email).first()
    if user is None or not user.check_pass(password):
        return jsonify({"message": "Invalid Credentials","category":"danger"}),401

    if user.is_blacklisted:
        return jsonify({"message":"Your account is blacklisted,Please Contact Admin","category":"danger"}),403
    if not user.is_active:
        return jsonify({"message":"Your account is not active,Please Contact Admin","category":"danger"}),403


    additional_claims = {'role':user.role}
    access_token = create_access_token(identity=str(user.id),additional_claims = additional_claims)
    return jsonify(access_token=access_token,role = user.role),200

@auth_bp.route("/register",methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"message":"Enter the data","category":"danger"}),400

    errors = valid_entry_details(data)
    if errors:
        return jsonify({"message":";".join(errors),"category":"danger"}),400

    existing_user = User.query.filter_by(email = data['email'].lower().strip()).first()
    if existing_user:
        return jsonify({"message":"Already user exists", "category": "danger"}), 400

    user = User(
        username=data['username'].strip(),
        email=data['email'].lower().strip(),
        phone=data.get('phone', '').strip(),
        role='trekker',
        is_active=True,
        is_blacklisted=False
    )
    user.set_pass(data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": " Registration Successful ", "category": "success"}),201

@auth_bp.route("/profile",methods = ["GET"])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({"message": "user doesn't exists", "category": "danger"}), 401

    profile_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active
    }
    if user.role == "staff" and user.staff_profile:
        profile_data['staff_details'] = {
            "experience": user.staff_profile.experience,
            "specialization": user.staff_profile.specialization,
            "status": user.staff_profile.status,
            "assigned_treks_count": len(user.staff_profile.assigned_treks)
        }
    return jsonify(profile_data), 200

@auth_bp.route("/update_profile",methods = ["PUT","POST"])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    data = request.get_json()

    if not data :
        return jsonify({"message": "Enter data to update details", "category": "danger"}), 400
    if not user:
        return jsonify({"message": "user does not  exists", "category": "danger"}), 404
    if 'username' in data:
        if len(data['username'].strip()) >= 5:
            user.username = data['username'].strip()
        else:
            return jsonify({"message": "Enter valid username", "category": "danger"}), 400
    if 'phone' in data:
        if not valid_phone_number(data['phone']):
            return jsonify({"message": "Enter correct number", "category": "danger"}), 400
        user.phone = data['phone'].strip()
    db.session.commit()

    return jsonify({"message":"Profile updated correctly","category":"success"}),200

@auth_bp.route("/change_password",methods=["POST"])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    data = request.get_json()

    if not data :
        return jsonify({"message": "Enter data to update details", "category": "danger"}), 400

    if not data.get('old_pass') or not data.get('new_pass'):
        return jsonify({"message":"please give valid data to update","category":"danger"}),400

    if not user:
        return jsonify({"message": "user does not  exists", "category": "danger"}), 404

    if not user.check_pass(data['old_pass']):
        return jsonify({"message":"old password is incorrect","category":"danger"}),401
    valid,msg = valid_password(data['new_pass'])
    if not valid:
        return jsonify({"message": msg, "category": "danger"}), 400
    user.set_pass(data['new_pass'])

    db.session.commit()

    return jsonify({"message":"Password reset successfully","category":"success"}),200

@auth_bp.route("/logout")
@jwt_required()
def logout():
    return