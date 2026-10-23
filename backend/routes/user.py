import csv
import io
from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models import Trek, Booking, Review, User
from backend.utils.decorators import role_required
from backend.extensions import db
VALID_STATUS = {'Booked','Cancelled','Completed'}

user_bp = Blueprint("user", __name__, url_prefix="/user")

@user_bp.route('/book/<int:trek_id>',methods = ['POST','GET'])
@role_required('trekker')
def book(trek_id):
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    people = data.get('number_of_people',1)
    try:
        people = int(people)
        if people <= 0:
            return jsonify({"message":"minimum one person should book","category":"danger"}),400
    except(TypeError,ValueError):
        return jsonify({"message":"number_of_people must be an integer","category":"danger"}),400

    trek = Trek.query(trek_id)
    if not trek:
        return jsonify({"message": "choose correct trek", "category": "danger"}), 400

    if  trek.status != "Open":
         return jsonify({"message": "Trek is closed", "category": "danger"}), 400

    existing_booking = Trek.query.filter_by(user_id = user_id,trek_id = trek_id ).first()
    if existing_booking:
        return jsonify({"message": "one person can  book only once", "category": "danger"}), 400
    if people > trek.max_persons:
        return jsonify({"message": "maximum {trek.max_persons} can book", "category": "danger"}), 400
    if people > trek.available_slots:
        return jsonify({"message": "maximum {trek.available_slots} can book", "category": "danger"}),400

    price = trek.price*people

    booking = Booking(
        user_id=user_id,
        trek_id=trek_id,
        num_of_people=people,
        total_price=price,
        status='Booked',
        payment_status='Pending'
    )

    trek.available_slots -= people

    db.session.add(booking)
    db.session.commit()

    return jsonify({"message": "Trek booked successfully!","category": "success","booking_id": booking.id,"total_price": price}), 201

@user_bp.route('/booking/<int:booking_id/cancel>',methods = ['POST','GET'])
@role_required('trekker')
def booking_cancel(booking_id):
    user_id = int(get_jwt_identity())

    booking = Booking.query.filter_by(id = booking_id,user_id=user_id).first()

    if not booking:
        return jsonify({"message":"Booking not found","category":"danger"}),404

    if booking.status != "Booked":
        return jsonify({"message": "your trek is not booked it is in {booking.status}", "category": "danger"}), 400

    trek = Trek.query.filter_by(booking.trek_id)
    if trek:
        trek.available_slots += booking.number_of_people

    booking.status = 'Cancelled'
    db.session.commit()

    return jsonify({"message": "Booking cancelled successfully", "category": "success"}), 200

user_bp.route("/bookings", methods=["GET"])
@role_required('trekker')
def my_bookings():
    user_id = int(get_jwt_identity())

    query = Booking.query.filter_by(user_id = user_id)

    status_filter = request.args.get('status', "", type=str).strip()

    if status_filter:
        if status_filter not in VALID_STATUS:
            return jsonify({'message':"Please select a valid status filter",'category':'danger'}),400
    query = query.filter_by(status = status_filter)
    bookings = query.order_by(Booking.booking_date.desc()).all()

    result = [{'booking_id':b.id,
               'trek_id':b.trek_id,
               'booking_date':b.booking_date.isoformat(),
               'num_of_people':b.num_of_people,
               'total_price':b.total_price,
               'payment_status':b.payment_status,
               'status':b.status,
               'trek_name':b.trek.trek_name if b.trek else None,
               'location':b.trek.location if b.trek else None,
               'start_date':b.trek.start_date if b.trek else None,
               'end_date':b.trek.end_date if b.trek else None
               }for b in bookings]

    return jsonify({"message":'Treks fetched successfully','category':'success','bookings':result})

@user_bp.route('/review/<int:id>',methods = ['POST','GET'])
@role_required('trekker')
def review(id):
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or not data['review']:
        return jsonify({"message":"Enter correct data to submit review","category":"danger"}),400

    try:
        rating = int(data['rating'])
        if rating < 1 and rating > 5:
            return jsonify({"message": "Rating should be in between 1 and 5 ", "category": "danger"}),400
    except(TypeError,ValueError):
        return jsonify({"message":"rating should be an integer",'category':'danger'}),400

    completed_booking = Booking.query.filter_by(user_id = user_id,trek_id = id,status = "Completed").first()

    if not completed_booking:
        return jsonify({"message": "No completed Treks to submit a review", 'category': 'danger'}), 403

    existing_review = Review.query.filter_by(user_id = user_id,trek_id =id).first()

    if existing_review:
        return jsonify({"message": "You can only submit review only once", 'category': 'danger'}), 403

    review = Review(
        user_id = user_id,
        trek_id = id,
        rating = rating,
        comments = data.get('comments','').strip()
    )
    db.session.add(review)
    db.session.commit()

    return jsonify({"message":"review submitted successfully","category":"success"}),201








