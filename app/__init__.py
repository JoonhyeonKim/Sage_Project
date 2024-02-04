from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from config import Config  # You will create this config file in the next step
from .models.models import db, init_app, Conversation, Message  # Import db and init_app

db = db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    Session(app)

    with app.app_context():
        from .main.routes import main as main_routes
        app.register_blueprint(main_routes)

        db.create_all()  # Create database tables
        # init_app(app)  # This is actually not needed since db.init_app(app) is called already

    return app
