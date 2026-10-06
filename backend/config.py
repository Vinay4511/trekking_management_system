import os
from datetime import timedelta
class Config:
    SECRET_KEY = 'your-secret-key-change-this'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///trekking.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = 'jwt-secret-key-change-this'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)