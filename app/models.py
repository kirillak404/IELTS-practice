from datetime import datetime
from typing import Optional

from flask import abort
from flask_login import UserMixin
from sqlalchemy import func, desc
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.dialects.postgresql import JSONB
from itertools import zip_longest

from app import db, login


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), index=True, unique=True, nullable=False)
    is_email_verified = db.Column(db.Boolean, default=False)

    hashed_password = db.Column(db.String(128))
    google_account_id = db.Column(db.String(255), unique=True)

    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    profile_picture = db.Column(db.String(255))
    locale = db.Column(db.String(10))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_progress = db.relationship('UserProgress', backref='user',
                                    cascade='all, delete')

    def __repr__(self):
        return '<User %r>' % self.email

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password, salt_length=16)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

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

    def get_user_subsections_progress(self, user) -> list:
        """
        Returns a list of subsections with user's progress status.

        Function retrieves progress of a user for each subsection in a section.
        The progress status can be "Completed", "In Progress", or "Upcoming".

        Args:
            user (User): User instance.

        Returns:
            list[Subsection]: Subsections with progress status.
        """

        # get user's progress in this section
        user_progress = user.get_section_progress(self.id)

        # get subsections for this section
        subsections = Subsection.query.filter_by(section=self).all()

        # get user attempts for this subsection
        user_attempts = user_progress.user_subsection_attempt if user_progress else ()

        # iterating over subsections and set statuses and attempt id if any
        zipped = zip_longest(subsections, user_attempts)
        is_completed = False
        for subsection, attempt in zipped:
            if attempt:
                subsection.status = "Completed"
                subsection.attempt_id = attempt.id  # set attempt_id for completed subsection
            else:
                if not is_completed:
                    subsection.status = "In Progress"
                    is_completed = True
                else:
                    subsection.status = "Upcoming"
        return subsections


class Subsection(db.Model):
    __tablename__ = 'subsections'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    part_number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    time_limit_minutes = db.Column(db.Integer, nullable=False)

    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'),
                           nullable=False)
    section = db.relationship('Section', back_populates='subsections')

    def __repr__(self):
        return f"<Subsection {self.name}>"

    @staticmethod
    def get_by_section_and_part(section, part):
        return Subsection.query.filter_by(section=section,
                                          part_number=part).first()


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
    def get_random_for_subsection(subsection, last_topic):
        query = QuestionSet.query.filter_by(subsection=subsection)
        if last_topic:
            query = query.filter_by(topic=last_topic)
        return query.order_by(func.random()).first()

    @staticmethod
    def valid_for_subsection(question_set_id, subsection_id):
        question_set = QuestionSet.query.get(question_set_id)
        if not question_set or subsection_id != question_set.subsection_id:
            return False
        return True

    @staticmethod
    def validate_question_set(question_set_id: str) -> Optional['QuestionSet']:
        if not question_set_id:
            abort(400, "question_set_id is missing")
        try:
            question_set_id = int(question_set_id)
        except ValueError:
            return abort(400, "question_set_id must be an integer")
        questions_set = QuestionSet.query.get(question_set_id)
        if not questions_set:
            abort(400, "Invalid question_set_id")
        return questions_set


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
    completed_at = db.Column(db.DateTime)

    user_subsection_attempt = db.relationship('UserSubsectionAttempt',
                                              backref='user_progress',
                                              cascade='all, delete')

    def __init__(self, *args, **kwargs):
        super(UserProgress, self).__init__(*args, **kwargs)
        self.next_subsection_id = Subsection.query.filter_by(
            section_id=self.section_id, part_number=2).first().id

    def update_next_subsection(self, section):
        current_subsection = Subsection.query.get(self.next_subsection_id)
        next_part = current_subsection.part_number + 1
        next_subsection = Subsection.query.filter_by(section=section,
                                                     part_number=next_part).first()

        # if not next_subsection -> section completed
        if not next_subsection:
            self.is_completed = True
            self.next_subsection_id = None
            self.completed_at = datetime.utcnow()
        else:
            self.next_subsection_id = next_subsection.id

    def get_last_topic(self):
        last_attempt = UserSubsectionAttempt.query.filter(
            UserSubsectionAttempt.user_progress_id == self.id
        ).order_by(desc(UserSubsectionAttempt.id)).first()

        return last_attempt.question_set.topic

    @staticmethod
    def create_or_update_user_progress(current_user, user_progress, section,
                                       question_set_id):
        if not user_progress:

            # checking that question_set_id from POST request is valid
            subsection = Subsection.get_by_section_and_part(section, 1)
            subsection_id = subsection.id
            question_set_is_valid = QuestionSet.valid_for_subsection(
                question_set_id, subsection_id)
            if not question_set_is_valid:
                abort(400, "Invalid question_set_id")

            user_progress = UserProgress(user=current_user,
                                         section_id=section.id)
            db.session.add(user_progress)

        # updating user_progress record
        else:
            subsection_id = user_progress.next_subsection_id

            # checking that question_set_id from POST request is valid
            question_set_is_valid = QuestionSet.valid_for_subsection(
                question_set_id, user_progress.next_subsection_id)
            if not question_set_is_valid:
                abort(400, "Invalid question_set_id")

            user_progress.update_next_subsection(section)

        return subsection_id, user_progress


class UserSubsectionAttempt(db.Model):
    __tablename__ = 'user_subsection_attempts'

    id = db.Column(db.Integer, primary_key=True)
    user_progress_id = db.Column(db.Integer, db.ForeignKey('user_progress.id'),
                                 nullable=False)

    subsection_id = db.Column(db.Integer, db.ForeignKey('subsections.id'),
                              nullable=False)
    subsection = db.relationship('Subsection',
                                 backref='user_subsection_attempt')

    question_set_id = db.Column(db.Integer, db.ForeignKey('question_sets.id'),
                                nullable=False)
    question_set = db.relationship('QuestionSet',
                                   backref='user_subsection_attempt')

    created_at = db.Column(db.DateTime, default=datetime.utcnow,
                           nullable=False)

    user_answers = db.relationship('UserSubsectionAnswer',
                                   backref='subsection_attempt',
                                   lazy='joined',
                                   cascade='all, delete')

    speaking_result = db.relationship('UserSpeakingAttemptResult',
                                      uselist=False,
                                      backref='subsection_attempt',
                                      lazy='joined',
                                      cascade='all, delete')

    def aggregate_scores(self) -> dict:
        answers = [a for a in self.user_answers if
                   a.pronunciation_assessment_json]
        total_scores = {
            "accuracy_score": 0,
            "fluency_score": 0,
            "completeness_score": 0,
            "pronunciation_score": 0,
        }
        count = len(answers)
        if not count:
            return total_scores

        for answer in answers:
            total_scores["accuracy_score"] += int(answer.accuracy_score)
            total_scores["fluency_score"] += int(answer.fluency_score)
            total_scores["completeness_score"] += int(
                answer.completeness_score)
            total_scores["pronunciation_score"] += int(
                answer.pronunciation_score)

        # Get the average score
        for score in total_scores:
            total_scores[score] //= count

        return total_scores


class UserSubsectionAnswer(db.Model):
    __tablename__ = 'user_subsection_answers'

    id = db.Column(db.Integer, primary_key=True)
    user_subsection_attempt_id = db.Column(db.Integer,
                                           db.ForeignKey(
                                               'user_subsection_attempts.id'),
                                           nullable=False)

    question_id = db.Column(db.Integer,
                            db.ForeignKey('questions.id'),
                            nullable=False)
    question = db.relationship('Question',
                               backref='user_subsection_answers',
                               lazy='joined')

    transcribed_answer = db.Column(db.Text)
    pronunciation_assessment_json = db.Column(JSONB)
    accuracy_score = db.Column(db.Float)
    fluency_score = db.Column(db.Float)
    completeness_score = db.Column(db.Float)
    pronunciation_score = db.Column(db.Float)

    @staticmethod
    def insert_user_answers(subsection_attempt, questions_set,
                            transcriptions_and_pron_assessments) -> list:
        questions_and_answers = []
        for question, answer in zip(questions_set.questions,
                                    transcriptions_and_pron_assessments):

            pronunciation_assessment = answer.get("pronunciation", {})

            if pronunciation_assessment.get("RecognitionStatus") == "Success":
                n_best = pronunciation_assessment.get("NBest", [{}])
                display_text = n_best[0].get("Display")

                if display_text is not None:
                    questions_and_answers.append(
                        {"question": question.text, "answer": display_text})

                scores = n_best[0]
            else:
                scores = {}

            accuracy_score = scores.get("AccuracyScore")
            fluency_score = scores.get("FluencyScore")
            completeness_score = scores.get("CompletenessScore")
            pronunciation_score = scores.get("PronScore")

            user_subsection_answers = UserSubsectionAnswer(
                subsection_attempt=subsection_attempt,
                question=question,
                transcribed_answer=answer["transcript"],
                pronunciation_assessment_json=pronunciation_assessment,
                accuracy_score=accuracy_score,
                fluency_score=fluency_score,
                completeness_score=completeness_score,
                pronunciation_score=pronunciation_score
            )
            db.session.add(user_subsection_answers)
        return questions_and_answers


class UserSpeakingAttemptResult(db.Model):
    __tablename__ = 'user_speaking_attempt_results'

    id = db.Column(db.Integer, primary_key=True)
    user_subsection_attempt_id = db.Column(db.Integer, db.ForeignKey(
        'user_subsection_attempts.id'), unique=True, nullable=False)
    general_feedback = db.Column(db.Text)
    fluency_coherence_score = db.Column(db.Integer, nullable=False)
    fluency_coherence_json = db.Column(JSONB, nullable=False)
    grammatical_range_accuracy_score = db.Column(db.Integer, nullable=False)
    grammatical_range_accuracy_json = db.Column(JSONB, nullable=False)
    lexical_resource_score = db.Column(db.Integer, nullable=False)
    lexical_resource_json = db.Column(JSONB, nullable=False)
    pronunciation_score = db.Column(db.Integer, nullable=False)
    pronunciation_json = db.Column(JSONB, nullable=False)

    @staticmethod
    def insert_speaking_result(subsection_attempt, gpt_speaking_result):
        speaking_attempt_result = UserSpeakingAttemptResult(
            subsection_attempt=subsection_attempt,
            fluency_coherence_score=gpt_speaking_result['speaking_fluency'][
                'score'],
            fluency_coherence_json=gpt_speaking_result['speaking_fluency'],
            grammatical_range_accuracy_score=
            gpt_speaking_result['speaking_grammar']['score'],
            grammatical_range_accuracy_json=gpt_speaking_result[
                'speaking_grammar'],
            lexical_resource_score=gpt_speaking_result['speaking_lexis'][
                'score'],
            lexical_resource_json=gpt_speaking_result['speaking_lexis'],
            pronunciation_score=gpt_speaking_result['speaking_pronunciation'][
                'score'],
            pronunciation_json=gpt_speaking_result['speaking_pronunciation']
        )
        db.session.add(speaking_attempt_result)
