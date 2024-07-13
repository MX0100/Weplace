import uuid
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)


class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    date_published = db.Column(db.DateTime, default=datetime.utcnow)


class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token = db.Column(db.String(36), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    user = db.relationship('User', backref=db.backref('sessions', lazy=True))

    def __init__(self, user_id):
        self.user_id = user_id
        self.session_token = str(uuid.uuid4())
        self.expires_at = datetime.utcnow() + timedelta(hours=1)  # 1小时会话
