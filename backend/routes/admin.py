from flask import Blueprint,jsonify,request
from flask_jwt_extended import get_jwt_identity,jwt_required
from backend.models import User,StaffProfile,Trek,Booking,TrekFAQ,Packing,Review,TrekItinerary
from backend.utils.decorators import role_required
from sqlalchemy import func
from backend.extensions import db
from datetime import datetime,date
from backend.utils.validators import check_valid_email,valid_phone_number,valid_password

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
Valid_difficulty = {'easy','moderate','hard'}
Valid_status = {'Pending','approved','completed','open','closed'}
Valid_status_trekkers = {'active','blacklisted'}
Valid_status_booking = {'Booked','cancelled','completed'}
Valid_staff_status = {'active','inactive'}

@admin_bp.route("/dashboard",methods =["GET"])
@role_required('admin')
def dashboard():
    total_trekkers = User.query.filter_by(role ="trekker").count()
    total_staff = User.query.filter_by(role = "staff").count()
    active_users = User.query.filter_by(is_active = True).count()
    blacklisted_users = User.query.filter_by(is_blacklisted = True).count()
    total_bookings = Booking.query.count()
    booked_count = Booking.query.filter_by(status = "Booked").count()
    confirmed_bookings = Booking.query.filter_by(status = "completed").count()
    cancelled_bookings = Booking.query.filter_by(status = "cancelled").count()
    total_treks = Trek.query.count()
    open_treks = Trek.query.filter_by(status ='open').count()
    pending_treks = Trek.query.filter_by(status ='Pending').count()

    total_revenue = db.session.query(func.sum(Booking.total_price)).filter(
        Booking.payment_status == "paid").scalar() or 0.0

    return jsonify({"users":{"total_trekkers":total_trekkers,"total_staff":total_staff,"active_users":active_users,"blacklisted_users":blacklisted_users}
                    ,"bookings":{"total_bookings":total_bookings,"booked_count":booked_count,"confirmed_bookings":confirmed_bookings,"cancelled_bookings":cancelled_bookings},"treks":{"total_treks":total_treks,"open_treks":open_treks,
                    "pending_treks":pending_treks},"financial":{"total_revenue":float(total_revenue)}}
                   ),200

@admin_bp.route("/trek/create",methods = ["POST"])
@role_required('admin')
def admin_create_trek():
    data = request.get_json()
    errors = []
    if not data :
        return jsonify({"message": "Enter data to update details", "category": "danger"}), 400

    required_fields = ['trek_name','location','difficulty','duration_time','total_slots','start_date','end_date','price']

    missing_fields = [field for field in required_fields if field not in data or data.get(field) is None]

    if missing_fields:
        return jsonify({"message":f"missing field required","category":"danger"}),400

    difficulty = data['difficulty']
    if difficulty not in Valid_difficulty:
        errors.append(f"difficulties must one of the ({Valid_difficulty})")

    status = 'Pending'

    try:
        duration_time = int(data['duration_time'])
        if duration_time <= 0:
            errors.append("Time must be a positive number")
    except(ValueError,TypeError):
        errors.append("Time must be an Integer value")

    try:
        total_slots = int(data['total_slots'])
        if total_slots <= 0:
            errors.append("total slots must be a positive number")
    except(ValueError,TypeError):
        errors.append("slots  must be an Integer value ")

    try:
        price = float(data['price'])
        if price < 0:
             errors.append("price must >= 0")
    except(ValueError,TypeError):
        errors.append("price  must be an Integer value ")

    distance = data.get('distance')
    if distance is not None:
        try:
            distance = float(distance)
            if distance <= 0:
                errors.append("distance must be > 0")
        except(ValueError,TypeError):
            errors.append("distance  must be an Integer value ")

    try:
        start_date = datetime.strptime(data['start_date'], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        errors.append("start_date must be yyyy-mm-dd")
    try:
        end_date = datetime.strptime(data['end_date'], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        errors.append("end_date must be yyyy-mm-dd")

    if 'start_date' in data and 'end_date' in data and not errors:
        if end_date<start_date:
            errors.append("end_date must be >= start_date")
        if start_date < date.today():
            errors.append("start_date cannot be in the past")

    try:
        min_age = int(data.get('min_age', 12))
        max_age = int(data.get('max_age', 50))
        max_persons = int(data.get('max_persons', 10))
        if not (0 < min_age <= max_age):
            errors.append("must be 0 < min_age <= max_age")
        if max_persons <= 0:
            errors.append("max_persons must be > 0")
    except (TypeError, ValueError):
        errors.append("start_date must be yyyy-mm-dd")


    if 'start_date' in data and 'trek_name' in data and not errors:
        trek = Trek.query.filter_by(trek_name = data['trek_name'],start_date = start_date).first()
        if trek:
            errors.append("Trek already exists on this date choose other")

    if errors:
        return jsonify({"message":errors,"category":"danger"}),400

    trek = Trek(
        trek_name=data['trek_name'],
        state=data.get('state'),
        location=data['location'],
        start_point=data.get('start_point'),
        end_point=data.get('end_point'),
        pickup_point=data.get('pickup_point'),
        difficulty=difficulty,
        duration_time=duration_time,
        distance=distance,
        altitude_max=data.get('altitude_max'),
        terrain=data.get('terrain'),
        min_age=min_age,
        max_age=max_age,
        max_persons=max_persons,
        available_slots=total_slots,
        total_slots=total_slots,
        start_date=start_date,
        end_date=end_date,
        description=data.get('description'),
        inclusions=data.get('inclusions'),
        exclusions=data.get('exclusions'),
        how_to_reach=data.get('how_to_reach'),
        cover_image_url=data.get('cover_image_url'),
        price=price,
        status=status,
    )
    db.session.add(trek)
    db.session.commit()
    return jsonify({"message": "Trek created successfully","category": "success","trek_name": trek.trek_name}), 201


@admin_bp.route("/trek/edit/<int:trek_id>", methods=["PUT"])
@role_required('admin')
def edit_trek(trek_id):
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({"message": "Trek not found", "category": "danger"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "Enter data to update details", "category": "danger"}), 400

    errors = []
    updates = {}

    if 'difficulty' in data:
        difficulty = data['difficulty']
        if difficulty not in Valid_difficulty:
            errors.append(f"difficulties must one of the ({Valid_difficulty})")
        else:
            updates['difficulty'] = difficulty

    if 'status' in data:
        status = data['status']
        if status not in Valid_status:
            errors.append(f"must be one of the ({Valid_status})")
        else:
            updates['status'] = status

    if 'duration_time' in data:
        try:
            duration_time = int(data['duration_time'])
            if duration_time <= 0:
                errors.append("Time must be a positive number")
            else:
                updates['duration_time'] = duration_time
        except (ValueError, TypeError):
            errors.append("Time must be an Integer value")

    if 'total_slots' in data:
        try:
            total_slots = int(data['total_slots'])
            if total_slots <= 0:
                errors.append("total slots must be a positive number")
            else:
                updates['total_slots'] = total_slots
        except (ValueError, TypeError):
            errors.append("slots must be an Integer value")

    if 'available_slots' in data:
        try:
            available_slots = int(data['available_slots'])
            if available_slots < 0:
                errors.append("available slots must be >= 0")
            else:
                updates['available_slots'] = available_slots
        except (ValueError, TypeError):
            errors.append("slots must be an Integer value")

    if 'price' in data:
        try:
            price = float(data['price'])
            if price < 0:
                errors.append("price must >= 0")
            else:
                updates['price'] = price
        except (ValueError, TypeError):
            errors.append("price must be an Integer value")

    if 'distance' in data and data['distance'] is not None:
        try:
            distance = float(data['distance'])
            if distance <= 0:
                errors.append("distance must be > 0")
            else:
                updates['distance'] = distance
        except (ValueError, TypeError):
            errors.append("distance must be an Integer value")

    if 'start_date' in data:
        try:
            updates['start_date'] = datetime.strptime(data['start_date'], "%Y-%m-%d").date()
        except (TypeError, ValueError):
            errors.append("start_date must be yyyy-mm-dd")

    if 'end_date' in data:
        try:
            updates['end_date'] = datetime.strptime(data['end_date'], "%Y-%m-%d").date()
        except (TypeError, ValueError):
            errors.append("end_date must be yyyy-mm-dd")

    if 'start_date' in updates and 'end_date' in updates and not errors:
        if updates['end_date'] < updates['start_date']:
            errors.append("end_date must be >= start_date")
        if updates['start_date'] < date.today():
            errors.append("start_date cannot be in the past")

    if errors:
        return jsonify({"message": "Validation failed", "errors": errors, "category": "danger"}), 400
    for f in ('trek_name', 'state', 'location', 'start_point', 'end_point',
              'pickup_point', 'altitude_max', 'terrain', 'description',
              'inclusions', 'exclusions', 'how_to_reach', 'cover_image_url'):
        if f in data:
            updates[f] = data[f]

    for k, v in updates.items():
        setattr(trek, k, v)

    db.session.commit()
    return jsonify({"message": "Trek updated successfully", "category": "success", "trek_id": trek.id}), 200

@admin_bp.route("/trek/delete/<int:trek_id>", methods=["DELETE"])
@role_required('admin')
def trek_delete(trek_id):
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({"message": "Trek not found", "category": "danger"}), 404
    active_bookings = [booking for booking in trek.bookings if booking.status == "Booked"]
    if active_bookings:
        return jsonify({"message":"cannot delete trek with active bookings","category":"danger"}),400

    db.session.delete(trek)
    db.session.commit()

    return jsonify({"message":"trek deleted successfully","category":"success"}),200

@admin_bp.route("/trek", methods=["GET"])
@role_required('admin')
def treks():
    status = request.args.get('status',"",type = str ).strip()
    search  = request.args.get('search',"",type = str ).strip()
    limit = request.args.get('limit',10,type =int)
    page = request.args.get('page',1,type = int)

    if limit <= 0 or limit > 100:
        limit = 10
    if page <= 0:
        page = 1

    query = Trek.query

    if status:
        if status not in Valid_status:
            return jsonify({"message":"Invalid status selected","category":"danger"}),400
        query = query.filter(Trek.status == status)

    if search:
        query = query.filter(
            Trek.trek_name.ilike(f'%{search}%'))
    query = query.order_by(Trek.start_date.asc())

    pagination = query.paginate(page=page,per_page=limit,error_out=False)

    treks_list = [{
        "id": t.id,
        "trek_name": t.trek_name,
        "location": t.location,
        "difficulty": t.difficulty,
        "available_slots": t.available_slots,
        "total_slots": t.total_slots,
        "start_date": t.start_date.isoformat() if t.start_date else None,
        "price": t.price,
        "status": t.status
    } for t in pagination.items]


    return jsonify({"message": "Treks fetched","category": "success","treks_list": treks_list,"pagination": {"page": pagination.page,"limit": limit,"total": pagination.total,
            "pages": pagination.pages,},"filters": {"search": search,"status": status or None, },}), 200


@admin_bp.route("/trek/detail/<int:trek_id>", methods=["GET"])
@role_required('admin')
def trek_detail(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    return jsonify({
        "message": "Trek details fetched",
        "category": "success",
        "trek": {
            "id": trek.id,
            "trek_name": trek.trek_name,
            "state": trek.state,
            "location": trek.location,
            "start_point": trek.start_point,
            "end_point": trek.end_point,
            "pickup_point": trek.pickup_point,
            "difficulty": trek.difficulty,
            "duration_time": trek.duration_time,
            "distance": trek.distance,
            "altitude_max": trek.altitude_max,
            "terrain": trek.terrain,
            "min_age": trek.min_age,
            "max_age": trek.max_age,
            "max_persons": trek.max_persons,
            "available_slots": trek.available_slots,
            "total_slots": trek.total_slots,
            "start_date": trek.start_date.isoformat() if trek.start_date else None,
            "end_date": trek.end_date.isoformat() if trek.end_date else None,
            "price": trek.price,
            "status": trek.status,
            "description": trek.description,
            "inclusions": trek.inclusions,
            "exclusions": trek.exclusions,
            "how_to_reach": trek.how_to_reach,
            "cover_image_url": trek.cover_image_url,
            "staff_assigned_id": trek.staff_assigned_id,
            "rating": trek.rating(),
            "review_count": len(trek.reviews),
            "itinerary": [{
                "day": i.day,
                "title": i.title,
                "description": i.description,
                "altitude": i.altitude,
                "distance": i.distance,
                "time_taking": i.time_taking
            } for i in trek.itinerary],
            "images": [img.image_url for img in trek.trek_images],
            "faqs": [{
                "question": f.question,
                "answer": f.answer,
            } for f in trek.trek_faq],
            "packing_items": [{
                "category": p.category,
                "item_name": p.item_name
            } for p in trek.packing_items],
            "reviews": [{
                "username": r.user.username if r.user else None,
                "rating": r.rating,
                "comments": r.comments,
                "created_at": r.created_at.strftime("%Y-%m-%d") if r.created_at else None
            } for r in trek.reviews]
        },
    }), 200

@admin_bp.route("/create/staff",methods = ["POST"])
@role_required('admin')
def create_staff():
    data = request.get_json()

    if not data:
        return jsonify({"message":"please give correct data "}),400

    required_fields = ['email','password','username']

    missing_fields = [field for field in required_fields if field not in data or data.get(field) is None]

    errors = []
    if missing_fields:
        return jsonify({"message": f"missing field required", "category": "danger"}), 400

    email = data['email'].lower().strip()
    if not check_valid_email(email):
        errors.append("Enter correct email")

    if User.query.filter_by(email=email).first():
        errors.append("A user with this email already exists")

    valid,message = valid_password(data['password'])
    if not valid:
        errors.append(message)

    if len(data['username']) < 5:
        errors.append("username must be minimum of length 5")

    if data.get('phone') and not valid_phone_number(data['phone']):
        errors.append("Invalid phone number")

    if errors:
        return jsonify({"message": errors, "category": "danger"}),400

    staff_user = User(
        username=data['username'].strip(),
        email=email,
        phone=data.get('phone','').strip(),
        role='staff',
        is_active=True,
        is_blacklisted=False
    )
    staff_user.set_pass(data['password'])
    db.session.add(staff_user)
    db.session.flush()

    staff_profile = StaffProfile(
        user_id = staff_user.id,
        experience = data.get('experience',0),
        specialization = data.get('specialization',''),
        status = 'Active'
    )
    db.session.add(staff_profile)
    db.session.commit()

    return jsonify({"message":f"Staff account created successfully for {staff_user.username}","staff_id":staff_profile.id,"user_id":staff_user.id}),201


@admin_bp.route("/staff",methods = ["GET"])
@role_required('admin')
def staff():
    status = request.args.get('status',"",type = str ).strip()
    search  = request.args.get('search',"",type = str ).strip()
    limit = request.args.get('limit',10,type =int)
    page = request.args.get('page',1,type = int)

    if limit <= 0 or limit > 100:
        limit = 10
    if page <= 0:
        page = 1

    query = StaffProfile.query.join(User)

    if status:
        if status not in Valid_staff_status:
            return jsonify({"message":"Invalid status selected","category":"danger"}),400
        query = query.filter(StaffProfile.status == status)

    if search:
        query = query.filter(
            User.username.ilike(f'%{search}%'))
    query = query.order_by(User.id.asc())

    pagination = query.paginate(page=page,per_page=limit,error_out=False)

    staff_list = [{
        "id": s.id,
        "user_id": s.user_id,
        "username": s.user.username if s.user else None,
        "email": s.user.email if s.user else None }for s in pagination.items]
    return jsonify({"message": "Staff fetched","category": "success","Staff": staff_list,"pagination": {"page": pagination.page,"limit": limit,"total": pagination.total,
            "pages": pagination.pages},"filters": {"search": search,"status": status or None, },}), 200

@admin_bp.route("/trekkers")
@role_required('admin')
def trekkers():
    status = request.args.get('status',"",type = str ).strip()
    search  = request.args.get('search',"",type = str ).strip()
    limit = request.args.get('limit',10,type =int)
    page = request.args.get('page',1,type = int)

    if limit <= 0 or limit > 100:
        limit = 10
    if page <= 0:
        page = 1

    query = User.query.filter_by(role = 'trekker')

    if status:
        if status not in Valid_status_trekkers:
            return jsonify({"message":"Invalid status selected","category":"danger"}),400
        if status == 'active':
            query = query.filter(User.is_active == True)
        else:
            query = query.filter(User.is_blacklisted == True)

    if search:
        query = query.filter(
            User.username.ilike(f'%{search}%'))
    query = query.order_by(User.created_at.desc() )

    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    result = []
    for t in pagination.items:
        total_bookings = Booking.query.filter_by(user_id=t.id).count()
        result.append({
           'user_id' :t.id,
           'username':t.username,
           'email':t.email,
           'phone':t.phone,
            'is_active':t.is_active,
            'is_blacklisted' :t.is_blacklisted,
            "created_at": t.created_at.strftime("%Y-%m-%d") if t.created_at else None,
            'total_bookings': total_bookings
       })

    return jsonify({'message':"listed all users",'result':result,'pagination': {
        'page': pagination.page,
        'limit': limit,
        'total': pagination.total,
        'pages': pagination.pages
    }}),200

@admin_bp.route('/toggle/<int:user_id>/active',methods = ['POST'])
@role_required('admin')
def toggle(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message":"No user found","category":"danger"}),400

    if user.role == 'admin':
        return jsonify({ "message":"admin status cannot be changed","category":"danger"}),400

    user.is_active = not user.is_active
    db.session.commit()

    return jsonify({"message":"active status changed successfully","category":"success"}),200


@admin_bp.route('/toggle/<int:user_id>/blacklisted', methods=['POST'])
@role_required('admin')
def toggle_blacklist(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "No user found", "category": "danger"}), 400

    if user.role == 'admin':
        return jsonify({"message": "admin status cannot be changed", "category": "danger"}), 400

    user.is_blacklisted = not user.is_blacklisted
    db.session.commit()

    return jsonify({"message": "blacklisted status changed successfully", "category": "success"}), 200

@admin_bp.route("/bookings")
@role_required('admin')
def bookings():
    status = request.args.get('status',"",type = str ).strip()
    search  = request.args.get('search',"",type = str ).strip()
    trek_name = request.args.get('trek_name',"",type = str).strip()
    limit = request.args.get('limit',10,type =int)
    page = request.args.get('page',1,type = int)


    if limit <= 0 or limit > 100:
        limit = 10
    if page <= 0:
        page = 1

    query = Booking.query.join(User, Booking.user_id == User.id) \
                         .join(Trek, Booking.trek_id == Trek.id)

    if status:
        if status not in Valid_status_booking:
            return jsonify({"message":"Choose correct status to get data","category":"danger"}),400
        query = query.filter(Booking.status == status)
    if trek_name:
        query = query.filter(Trek.trek_name.ilike(f"%{trek_name}%"))

    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                User.username.ilike(like),
                User.email.ilike(like),
                Trek.trek_name.ilike(like)))

    query = query.order_by(Booking.booking_date.desc())

    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    bookings = [{
        "id": b.id,
        "user_id": b.user_id,
        "username": b.user.username if b.user else None,
        "email": b.user.email if b.user else None,
        "trek_id": b.trek_id,
        "trek_name": b.trek.trek_name if b.trek else None,
        "trek_location": b.trek.location if b.trek else None,
        "trek_start_date": b.trek.start_date.isoformat() if b.trek and b.trek.start_date else None,
        "persons": b.num_of_people,
        "total_price": b.total_price,
        "status": b.status,
        "booking_date": b.booking_date.isoformat() if b.booking_date else None,
    } for b in pagination.items]

    return jsonify({"message":"Bookings Fetched","bookings":bookings,"filters":{"status":status or None,"trek_name":trek_name or None,"search":search or None},"pagination Items":{"page": pagination.page,"limit": limit,"total": pagination.total,
            "pages": pagination.pages}})



















