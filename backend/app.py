from flask import Flask
from config import Config
from extensions import db,mail,jwt,cache
from routes.auth import auth_bp

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(auth_bp)

db.init_app(app)
mail.init_app(app)
jwt.init_app(app)
cache.init_app(app)

from models import User,StaffProfile,Booking,Trek,TrekImage,TrekFAQ,Packing,TrekItinerary

@app.route('/')
def index():
    from flask import render_template
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

