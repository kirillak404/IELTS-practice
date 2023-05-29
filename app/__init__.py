from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth

from app.utils import validation_class
from app.ielts_seeds import SECTIONS, SUBSECTIONS, QUESTIONS, TOPICS
from config import Config

db = SQLAlchemy()
login = LoginManager()
oauth = OAuth()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    login.init_app(app)
    db.init_app(app)
    oauth.init_app(app)

    with app.app_context():
        # importing models
        from app import models

        # creating tables
        db.create_all()

        # creating defaults data TODO вынести в utils
        if not models.Section.query.first():  # if no sections in database

            # inserting sections
            for section in SECTIONS:
                new_section = models.Section(**section)
                db.session.add(new_section)

            db.session.commit()

            # inserting subsections
            for subsection in SUBSECTIONS:
                section = models.Section.query.filter_by(
                    name=subsection["section"]).first()
                subsection["section"] = section
                new_subsection = models.Subsection(**subsection)
                db.session.add(new_subsection)
            db.session.commit()

            # inserting PART 1 topics
            for question_set in QUESTIONS:
                subsection = models.Subsection.query.filter_by(
                    name=question_set["subsection"]).first()

                # inserting new subsection_question
                new_question_set = models.QuestionSet(subsection=subsection)
                db.session.add(new_question_set)

                # inserting questions inside topic
                for question in question_set["questions"]:
                    new_question = models.Question(text=question,
                                                   question_set=new_question_set)
                    db.session.add(new_question)

            db.session.commit()

            # inserting PART 2-3 topics
            for topic in TOPICS:
                subsection = models.Subsection.query.filter_by(
                    name=topic["subsection"]).first()

                # inserting new topic
                new_topic = models.Topic(name=topic["name"],
                                         description=topic["description"])
                db.session.add(new_topic)

                # inserting topic GENERAL questions
                new_question_set = models.QuestionSet(subsection=subsection,
                                                       topic=new_topic)
                db.session.add(new_question_set)

                for question in topic["general_questions"]:
                    new_question = models.Question(text=question,
                                                   question_set=new_question_set)
                    db.session.add(new_question)

                # inserting topic DISCUSSION questions
                subsection = models.Subsection.query.filter_by(
                    name="Two-way Discussion").first()
                new_question_set = models.QuestionSet(subsection=subsection, topic=new_topic)

                for question in topic["discussion_questions"]:
                    new_question = models.Question(text=question,
                                                   question_set=new_question_set)
                    db.session.add(new_question)

            db.session.commit()

    # register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    app.jinja_env.filters['validation_class'] = validation_class

    return app
