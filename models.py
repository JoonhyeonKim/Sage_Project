from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.orm import Session
# from app import app

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
db = SQLAlchemy()

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    messages = db.relationship('Message', backref='conversation', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    is_user = db.Column(db.Boolean, default=True)  # True for user, False for AI

def init_app(app):
    db.init_app(app)
# Remember to create the database by running: db.create_all() after defining your models