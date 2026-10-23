from flask import Blueprint,jsonify,request
from backend.models import Trek
VALID_DIFFICULTY = {'Easy','Moderate','Hard'}

trek_bp = Blueprint("trek", __name__, url_prefix="/trek")

@trek_bp.route("", methods=["GET"])
def treks():
    status = request.args.get('status',"",type = str ).strip()
    search  = request.args.get('search',"",type = str ).strip()
    limit = request.args.get('limit',10,type =int)
    page = request.args.get('page',1,type = int)
    difficulty = request.args.get('difficulty', "", type=str).strip()
    location = request.args.get('location', "", type=str).strip()
    duration = request.args.get('duration', "", type=int)

    if limit <= 0 or limit > 100:
        limit = 10
    if page <= 0:
        page = 1

    query = Trek.query.filter_by(status = 'Open')

    if search:
        query = query.filter(
            Trek.trek_name.ilike(f'%{search}%'))


    if difficulty:
        if difficulty in VALID_DIFFICULTY:
            query = query.filter(Trek.difficulty == difficulty)
        else:
            return jsonify({"message":"select difficulty in {VALID_DIFFICULTY}","category":'danger'}),400

    if location:
        query = query.filter_by(Trek.location == f'&{location}&')

    if duration:
        query = query.filter_by(Trek.duration_time == duration)

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
        "status": t.status,
        "duration_time":t.duration_time,
        "end_date":t.end_date.isoformat() if t.end_date else None,
        "image_url":t.cover_image_url,
        "avg_rating":t.avg_rating
    } for t in pagination.items]


    return jsonify({"message": "Treks fetched","category": "success","treks_list": treks_list,"pagination": {"page": pagination.page,"limit": limit,"total": pagination.total,
            "pages": pagination.pages,},"filters": {"search": search,"status": status or None, },}), 200

@trek_bp.route("/detail/<int:trek_id>", methods=["GET"])
def trek_detail(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if not trek:
        return jsonify({"message": "Trek not found", "category": "danger"}), 404

    if trek.status != 'Open':
        return jsonify({"message": " trek is not available", "category": "danger"}), 404

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

@trek_bp.route("/similar/<int:trek_id>", methods=["GET"])
def trek_similar(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if not trek:
        return jsonify({"message": "Trek not found", "category": "danger"}), 404

    similar = Trek.query.filter(Trek.difficulty == trek.difficulty,Trek.duration_time == trek.duration_time,Trek.id != trek_id).limit(4).all()

    result =[{"id": t.id,
        "trek_name": t.trek_name,
        "location": t.location,
        "difficulty": t.difficulty,
        "available_slots": t.available_slots,
        "total_slots": t.total_slots,
        "start_date": t.start_date.isoformat() if t.start_date else None} for t in similar]
    return jsonify({"message": "Similar treks fetched", "category": "success", "treks": result}), 200
