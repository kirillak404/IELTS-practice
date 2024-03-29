from datetime import datetime
from typing import Optional
from collections import defaultdict

from flask import abort, flash
from flask_login import UserMixin
from sqlalchemy import func, desc
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.dialects.postgresql import JSONB, UUID
from itertools import zip_longest
import uuid

from config.database import db
from config.auth import login
from app.content.scores import SPEAKING_SCORES_FEEDBACK, SPEAKING_FINAL_FEEDBACK


class User(UserMixin, db.Model):
    """User model. Represents registered users of the app."""

    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    email = db.Column(db.String(255), index=True, unique=True,
                      nullable=False)  # User email address
    is_email_verified = db.Column(db.Boolean, default=False)  # Boolean indicating if email is verified

    hashed_password = db.Column(db.String(128))  # Hashed password for users who registered via email
    google_account_id = db.Column(db.String(255), unique=True)  # Google account ID for users who registered via Google

    first_name = db.Column(db.String(255))  # User's first name
    last_name = db.Column(db.String(255))  # User's last name
    profile_picture = db.Column(db.String(255))  # URL to the user's profile picture
    locale = db.Column(db.String(10))  # User's locale (e.g. en-US)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # The time when the user account was created

    user_progress = db.relationship('UserProgress', backref='user',
                                    cascade='all, delete')  # Tracks user's progress in IELTS sections

    def __repr__(self):
        return '<User %r>' % self.email

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password, salt_length=16)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def get_section_progress(self, section_id):
        return UserProgress.query.filter(
            UserProgress.user_id == self.id,
            UserProgress.section_id == section_id,
            UserProgress.is_completed is False
        ).first()

    def get_sections_history(self):
        user_progress = UserProgress.query.filter(
            UserProgress.user_id == self.id
        ).all()
        return user_progress


@login.user_loader
def load_user(id):
    return User.query.get(id)


class Section(db.Model):
    """Section model. Represents a section in the IELTS exam."""

    __tablename__ = 'sections'

    id = db.Column(db.Integer, primary_key=True)  # Unique section ID
    name = db.Column(db.String(128), unique=True, nullable=False)  # Section name
    description = db.Column(db.String(255), nullable=False)  # Description of the section

    subsections = db.relationship('Subsection', back_populates='section')  # List of subsections in a section

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
        user_attempts = user_progress.attempts if user_progress else ()

        # iterating over subsections and set statuses and attempt id if any
        is_completed = False
        for subsection, attempt in zip_longest(subsections, user_attempts):
            if attempt:
                subsection.status = "Completed"
                subsection.attempt_id = attempt.id  # set attempt_id for completed subsection
            else:
                if not is_completed:
                    subsection.status = "Available"
                    is_completed = True
                else:
                    subsection.status = "Upcoming"
        return subsections


class Subsection(db.Model):
    """Subsection model. Represents a subsection in an IELTS exam section."""

    __tablename__ = 'subsections'

    id = db.Column(db.Integer, primary_key=True)  # Unique subsection ID
    name = db.Column(db.String(128), nullable=False)  # Subsection name
    part_number = db.Column(db.Integer, nullable=False)  # Order number of the subsection within the section
    description = db.Column(db.String(255), nullable=False)  # Description of the subsection
    time_limit_minutes = db.Column(db.Integer, nullable=False)  # Time limit for the subsection in minutes

    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)  # ID of the section this subsection belongs to
    section = db.relationship('Section', back_populates='subsections')  # Relationship to the parent section

    def __repr__(self):
        return f"<Subsection {self.name}>"

    @staticmethod
    def get_by_section_and_part(section, part):
        return Subsection.query.filter_by(section=section,
                                          part_number=part).first()


class Topic(db.Model):
    """Topic model. Represents a topic that can appear in a subsection."""

    __tablename__ = 'topics'

    id = db.Column(db.Integer, primary_key=True)  # Unique topic ID
    name = db.Column(db.String(128), nullable=False)  # Topic name
    description = db.Column(db.String(255), nullable=False)  # Description of the topic

    def __repr__(self):
        return f"<Topic {self.name}>"


class QuestionSet(db.Model):
    """QuestionSet model. Represents a set of questions for a subsection-topic pair."""

    __tablename__ = 'question_sets'

    id = db.Column(db.Integer, primary_key=True)  # Unique question set ID

    subsection_id = db.Column(db.Integer, db.ForeignKey('subsections.id'), nullable=False)  # ID of the subsection this question set belongs to
    subsection = db.relationship('Subsection', backref='question_sets')  # Relationship to the subsection

    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'))  # ID of the topic this question set is about
    topic = db.relationship('Topic', backref='question_sets', lazy='joined')  # Relationship to the topic

    questions = db.relationship('Question', backref='question_set', lazy='joined')  # List of questions in the set

    __table_args__ = (
        db.UniqueConstraint('subsection_id', 'topic_id', name='uix_1'),)

    def __iter__(self):
        yield from self.questions

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
            flash("An error has occurred, please try again")
            print("question_set_id is missing")
            abort(400, "question_set_id is missing")
        try:
            question_set_id = int(question_set_id)
        except ValueError:
            flash("An error has occurred, please try again")
            print("question_set_id must be an integer")
            return abort(400, "question_set_id must be an integer")
        questions_set = QuestionSet.query.get(question_set_id)
        if not questions_set:
            flash("An error has occurred, please try again")
            print("Invalid question_set_id")
            abort(400, "Invalid question_set_id")
        return questions_set


class Question(db.Model):
    """Question model. Represents a question in a question set."""

    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)  # Unique question ID
    text = db.Column(db.String(1000), nullable=False)  # Text of the question

    question_set_id = db.Column(db.Integer, db.ForeignKey('question_sets.id'), nullable=False)  # ID of the question set this question belongs to


class UserProgress(db.Model):
    """UserProgress model. Represents the progress of a user in a section."""

    __tablename__ = 'user_progress'

    id = db.Column(db.Integer, primary_key=True)  # Unique progress ID
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)  # ID of the section this progress record is for
    next_subsection_id = db.Column(db.Integer, db.ForeignKey('subsections.id'))  # ID of the next subsection the user should attempt
    is_completed = db.Column(db.Boolean, nullable=False, default=False)  # Boolean indicating if the section has been completed
    completed_at = db.Column(db.DateTime)  # The time when the section was completed

    section = db.relationship('Section', lazy='joined')
    attempts = db.relationship('UserSubsectionAttempt', backref='user_progress', cascade='all, delete')  # Tracks user's attempts in subsections

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
    def create_or_update_user_progress(user, user_progress, section,
                                       question_set_id):
        if not user_progress:

            # checking that question_set_id from POST request is valid
            subsection = Subsection.get_by_section_and_part(section, 1)
            subsection_id = subsection.id
            question_set_is_valid = QuestionSet.valid_for_subsection(
                question_set_id, subsection_id)
            if not question_set_is_valid:
                abort(400, "Invalid question_set_id")

            user_progress = UserProgress(user=user,
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

    def get_speaking_final_scores(self) -> dict:
        """
        Calculate and return final scores for speaking. Each score is an average of attempts,
        rounded to the nearest whole number. The final score is an average of all scores,
        rounded to the nearest 0.5.

        Returns:
            dict: Dictionary containing the final scores for fluency_coherence,
                  grammatical_range_accuracy, lexical_resource, pronunciation, and final score.
        """

        if not self.is_completed:
            raise RuntimeError("Cannot calculate final scores before section completion.")

        # Define the score types
        score_types = ['fluency_coherence_score',
                       'grammatical_range_accuracy_score',
                       'lexical_resource_score',
                       'pronunciation_score']

        # Initialize a defaultdict to store total scores
        scores = defaultdict(int)

        # Add up all the scores for each score type
        for attempt in self.attempts:
            for score_type in score_types:
                scores[score_type] += getattr(attempt.results, score_type)

        # Calculate the average for each score type and round to the nearest whole number
        for score in scores:
            scores[score] = round(scores[score] / len(self.attempts))

        # Calculate and store the final score as the average of all scores, rounded to the nearest 0.5
        overall_score = round(sum(scores.values()) / len(scores) * 2) / 2
        scores['overall_score'] = overall_score

        # Set text feedback for final (overall) score
        scores['overall_score_feedback_text'] = SPEAKING_FINAL_FEEDBACK[int(overall_score)]

        return scores


class UserSubsectionAttempt(db.Model):
    """UserSubsectionAttempt model. Represents an attempt by a user to answer a question set in a subsection."""

    __tablename__ = 'user_subsection_attempts'

    id = db.Column(db.Integer, primary_key=True)  # Unique attempt ID
    user_progress_id = db.Column(db.Integer, db.ForeignKey('user_progress.id'), nullable=False)  # ID of the user progress record this attempt is linked to

    subsection_id = db.Column(db.Integer, db.ForeignKey('subsections.id'), nullable=False)  # ID of the subsection this attempt is for
    subsection = db.relationship('Subsection', backref='user_subsection_attempt')  # Relationship to the subsection

    question_set_id = db.Column(db.Integer, db.ForeignKey('question_sets.id'), nullable=False)  # ID of the question set this attempt is for
    question_set = db.relationship('QuestionSet', backref='user_subsection_attempt')  # Relationship to the question set

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # The time when the attempt was made

    user_answers = db.relationship('UserSubsectionAnswer', backref='subsection_attempt', lazy='joined', cascade='all, delete')  # Tracks user's answers in the attempt

    results = db.relationship('UserSpeakingAttemptResult', uselist=False, backref='subsection_attempt', lazy='joined', cascade='all, delete')  # Stores result of speaking attempt

    def get_overall_pron_scores(self) -> dict:
        answers = tuple(a for a in self.user_answers if
                        a.pronunciation_assessment_json)

        count = len(answers)
        if not count:
            return {"accuracy_score": 0, "fluency_score": 0,
                    "completeness_score": 0, "pronunciation_score": 0}

        total_scores = {
            "accuracy_score": sum(int(a.accuracy_score) for a in answers),
            "fluency_score": sum(int(a.fluency_score) for a in answers),
            "completeness_score": sum(
                int(a.completeness_score) for a in answers),
            "pronunciation_score": sum(
                int(a.pronunciation_score) for a in answers),
        }

        average_scores = {score: total // count for score, total in
                          total_scores.items()}

        return average_scores

    def get_attempt_overall_score(self):
        """
        Calculate the average of four different scores, then rounds it to the nearest 0.5.
        If any of the scores is None, the method will return 0.0.

        Returns:
            float: Overall score rounded to the nearest 0.5, or 0.0 if any score is None.
        """

        # Retrieving scores
        scores = (self.results.fluency_coherence_score,
                  self.results.grammatical_range_accuracy_score,
                  self.results.lexical_resource_score,
                  self.results.pronunciation_score)

        # Check if all scores are not None
        if all(s is not None for s in scores):
            # If all scores are present, calculate the average, double it,
            # round to the nearest whole number, then halve it to get rounding to the nearest 0.5
            return round(sum(scores) / 4 * 2) / 2
        else:
            # If any score is None, return 0.0
            return 0.0


class UserSubsectionAnswer(db.Model):
    """UserSubsectionAnswer model. Represents a user's answer to a question in an attempt."""

    __tablename__ = 'user_subsection_answers'

    id = db.Column(db.Integer, primary_key=True)  # Unique answer ID
    user_subsection_attempt_id = db.Column(db.Integer, db.ForeignKey('user_subsection_attempts.id'), nullable=False)  # ID of the attempt this answer is part of

    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)  # ID of the question this answer is for
    question = db.relationship('Question', backref='user_subsection_answers', lazy='joined')  # Relationship to the question

    transcribed_answer = db.Column(db.Text)  # Text of the transcribed answer
    pronunciation_assessment_json = db.Column(JSONB)  # JSON data from pronunciation assessment
    accuracy_score = db.Column(db.Float)  # Score for accuracy
    fluency_score = db.Column(db.Float)  # Score for fluency
    completeness_score = db.Column(db.Float)  # Score for completeness
    pronunciation_score = db.Column(db.Float)  # Score for pronunciation

    @staticmethod
    def insert_user_answers(subsection_attempt, answers_evaluation) -> None:

        for answer in answers_evaluation:
            pronunciation_assessment = answer.get('pronunciation_assessment')
            scores = pronunciation_assessment.get('NBest')[0]
            user_subsection_answers = UserSubsectionAnswer(
                subsection_attempt=subsection_attempt,
                question=answer.get('question'),
                transcribed_answer=answer.get('answer_transcription'),
                pronunciation_assessment_json=pronunciation_assessment,
                accuracy_score=scores['AccuracyScore'],
                fluency_score=scores['FluencyScore'],
                completeness_score=scores['CompletenessScore'],
                pronunciation_score=scores['PronScore']
            )
            db.session.add(user_subsection_answers)


class UserSpeakingAttemptResult(db.Model):
    """UserSpeakingAttemptResult model. Represents the result of a speaking attempt."""

    __tablename__ = 'user_speaking_attempt_results'

    id = db.Column(db.Integer, primary_key=True)  # Unique result ID
    user_subsection_attempt_id = db.Column(db.Integer, db.ForeignKey('user_subsection_attempts.id'), unique=True, nullable=False)  # ID of the attempt this result is for
    general_feedback = db.Column(db.Text)  # General feedback for the speaking attempt
    fluency_coherence_score = db.Column(db.Integer, nullable=False)  # Score for fluency and coherence
    grammatical_range_accuracy_score = db.Column(db.Integer, nullable=False)  # Score for grammatical range and accuracy
    lexical_resource_score = db.Column(db.Integer, nullable=False)  # Score for lexical resource
    pronunciation_score = db.Column(db.Integer, nullable=False)  # Score for pronunciation

    @staticmethod
    def insert_speaking_result(subsection_attempt, speaking_result):
        speaking_attempt_result = UserSpeakingAttemptResult(
            subsection_attempt=subsection_attempt,
            general_feedback=speaking_result['generalFeedback'],
            fluency_coherence_score=speaking_result['fluencyAndCoherence']['score'],
            grammatical_range_accuracy_score=speaking_result['grammaticalRangeAndAccuracy']['score'],
            lexical_resource_score=speaking_result['lexicalResource']['score'],
            pronunciation_score=speaking_result['pronunciation']['score'],
        )
        db.session.add(speaking_attempt_result)

    def get_speaking_scores(self) -> tuple:
        """
        Gather and return speaking scores, and add feedback using another function.

        Returns:
            tuple: A tuple of dictionaries, each containing criterion name, its score, and feedback.
        """
        CRITERIA_DESCRIPTION = ('Evaluates how smoothly and logically a speaker communicates ideas, focusing on organization of thoughts and fluid speech.',
                                'Assesses the range and appropriateness of vocabulary usage, including the ability to paraphrase.',
                                'Measures the usage of various grammatical structures correctly, examining both range and accuracy.',
                                'Rates the clarity of speech, including pronunciation of words, sentence stress, and intonation.')

        scores = ({'name': 'Fluency and Coherence',
                   'score': self.fluency_coherence_score,
                   'description': CRITERIA_DESCRIPTION[0]},
                  {'name': 'Lexical Resource',
                   'score': self.lexical_resource_score,
                   'description': CRITERIA_DESCRIPTION[1]},
                  {'name': 'Grammatical Range & Accuracy',
                   'score': self.grammatical_range_accuracy_score,
                   'description': CRITERIA_DESCRIPTION[2]},
                  {'name': 'Pronunciation',
                   'score': self.pronunciation_score,
                   'description': CRITERIA_DESCRIPTION[3]})

        UserSpeakingAttemptResult.set_speaking_scores_feedback(scores)
        return scores

    @staticmethod
    def set_speaking_scores_feedback(scores: tuple) -> None:
        """
        Assign feedback to each score based on the SCORES_FEEDBACK dictionary.

        Args:
            scores (tuple): A tuple of dictionaries containing criterion name and its score.
        """
        for score in scores:
            criterion = score['name']
            criterion_score = score['score']
            feedback_text = SPEAKING_SCORES_FEEDBACK[criterion][criterion_score]
            score['feedback'] = feedback_text

    @staticmethod
    def save_result(user, question_set):

        # Get the 'speaking' section
        section = Section.get_by_name("speaking")
        # Get the current user's progress in this section
        user_progress = user.get_section_progress(section.id)

        # Update or create user's progress based on previous section progress
        subsection_id, user_progress = UserProgress.create_or_update_user_progress(
            user, user_progress, section, question_set.id)
