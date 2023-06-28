from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user

from app.ielts_speaking import evaluate_ielts_speaking
from app.main import bp
from app.models import *
from app.utils import get_current_subsection_and_last_topic, get_practice_data, \
    get_audio_files, get_pron_errors_and_recommendations, \
    save_speaking_results_to_database


@bp.route('/')
def index():
    if current_user.is_authenticated:
        return render_template("dashboard.html")
    return render_template("index.html")


@login_required
@bp.route('/section/<name>')
def render_section(name):
    section = Section.get_by_name(name)
    subsections = section.get_user_subsections_progress(current_user)

    return render_template("section.html",
                           section=section,
                           subsections=subsections)


@login_required
@bp.route('/section/speaking/practice', methods=["GET"])
def speaking_practice_get():
    # Retrieve the 'speaking' section
    section = Section.get_by_name("speaking")
    # Get the current user's progress in this section
    user_progress = current_user.get_section_progress(section.id)
    # Determine the current subsection and last topic based on user's progress
    subsection, last_topic = get_current_subsection_and_last_topic(
        user_progress, section)
    # Get data required for the practice page
    practice = get_practice_data(subsection, last_topic)
    # Render the practice page with obtained data
    return render_template("speaking.html",
                           current_subsection=subsection,
                           practice=practice)


@login_required
@bp.route('/section/speaking/practice', methods=["POST"])
def speaking_practice_post():
    # Retrieving and checking questions_set from the request
    question_set_id = request.form.get('question_set_id')
    questions_set = QuestionSet.validate_question_set(question_set_id)

    # Retrieving audio files from the request
    audio_files = get_audio_files(questions_set)

    # Evaluate speaking with ChatGPT and Azure pronunciation assessment
    speaking_result, answers_evaluation = evaluate_ielts_speaking(questions_set, audio_files)

    # Save result and answers to database
    subsection_attempt = save_speaking_results_to_database(current_user,
                                                           questions_set,
                                                           speaking_result,
                                                           answers_evaluation)

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

    # Your results
    result = user_subsection_attempt.speaking_result

    # Advanced Pronunciation Analysis
    answers = user_subsection_attempt.user_answers
    pron_scores = user_subsection_attempt.aggregate_scores()
    pron_errors = get_pron_errors_and_recommendations(answers)
    return render_template('speaking_result.html', result=result,
                           attempt=user_subsection_attempt,
                           answers=answers, pron_scores=pron_scores,
                           pron_errors=pron_errors)


@login_required
@bp.route('/section/speaking/result/<int:id>/')
def get_speaking_result():
    pass


@bp.route('/reset-section-progress', methods=["POST"])
def reset_section_progress():
    # Retrieve the 'speaking' section
    section = Section.get_by_name("speaking")
    # Get the current user's progress in this section
    user_progress = current_user.get_section_progress(section.id)
    if user_progress:
        db.session.delete(user_progress)
        db.session.commit()

    return redirect(url_for('main.speaking_practice_get'))