from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user

from app.ielts_speaking import evaluate_ielts_speaking
from app.speaking_eval import SpeechEvaluator
from app.main import bp
from app.models import *
from app.utils import get_current_subsection_and_last_topic, get_practice_data, \
    get_audio_files, save_speaking_results_to_database, send_amplitude_event


@bp.route('/')
def index():
    if current_user.is_authenticated:
        return render_template("dashboard.html")
    return redirect(url_for('auth.login'))


@bp.route('/section/<name>')
@login_required
def render_section(name):
    section = Section.get_by_name(name)
    subsections = section.get_user_subsections_progress(current_user)

    return render_template("section.html",
                           section=section,
                           subsections=subsections)


@bp.route('/section/speaking/practice', methods=["GET"])
@login_required
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


@bp.route('/section/speaking/practice', methods=["POST"])
@login_required
def speaking_practice_post():
    # Retrieving and checking questions_set from the request
    question_set_id = request.form.get('question_set_id')
    questions_set = QuestionSet.validate_question_set(question_set_id)

    # Retrieving audio files from the request
    audio_files = get_audio_files(questions_set)

    speech_evaluator = SpeechEvaluator(questions_set, audio_files)
    speech_evaluator.evaluate_speaking()
    print('scores:')
    print(speech_evaluator.ielts_scores)
    return render_template("dashboard.html")


    # # Evaluate speaking with ChatGPT and Azure pronunciation assessment
    # speaking_result, answers_evaluation = evaluate_ielts_speaking(
    #     questions_set, audio_files)
    #
    # # Save result and answers to database
    # subsection_attempt = save_speaking_results_to_database(current_user,
    #                                                        questions_set,
    #                                                        speaking_result,
    #                                                        answers_evaluation)
    #
    # # sending events to Amplitude Analytics
    # part_number = questions_set.subsection.part_number
    # send_amplitude_event(current_user.id,
    #                      'complete subsection',
    #                      {'section': 'speaking',
    #                       'part number': part_number})
    # if part_number == 3:
    #     send_amplitude_event(current_user.id,
    #                          'complete section',
    #                          {'section': 'speaking'})
    #
    # return redirect(url_for('main.get_speaking_attempt',
    #                         user_subsection_attempt_id=subsection_attempt.id))


@bp.route('/section/speaking/attempt/<int:user_subsection_attempt_id>/')
@login_required
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
    result = user_subsection_attempt.results
    speaking_scores = result.get_speaking_scores()

    # Advanced Pronunciation Analysis
    answers = user_subsection_attempt.get_transcribed_user_answers
    pron_scores = user_subsection_attempt.get_overall_pron_scores()

    return render_template('subsection_results.html', result=result,
                           speaking_scores=speaking_scores,
                           attempt=user_subsection_attempt,
                           answers=answers, pron_scores=pron_scores,
                           user_progress=user_progress)


@bp.route('/section/results/<int:user_progress_id>/')
@login_required
def get_section_results(user_progress_id):
    user_progress = UserProgress.query.get(user_progress_id)

    # check that user_progress exists
    if not user_progress:
        abort(404)

    # check that user_progress belongs to the current user
    if user_progress.user_id != current_user.id:
        abort(403)

    # check that user_progress is completed
    if not user_progress.is_completed:
        abort(409)

    final_scores = user_progress.get_speaking_final_scores()

    return render_template('section_results.html',
                           user_progress=user_progress,
                           final_scores=final_scores)


@bp.route('/history')
@login_required
def get_sections_history():
    user_progress_history = current_user.get_sections_history()
    return render_template("history.html",
                           user_progress_history=user_progress_history)


@bp.route('/reset-section-progress', methods=["POST"])
@login_required
def reset_section_progress():
    # Retrieve section
    section_name = request.form.get('section_name')
    if section_name:
        section = Section.get_by_name(section_name)
        # Get the current user's progress in this section
        user_progress = current_user.get_section_progress(section.id)
        if user_progress:
            db.session.delete(user_progress)
            db.session.commit()
            flash(
                "You've successfully reset the progress of this section. It's a fresh start!")
    return redirect(url_for('main.index'))
