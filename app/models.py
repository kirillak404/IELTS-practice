from app import app
from app import db
import re

from werkzeug.security import check_password_hash, generate_password_hash


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    hash = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

    def check_password(self, password):
        return check_password_hash(self.hash, password)

    @staticmethod
    def create_user(email: str, password: str):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        email_is_valid = re.match(pattern, email)
        if email_is_valid and 4 <= len(password) <= 60:
            print("valid")

