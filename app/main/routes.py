import json

from flask import render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError, OperationalError

from app import db
from app.main import bp
from app.models import *

from app.openai_tools import transcribe_and_check_errors_in_multiple_files, gpt_evaluate_speaking


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


# TODO: refactoring
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
        practice = {"part": subsection.part_number,
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
    question_set_id = request.form.get('question_set_id')
    if not question_set_id:
        abort(400, "question_set_id is missing")
    try:
        question_set_id = int(question_set_id)
    except ValueError:
        return abort(400, "question_set_id must be an integer")
    questions_set = QuestionSet.query.get(question_set_id)
    if not questions_set:
        abort(400, "Invalid question_set_id")

    # audio files processing
    audio_files = [request.files[key] for key in request.files.keys() if
                   key.startswith('audio_')]
    transcriptions_and_grammar_errors = transcribe_and_check_errors_in_multiple_files(
        audio_files)

    section = Section.get_by_name("speaking")
    user_progress = current_user.get_section_progress(section.id)

    # creating new user_progress record
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

    # inserting new user_subsection_progress
    subsection_attempt = UserSubsectionAttempt(
        user_progress=user_progress,
        subsection_id=subsection_id,
        question_set_id=question_set_id)
    db.session.add(subsection_attempt)

    # TODO check that files count == questions_set questions count AT TOP func
    # inserting user_subsection_answers
    questions_and_answers = []
    for question, answer in zip(questions_set.questions,
                                transcriptions_and_grammar_errors):

        questions_and_answers.append({"question": question.text,
                                      "answer": answer["transcript"]})

        user_subsection_answers = UserSubsectionAnswer(
            subsection_attempt=subsection_attempt,
            question=question,
            transcribed_answer=answer["transcript"],
            transcribed_answer_errors=answer["errors"]
        )
        db.session.add(user_subsection_answers)

    # inserting new user_speaking_attempt_results
    gpt_speaking_result = gpt_evaluate_speaking(questions_and_answers)
    speaking_attempt_result = UserSpeakingAttemptResult(
        subsection_attempt=subsection_attempt,
        general_feedback=gpt_speaking_result.get('generalFeedback'),
        fluency_coherence_score=gpt_speaking_result['criteria']['fluency'].get('score'),
        fluency_coherence_feedback=gpt_speaking_result['criteria']['fluency'].get('feedback'),
        grammatical_range_accuracy_score=gpt_speaking_result['criteria']['grammar'].get('score'),
        grammatical_range_accuracy_feedback=gpt_speaking_result['criteria']['grammar'].get('feedback'),
        lexical_resource_score=gpt_speaking_result['criteria']['lexic'].get('score'),
        lexical_resource_feedback=gpt_speaking_result['criteria']['lexic'].get('feedback'),
        pronunciation_score=gpt_speaking_result['criteria']['pron'].get('score'),
        pronunciation_feedback=gpt_speaking_result['criteria']['pron'].get('feedback')
    )
    db.session.add(speaking_attempt_result)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(400, "Database integrity error")
    except OperationalError:
        db.session.rollback()
        abort(500, "Database operational error")

    return redirect(url_for('main.get_speaking_attempt',
                            user_subsection_attempt_id=subsection_attempt.id))


@login_required
@bp.route('/section/speaking/attempt/<int:user_subsection_attempt_id>/')
def get_speaking_attempt(user_subsection_attempt_id):
    user_subsection_attempt = UserSubsectionAttempt.query.get(
        user_subsection_attempt_id)
    if not user_subsection_attempt:
        abort(404)

    # check that the user requests his answer
    user_progress = user_subsection_attempt.user_progress
    if current_user != user_progress.user:
        abort(403)

    speaking_result = user_subsection_attempt.speaking_result
    questions_and_answers = user_subsection_attempt.get_questions_answer()
    return render_template('section_results.html',
                           result=speaking_result,
                           questions_and_answers=questions_and_answers)


@login_required
@bp.route('/section/speaking/result/<int:id>/')
def get_speaking_result():
    pass
