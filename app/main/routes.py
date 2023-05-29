import json
import os
from flask import render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError, OperationalError

from app import db
from app.main import bp
from app.models import *

from app.openai_tools import transcribe_audio


@bp.route('/')
def index():
    if current_user.is_authenticated:
        return render_template("dashboard.html")
    return render_template("index.html")


@login_required
@bp.route('/section/<name>')
def render_section(name):
    section = Section.get_by_name(name)
    subsections = Subsection.query.filter_by(section=section).all()

    return render_template("section.html",
                           section=section,
                           subsections=subsections)


@login_required
@bp.route('/section/speaking/practice', methods=["GET", "POST"])
def speaking_practice():
    if request.method == "GET":
        section = Section.get_by_name("speaking")
        user_progress = current_user.get_section_progress(section.id)

        if user_progress:
            subsection = Subsection.query.get(
                user_progress.next_subsection_id)
            last_topic_id = user_progress.get_last_topic()
        else:
            subsection = Subsection.get_by_section_and_part(section, 1)
            last_topic_id = None

        # data for the practice page
        question_set = QuestionSet.get_random_for_subsection(
            subsection, last_topic_id)
        topic_name = question_set.topic.name if question_set.topic else None
        topic_desc = question_set.topic.description if question_set.topic else None
        practice = {"part": subsection.part,
                    "topic_name": topic_name,
                    "topic_desc": topic_desc,
                    "answer_time_limit": subsection.time_limit_minutes,
                    "question_id": question_set.id,
                    "questions": [q.text for q in question_set.questions]}

        return render_template("speaking.html",
                               subsections=section.subsections,
                               current_subsection=subsection,
                               practice=practice)

    # POST request processing

    # validating data
    audio_file = request.files.get('audio')
    if not audio_file:
        abort(400, "Audio record is missing")

    question_set_id = request.form.get('question_set_id')
    if not question_set_id:
        abort(400, "question_set_id is missing")
    try:
        question_set_id = int(question_set_id)
    except ValueError:
        return abort(400, "Question set must be an integer")

    # transcribing user answers TODO try...
    answer_text = transcribe_audio(audio_file)

    section = Section.get_by_name("speaking")
    user_progress = current_user.get_section_progress(section.id)

    # creating new user_progress record
    if not user_progress:

        # checking that question_set_id from POST request is valid
        subsection = Subsection.get_by_section_and_part(section, 1)
        question_set_is_valid = QuestionSet.valid_for_subsection(
            question_set_id, subsection.id)
        if not question_set_is_valid:
            abort(400, "Invalid question_set_id")

        user_progress = UserProgress(user=current_user,
                                     section_id=section.id)
        db.session.add(user_progress)

    # updating user_progress record
    else:
        # checking that question_set_id from POST request is valid
        question_set_is_valid = QuestionSet.valid_for_subsection(
            question_set_id, user_progress.next_subsection_id)
        if not question_set_is_valid:
            abort(400, "Invalid question_set_id")

        user_progress.update_next_subsection(section)

    # inserting new user_answer
    user_answer = UserAnswer(user_progress=user_progress,
                             question_set_id=question_set_id,
                             answer_text=answer_text)
    db.session.add(user_answer)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(400, "Database integrity error")
    except OperationalError:
        db.session.rollback()
        abort(500, "Database operational error")

    return redirect(url_for('main.speaking_practice'))


@bp.route('/test')
def test():
    return render_template("test.html")