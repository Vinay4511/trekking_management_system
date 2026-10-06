from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash,check_password_hash

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer,primary_key = True)
    username = db.Column(db.String(200),nullable =False)
    email = db.Column(db.String(200),unique = True,nullable = False)
    password = db.Column(db.String(200),nullable =False)
    phone = db.Column(db.String(11))
    role = db.Column(db.String(25),nullable = False)
    is_active =  db.Column(db.Boolean,default = True)
    is_blacklisted = db.Column(db.Boolean,default = False)
    created_at = db.Column(db.DateTime,default = datetime.utcnow)

    staff_profile = db.relationship('StaffProfile',backref = 'user', cascade='all, delete-orphan',uselist = False)
    booking = db.relationship('Booking',backref = 'user', cascade='all, delete-orphan',lazy = True)
    review = db.relationship('Review',backref = 'user',cascade='all, delete-orphan',lazy = True)

    def set_pass(self,password):
        self.password = generate_password_hash(password)

    def check_pass(self,password):
        return check_password_hash(self.password,password)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

class StaffProfile(db.Model):
    __tablename__ = "staff_profile"

    id = db.Column(db.Integer,primary_key = True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),unique = True,nullable = False)
    experience = db.Column(db.Integer,default =0)
    specialization = db.Column(db.String(300))
    status = db.Column(db.String(15),default = 'Active')

    assigned_treks = db.relationship('Trek',backref='staff',lazy=True)

    def __repr__(self):
        return f"<StaffProfile {self.id} - User {self.user_id}>"

class Trek(db.Model):
    __tablename__ = "trek"
    id = db.Column(db.Integer,primary_key = True)
    trek_name = db.Column(db.String(100),nullable = False)

    state = db.Column(db.String(50))
    location =  db.Column(db.String(200),nullable = False)
    start_point = db.Column(db.String(50))
    end_point = db.Column(db.String(50))
    pickup_point = db.Column(db.String(50))

    difficulty = db.Column(db.String(20), nullable=False)
    duration_time = db.Column(db.Integer,nullable = False)
    distance = db.Column(db.Float)
    altitude_max = db.Column(db.String(50))
    terrain = db.Column(db.String(50))

    min_age = db.Column(db.Integer,default = 12)
    max_age = db.Column(db.Integer,default = 50)
    max_persons = db.Column(db.Integer,default = 10)

    available_slots = db.Column(db.Integer,nullable = False)
    total_slots = db.Column(db.Integer,nullable = False)
    staff_assigned_id = db.Column(db.Integer,db.ForeignKey('staff_profile.id'),nullable = True)

    start_date = db.Column(db.Date,nullable = False)
    end_date = db.Column(db.Date,nullable = False)

    description = db.Column(db.String(200))
    inclusions = db.Column(db.Text)
    exclusions = db.Column(db.Text)
    how_to_reach = db.Column(db.Text)
    cover_image_url = db.Column(db.String(300))
    created_at = db.Column(db.DateTime,default = datetime.utcnow)
    price = db.Column(db.Float,default = 0.00)
    status = db.Column(db.String(20),default = 'Pending',nullable = False)

    bookings =db.relationship('Booking',backref = 'trek',cascade='all, delete-orphan',lazy = True)
    itinerary = db.relationship('TrekItinerary',backref = 'trek',cascade='all, delete-orphan',lazy = True,order_by='TrekItinerary.day')
    reviews = db.relationship('Review',backref = 'trek',cascade='all, delete-orphan',lazy = True)
    trek_faq = db.relationship('TrekFAQ',backref = 'trek',cascade='all, delete-orphan',lazy = True)
    trek_images = db.relationship('TrekImage',backref = 'trek',cascade='all, delete-orphan',lazy = True)
    packing_items = db.relationship('Packing',backref = 'trek',cascade='all, delete-orphan',lazy = True)

    def rating(self):
        if not self.reviews:
            return 0
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)

    def __repr__(self):
        return f"<Trek name {self.trek_name} - User {self.status}>"

class Booking(db.Model):
    __tablename__ = "booking"
    id = db.Column(db.Integer,primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trek_id = db.Column(db.Integer,db.ForeignKey('trek.id'),nullable = False)
    booking_date = db.Column(db.DateTime,default = datetime.utcnow)
    num_of_people  = db.Column(db.Integer,nullable = False,default = 2)
    total_price = db.Column(db.Float)
    status = db.Column(db.String(25),default = 'Booked')
    payment_status = db.Column(db.String(25),default = 'Pending')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'trek_id', name="unique_trek_user"),
    )

class Review(db.Model):
    __tablename__ = "review"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'), nullable=False)
    rating = db.Column(db.Integer,nullable = False)
    comments = db.Column(db.String(200))
    created_at = db.Column(db.DateTime,default = datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'trek_id', name="unique_user_review"),
        db.CheckConstraint('rating >= 1 AND rating <= 5',name = "rating_range"),
    )
class TrekItinerary(db.Model):
    __tablename__ = "itinerary"
    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'), nullable=False)
    day = db.Column(db.Integer,nullable = False)
    title = db.Column(db.String(100))
    description = db.Column(db.String(250))
    altitude =db.Column(db.Integer)
    distance = db.Column(db.Float)
    time_taking = db.Column(db.String(50))

    __table_args__ = (
       db.UniqueConstraint('trek_id','day',name = "unique_trek_day"),
    )

    def __repr__(self):
        return f"<Itinerary {self.trek_id} - day: {self.day}>"

class TrekImage(db.Model):
    __tablename__ = "images"
    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'), nullable=False)
    image_url = db.Column(db.String(100),nullable = False)
    caption = db.Column(db.String(200))

class Packing(db.Model):
    __tablename__ = "packing"
    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'), nullable=False)
    category = db.Column(db.String(50),nullable = False)
    item_name = db.Column(db.String(55),nullable = False)

class TrekFAQ(db.Model):
    __tablename__ = "TrekFaqs"
    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'), nullable=False)
    question = db.Column(db.String(300),nullable = False)
    answer = db.Column(db.Text,nullable = False)
