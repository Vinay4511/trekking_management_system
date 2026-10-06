from backend.models import User,StaffProfile
from backend.extensions import jwt,db
from flask import Blueprint,jsonify,request,render_template,url_for,flash,redirect
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login",methods = ["POST"])
def login():
    username = request.json.get("username",None)
    password = request.json.get("password",None)
    user = User.query.filter_by(username= username).first()
    if user is None or not user.check_password(password):
        flash('Invalid username or password', 'danger')
        return redirect(url_for('auth.login'))
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)