from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import func, desc
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
    profile_picture = db.Column(db.Text)
    locale = db.Column(db.String(10))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_progress = db.relationship('UserProgress', backref='user',
                                    cascade='all, delete')

    def __repr__(self):
        return '<User %r>' % self.email

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, salt_length=16)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_google_id(self, google_id):
        self.google_id = google_id

    def get_section_progress(self, section_id):
        user_progress = UserProgress.query.filter(
            UserProgress.user_id == self.id,
            UserProgress.section_id == section_id,
            UserProgress.is_completed == False
        ).first()
        return user_progress


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Section(db.Model):
    __tablename__ = 'sections'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)

    subsections = db.relationship('Subsection', back_populates='section')

    def __repr__(self):
        return f"<Section {self.name}>"

    @staticmethod
    def get_by_name(name):
        return Section.query.filter(Section.name.ilike(name)).first_or_404()


class Subsection(db.Model):
    __tablename__ = 'subsections'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    part = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    time_limit_minutes = db.Column(db.Integer, nullable=False)

    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'),
                           nullable=False)
    section = db.relationship('Section', back_populates='subsections')

    def __repr__(self):
        return f"<Subsection {self.name}>"

    @staticmethod
    def get_by_section_and_part(section, part):
        return Subsection.query.filter_by(section=section, part=part).first()


class Topic(db.Model):
    __tablename__ = 'topics'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Topic {self.name}>"


class QuestionSet(db.Model):
    __tablename__ = 'question_sets'

    id = db.Column(db.Integer, primary_key=True)

    subsection_id = db.Column(db.Integer, db.ForeignKey('subsections.id'),
                              nullable=False)
    subsection = db.relationship('Subsection', backref='question_sets')

    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'))
    topic = db.relationship('Topic', backref='question_sets', lazy='joined')

    questions = db.relationship('Question', backref='question_set',
                                lazy='joined')
    __table_args__ = (
        db.UniqueConstraint('subsection_id', 'topic_id', name='uix_1'),)

    @staticmethod
    def get_random_for_subsection(subsection, topic_id=None):
        query = QuestionSet.query.filter_by(subsection=subsection)
        if topic_id:
            query = query.filter_by(topic_id=topic_id)
        return query.order_by(func.random()).first()

    @staticmethod
    def valid_for_subsection(question_set_id, subsection_id):
        question_set = QuestionSet.query.get(question_set_id)
        if not question_set or subsection_id != question_set.subsection_id:
            return False
        return True


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(1000), nullable=False)

    question_set_id = db.Column(db.Integer, db.ForeignKey('question_sets.id'),
                                nullable=False)


class UserProgress(db.Model):
    __tablename__ = 'user_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'),
                           nullable=False)
    next_subsection_id = db.Column(db.Integer, db.ForeignKey('subsections.id'))
    is_completed = db.Column(db.Boolean, nullable=False, default=False)
    completed_on = db.Column(db.DateTime)

    user_subsection_progress = db.relationship('UserSubsectionProgress',
                                               backref='user_progress',
                                               cascade='all, delete')

    def __init__(self, *args, **kwargs):
        super(UserProgress, self).__init__(*args, **kwargs)
        self.next_subsection_id = Subsection.query.filter_by(
            section_id=self.section_id, part=2).first().id

    def update_next_subsection(self, section):
        current_subsection = Subsection.query.get(self.next_subsection_id)
        next_part = current_subsection.part + 1
        next_subsection = Subsection.query.filter_by(section=section,
                                                     part=next_part).first()

        # if not next_subsection -> section completed
        if not next_subsection:
            self.is_completed = True
            self.next_subsection_id = None
            self.completed_on = datetime.utcnow()
        else:
            self.next_subsection_id = next_subsection.id

    def get_last_topic(self):
        last_answer = UserSubsectionProgress.query.filter(
            UserSubsectionProgress.user_progress_id == self.id
        ).order_by(desc(UserSubsectionProgress.id)).first()

        return last_answer.question_set.topic_id


class UserSubsectionProgress(db.Model):
    __tablename__ = 'user_subsection_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_progress_id = db.Column(db.Integer, db.ForeignKey('user_progress.id'),
                                 nullable=False)

    subsection_id = db.Column(db.Integer, db.ForeignKey('subsections.id'),
                              nullable=False)
    subsection = db.relationship('Subsection',
                                 backref='user_subsection_progress')

    question_set_id = db.Column(db.Integer, db.ForeignKey('question_sets.id'),
                                nullable=False)
    question_set = db.relationship('QuestionSet',
                                   backref='user_subsection_progress')

    created_at = db.Column(db.DateTime, default=datetime.utcnow,
                           nullable=False)

    user_answers = db.relationship('UserSubsectionAnswer',
                                   backref='user_subsection_progress',
                                   lazy='joined')

    def get_questions_answer(self):
        user_answers = self.user_answers
        result = []

        for answer in user_answers:
            question = answer.question.text
            grammar_marked_answer = answer.transcribed_answer  # TODO replace on answer.grammar_marked_answer
            result.append(
                {"question": question, "answer": grammar_marked_answer})

        return result


class UserSubsectionAnswer(db.Model):
    __tablename__ = 'user_subsection_answers'

    id = db.Column(db.Integer, primary_key=True)
    user_subsection_progress_id = db.Column(db.Integer,
                                            db.ForeignKey(
                                                'user_subsection_progress.id'),
                                            nullable=False)

    question_id = db.Column(db.Integer,
                            db.ForeignKey('questions.id'),
                            nullable=False)
    question = db.relationship('Question',
                               backref='user_subsection_answers',
                               lazy='joined')

    transcribed_answer = db.Column(db.Text, nullable=False)
    grammar_marked_answer = db.Column(db.Text, nullable=False)
