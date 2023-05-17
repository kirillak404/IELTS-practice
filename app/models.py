from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), index=True, unique=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False)

    password_hash = db.Column(db.String(128))
    google_id = db.Column(db.String(255), unique=True)

    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    profile_picture = db.Column(db.String(255))
    locale = db.Column(db.String(10))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<User %r>' % self.email

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, salt_length=16)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_google_id(self, google_id):
        self.google_id = google_id


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Section(db.Model):
    __tablename__ = 'sections'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"{self.id}, {self.name}, {self.description}"


class Subsection(db.Model):
    __tablename__ = 'subsections'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    part_number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    approx_time = db.Column(db.String(128), nullable=False)

    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    section = db.relationship('Section', backref='subsections')


class QuestionSet(db.Model):
    __tablename__ = 'question_sets'

    id = db.Column(db.Integer, primary_key=True)

    subsection_id = db.Column(db.Integer, db.ForeignKey('subsections.id'), nullable=False)
    subsection = db.relationship('Subsection', backref='question_sets')


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)

    question_set_id = db.Column(db.Integer, db.ForeignKey('question_sets.id'), nullable=False)
    question_set = db.relationship('QuestionSet', backref='questions')


class Topic(db.Model):
    __tablename__ = 'topics'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False, unique=True)

    subsection_id = db.Column(db.Integer, db.ForeignKey('subsections.id'), nullable=False)
    subsection = db.relationship('Subsection', backref='topics')


class TopicQuestion(db.Model):
    __tablename__ = 'topic_questions'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)

    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    topic = db.relationship('Topic', backref='topic_questions')


class TopicDiscussionQuestion(db.Model):
    __tablename__ = 'topic_discussion_questions'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)

    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    topic = db.relationship('Topic', backref='topic_discussion_questions')